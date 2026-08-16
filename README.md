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

## Draft order

Sleeper's `draft_order` (user_id → slot) is null until the commissioner sets it,
and it can be reshuffled right up to the first pick. It was null when this was
first built, so the team columns sat in league order and stayed there — nothing
re-read it.

The page now pulls it live from `/v1/draft/<id>`:

- **automatically on every page load**, quietly — it only says anything if a
  team actually moved;
- **on demand** from `Sync draft order` on the Draft Board tab, or the same
  button in Setup.

`build.py` embeds a `users` map (user_id → team name) so the page can rebuild the
order by itself. A synced order is saved to `localStorage` and wins over the one
baked into the build.

**Picks stay with their slot, exactly as they do on Sleeper** — whoever ends up
in slot 3 owns 1.03. What follows a team's *name* to its new column is your own
slot, the Rosters view, and the add-to-team target, so "which team is mine"
survives a reshuffle.

`python fetch_league.py` refreshes `league.json` / `draft.json` / `users.json`
so a new build bakes in the current order; it is not needed just to correct a
running page.

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

## Suggest tab — live pick recommendations

Optional (Setup → Pick suggestions), and it changes nothing else when off.

The useful question mid-draft is not "who is best" but **"who will not survive
the 11–13 picks until my next turn"**, so that is what it scores. At slot 6 the
gaps are a steady 13, 11, 13, 11 — you never pick back-to-back, and 12 players
leave the board every time.

**There are no projected points anywhere in this.** All three ranking sources
are rank-only, which is the same wall the 6pt-passing-TD adjustment hit. Real
VOR needs projections, so anything printing a point total off this data would be
inventing it. Everything below is ordinal on purpose.

| Input | Where it comes from |
|---|---|
| Value | FantasyPros tiers, anchored on the blended board — flat inside a tier, because that is what a tier means |
| When a player goes | `adp` blended with Sleeper's `search_rank`, converted to an ordinal within this pool |
| How sure we are | How far those two signals disagree, which widens with rank |
| Roster fit | The same `fillLineup()` the Rosters tab uses |
| Risk | `spread`, `inj`, the curated sleeper/bust list, and your own marks |

**Scoring:** `need × risk × fit × urgency × (value + 0.75 × dropoff)`, where
dropoff is the value you lose at that position by waiting a turn — the term that
makes it a decision rather than a ranking.

Some deliberate calls:

- **Value decays exponentially, not as a power law.** A power curve is so flat
  past pick 100 that every remaining player scores within a few percent of every
  other; the scarcity term washed out and roster need decided everything alone,
  which briefly put a rank-200 backup QB above real starters.
- **A 4th RB/WR is a starter, a 2nd QB is not.** Three flex spots and no
  superflex. This asymmetry moves more picks than anything else in the formula.
- **Risk preference inverts.** Early picks want agreement — a bust in round 2 is
  unrecoverable. Late picks want variance: a "safe" 12th-rounder is worthless
  because you will drop him in week 3 regardless, so only the ceiling counts.
- **Bye weeks are a tiebreaker, nothing more.** With five bench spots and free
  agency, a bye clash is a one-week annoyance; it only really bites at QB and TE
  where you start exactly one. Two RBs out of one backfield is the genuine
  roster-construction negative, and it is not a bye problem at all.
- **Runs need three picks to count.** QB sits at a ~10% base rate, so one extra
  in a twelve-pick window would otherwise register as the room accelerating 70%.
- **Draft buttons only appear on your own pick**, so the tab cannot quietly hand
  a player to whoever is actually on the clock.

`Safe to wait on` is drawn from the players just below the recommendations, not
from the whole board — filtering everything surfaces deep bench names that
survive only because nobody wants them.

Still to build: opponent-need modelling (we know all 11 other rosters from the
pick feed, so we can predict what the next 12 picks actually target, which is
much sharper than league-average ADP).

## The `split` number

Some rows end with `split 49`. That is **the spread between our three ranking
sources on that player — their worst rank minus their best.**

