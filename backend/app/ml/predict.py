"""Model loading and prediction utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.config import get_settings


def load_model_bundle(model_path: Path | None = None) -> dict[str, Any]:
    """Load the trained model bundle from disk."""

    settings = get_settings()
    artifact_path = model_path or settings.model_artifact_path
    if not artifact_path.exists():
        raise FileNotFoundError(
            "Trained model artifact not found. Run `python -m app.ml.train_model` first."
        )

    bundle = joblib.load(artifact_path)
    if not isinstance(bundle, dict) or "model" not in bundle or "feature_columns" not in bundle:
        raise ValueError("Model artifact is not in the expected format.")

    return bundle


def predict_game_from_features(
    model_bundle: dict[str, Any],
    feature_values: dict[str, Any],
    home_team: str,
    away_team: str,
) -> dict[str, Any]:
    """Run a game winner prediction from an already-built feature row."""

    feature_columns: list[str] = model_bundle["feature_columns"]
    model = model_bundle["model"]
    feature_frame = pd.DataFrame(
        [{column: feature_values.get(column) for column in feature_columns}],
        columns=feature_columns,
    )

    probabilities = model.predict_proba(feature_frame)[0]
    home_win_probability = float(probabilities[1])
    away_win_probability = float(probabilities[0])
    predicted_winner = home_team if home_win_probability >= away_win_probability else away_team
    confidence_score = float(max(home_win_probability, away_win_probability))

    return {
        "predicted_winner": predicted_winner,
        "home_win_probability": round(home_win_probability, 4),
        "away_win_probability": round(away_win_probability, 4),
        "confidence_score": round(confidence_score, 4),
        "model_name": str(model_bundle.get("model_name", "unknown")),
    }
