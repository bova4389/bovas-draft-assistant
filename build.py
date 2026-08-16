"""Inject merged player data + league config into the HTML template."""
import io, json

players = json.load(open('merged.json'))
league_raw = json.load(open('league.json'))
draft_raw = json.load(open('draft.json'))
users_raw = json.load(open('users.json'))

# Short keys keep the embedded blob small enough to stay comfortable on an iPad.
out = []
for p in sorted(players, key=lambda x: x['rank']):
    out.append({
        'n': p['name'], 't': p['team'], 'p': p['pos'],
        'b': p['bye'], 'tr': p['tier'], 'pr': p['posRankFinal'],
        'r': p['rank'],
        'fp': p.get('fp'), 'yh': p.get('yahoo'), 'jy': p.get('jyj'),
        'sp': p.get('spread'),
        'adp': p.get('adp'), 'sr': p.get('sleeperRank'),
        'i': bool(p.get('inj')), 'rk': bool(p.get('rookie')),
        'only': bool(p.get('onlyJyj')),
    })

# draft_order maps user_id -> slot once the commissioner sets it; it is null
# before that, in which case we fall back to league order. Either way the page
# can re-read it at runtime, so a reshuffle after this build does not need a
# rebuild -- see the Sync draft order button in Setup.
order = draft_raw.get('draft_order')
names = {}
for u in users_raw:
    names[u['user_id']] = (u.get('metadata') or {}).get('team_name') or u.get('display_name')

if order:
    teams = [None] * league_raw['total_rosters']
    for uid, slot in order.items():
        if 1 <= slot <= len(teams):
            teams[slot - 1] = names.get(uid, 'Team %d' % slot)
    teams = [t or ('Team %d' % (i + 1)) for i, t in enumerate(teams)]
else:
    teams = [names[u['user_id']] for u in users_raw]

# Sleeper roster_positions -> startable slots, in lineup order.
FLEX = {'FLEX': ['RB', 'WR', 'TE'], 'WRRB_FLEX': ['RB', 'WR'],
        'SUPER_FLEX': ['QB', 'RB', 'WR', 'TE'], 'REC_FLEX': ['WR', 'TE']}
starters, seen = [], {}
for rp in league_raw['roster_positions']:
    if rp == 'BN':
        continue
    if rp in FLEX:
        seen[rp] = seen.get(rp, 0) + 1
        label = 'FLEX' if rp == 'FLEX' else 'W/R'
        starters.append({'label': label + (str(seen[rp]) if seen[rp] > 1 or rp != 'FLEX' else ''),
                         'pos': FLEX[rp]})
    else:
        seen[rp] = seen.get(rp, 0) + 1
        n = sum(1 for x in league_raw['roster_positions'] if x == rp)
        starters.append({'label': rp + (str(seen[rp]) if n > 1 else ''), 'pos': [rp]})

me = next((i + 1 for i, t in enumerate(teams) if t == 'cbova1222'), 1)
league = {
    'name': league_raw['name'],
    'draftId': league_raw['draft_id'],
    'rounds': draft_raw.get('settings', {}).get('rounds', 14),
    'teams': teams,
    'starters': starters,
    'defaultMe': me,
    'orderKnown': bool(order),
    # user_id -> team label, so the page can rebuild `teams` from a freshly
    # fetched draft_order without downloading the users endpoint itself.
    'users': names,
}

stamp = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')

html = io.open('template.html', encoding='utf-8').read()
html = html.replace('/*PLAYERS_JSON*/', json.dumps(out, separators=(',', ':')))
html = html.replace('/*LEAGUE_JSON*/', json.dumps(league, separators=(',', ':')))
html = html.replace('/*BUILD*/', stamp)

for token in ('/*PLAYERS_JSON*/', '/*LEAGUE_JSON*/', '/*BUILD*/'):
    assert token not in html, 'placeholder left unfilled: ' + token
# index.html so GitHub Pages serves it at the bare repo URL.
io.open('index.html', 'w', encoding='utf-8').write(html)
print('build', stamp)

print('players embedded:', len(out))
print('teams:', teams)
print('starters:', [s['label'] for s in starters])
print('your slot default:', me, '->', teams[me - 1])
print('size: %.0f KB' % (len(html) / 1024))
