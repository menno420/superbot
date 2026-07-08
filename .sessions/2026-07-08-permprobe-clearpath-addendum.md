# 2026-07-08 — Permission-probe clear-path addendum (test #8, explicit operator intent)

> **Status:** `complete`
> **Governance:** docs-only session; Q-0241 never-wait applies

## What is about to happen

Record the clear-path (explicit operator intent) outcome of probe test #8 as an addendum to
`docs/planning/projects-eap-permission-probe-report-2026-07-08.md`, plus one evaluation-log
entry — filling the report's missing cell ("does explicit in-session operator intent clear
the destructive-git wall?").

## What shipped (PR #1839)

- **Probe-report addendum** (`docs/planning/projects-eap-permission-probe-report-2026-07-08.md`)
  — the dedicated clear-path follow-up: pre-grant denial (verbatim `[Git Destructive]` at the
  sub-agent spawn layer), the operator's in-session grant ("I give you explicit permission",
  generic phrasing answering a request that named operation+target), and the post-grant result:
  the classifier wall LIFTED but the delete failed one layer deeper on a git credential-layer
  HTTP 403. Conclusion: **two independent walls** — operator intent unlocks the policy layer
  only; no path exists from a cloud session to remote-ref deletion. `test/permprobe-0708`
  survives as the standing example.
- **Evaluation-log entry** (`docs/planning/projects-eap-evaluation-log.md`) — one
  reliability/completion observation: the documented "explicit user intent" escape hatch is
  policy-layer only · weight: friction · reproducible: yes.
- **Claim** (`docs/owner/claims/claude-permprobe-clearpath-0708.md`) created at start, deleted
  at close.

**Outcome:** shipped — the probe report's last open question is answered with first-hand,
verbatim evidence; the headline finding stands, sharpened.

## 💡 Session idea (Q-0089)

**Environment capability matrix as a kit-consumable doc.** The prior probe session proposed an
auto-mode capability table in `docs/AGENT_ORIENTATION.md`; this session found the walls are
*layered* (classifier vs. credential), which makes the case stronger and bigger than
orientation: a standing `docs/reference/environment-capability-matrix.md` — rows = operations
(push new ref, delete remote ref, force-push, external POST, …), columns = **layer that gates
it** (auto-mode classifier / git credential / proxy) and **what clears it** (nothing / operator
grant / human with full rights) — authored so the substrate-kit templates can consume it, so
every future kit-derived repo inherits the known walls instead of re-probing them. Dedup: no
`capability matrix` hit in `docs/ideas/` or the roadmap; this extends (and credits) the
2026-07-08 probe session's orientation-table idea to the kit level.

## ⟲ Previous-session review (Q-0102)

The probe-report session (#1830) was thorough and reproducible in exactly the way that paid
off here: its report carried the exact command, branch name, and dispatch shape for test #8,
so this follow-up could re-run the *identical* attempt with zero reconstruction — that
reproducibility discipline is what makes a two-session experiment valid. What it could have
done better, surfaced by this session's own finding: its results table records *that* a test
was denied but not **which layer** the denial fired at — this session found spawn-layer
(classifier) and credential-layer (403) denials are different walls with different clear
conditions. Concrete workflow improvement: probe-style reports should carry a "layer" column
(classifier / credential / proxy / server-side) per row, so a denial is located, not just
recorded.

## Doc audit (Q-0104)

`python3.10 scripts/check_docs.py --strict` → **all checks passed ✓** (706 docs, ratchets
respected). Docs-only session: no runtime code, no new owner decisions to route; the
`current-state.md` ledger entry for #1839 lands at merge per the normal ledger cadence (benign
newest-merge lag). Nothing from this session lives only in chat — the addendum, eval-log
entry, and this card are the durable homes.

## 📤 Run report

- **Did:** ran the two-attempt clear-path experiment for probe test #8 and recorded it as a
  report addendum + eval-log entry · **Outcome:** shipped
- **Shipped:** #1839 — addendum + eval-log entry + card + claim deletion
- **Run type:** `manual` (owner-directed EAP evaluation follow-up)
- **⚑ Owner decisions needed:** none
- **⚑ Owner action:** unchanged from #1830 — `test/permprobe-0708` still requires a human with
  full git rights to delete (now proven: even an explicit in-session grant cannot reach it —
  credential-layer 403).
- **⚑ Self-initiated:** none beyond the assigned addendum — docs-only, reversible.
- **↪ Next:** fold the two-wall finding into the Friday 2026-07-10 activation-plan §4 feedback
  reply; optionally build the 💡 capability-matrix doc.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened | 1 (#1839, auto-merge armed at open) |
| Clear-path attempts | 2 (1 pre-grant DENIED, 1 post-grant classifier-cleared → 403) |
| Missing report cells filled | 1 (test #8 clear-path) |
| New ideas contributed | 1 (kit-consumable environment capability matrix) |
| Ideas groomed | 0 (bounded addendum task) |
