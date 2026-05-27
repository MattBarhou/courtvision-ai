"""Train the CourtVision AI game winner model."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.config import get_settings
from app.ml.data_loader import (
    load_games,
    load_team_statistics,
    load_team_statistics_extended,
)
from app.ml.evaluate import evaluate_classification_model
from app.ml.feature_engineering import build_training_frame
from app.ml.preprocess import prepare_team_games


def _chronological_train_test_split(
    game_frame: pd.DataFrame,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered_games = game_frame[["gameId", "gameDate"]].drop_duplicates().sort_values(["gameDate", "gameId"])
    if len(ordered_games) < 10:
        raise ValueError("Not enough historical games to create a stable chronological split.")

    split_index = max(int(len(ordered_games) * (1 - test_fraction)), 1)
    split_index = min(split_index, len(ordered_games) - 1)
    train_ids = set(ordered_games.iloc[:split_index]["gameId"].tolist())
    test_ids = set(ordered_games.iloc[split_index:]["gameId"].tolist())

    train_frame = game_frame[game_frame["gameId"].isin(train_ids)].copy()
    test_frame = game_frame[game_frame["gameId"].isin(test_ids)].copy()
    if train_frame.empty or test_frame.empty:
        raise ValueError("Chronological split produced an empty train or test set.")

    return train_frame, test_frame


def _build_model_candidates(random_seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1000, random_state=random_seed)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=2,
                        random_state=random_seed,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "xgboost": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    XGBClassifier(
                        n_estimators=300,
                        max_depth=4,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=random_seed,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
    }


def train_model() -> dict[str, object]:
    """Train baseline and tree models, then persist the best one."""

    settings = get_settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)

    team_games = prepare_team_games(
        games_df=load_games(),
        team_statistics_df=load_team_statistics(),
        team_statistics_extended_df=load_team_statistics_extended(),
    )
    game_frame, feature_columns = build_training_frame(
        team_games=team_games,
        window=settings.rolling_window,
    )
    game_frame = game_frame.dropna(subset=["home_win"]).copy()

    train_frame, test_frame = _chronological_train_test_split(game_frame=game_frame)
    x_train = train_frame[feature_columns]
    y_train = train_frame["home_win"].astype(int).to_numpy()
    x_test = test_frame[feature_columns]
    y_test = test_frame["home_win"].astype(int).to_numpy()

    model_candidates = _build_model_candidates(settings.random_seed)
    evaluation_summary: dict[str, dict[str, object]] = {}
    best_model_name = ""
    best_model: Pipeline | None = None
    best_score = float("-inf")

    for model_name, pipeline in model_candidates.items():
        pipeline.fit(x_train, y_train)
        predicted_labels = pipeline.predict(x_test)
        predicted_probabilities = pipeline.predict_proba(x_test)[:, 1]
        metrics = evaluate_classification_model(
            y_true=y_test,
            y_pred=predicted_labels,
            y_proba=predicted_probabilities,
        )
        evaluation_summary[model_name] = metrics

        candidate_score = metrics["roc_auc"]
        if candidate_score is None:
            candidate_score = metrics["accuracy"]
        if float(candidate_score) > best_score:
            best_score = float(candidate_score)
            best_model_name = model_name
            best_model = pipeline

    if best_model is None:
        raise RuntimeError("Model selection failed because no candidate models were trained.")

    model_bundle = {
        "model": best_model,
        "feature_columns": feature_columns,
        "model_name": best_model_name,
        "trained_at": datetime.now(UTC).isoformat(),
        "rolling_window": settings.rolling_window,
    }
    joblib.dump(model_bundle, settings.model_artifact_path)
    settings.feature_columns_path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")

    evaluation_payload = {
        "best_model": best_model_name,
        "selected_metric": "roc_auc",
        "feature_count": len(feature_columns),
        "training_games": int(train_frame["gameId"].nunique()),
        "test_games": int(test_frame["gameId"].nunique()),
        "train_date_range": [
            str(pd.Timestamp(train_frame["gameDate"].min()).date()),
            str(pd.Timestamp(train_frame["gameDate"].max()).date()),
        ],
        "test_date_range": [
            str(pd.Timestamp(test_frame["gameDate"].min()).date()),
            str(pd.Timestamp(test_frame["gameDate"].max()).date()),
        ],
        "metrics": evaluation_summary,
    }
    settings.evaluation_path.write_text(json.dumps(evaluation_payload, indent=2), encoding="utf-8")

    return {
        "best_model": best_model_name,
        "feature_count": len(feature_columns),
        "training_rows": int(len(train_frame)),
        "test_rows": int(len(test_frame)),
        "best_score": round(best_score, 4),
    }


def main() -> None:
    result = train_model()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
