"""Mike Clay's 2026 NFL Projection Guide -> clay_offense.json (team scoring ranks).

The guide is a public PDF on ESPN's CDN, refreshed through Week 1. Two numbers
per team are pulled out of it:

  pf      projected points scored, from the Projected Standings page (p61).
          This is the actual "scoring offense" number and drives the rank.
  offPts  projected *fantasy* points scored by that team's QB/RB/WR/TE, summed
          from the Total line of the team's own page (p2-33). Clay's Pts column
          is full PPR, which is this league's scoring.

pf is a whole number, so it ties often (three ties in the 2026 guide). offPts
breaks them - it is the same question asked at higher resolution.

Team pages are matched to teams by their (pf, pa) pair rather than by page
order. Page order happens to be alphabetical, but nothing in the PDF promises
that, and a silently mis-assigned offense would be worse than a crash.

    pip install pypdf
    python fetch_clay.py [--local clay2026.pdf]
"""
import io, json, re, sys, urllib.request

from pypdf import PdfReader

URL = ('https://g.espncdn.com/s/ffldraftkit/26/'
       'NFLDK2026_CS_ClayProjections2026.pdf')

# Clay writes out full team names; the rest of the project keys off the
# abbreviations Sleeper/FantasyPros use (JAC not JAX, ARI not ARZ).
TEAMS = {
    'Arizona Cardinals': 'ARI', 'Atlanta Falcons': 'ATL',
    'Baltimore Ravens': 'BAL', 'Buffalo Bills': 'BUF',
    'Carolina Panthers': 'CAR', 'Chicago Bears': 'CHI',
    'Cincinnati Bengals': 'CIN', 'Cleveland Browns': 'CLE',
    'Dallas Cowboys': 'DAL', 'Denver Broncos': 'DEN',
    'Detroit Lions': 'DET', 'Green Bay Packers': 'GB',
    'Houston Texans': 'HOU', 'Indianapolis Colts': 'IND',
    'Jacksonville Jaguars': 'JAC', 'Kansas City Chiefs': 'KC',
    'Las Vegas Raiders': 'LV', 'Los Angeles Chargers': 'LAC',
    'Los Angeles Rams': 'LAR', 'Miami Dolphins': 'MIA',
    'Minnesota Vikings': 'MIN', 'New England Patriots': 'NE',
    'New Orleans Saints': 'NO', 'New York Giants': 'NYG',
    'New York Jets': 'NYJ', 'Philadelphia Eagles': 'PHI',
    'Pittsburgh Steelers': 'PIT', 'San Francisco 49ers': 'SF',
    'Seattle Seahawks': 'SEA', 'Tampa Bay Buccaneers': 'TB',
    'Tennessee Titans': 'TEN', 'Washington Commanders': 'WAS',
}

# Div Team Win Loss Fav PF PA Diff Sch. The draft-order table is printed to the
# right of the standings and lands on the same extracted line, so the pattern is
# anchored to the team name and stops after the eight columns it wants.
STANDINGS = r'\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(\d+)'


def load(path=None):
    if path:
        return io.open(path, 'rb').read()
    print('downloading', URL)
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def main(path=None):
    raw = load(path)
    print('pdf: %.1f MB' % (len(raw) / 1048576.0))
    rd = PdfReader(io.BytesIO(raw))

    updated = re.search(r'Updated:\s*(\S+)', rd.pages[0].extract_text() or '')
    updated = updated.group(1) if updated else '?'

    # --- projected standings: points for / against -------------------------
    page = None
    for i in range(len(rd.pages)):
        t = rd.pages[i].extract_text() or ''
        if '2026 Projected Standings' in t or 'Projected Standings' in t:
            page, txt = i, t
            break
    if page is None:
        raise SystemExit('could not find the Projected Standings page')
    print('standings on pdf page', page + 1)

    teams = {}
    for name, ab in TEAMS.items():
        m = re.search(re.escape(name) + STANDINGS, txt)
        if not m:
            raise SystemExit('no standings row for ' + name)
        teams[ab] = {'name': name, 'win': float(m.group(1)),
                     'pf': int(m.group(4)), 'pa': int(m.group(5))}

    # --- team pages: offensive fantasy points ------------------------------
    # Identified by the (pf, pa) pair printed on each page, not by page order.
    bypfpa = {(t['pf'], t['pa']): ab for ab, t in teams.items()}
    if len(bypfpa) != 32:
        raise SystemExit('pf/pa pairs are not unique - cannot map team pages')

    for i in range(len(rd.pages)):
        t = rd.pages[i].extract_text() or ''
        head = re.search(r'Total (\d+) (\d+) \d+%', t)
        tot = re.search(r'^Total((?: -?\d+){16})', t, re.M)
        if not head or not tot:
            continue
        ab = bypfpa.get((int(head.group(1)), int(head.group(2))))
        if ab and 'offPts' not in teams[ab]:
            # Gm Att Comp Yds TD INT Sk | Att Yds TD | Tgt Rec Yds TD | Pts Rk
            teams[ab]['offPts'] = int(tot.group(1).split()[14])

    missing = [ab for ab, t in teams.items() if 'offPts' not in t]
    if missing:
        raise SystemExit('no team page matched: ' + ', '.join(missing))

    # --- ranks -------------------------------------------------------------
    for i, ab in enumerate(sorted(teams, key=lambda a: (-teams[a]['pf'],
                                                        -teams[a]['offPts'])), 1):
        teams[ab]['rank'] = i
    for i, ab in enumerate(sorted(teams, key=lambda a: -teams[a]['offPts']), 1):
        teams[ab]['fRank'] = i

    out = {'source': "Mike Clay's 2026 NFL Projection Guide",
           'url': URL, 'updated': updated, 'teams': teams}
    json.dump(out, open('clay_offense.json', 'w'), indent=1, sort_keys=True)

    print('\nguide updated %s   wrote clay_offense.json\n' % updated)
    print('  #  tm    PF   offPts(PPR)')
    for ab in sorted(teams, key=lambda a: teams[a]['rank']):
        t = teams[ab]
        band = 'TOP' if t['rank'] <= 10 else ('BOT' if t['rank'] >= 23 else '   ')
        print('  %2d %-4s %4d  %5d   %s  %s'
              % (t['rank'], ab, t['pf'], t['offPts'], band, t['name']))


if __name__ == '__main__':
    a = sys.argv[1:]
    main(a[1] if len(a) > 1 and a[0] == '--local' else None)
