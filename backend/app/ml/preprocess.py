"""Dataset cleaning and merge logic for CourtVision AI."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


TEAM_NAME_ALIASES = {
    "LA Clippers": "Los Angeles Clippers",
    "LA Lakers": "Los Angeles Lakers",
    "New Jersey Nets": "Brooklyn Nets",
    "New Orleans Hornets": "New Orleans Pelicans",
    "Seattle SuperSonics": "Oklahoma City Thunder",
    "Charlotte Bobcats": "Charlotte Hornets",
}


def _build_full_team_name(city_series: pd.Series, name_series: pd.Series) -> pd.Series:
    city_values = city_series.fillna("").astype(str).str.strip()
    name_values = name_series.fillna("").astype(str).str.strip()
    full_names = (city_values + " " + name_values).str.replace(r"\s+", " ", regex=True).str.strip()
    full_names = full_names.replace("", np.nan)
    return full_names.replace(TEAM_NAME_ALIASES)


def _mode_or_first(values: pd.Series) -> str:
    cleaned = values.dropna().astype(str)
    if cleaned.empty:
        return ""
    mode = cleaned.mode()
    if not mode.empty:
        return mode.iloc[0]
    return cleaned.iloc[0]


def _coerce_numeric(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for column in columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def prepare_team_games(
    games_df: pd.DataFrame,
    team_statistics_df: pd.DataFrame,
    team_statistics_extended_df: pd.DataFrame,
) -> pd.DataFrame:
    """Clean and merge the team-level NBA datasets into one training table."""

    games = games_df.copy()
    team_stats = team_statistics_df.copy()
    extended = team_statistics_extended_df.copy()

    games["gameDate"] = pd.to_datetime(games["gameDate"], errors="coerce")
    games["gameDateTimeEst"] = pd.to_datetime(games["gameDateTimeEst"], errors="coerce")
    team_stats["gameDate"] = pd.to_datetime(team_stats["gameDate"], errors="coerce")
    team_stats["gameDateTimeEst"] = pd.to_datetime(team_stats["gameDateTimeEst"], errors="coerce")
    extended["gameDateTimeEst"] = pd.to_datetime(extended["gameDateTimeEst"], errors="coerce")

    games = games.sort_values(["gameDateTimeEst", "gameId"]).drop_duplicates(subset=["gameId"], keep="last")
    team_stats = team_stats.sort_values(["gameDateTimeEst", "gameId"]).drop_duplicates(
        subset=["gameId", "teamId"],
        keep="last",
    )
    extended = extended.sort_values(["gameDateTimeEst", "gameId"]).drop_duplicates(
        subset=["gameId", "teamId"],
        keep="last",
    )

    team_stats["team_full_name"] = _build_full_team_name(team_stats["teamCity"], team_stats["teamName"])
    team_stats["opponent_full_name"] = _build_full_team_name(
        team_stats["opponentTeamCity"],
        team_stats["opponentTeamName"],
    )
    games["home_team_full_name"] = _build_full_team_name(games["hometeamCity"], games["hometeamName"])
    games["away_team_full_name"] = _build_full_team_name(games["awayteamCity"], games["awayteamName"])

    canonical_name_map = pd.concat(
        [
            pd.DataFrame(
                {
                    "teamId": team_stats["teamId"],
                    "team_full_name": team_stats["team_full_name"],
                }
            ),
            pd.DataFrame(
                {
                    "teamId": team_stats["opponentTeamId"],
                    "team_full_name": team_stats["opponent_full_name"],
                }
            ),
            pd.DataFrame(
                {
                    "teamId": games["hometeamId"],
                    "team_full_name": games["home_team_full_name"],
                }
            ),
            pd.DataFrame(
                {
                    "teamId": games["awayteamId"],
                    "team_full_name": games["away_team_full_name"],
                }
            ),
        ],
        ignore_index=True,
    )
    canonical_name_map = canonical_name_map.dropna(subset=["teamId", "team_full_name"])
    canonical_name_map = canonical_name_map.groupby("teamId")["team_full_name"].agg(_mode_or_first)

    team_stats["team_full_name"] = team_stats["teamId"].map(canonical_name_map).fillna(team_stats["team_full_name"])
    team_stats["opponent_full_name"] = team_stats["opponentTeamId"].map(canonical_name_map).fillna(
        team_stats["opponent_full_name"]
    )
    games["home_team_full_name"] = games["hometeamId"].map(canonical_name_map).fillna(games["home_team_full_name"])
    games["away_team_full_name"] = games["awayteamId"].map(canonical_name_map).fillna(games["away_team_full_name"])

    advanced_columns = [
        column
        for column in [
            "gameId",
            "teamId",
            "offensiveRating",
            "defensiveRating",
            "estimatedOffensiveRating",
            "estimatedDefensiveRating",
            "possessions",
        ]
        if column in extended.columns
    ]
    advanced_stats = extended[advanced_columns].copy()
    team_games = team_stats.merge(
        advanced_stats,
        on=["gameId", "teamId"],
        how="left",
        validate="one_to_one",
    )

    games_for_merge = games[
        [
            "gameId",
            "gameDate",
            "gameDateTimeEst",
            "hometeamId",
            "awayteamId",
            "homeScore",
            "awayScore",
            "winner",
            "gameType",
            "gameLabel",
            "gameSubLabel",
        ]
    ].rename(
        columns={
            "gameDate": "gameDateFromGames",
            "gameDateTimeEst": "gameDateTimeEstFromGames",
            "gameType": "gameTypeFromGames",
            "gameLabel": "gameLabelFromGames",
            "gameSubLabel": "gameSubLabelFromGames",
        }
    )

    team_games = team_games.merge(
        games_for_merge,
        on="gameId",
        how="left",
        validate="many_to_one",
    )

    team_games["gameDate"] = team_games["gameDate"].fillna(team_games["gameDateTimeEst"])
    team_games["gameDate"] = team_games["gameDate"].fillna(team_games["gameDateFromGames"])
    team_games["gameDate"] = team_games["gameDate"].fillna(team_games["gameDateTimeEstFromGames"])
    team_games["gameType"] = team_games["gameType"].fillna(team_games["gameTypeFromGames"])
    team_games["gameLabel"] = team_games["gameLabel"].fillna(team_games["gameLabelFromGames"])
    team_games["gameSubLabel"] = team_games["gameSubLabel"].fillna(team_games["gameSubLabelFromGames"])

    numeric_columns = [
        "home",
        "win",
        "teamId",
        "opponentTeamId",
        "hometeamId",
        "awayteamId",
        "teamScore",
        "opponentScore",
        "homeScore",
        "awayScore",
        "assists",
        "reboundsTotal",
        "turnovers",
        "offensiveRating",
        "defensiveRating",
        "estimatedOffensiveRating",
        "estimatedDefensiveRating",
    ]
    team_games = _coerce_numeric(team_games, numeric_columns)

    team_games["offensiveRating"] = team_games["offensiveRating"].fillna(team_games["estimatedOffensiveRating"])
    team_games["defensiveRating"] = team_games["defensiveRating"].fillna(team_games["estimatedDefensiveRating"])

    inferred_home = np.where(team_games["teamId"].eq(team_games["hometeamId"]), 1, 0)
    team_games["home"] = team_games["home"].fillna(pd.Series(inferred_home, index=team_games.index))

    fallback_team_score = pd.Series(
        np.where(team_games["home"].eq(1), team_games["homeScore"], team_games["awayScore"]),
        index=team_games.index,
    )
    fallback_opponent_score = pd.Series(
        np.where(team_games["home"].eq(1), team_games["awayScore"], team_games["homeScore"]),
        index=team_games.index,
    )
    team_games["teamScore"] = team_games["teamScore"].fillna(fallback_team_score)
    team_games["opponentScore"] = team_games["opponentScore"].fillna(fallback_opponent_score)

    inferred_win = (team_games["teamScore"] > team_games["opponentScore"]).astype(float)
    team_games["win"] = team_games["win"].fillna(inferred_win)

    inferred_home_win = pd.Series(np.nan, index=team_games.index)
    valid_home_scores = team_games["homeScore"].notna() & team_games["awayScore"].notna()
    inferred_home_win.loc[valid_home_scores] = (
        team_games.loc[valid_home_scores, "homeScore"]
        > team_games.loc[valid_home_scores, "awayScore"]
    ).astype(float)
    fallback_home_win = np.where(team_games["home"].eq(1), team_games["win"], 1 - team_games["win"])
    team_games["home_win"] = inferred_home_win
    team_games.loc[
        team_games["home_win"].isna(),
        "home_win",
    ] = pd.Series(fallback_home_win, index=team_games.index)

    team_games = team_games.dropna(
        subset=[
            "gameDate",
            "teamId",
            "opponentTeamId",
            "team_full_name",
            "opponent_full_name",
            "teamScore",
            "opponentScore",
        ]
    ).copy()

    team_games["teamId"] = team_games["teamId"].astype(int)
    team_games["opponentTeamId"] = team_games["opponentTeamId"].astype(int)
    team_games["home"] = team_games["home"].astype(int)
    team_games["win"] = team_games["win"].astype(int)
    team_games["home_win"] = team_games["home_win"].astype(int)

    team_games = team_games.sort_values(["gameDate", "gameId", "teamId"]).reset_index(drop=True)
    return team_games
