"""Merge FantasyPros (primary) + Yahoo + JYJ into one ranked player set."""
import csv, json, os, re, unicodedata, collections

TEAM = {  # normalise every source to Sleeper-style codes
    'SFO': 'SF', 'LVR': 'LV', 'KAN': 'KC', 'NWE': 'NE', 'GNB': 'GB',
    'TAM': 'TB', 'NOR': 'NO', 'JAX': 'JAC', 'WSH': 'WAS', 'LA': 'LAR',
}
SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
# Nickname/legal-name splits between sources, keyed on the normalised form.
ALIAS = {'marquise brown': 'hollywood brown'}


def team(t):
    t = (t or '').strip().upper()
    return TEAM.get(t, t)


def norm(name):
    """Lowercase, strip accents/punctuation/suffixes -> comparable token list."""
    s = unicodedata.normalize('NFKD', name or '')
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('.', ' ').replace("'", '').replace('-', ' ')
    toks = [t for t in re.split(r'\s+', s) if t and t not in SUFFIX]
    return toks


def key_full(name):
    k = ' '.join(norm(name))
    return ALIAS.get(k, k)


def stars(v):
    """'4 out of 5' -> 4; '-' or blank -> None."""
    m = re.match(r'\s*(\d)', v or '')
    return int(m.group(1)) if m else None


def key_abbrev(name):
    """(first-initial, final-surname-token).

    Deliberately loose so the three sources' name styles collapse together:
    'A. St. Brown'/'Amon-Ra St. Brown' -> ('a','brown'), 'AJ Brown'/'A.J. Brown'
    -> ('a','brown'), 'J. Smith-Njigba' -> ('j','njigba'). Collisions are then
    resolved by position, team, and rank proximity in `attach`.
    """
    toks = norm(name)
    if not toks:
        return None
    return (toks[0][0], toks[-1] if len(toks) > 1 else toks[0])


