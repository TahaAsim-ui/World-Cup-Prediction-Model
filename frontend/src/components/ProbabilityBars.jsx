export default function ProbabilityBars({ team1, team2, p1, pDraw, p2 }) {
  const bars = [
    { label: team1, prob: p1, colorClass: 'bar-team1' },
    { label: 'Draw', prob: pDraw, colorClass: 'bar-draw' },
    { label: team2, prob: p2, colorClass: 'bar-team2' },
  ]

  const maxProb = Math.max(p1, pDraw, p2)

  return (
    <div className="prob-bars">
      {bars.map(({ label, prob, colorClass }) => (
        <div key={label} className="prob-row">
          <div className="prob-meta">
            <span className={`prob-label ${prob === maxProb ? 'prob-label-winner' : ''}`}>
              {prob === maxProb && <span className="prob-crown">★ </span>}
              {label}
            </span>
            <span className={`prob-pct ${prob === maxProb ? 'prob-pct-winner' : ''}`}>
              {prob.toFixed(1)}%
            </span>
          </div>
          <div className="prob-track">
            <div
              className={`prob-fill ${colorClass}`}
              style={{ width: `${prob}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
