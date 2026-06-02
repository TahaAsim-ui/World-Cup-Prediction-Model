import { getFlagEmoji } from '../utils/countryUtils'
import ProbabilityBars from './ProbabilityBars'

function StatPill({ label, value }) {
  return (
    <div className="stat-pill">
      <span className="stat-pill-label">{label}</span>
      <span className="stat-pill-value">{value}</span>
    </div>
  )
}

function TeamStats({ team, elo, form, avgGf, avgGa }) {
  return (
    <div className="team-stats-block">
      <div className="team-stats-name">
        <span className="team-stats-flag">{getFlagEmoji(team)}</span>
        {team}
      </div>
      <div className="stat-pills">
        <StatPill label="Elo" value={elo} />
        <StatPill label="Recent" value={form} />
        <StatPill label="Avg GF" value={avgGf} />
        <StatPill label="Avg GA" value={avgGa} />
      </div>
    </div>
  )
}

export default function PredictionCard({ data }) {
  const {
    team1, team2,
    team1_win_probability: p1,
    draw_probability: pDraw,
    team2_win_probability: p2,
    predicted_winner,
    score1, score2,
    team1_elo, team2_elo,
    team1_form_string, team2_form_string,
    team1_avg_gf, team2_avg_gf,
    team1_avg_ga, team2_avg_ga,
    h2h_n, h2h_team1_win_rate, h2h_draw_rate, h2h_team2_win_rate,
    explanation,
  } = data

  const isTeam1Winner = predicted_winner === team1
  const isTeam2Winner = predicted_winner === team2
  const isDraw = predicted_winner === 'Draw'

  return (
    <div className="prediction-card">
      {/* Header banner */}
      <div className="prediction-banner">
        <div className="banner-team">
          <div className="banner-flag">{getFlagEmoji(team1)}</div>
          <div className="banner-name">{team1}</div>
        </div>

        <div className="banner-center">
          <div className="banner-vs">VS</div>
          <div className={`winner-badge ${isTeam1Winner ? 'badge-team1' : isTeam2Winner ? 'badge-team2' : 'badge-draw'}`}>
            {isDraw ? '🤝 Draw Predicted' : `🏆 ${predicted_winner} to Win`}
          </div>
        </div>

        <div className="banner-team banner-team-right">
          <div className="banner-flag">{getFlagEmoji(team2)}</div>
          <div className="banner-name">{team2}</div>
        </div>
      </div>

      {/* Predicted score */}
      <div className="predicted-score-section">
        <span className="score-label">Predicted Score</span>
        <div className="score-display">
          <span className={`score-num ${isTeam1Winner ? 'score-winner' : ''}`}>{score1}</span>
          <span className="score-dash">–</span>
          <span className={`score-num ${isTeam2Winner ? 'score-winner' : ''}`}>{score2}</span>
        </div>
      </div>

      {/* Probability bars */}
      <div className="section">
        <h3 className="section-title">Match Outcome Probabilities</h3>
        <ProbabilityBars team1={team1} team2={team2} p1={p1} pDraw={pDraw} p2={p2} />
      </div>

      {/* Team stats */}
      <div className="section">
        <h3 className="section-title">Team Statistics (Last 10 Matches)</h3>
        <div className="team-stats-grid">
          <TeamStats
            team={team1}
            elo={team1_elo}
            form={team1_form_string}
            avgGf={team1_avg_gf}
            avgGa={team1_avg_ga}
          />
          <TeamStats
            team={team2}
            elo={team2_elo}
            form={team2_form_string}
            avgGf={team2_avg_gf}
            avgGa={team2_avg_ga}
          />
        </div>
      </div>

      {/* H2H */}
      {h2h_n > 0 && (
        <div className="section">
          <h3 className="section-title">Head-to-Head (Last {Math.min(h2h_n, 10)} Meetings)</h3>
          <div className="h2h-bar-wrapper">
            <span className="h2h-label">{team1}</span>
            <div className="h2h-track">
              <div className="h2h-fill h2h-team1" style={{ width: `${h2h_team1_win_rate}%` }} title={`${team1}: ${h2h_team1_win_rate}%`} />
              <div className="h2h-fill h2h-draw" style={{ width: `${h2h_draw_rate}%` }} title={`Draw: ${h2h_draw_rate}%`} />
              <div className="h2h-fill h2h-team2" style={{ width: `${h2h_team2_win_rate}%` }} title={`${team2}: ${h2h_team2_win_rate}%`} />
            </div>
            <span className="h2h-label">{team2}</span>
          </div>
          <div className="h2h-legend">
            <span className="h2h-legend-item team1-dot">{team1}: {h2h_team1_win_rate}%</span>
            <span className="h2h-legend-item draw-dot">Draw: {h2h_draw_rate}%</span>
            <span className="h2h-legend-item team2-dot">{team2}: {h2h_team2_win_rate}%</span>
          </div>
        </div>
      )}

      {/* Explanation */}
      <div className="section explanation-section">
        <h3 className="section-title">Why This Prediction?</h3>
        <p className="explanation-text">{explanation}</p>
      </div>
    </div>
  )
}
