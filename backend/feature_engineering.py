import pandas as pd
import numpy as np
import requests
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / 'data'
DATA_FILE = DATA_DIR / 'results.csv'
XG_FILE   = DATA_DIR / 'xg_data.csv'
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"


def download_data():
    DATA_DIR.mkdir(exist_ok=True)
    if DATA_FILE.exists():
        print("Data already exists, skipping download.")
        return
    print("Downloading international football results dataset...")
    r = requests.get(RESULTS_URL, timeout=60)
    r.raise_for_status()
    DATA_FILE.write_bytes(r.content)
    print(f"Downloaded {len(r.content) / 1024:.0f} KB to {DATA_FILE}")


def load_data():
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    df = df.dropna(subset=['home_score', 'away_score'])
    df['home_score'] = df['home_score'].astype(int)
    df['away_score'] = df['away_score'].astype(int)
    df = df.sort_values('date').reset_index(drop=True)
    return df


def _load_xg_lookup():
    """Load StatsBomb xG data keyed by (date_str, home, away)."""
    if not XG_FILE.exists():
        return {}
    xg = pd.read_csv(XG_FILE)
    xg['date'] = pd.to_datetime(xg['date'])
    lookup = {}
    for _, row in xg.iterrows():
        key = (row['date'].strftime('%Y-%m-%d'), row['home_team'], row['away_team'])
        lookup[key] = row
    return lookup


# ── Helper functions ──────────────────────────────────────────────────────────

def _default_form():
    return {'win_rate': 0.35, 'draw_rate': 0.25, 'avg_gf': 1.3, 'avg_ga': 1.3,
            'goal_diff': 0.0, 'n': 0}


def _compute_form(history):
    if not history:
        return _default_form()
    n = len(history)
    wins  = sum(1 for gf, ga in history if gf > ga)
    draws = sum(1 for gf, ga in history if gf == ga)
    avg_gf = sum(gf for gf, ga in history) / n
    avg_ga = sum(ga for gf, ga in history) / n
    return {'win_rate': wins / n, 'draw_rate': draws / n,
            'avg_gf': avg_gf, 'avg_ga': avg_ga,
            'goal_diff': avg_gf - avg_ga, 'n': n}


def _compute_weighted_form(history, n=10):
    """Win rate weighted so the most recent match counts n× the oldest."""
    recent = history[-n:]
    if not recent:
        return 0.35
    total_w = won_w = 0.0
    for i, (gf, ga) in enumerate(recent):
        w = float(i + 1)          # weight 1 for oldest, n for newest
        total_w += w
        if gf > ga:
            won_w += w
    return won_w / total_w if total_w else 0.35


def _compute_consistency(history, n=10):
    """Std-dev of goal difference in last n matches (lower = more predictable)."""
    recent = history[-n:]
    if len(recent) < 3:
        return 1.5   # neutral/average value
    return float(np.std([gf - ga for gf, ga in recent]))


def _compute_xg_form(xg_history, n=10):
    """Rolling average xG-for and xG-against."""
    recent = xg_history[-n:]
    if not recent:
        return None, None
    return (sum(xf for xf, xa in recent) / len(recent),
            sum(xa for xf, xa in recent) / len(recent))


def _compute_h2h(history, team1_is_first):
    if not history:
        return {'win_rate': 0.33, 'draw_rate': 0.34, 'loss_rate': 0.33, 'n': 0}
    n = len(history)
    wins = draws = losses = 0
    for gf, ga in history:
        if not team1_is_first:
            gf, ga = ga, gf
        if gf > ga:      wins   += 1
        elif gf == ga:   draws  += 1
        else:            losses += 1
    return {'win_rate': wins / n, 'draw_rate': draws / n,
            'loss_rate': losses / n, 'n': n}


def _k_factor(tournament: str) -> float:
    t = tournament.lower()
    if 'world cup' in t:  return 40.0
    if 'friendly'  in t:  return 15.0
    return 25.0


# ── Core training-data builder ────────────────────────────────────────────────

