"""Leakage-safe NBA feature engineering utilities."""

from __future__ import annotations

import numpy as np
import pandas as pd


ROLLING_SOURCE_COLUMNS = {
    "rolling_points_scored": "teamScore",
    "rolling_points_allowed": "opponentScore",
    "rolling_point_margin": "point_margin",
    "rolling_offensive_rating": "offensiveRating",
    "rolling_defensive_rating": "defensiveRating",
    "rolling_rebounds": "reboundsTotal",
    "rolling_assists": "assists",
    "rolling_turnovers": "turnovers",
}

TEAM_FEATURE_COLUMNS = list(ROLLING_SOURCE_COLUMNS.keys()) + [
    "recent_win_pct",
    "season_win_pct",
    "season_point_margin",
    "rest_days",
    "back_to_back",
    "games_played_before",
    "elo_rating",
]


def add_leakage_safe_team_features(
    team_games: pd.DataFrame,
    window: int,
) -> pd.DataFrame:
    """Create rolling team features using only games that happened before the current game."""

    engineered = team_games.copy().sort_values(["teamId", "gameDate", "gameId"]).reset_index(drop=True)
    engineered["point_margin"] = engineered["teamScore"] - engineered["opponentScore"]
    grouped = engineered.groupby("teamId", sort=False)

    for feature_name, source_column in ROLLING_SOURCE_COLUMNS.items():
        engineered[feature_name] = grouped[source_column].transform(
            lambda series: series.shift(1).rolling(window=window, min_periods=1).mean()
        )

    engineered["recent_win_pct"] = grouped["win"].transform(
        lambda series: series.shift(1).rolling(window=window, min_periods=1).mean()
    )
    engineered["season_win_pct"] = grouped["win"].transform(
        lambda series: series.shift(1).expanding(min_periods=1).mean()
    )
    engineered["season_point_margin"] = grouped["point_margin"].transform(
        lambda series: series.shift(1).expanding(min_periods=1).mean()
    )
    engineered["rest_days"] = grouped["gameDate"].diff().dt.days
    engineered["back_to_back"] = engineered["rest_days"].fillna(2).le(1).astype(float)
    engineered["games_played_before"] = grouped.cumcount().astype(float)
    engineered["home_advantage"] = engineered["home"].astype(float)
    engineered = _add_pregame_elo_ratings(engineered)

    return engineered


def _add_pregame_elo_ratings(
    team_games: pd.DataFrame,
    base_rating: float = 1500.0,
    k_factor: float = 20.0,
    home_advantage_points: float = 65.0,
) -> pd.DataFrame:
    """Attach leakage-safe pregame Elo ratings to each team row."""

    rated = team_games.copy().sort_values(["gameDate", "gameId", "home"], ascending=[True, True, False])
    rated["elo_rating"] = np.nan
    ratings: dict[int, float] = {}

    for _, game_rows in rated.groupby("gameId", sort=False):
        if len(game_rows) != 2:
            continue

        home_rows = game_rows[game_rows["home"].eq(1)]
        away_rows = game_rows[game_rows["home"].eq(0)]
        if home_rows.empty or away_rows.empty:
            continue

        home_row = home_rows.iloc[0]
        away_row = away_rows.iloc[0]
        home_team_id = int(home_row["teamId"])
        away_team_id = int(away_row["teamId"])

        home_rating = ratings.get(home_team_id, base_rating)
        away_rating = ratings.get(away_team_id, base_rating)

        rated.loc[home_row.name, "elo_rating"] = home_rating
        rated.loc[away_row.name, "elo_rating"] = away_rating

        expected_home_win = 1.0 / (
            1.0 + 10.0 ** (((away_rating) - (home_rating + home_advantage_points)) / 400.0)
        )
        actual_home_win = float(home_row["home_win"])

        ratings[home_team_id] = home_rating + k_factor * (actual_home_win - expected_home_win)
        ratings[away_team_id] = away_rating + k_factor * ((1.0 - actual_home_win) - (1.0 - expected_home_win))

    return rated.sort_index().reset_index(drop=True)


