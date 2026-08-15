"""One-time download of Sleeper's full NFL player list -> sleeper_players.json.

Sleeper's docs ask that GET /v1/players/nfl not be hit more than once a day
(the response is ~5MB and rarely changes), so this caches to disk and only
re-fetches when explicitly forced. merge.py reads the cache; it never calls
the network itself.

Usage:
    python fetch_sleeper.py            # fetch only if no cache on disk
    python fetch_sleeper.py --force    # re-fetch even if cache exists
"""
import json
import sys
import urllib.request

CACHE = 'sleeper_players.json'
URL = 'https://api.sleeper.app/v1/players/nfl'


def main():
    import os
    if os.path.exists(CACHE) and '--force' not in sys.argv:
        print(f'{CACHE} already exists - skipping fetch (pass --force to re-download).')
        return
    print(f'Fetching {URL} ...')
    with urllib.request.urlopen(URL, timeout=60) as r:
        data = json.load(r)
    with open(CACHE, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print(f'Wrote {len(data)} players to {CACHE}')


if __name__ == '__main__':
    main()
