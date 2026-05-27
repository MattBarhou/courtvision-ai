"""Service helpers for real-time game predictions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache
from typing import Any

import pandas as pd

from app.config import get_settings
from app.ml.data_loader import (
    load_games,
    load_team_statistics,
    load_team_statistics_extended,
)
from app.ml.feature_engineering import (
    build_matchup_feature_row,
    build_team_snapshots,
)
from app.ml.predict import load_model_bundle, predict_game_from_features
from app.ml.preprocess import prepare_team_games
from app.schemas.prediction_schema import GamePredictionRequest, GamePredictionResponse


def _normalize_team_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


@dataclass(frozen=True)
class PredictionContext:
    """Cached prediction resources."""

    model_bundle: dict[str, Any]
    team_snapshots: pd.DataFrame
    team_lookup: dict[str, int]
    team_names: dict[int, str]
    team_games: pd.DataFrame


def _build_team_lookup(team_snapshots: pd.DataFrame) -> tuple[dict[str, int], dict[int, str]]:
    lookup: dict[str, int] = {}
    names: dict[int, str] = {}

    for row in team_snapshots.itertuples(index=False):
        team_id = int(row.teamId)
        team_name = str(row.team_full_name)
        names[team_id] = team_name

        candidates = {
            team_name,
            team_name.split()[-1],
            str(team_id),
        }
        for candidate in candidates:
            lookup[_normalize_team_key(candidate)] = team_id

    return lookup, names


@lru_cache(maxsize=1)
def get_prediction_context() -> PredictionContext:
    """Load and cache the model, team history, and lookup tables."""

    settings = get_settings()
    team_games = prepare_team_games(
        games_df=load_games(),
        team_statistics_df=load_team_statistics(),
        team_statistics_extended_df=load_team_statistics_extended(),
    )
    team_snapshots = build_team_snapshots(
        team_games=team_games,
        window=settings.rolling_window,
    ).set_index("teamId", drop=False)
    team_lookup, team_names = _build_team_lookup(team_snapshots.reset_index(drop=True))

    return PredictionContext(
        model_bundle=load_model_bundle(settings.model_artifact_path),
        team_snapshots=team_snapshots,
        team_lookup=team_lookup,
        team_names=team_names,
        team_games=team_games,
    )


def _resolve_team(
    context: PredictionContext,
    team_name: str | None,
    team_id: int | None,
    role: str,
) -> tuple[int, str]:
    if team_id is not None:
        if team_id not in context.team_names:
            raise ValueError(f"Unknown {role} team id: {team_id}.")
        return team_id, context.team_names[team_id]

    if not team_name:
        raise ValueError(f"{role.capitalize()} team name is required.")

    lookup_key = _normalize_team_key(team_name)
    if lookup_key not in context.team_lookup:
        raise ValueError(f"Unknown {role} team: {team_name}.")

    resolved_id = context.team_lookup[lookup_key]
    return resolved_id, context.team_names[resolved_id]


def _resolve_game_date(game_date: date | None) -> pd.Timestamp:
    if game_date is None:
        return pd.Timestamp(datetime.now(UTC).date())
    return pd.Timestamp(game_date)


def get_prediction_health() -> dict[str, object]:
    """Return a health payload for the prediction subsystem."""

    settings = get_settings()
    return {
        "status": "ok",
        "model_available": settings.model_artifact_path.exists(),
        "artifacts_path": str(settings.artifacts_dir),
    }


def predict_game(payload: GamePredictionRequest) -> GamePredictionResponse:
    """Serve a single matchup prediction using the trained model."""

    context = get_prediction_context()
    home_team_id, home_team_name = _resolve_team(
        context=context,
        team_name=payload.home_team,
        team_id=payload.home_team_id,
        role="home",
    )
    away_team_id, away_team_name = _resolve_team(
        context=context,
        team_name=payload.away_team,
        team_id=payload.away_team_id,
        role="away",
    )

    if home_team_id == away_team_id:
        raise ValueError("Home and away teams must be different.")

    reference_date = _resolve_game_date(payload.game_date)
    feature_values = build_matchup_feature_row(
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        team_snapshots=context.team_snapshots,
        game_date=reference_date,
    )
    prediction = predict_game_from_features(
        model_bundle=context.model_bundle,
        feature_values=feature_values,
        home_team=home_team_name,
        away_team=away_team_name,
    )

    return GamePredictionResponse(
        home_team=home_team_name,
        away_team=away_team_name,
        predicted_winner=prediction["predicted_winner"],
        home_win_probability=prediction["home_win_probability"],
        away_win_probability=prediction["away_win_probability"],
        confidence_score=prediction["confidence_score"],
        model_name=prediction["model_name"],
    )
