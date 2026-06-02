"""
Fetches xG, shots, and shots-on-target from StatsBomb Open Data
for 5 major international competitions.

Run: python3 backend/fetch_xg.py
Saves: data/xg_data.csv  (~270 matches)
"""
import sys, warnings
warnings.filterwarnings('ignore')
from pathlib import Path
import pandas as pd
from statsbombpy import sb

OUTPUT = Path(__file__).parent.parent / 'data' / 'xg_data.csv'

# Every international competition available in StatsBomb open data with xG
COMPETITIONS = [
    (43, 106, 'FIFA World Cup 2022'),
    (43,   3, 'FIFA World Cup 2018'),
    (55,  43, 'UEFA Euro 2020'),
    (55, 282, 'UEFA Euro 2024'),
    (223, 282, 'Copa America 2024'),
]

# Normalise StatsBomb team names → names used in our results.csv
NAME_MAP = {
    "United States Men's": "United States",
    "Korea Republic":      "South Korea",
    "IR Iran":             "Iran",
    "Côte d'Ivoire":       "Ivory Coast",
    "Türkiye":             "Turkey",
    "Bosnia and Herzegovi": "Bosnia and Herzegovina",
}

def norm(name):
    return NAME_MAP.get(name, name)


def match_xg(match_id):
    """Aggregate shot_statsbomb_xg, shots, and shots on target per team."""
    try:
        events = sb.events(match_id=match_id)
        shots = events[events['type'] == 'Shot'].copy()
        out = {}
        for team, grp in shots.groupby('team'):
            on_target = grp['shot_outcome'].isin(
                ['Goal', 'Saved', 'Saved to Post']
            ).sum() if 'shot_outcome' in grp.columns else 0
            out[norm(team)] = {
                'xg':  round(float(grp['shot_statsbomb_xg'].sum()), 4),
                'shots': int(len(grp)),
                'sot':   int(on_target),
            }
        return out
    except Exception:
        return {}


records = []

for comp_id, season_id, label in COMPETITIONS:
    print(f"\n{label}")
    try:
        matches = sb.matches(competition_id=comp_id, season_id=season_id)
        print(f"  {len(matches)} matches — fetching events...")
        for n, (_, row) in enumerate(matches.iterrows(), 1):
            home = norm(row['home_team'])
            away = norm(row['away_team'])
            xg   = match_xg(row['match_id'])
            h    = xg.get(home, {})
            a    = xg.get(away, {})
            records.append({
                'date':       row['match_date'],
                'home_team':  home,
                'away_team':  away,
                'home_score': row['home_score'],
                'away_score': row['away_score'],
                'competition': label,
                'home_xg':    h.get('xg'),
                'away_xg':    a.get('xg'),
                'home_shots': h.get('shots'),
                'away_shots': a.get('shots'),
                'home_sot':   h.get('sot'),
                'away_sot':   a.get('sot'),
            })
            print(f"  [{n:3}/{len(matches)}] {home} vs {away}  "
                  f"xG {h.get('xg','?'):.2f}–{a.get('xg','?'):.2f}", end='\r')
        print(f"\n  Done ✓")
    except Exception as e:
        print(f"\n  Error: {e}")

df = pd.DataFrame(records)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)
df.to_csv(OUTPUT, index=False)

print(f"\n{'='*60}")
print(f"Saved {len(df)} matches to {OUTPUT}")
print(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
print(f"\nSample:")
print(df[['date','home_team','away_team','home_xg','away_xg','home_shots','away_shots']].tail(10).to_string(index=False))
