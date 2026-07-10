# 2026-07-10 — EAP journal: routine-observability bug entry (round-3 brief §1(d))

> **Status:** `complete` — PR #1936.

- **📊 Model:** claude-fable-5 · worker session (coordinator-dispatched, round-3 brief §1 task 3)

## What happened

Appended one entry to `docs/planning/projects-eap-evaluation-log.md` (2026-07-10
~11:01–11:04Z, owner-observed, lived incidents — screen recordings 13:01 + 13:04 CEST)
recording the two routine-observability bugs the round-3 launch pack §1(d) ordered logged:

1. **Completed routine runs not inspectable from the Routines screen** — "Open session" is
   ineffective; completed autonomous work is visible only as a timestamp, never as a
   transcript/summary.
2. **Session-side Runs panel says "No runs yet"** while the Routines screen shows 3 completed
   runs for the same self-armed kit-lab routine — two surfaces disagreeing about one
   routine's history.

Both observations were already *embedded* in the 11:01Z capability-unlock entry, so the new
entry is written as a split-out bug record that cross-references rather than restates it
(guidebook §4 integrity rule: deepen, never restate), and adds the synthesis the brief
implies — the two bugs together gut the audit trail for exactly the capability that just
unlocked (agent self-arming).

Diff kept minimal on purpose (brief-directed): journal entry + this card + claim add/delete
+ telemetry row. No ledger entry pre-merge (benign newest-merge lag; the next reconciliation
pass records #1936).

## Verification

- `python3.10 scripts/check_docs.py --strict` — exit 0.
- `python3.10 scripts/check_session_slug_unique.py` — OK.
- `python3.10 scripts/check_current_state_ledger.py --strict` — exit 0.
- Docs-only diff; no `disbot/` code touched.

## Context delta

- **Needed but not pointed to:** none material — the brief named both source docs and the
  journal's own "How to append" header carried the entry shape + integrity rules.
- **Pointed to but didn't need:** none.
- **Discovered by hand:** the local clone sat detached 85 commits behind origin/main at
  session start; the launch pack (the task's source doc) did not exist locally until
  `git fetch` + fast-forward. Same staleness class as the journal's own 2026-07-07 entry
  ("trusting local disk would have produced answers from a stale world").
- **Decisions made alone:** wrote the entry as a cross-referencing split-out of the 11:01Z
  entry rather than a standalone restatement — the guidebook §4 never-restate rule forced
  the shape; flagging for ratification since the brief's wording ("log the two bugs") could
  also be read as wanting fully self-contained entries.

## 🛠 Friction → guard

Stale-clone-at-start (85 commits behind, detached HEAD; the task's source doc missing
locally). An idea for exactly this class already exists —
`docs/ideas/session-start-staleness-banner-2026-07-07.md` — so no new guard shipped;
this session is a +1 datapoint on that idea's motivation (noted here rather than
duplicated as a new idea).

## 💡 Session idea

**Stable entry IDs for the EAP evaluation journal** (`E-0001`, `E-0002`, … prefixed on each
`§ Entries` bullet). Why it's worth having: entries now cite each other positionally ("the
11:01Z entry above" — this session added the second such cross-reference), and the Friday
feedback-reply template + the anthropic-email drafts quote entries by date/time, which
breaks if two observations share a timestamp (there are already two 11:01Z-adjacent entries
and three "2026-07-08 ·" quadruplets). A greppable ID makes cross-references durable and
lets the email drafts cite `E-00NN` unambiguously. Cheap: a one-pass renumber + a line in
"How to append" ("take the next free E-number"; append-only, so no collision risk).
Dedup-grepped `docs/ideas/` — no existing idea covers journal entry addressing.

## ⟲ Previous-session review (#1934, round-3 launch pack)

Did well: the launch pack is a genuinely executable owner artifact — this session ran §1(d)
straight from its wording with zero ambiguity, and the same PR shipped a friction→guard
(`check_plan_homing` mirrored into `check_quality.py`) instead of just noting the homing
miss. Improvement it surfaces: #1934 appended its close-out as a 12-line addendum to the
*previous* session's card (`2026-07-10-fleet-overnight-review.md`) rather than opening its
own — the second consecutive session review to flag multi-PR/continuation card ambiguity
(#1926's review flagged the same class). Per the Q-0102 loop, twice-flagged means it's
promotable: a one-line convention in `.sessions/README.md` ("continuation PRs either open a
fresh card or carry a pointer-only stub — enders live in exactly one card") is now
justified, not speculative.

## 📄 Documentation audit

- Checkers green (see Verification). No new owner decisions (the entry executes a written
  owner-directed order) → nothing for the router.
- Durable homes: the two bugs now live in the evaluation journal (their canonical home —
  the launch pack §1(d) itself pointed there); the capability-unlock context stays in the
  11:01Z entry. Nothing captured only in chat.

## 📤 Run report

- **Did:** appended the §1(d) routine-observability bug entry to the EAP evaluation journal
  · **Outcome:** shipped
- **Shipped:** PR #1936 — `docs/planning/projects-eap-evaluation-log.md` (one entry)
- **Run type:** `manual` (coordinator-dispatched worker task, round-3 brief §1 task 3)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (task-scoped; the entry-ID idea is flagged above for a future
  grooming pass, not built)
- **↪ Next:** round-3 brief §1 orders (a)–(c) remain with fleet-manager (capabilities.md
  correction, arming-recipe capture, remaining-lane arming); the journal's Friday
  feedback-reply fill can now cite both §1(d) bugs from one entry

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1936, via auto-merge on green) |
| CI-red rounds | 0 (born-red hold only; no check failures) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (journal entry IDs) |
| Ideas groomed | 0 (small dispatched task; staleness-banner idea got a +1 datapoint) |
