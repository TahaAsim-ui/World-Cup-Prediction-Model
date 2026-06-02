import { getFlagEmoji } from '../../utils/countryUtils'

const COLS = ['R16', 'Quarterfinals', 'Semifinals', 'Final', 'Champion']
const LABELS = ['R16', 'QF', 'SF', 'Final', '🏆']

function pctColor(pct) {
  if (pct >= 50) return '#22c55e'
  if (pct >= 25) return '#86efac'
  if (pct >= 10) return '#a3e635'
  if (pct >= 5)  return '#facc15'
  return '#6b7280'
}

export default function ProbabilityTable({ probabilities }) {
  const teams = Object.keys(probabilities)
    .sort((a, b) => probabilities[b]['Champion'] - probabilities[a]['Champion'])

  return (
    <div className="prob-table-wrapper">
      <h3 className="prob-table-title">Tournament Probability Estimates</h3>
      <p className="prob-table-sub">From 3,000 Monte Carlo simulations — each run draws winners probabilistically based on the ML model.</p>
      <div className="prob-table-scroll">
        <table className="prob-table">
          <thead>
            <tr>
              <th className="pt-team-col">Team</th>
              {LABELS.map((l, i) => <th key={i}>{l}</th>)}
            </tr>
          </thead>
          <tbody>
            {teams.map(team => {
              const row = probabilities[team]
              return (
                <tr key={team}>
                  <td className="pt-team-cell">
                    <span className="pt-flag">{getFlagEmoji(team)}</span>
                    {team}
                  </td>
                  {COLS.map(col => (
                    <td key={col} className="pt-pct-cell" style={{ color: pctColor(row[col]) }}>
                      {row[col].toFixed(1)}%
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
