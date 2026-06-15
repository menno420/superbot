# Session — P1-3 machine-checkable contract invariants (the cross-cutting "stays fixed" layer)

> **Status:** `complete`

## What I did

The next ▶ startable plan slice (band-#900 decade queue slot 3 · hardening roadmap §P1-3). The
mining lane was already complete (D/A/B/C/E/F shipped) and the Railway log-triage skill had shipped
(#906), so P1-3 invariants was the genuine next slice. Per the 2026-06-15 `current-state.md`
finding, P1-3 is **"identify a specific uncovered contract and add an invariant, or close the track
as substantially-covered"** — not "land one per track from scratch."

I reviewed all four named tracks (settings · games terminal-state · AI declared-vs-consumed ·
BTD6 provenance), found + closed the **two** genuine buildable-now gaps with new CI-runnable AST
invariants, and closed the other two with a disposition doc. Both new guards were verified to
actually fire (a guard that can't fail is worthless).

## What shipped (PR #917)

- **Settings gap → closed.** `tests/unit/invariants/test_settings_declared_vs_consumed_parity.py`
  — the *explicitly-named* missing invariant (settings readiness map §Required #3 / §Bugs:
  "Declaration-to-runtime-consumer parity is manually verified, not invariant-backed"). It proves
  every declared `SettingSpec` (63) has a runtime reader, handling all four read patterns the code
  actually uses: literal `resolve_value`/`resolve_setting(g, sub, name)`; `resolve_batch` /
  dynamic-name resolution (conservatively consumes the whole subsystem — e.g. the AI config
  projection's `resolve_setting(g, "ai", legacy_key)` loop); and key-constant / raw-key references
  outside the declaration (legacy `db.get_setting` **and** the binding/governance lane, e.g.
  `moderation.trusted_role` consumed as `legacy_key=` in `binding_backfill`/`config_arbitration`).
  Result: **0 dead settings**. A future editable-no-op now fails CI.
- **Games gap → closed.** A third check on `tests/unit/invariants/test_game_wager_write_boundary.py`
  — `test_two_sided_economy_calls_are_accounted_for`. The existing fence guards a hardcoded
  `_WAGER_FILES` list, catching only *deletion* staleness; the new check fails on a *new* two-party
  game pairing `economy_service.credit`+`.debit` outside `game_wager_workflow` even without
  `allow_overdraft` (the mint signature). Today only the two solo views match (allowlisted).
- **AI + BTD6 → closed with evidence** in
  `docs/planning/production-readiness/p1-3-contract-invariants-disposition-2026-06-15.md`: AI is
  substantially-covered by the 34/34 catalogue/eval ratchet; BTD6 source-provenance is
  invariant-covered, and uniform per-derived-value attribution is a documented design-for-review
  residual (a docstring/AST-marker guard would be brittle — fails the repo's "verifiable, not a
  temporary patch" bar).
- **De-staled:** hardening roadmap §P1-3 marked ✅ substantially-complete; `current-state.md` ▶ Next
  action re-pointed (next ▶ = welcome phase 2 PIL cards, then BUG-0009); ledger entry for #917 +
  archived the 4 oldest live entries to hold the soft ratchet at 20.
- **Verified:** `check_quality --full` green (9810); `check_architecture --mode strict` 0 errors;
  `check_docs --strict` ✓. Both new guards verified to fire on an injected violation.

## Handoff / next

- **Next ▶ startable:** the **safety quick-win — welcome phase 2 PIL cards** (decade-queue slot 7;
  the `render_welcome_card` prototype exists, small follow-up on the stable embed-first v1). Then
  **plan-first BUG-0009** (AI §7 deterministic list-builders, slot 6, clears an OPEN bug). The
  remaining P1 (absence-guard **Layer B** · live-quality eval **battery**) stays creds/review-blocked.
- **Pre-existing ledger drift to reconcile (NOT mine):** `check_current_state_ledger --strict`
  (advisory, not CI) flags **9** merged PRs from other sessions absent from the ledger — **#902,
  #904, #907, #908, #909, #913, #914, #915, #916** (the Hermes-context / routine-consolidation /
  docs band #901–#916). I did not enter them — accurate descriptions need per-PR investigation, the
  imminent **#930 reconciliation pass**'s job. `check_docs` (the CI gate) is green regardless.
- **Tooling note for the next P1-3-style pass:** the settings parity detector's one real limitation
  is **dynamic-name resolution** — a subsystem that calls `resolve_setting(g, sub, <loop var>)` gets
  its *whole* subsystem treated as consumed (fail-safe). That is correct (we can't statically prove
  which names a loop reads), but it means a dead setting added to a dynamic-read subsystem (today:
  only `ai`) would not be caught. Acceptable + documented; flagged so a later session doesn't mistake
  it for a bug.

## 💡 Session idea (Q-0089)

**A reverse-parity invariant: every `resolve_value`/`resolve_setting` literal `(subsystem, name)`
read must correspond to a *declared* setting.** This session built declared→consumer parity (no dead
declarations). The mirror gap is just as real: a typo'd or stale read — `resolve_value(g, "welcom",
"enabld", default)` — silently returns the fallback forever, an invisible always-default bug that no
test catches today (the misspelled key is simply never written, so it always resolves to the
default). The detector I built already collects every literal `(subsystem, name)` consumer pair; a
second assertion that each such pair exists in the schema registry would close the loop cheaply,
reusing the same AST walk. Dedup-checked `docs/ideas/` + the roadmap — not present. Worth having: it
turns the settings lane's parity from one-directional into a true bijection (declared ⇔ consumed),
the same shape as the AI catalogue's `declared == consumed` ratchet that the disposition praised.
*(Recorded here under the session-idea flag; small enough to fold into the same invariant file in a
follow-up, so no standalone idea doc.)*

## ⟲ Previous-session review (Q-0102)

**Previous run** (#912, mining Slices E + F — respec polish + skill/milestone titles): a clean,
well-executed close of the mining structures lane. What it did well: it explicitly built **away
from** the one open PR (#911, the owner's live mining-hub UX work on the same panels) to avoid a
collision — exactly the parallel-agent discipline the active-work ledger exists to enforce, and it
named the avoidance in its ledger entry. What it (and the whole #900-band) could have done better is
the *system* point below.

**System improvement this surfaces:** the `check_current_state_ledger --strict` drift this session
hit (9 unentered PRs, #902–#916) shows the **born-red ledger-entry discipline isn't holding for
docs/housekeeping PRs**. The Q-0133 gate requires a *session card*, and code sessions reliably add
their `Recently shipped` entry under it — but small docs/routine PRs (the Hermes arc, dispatch-prompt
trims) merge without one, so their ledger entries are silently skipped and pile up as between-pass
drift that only a reconcile clears. The cheap fix: extend `check_session_gate` (or a new advisory
step) so that a PR which merges to `main` *without* adding either a `.sessions/` card **or** a
`Recently shipped` ledger line is flagged at merge time — closing the exact gap that makes the
ledger drift in the first place, rather than relying on a reconcile pass to mop it up every 30 PRs.
Captured as a candidate for the next reconcile/owner-review (it touches an executable-config file,
so it's a proposal, not a self-applied change — CLAUDE.md Q-0106).

## Doc audit (Q-0104)

- `check_current_state_ledger --strict`: my PR #917 is entered; 9 pre-existing drift PRs flagged +
  handed off above (not mine to attribute). `check_docs --strict` ✓ (ratchet back to 20).
- New owner decisions: none (P1-3 was already-decided plan work — no router Q needed).
- New docs reachable: the P1-3 disposition is linked from the hardening roadmap §P1-3 + the
  current-state ▶ Next action + the #917 ledger entry (`check_docs` badge/link checks pass).
- Bug book: no new runtime bugs; BUG-0009 (AI claim-assembly) stays OPEN, now also referenced by the
  P1-3 disposition's BTD6 residual. No bug-book entry moved to FIXED this session.
