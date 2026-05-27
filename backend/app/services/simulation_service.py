"""Season simulation helpers."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd

from app.config import get_settings
from app.ml.data_loader import load_schedule
from app.ml.feature_engineering import build_matchup_feature_row
from app.ml.predict import predict_game_from_features
from app.schemas.prediction_schema import (
    ChampionshipProbabilityItem,
    ChampionshipProbabilityResponse,
    SeasonSimulationResponse,
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


def _compose_team_name(city: object, name: object) -> str:
    city_text = "" if pd.isna(city) else str(city).strip()
    name_text = "" if pd.isna(name) else str(name).strip()
    return " ".join(part for part in (city_text, name_text) if part).strip()


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
            championship_counts[ordered_rows[0]["team_id"]] += 1

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

    _, probabilities, _, _ = _run_season_simulations(num_simulations=num_simulations)
    return ChampionshipProbabilityResponse(
        simulation_count=num_simulations,
        methodology=(
            "Version 1 treats the simulated top regular-season team as the "
            "championship proxy rather than running a playoff bracket model."
        ),
        probabilities=probabilities,
    )