# ---------------------------------------------------------------- FantasyPros
players = []
with open('fp_all.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        pos = re.sub(r'\d+', '', r['POS']).strip()
        if pos in ('K', 'DST'):
            continue
        players.append({
            'name': r['PLAYER NAME'].strip(),
            'team': team(r['TEAM']),
            'pos': pos,
            'posRank': int(re.sub(r'\D', '', r['POS'])),
            'bye': int(r['BYE WEEK']) if r['BYE WEEK'].strip().isdigit() else None,
            'fp': int(r['RK'].strip('"')),
            'fpTier': int(r['TIERS']) if r['TIERS'].strip() else None,
            'upside': stars(r['UPSIDE ']),
            'bust': stars(r['BUST ']),
            'sos': stars(r['SOS SEASON']),
            'ecrVsAdp': (r['ECR VS. ADP'] or '').strip(),
        })

# FantasyPros' "ECR VS. ADP" is signed ADP-minus-ECR (e.g. Chase RK=1, "+2" ->
# ADP 3; Gibbs RK=2, "-1" -> ADP 1), so the real ADP number is just RK + diff.
for p in players:
    m = re.match(r'^([+-]?\d+)$', p['ecrVsAdp'])
    diff = int(m.group(1)) if m else None
    p['adp'] = (p['fp'] + diff) if (diff is not None and p.get('fp')) else None

by_full = collections.defaultdict(list)
by_abbrev = collections.defaultdict(list)
for p in players:
    by_full[key_full(p['name'])].append(p)
    by_abbrev[key_abbrev(p['name'])].append(p)


def resolve(cands, pos, tm, rank, field):
    """Narrow same-key candidates by position, then team, then rank proximity.

    `field` is the source column being filled; already-filled players are
    dropped first so two same-named players can't both take the same rank
    (Bijan vs Brian Robinson, both ATL RB).
    """
    c = [x for x in cands if x.get(field) is None] or list(cands)
    c = [x for x in c if x['pos'] == pos] or c
    if len(c) > 1:
        c = [x for x in c if x['team'] == tm] or c
    if len(c) > 1:
        c = [min(c, key=lambda x: abs((x.get('fp') or rank) - rank))]
    return c[0] if len(c) == 1 else None


# --------------------------------------------------------------------- Yahoo
y_miss = []
for line in open('yahoo300.txt', encoding='utf-8').read().splitlines()[1:]:
    rank, name, tm, pos, avg = line.split('|')
    if pos in ('K', 'DST'):
        continue
    p = resolve(by_abbrev.get(key_abbrev(name), []), pos, team(tm), int(rank), 'yahoo')
    if p:
        p['yahoo'] = int(rank)
    else:
        y_miss.append(f'{rank} {name} {tm} {pos}')

# ----------------------------------------------------------------------- JYJ
j_miss, j_bad = [], []
for line in open('jyj.txt', encoding='utf-8').read().splitlines()[1:]:
    f = line.split('|')
    # The five leading and three trailing columns are always present; the
    # optional middle three (adp, consensus, injury) can lose a delimiter when
    # all are blank, so anchor from both ends rather than trusting positions.
    if len(f) < 8:
        j_bad.append(line)
        continue
    head, tail = f[:5], f[-3:]
    mid = f[5:-3] + [''] * 3
    f = head + mid[:3] + tail
    rank, name, tm, pos = f[0], f[1], f[2], f[3]
    if pos in ('PK', 'DEF'):
        continue
    cands = by_full.get(key_full(name)) or by_abbrev.get(key_abbrev(name)) or []
    p = resolve(cands, pos, team(tm), int(rank), 'jyj')
    if not p:
        # Keep anyone JYJ ranks clearly startable: FantasyPros' export has a
        # few real omissions (e.g. Ricky Pearsall) and a draft board that
        # silently hides a rosterable player is worse than one extra row.
        # Past ~130 the only JYJ-exclusive names are fullbacks and camp bodies.
        if int(rank) <= 130:
            p = {'name': name, 'team': team(tm), 'pos': pos, 'posRank': None,
                 'bye': int(f[4]) if f[4].isdigit() else None, 'fp': None,
                 'fpTier': None, 'upside': None, 'bust': None, 'sos': None,
                 'ecrVsAdp': '', 'jyj': int(rank), 'onlyJyj': True}
            players.append(p)
        else:
            j_miss.append(f'{rank} {name} {tm} {pos}')
            continue
    p['jyj'] = int(rank)
    p['inj'] = 'Inj' in (f[7] or '')
    p['rookie'] = 'R' in (f[7] or '').replace('Inj', '')
    p['oline'] = f[8] or None
    p['sosEarly'] = int(f[9]) if f[9] else None
    p['sosPlayoff'] = int(f[10]) if f[10] else None

# ------------------------------------------------------------------- Sleeper
# Sleeper's own default overall ranking (search_rank), for the "what's my
# draft room actually looking at" comparison. Read-only cache built once by
# fetch_sleeper.py - merge.py never hits the network itself.
# Rebuilt (not the original by_full/by_abbrev) so the JYJ-only additions
# above - e.g. Ricky Pearsall, missing from FantasyPros' own export - are
# still matchable here.
by_full_all = collections.defaultdict(list)
by_abbrev_all = collections.defaultdict(list)
for p in players:
    by_full_all[key_full(p['name'])].append(p)
    by_abbrev_all[key_abbrev(p['name'])].append(p)

s_miss = []
if os.path.exists('sleeper_players.json'):
    with open('sleeper_players.json', encoding='utf-8') as f:
        sleeper = json.load(f)
    # Sleeper uses (at least) two round-number placeholders for "no meaningful
    # rank" rather than omitting the field: 9999999 (2226 of ~3900 skill-position
    # entries) and 999 (269 entries - real ranks are all but unique, so 269
    # players tied at exactly the same rank is not organic). Every genuine rank
    # is otherwise a one-off value under ~2100. Both get dropped here, which is
    # what actually stops false matches (see position guard below): e.g.
    # inactive RB "Javorius Allen" (9999999) or a placeholder-ranked "Jayden
    # Reed" duplicate (999) would otherwise collide by first-initial+surname or
    # exact name with the real "Josh Allen"/"Jayden Reed" and overwrite their
    # true rank.
    SLEEPER_SENTINELS = {999, 9999999}
    for sp in sleeper.values():
        if sp.get('position') not in ('QB', 'RB', 'WR', 'TE') or not sp.get('search_rank') \
                or sp['search_rank'] in SLEEPER_SENTINELS:
            continue
        name = sp.get('full_name') or ('%s %s' % (sp.get('first_name') or '', sp.get('last_name') or '')).strip()
        pos, tm, rank = sp['position'], team(sp.get('team') or ''), sp['search_rank']
        cands = by_full_all.get(key_full(name)) or by_abbrev_all.get(key_abbrev(name)) or []
        # resolve()'s position filter falls back to the unfiltered list when it
        # would otherwise empty out - fine for genuine same-source position
        # typos, but Sleeper's dump includes decades of retired/inactive
        # players, so an abbrev-only hit (e.g. RB "Javorius Allen", inactive)
        # can collide with an unrelated real starter (QB "Josh Allen") purely
        # by first-initial+surname. Require the position class to actually
        # match before resolve() ever runs, so a same-position candidate has
        # to be genuinely absent before we call it a real miss.
        cands = [c for c in cands if c['pos'] == pos]
        p = resolve(cands, pos, tm, rank, 'sleeperRank')
        if p:
            p['sleeperRank'] = rank
        elif rank <= 300:  # deeper misses are just Sleeper's longer tail, not worth reporting
            s_miss.append(f'{rank} {name} {tm} {pos}')
else:
    print('sleeper_players.json not found - run `python fetch_sleeper.py` first; skipping Sleeper ranks.')

print(f'FantasyPros skill players: {len(players)}')
print(f'Yahoo matched: {sum(1 for p in players if p.get("yahoo"))}  unmatched: {len(y_miss)}')
for m in y_miss:
    print('   yahoo miss:', m)
print(f'JYJ matched: {sum(1 for p in players if p.get("jyj"))}  unmatched: {len(j_miss)}')
for m in j_miss:
    print('   jyj miss:', m)
if os.path.exists('sleeper_players.json'):
    print(f'Sleeper matched: {sum(1 for p in players if p.get("sleeperRank"))}  unmatched (rank<=300): {len(s_miss)}')
    for m in sorted(s_miss, key=lambda x: int(x.split(" ")[0])):
        print('   sleeper miss:', m)


# ------------------------------------------------------------------- blend
# FantasyPros carries the most expert inputs and is the only PPR-specific
# source, so it gets half the weight; Yahoo and JYJ split the rest. Weights
# are renormalised over whichever sources actually rank a given player.
WEIGHT = {'fp': 0.50, 'yahoo': 0.25, 'jyj': 0.25}
DEEP = 400  # stand-in rank so one missing source can't inflate a player

for p in players:
    num = den = 0.0
    for src, w in WEIGHT.items():
        if p.get(src):
            num += w * p[src]
            den += w
    p['blend'] = round(num / den, 2) if den else DEEP
    p['sources'] = sum(1 for s in WEIGHT if p.get(s))
    ranks = [p[s] for s in WEIGHT if p.get(s)]
    # How far apart the sources are — a big spread is a real draft-room signal.
    p['spread'] = (max(ranks) - min(ranks)) if len(ranks) > 1 else None

players.sort(key=lambda p: p['blend'])
for i, p in enumerate(players, 1):
    p['rank'] = i

# ------------------------------------------- no league-specific adjustment
# Deliberately none. Two of this league's settings push in opposite directions
# and roughly cancel:
#   - 6 points per passing TD (public rankings assume 4) lifts QBs;
#   - three flex spots on top of 2RB/2WR drain RB/WR far faster than the
#     rankings assume, which lifts those.
# An earlier build shifted QBs up but had no way to do the RB/WR half honestly
# (that needs value-over-replacement, which needs projected points, and all
# three sources are rank-only). Correcting one side alone just biased the board
# toward QBs, so the ranking below is straight blended consensus. The old shift
# is in git history if it is ever wanted back.

# -------------------------------------------------------------------- tiers
# FantasyPros' own per-position tiers, straight from their position exports.
# They are analyst-set, so they win outright over anything derived here; the
# banding below only covers players their position files leave out.
POSITIONS = ['QB', 'RB', 'WR', 'TE']

fp_tier = {}
for pos in POSITIONS:
    with open('fp_%s.csv' % pos, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            fp_tier[(pos, key_full(r['PLAYER NAME']))] = int(r['TIERS'])

untiered = []
for p in players:
    t = fp_tier.get((p['pos'], key_full(p['name'])))
    if t:
        p['tier'], p['tierSrc'] = t, 'fp'
    else:
        untiered.append(p)

# Anyone FantasyPros skips is slotted into whichever tier band their blended
# rank falls inside, so nobody vanishes off a position tab.
for pos in POSITIONS:
    edges = sorted(
        {p['tier']: p['blend']
         for p in sorted((x for x in players
                          if x['pos'] == pos and x.get('tierSrc') == 'fp'),
                         key=lambda x: -x['blend'])}.items())
    for p in (x for x in untiered if x['pos'] == pos):
        t = edges[-1][0] if edges else 1
        for tier, lo in edges:
            if p['blend'] < lo:
                t = max(1, tier - 1)
                break
        p['tier'], p['tierSrc'] = t, 'band'

# Position rank follows the blended order so each tab reads 1, 2, 3 ...
for pos in POSITIONS:
    for i, p in enumerate(sorted((x for x in players if x['pos'] == pos),
                                 key=lambda x: x['blend']), 1):
        p['posRankFinal'] = i

print('\ntiers from FantasyPros: %d   banded fallback: %d'
      % (sum(1 for p in players if p.get('tierSrc') == 'fp'), len(untiered)))
for pos in POSITIONS:
    g = sorted((p for p in players if p['pos'] == pos and p['tier'] <= 6),
               key=lambda x: (x['tier'], x['blend']))
    print('\n%s' % pos)
    cur = None
    for p in g:
        if p['tier'] != cur:
            cur = p['tier']
            print('\n  T%d:' % cur, end='')
        print(' %s%s' % (p['name'], '*' if p.get('tierSrc') == 'band' else ''), end='')
    print()

json.dump(players, open('merged.json', 'w'), indent=1)
print('\n\nwrote %d players' % len(players))
raise SystemExit

# --- superseded by the FantasyPros exports above; kept for reference --------
def jenks(vals, k):
    n = len(vals)
    k = min(k, n)
    if k <= 1:
        return [0]
    INF = float('inf')
    cost = [[0.0] * n for _ in range(n)]
    for i in range(n):
        s = sq = 0.0
        for j in range(i, n):
            s += vals[j]
            sq += vals[j] ** 2
            m = j - i + 1
            cost[i][j] = sq - s * s / m  # within-group variance
    dp = [[INF] * (k + 1) for _ in range(n + 1)]
    back = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for j in range(1, k + 1):
        for i in range(1, n + 1):
            for t in range(j - 1, i):
                c = dp[t][j - 1] + cost[t][i - 1]
                if c < dp[i][j]:
                    dp[i][j] = c
                    back[i][j] = t
    starts, i = [], n
    for j in range(k, 0, -1):
        starts.append(back[i][j])
        i = back[i][j]
    return sorted(starts)


# How deep each position stays relevant in a 12-team / 14-round / 3-flex draft,
# and how many tiers to cut that pool into.
POOL = {'QB': (26, 8), 'RB': (68, 12), 'WR': (78, 12), 'TE': (26, 8)}

for pos, (depth, ntiers) in POOL.items():
    group = [p for p in players if p['pos'] == pos]
    group.sort(key=lambda p: p['blend'])
    for i, p in enumerate(group, 1):
        p['posRankFinal'] = i
    pool = group[:depth]
    starts = set(jenks([p['blend'] for p in pool], ntiers))
    tier = 0
    for i, p in enumerate(pool):
        if i in starts:
            tier += 1
        p['tier'] = max(tier, 1)
    for p in group[depth:]:
        p['tier'] = ntiers + 1  # everyone past the useful pool

print('\n--- tiers ---')
for pos, (depth, ntiers) in POOL.items():
    group = sorted([p for p in players if p['pos'] == pos and p['tier'] <= ntiers],
                   key=lambda p: p['blend'])
    print(f'\n{pos}')
    cur = None
    for p in group:
        if p['tier'] != cur:
            cur = p['tier']
            print(f'  T{cur}:', end='')
        print(f" {p['name']}", end='')
    print()

json.dump(players, open('merged.json', 'w'), indent=1)
print(f'\nwrote {len(players)} players')

