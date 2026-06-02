"""Prediction-related API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.prediction_schema import (
    ChampionshipProbabilityResponse,
    GamePredictionRequest,
    GamePredictionResponse,
    SeasonResultsResponse,
    SeasonSimulationResponse,
)
from app.services.prediction_service import get_prediction_health, predict_game
from app.services.simulation_service import (
    estimate_championship_probabilities,
    get_season_results,
    simulate_season,
)


router = APIRouter(prefix="/api/predictions", tags=["predictions"])


def _raise_http_error(error: Exception) -> None:
    if isinstance(error, FileNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    if isinstance(error, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while processing the request.",
    ) from error


@router.get("/health")
def predictions_health() -> dict[str, object]:
    """Health check for the prediction subsystem."""

    return get_prediction_health()


@router.post("/game", response_model=GamePredictionResponse)
def game_prediction(payload: GamePredictionRequest) -> GamePredictionResponse:
    """Predict the winner of a single NBA matchup."""

    try:
        return predict_game(payload)
    except Exception as error:  # pragma: no cover - API boundary
        _raise_http_error(error)


@router.post("/season-simulation", response_model=SeasonSimulationResponse)
def season_simulation(
    num_simulations: int = Query(default=200, ge=1, le=5000),
) -> SeasonSimulationResponse:
    """Simulate remaining regular-season standings."""

    try:
        return simulate_season(num_simulations=num_simulations)
    except Exception as error:  # pragma: no cover - API boundary
        _raise_http_error(error)


@router.get("/season-results", response_model=SeasonResultsResponse)
def season_results(
    num_simulations: int = Query(default=200, ge=1, le=5000),
) -> SeasonResultsResponse:
    """Return projected standings beside actual regular-season and playoff results."""

    try:
        return get_season_results(num_simulations=num_simulations)
    except Exception as error:  # pragma: no cover - API boundary
        _raise_http_error(error)


@router.get(
    "/championship-probabilities",
    response_model=ChampionshipProbabilityResponse,
)
def championship_probabilities(
    num_simulations: int = Query(default=200, ge=1, le=5000),
) -> ChampionshipProbabilityResponse:
    """Estimate simple championship proxy probabilities."""

    try:
        return estimate_championship_probabilities(num_simulations=num_simulations)
    except Exception as error:  # pragma: no cover - API boundary
        _raise_http_error(error)
