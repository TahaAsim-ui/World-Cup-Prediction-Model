import BracketMatch from './BracketMatch'
import { getFlagEmoji } from '../../utils/countryUtils'

const ROUND_LABELS = {
  R32: 'Round of 32',
  R16: 'Round of 16',
  Quarterfinals: 'Quarter Finals',
  Semifinals: 'Semi Finals',
  Final: 'Final',
}

// Groups consecutive pairs of matches into [[m0,m1],[m2,m3],...]
function toPairs(matches) {
  const pairs = []
  for (let i = 0; i < matches.length; i += 2) {
    pairs.push([matches[i], matches[i + 1]].filter(Boolean))
  }
  return pairs
}

function RoundCol({ roundName, matches, side, isManual, onPickWinner }) {
  const isSingle = matches.length === 1
  const pairs = isSingle ? null : toPairs(matches)

  return (
    <div className={`br-round-col br-round-${side}`}>
      <div className="br-round-label">{ROUND_LABELS[roundName] || roundName}</div>
      <div className="br-round-body">
        {isSingle ? (
          <div className="br-single">
            <BracketMatch
              match={matches[0]}
              isManual={isManual}
              onPickWinner={onPickWinner}
            />
          </div>
        ) : (
          pairs.map((pair, pi) => (
            <div key={pi} className="br-pair">
              {pair.map(match => (
                <BracketMatch
                  key={match.id}
                  match={match}
                  isManual={isManual}
                  onPickWinner={onPickWinner}
                />
              ))}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function FinalCenter({ match, champion }) {
  return (
    <div className="br-center">
      <div className="br-center-label">Final</div>
      <div className="br-final-match">
        <BracketMatch match={match} isManual={false} onPickWinner={() => {}} />
      </div>
      {champion && (
        <div className="br-champion">
          <div className="br-champion-trophy">🏆</div>
          <div className="br-champion-label">Predicted Champion</div>
          <div className="br-champion-name">
            <span className="br-champion-flag">{getFlagEmoji(champion)}</span>
            {champion}
          </div>
        </div>
      )}
    </div>
  )
}

export default function BracketVisualization({ rounds, champion, isManual, onPickWinner }) {
  // Split each round into left half and right half
  const split = rounds.map(r => {
    const mid = Math.floor(r.matches.length / 2)
    return {
      name: r.name,
      left: r.matches.slice(0, mid),
      right: r.matches.slice(mid),
    }
  })

  // Left side: R32→R16→QF→SF columns displayed left→right (progressing toward center)
  const leftRounds = split.slice(0, 4).map(r => ({ name: r.name, matches: r.left }))
  // Right side: R32→R16→QF→SF data, but displayed right→left (row-reverse)
  const rightRounds = split.slice(0, 4).map(r => ({ name: r.name, matches: r.right }))

  const finalMatch = rounds[4]?.matches[0]

  return (
    <div className="br-scroll-wrapper">
      <div className="br-bracket">

        {/* Left half */}
        <div className="br-half br-half-left">
          {leftRounds.map(r => (
            <RoundCol
              key={r.name}
              roundName={r.name}
              matches={r.matches}
              side="left"
              isManual={isManual}
              onPickWinner={onPickWinner}
            />
          ))}
        </div>

        {/* Center: Final + Champion */}
        {finalMatch && (
          <FinalCenter match={finalMatch} champion={champion} />
        )}

        {/* Right half — row-reverse makes it mirror */}
        <div className="br-half br-half-right">
          {rightRounds.map(r => (
            <RoundCol
              key={r.name}
              roundName={r.name}
              matches={r.matches}
              side="right"
              isManual={isManual}
              onPickWinner={onPickWinner}
            />
          ))}
        </div>

      </div>
    </div>
  )
}
