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

## Tiers

Public 2026 draft tiers were not available — Boris Chen's files still hold last
season's data, and FantasyPros only exports *overall* tiers, not per-position.
So position tiers are computed here: 1-D Jenks natural breaks (optimal dynamic
programming) over the blended rank inside each position, which is the same
"cluster players the experts treat as interchangeable" idea. Pool depth and tier
count per position are set in `POOL` in `merge.py`.

## The 6-point passing TD adjustment

Every public ranking assumes 4-point passing TDs. This league pays 6, which
widens the gap between elite and streamer QBs — historically about a round to a
round and a half at the top. The **6pt QB** toggle applies it (QB1–4 up 10
spots, QB5–10 up 7, QB11–16 up 4, rest up 1). Turn it off to see straight
consensus. It only changes where QBs sit in the *overall* list; it never
reorders QBs among themselves, so QB tiers are unaffected either way.

## Rebuilding

```bash
python merge.py   # sources -> merged.json (+ prints tiers and match diagnostics)
python build.py   # merged.json + template.html -> index.html
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
