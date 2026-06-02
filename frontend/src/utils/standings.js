export function calculateStandings(teams, matches) {
  const table = {}
  teams.forEach(t => {
    table[t] = { team: t, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 }
  })

  matches.forEach(({ team1, team2, score1, score2 }) => {
    const s1 = Number(score1)
    const s2 = Number(score2)
    if (score1 == null || score2 == null || isNaN(s1) || isNaN(s2)) return

    table[team1].p++
    table[team2].p++
    table[team1].gf += s1
    table[team1].ga += s2
    table[team2].gf += s2
    table[team2].ga += s1

    if (s1 > s2) {
      table[team1].w++; table[team1].pts += 3; table[team2].l++
    } else if (s1 === s2) {
      table[team1].d++; table[team1].pts++
      table[team2].d++; table[team2].pts++
    } else {
      table[team2].w++; table[team2].pts += 3; table[team1].l++
    }
  })

  return Object.values(table).sort((a, b) => {
    if (b.pts !== a.pts) return b.pts - a.pts
    const gd = (b.gf - b.ga) - (a.gf - a.ga)
    if (gd !== 0) return gd
    if (b.gf !== a.gf) return b.gf - a.gf
    return a.team.localeCompare(b.team)
  })
}

export function getAllStandings(groupsData) {
  const all = {}
  for (const [grp, g] of Object.entries(groupsData)) {
    all[grp] = calculateStandings(g.teams, g.matches)
  }
  return all
}

// Returns the 8 best 3rd-place teams that qualify for the knockout stage
export function getBestThirdPlace(allStandings) {
  return Object.entries(allStandings)
    .map(([grp, rows]) => ({ grp, ...rows[2] }))
    .filter(r => r.team)
    .sort((a, b) => {
      if (b.pts !== a.pts) return b.pts - a.pts
      const gd = (b.gf - b.ga) - (a.gf - a.ga)
      if (gd !== 0) return gd
      if (b.gf !== a.gf) return b.gf - a.gf
      return a.team.localeCompare(b.team)
    })
    .slice(0, 8)
    .map(r => r.team)
}