def build_training_data(df, initial_elo=1500, n_form=10, elo_decay=0.97,
                        training_start_year=2000):
    """
    Processes matches chronologically, maintaining running state for:
      • Elo ratings (all history from 1872, with annual decay)
      • Form stats  (last n_form goals, wins, draws)
      • Strength-of-schedule (opponent Elo history)
      • xG stats    (from StatsBomb data where available)

    XGBoost training rows are restricted to training_start_year+ to avoid
    learning patterns from eras when football was a different sport.
    """
    xg_lookup = _load_xg_lookup()
    has_xg = bool(xg_lookup)
    if has_xg:
        print(f"  xG data loaded: {len(xg_lookup)} matches")

    elo          = {}
    team_history = {}    # team -> [(gf, ga), ...]
    opp_elo_hist = {}    # team -> [opponent_elo, ...]  (for SOS)
    xg_history   = {}    # team -> [(xg_for, xg_against), ...]
    h2h_history  = {}

    features_list = []
    labels        = []
    current_year  = None

    for idx, row in df.iterrows():
        home       = row['home_team']
        away       = row['away_team']
        hs         = int(row['home_score'])
        as_        = int(row['away_score'])
        neutral    = bool(row.get('neutral', False))
        tournament = str(row.get('tournament', ''))
        match_year = row['date'].year
        date_str   = row['date'].strftime('%Y-%m-%d')

        # ── Annual Elo decay ──────────────────────────────────────────────────
        if current_year is None:
            current_year = match_year
        elif match_year > current_year:
            for _ in range(match_year - current_year):
                for t in elo:
                    elo[t] = 1500.0 + (elo[t] - 1500.0) * elo_decay
            current_year = match_year

        elo_home = elo.get(home, initial_elo)
        elo_away = elo.get(away, initial_elo)

        # ── Look up pre-match form ────────────────────────────────────────────
        home_hist = team_history.get(home, [])[-n_form:]
        away_hist = team_history.get(away, [])[-n_form:]

        h2h_key      = tuple(sorted([home, away]))
        home_is_first = home <= away
        h2h_hist     = h2h_history.get(h2h_key, [])[-n_form:]

        home_form = _compute_form(home_hist)
        away_form = _compute_form(away_hist)
        h2h       = _compute_h2h(h2h_hist, home_is_first)

        # Strength of schedule: average Elo of last N opponents
        sos_home = (sum(opp_elo_hist.get(home, [])[-n_form:]) /
                    len(opp_elo_hist.get(home, [])[-n_form:])
                    if opp_elo_hist.get(home) else 1500.0)
        sos_away = (sum(opp_elo_hist.get(away, [])[-n_form:]) /
                    len(opp_elo_hist.get(away, [])[-n_form:])
                    if opp_elo_hist.get(away) else 1500.0)

        # Weighted form & consistency
        wform_home = _compute_weighted_form(home_hist, n_form)
        wform_away = _compute_weighted_form(away_hist, n_form)
        cons_home  = _compute_consistency(home_hist, n_form)
        cons_away  = _compute_consistency(away_hist, n_form)

        # xG rolling averages
        xgf_home, xga_home = _compute_xg_form(xg_history.get(home, []), n_form)
        xgf_away, xga_away = _compute_xg_form(xg_history.get(away, []), n_form)

        # ── Build feature row ─────────────────────────────────────────────────
        if idx >= 200 and match_year >= training_start_year:
            features_list.append({
                # Original 17 features
                'elo_diff':            elo_home - elo_away,
                'team1_elo':           elo_home,
                'team2_elo':           elo_away,
                'team1_win_rate':      home_form['win_rate'],
                'team2_win_rate':      away_form['win_rate'],
                'team1_draw_rate':     home_form['draw_rate'],
                'team2_draw_rate':     away_form['draw_rate'],
                'team1_avg_gf':        home_form['avg_gf'],
                'team2_avg_gf':        away_form['avg_gf'],
                'team1_avg_ga':        home_form['avg_ga'],
                'team2_avg_ga':        away_form['avg_ga'],
                'team1_goal_diff':     home_form['goal_diff'],
                'team2_goal_diff':     away_form['goal_diff'],
                'h2h_team1_win_rate':  h2h['win_rate'],
                'h2h_draw_rate':       h2h['draw_rate'],
                'h2h_team2_win_rate':  h2h['loss_rate'],
                'is_neutral':          int(neutral),
                # New: Strength of Schedule
                'sos_team1':           sos_home,
                'sos_team2':           sos_away,
                # New: Weighted recency form
                'team1_weighted_form': wform_home,
                'team2_weighted_form': wform_away,
                # New: Consistency (lower = more predictable)
                'team1_consistency':   cons_home,
                'team2_consistency':   cons_away,
                # New: xG features (NaN when no StatsBomb data for this team)
                'team1_avg_xg_for':    xgf_home if xgf_home is not None else np.nan,
                'team2_avg_xg_for':    xgf_away if xgf_away is not None else np.nan,
                'team1_avg_xg_against':xga_home if xga_home is not None else np.nan,
                'team2_avg_xg_against':xga_away if xga_away is not None else np.nan,
                'team1_xg_diff':       (xgf_home - xga_home) if xgf_home is not None else np.nan,
                'team2_xg_diff':       (xgf_away - xga_away) if xgf_away is not None else np.nan,
            })
            if hs > as_:  labels.append(2)
            elif hs==as_: labels.append(1)
            else:         labels.append(0)

        # ── Update Elo ────────────────────────────────────────────────────────
        exp_home = 1.0 / (1.0 + 10.0 ** ((elo_away - elo_home) / 400.0))
        s_home   = 1.0 if hs > as_ else (0.5 if hs == as_ else 0.0)
        k        = _k_factor(tournament)
        elo[home] = elo_home + k * (s_home - exp_home)
        elo[away] = elo_away + k * ((1 - s_home) - (1 - exp_home))

        # ── Update histories ──────────────────────────────────────────────────
        team_history.setdefault(home, []).append((hs, as_))
        team_history.setdefault(away, []).append((as_, hs))

        opp_elo_hist.setdefault(home, []).append(elo_away)
        opp_elo_hist.setdefault(away, []).append(elo_home)

        if home_is_first:
            h2h_history.setdefault(h2h_key, []).append((hs, as_))
        else:
            h2h_history.setdefault(h2h_key, []).append((as_, hs))

        # Update xG history if StatsBomb data exists for this match
        xg_key = (date_str, home, away)
        if xg_key in xg_lookup:
            xgr = xg_lookup[xg_key]
            if pd.notna(xgr.get('home_xg')) and pd.notna(xgr.get('away_xg')):
                xg_history.setdefault(home, []).append(
                    (float(xgr['home_xg']), float(xgr['away_xg'])))
                xg_history.setdefault(away, []).append(
                    (float(xgr['away_xg']), float(xgr['home_xg'])))

    X         = pd.DataFrame(features_list)
    y         = np.array(labels)
    all_teams = sorted(elo.keys())

    return X, y, elo, team_history, h2h_history, all_teams, xg_history, opp_elo_hist


