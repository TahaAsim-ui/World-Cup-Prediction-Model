# World Cup Prediction Model

An AI-powered football prediction app for simulating 2026 World Cup matches, group-stage standings, and knockout brackets.

The project combines a Flask backend, an XGBoost match outcome model, and a React/Vite frontend. The model predicts three outcomes for a fixture: Team 1 win, draw, or Team 2 win.

## Features

- Single-match prediction with win/draw/loss probabilities
- Predicted scoreline and short explanation
- 2026 World Cup group-stage simulator
- Group standings with manual score overrides
- 32-team knockout bracket simulator
- Monte Carlo tournament probability table
- Historical model training pipeline using international match results

## Tech Stack

- Backend: Python, Flask, XGBoost, scikit-learn, pandas
- Frontend: React, Vite
- Data: historical international football results from `data/results.csv`

## Project Structure

```text
backend/
  app.py                  Flask API server
  predictor.py            Prediction, group-stage, and bracket simulation logic
  feature_engineering.py  Data loading, Elo, form, and model feature generation
  train.py                Model training script
  artifacts/              Saved trained model artifacts

frontend/
  src/                    React app source
  package.json            Frontend dependencies and scripts

data/
  results.csv             International football results dataset

backtest_2022.py          World Cup backtesting helper
generate_report.py        Static report generator
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train.py
python app.py
```

The Flask API runs on `http://localhost:5001`.

### Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on `http://localhost:3000` and proxies `/api` requests to the Flask backend.

## API Endpoints

- `GET /api/health`
- `GET /api/teams`
- `GET /api/model-info`
- `POST /api/predict`
- `GET /api/bracket/seeds`
- `POST /api/bracket/simulate`
- `GET /api/group-stage/groups`
- `POST /api/group-stage/simulate`

## Model Notes

The model is trained chronologically on historical international football matches. Features include Elo rating, recent form, average goals scored/conceded, goal difference, head-to-head history, and neutral venue status.

The current app uses a static estimated 2026 World Cup team/group setup in `backend/predictor.py`. Predictions are probabilistic estimates and should not be treated as guarantees.

## Backtesting

Run a World Cup backtest:

```bash
python3 backtest_2022.py 2022
```

Supported years are defined inside `backtest_2022.py`.

## Static Report

Generate a local HTML report:

```bash
python3 generate_report.py
```

