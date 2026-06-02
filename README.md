# CourtVision AI

CourtVision AI is a full-stack NBA analytics application that combines a production-style FastAPI backend, a Next.js frontend, and a machine learning pipeline to forecast game outcomes and season-level performance. The app uses historical NBA data to predict single-game winners, simulate regular-season standings, estimate championship probabilities, and compare model projections with the actual 2025-26 NBA standings and playoff bracket.

The goal of the project is to turn historical team performance data into a clean, interactive product that helps users explore both predictive basketball analytics and model accuracy. Rather than focusing only on model training, CourtVision AI is built as an end-to-end application with an API layer, reusable services, trained model artifacts, responsive UI, and live public-data integration for real-world comparison.

## Core Features

- Single-game winner prediction for NBA matchups
- Projected home-win and away-win probabilities with confidence score
- Regular-season simulation using the trained game prediction model
- Championship probability estimates based on simulated season outcomes
- Side-by-side comparison of predicted standings vs. actual 2025-26 regular-season standings
- Live playoff bracket display using public NBA/ESPN data
- Responsive multi-page frontend for game predictions, season comparison, and title odds

## AI and Machine Learning Techniques

CourtVision AI uses supervised machine learning to model the probability that the home team wins a game. The training pipeline is designed to reflect realistic forecasting conditions and avoid common sports-modeling mistakes like data leakage.

### Modeling approach

- Binary classification target: `home_win`
- Baseline model: `LogisticRegression`
- Tree-based ensemble model: `RandomForestClassifier`
- Gradient boosting model: `XGBoostClassifier`
- Model selection based on chronological validation performance

### Feature engineering

The model relies on pregame team-level context rather than postgame outcomes. Features are built using only information available before the target game:

- rolling points scored
- rolling points allowed
- recent win percentage
- rolling offensive rating
- rolling defensive rating
- rolling rebounds
- rolling assists
- rolling turnovers
- home-court indicator
- rest-day features when date information is available

### Leakage prevention

To keep the model realistic and production-usable:

- rolling features are computed from previous games only
- the current game is never included in its own feature set
- train/test evaluation uses chronological splitting instead of random shuffling

### Evaluation

The training pipeline evaluates model quality using:

- accuracy
- precision
- recall
- F1 score
- ROC AUC
- confusion matrix

## Data Sources

The project is built primarily around historical NBA team and game data from:

- `Games.csv`
- `TeamStatistics.csv`
- `TeamStatisticsExtended.csv`
- `LeagueSchedule25_26.csv`

For live comparison features, the app also uses public standings and playoff data to show how the model's projections compare to the real 2025-26 NBA season.

## Tech Stack

### Backend

- Python
- FastAPI
- pandas
- numpy
- scikit-learn
- xgboost
- joblib
- pyarrow
- pydantic

### Frontend

- Next.js
- React
- Mantine
- Motion

## Project Structure

```text
backend/   FastAPI API, ML pipeline, data loaders, model artifacts
frontend/  Next.js client for predictions, standings, and title odds
```

## Why This Project Stands Out

CourtVision AI is more than a notebook-based model experiment. It demonstrates:

- end-to-end ML product development
- production-minded API design
- practical feature engineering for time-series sports data
- model evaluation with leakage-aware validation
- frontend integration for real user interaction
- external-data enrichment for live contextual comparison

## Running Locally

Backend setup and API usage are documented in [backend/README.md](</c:/Users/16479/Desktop/courtvision-ai/backend/README.md>).

Frontend setup and local UI usage are documented in [frontend/README.md](</c:/Users/16479/Desktop/courtvision-ai/frontend/README.md>).
