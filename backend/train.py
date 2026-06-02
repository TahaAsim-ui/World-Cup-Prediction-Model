"""
Run this script once before starting the Flask server:
    cd backend && python train.py
"""
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

from feature_engineering import download_data, load_data, build_training_data

ARTIFACTS_DIR = Path(__file__).parent / 'artifacts'


def train():
    print("=== World Cup AI Match Predictor — Training ===\n")

    download_data()

    print("Loading and preprocessing data...")
    df = load_data()
    print(f"Loaded {len(df):,} matches ({df['date'].min().year}–{df['date'].max().year})")

    print("Building features from match history (may take ~30 seconds)...")
    # Elo is computed across ALL history (1872 onward) for accurate calibration.
    # XGBoost training samples are restricted to 2000+ to avoid learning
    # patterns from an era when football was a genuinely different sport.
    X, y, elo, team_history, h2h_history, all_teams, xg_history, opp_elo_hist = \
        build_training_data(df, training_start_year=2000)
    print(f"Feature matrix: {X.shape[0]:,} samples × {X.shape[1]} features")
    print(f"(Elo computed on all {len(df):,} matches; XGBoost trains on post-2000 rows only)")
    xg_coverage = sum(1 for v in X['team1_avg_xg_for'] if pd.notna(v))
    print(f"Rows with xG data: {xg_coverage:,} / {len(X):,} ({xg_coverage/len(X)*100:.1f}%)")

    dist = {v: round(np.mean(y == v) * 100, 1) for v in [0, 1, 2]}
    print(f"Class balance — Team1 Win: {dist[2]}%  Draw: {dist[1]}%  Team2 Win: {dist[0]}%")

    # ── 3-way chronological split ─────────────────────────────────────────────
    # Train  70 % — model sees this
    # Val    15 % — used ONLY for early stopping, never for accuracy reporting
    # Test   15 % — completely held out; reported accuracy is honest
    n = len(X)
    t1 = int(n * 0.70)
    t2 = int(n * 0.85)

    X_train, X_val, X_test = X.iloc[:t1], X.iloc[t1:t2], X.iloc[t2:]
    y_train, y_val, y_test = y[:t1],      y[t1:t2],      y[t2:]

    print(f"\nSplit — Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # ── Train ─────────────────────────────────────────────────────────────────
    print("Training XGBoost classifier...")
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.04,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        eval_metric='mlogloss',
        early_stopping_rounds=30,
        random_state=42,
        n_jobs=-1,
    )

    # Val set drives early stopping — test set is never touched during training
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    # ── Evaluate on the truly held-out test set ───────────────────────────────
    y_pred = model.predict(X_test)
    test_acc = accuracy_score(y_test, y_pred)
    print(f"\nHeld-out Test Accuracy: {test_acc:.4f} ({test_acc*100:.1f}%)")
    print("(Early stopping used validation set — test set was never seen during training)\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Team2 Win', 'Draw', 'Team1 Win']))

    importances = model.feature_importances_
    feature_names = X.columns.tolist()
    top_idx = np.argsort(importances)[::-1][:6]
    print("Top Feature Importances:")
    for i in top_idx:
        print(f"  {feature_names[i]:<25} {importances[i]:.4f}")

    # ── Save ──────────────────────────────────────────────────────────────────
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    artifacts = {
        'model': model,
        'elo': elo,
        'team_history': team_history,
        'h2h_history': h2h_history,
        'all_teams': all_teams,
        'feature_names': feature_names,
        'xg_history': xg_history,
        'opp_elo_hist': opp_elo_hist,
        'test_accuracy': round(test_acc * 100, 1),
        'n_matches': len(df),
        'year_range': f"{df['date'].min().year}–{df['date'].max().year}",
    }

    out_path = ARTIFACTS_DIR / 'model_artifacts.pkl'
    with open(out_path, 'wb') as f:
        pickle.dump(artifacts, f)

    print(f"\nModel artifacts saved to {out_path}")
    print(f"Teams in model: {len(all_teams)}")
    print("\nTraining complete. You can now start the Flask server.")


if __name__ == '__main__':
    train()
