import { useState, useRef, useEffect } from 'react'
import { getFlagEmoji } from '../utils/countryUtils'

export default function TeamSelector({ label, teams, value, onChange, excludeTeam }) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  const filtered = teams
    .filter(t => t !== excludeTeam)
    .filter(t => t.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 80)

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSelect = (team) => {
    onChange(team)
    setQuery('')
    setOpen(false)
  }

  const handleInputChange = (e) => {
    setQuery(e.target.value)
    setOpen(true)
    if (!e.target.value) onChange('')
  }

  const displayValue = value ? `${getFlagEmoji(value)} ${value}` : ''

  return (
    <div className="selector-wrapper" ref={ref}>
      <label className="selector-label">{label}</label>
      <div className="selector-box" onClick={() => setOpen(true)}>
        <input
          className="selector-input"
          type="text"
          placeholder="Search team..."
          value={open ? query : displayValue}
          onChange={handleInputChange}
          onFocus={() => setOpen(true)}
          autoComplete="off"
        />
        <span className="selector-chevron">{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <ul className="selector-dropdown">
          {filtered.length === 0 && (
            <li className="selector-empty">No teams found</li>
          )}
          {filtered.map(team => (
            <li
              key={team}
              className={`selector-option ${team === value ? 'selected' : ''}`}
              onMouseDown={() => handleSelect(team)}
            >
              <span className="selector-flag">{getFlagEmoji(team)}</span>
              {team}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
