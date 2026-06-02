import GroupMatch from './GroupMatch'
import GroupStandings from './GroupStandings'

export default function GroupCard({ letter, teams, matches, standings, isManual, onEdit, qualifiedThirds }) {
  return (
    <div className="gc">
      <div className="gc-header">Group {letter}</div>

      <div className="gc-matches">
        {matches.map(m => (
          <GroupMatch
            key={m.id}
            match={m}
            isManual={isManual}
            onEdit={onEdit}
          />
        ))}
      </div>

      <div className="gc-standings">
        <GroupStandings standings={standings} qualifiedThirds={qualifiedThirds} />
      </div>
    </div>
  )
}
