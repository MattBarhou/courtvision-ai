# CourtVision AI Backend

FastAPI backend for NBA winner prediction, season simulation, and simple championship probability estimation.

## Project Structure

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── predictions.py
│   ├── services/
│   │   ├── prediction_service.py
│   │   └── simulation_service.py
│   ├── ml/
│   │   ├── data_loader.py
│   │   ├── preprocess.py
│   │   ├── feature_engineering.py
│   │   ├── train_model.py
│   │   ├── evaluate.py
│   │   └── predict.py
│   └── schemas/
│       └── prediction_schema.py
├── data/
│   ├── raw/
│   └── processed/
├── artifacts/
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Setup

From the project root:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
```

## Train the Model

```powershell
python -m app.ml.train_model
```

This trains three models:

- Logistic Regression
- Random Forest
- XGBoost

Artifacts are written to `backend/artifacts/`.

## Run the API

```powershell
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health`
- `GET /api/predictions/health`
- `POST /api/predictions/game`
- `POST /api/predictions/season-simulation`
- `GET /api/predictions/championship-probabilities`

## Notes

- Training uses a chronological train/test split.
- Rolling features use only previous games to avoid data leakage.
- Version 1 championship probabilities are a regular-season proxy, not a playoff bracket simulator.