def get_prediction_features(team1, team2, elo, team_history, h2h_history,
                             xg_history=None, opp_elo_hist=None, n_form=10):
    elo1 = elo.get(team1, 1500)
    elo2 = elo.get(team2, 1500)

    hist1 = team_history.get(team1, [])[-n_form:]
    hist2 = team_history.get(team2, [])[-n_form:]

    form1 = _compute_form(hist1)
    form2 = _compute_form(hist2)

    h2h_key      = tuple(sorted([team1, team2]))
    team1_is_first = team1 <= team2
    h2h_hist     = h2h_history.get(h2h_key, [])[-n_form:]
    h2h          = _compute_h2h(h2h_hist, team1_is_first)

    sos1 = (sum((opp_elo_hist or {}).get(team1, [])[-n_form:]) /
            len((opp_elo_hist or {}).get(team1, [])[-n_form:])
            if (opp_elo_hist or {}).get(team1) else 1500.0)
    sos2 = (sum((opp_elo_hist or {}).get(team2, [])[-n_form:]) /
            len((opp_elo_hist or {}).get(team2, [])[-n_form:])
            if (opp_elo_hist or {}).get(team2) else 1500.0)

    wform1 = _compute_weighted_form(hist1, n_form)
    wform2 = _compute_weighted_form(hist2, n_form)
    cons1  = _compute_consistency(hist1, n_form)
    cons2  = _compute_consistency(hist2, n_form)

    xgf1, xga1 = _compute_xg_form((xg_history or {}).get(team1, []), n_form)
    xgf2, xga2 = _compute_xg_form((xg_history or {}).get(team2, []), n_form)

    X = pd.DataFrame([{
        'elo_diff':            elo1 - elo2,
        'team1_elo':           elo1,
        'team2_elo':           elo2,
        'team1_win_rate':      form1['win_rate'],
        'team2_win_rate':      form2['win_rate'],
        'team1_draw_rate':     form1['draw_rate'],
        'team2_draw_rate':     form2['draw_rate'],
        'team1_avg_gf':        form1['avg_gf'],
        'team2_avg_gf':        form2['avg_gf'],
        'team1_avg_ga':        form1['avg_ga'],
        'team2_avg_ga':        form2['avg_ga'],
        'team1_goal_diff':     form1['goal_diff'],
        'team2_goal_diff':     form2['goal_diff'],
        'h2h_team1_win_rate':  h2h['win_rate'],
        'h2h_draw_rate':       h2h['draw_rate'],
        'h2h_team2_win_rate':  h2h['loss_rate'],
        'is_neutral':          1,
        'sos_team1':           sos1,
        'sos_team2':           sos2,
        'team1_weighted_form': wform1,
        'team2_weighted_form': wform2,
        'team1_consistency':   cons1,
        'team2_consistency':   cons2,
        'team1_avg_xg_for':    xgf1 if xgf1 is not None else np.nan,
        'team2_avg_xg_for':    xgf2 if xgf2 is not None else np.nan,
        'team1_avg_xg_against':xga1 if xga1 is not None else np.nan,
        'team2_avg_xg_against':xga2 if xga2 is not None else np.nan,
        'team1_xg_diff':       (xgf1 - xga1) if xgf1 is not None else np.nan,
        'team2_xg_diff':       (xgf2 - xga2) if xgf2 is not None else np.nan,
    }])

    return X, form1, form2, h2h


