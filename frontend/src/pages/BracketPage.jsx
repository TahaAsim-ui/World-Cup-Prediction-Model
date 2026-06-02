import { useState, useEffect } from 'react'
import BracketVisualization from '../components/bracket/BracketVisualization'
import BracketSetup from '../components/bracket/BracketSetup'
import ProbabilityTable from '../components/bracket/ProbabilityTable'
import '../../src/bracket.css'

export default function BracketPage() {
  const [seeds, setSeeds]               = useState(null)
  const [customTeams, setCustomTeams]   = useState(null)   // editable R32 team list
  const [bracketData, setBracketData]   = useState(null)
  const [overrides, setOverrides]       = useState({})
  const [mode, setMode]                 = useState('auto')
  const [showSetup, setShowSetup]       = useState(false)  // team editor visible
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [pickerState, setPickerState]   = useState(null)

  useEffect(() => {
    fetch('/api/bracket/seeds')
      .then(r => r.json())
      .then(d => {
        setSeeds(d)
        setCustomTeams(d.bracket_teams)
      })
      .catch(() => setError('Failed to load bracket seeds. Is the server running?'))
  }, [])

  const simulate = async (customOverrides) => {
    if (!customTeams) return
    setLoading(true)
    setError('')
    setPickerState(null)
    setShowSetup(false)
    try {
      const res = await fetch('/api/bracket/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bracket_teams: customTeams,
          overrides: customOverrides ?? overrides,
        }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setBracketData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handlePickWinner = (matchId, team1, team2) => {
    setPickerState({ matchId, team1, team2 })
  }

  const applyOverride = (matchId, winner) => {
    const next = { ...overrides, [matchId]: winner }
    if (winner === null) delete next[matchId]
    setOverrides(next)
    setPickerState(null)
  }

  const resetBracket = () => {
    setOverrides({})
    setBracketData(null)
    setPickerState(null)
    setShowSetup(false)
    if (seeds) setCustomTeams(seeds.bracket_teams)
  }

  const teamsEdited = seeds && customTeams &&
    JSON.stringify(customTeams) !== JSON.stringify(seeds.bracket_teams)

  const nOverrides = Object.keys(overrides).length

  return (
    <div className="bracket-page">

      {/* Controls */}
      <div className="bp-controls">
        <div className="bp-mode-toggle">
          <button
            className={`bp-mode-btn ${mode === 'auto' ? 'active' : ''}`}
            onClick={() => setMode('auto')}
          >
            ⚡ Auto Simulate
          </button>
          <button
            className={`bp-mode-btn ${mode === 'manual' ? 'active' : ''}`}
            onClick={() => setMode('manual')}
          >
            ✏️ Manual Winners
          </button>
        </div>

        <div className="bp-actions">
          {/* Edit teams toggle */}
          {!bracketData && (
            <button
              className={`bp-reset-btn ${showSetup ? 'bp-setup-active' : ''}`}
              onClick={() => setShowSetup(s => !s)}
              disabled={!seeds}
              title="Edit which teams are in the Round of 32"
            >
              {showSetup ? '✕ Close Editor' : '⚙ Edit Teams'}
            </button>
          )}
          {bracketData && (
            <button
              className="bp-reset-btn"
              onClick={() => { setShowSetup(true); setBracketData(null); setOverrides({}) }}
              title="Go back and change teams"
            >
              ⚙ Edit Teams
            </button>
          )}

          {/* Badges */}
          {teamsEdited && (
            <span className="bp-override-badge" style={{ background: 'rgba(59,130,246,0.15)', borderColor: 'rgba(59,130,246,0.35)', color: '#60a5fa' }}>
              Custom bracket
            </span>
          )}
          {mode === 'manual' && nOverrides > 0 && (
            <span className="bp-override-badge">
              {nOverrides} override{nOverrides > 1 ? 's' : ''}
            </span>
          )}

          <button
            className="bp-simulate-btn"
            onClick={() => simulate()}
            disabled={loading || !seeds || showSetup}
          >
            {loading
              ? <><span className="spinner" /> Simulating…</>
              : '▶ Simulate Bracket'}
          </button>

          {(bracketData || teamsEdited) && (
            <button className="bp-reset-btn" onClick={resetBracket}>↺ Reset</button>
          )}
        </div>
      </div>

      {/* Manual mode hint */}
      {mode === 'manual' && bracketData && (
        <p className="bp-manual-hint">
          Click any match card to override the winner, then press <strong>Simulate Bracket</strong> to re-run downstream rounds.
        </p>
      )}

      {error && <div className="error-banner" style={{ margin: '0 0 16px' }}>⚠ {error}</div>}

      {/* Team editor */}
      {showSetup && customTeams && (
        <div style={{ padding: '0 0 8px' }}>
          <BracketSetup
            teams={customTeams}
            onChange={setCustomTeams}
          />
          <div style={{ padding: '16px 24px', display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              className="bp-simulate-btn"
              style={{ width: 'auto', padding: '12px 28px' }}
              onClick={() => simulate()}
              disabled={loading}
            >
              {loading ? <><span className="spinner" /> Simulating…</> : '▶ Simulate with These Teams'}
            </button>
            {teamsEdited && (
              <button
                className="bp-reset-btn"
                onClick={() => { setCustomTeams(seeds.bracket_teams); setShowSetup(false) }}
              >
                Reset to Elo Seeding
              </button>
            )}
          </div>
        </div>
      )}

      {/* Pre-simulation idle state */}
      {!bracketData && !showSetup && seeds && !loading && (
        <div className="bp-presim">
          <div className="bp-presim-icon">⚽</div>
          <div className="bp-presim-title">Ready to Simulate</div>
          <p className="bp-presim-text">
            The bracket is seeded by Elo rating — <strong>{customTeams?.[0]}</strong> vs{' '}
            <strong>{customTeams?.[1]}</strong> in Match 1, etc.
            <br /><br />
            Use <strong>⚙ Edit Teams</strong> to set your own R32 matchups based on actual group stage results,
            then click <strong>Simulate Bracket</strong>.
          </p>
        </div>
      )}

      {loading && (
        <div className="bp-loading">
          <div className="bp-spinner-large" />
          <p>Running {(3000).toLocaleString()} simulations…</p>
        </div>
      )}

      {/* Bracket result */}
      {bracketData && !loading && (
        <>
          <BracketVisualization
            rounds={bracketData.rounds}
            champion={bracketData.champion}
            isManual={mode === 'manual'}
            onPickWinner={handlePickWinner}
          />
          <ProbabilityTable probabilities={bracketData.probabilities} />
        </>
      )}

      {/* Winner picker modal */}
      {pickerState && (
        <div className="picker-backdrop" onClick={() => setPickerState(null)}>
          <div className="picker-modal" onClick={e => e.stopPropagation()}>
            <div className="picker-title">Override match winner</div>
            <div className="picker-match-id">{pickerState.matchId}</div>
            <div className="picker-options">
              <button
                className={`picker-btn ${overrides[pickerState.matchId] === pickerState.team1 ? 'picker-selected' : ''}`}
                onClick={() => applyOverride(pickerState.matchId, pickerState.team1)}
              >
                {pickerState.team1}
              </button>
              <button
                className={`picker-btn ${overrides[pickerState.matchId] === pickerState.team2 ? 'picker-selected' : ''}`}
                onClick={() => applyOverride(pickerState.matchId, pickerState.team2)}
              >
                {pickerState.team2}
              </button>
            </div>
            {overrides[pickerState.matchId] && (
              <button
                className="picker-clear"
                onClick={() => applyOverride(pickerState.matchId, null)}
              >
                Clear override
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
