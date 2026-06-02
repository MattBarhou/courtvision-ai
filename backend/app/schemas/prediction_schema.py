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


class ActualStanding(BaseModel):
    """Actual regular-season standings row from the external data source."""

    rank: int
    conference: str
    conference_rank: int
    playoff_seed: int | None = None
    team_name: str
    wins: int
    losses: int
    win_pct: float
    games_back: str | None = None


class PlayoffSeriesTeam(BaseModel):
    """Team representation inside a playoff matchup."""

    team_name: str
    abbreviation: str
    seed: int | None = None
    is_series_winner: bool = False


class PlayoffMatchup(BaseModel):
    """Current or completed playoff series."""

    matchup_id: str
    series_title: str
    series_summary: str
    status_detail: str
    status_state: str
    scheduled_date: str | None = None
    is_complete: bool
    competitor_one: PlayoffSeriesTeam
    competitor_two: PlayoffSeriesTeam


class PlayoffRound(BaseModel):
    """Playoff bracket round."""

    round_id: int
    round_name: str
    matchups: list[PlayoffMatchup]


class StandingsAccuracySummary(BaseModel):
    """High-level accuracy metrics comparing projected and actual regular-season standings."""

    compared_teams: int
    exact_rank_matches: int
    within_three_slots: int
    top_eight_overlap: int
    mean_absolute_rank_error: float


class SeasonResultsResponse(BaseModel):
    """Combined predicted-vs-actual season response for regular season and playoffs."""

    season: str
    simulation_count: int
    generated_at: str
    methodology: str
    playoff_status: str
    predicted_standings: list[TeamStanding]
    actual_regular_season_standings: list[ActualStanding]
    current_playoff_bracket: list[PlayoffRound]
    accuracy_summary: StandingsAccuracySummary