A split of 2 (Ja'Marr Chase) means FantasyPros, Yahoo and JYJ all landed in the
same place and the blended rank is a settled opinion. A split of 60 means one
source likes him five rounds more than another, and the blended rank is the
midpoint of a real argument rather than a consensus.

It is only rendered at **25 or above**, where the disagreement stops being noise.
Computed in `merge.py` as `max(ranks) - min(ranks)`, and null for anyone only one
source ranks. High-split players are disproportionately the ones showing up on
sleeper and bust lists, which is why the Sleepers & Busts cards surface it.

Sleeper's player dump uses two round-number placeholders for "no meaningful
rank" (`9999999` and `999`) instead of omitting the field, which `merge.py`
filters out — otherwise an inactive/irrelevant same-initial-and-surname player
(e.g. retired RB "Javorius Allen") can collide with a real starter ("Josh
Allen", QB) and stamp them with the placeholder instead of a real rank.

## Sleepers & Busts tab

53 curated candidates (25 sleepers, 28 busts) with the analyst write-up behind
each one, sourced from seven national lists:

| Source | Published |
|---|---|
| ESPN sleepers/busts/breakouts panel | Aug 11 2026 |
| FantasyPros "13 players to avoid" | Aug 2026 |
| FantasyPros "do not draft: 6 busts" | Aug 7 2026 |
| CBS — Jamey Eisenberg's do-not-draft list | Jul 25 2026 |
| RotoWire sleepers: rookies and sophomores | Jul 27 2026 |
| RotoWire "6 busts to avoid" | Aug 4 2026 |
| Draft Sharks sleepers | Aug 4 2026 |
| NFL.com six late-round sleepers | Aug 2026 |

**Every source must be published on or after July 1.** Anything from the spring
predates camp and most of free agency. Sports Illustrated's 2026 breakout list
was pulled for exactly this reason — it is dated Dec 29 2025 and its team
assignments are stale.

**Teams and ranks come from `merged.json`, never from the articles.** Several of
them had players on the wrong team (one put Jaxson Dart in New Orleans, another
had Isaiah Likely still in Baltimore). The curated list stores only a name, which
`buildSpot()` resolves through the same normaliser the Sleeper sync uses, so
suffix and punctuation differences do not have to line up. An unresolved name is
dropped and logged to the console rather than rendered without a team.

Where two outlets genuinely disagree, the card says so instead of picking a side
— Luther Burden III is an ESPN breakout and a FantasyPros do-not-draft in the
same month, and the Buffalo pair (DJ Moore, Khalil Shakir) are each cited as the
reason to fade the other.

### Icons and your own marks

Flagged players carry a 🚀 (sleeper) or 💣 (bust) badge on every player list.
Tapping it jumps to that player's write-up and flashes the card — it never
drafts them. Researched badges are permanent.

**Mark** in the toolbar enters marking mode, where tapping a player cycles
🚀 → 💣 → off for your own candidates. It uses the same loud sticky banner as
add-to-team mode, because being stuck in a tap-does-something-else mode mid-draft
would be worse than the banner being noisy. Your marks render **dashed** so a
hunch never reads as a researched pick, get their own sections on the tab, and
are keyed by player **name** — rebuilding `merged.json` reshuffles pool indexes,
and a mark surviving that is worth more than matching how picks are stored.

The badge sits in its own row column rather than inline in the name. `.nm` sets
`overflow:hidden` for the ellipsis, which clips a pseudo-element hit area down to
the text height; in the row it gets a real 41×42px target. Rows without a mark
omit it and `.mid` absorbs the width, so the right-hand badges stay aligned.

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
python fetch_league.py    # refresh league/draft/users snapshots (incl. draft order)
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
- Tap a 🚀 or 💣 badge to read why that player is flagged. **Mark** adds your own.
- Drafted rows show the owner as a chip between the name and the position badge.
- **Rosters** tab: pick any team from the dropdown to see their picks by round,
  each with a `×` to remove it, plus **Add player** to assign straight to that
  team. This is the fast path for fixing a mis-tap.
- Everything is sized for an Apple Pencil: 52px rows, 44px `×` buttons,
  `touch-action: manipulation` so taps register without the double-tap-zoom delay,
  and no hover-dependent controls.
