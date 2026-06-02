import { getFlagEmoji } from '../../utils/countryUtils'

export default function GroupStandings({ standings, qualifiedThirds }) {
  return (
    <table className="gs-table">
      <thead>
        <tr>
          <th className="gs-th-pos">#</th>
          <th className="gs-th-team">Team</th>
          <th>P</th>
          <th>W</th>
          <th>D</th>
          <th>L</th>
          <th>GF</th>
          <th>GA</th>
          <th>GD</th>
          <th className="gs-th-pts">Pts</th>
        </tr>
      </thead>
      <tbody>
        {standings.map((row, i) => {
          const gd = row.gf - row.ga
          const isQ1 = i === 0
          const isQ2 = i === 1
          const isQ3 = i === 2 && qualifiedThirds?.includes(row.team)
          const isOut = i === 3 || (i === 2 && !isQ3)
          return (
            <tr
              key={row.team}
              className={`gs-row ${isQ1 || isQ2 ? 'gs-qualified' : isQ3 ? 'gs-third-qualified' : isOut ? 'gs-eliminated' : ''}`}
            >
              <td className="gs-td-pos">
                {(isQ1 || isQ2) && <span className="gs-q-dot gs-q-green" />}
                {isQ3 && <span className="gs-q-dot gs-q-yellow" />}
                {isOut && <span className="gs-q-dot gs-q-red" />}
                {i + 1}
              </td>
              <td className="gs-td-team">
                <span className="gs-flag">{getFlagEmoji(row.team)}</span>
                {row.team}
              </td>
              <td>{row.p}</td>
              <td>{row.w}</td>
              <td>{row.d}</td>
              <td>{row.l}</td>
              <td>{row.gf}</td>
              <td>{row.ga}</td>
              <td className={gd > 0 ? 'gs-pos' : gd < 0 ? 'gs-neg' : ''}>{gd > 0 ? `+${gd}` : gd}</td>
              <td className="gs-td-pts">{row.pts}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
