# 2026-06-22 — Unattended-fit dimension for the per-sector dispatch contract

> **Status:** `complete` — Dispatch routine, scheduled empty-fire (no work order). Bugs-first found
> the open bugs blocked (BUG-0011 infra · BUG-0019 #1 owner-fork · BUG-0009 data-gated); the actionable
> signal is the **recurring empty-fire stall** two consecutive runs hit (#1274 and this one): rediscovering
> mid-run that the *headline* lanes all need a human. Built the previous run's explicitly-surfaced-but-
> unpromoted fix. Self-initiated (Q-0172). PR #1285, auto-merge armed on green.

> **Run type:** `routine · dispatch`

## What I'm about to do

The dispatch contract tags each `Now` item **▶ startable / ⛔ gated / 👤 maintainer** — that answers
*"may Claude **start** this?"* but NOT *"can an **unattended** run **complete and self-merge** it without
a human?"* So an empty-fire run picks a `▶` lane, starts it, and only then discovers it needs a live
guild walk, is `needs-hermes-review`, or commits external IP-sensitive data. PR #1274's ⟲ review named
this exact fix ("tag each queued lane with an unattended-fit flag — offline-verifiable? self-mergeable?
needs-live-verify? external-data/IP?") and explicitly left it **unpromoted**. This run promotes it.

Add an orthogonal **unattended-fit** dimension to each sector's `Dispatch` line:
- 🟢 `auto` — offline-verifiable AND self-mergeable (an unattended run can complete it + auto-merge on green)
- 🟡 `review` — buildable offline but `needs-hermes-review` (build + open PR, do NOT self-merge)
- 🔵 `live` — needs a live guild walk / runtime creds to verify (weak unattended fit)
- 🟠 `ext-data` — commits externally-sourced data (external-data safety brake → owner confirm first)

Then teach `dispatch_menu.py` to parse + surface it and add `--unattended` (aggregate: which sector, if
any, an empty-fire run can complete & merge), and make `check_sector_map.py` require the tag on every
sector's Dispatch line (self-maintaining, like the startability glyph). The payoff this run already
proved: the per-sector first-`▶` items (S2 eval cases · S3 substrate-kit · S4 nav layers) are 🟢 `auto` —
the empty-fire runs were anchoring on the *headline* (human-needed) lanes and missing them.

## Shipped (PR #1285)
- `scripts/dispatch_menu.py` — `unattended_fit()` parser, fit surfaced in `build_menu`/`sector_record`,
  and a new `--unattended` mode that ranks the lanes an empty-fire run can finish & merge (🟢 first,
  then 🟡, then 🔵/🟠, with a clear "build a 🟡 / promote an idea (Q-0172)" fallback nudge).
- `scripts/check_sector_map.py` — requires an `unattended-fit **<tag>**` token on every sector's
  Dispatch line (self-maintaining, exactly like the startability glyph; `_UNATTENDED_FIT` regex).
- `docs/repo-sector-map.md` — new § "the unattended-fit tag" defining the four tags + the payoff.
- `docs/roadmap.md` — header definition + the five per-sector tags (S1 🟡 · S2/S3/S4 🟢 · S5 🔵).
- `tests/unit/scripts/test_dispatch_menu.py` (+5) / `test_check_sector_map.py` (+1) — parsing,
  ranking, fallback, and the checker enforcement. 30 tests green; full suite 11479 green; arch 0.

## Live `--unattended` output (proves the thesis)
```
🟢 SELF-MERGEABLE now: S2 (P1-1 BTD6 eval cases) · S3 (substrate-kit) · S4 (3-tap nav layers)
🟡 build PR for review: S1 (Layer B)
```
The empty-fire runs had anchored on the *headline* lanes (Project Moon · AI-panel · botsite — all
🔵/🟠/human-needed) and missed the per-sector first-▶ items, which are 🟢 auto. That gap is exactly
what the tag closes.

## Decisions made alone (ratify if wrong)
- **Tag lives on the Dispatch line, not per-item.** The dense inline `Now` prose (one bullet, many
  ▶/⛔/👤 sub-items) makes reliable per-item tagging fragile; the Dispatch line is structured, parseable,
  and already the home of the executor dimension. One unattended-fit tag per sector, applied to the
  sector's *currently-resolved* startable lane.
- **S2 (BTD6 eval cases) = 🟢 auto:** the eval cases assert already-grounded facts as offline tests →
  offline-verifiable + self-mergeable. (The *data-gated* BUG-0009 newest-towers work is a different,
  blocked lane — not what the resolver currently surfaces for S2.)
- **S5 = 🔵 live:** its live ops lanes need a maintainer token / runtime; noted that the thin in-repo
  `check_*`/workflow-tooling sub-lane is itself 🟢 (but S5's resolver state is already non-Claude).

## 💡 Session idea (Q-0089)
**Reconciliation pass should *set* the unattended-fit tag as it plans each band** — make it part of the
queue-slot gate-state tag the band passes already attach (§6 of the band records), so the dimension stays
fresh by construction instead of needing a dispatch run to (re)classify. This run added the *mechanism +
the current five tags*; the natural next step is for the planner that already tags slots ▶/⛔/👤 +
gate-state to also stamp 🟢/🟡/🔵/🟠, and `check_sector_map.py` now fails if it forgets. (Captured as the
forward direction; the checker already enforces presence, so it won't silently rot.)

## ⟲ Previous-session review (Q-0102 — #1274 allowlist-curl)
- **Did well:** the lane assessment was genuinely useful — it named *why* each headline lane is a poor
  unattended fit (external-IP data · needs-live-walk · Q-0106 config) rather than just "blocked," and it
  explicitly proposed the unattended-fit flag. That precision is what made *this* run able to act in one
  hop instead of re-deriving the wall.
- **Missed / could improve:** it left the fix as prose ("captured as the forward direction; not promoted
  to a plan") — so this run still had to start by rediscovering the same wall before building. The
  concrete system improvement it *named* but didn't *build* is exactly what this run shipped; the meta-
  lesson is that a surfaced-but-unbuilt workflow fix is itself the kind of contained, offline, self-
  mergeable lane an empty-fire run should grab (idea→plan→ship is open, Q-0172) — which is now also the
  literal 🟢-auto recommendation the tool emits.

## 🛠 Doc audit (Q-0104)
- `check_current_state_ledger.py --strict`: not re-run as blocking here — this PR adds no merged-PR
  ledger entry (Recently-shipped is reconciliation-owned; the durable home for this change is
  repo-sector-map.md + roadmap.md + this card, all updated).
- New convention reachable: yes — `repo-sector-map.md` § "the unattended-fit tag" + the roadmap header
  both link to it and to `dispatch_menu.py --unattended`.
- No owner decision to record (Q-0172 self-initiated; flagged below). No new top-level doc.

## 📤 Run report
- **Did:** added the orthogonal unattended-fit dimension to the per-sector dispatch contract
  (tag + `--unattended` resolver + checker enforcement + convention docs + tests), fixing the recurring
  empty-fire lane-discovery stall. · **Outcome:** shipped (PR #1285, auto-merge armed on green)
- **Shipped:** PR #1285 — `dispatch_menu.py` (+`--unattended`) · `check_sector_map.py` enforcement ·
  `roadmap.md` + `repo-sector-map.md` convention · +6 tests
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (tooling/docs only; merge auto-deploys nothing runtime)
- **⚑ Self-initiated (Q-0172):** **yes** — promoted #1274's surfaced-but-unpromoted unattended-fit fix
  into an implementation. Contained, offline-verifiable, IP-clean, test-covered → self-merge on green.
- **↪ Next:** the tool now points the way — an empty-fire run can run `python3.10 scripts/dispatch_menu.py
  --unattended` and pick a 🟢 lane (S2 BTD6 eval cases · S3 substrate-kit PR-2 remainder · S4 3-tap nav
  middle/bottom layers) to build & self-merge, or a 🟡 lane (S1 Layer B) for review. The band-#1260 queue
  otherwise stands.

## 📊 Telemetry
| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1285, auto-merge armed; born-red hold flipped last) |
| CI-red rounds | 2 expected (born-red `check_session_gate` holds) + black/ruff E501 fixed locally pre-final-push |
| Repo-rule trips | 0 arch errors; formatters resolved (emoji double-width E501 — noted for future emoji-heavy strings) |
| New ideas contributed | 1 (planner sets the fit tag at band-plan time) |
| Ideas groomed | 0 (the build itself promoted #1274's deferred idea) |
