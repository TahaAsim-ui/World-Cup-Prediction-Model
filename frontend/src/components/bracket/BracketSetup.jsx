import { getFlagEmoji, WORLD_CUP_2026_TEAMS } from '../../utils/countryUtils'

const WC_TEAMS = [...WORLD_CUP_2026_TEAMS].sort()

function TeamPicker({ value, onChange, excludeTeams }) {
  return (
    <div className="bs-team-cell">
      <span className="bs-flag">{getFlagEmoji(value)}</span>
      <select
        className="bs-select"
        value={value}
        onChange={e => onChange(e.target.value)}
      >
        {WC_TEAMS.map(t => (
          <option key={t} value={t} disabled={excludeTeams.has(t) && t !== value}>
            {t}
          </option>
        ))}
      </select>
    </div>
  )
}

export default function BracketSetup({ teams, onChange }) {
  // teams: flat array of 32 — [t1a,t1b, t2a,t2b, ...] (pairs = R32 matches)
  const usedTeams = new Set(teams)

  const handleChange = (idx, newTeam) => {
    const next = [...teams]
    // If newTeam already exists somewhere else, swap them
    const existingIdx = next.indexOf(newTeam)
    if (existingIdx !== -1 && existingIdx !== idx) {
      next[existingIdx] = next[idx]  // put the displaced team back
    }
    next[idx] = newTeam
    onChange(next)
  }

  const pairs = Array.from({ length: 16 }, (_, i) => ({
    i,
    t1: teams[i * 2],
    t2: teams[i * 2 + 1],
    idx1: i * 2,
    idx2: i * 2 + 1,
  }))

  return (
    <div className="bs-wrapper">
      <div className="bs-header">
        <span className="bs-title">Round of 32 — Edit Teams</span>
        <span className="bs-hint">
          Change any team. If you pick a team already in the bracket, the two teams swap slots.
        </span>
      </div>

      <div className="bs-grid">
        {pairs.map(({ i, t1, t2, idx1, idx2 }) => (
          <div key={i} className="bs-card">
            <div className="bs-match-num">Match {i + 1}</div>
            <div className="bs-teams">
              <TeamPicker
                value={t1}
                onChange={v => handleChange(idx1, v)}
                excludeTeams={usedTeams}
              />
              <span className="bs-vs">vs</span>
              <TeamPicker
                value={t2}
                onChange={v => handleChange(idx2, v)}
                excludeTeams={usedTeams}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
