import { getFlagEmoji } from '../../utils/countryUtils'

export default function GroupMatch({ match, isManual, onEdit }) {
  const { team1, team2, score1, score2, team1_win_prob, draw_prob, team2_win_prob, is_override } = match
  const s1 = Number(score1), s2 = Number(score2)

  return (
    <div
      className={`gm ${is_override ? 'gm-override' : ''} ${isManual ? 'gm-clickable' : ''}`}
      onClick={isManual ? () => onEdit(match) : undefined}
      title={isManual ? 'Click to edit score' : undefined}
    >
      <span className="gm-team gm-left">
        <span className="gm-flag">{getFlagEmoji(team1)}</span>
        <span className="gm-name">{team1}</span>
      </span>

      <div className="gm-result">
        <span className={`gm-score ${s1 > s2 ? 'gm-winner-score' : s1 < s2 ? 'gm-loser-score' : 'gm-draw-score'}`}>
          {score1}
        </span>
        <span className="gm-sep">–</span>
        <span className={`gm-score ${s2 > s1 ? 'gm-winner-score' : s2 < s1 ? 'gm-loser-score' : 'gm-draw-score'}`}>
          {score2}
        </span>
        {is_override && <span className="gm-override-dot" title="Manually set" />}
        {isManual && <span className="gm-edit-icon">✏</span>}
      </div>

      <span className="gm-team gm-right">
        <span className="gm-name">{team2}</span>
        <span className="gm-flag">{getFlagEmoji(team2)}</span>
      </span>
    </div>
  )
}
