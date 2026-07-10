# Session — round-3 dispatch, part 4c: capability self-awareness + boot verifications

> **Status:** `complete`
> **Run type:** owner-directed · same live dispatch chat (parts 4/4b: PRs #1957/#1963, merged)
> **Model/time:** fable-5 · 2026-07-10 ~21:1xZ → ~21:2xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1963) · PR #1964.

## What is about to happen

Owner raised (live): Projects aren't self-aware of their own capabilities — "if you
could just ask a project what its abilities are, and it could answer honestly, that
would be really nice" — route it to Anthropic via the EAP wrap-up email (due 07-14).
Also: verify sim-lab + trading boots at ground truth (registry + git) and tick runbook
§5; fold the now-twice-proven worker-seat arming fallback into the gen-3 standard §2.

## What happened

- **Boot verifications (registry + git, ~21:1xZ):**
  - **sim-lab LIVE — pipeline proof EXCEEDED**: boot PRs #2–#5 (ORDER 000 walking
    skeleton; `sims/REFERENCE.md`; **INTAKE 001–003 pulled from the idea-engine
    outbox** — three proposals, not just PROPOSAL 001), heartbeat 21:00Z green.
    **OA-003 self-resolved**: coordinator toolset lacked BOTH `create_trigger` and
    `send_later` (verbatim wall in its status) → a spawned worker had both → failsafe
    `trig_01SHfnLv6EqZesr4tC3T9kUU` armed, **first fire 21:03Z**; pacemaker test
    one-shot in flight. Remaining click: **OA-002 Codex toggle**.
  - **Trading BOOTED, loop hot**: `trading-strategy failsafe wake`
    (`trig_01YBaVeKA…`, created 21:03Z, bound to its coordinator + the owner's new
    env) + live continuation chain (next link 21:20Z). ORDER 008 execution + old
    4-hourly wake deletion = next sweep's checks. Runbook §3.6 ☑ + §5 rows updated
    (sim-lab row rewritten LIVE, trading row added).
- **Owner's capability-self-awareness ask routed durably:**
  - **EAP wrap-up email** (`docs/eap/gen1-wrapup-email-final-candidate.md`): new §(d)
    item 2 (owner's words verbatim; items renumbered 1–9) + §(g) evidence bullet (the
    one-session sim-lab datapoint: coordinator vs worker, different capability worlds).
  - **Idea file** `docs/ideas/project-capability-self-awareness-2026-07-10.md` +
    README index: the buildable half — a kit `capabilities --probe` battery that
    regenerates `docs/CAPABILITIES.md` from live probe results.
- **Friction → guard (Q-0194):** the worker-seat retry is now DOCTRINE, not folklore —
  gen-3 standard §2 pacemaker bullet rewritten: scheduling tool absent → FIRST retry
  from a spawned worker (twice-proven: idea-engine, sim-lab) → only then owner-manual.

## ⚑ Self-initiated

- The §(d) renumbering of a SEND-READY email (insertion at item 2 was a judgment call
  on priority — the owner raised it unprompted, so it outranks the pre-existing asks
  below it; flagged for the owner's Part-1 pass before sending).
- The gen-3 §2 worker-seat-fallback rewrite (contained, twice-evidenced).
- Runbook §5 trading "BOOTED, loop hot" verdict from registry evidence alone
  (calibration paste-back not chat-verifiable from this seat — flagged in the row).

## 💡 Session idea

The `capabilities --probe` battery (in the idea file above) — distinct from the
seat-boot-verification harness (part 4's idea, which verifies a seat from OUTSIDE via
registry/raw): the probe answers from INSIDE what a session can actually do, and its
committed output is simultaneously the honest self-answer the owner asked for and EAP
evidence. The two compose: `check_seat.py` reads what `capabilities --probe` writes.

## ⟲ Previous-session review

Part 4b shipped a clean package but its §2 step-4 arming fallback said "IF THE CALL IS
WALLED: record + owner-manual" — the idea-engine worker-seat recipe was ALREADY in
runbook §5 at drafting time, and 4b didn't carry it into the package; sim-lab then paid
the exact cost one hour later (owner intervention + OA-003). **Improvement (applied):**
the fallback ladder is now in the gen-3 standard §2, so future packages inherit it from
the template instead of depending on the drafter remembering a §5 table cell. The
deeper lesson feeds this session's own idea: recipes proven once belong in doctrine
files, not verification-log cells.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ (4b's journal rule applied —
no new plan doc this session, ran it anyway) · `check_current_state_ledger --strict` ✓
(benign lag only) · chat-only material swept: owner's ask → email §(d)/§(g) + idea file
(words preserved verbatim in both); registry findings → runbook §3.6/§5; worker-seat
recipe → gen-3 §2. Claim file deleted this commit.

## Handoff

Owner clicks now: **OA-002 sim-lab Codex toggle** (the ONLY thing between sim-lab and
finalized verdicts); the §2.5 batch + orphan watchdog go (chain still alive); **EAP
email send before 07-14** — §(d)/§(g) now carry the self-awareness item, owner writes
Part 1. Next sweep verifies: trading ORDER 008 report (13 verdicts + denominators),
old trading 4-hourly wake deleted, sim-lab INTAKE 003 verdict + first @codex reply
(proves the toggle), games-mapping proposal from the manager (relay paste pending).
