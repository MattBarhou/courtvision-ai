"""Safe dataset loading utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.config import get_settings


def _read_csv_file(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    try:
        dataframe = pd.read_csv(file_path, low_memory=False)
    except Exception as error:  # pragma: no cover - pandas boundary
        raise ValueError(f"Failed to load dataset: {file_path}") from error

    if dataframe.empty:
        raise ValueError(f"Dataset is empty: {file_path}")

    return dataframe


def load_games() -> pd.DataFrame:
    settings = get_settings()
    return _read_csv_file(settings.raw_data_dir / settings.games_filename)


def load_team_statistics() -> pd.DataFrame:
    settings = get_settings()
    return _read_csv_file(settings.raw_data_dir / settings.team_statistics_filename)


def load_team_statistics_extended() -> pd.DataFrame:
    settings = get_settings()
    return _read_csv_file(settings.raw_data_dir / settings.team_statistics_extended_filename)


def load_schedule() -> pd.DataFrame:
    settings = get_settings()
    return _read_csv_file(settings.raw_data_dir / settings.schedule_filename)