def build_training_frame(
    team_games: pd.DataFrame,
    window: int,
) -> tuple[pd.DataFrame, list[str]]:
    """Convert team-level game history into a single row per game for model training."""

    engineered = add_leakage_safe_team_features(team_games=team_games, window=window)

    home_games = engineered[engineered["home"].eq(1)].copy()
    away_games = engineered[engineered["home"].eq(0)].copy()

    home_columns = [
        "gameId",
        "gameDate",
        "gameType",
        "gameLabel",
        "home_win",
        "teamId",
        "team_full_name",
        "opponentTeamId",
        "opponent_full_name",
        *TEAM_FEATURE_COLUMNS,
    ]
    away_columns = [
        "gameId",
        "gameDate",
        "teamId",
        "team_full_name",
        *TEAM_FEATURE_COLUMNS,
    ]

    home_frame = home_games[home_columns].rename(
        columns={
            "teamId": "home_team_id",
            "team_full_name": "home_team_name",
            "opponentTeamId": "away_team_id",
            "opponent_full_name": "away_team_name",
            **{column: f"home_{column}" for column in TEAM_FEATURE_COLUMNS},
        }
    )
    away_frame = away_games[away_columns].rename(
        columns={
            "teamId": "away_team_id",
            "team_full_name": "away_team_name",
            **{column: f"away_{column}" for column in TEAM_FEATURE_COLUMNS},
        }
    )

    game_frame = home_frame.merge(
        away_frame,
        on=["gameId", "gameDate", "away_team_id", "away_team_name"],
        how="inner",
        validate="one_to_one",
    )
    game_frame["home_advantage"] = 1.0

    diff_feature_columns: list[str] = []
    for column in TEAM_FEATURE_COLUMNS:
        diff_column = f"{column}_diff"
        game_frame[diff_column] = game_frame[f"home_{column}"] - game_frame[f"away_{column}"]
        diff_feature_columns.append(diff_column)

    model_feature_columns = (
        ["home_advantage"]
        + [f"home_{column}" for column in TEAM_FEATURE_COLUMNS]
        + [f"away_{column}" for column in TEAM_FEATURE_COLUMNS]
        + diff_feature_columns
    )

    game_frame = game_frame.sort_values(["gameDate", "gameId"]).reset_index(drop=True)
    return game_frame, model_feature_columns


def build_team_snapshots(team_games: pd.DataFrame, window: int) -> pd.DataFrame:
    """Build the latest rolling snapshot for each team for future predictions."""

    snapshots: list[dict[str, object]] = []
    ordered = add_leakage_safe_team_features(team_games=team_games, window=window)
    ordered = ordered.sort_values(["teamId", "gameDate", "gameId"]).reset_index(drop=True)

    for team_id, group in ordered.groupby("teamId", sort=False):
        trailing = group.tail(window)
        snapshot = {
            "teamId": int(team_id),
            "team_full_name": str(group["team_full_name"].iloc[-1]),
            "last_game_date": pd.to_datetime(group["gameDate"].iloc[-1], errors="coerce"),
            "rolling_points_scored": trailing["teamScore"].mean(),
            "rolling_points_allowed": trailing["opponentScore"].mean(),
            "rolling_point_margin": trailing["point_margin"].mean(),
            "recent_win_pct": trailing["win"].mean(),
            "season_win_pct": group["win"].mean(),
            "season_point_margin": group["point_margin"].mean(),
            "rolling_offensive_rating": trailing["offensiveRating"].mean(),
            "rolling_defensive_rating": trailing["defensiveRating"].mean(),
            "rolling_rebounds": trailing["reboundsTotal"].mean(),
            "rolling_assists": trailing["assists"].mean(),
            "rolling_turnovers": trailing["turnovers"].mean(),
            "games_played_before": float(len(group)),
            "elo_rating": float(group["elo_rating"].iloc[-1]),
        }
        snapshots.append(snapshot)

    return pd.DataFrame(snapshots)


def build_matchup_feature_row(
    home_team_id: int,
    away_team_id: int,
    team_snapshots: pd.DataFrame,
    game_date: pd.Timestamp,
) -> dict[str, float | int | None]:
    """Build a model-ready feature row for a future matchup."""

    if home_team_id not in team_snapshots.index or away_team_id not in team_snapshots.index:
        raise ValueError("Unable to build matchup features for teams without historical data.")

    home_snapshot = team_snapshots.loc[home_team_id]
    away_snapshot = team_snapshots.loc[away_team_id]
    game_timestamp = pd.Timestamp(game_date)

    home_rest_days = np.nan
    away_rest_days = np.nan
    if pd.notna(home_snapshot["last_game_date"]):
        home_rest_days = max((game_timestamp - pd.Timestamp(home_snapshot["last_game_date"])).days, 0)
    if pd.notna(away_snapshot["last_game_date"]):
        away_rest_days = max((game_timestamp - pd.Timestamp(away_snapshot["last_game_date"])).days, 0)

    features: dict[str, float | int | None] = {"home_advantage": 1.0}
    for column in TEAM_FEATURE_COLUMNS:
        if column == "rest_days":
            home_value = float(home_rest_days) if not np.isnan(home_rest_days) else np.nan
            away_value = float(away_rest_days) if not np.isnan(away_rest_days) else np.nan
        elif column == "back_to_back":
            home_value = 1.0 if not np.isnan(home_rest_days) and home_rest_days <= 1 else 0.0
            away_value = 1.0 if not np.isnan(away_rest_days) and away_rest_days <= 1 else 0.0
        else:
            home_value = home_snapshot.get(column, np.nan)
            away_value = away_snapshot.get(column, np.nan)

        features[f"home_{column}"] = None if pd.isna(home_value) else float(home_value)
        features[f"away_{column}"] = None if pd.isna(away_value) else float(away_value)

        if pd.isna(home_value) or pd.isna(away_value):
            features[f"{column}_diff"] = None
        else:
            features[f"{column}_diff"] = float(home_value - away_value)

    return features
