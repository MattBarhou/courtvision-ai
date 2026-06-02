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


def _chronological_train_validation_test_split(
    game_frame: pd.DataFrame,
    validation_fraction: float = 0.1,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered_games = game_frame[["gameId", "gameDate"]].drop_duplicates().sort_values(["gameDate", "gameId"])
    if len(ordered_games) < 20:
        raise ValueError("Not enough historical games to create stable train, validation, and test splits.")

    total_games = len(ordered_games)
    test_games = max(int(total_games * test_fraction), 1)
    validation_games = max(int(total_games * validation_fraction), 1)
    train_games = total_games - validation_games - test_games
    if train_games < 1:
        raise ValueError("Chronological split produced an empty training set.")

    train_end = train_games
    validation_end = train_games + validation_games
    train_ids = set(ordered_games.iloc[:train_end]["gameId"].tolist())
    validation_ids = set(ordered_games.iloc[train_end:validation_end]["gameId"].tolist())
    test_ids = set(ordered_games.iloc[validation_end:]["gameId"].tolist())

    train_frame = game_frame[game_frame["gameId"].isin(train_ids)].copy()
    validation_frame = game_frame[game_frame["gameId"].isin(validation_ids)].copy()
    test_frame = game_frame[game_frame["gameId"].isin(test_ids)].copy()
    if train_frame.empty or validation_frame.empty or test_frame.empty:
        raise ValueError("Chronological split produced an empty train, validation, or test set.")

    return train_frame, validation_frame, test_frame


def _build_model_candidates(random_seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        C=0.7,
                        max_iter=2000,
                        random_state=random_seed,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=500,
                        max_depth=10,
                        min_samples_leaf=2,
                        min_samples_split=8,
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
                        max_depth=3,
                        learning_rate=0.03,
                        min_child_weight=3,
                        subsample=0.85,
                        colsample_bytree=0.85,
                        reg_alpha=0.1,
                        reg_lambda=2.0,
                        objective="binary:logistic",
                        eval_metric="logloss",
                        random_state=random_seed,
                        n_jobs=1,
                    ),
                ),
            ]
        ),
    }


def _filter_recent_history(
    train_frame: pd.DataFrame,
    reference_date: pd.Timestamp,
    history_window_years: int | None,
) -> pd.DataFrame:
    if history_window_years is None:
        return train_frame

    cutoff_date = reference_date - pd.DateOffset(years=history_window_years)
    filtered = train_frame[train_frame["gameDate"].ge(cutoff_date)].copy()
    return filtered if not filtered.empty else train_frame


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

    train_frame, validation_frame, test_frame = _chronological_train_validation_test_split(
        game_frame=game_frame
    )
    x_validation = validation_frame[feature_columns]
    y_validation = validation_frame["home_win"].astype(int).to_numpy()
    x_test = test_frame[feature_columns]
    y_test = test_frame["home_win"].astype(int).to_numpy()

    model_candidates = _build_model_candidates(settings.random_seed)
    history_window_candidates: list[int | None] = [None, 15]
    evaluation_summary: dict[str, dict[str, object]] = {}
    best_model_name = ""
    best_model: Pipeline | None = None
    best_history_window_years: int | None = None
    best_score = float("-inf")
    validation_reference_date = pd.Timestamp(validation_frame["gameDate"].min())

    for model_name, pipeline in model_candidates.items():
        for history_window_years in history_window_candidates:
            candidate_train_frame = _filter_recent_history(
                train_frame=train_frame,
                reference_date=validation_reference_date,
                history_window_years=history_window_years,
            )
            x_train = candidate_train_frame[feature_columns]
            y_train = candidate_train_frame["home_win"].astype(int).to_numpy()

            pipeline.fit(x_train, y_train)
            validation_labels = pipeline.predict(x_validation)
            validation_probabilities = pipeline.predict_proba(x_validation)[:, 1]
            validation_metrics = evaluate_classification_model(
                y_true=y_validation,
                y_pred=validation_labels,
                y_proba=validation_probabilities,
            )

            window_label = "all_history" if history_window_years is None else f"last_{history_window_years}_years"
            evaluation_summary[f"{model_name}__{window_label}"] = {
                "validation_metrics": validation_metrics,
                "training_games": int(candidate_train_frame["gameId"].nunique()),
            }

            candidate_score = validation_metrics["roc_auc"]
            if candidate_score is None:
                candidate_score = validation_metrics["accuracy"]
            if float(candidate_score) > best_score:
                best_score = float(candidate_score)
                best_model_name = model_name
                best_history_window_years = history_window_years
                best_model = pipeline

    if best_model is None:
        raise RuntimeError("Model selection failed because no candidate models were trained.")

    combined_train_frame = pd.concat([train_frame, validation_frame], ignore_index=True)
    final_reference_date = pd.Timestamp(test_frame["gameDate"].min())
    final_train_frame = _filter_recent_history(
        train_frame=combined_train_frame,
        reference_date=final_reference_date,
        history_window_years=best_history_window_years,
    )
    x_final_train = final_train_frame[feature_columns]
    y_final_train = final_train_frame["home_win"].astype(int).to_numpy()
    best_model.fit(x_final_train, y_final_train)

    predicted_labels = best_model.predict(x_test)
    predicted_probabilities = best_model.predict_proba(x_test)[:, 1]
    test_metrics = evaluate_classification_model(
        y_true=y_test,
        y_pred=predicted_labels,
        y_proba=predicted_probabilities,
    )

    model_bundle = {
        "model": best_model,
        "feature_columns": feature_columns,
        "model_name": best_model_name,
        "trained_at": datetime.now(UTC).isoformat(),
        "rolling_window": settings.rolling_window,
        "history_window_years": best_history_window_years,
    }
    joblib.dump(model_bundle, settings.model_artifact_path)
    settings.feature_columns_path.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")

    evaluation_payload = {
        "best_model": best_model_name,
        "selected_metric": "validation_roc_auc",
        "selected_history_window_years": best_history_window_years,
        "feature_count": len(feature_columns),
        "training_games": int(final_train_frame["gameId"].nunique()),
        "validation_games": int(validation_frame["gameId"].nunique()),
        "test_games": int(test_frame["gameId"].nunique()),
        "train_date_range": [
            str(pd.Timestamp(final_train_frame["gameDate"].min()).date()),
            str(pd.Timestamp(final_train_frame["gameDate"].max()).date()),
        ],
        "validation_date_range": [
            str(pd.Timestamp(validation_frame["gameDate"].min()).date()),
            str(pd.Timestamp(validation_frame["gameDate"].max()).date()),
        ],
        "test_date_range": [
            str(pd.Timestamp(test_frame["gameDate"].min()).date()),
            str(pd.Timestamp(test_frame["gameDate"].max()).date()),
        ],
        "validation_candidates": evaluation_summary,
        "test_metrics": test_metrics,
    }
    settings.evaluation_path.write_text(json.dumps(evaluation_payload, indent=2), encoding="utf-8")

    return {
        "best_model": best_model_name,
        "feature_count": len(feature_columns),
        "training_rows": int(len(final_train_frame)),
        "validation_rows": int(len(validation_frame)),
        "test_rows": int(len(test_frame)),
        "best_score": round(float(test_metrics["roc_auc"] or test_metrics["accuracy"]), 4),
    }


def main() -> None:
    result = train_model()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
