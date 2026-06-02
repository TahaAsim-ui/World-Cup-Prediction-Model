"""
Backtests the model against any FIFA World Cup.
Trains entirely on pre-tournament data, then predicts all matches.
Does NOT affect the main model.

Run: python3 backtest_2022.py [year]
  python3 backtest_2022.py       → 2022 World Cup
  python3 backtest_2022.py 2014  → 2014 World Cup
  python3 backtest_2022.py 2018  → 2018 World Cup
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import pandas as pd
import numpy as np
import xgboost as xgb
from feature_engineering import load_data, build_training_data, get_prediction_features

# World Cup date ranges and knockout start dates
WC_DATES = {
    2014: ('2014-06-12', '2014-07-14', '2014-06-29'),
    2018: ('2018-06-14', '2018-07-16', '2018-06-30'),
    2022: ('2022-11-20', '2022-12-19', '2022-12-03'),
}

year = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
if year not in WC_DATES:
    print(f"Unknown year {year}. Available: {list(WC_DATES.keys())}")
    sys.exit(1)

wc_start_str, wc_end_str, ko_start_str = WC_DATES[year]
WC_START       = pd.Timestamp(wc_start_str)
WC_END         = pd.Timestamp(wc_end_str)
KNOCKOUT_START = pd.Timestamp(ko_start_str)

print("=" * 70)
print(f"  {year} FIFA World Cup — Model Backtest")
print(f"  Training cutoff: {WC_START.date()}  |  Test: all WC matches")
print("=" * 70)

# ── Load & split data ─────────────────────────────────────────────────────────
print("\nLoading data...")
df_all = load_data()

df_train = df_all[df_all['date'] < WC_START].copy()
df_wc    = df_all[
    (df_all['date'] >= WC_START) &
    (df_all['date'] <= WC_END) &
    (df_all['tournament'].str.contains('World Cup', na=False))
].copy().reset_index(drop=True)

print(f"Training samples : {len(df_train):,} matches (up to {WC_START.date()})")
print(f"2022 WC matches  : {len(df_wc)}")

# ── Train temporary model ────────────────────────────────────────────────────
print("\nBuilding features from pre-2022 data (may take ~30 s)...")
X, y, elo, team_history, h2h_history, _, xg_history, opp_elo_hist = build_training_data(df_train)

# Proper split: train 70%, val 15%, test 15% (chronological)
n = len(X)
t1, t2 = int(n * 0.70), int(n * 0.85)
X_tr, X_val, X_te = X.iloc[:t1], X.iloc[t1:t2], X.iloc[t2:]
y_tr, y_val, y_te = y[:t1], y[t1:t2], y[t2:]

print(f"Train/Val/Test split: {len(X_tr):,} / {len(X_val):,} / {len(X_te):,}")

model = xgb.XGBClassifier(
    n_estimators=500, max_depth=5, learning_rate=0.04,
    subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
    gamma=0.1, eval_metric='mlogloss', early_stopping_rounds=30,
    random_state=42, n_jobs=-1,
)
model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)

from sklearn.metrics import accuracy_score
held_out_acc = accuracy_score(y_te, model.predict(X_te))
print(f"Held-out accuracy (pre-WC data): {held_out_acc:.4f} ({held_out_acc*100:.1f}%)")

# ── Predict all 64 WC 2022 matches ───────────────────────────────────────────
print("\nPredicting all WC 2022 matches...\n")

records = []
skipped = []

for _, row in df_wc.iterrows():
    home = row['home_team']
    away = row['away_team']
    hs   = int(row['home_score'])
    as_  = int(row['away_score'])
    date = row['date']
    is_knockout = date >= KNOCKOUT_START

    if home not in elo or away not in elo:
        skipped.append(f"{home} vs {away}")
        continue

    X_pred, _, _, _ = get_prediction_features(home, away, elo, team_history, h2h_history,
                                               xg_history=xg_history, opp_elo_hist=opp_elo_hist)
    proba = model.predict_proba(X_pred)[0]
    p_away, p_draw, p_home = float(proba[0]), float(proba[1]), float(proba[2])

    # Predicted winner (3-class)
    if p_home >= p_draw and p_home >= p_away:
        predicted = 'home'
    elif p_away >= p_draw:
        predicted = 'away'
    else:
        predicted = 'draw'

    # Actual result
    if hs > as_:
        actual = 'home'
    elif hs < as_:
        actual = 'away'
    else:
        actual = 'draw'   # includes pens in knockout

    # For knockout draws: who the model would have picked if forced
    if is_knockout and actual == 'draw':
        # Went to penalties — model's binary pick
        model_ko_pick = home if p_home >= p_away else away
        actual_ko_winner = None  # we don't parse pens from this data
        went_to_pens = True
    else:
        model_ko_pick   = None
        actual_ko_winner = None
        went_to_pens    = False

    correct = (predicted == actual)

    # Flag big upsets: underdog (< 35% win chance) actually won
    if actual == 'home' and p_home < 0.35:
        upset_label = 'UPSET'
    elif actual == 'away' and p_away < 0.35:
        upset_label = 'UPSET'
    else:
        upset_label = ''

    records.append(dict(
        date=date.strftime('%b %d'),
        stage='Knockout' if is_knockout else 'Group',
        home=home, away=away,
        score=f"{hs}–{as_}",
        actual=actual, predicted=predicted,
        p_home=round(p_home*100,1),
        p_draw=round(p_draw*100,1),
        p_away=round(p_away*100,1),
        correct=correct,
        went_to_pens=went_to_pens,
        upset=upset_label,
        elo_home=round(elo.get(home,1500)),
        elo_away=round(elo.get(away,1500)),
    ))

# ── Summary stats ─────────────────────────────────────────────────────────────
total    = len(records)
correct  = sum(r['correct'] for r in records)
group_r  = [r for r in records if r['stage']=='Group']
ko_r     = [r for r in records if r['stage']=='Knockout']
upsets   = [r for r in records if r['upset']=='UPSET']
pens_r   = [r for r in records if r['went_to_pens']]

g_correct  = sum(r['correct'] for r in group_r)
ko_correct = sum(r['correct'] for r in ko_r)

print("=" * 70)
print(f"  OVERALL ACCURACY       {correct:2}/{total}   ({correct/total*100:.1f}%)")
print(f"  Group stage            {g_correct:2}/{len(group_r)}  ({g_correct/len(group_r)*100:.1f}%)")
print(f"  Knockout stage         {ko_correct:2}/{len(ko_r)}  ({ko_correct/len(ko_r)*100:.1f}%)")
print(f"  Matches to penalties   {len(pens_r)} (result = draw in data; model can't predict pens)")
print(f"  Upsets (underdog won)  {len(upsets)}")
print("=" * 70)

# ── Group stage results ───────────────────────────────────────────────────────
print("\n── GROUP STAGE ──────────────────────────────────────────────────────")
print(f"{'Date':<8} {'Home':<22} {'Score':<7} {'Away':<22} {'Probs H/D/A':<22} {'Pred':<6} {'Act':<5} {''}")
print("-" * 100)
for r in group_r:
    tick = '✓' if r['correct'] else ('⚠ '+r['upset'] if r['upset'] else '✗')
    probs = f"{r['p_home']}%/{r['p_draw']}%/{r['p_away']}%"
    print(f"{r['date']:<8} {r['home']:<22} {r['score']:<7} {r['away']:<22} {probs:<22} {r['predicted']:<6} {r['actual']:<5} {tick}")

# ── Knockout results ──────────────────────────────────────────────────────────
print("\n── KNOCKOUT STAGE ───────────────────────────────────────────────────")
print(f"{'Date':<8} {'Home':<22} {'Score':<7} {'Away':<22} {'Probs H/D/A':<22} {'Pred':<6} {'Act':<5} {''}")
print("-" * 100)
for r in ko_r:
    note = '(pens)' if r['went_to_pens'] else ''
    tick = '✓' if r['correct'] else ('⚠ '+r['upset'] if r['upset'] else '✗')
    if r['went_to_pens']:
        tick = f"~ pens"
    probs = f"{r['p_home']}%/{r['p_draw']}%/{r['p_away']}%"
    print(f"{r['date']:<8} {r['home']:<22} {r['score']:<7} {r['away']:<22} {probs:<22} {r['predicted']:<6} {r['actual']:<5} {tick}")

# ── Upsets the model missed ───────────────────────────────────────────────────
missed_upsets = [r for r in upsets if not r['correct']]
print(f"\n── UPSETS THE MODEL MISSED ({len(missed_upsets)}) ────────────────────────────────")
for r in missed_upsets:
    winner = r['home'] if r['actual']=='home' else r['away']
    loser  = r['away'] if r['actual']=='home' else r['home']
    wp = r['p_home'] if r['actual']=='home' else r['p_away']
    print(f"  {r['date']}  {winner} beat {loser}  (model gave {winner} only {wp}% chance)  {r['score']}")

# ── Upsets model DID predict ──────────────────────────────────────────────────
called_upsets = [r for r in upsets if r['correct']]
if called_upsets:
    print(f"\n── UPSETS THE MODEL CALLED ({len(called_upsets)}) ─────────────────────────────────")
    for r in called_upsets:
        winner = r['home'] if r['actual']=='home' else r['away']
        wp = r['p_home'] if r['actual']=='home' else r['p_away']
        print(f"  {r['date']}  {winner}  ({winner} had {wp}% — still an upset but model was closer)")

if skipped:
    print(f"\nSkipped (teams not in pre-2022 Elo): {', '.join(skipped)}")

print("\nDone. No changes made to the main model.\n")
