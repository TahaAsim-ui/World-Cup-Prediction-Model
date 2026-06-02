import { useState, useMemo } from 'react'
import GroupCard from '../components/groups/GroupCard'
import { calculateStandings, getAllStandings, getBestThirdPlace } from '../utils/standings'
import '../../src/group.css'

export default function GroupStagePage() {
  const [groupData, setGroupData]     = useState(null)   // raw API response
  const [overrides, setOverrides]     = useState({})     // {matchId: {score1,score2}}
  const [mode, setMode]               = useState('auto')
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState('')
  const [editing, setEditing]         = useState(null)   // match being edited in modal
  const [editS1, setEditS1]           = useState(0)
  const [editS2, setEditS2]           = useState(0)

  // Merge API data with user overrides
  const resolvedGroups = useMemo(() => {
    if (!groupData) return null
    const out = {}
    for (const [grp, g] of Object.entries(groupData)) {
      out[grp] = {
        ...g,
        matches: g.matches.map(m => {
          const ov = overrides[m.id]
          return ov ? { ...m, score1: ov.score1, score2: ov.score2, is_override: true } : m
        }),
      }
    }
    return out
  }, [groupData, overrides])

  // Standings auto-recalculate whenever resolvedGroups changes
  const allStandings = useMemo(() => {
    if (!resolvedGroups) return {}
    return getAllStandings(resolvedGroups)
  }, [resolvedGroups])

  const qualifiedThirds = useMemo(() => getBestThirdPlace(allStandings), [allStandings])

  const simulate = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/group-stage/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ overrides: {} }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setGroupData(data)
      setOverrides({})
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setGroupData(null)
    setOverrides({})
    setEditing(null)
  }

  const openEditor = (match) => {
    setEditing(match)
    setEditS1(match.is_override ? overrides[match.id]?.score1 ?? match.score1 : match.score1)
    setEditS2(match.is_override ? overrides[match.id]?.score2 ?? match.score2 : match.score2)
  }

  const applyEdit = () => {
    if (!editing) return
    const s1 = Math.max(0, Math.min(20, parseInt(editS1) || 0))
    const s2 = Math.max(0, Math.min(20, parseInt(editS2) || 0))
    setOverrides(prev => ({ ...prev, [editing.id]: { score1: s1, score2: s2 } }))
    setEditing(null)
  }

  const clearOverride = () => {
    if (!editing) return
    setOverrides(prev => {
      const next = { ...prev }
      delete next[editing.id]
      return next
    })
    setEditing(null)
  }

  const nOverrides = Object.keys(overrides).length
  const groups = Object.keys(allStandings).length > 0 ? resolvedGroups : null

  return (
    <div className="gs-page">
      {/* Controls */}
      <div className="bp-controls">
        <div className="bp-mode-toggle">
          <button className={`bp-mode-btn ${mode === 'auto' ? 'active' : ''}`} onClick={() => setMode('auto')}>
            ⚡ Auto Simulate
          </button>
          <button className={`bp-mode-btn ${mode === 'manual' ? 'active' : ''}`} onClick={() => setMode('manual')}>
            ✏️ Manual Mode
          </button>
        </div>
        <div className="bp-actions">
          {mode === 'manual' && nOverrides > 0 && (
            <span className="bp-override-badge">{nOverrides} edit{nOverrides > 1 ? 's' : ''}</span>
          )}
          <button className="bp-simulate-btn" onClick={simulate} disabled={loading}>
            {loading ? <><span className="spinner" /> Simulating…</> : '▶ Simulate Group Stage'}
          </button>
          {groupData && (
            <button className="bp-reset-btn" onClick={reset}>↺ Reset</button>
          )}
        </div>
      </div>

      {mode === 'manual' && groupData && (
        <p className="bp-manual-hint">
          Click any match score to override it — standings update instantly.
        </p>
      )}

      {error && <div className="error-banner" style={{ margin: '0 0 16px' }}>⚠ {error}</div>}

      {/* Pre-simulate state */}
      {!groupData && !loading && (
        <div className="bp-presim">
          <div className="bp-presim-icon">📋</div>
          <div className="bp-presim-title">12 Groups · 72 Matches</div>
          <p className="bp-presim-text">
            Groups A–L, 4 teams each. Top 2 from every group qualify, plus the 8 best 3rd-place teams (32 total advance to the knockout stage).
            <br /><br />
            Click <strong>Simulate Group Stage</strong> to predict all matches.
          </p>
        </div>
      )}

      {loading && (
        <div className="bp-loading">
          <div className="bp-spinner-large" />
          <p>Predicting 72 matches…</p>
        </div>
      )}

      {/* Legend */}
      {groups && (
        <div className="gs-legend">
          <span className="gs-legend-item"><span className="gs-q-dot gs-q-green inline" />Qualified (1st/2nd)</span>
          <span className="gs-legend-item"><span className="gs-q-dot gs-q-yellow inline" />Best 3rd (qualified)</span>
          <span className="gs-legend-item"><span className="gs-q-dot gs-q-red inline" />Eliminated</span>
          {nOverrides > 0 && <span className="gs-legend-item"><span className="gm-override-dot inline" />Manually edited</span>}
        </div>
      )}

      {/* 12 Group cards grid */}
      {groups && (
        <div className="gs-grid">
          {Object.keys(groups).map(letter => (
            <GroupCard
              key={letter}
              letter={letter}
              teams={groups[letter].teams}
              matches={groups[letter].matches}
              standings={allStandings[letter] || []}
              isManual={mode === 'manual'}
              onEdit={openEditor}
              qualifiedThirds={qualifiedThirds}
            />
          ))}
        </div>
      )}

      {/* Score edit modal */}
      {editing && (
        <div className="picker-backdrop" onClick={() => setEditing(null)}>
          <div className="picker-modal" onClick={e => e.stopPropagation()}>
            <div className="picker-title">Edit match score</div>
            <div className="picker-match-id">{editing.id.replace('gs-', 'Group ')}</div>

            <div className="gs-edit-row">
              <div className="gs-edit-team">
                <span>{editing.team1}</span>
                <input
                  type="number" min="0" max="20"
                  className="gs-score-input"
                  value={editS1}
                  onChange={e => setEditS1(e.target.value)}
                  onFocus={e => e.target.select()}
                  autoFocus
                />
              </div>
              <span className="gs-edit-sep">–</span>
              <div className="gs-edit-team gs-edit-team-right">
                <input
                  type="number" min="0" max="20"
                  className="gs-score-input"
                  value={editS2}
                  onChange={e => setEditS2(e.target.value)}
                  onFocus={e => e.target.select()}
                />
                <span>{editing.team2}</span>
              </div>
            </div>

            <div className="gs-edit-probs">
              Model: {editing.team1_win_prob}% / {editing.draw_prob}% draw / {editing.team2_win_prob}%
            </div>

            <div className="gs-edit-actions">
              <button className="bp-simulate-btn" style={{ flex: 1 }} onClick={applyEdit}>
                Apply
              </button>
              {overrides[editing.id] && (
                <button className="picker-clear" style={{ marginTop: 0, flex: 0.5 }} onClick={clearOverride}>
                  Reset
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