def generate_explanation(team1, team2, elo, form1, form2, h2h):
    elo1 = elo.get(team1, 1500)
    elo2 = elo.get(team2, 1500)
    elo_diff = elo1 - elo2
    parts = []

    if abs(elo_diff) > 150:
        stronger = team1 if elo_diff > 0 else team2
        weaker   = team2 if elo_diff > 0 else team1
        parts.append(
            f"{stronger} holds a clear Elo rating advantage of {abs(elo_diff):.0f} points over {weaker}, "
            f"reflecting stronger historical performance.")
    elif abs(elo_diff) > 60:
        stronger = team1 if elo_diff > 0 else team2
        parts.append(f"{stronger} has a slight Elo edge ({abs(elo_diff):.0f} points), "
                     f"suggesting marginally stronger historical results.")
    else:
        parts.append(f"Both teams are very closely matched on Elo rating "
                     f"(gap of {abs(elo_diff):.0f} points), making this fixture hard to call.")

    form_diff = form1['win_rate'] - form2['win_rate']
    if abs(form_diff) > 0.2:
        in_form = team1 if form_diff > 0 else team2
        parts.append(f"{in_form} has been in significantly better recent form.")
    elif abs(form_diff) > 0.1:
        in_form = team1 if form_diff > 0 else team2
        parts.append(f"{in_form} shows slightly better recent form.")

    if form1['avg_gf'] > form2['avg_gf'] + 0.35:
        parts.append(f"{team1} averages more goals per match ({form1['avg_gf']:.1f} vs {form2['avg_gf']:.1f}).")
    elif form2['avg_gf'] > form1['avg_gf'] + 0.35:
        parts.append(f"{team2} averages more goals per match ({form2['avg_gf']:.1f} vs {form1['avg_gf']:.1f}).")

    if form1['avg_ga'] < form2['avg_ga'] - 0.3:
        parts.append(f"{team1} has the stronger defensive record, conceding fewer goals on average.")
    elif form2['avg_ga'] < form1['avg_ga'] - 0.3:
        parts.append(f"{team2} has the stronger defensive record, conceding fewer goals on average.")

    if h2h['n'] >= 3:
        if h2h['win_rate'] > 0.5:
            parts.append(f"{team1} dominates the head-to-head "
                         f"({h2h['win_rate']*100:.0f}% win rate in recent meetings).")
        elif h2h['loss_rate'] > 0.5:
            parts.append(f"{team2} dominates the head-to-head "
                         f"({h2h['loss_rate']*100:.0f}% win rate in recent meetings).")
        elif h2h['draw_rate'] > 0.4:
            parts.append("Recent head-to-head meetings have been tight, with frequent draws.")

    return (" ".join(parts) if parts else
            "This is a competitive match where both teams have broadly similar historical strength.")
