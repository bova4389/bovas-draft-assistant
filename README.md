# 2 Mitchs 1 Cup — Draft Assistant (2026)

`index.html` is the whole thing: one self-contained file, no build step, no network
needed except the optional Sleeper sync. Open it on the iPad and go.

Hosted on GitHub Pages so the iPad can reach it from anywhere — and so Safari
actually allows `localStorage`, which it refuses for `file://` pages.

## League (pulled from Sleeper, id `1383837552376545280`)

- 12 teams, snake, 14 rounds. Draft: **Sun Aug 16 2026, 2:00 PM**.
- Full PPR (`rec: 1.0`), **6 points per passing TD**, no TE premium.
- Starters: QB, RB, RB, WR, WR, TE, FLEX (R/W/T), W/R, W/R — 9 starters, 5 bench.
- No K, no DST — both stripped from the player pool.

## Where the rankings come from

| Source | Weight | Notes |
|---|---|---|
| FantasyPros PPR ECR | 0.50 | Most experts behind it, only PPR-specific source, supplies tiers/bye/upside |
| Yahoo consensus (6 analysts) | 0.25 | Current, includes 2026 rookies |
| JYJ 8/10/26 | 0.25 | Adds injury flags, O-line grade, playoff SOS |

Weights renormalise over whichever sources actually rank a player, so a missing
source never inflates someone.

**Deliberately excluded:** `Fantasy Football Draft Rankings (2026).csv` from the
ZIP. It is dated 2026-02-24 — before free agency and the 2026 draft — so it has
no rookies at all and stale teams (A.J. Brown on PHI, not NE). Blending it in
would have dragged good players down for no reason.

## ADP and Sleeper rank — draft-room value check

Each row also shows two numbers next to the blended rank, so you can see where
the room is likely to actually take a player relative to our own list:

- **A (ADP)** — real-world average draft position, reconstructed as FantasyPros'
  own rank plus their "ECR VS. ADP" differential (already in `fp_all.csv`, no
  extra download).
- **S (Sleeper rank)** — Sleeper's own `search_rank`, the field its app sorts
  the default draft-room player list by. Fetched once via `fetch_sleeper.py`
  (`python fetch_sleeper.py`, ~5MB, cached to `sleeper_players.json` and
  gitignored) and matched into `merge.py`.

A number turns **green** when it sits 50+ spots later than our rank (the room
will likely let them fall — safe to wait) and **red** when it sits 50+ spots
earlier (someone else will likely grab them first — reach now if you want them).

Sleeper's player dump uses two round-number placeholders for "no meaningful
rank" (`9999999` and `999`) instead of omitting the field, which `merge.py`
filters out — otherwise an inactive/irrelevant same-initial-and-surname player
(e.g. retired RB "Javorius Allen") can collide with a real starter ("Josh
Allen", QB) and stamp them with the placeholder instead of a real rank.

## Tiers

Straight from FantasyPros' per-position exports (`fp_QB.csv` … `fp_TE.csv`) —
analyst-set, not derived. 439 of 441 players match by name; the two they omit
get banded into whichever tier their blended rank falls inside, and are marked
`tierSrc: "band"` in `merged.json`.

QB has 9 tiers, RB 12, WR 13, TE 11.

Because the blend is only 50% FantasyPros, blended rank and FantasyPros tier
occasionally disagree. Position tabs therefore sort **tier-major** (tier first,
blended rank within the tier) so the tier bars stay in order; the Overall tab
sorts purely by blended rank and shows the tier as a badge.

An earlier build computed tiers with Jenks natural breaks because no 2026
per-position tiers were published anywhere — Boris Chen's fftiers S3 files still
serve last season's data. That code is retained below the `raise SystemExit` in
`merge.py` for reference only.

## No league-specific adjustment — on purpose

Two of this league's settings pull in opposite directions and roughly cancel:

- **6 points per passing TD** (public rankings assume 4) lifts QBs;
- **three flex spots** on top of 2RB/2WR drain RB/WR far faster than the
  rankings assume, which lifts those.

An earlier build shifted QBs up for the first one, but there was no honest way
to do the RB/WR half: that needs value-over-replacement, VOR needs projected
points, and all three sources are rank-only. Correcting one side alone just
biased the board toward QBs. So the ranking is straight blended consensus, and
Josh Allen sits at overall 27 where the experts put him.

The old shift is in git history if it is ever wanted back.

## Rebuilding

```bash
python fetch_sleeper.py   # one-time: caches Sleeper's player list -> sleeper_players.json
python merge.py           # sources -> merged.json (+ prints tiers and match diagnostics)
python build.py           # merged.json + template.html -> index.html
```

Edit `template.html` for UI changes, never `index.html` — it is generated, and
`build.py` stamps it with a build time shown in the Setup dialog. If the iPad
looks stale after a deploy, open Setup and check that stamp before debugging
anything else.

## Using it during the draft

- Tap any player row to draft them to whoever is on the clock; the dropdown at
  the top overrides the team first. Tap a drafted player again to undo.
- The filter button cycles **Hide drafted → Show all → Only drafted**.
- Drafted rows show the owner as a chip between the name and the position badge.
- **Rosters** tab: pick any team from the dropdown to see their picks by round,
  each with a `×` to remove it, plus **Add player** to assign straight to that
  team. This is the fast path for fixing a mis-tap.
- Everything is sized for an Apple Pencil: 52px rows, 44px `×` buttons,
  `touch-action: manipulation` so taps register without the double-tap-zoom delay,
  and no hover-dependent controls.
