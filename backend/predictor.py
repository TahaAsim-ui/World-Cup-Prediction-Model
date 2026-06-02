import pickle
import numpy as np
from pathlib import Path
from feature_engineering import get_prediction_features, generate_explanation, _compute_form

ARTIFACTS_PATH = Path(__file__).parent / 'artifacts' / 'model_artifacts.pkl'

# All 48 qualified teams for the 2026 World Cup
WC_2026_TEAMS = [
    'Argentina', 'France', 'Spain', 'England', 'Brazil', 'Portugal',
    'Netherlands', 'Germany', 'Belgium', 'Croatia', 'Denmark', 'Switzerland',
    'Uruguay', 'Morocco', 'Colombia', 'Ecuador', 'Mexico', 'United States',
    'South Korea', 'Japan', 'Australia', 'Serbia', 'Austria', 'Turkey',
    'Senegal', 'Nigeria', 'Ghana', 'Venezuela', 'Poland', 'Panama',
    'Saudi Arabia', 'Ivory Coast', 'Tunisia', 'Cameroon', 'Egypt',
    'South Africa', 'Iraq', 'Jordan', 'Honduras', 'Costa Rica', 'Scotland',
    'Albania', 'Paraguay', 'Indonesia', 'Uzbekistan', 'New Zealand',
    'Canada', 'Iran',
]

_ROUND_NAMES  = ['R32', 'R16', 'Quarterfinals', 'Semifinals', 'Final']
_TRACK_LABELS = ['R16', 'Quarterfinals', 'Semifinals', 'Final', 'Champion']

# 2026 World Cup groups (estimated based on seeding / confederation rules)
GROUPS = {
    'A': ['Spain',       'United States', 'Senegal',      'Iraq'],
    'B': ['Argentina',   'Mexico',        'Nigeria',       'Jordan'],
    'C': ['France',      'Canada',        'Ghana',         'Honduras'],
    'D': ['England',     'Uruguay',       'Poland',        'Scotland'],
    'E': ['Brazil',      'Colombia',      'Venezuela',     'Indonesia'],
    'F': ['Portugal',    'Morocco',       'Saudi Arabia',  'Paraguay'],
    'G': ['Netherlands', 'Japan',         'Cameroon',      'Costa Rica'],
    'H': ['Germany',     'Ecuador',       'Ivory Coast',   'Albania'],
    'I': ['Belgium',     'South Korea',   'Tunisia',       'New Zealand'],
    'J': ['Croatia',     'Australia',     'South Africa',  'Uzbekistan'],
    'K': ['Denmark',     'Serbia',        'Iran',          'Panama'],
    'L': ['Switzerland', 'Austria',       'Turkey',        'Egypt'],
}
# Standard round-robin schedule for a 4-team group (index pairs)
_GS_SCHEDULE = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]


