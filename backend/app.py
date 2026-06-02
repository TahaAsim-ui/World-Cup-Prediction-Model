from flask import Flask, jsonify, request
from flask_cors import CORS
from predictor import MatchPredictor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

try:
    predictor = MatchPredictor()
    logger.info(f"Model loaded. {len(predictor.get_teams())} teams available.")
except FileNotFoundError as e:
    logger.error(str(e))
    predictor = None


def _check_model():
    if predictor is None:
        return jsonify({'error': 'Model not trained yet. Run: python train.py'}), 503
    return None


# ── Single match ──────────────────────────────────────────────────────────────

@app.route('/api/teams', methods=['GET'])
def get_teams():
    err = _check_model()
    if err: return err
    return jsonify({'teams': predictor.get_teams()})


@app.route('/api/predict', methods=['POST'])
def predict():
    err = _check_model()
    if err: return err
    data  = request.get_json(silent=True) or {}
    team1 = str(data.get('team1', '')).strip()
    team2 = str(data.get('team2', '')).strip()
    if not team1 or not team2:
        return jsonify({'error': 'Both team1 and team2 are required.'}), 400
    try:
        return jsonify(predictor.predict(team1, team2))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception:
        logger.exception("Prediction error")
        return jsonify({'error': 'Internal server error.'}), 500


@app.route('/api/model-info', methods=['GET'])
def model_info():
    err = _check_model()
    if err: return err
    return jsonify(predictor.get_model_info())


# ── Bracket ───────────────────────────────────────────────────────────────────

@app.route('/api/bracket/seeds', methods=['GET'])
def bracket_seeds():
    err = _check_model()
    if err: return err
    return jsonify(predictor.get_bracket_seeds())


@app.route('/api/bracket/simulate', methods=['POST'])
def bracket_simulate():
    err = _check_model()
    if err: return err
    data          = request.get_json(silent=True) or {}
    bracket_teams = data.get('bracket_teams')
    overrides     = data.get('overrides', {})
    n_mc          = int(data.get('n_mc', 3000))

    if not bracket_teams or len(bracket_teams) != 32:
        return jsonify({'error': 'bracket_teams must be a list of exactly 32 team names.'}), 400

    try:
        result = predictor.simulate_bracket(bracket_teams, overrides, n_mc)
        return jsonify(result)
    except Exception:
        logger.exception("Bracket simulation error")
        return jsonify({'error': 'Internal server error.'}), 500


# ── Group stage ──────────────────────────────────────────────────────────────

@app.route('/api/group-stage/groups', methods=['GET'])
def group_stage_groups():
    err = _check_model()
    if err: return err
    return jsonify(predictor.get_groups())


@app.route('/api/group-stage/simulate', methods=['POST'])
def group_stage_simulate():
    err = _check_model()
    if err: return err
    data      = request.get_json(silent=True) or {}
    overrides = data.get('overrides', {})
    try:
        result = predictor.simulate_group_stage(overrides)
        return jsonify(result)
    except Exception:
        logger.exception("Group stage simulation error")
        return jsonify({'error': 'Internal server error.'}), 500


# ── Health ────────────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model_ready': predictor is not None})


if __name__ == '__main__':
    app.run(debug=True, port=5001)
