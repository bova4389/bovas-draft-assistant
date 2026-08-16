"""Refresh the league/draft/user snapshots -> league.json, draft.json, users.json.

These three are small and change whenever the commissioner touches settings,
adds a member, or -- most importantly -- sets or reshuffles the draft order.
draft.json was captured while `draft_order` was still null, which is why the
built page had the team columns in league order.

The page itself can now re-read the draft order at runtime (Setup -> Sync draft
order), so this script is only needed to bake a fresh order into a new build.

Usage:
    python fetch_league.py
"""
import json
import urllib.request

LEAGUE_ID = '1383837552376545280'
API = 'https://api.sleeper.app/v1/league/' + LEAGUE_ID


def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def write(name, data):
    with open(name, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print('wrote', name)


def main():
    league = get(API)
    write('league.json', league)
    write('users.json', get(API + '/users'))

    draft = get('https://api.sleeper.app/v1/draft/' + league['draft_id'])
    write('draft.json', draft)

    order = draft.get('draft_order')
    if order:
        print('draft order (slot -> user_id):')
        for uid, slot in sorted(order.items(), key=lambda kv: kv[1]):
            print('  %2d  %s' % (slot, uid))
    else:
        print('draft order is still null on Sleeper.')


if __name__ == '__main__':
    main()
