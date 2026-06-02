import { getFlagEmoji } from '../../utils/countryUtils'

export default function BracketMatch({ match, isManual, onPickWinner }) {
  const { team1, team2, score1, score2, winner, id } = match

  const handleClick = () => {
    if (!isManual) return
    // Cycle: no override → team1 → team2 → no override
    onPickWinner(id, team1, team2)
  }

  return (
    <div
      className={`bm ${isManual ? 'bm-manual' : ''}`}
      title={isManual ? 'Click to override winner' : undefined}
      onClick={handleClick}
    >
      <div className={`bm-team ${winner === team1 ? 'bm-winner' : winner ? 'bm-loser' : ''}`}>
        <span className="bm-flag">{getFlagEmoji(team1)}</span>
        <span className="bm-name">{team1}</span>
        <span className="bm-score">{winner != null ? score1 : ''}</span>
      </div>
      <div className="bm-divider" />
      <div className={`bm-team ${winner === team2 ? 'bm-winner' : winner ? 'bm-loser' : ''}`}>
        <span className="bm-flag">{getFlagEmoji(team2)}</span>
        <span className="bm-name">{team2}</span>
        <span className="bm-score">{winner != null ? score2 : ''}</span>
      </div>
    </div>
  )
}
