// ISO 3166-1 alpha-2 codes for football nations (as named in the dataset)
const COUNTRY_CODES = {
  'Afghanistan': 'AF', 'Albania': 'AL', 'Algeria': 'DZ', 'Angola': 'AO',
  'Argentina': 'AR', 'Armenia': 'AM', 'Australia': 'AU', 'Austria': 'AT',
  'Azerbaijan': 'AZ', 'Bahrain': 'BH', 'Bangladesh': 'BD', 'Belarus': 'BY',
  'Belgium': 'BE', 'Benin': 'BJ', 'Bolivia': 'BO', 'Bosnia and Herzegovina': 'BA',
  'Botswana': 'BW', 'Brazil': 'BR', 'Bulgaria': 'BG', 'Burkina Faso': 'BF',
  'Burundi': 'BI', 'Cambodia': 'KH', 'Cameroon': 'CM', 'Canada': 'CA',
  'Cape Verde': 'CV', 'Chile': 'CL', 'China': 'CN', 'China PR': 'CN',
  'Colombia': 'CO', 'Congo': 'CG', 'Costa Rica': 'CR', 'Croatia': 'HR',
  'Cuba': 'CU', 'Czech Republic': 'CZ', 'Czechia': 'CZ', 'Denmark': 'DK',
  'DR Congo': 'CD', 'Ecuador': 'EC', 'Egypt': 'EG', 'El Salvador': 'SV',
  'England': 'GB-ENG', 'Estonia': 'EE', 'Ethiopia': 'ET', 'Finland': 'FI',
  'France': 'FR', 'Gabon': 'GA', 'Gambia': 'GM', 'Georgia': 'GE',
  'Germany': 'DE', 'Ghana': 'GH', 'Greece': 'GR', 'Guatemala': 'GT',
  'Guinea': 'GN', 'Guinea-Bissau': 'GW', 'Haiti': 'HT', 'Honduras': 'HN',
  'Hungary': 'HU', 'Iceland': 'IS', 'India': 'IN', 'Indonesia': 'ID',
  'Iran': 'IR', 'Iraq': 'IQ', 'Ireland': 'IE', 'Israel': 'IL',
  'Italy': 'IT', 'Ivory Coast': 'CI', 'Jamaica': 'JM', 'Japan': 'JP',
  'Jordan': 'JO', 'Kazakhstan': 'KZ', 'Kenya': 'KE', 'Kosovo': 'XK',
  'Kuwait': 'KW', 'Kyrgyzstan': 'KG', 'Laos': 'LA', 'Latvia': 'LV',
  'Lebanon': 'LB', 'Liberia': 'LR', 'Libya': 'LY', 'Lithuania': 'LT',
  'Luxembourg': 'LU', 'Madagascar': 'MG', 'Malawi': 'MW', 'Malaysia': 'MY',
  'Mali': 'ML', 'Malta': 'MT', 'Mauritania': 'MR', 'Mauritius': 'MU',
  'Mexico': 'MX', 'Moldova': 'MD', 'Montenegro': 'ME', 'Morocco': 'MA',
  'Mozambique': 'MZ', 'Myanmar': 'MM', 'Namibia': 'NA', 'Nepal': 'NP',
  'Netherlands': 'NL', 'New Zealand': 'NZ', 'Nicaragua': 'NI', 'Niger': 'NE',
  'Nigeria': 'NG', 'North Korea': 'KP', 'North Macedonia': 'MK', 'Norway': 'NO',
  'Oman': 'OM', 'Pakistan': 'PK', 'Palestine': 'PS', 'Panama': 'PA',
  'Papua New Guinea': 'PG', 'Paraguay': 'PY', 'Peru': 'PE', 'Philippines': 'PH',
  'Poland': 'PL', 'Portugal': 'PT', 'Qatar': 'QA', 'Romania': 'RO',
  'Russia': 'RU', 'Rwanda': 'RW', 'Saudi Arabia': 'SA', 'Scotland': 'GB-SCT',
  'Senegal': 'SN', 'Serbia': 'RS', 'Sierra Leone': 'SL', 'Singapore': 'SG',
  'Slovakia': 'SK', 'Slovenia': 'SI', 'Somalia': 'SO', 'South Africa': 'ZA',
  'South Korea': 'KR', 'Korea Republic': 'KR', 'Spain': 'ES', 'Sri Lanka': 'LK',
  'Sudan': 'SD', 'Sweden': 'SE', 'Switzerland': 'CH', 'Syria': 'SY',
  'Tajikistan': 'TJ', 'Tanzania': 'TZ', 'Thailand': 'TH', 'Togo': 'TG',
  'Trinidad and Tobago': 'TT', 'Tunisia': 'TN', 'Turkey': 'TR', 'Turkmenistan': 'TM',
  'Uganda': 'UG', 'Ukraine': 'UA', 'United Arab Emirates': 'AE',
  'United States': 'US', 'Uruguay': 'UY', 'Uzbekistan': 'UZ', 'Venezuela': 'VE',
  'Vietnam': 'VN', 'Wales': 'GB-WLS', 'Yemen': 'YE', 'Zambia': 'ZM',
  'Zimbabwe': 'ZW',
}

// UK nations use subdivision codes — fall back to GB flag emoji
const SUBDIVISION_FLAGS = {
  'GB-ENG': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'GB-SCT': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  'GB-WLS': '🏴󠁧󠁢󠁷󠁬󠁳󠁿',
}

function isoToEmoji(code) {
  if (!code) return '🏳'
  if (SUBDIVISION_FLAGS[code]) return SUBDIVISION_FLAGS[code]
  const offset = 0x1F1E6
  const A = 65
  return code
    .toUpperCase()
    .split('')
    .map(c => String.fromCodePoint(c.charCodeAt(0) - A + offset))
    .join('')
}

export function getFlagEmoji(teamName) {
  const code = COUNTRY_CODES[teamName]
  return isoToEmoji(code)
}

export function getTeamDisplayName(teamName) {
  const flag = getFlagEmoji(teamName)
  return flag ? `${flag} ${teamName}` : teamName
}

// 2026 FIFA World Cup participants (USA, Canada, Mexico as hosts)
// Based on confirmed/projected qualifiers — 48 teams total
export const WORLD_CUP_2026_TEAMS = new Set([
  // Hosts
  'United States', 'Canada', 'Mexico',

  // CONMEBOL (6 direct)
  'Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Uruguay', 'Venezuela',

  // UEFA (16)
  'England', 'Germany', 'France', 'Spain', 'Portugal', 'Netherlands',
  'Belgium', 'Switzerland', 'Denmark', 'Austria', 'Scotland', 'Croatia',
  'Serbia', 'Poland', 'Turkey', 'Albania',

  // AFC (8)
  'Japan', 'South Korea', 'Iran', 'Australia',
  'Saudi Arabia', 'Uzbekistan', 'Iraq', 'Jordan',

  // CAF (9)
  'Morocco', 'Senegal', 'Nigeria', 'Cameroon', 'Egypt',
  'Tunisia', 'Ghana', 'Ivory Coast', 'South Africa',

  // CONCACAF (3 qualifying spots beyond the hosts)
  'Panama', 'Honduras', 'Costa Rica',

  // OFC (1)
  'New Zealand',

  // Interconfederal playoff spots (best estimate)
  'Paraguay', 'Indonesia',
])
