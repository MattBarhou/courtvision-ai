"""Season simulation helpers and actual standings comparison utilities."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from app.config import get_settings
from app.ml.data_loader import load_schedule
from app.ml.feature_engineering import build_matchup_feature_row
from app.ml.predict import predict_game_from_features
from app.schemas.prediction_schema import (
    ActualStanding,
    ChampionshipProbabilityItem,
    ChampionshipProbabilityResponse,
    PlayoffMatchup,
    PlayoffRound,
    PlayoffSeriesTeam,
    SeasonResultsResponse,
    SeasonSimulationResponse,
    StandingsAccuracySummary,
    TeamStanding,
)
from app.services.prediction_service import get_prediction_context


EXCLUDED_SCHEDULE_LABELS = {
    "All-Star",
    "All-Star Championship",
    "East Conf. Finals",
    "East Conf. Semifinals",
    "East First Round",
    "NBA Finals",
    "Preseason",
    "Rising Stars Final",
    "Rising Stars Semifinal",
    "SoFi Play-In Tournament",
    "West Conf. Finals",
    "West Conf. Semifinals",
    "West First Round",
}

ACTUAL_RESULTS_SEASON = 2026
ACTUAL_RESULTS_LABEL = "2025-26"
ACTUAL_STANDINGS_URL = (
    "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"
    "?region=us&lang=en&contentorigin=espn&type=0&level=2"
    "&sort=playoffseed:asc&seasontype=2&season=2026"
)
PLAYOFF_BRACKET_URL = "https://www.espn.com/nba/playoff-bracket"

TEAM_NAME_ALIASES = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
}


@dataclass
class ExternalCacheEntry:
    """Small in-memory cache entry for public NBA data."""

    checked_at: float
    body: str
    etag: str | None = None
    last_modified: str | None = None


_external_cache: dict[str, ExternalCacheEntry] = {}


def _compose_team_name(city: object, name: object) -> str:
    city_text = "" if pd.isna(city) else str(city).strip()
    name_text = "" if pd.isna(name) else str(name).strip()
    return " ".join(part for part in (city_text, name_text) if part).strip()


def _normalize_team_name(team_name: str) -> str:
    canonical_name = TEAM_NAME_ALIASES.get(team_name, team_name)
    return re.sub(r"[^a-z0-9]", "", canonical_name.lower())


def _http_get(
    url: str,
    *,
    etag: str | None = None,
    last_modified: str | None = None,
) -> ExternalCacheEntry:
    headers = {
        "User-Agent": "CourtVisionAI/1.0 (+https://example.local)",
        "Accept": "*/*",
    }
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return ExternalCacheEntry(
                checked_at=time.time(),
                body=response.read().decode("utf-8"),
                etag=response.headers.get("ETag"),
                last_modified=response.headers.get("Last-Modified"),
            )
    except HTTPError as error:  # pragma: no cover - network boundary
        if error.code == 304:
            raise
        raise ValueError(f"Unable to fetch external NBA data from {url}.") from error
    except URLError as error:  # pragma: no cover - network boundary
        raise ValueError(f"Unable to fetch external NBA data from {url}.") from error


def _get_cached_external_data(
    cache_key: str,
    url: str,
    *,
    refresh_seconds: int,
) -> str:
    cached_entry = _external_cache.get(cache_key)
    now = time.time()
    if cached_entry and now - cached_entry.checked_at < refresh_seconds:
        return cached_entry.body

    try:
        refreshed_entry = _http_get(
            url,
            etag=cached_entry.etag if cached_entry else None,
            last_modified=cached_entry.last_modified if cached_entry else None,
        )
    except HTTPError as error:  # pragma: no cover - network boundary
        if error.code == 304 and cached_entry:
            cached_entry.checked_at = now
            return cached_entry.body
        raise ValueError(f"Unable to refresh external NBA data from {url}.") from error
    except ValueError:
        if cached_entry:
            return cached_entry.body
        raise

    _external_cache[cache_key] = refreshed_entry
    return refreshed_entry.body


def _fetch_actual_regular_season_standings() -> list[ActualStanding]:
    settings = get_settings()
    standings_payload = json.loads(
        _get_cached_external_data(
            "actual_regular_season_standings",
            ACTUAL_STANDINGS_URL,
            refresh_seconds=settings.standings_refresh_seconds,
        )
    )

    standings_rows: list[dict[str, Any]] = []
    for conference in standings_payload.get("children", []):
        conference_name = str(conference.get("name", ""))
        entries = conference.get("standings", {}).get("entries", [])
        for conference_rank, entry in enumerate(entries, start=1):
            team = entry.get("team", {})
            stats = entry.get("stats", [])
            team_name = TEAM_NAME_ALIASES.get(team.get("displayName", ""), team.get("displayName", ""))
            wins = int(_extract_stat_value(stats, "wins", 0))
            losses = int(_extract_stat_value(stats, "losses", 0))
            win_pct = float(_extract_stat_value(stats, "winpercent", 0.0))
            playoff_seed = _extract_stat_value(stats, "playoffseed", None)
            games_back_value = _extract_stat_display(stats, "gamesbehind")

            standings_rows.append(
                {
                    "conference": conference_name,
                    "conference_rank": conference_rank,
                    "playoff_seed": int(playoff_seed) if playoff_seed is not None else None,
                    "team_name": team_name,
                    "wins": wins,
                    "losses": losses,
                    "win_pct": win_pct,
                    "games_back": games_back_value,
                }
            )

    standings_rows.sort(
        key=lambda row: (
            -row["win_pct"],
            -row["wins"],
            row["losses"],
            row["team_name"],
        )
    )

    return [
        ActualStanding(
            rank=index,
            conference=row["conference"],
            conference_rank=row["conference_rank"],
            playoff_seed=row["playoff_seed"],
            team_name=row["team_name"],
            wins=row["wins"],
            losses=row["losses"],
            win_pct=round(row["win_pct"], 4),
            games_back=row["games_back"],
        )
        for index, row in enumerate(standings_rows, start=1)
    ]


def _extract_stat_value(stats: list[dict[str, Any]], stat_type: str, default: Any) -> Any:
    for stat in stats:
        if stat.get("type") == stat_type or stat.get("name") == stat_type:
            return stat.get("value", default)
    return default


def _extract_stat_display(stats: list[dict[str, Any]], stat_type: str) -> str | None:
    for stat in stats:
        if stat.get("type") == stat_type or stat.get("name") == stat_type:
            display_value = stat.get("displayValue")
            return None if display_value in (None, "") else str(display_value)
    return None


def _fetch_current_playoff_bracket() -> tuple[list[PlayoffRound], str]:
    settings = get_settings()
    bracket_html = _get_cached_external_data(
        "current_playoff_bracket_html",
        PLAYOFF_BRACKET_URL,
        refresh_seconds=settings.playoff_refresh_seconds,
    )

    try:
        bracket_root = _extract_playoff_bracket_root(bracket_html)
        bracket_data = bracket_root.get("page", {}).get("content", {}).get("bracket", {})
    except ValueError:
        bracket_data = _extract_playoff_bracket_data_from_html_resilient(bracket_html)

    round_labels = {
        int(round_entry.get("id")): str(round_entry.get("labelPrimary", f"Round {round_entry.get('id')}"))
        for round_entry in bracket_data.get("rounds", [])
    }
    grouped_matchups: dict[int, list[PlayoffMatchup]] = {}
    playoff_status = "complete"

    for matchup in bracket_data.get("matchups", []):
        round_id = int(matchup.get("roundId", 0))
        if not matchup.get("isSeriesComplete", False):
            playoff_status = "in_progress"

        grouped_matchups.setdefault(round_id, []).append(
            PlayoffMatchup(
                matchup_id=str(matchup.get("matchupId", matchup.get("id", ""))),
                series_title=str(matchup.get("seriesTitle", "")),
                series_summary=str(matchup.get("seriesSummary", "")),
                status_detail=str(matchup.get("statusDetail", "")),
                status_state=str(matchup.get("statusState", "")),
                scheduled_date=matchup.get("date"),
                is_complete=bool(matchup.get("isSeriesComplete", False)),
                competitor_one=PlayoffSeriesTeam(
                    team_name=f"{matchup.get('competitorOne', {}).get('location', '')} {matchup.get('competitorOne', {}).get('name', '')}".strip(),
                    abbreviation=str(matchup.get("competitorOne", {}).get("abbreviation", "")),
                    seed=_safe_int(matchup.get("competitorOne", {}).get("seed")),
                    is_series_winner=bool(matchup.get("competitorOne", {}).get("seriesWinner", False)),
                ),
                competitor_two=PlayoffSeriesTeam(
                    team_name=f"{matchup.get('competitorTwo', {}).get('location', '')} {matchup.get('competitorTwo', {}).get('name', '')}".strip(),
                    abbreviation=str(matchup.get("competitorTwo", {}).get("abbreviation", "")),
                    seed=_safe_int(matchup.get("competitorTwo", {}).get("seed")),
                    is_series_winner=bool(matchup.get("competitorTwo", {}).get("seriesWinner", False)),
                ),
            )
        )

    playoff_rounds = [
        PlayoffRound(
            round_id=round_id,
            round_name=round_labels.get(round_id, f"Round {round_id}"),
            matchups=grouped_matchups[round_id],
        )
        for round_id in sorted(grouped_matchups)
    ]

    return playoff_rounds, playoff_status


def _extract_playoff_bracket_root(bracket_html: str) -> dict[str, Any]:
    marker = "__espnfitt__="
    start_index = bracket_html.find(marker)
    if start_index != -1:
        end_index = bracket_html.find(";</script>", start_index)
        if end_index == -1:
            raise ValueError("Unable to parse playoff bracket payload from the source page.")
        return json.loads(bracket_html[start_index + len(marker) : end_index])

    raw_json_markers = ('{"meta":', '{"page":{"content":{"bracket"', '{"page":')
    for raw_json_marker in raw_json_markers:
        raw_json_index = bracket_html.find(raw_json_marker)
        if raw_json_index == -1:
            continue

        script_close_index = bracket_html.find("</script>", raw_json_index)
        if script_close_index == -1:
            continue

        payload = bracket_html[raw_json_index:script_close_index].strip()
        if payload.endswith(";"):
            payload = payload[:-1]

        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            continue

    raise ValueError("Unable to locate playoff bracket data on the source page.")


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_alive_playoff_teams(playoff_rounds: list[PlayoffRound]) -> set[str]:
    alive_teams: set[str] = set()
    eliminated_teams: set[str] = set()

    for round_data in playoff_rounds:
        for matchup in round_data.matchups:
            competitor_one = matchup.competitor_one
            competitor_two = matchup.competitor_two
            team_one = competitor_one.team_name.strip()
            team_two = competitor_two.team_name.strip()

            if team_one:
                alive_teams.add(_normalize_team_name(team_one))
            if team_two:
                alive_teams.add(_normalize_team_name(team_two))

            if competitor_one.is_series_winner and team_two:
                eliminated_teams.add(_normalize_team_name(team_two))
            elif competitor_two.is_series_winner and team_one:
                eliminated_teams.add(_normalize_team_name(team_one))

    return alive_teams - eliminated_teams


def _load_regular_season_schedule() -> pd.DataFrame:
    schedule = load_schedule().copy()
    schedule["gameDate"] = pd.to_datetime(schedule["gameDateTimeEst"], errors="coerce")
    schedule = schedule.dropna(subset=["gameDate"])
    schedule["homeTeamId"] = pd.to_numeric(schedule["homeTeamId"], errors="coerce")
    schedule["awayTeamId"] = pd.to_numeric(schedule["awayTeamId"], errors="coerce")
    schedule = schedule[
        schedule["homeTeamId"].fillna(0).gt(0)
        & schedule["awayTeamId"].fillna(0).gt(0)
    ].copy()
    schedule = schedule[~schedule["gameLabel"].isin(EXCLUDED_SCHEDULE_LABELS)].copy()
    schedule = schedule[~schedule["gameSubtype"].fillna("").eq("in-season-knockout")].copy()
    schedule["home_team_full_name"] = schedule.apply(
        lambda row: _compose_team_name(row["homeTeamCity"], row["homeTeamName"]),
        axis=1,
    )
    schedule["away_team_full_name"] = schedule.apply(
        lambda row: _compose_team_name(row["awayTeamCity"], row["awayTeamName"]),
        axis=1,
    )
    schedule["homeTeamId"] = schedule["homeTeamId"].astype(int)
    schedule["awayTeamId"] = schedule["awayTeamId"].astype(int)
    return schedule.sort_values(["gameDate", "gameId"]).reset_index(drop=True)


def _build_base_standings(
    team_games: pd.DataFrame,
    season_start: pd.Timestamp,
    season_end: pd.Timestamp,
) -> tuple[dict[int, dict[str, Any]], set[int]]:
    regular_games = team_games[
        team_games["gameType"].fillna("").eq("Regular Season")
        & team_games["gameDate"].between(season_start, season_end)
    ].copy()

    completed_game_ids = set(
        regular_games.loc[regular_games["home"].eq(1), "gameId"].astype(int).tolist()
    )
    standings: dict[int, dict[str, Any]] = {}

    for row in regular_games.itertuples(index=False):
        team_id = int(row.teamId)
        team_name = str(row.team_full_name)
        record = standings.setdefault(
            team_id,
            {
                "team_id": team_id,
                "team_name": team_name,
                "wins": 0.0,
                "losses": 0.0,
            },
        )
        if int(row.win) == 1:
            record["wins"] += 1.0
        else:
            record["losses"] += 1.0

    return standings, completed_game_ids


def _standings_to_rows(standings: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = list(standings.values())
    rows.sort(
        key=lambda row: (
            -row["wins"],
            row["losses"],
            row["team_name"],
        )
    )
    return rows


def _run_season_simulations(
    num_simulations: int,
    eligible_team_keys: set[str] | None = None,
) -> tuple[list[TeamStanding], list[ChampionshipProbabilityItem], int, int]:
    settings = get_settings()
    context = get_prediction_context()
    schedule = _load_regular_season_schedule()

    if schedule.empty:
        return [], [], 0, 0

    season_start = schedule["gameDate"].min().normalize()
    season_end = schedule["gameDate"].max().normalize()
    base_standings, completed_game_ids = _build_base_standings(
        team_games=context.team_games,
        season_start=season_start,
        season_end=season_end,
    )
    remaining_schedule = schedule[~schedule["gameId"].isin(completed_game_ids)].copy()

    all_teams = pd.concat(
        [
            schedule[["homeTeamId", "home_team_full_name"]].rename(
                columns={
                    "homeTeamId": "team_id",
                    "home_team_full_name": "team_name",
                }
            ),
            schedule[["awayTeamId", "away_team_full_name"]].rename(
                columns={
                    "awayTeamId": "team_id",
                    "away_team_full_name": "team_name",
                }
            ),
        ],
        ignore_index=True,
    ).drop_duplicates(subset=["team_id"])

    template_standings = deepcopy(base_standings)
    for row in all_teams.itertuples(index=False):
        template_standings.setdefault(
            int(row.team_id),
            {
                "team_id": int(row.team_id),
                "team_name": str(row.team_name),
                "wins": 0.0,
                "losses": 0.0,
            },
        )

    aggregate_records = {
        team_id: {
            "team_id": record["team_id"],
            "team_name": record["team_name"],
            "wins": 0.0,
            "losses": 0.0,
        }
        for team_id, record in template_standings.items()
    }
    championship_counts: Counter[int] = Counter()
    rng = np.random.default_rng(settings.random_seed)

    for _ in range(num_simulations):
        standings = deepcopy(template_standings)
        for row in remaining_schedule.itertuples(index=False):
            feature_values = build_matchup_feature_row(
                home_team_id=int(row.homeTeamId),
                away_team_id=int(row.awayTeamId),
                team_snapshots=context.team_snapshots,
                game_date=row.gameDate,
            )
            prediction = predict_game_from_features(
                model_bundle=context.model_bundle,
                feature_values=feature_values,
                home_team=row.home_team_full_name,
                away_team=row.away_team_full_name,
            )
            home_win = rng.random() <= prediction["home_win_probability"]
            if home_win:
                standings[int(row.homeTeamId)]["wins"] += 1.0
                standings[int(row.awayTeamId)]["losses"] += 1.0
            else:
                standings[int(row.awayTeamId)]["wins"] += 1.0
                standings[int(row.homeTeamId)]["losses"] += 1.0

        ordered_rows = _standings_to_rows(standings)
        if ordered_rows:
            champion_row = next(
                (
                    row
                    for row in ordered_rows
                    if eligible_team_keys is None
                    or _normalize_team_name(str(row["team_name"])) in eligible_team_keys
                ),
                None,
            )
            if champion_row is not None:
                championship_counts[champion_row["team_id"]] += 1

        for team_id, record in standings.items():
            aggregate_records[team_id]["wins"] += record["wins"]
            aggregate_records[team_id]["losses"] += record["losses"]

    projected_rows = _standings_to_rows(
        {
            team_id: {
                "team_id": record["team_id"],
                "team_name": record["team_name"],
                "wins": record["wins"] / num_simulations,
                "losses": record["losses"] / num_simulations,
            }
            for team_id, record in aggregate_records.items()
        }
    )

    projected_standings = [
        TeamStanding(
            rank=index,
            team_id=row["team_id"],
            team_name=row["team_name"],
            wins=round(float(row["wins"]), 2),
            losses=round(float(row["losses"]), 2),
            win_pct=round(
                float(row["wins"] / max(row["wins"] + row["losses"], 1.0)),
                4,
            ),
        )
        for index, row in enumerate(projected_rows, start=1)
    ]

    championship_probabilities = []
    for standing in projected_standings:
        probability = championship_counts.get(standing.team_id, 0) / max(num_simulations, 1)
        championship_probabilities.append(
            ChampionshipProbabilityItem(
                team_id=standing.team_id,
                team_name=standing.team_name,
                championship_probability=round(float(probability), 4),
            )
        )

    championship_probabilities.sort(
        key=lambda item: (-item.championship_probability, item.team_name)
    )

    return (
        projected_standings,
        championship_probabilities,
        len(completed_game_ids),
        len(remaining_schedule),
    )


def _build_accuracy_summary(
    predicted_standings: list[TeamStanding],
    actual_standings: list[ActualStanding],
) -> StandingsAccuracySummary:
    predicted_lookup = {
        _normalize_team_name(standing.team_name): standing
        for standing in predicted_standings
    }
    actual_lookup = {
        _normalize_team_name(standing.team_name): standing
        for standing in actual_standings
    }
    shared_team_keys = sorted(set(predicted_lookup).intersection(actual_lookup))

    compared_teams = len(shared_team_keys)
    if compared_teams == 0:
        return StandingsAccuracySummary(
            compared_teams=0,
            exact_rank_matches=0,
            within_three_slots=0,
            top_eight_overlap=0,
            mean_absolute_rank_error=0.0,
        )

    rank_differences = []
    exact_rank_matches = 0
    within_three_slots = 0
    top_eight_overlap = 0

    for team_key in shared_team_keys:
        predicted_rank = predicted_lookup[team_key].rank
        actual_rank = actual_lookup[team_key].rank
        difference = abs(predicted_rank - actual_rank)
        rank_differences.append(difference)

        if difference == 0:
            exact_rank_matches += 1
        if difference <= 3:
            within_three_slots += 1
        if predicted_rank <= 8 and actual_rank <= 8:
            top_eight_overlap += 1

    return StandingsAccuracySummary(
        compared_teams=compared_teams,
        exact_rank_matches=exact_rank_matches,
        within_three_slots=within_three_slots,
        top_eight_overlap=top_eight_overlap,
        mean_absolute_rank_error=round(float(np.mean(rank_differences)), 2),
    )


def simulate_season(num_simulations: int) -> SeasonSimulationResponse:
    """Simulate regular-season standings using the trained game model."""

    projected_standings, _, completed_games, remaining_games = _run_season_simulations(
        num_simulations=num_simulations
    )
    return SeasonSimulationResponse(
        simulation_count=num_simulations,
        completed_games=completed_games,
        remaining_games=remaining_games,
        methodology=(
            "Version 1 uses fixed current team-strength snapshots to simulate "
            "remaining regular-season games."
        ),
        projected_standings=projected_standings,
    )


def estimate_championship_probabilities(
    num_simulations: int,
) -> ChampionshipProbabilityResponse:
    """Return simple championship proxy probabilities."""

    methodology = (
        "Version 1 treats the simulated top regular-season team as the "
        "championship proxy rather than running a playoff bracket model."
    )

    try:
        playoff_rounds, playoff_status = _fetch_current_playoff_bracket()
    except ValueError:
        playoff_rounds = []
        playoff_status = ""

    alive_team_keys = _extract_alive_playoff_teams(playoff_rounds)
    _, probabilities, _, _ = _run_season_simulations(
        num_simulations=num_simulations,
        eligible_team_keys=alive_team_keys or None,
    )

    if alive_team_keys:
        methodology += (
            " Live playoff results are used to zero out teams that have already "
            f"been eliminated from the {ACTUAL_RESULTS_LABEL} postseason"
            + ("." if playoff_status != "complete" else ", including the completed bracket.")
        )

    return ChampionshipProbabilityResponse(
        simulation_count=num_simulations,
        methodology=methodology,
        probabilities=probabilities,
    )


def get_season_results(num_simulations: int) -> SeasonResultsResponse:
    """Return projected standings next to actual 2025-26 regular-season and playoff data."""

    predicted_standings, _, _, _ = _run_season_simulations(num_simulations=num_simulations)
    actual_regular_season = _fetch_actual_regular_season_standings()
    playoff_rounds, playoff_status = _fetch_current_playoff_bracket()
    accuracy_summary = _build_accuracy_summary(
        predicted_standings=predicted_standings,
        actual_standings=actual_regular_season,
    )

    return SeasonResultsResponse(
        season=ACTUAL_RESULTS_LABEL,
        simulation_count=num_simulations,
        generated_at=datetime.now(UTC).isoformat(),
        methodology=(
            "Projected standings come from the CourtVision AI season simulator, "
            "while actual regular-season standings and the current playoff bracket "
            "come from public ESPN data."
        ),
        playoff_status=playoff_status,
        predicted_standings=predicted_standings,
        actual_regular_season_standings=actual_regular_season,
        current_playoff_bracket=playoff_rounds,
        accuracy_summary=accuracy_summary,
    )


def _extract_json_array_after_key(html: str, key: str) -> list:
    marker = f'"{key}":'
    start = html.find(marker)
    if start == -1:
        raise ValueError(f'Unable to locate "{key}" in the source page.')

    array_start = html.find("[", start + len(marker))
    if array_start == -1:
        raise ValueError(f'Unable to locate the "{key}" array in the source page.')

    depth = 0
    in_string = False
    escaped = False

    for index in range(array_start, len(html)):
        char = html[index]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return json.loads(html[array_start : index + 1])

    raise ValueError(f'Unable to parse the "{key}" array from the source page.')


def _extract_playoff_bracket_data_from_html_resilient(html: str) -> dict:
    return {
        "rounds": _extract_json_array_after_key(html, "rounds"),
        "matchups": _extract_json_array_after_key(html, "matchups"),
    }
