"""Application configuration for the CourtVision AI backend."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _split_csv_env(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from the backend `.env` file."""

    app_name: str = os.getenv("APP_NAME", "CourtVision AI")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv_env(os.getenv("CORS_ORIGINS", "*"))
    )
    random_seed: int = int(os.getenv("RANDOM_SEED", "42"))
    rolling_window: int = int(os.getenv("ROLLING_WINDOW", "10"))
    simulation_count: int = int(os.getenv("DEFAULT_SIMULATION_COUNT", "200"))
    standings_refresh_seconds: int = int(os.getenv("STANDINGS_REFRESH_SECONDS", "21600"))
    playoff_refresh_seconds: int = int(os.getenv("PLAYOFF_REFRESH_SECONDS", "900"))
    base_dir: Path = BASE_DIR
    raw_data_dir: Path = BASE_DIR / "data" / "raw"
    processed_data_dir: Path = BASE_DIR / "data" / "processed"
    artifacts_dir: Path = BASE_DIR / "artifacts"
    model_artifact_path: Path = BASE_DIR / "artifacts" / "game_winner_model.pkl"
    feature_columns_path: Path = BASE_DIR / "artifacts" / "feature_columns.json"
    evaluation_path: Path = BASE_DIR / "artifacts" / "evaluation.json"
    games_filename: str = "Games.csv"
    team_statistics_filename: str = "TeamStatistics.csv"
    team_statistics_extended_filename: str = "TeamStatisticsExtended.csv"
    schedule_filename: str = "LeagueSchedule25_26.csv"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    return Settings()