class MatchPredictor:
    def __init__(self):
        if not ARTIFACTS_PATH.exists():
            raise FileNotFoundError(
                f"Model artifacts not found at {ARTIFACTS_PATH}. "
                "Please run: cd backend && python train.py"
            )
        with open(ARTIFACTS_PATH, 'rb') as f:
            artifacts = pickle.load(f)

        self.model         = artifacts['model']
        self.elo           = artifacts['elo']
        self.team_history  = artifacts['team_history']
        self.h2h_history   = artifacts['h2h_history']
        self.all_teams     = artifacts['all_teams']
        self.feature_names = artifacts['feature_names']
        self.xg_history    = artifacts.get('xg_history', {})
        self.opp_elo_hist  = artifacts.get('opp_elo_hist', {})
        self.test_accuracy = artifacts.get('test_accuracy', 'N/A')
        self.n_matches     = artifacts.get('n_matches', 'N/A')
        self.year_range    = artifacts.get('year_range', 'N/A')

    # ── Single match predictor ────────────────────────────────────────────────

    def get_teams(self):
        return self.all_teams

    def get_model_info(self):
        return {
            'model_type': 'XGBoost Gradient Boosted Classifier',
            'prediction_target': 'Team 1 Win / Draw / Team 2 Win',
            'features': 'Elo rating, recent form (W/D/L), goals scored & conceded, head-to-head record',
            'training_matches': f"{self.n_matches:,}" if isinstance(self.n_matches, int) else self.n_matches,
            'data_range': self.year_range,
            'test_accuracy': f"{self.test_accuracy}%",
        }

    def predict(self, team1: str, team2: str) -> dict:
        if team1 not in self.elo:
            raise ValueError(f"Unknown team: '{team1}'")
        if team2 not in self.elo:
            raise ValueError(f"Unknown team: '{team2}'")
        if team1 == team2:
            raise ValueError("Please select two different teams.")

        X, form1, form2, h2h = get_prediction_features(
            team1, team2, self.elo, self.team_history, self.h2h_history,
            xg_history=self.xg_history, opp_elo_hist=self.opp_elo_hist
        )

        proba = self.model.predict_proba(X)[0]
        p_team2_win = float(proba[0])
        p_draw      = float(proba[1])
        p_team1_win = float(proba[2])

        elo1 = self.elo.get(team1, 1500)
        elo2 = self.elo.get(team2, 1500)

        # Determine predicted winner first, then compute scores
        if p_team1_win >= p_draw and p_team1_win >= p_team2_win:
            predicted_winner = team1
        elif p_team2_win >= p_draw and p_team2_win >= p_team1_win:
            predicted_winner = team2
        else:
            predicted_winner = 'Draw'

        if predicted_winner == 'Draw':
            l1 = max(0.5, (form1['avg_gf'] + form2['avg_ga']) / 2)
            l2 = max(0.5, (form2['avg_gf'] + form1['avg_ga']) / 2)
            draw_goals = max(0, round((l1 + l2) / 2 * 0.65))
            score1 = score2 = draw_goals
        else:
            winner = team1 if predicted_winner == team1 else team2
            score1, score2 = self._match_scores(
                team1, team2, p_team1_win, p_draw, p_team2_win, winner
            )

        explanation = generate_explanation(team1, team2, self.elo, form1, form2, h2h)

        def form_string(form):
            if form['n'] == 0:
                return 'N/A'
            wins   = round(form['win_rate'] * form['n'])
            draws  = round(form['draw_rate'] * form['n'])
            losses = form['n'] - wins - draws
            return f"{wins}W {draws}D {losses}L"

        return {
            'team1': team1, 'team2': team2,
            'team1_win_probability': round(p_team1_win * 100, 1),
            'draw_probability':      round(p_draw      * 100, 1),
            'team2_win_probability': round(p_team2_win * 100, 1),
            'predicted_winner': predicted_winner,
            'score1': score1, 'score2': score2,
            'team1_elo': round(elo1), 'team2_elo': round(elo2),
            'team1_form_string': form_string(form1),
            'team2_form_string': form_string(form2),
            'team1_avg_gf': round(form1['avg_gf'], 2),
            'team2_avg_gf': round(form2['avg_gf'], 2),
            'team1_avg_ga': round(form1['avg_ga'], 2),
            'team2_avg_ga': round(form2['avg_ga'], 2),
            'h2h_n':               h2h['n'],
            'h2h_team1_win_rate':  round(h2h['win_rate']  * 100, 1),
            'h2h_draw_rate':       round(h2h['draw_rate'] * 100, 1),
            'h2h_team2_win_rate':  round(h2h['loss_rate'] * 100, 1),
            'explanation': explanation,
        }

    # ── Bracket engine ────────────────────────────────────────────────────────

    def get_bracket_seeds(self):
        """Top 32 WC 2026 teams by Elo, arranged in standard bracket pairing order."""
        valid = [t for t in WC_2026_TEAMS if t in self.elo]
        valid.sort(key=lambda t: self.elo[t], reverse=True)
        seeded = valid[:32]
        # Standard seeding: match[i] = seed[i] vs seed[31-i]
        bracket_order = []
        for i in range(16):
            bracket_order.append(seeded[i])
            bracket_order.append(seeded[31 - i])
        return {
            'bracket_teams': bracket_order,
            'seedings': {t: i + 1 for i, t in enumerate(seeded)},
            'elo_ratings': {t: round(self.elo[t]) for t in seeded},
        }

    def _get_proba(self, t1, t2, cache):
        """Returns (p1_win, p_draw, p2_win) from cache or model."""
        key = (t1, t2)
        rev = (t2, t1)
        if key in cache:
            p = cache[key]
            return float(p[2]), float(p[1]), float(p[0])
        if rev in cache:
            p = cache[rev]
            return float(p[0]), float(p[1]), float(p[2])
        X, _, _, _ = get_prediction_features(t1, t2, self.elo, self.team_history, self.h2h_history, xg_history=self.xg_history, opp_elo_hist=self.opp_elo_hist)
        proba = self.model.predict_proba(X)[0]
        cache[key] = proba
        return float(proba[2]), float(proba[1]), float(proba[0])

    def _match_scores(self, t1, t2, p1_win, p_draw, p2_win, winner):
        """
        Predict a scoreline driven by win probability, not just expected goals.
        Higher win probability → larger goal margin.
        """
        form1 = _compute_form(self.team_history.get(t1, [])[-10:])
        form2 = _compute_form(self.team_history.get(t2, [])[-10:])

        # Expected goals per team (attack vs opponent defence)
        l1 = max(0.5, (form1['avg_gf'] + form2['avg_ga']) / 2)
        l2 = max(0.5, (form2['avg_gf'] + form1['avg_ga']) / 2)
        total_goals = l1 + l2  # expected combined goals

        # Winner's effective knockout probability (no draws in knockout)
        if winner == t1:
            p_win_eff = p1_win + 0.5 * p_draw
        else:
            p_win_eff = p2_win + 0.5 * p_draw

        # Map win probability → goal margin
        # p=0.50 → 1,  p=0.65 → 2,  p=0.80 → 3,  p=0.93+ → 4
        margin = max(1, round((p_win_eff - 0.5) * 6 + 0.7))

        # Distribute total goals: winner gets the larger share
        winner_goals = max(margin, round((total_goals + margin) / 2))
        loser_goals  = max(0, winner_goals - margin)

        return (winner_goals, loser_goals) if winner == t1 else (loser_goals, winner_goals)

    def _run_bracket(self, bracket_teams, overrides, cache):
        """Deterministic simulation. Returns (rounds_data, champion)."""
        current = list(bracket_teams)
        rounds_data = []

        for round_name in _ROUND_NAMES:
            matches = []
            next_round = []
            n = len(current) // 2
            for i in range(n):
                t1, t2 = current[2 * i], current[2 * i + 1]
                match_id = f"{round_name}-{i}"
                p1_win, p_draw, p2_win = self._get_proba(t1, t2, cache)
                p1_eff = p1_win + 0.5 * p_draw

                if match_id in overrides and overrides[match_id] in (t1, t2):
                    winner = overrides[match_id]
                else:
                    winner = t1 if p1_eff >= 0.5 else t2

                s1, s2 = self._match_scores(t1, t2, p1_win, p_draw, p2_win, winner)
                matches.append({
                    'id': match_id,
                    'team1': t1, 'team2': t2,
                    'score1': s1, 'score2': s2,
                    'winner': winner,
                    'team1_win_prob': round(p1_win * 100, 1),
                    'draw_prob':      round(p_draw  * 100, 1),
                    'team2_win_prob': round(p2_win  * 100, 1),
                })
                next_round.append(winner)
            rounds_data.append({'name': round_name, 'matches': matches})
            current = next_round

        champion = current[0] if current else None
        return rounds_data, champion

    def _monte_carlo(self, bracket_teams, overrides, cache, n=3000):
        """Runs n probabilistic simulations and returns reach-% for each round."""
        rng = np.random.default_rng(42)
        counts = {t: {r: 0 for r in _TRACK_LABELS} for t in bracket_teams}

        for _ in range(n):
            current = list(bracket_teams)
            for round_idx, round_name in enumerate(_ROUND_NAMES):
                next_teams = []
                for i in range(0, len(current), 2):
                    t1, t2 = current[i], current[i + 1]
                    match_id = f"{round_name}-{i // 2}"
                    if match_id in overrides and overrides[match_id] in (t1, t2):
                        winner = overrides[match_id]
                    else:
                        p1_win, p_draw, _ = self._get_proba(t1, t2, cache)
                        p1_eff = p1_win + 0.5 * p_draw
                        winner = t1 if rng.random() < p1_eff else t2
                    next_teams.append(winner)
                current = next_teams
                label = _TRACK_LABELS[round_idx]
                for t in current:
                    if t in counts:
                        counts[t][label] += 1

        return {
            t: {r: round(counts[t][r] / n * 100, 1) for r in _TRACK_LABELS}
            for t in bracket_teams
        }

    def simulate_bracket(self, bracket_teams=None, overrides=None, n_mc=3000):
        """Full bracket simulation with Monte Carlo probability table."""
        if bracket_teams is None:
            bracket_teams = self.get_bracket_seeds()['bracket_teams']
        if overrides is None:
            overrides = {}

        # Precompute all C(32,2) = 496 pairwise probabilities up front
        unique = list(dict.fromkeys(bracket_teams))
        cache = {}
        for i in range(len(unique)):
            for j in range(i + 1, len(unique)):
                t1, t2 = unique[i], unique[j]
                if t1 in self.elo and t2 in self.elo:
                    X, _, _, _ = get_prediction_features(
                        t1, t2, self.elo, self.team_history, self.h2h_history
                    )
                    cache[(t1, t2)] = self.model.predict_proba(X)[0]

        rounds_data, champion = self._run_bracket(bracket_teams, overrides, cache)
        probabilities = self._monte_carlo(bracket_teams, overrides, cache, n_mc)

        return {
            'bracket_teams': bracket_teams,
            'rounds': rounds_data,
            'champion': champion,
            'probabilities': probabilities,
        }

    # ── Group stage engine ────────────────────────────────────────────────────

    def get_groups(self):
        return GROUPS

    def simulate_group_stage(self, overrides=None):
        """
        Simulate all 72 group stage matches.
        overrides: {match_id: {'score1': int, 'score2': int}}
        Returns group data with matches and model probabilities.
        """
        if overrides is None:
            overrides = {}

        cache = {}
        groups_out = {}

        for grp, teams in GROUPS.items():
            # Pre-cache all 6 pairings in this group
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    t1, t2 = teams[i], teams[j]
                    if (t1, t2) not in cache and t1 in self.elo and t2 in self.elo:
                        X, _, _, _ = get_prediction_features(
                            t1, t2, self.elo, self.team_history, self.h2h_history
                        )
                        cache[(t1, t2)] = self.model.predict_proba(X)[0]

            matches = []
            for match_idx, (ai, bi) in enumerate(_GS_SCHEDULE):
                t1, t2 = teams[ai], teams[bi]
                match_id = f"gs-{grp}-{match_idx}"
                p1_win, p_draw, p2_win = self._get_proba(t1, t2, cache)

                if match_id in overrides:
                    s1 = int(overrides[match_id]['score1'])
                    s2 = int(overrides[match_id]['score2'])
                    is_override = True
                else:
                    is_override = False
                    if p1_win >= p_draw and p1_win >= p2_win:
                        s1, s2 = self._match_scores(t1, t2, p1_win, p_draw, p2_win, t1)
                    elif p2_win >= p_draw:
                        s1, s2 = self._match_scores(t1, t2, p1_win, p_draw, p2_win, t2)
                    else:
                        # Draw predicted
                        form1 = _compute_form(self.team_history.get(t1, [])[-10:])
                        form2 = _compute_form(self.team_history.get(t2, [])[-10:])
                        l1 = max(0.5, (form1['avg_gf'] + form2['avg_ga']) / 2)
                        l2 = max(0.5, (form2['avg_gf'] + form1['avg_ga']) / 2)
                        s1 = s2 = max(0, round(min(l1, l2) * 0.8))

                matches.append({
                    'id': match_id,
                    'team1': t1, 'team2': t2,
                    'score1': s1, 'score2': s2,
                    'team1_win_prob': round(p1_win * 100, 1),
                    'draw_prob':      round(p_draw  * 100, 1),
                    'team2_win_prob': round(p2_win  * 100, 1),
                    'is_override': is_override,
                })

            groups_out[grp] = {'teams': teams, 'matches': matches}

        return groups_out
