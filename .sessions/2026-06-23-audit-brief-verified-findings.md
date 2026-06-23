# 2026-06-23 — Consolidation audit: record three code-verified findings into the brief

> **Status:** `complete` — routine dispatch run, second slice. De-risks the owner-directed
> consolidation/discoverability audit (#1366) by resolving three of its "verify before trusting" /
> open-question TODOs against source, so the audit session starts ahead. PR #1367, auto-merge armed on
> green; docs-only.

> **Run type:** `routine · dispatch`

## What I'm about to do

While scoping a slice of the just-staged consolidation audit
(`docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md`), I verified three of its open
questions against source. None is a buildable code fix (the audit's real targets need live Discord
repro / owner decisions), but the findings are durable and remove research the audit session would
otherwise repeat. Recording them in the brief is first-class orientation work.

1. **§3.1 / §6 / §8 — the help-reachability guard is located, and it is subsystem-level only.** The
   brief said "a grep did not locate a standalone `check_help_reachability.py`; verify before
   trusting." It lives as **`tests/unit/invariants/test_help_reachability.py`** (→
   `tools/sim/help_menu_grouping_sim.py::check_reachability`) + **`test_discoverability.py`**. Both
   check **subsystem**-level homing (no orphan, ≤3 clicks, no dropdown overflow / a discovery path per
   subsystem). **Per-command reachability (rubric item 2) is NOT machine-checked** — resolving the §8
   "#1297 scope" open question: subsystem-homing only.
2. **§3.2 — the General cog menu IS already buttonized + homed (static).** `GeneralMenuView` has a
   per-command button for each of the 8 commands (`fact_btn`/`joke_btn`/…); `general` is a Utility
   `primary_child` with a `build_help_menu_view` hook. So the owner's "unfindable" complaint is **not**
   a static buttonization gap — it genuinely needs the live repro the brief calls for (path/listing,
   not buttons).
3. **§3.4 — both settings-orphan signals are already empty.** `build_catalogue(None).findings` reports
   `settings_without_panel == ()` and `panels_without_settings == ()` — that sub-goal is already at
   zero in the static build (the audit need only re-confirm the bot-dependent help-hook signal live).

## What shipped

The brief (`consolidation-discoverability-audit-brief-2026-06-23.md`) updated with the three
code-verified findings: §3.1 (reachability guard located + subsystem-only; rubric item 2 unguarded),
§3.2 (general cog already buttonized → cause narrowed to (b)/(c), still needs live repro), §3.4 (both
settings-orphan signals already empty), and the §8 "#1297 scope" open question marked RESOLVED.
Docs-only; `check_docs --strict` green; session gate green.

## Findings / decisions

- **The consolidation audit has no clean offline code slice to land unattended.** Its real targets need
  live Discord repro (general-cog path, setup-wizard walk), owner decisions (AI generative step, casino
  headwind), or substantial careful multi-cog work (per-command reachability guard, AI-panel/roles
  edit-in-place families). The honest, valuable contribution from an unattended run is to *verify and
  record* what's checkable offline so the (live-capable / owner-attended) audit session starts ahead —
  not to force a risky build into a just-staged owner-directed plan.
- **Rubric item 2 (per-command findability) is genuinely unguarded** and is the audit's highest-leverage
  *new* CI guard — but it's a real slice (command→menu-surface mapping), flagged as such, not a drive-by.

## 💡 Session idea

(One idea per run, Q-0089 — the same idea applies across both of this run's PRs, so it's recorded once
on the slice-1 log: a **rod-knob completeness invariant** that fails when a `Rod` dataclass field has no
consumer in the rod-shop summary / cast view / minigame. See
`.sessions/2026-06-23-fishing-premature-grace.md`.)

## ⟲ Previous-session review (Q-0102)

Covered on the slice-1 log (`.sessions/2026-06-23-fishing-premature-grace.md`) — the "designed-but-
never-wired" class (the `premature_grace` knob) and the de-staling fix. This second slice reinforces the
same theme from the other direction: the audit brief itself carried **unverified TODOs** ("a grep did
not locate…", "verify before trusting") — good honesty by #1366's author to flag them rather than assert
— and the right follow-up was simply to *do the verification* and fold the answers back in, so the
uncertainty didn't propagate to a third session.

## 📤 Run report

- **Did:** Verified + recorded 3 consolidation-audit findings into the brief (reachability guard scope ·
  general-cog already buttonized · settings orphans already zero) · **Outcome:** shipped (PR #1367,
  docs-only, auto-merge armed on green)
- **Shipped:** #1367 — consolidation-audit brief: 3 code-verified findings
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none new. (Carried by the brief: AI-advisor generative step needs a
  Q-0048 per-exposure decision; casino/gambling headwind is a product-coherence call — both pre-existing
  in #1366's §8, not raised by this run.)
- **⚑ Owner manual steps:** none — docs-only.
- **⚑ Self-initiated:** yes — no work order; this run also self-initiated PR #1365 (the `premature_grace`
  knob) and this brief-verification follow-up (Q-0172). Both reversible.
- **↪ Next:** the consolidation/discoverability audit is the live top priority (S1 ▶). Highest-leverage
  next slices, in order: (1) **per-command reachability CI guard** — the now-confirmed unguarded rubric
  item 2 (offline-buildable, a real slice); (2) **AI-panel `edit_in_place` family** (18 findings, has a
  plan); (3) **roles `edit_in_place` family** (15 findings). Live-repro / owner-gated: general-cog path
  confirm, setup-wizard walk, AI generative advisor.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` green; session gate green. Docs-only change to one planning doc + its session card;
no ledger/owner-decision drift introduced. The two PRs this run (#1365, #1367) will be recorded by the
next reconciliation pass (#1380; benign newest-merge lag, Q-0124).
