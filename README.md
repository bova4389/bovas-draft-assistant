# 2 Mitchs 1 Cup — Draft Assistant (2026)

`draft-assistant.html` is the whole thing: one self-contained file, no build step,
no network needed except the optional Sleeper sync. Open it on the iPad and go.

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
python build.py   # merged.json + template.html -> draft-assistant.html
```

Edit `template.html` for UI changes, never `draft-assistant.html` — it is generated.

## Known limitation

Safari sometimes refuses `localStorage` for pages opened straight off the
filesystem. The page detects this and shows a banner; picks then live only in
memory and a refresh loses them. Serving the file over http (or hosting it,
e.g. GitHub Pages like Bova's Picks) removes the risk entirely.
