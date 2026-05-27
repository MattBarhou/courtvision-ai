"""Pydantic request and response schemas for prediction endpoints."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class GamePredictionRequest(BaseModel):
    """Request payload for a single game prediction."""

    home_team: str = Field(..., description="Home team name, such as 'Boston Celtics'.")
    away_team: str = Field(..., description="Away team name, such as 'Milwaukee Bucks'.")
    game_date: date | None = Field(
        default=None,
        description="Optional game date used to estimate rest days.",
    )
    home_team_id: int | None = Field(default=None, description="Optional NBA home team id.")
    away_team_id: int | None = Field(default=None, description="Optional NBA away team id.")


class GamePredictionResponse(BaseModel):
    """Prediction response for one NBA game."""

    home_team: str
    away_team: str
    predicted_winner: str
    home_win_probability: float
    away_win_probability: float
    confidence_score: float
    model_name: str


class TeamStanding(BaseModel):
    """Projected team standing row."""

    rank: int
    team_id: int
    team_name: str
    wins: float
    losses: float
    win_pct: float


class ChampionshipProbabilityItem(BaseModel):
    """Simple championship probability row."""

    team_id: int
    team_name: str
    championship_probability: float


class SeasonSimulationResponse(BaseModel):
    """Response payload for season simulation results."""

    simulation_count: int
    completed_games: int
    remaining_games: int
    methodology: str
    projected_standings: list[TeamStanding]


class ChampionshipProbabilityResponse(BaseModel):
    """Response payload for championship probability estimates."""

    simulation_count: int
    methodology: str
    probabilities: list[ChampionshipProbabilityItem]
