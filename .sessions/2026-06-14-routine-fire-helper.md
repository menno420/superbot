# Session: routine_fire.py — robust Claude Code dispatch helper

> **Status:** `complete`

**Branch:** `claude/hermes-routine-fire` · **PR:** #864 (DRAFT — held for comparison) · **Date:** 2026-06-14 · **Type:** ops/dispatch bugfix (manual)

## What this session did
Live-testing Hermes' new operating prompt, Hermes diagnosed a **real bug** — the dispatch skill's
inline `curl -d "$(python3 -c … "$WORK_ORDER")"` is shell-quoting-fragile for multi-line work orders
— and started fixing it by writing `routine_fire.py` itself. The owner then **decided Hermes may
write its own code** (Q-0141), turning this into a "nice test": both Hermes and I build the helper.

### Shipped (my reference version)
- **`scripts/hermes/routine_fire.py`** — stdlib-only. Work order on **stdin** (zero shell quoting),
  loads `CLAUDE_ROUTINE_*` from env or `~/.hermes/routine.env`, POSTs `{"text": …}`, prints
  `Fired. Watch: <session_url>`, **never prints the token**, `--dry-run` to preview the request
  (token redacted). 7 unit tests; dry-run smoke proved a multi-line/quoted/`$var` order passes clean.
- **`dispatch.md` STEP 4** now fires via the helper (+ regenerated SKILL.md).
- **Q-0141** — Hermes' write scope expands from docs-only (Q-0140) to **code, via PRs (CI-gated)**;
  prefer dispatch for big/risky changes, write small self-tooling directly; never push to main /
  mutate prod outside gates. Operating prompt (WHO YOU ARE / WHAT YOU MAY WRITE / SAFETY) + skill-pack
  README updated to match.

### Opened as a DRAFT on purpose
The owner is running a comparison — Hermes is authoring its own `routine_fire.py` in parallel. This PR
is held (draft → won't auto-merge) so the owner can compare both and merge the better one (or a blend).

### Verified
`pytest test_routine_fire` 7 ✓ · `build_skills --check` 11 ✓ · `check_docs --strict` ✓ · `check_quality --check-only` ✓.

## 💡 Session idea (Q-0089)
**`routine_fire.py --log`**: append each fire (work-order summary + returned `session_url` + timestamp)
to `~/.hermes/cron-output/dispatches.jsonl` — a lightweight audit trail of what Hermes dispatched and
where it went. Directly feeds the `routine-activity-visibility` gap (no at-a-glance "what did Hermes
fire?" today). Small, opt-in flag. Dedup-checked: no existing dispatch-log idea.

## ⟲ Previous-session review (Q-0102)
Reviewing **#863 (skill-author + Q-0140):** clean build of the self-extension layer. **What it
missed:** it set Hermes' boundary as a *hard* "code → always dispatch, never edit" — which the owner
**reversed within the hour** (Q-0141) once he weighed Hermes' capability (StepFun Step 3.7 Flash,
~74.4% SWE-bench). **System improvement:** when defining an agent's capability boundary before trust
is calibrated, pair it with an explicit **"revisit when calibrated"** switch (like review-merge's
ADVISORY→TRUSTED) rather than a hard rule — so widening it is a one-line flip, not a multi-doc rewrite
(this session). Set boundaries conservative-but-revisable, not carved.

## Doc audit (Q-0104)
`check_docs --strict` ✓ · `build_skills --check` ✓ · Q-0141 recorded with provenance ·
operating-prompt / README / dispatch.md mutually consistent on the new write scope · quality green.
**Grooming (Q-0015):** unblocked the dispatch seam of the autonomous loop — `routine_fire.py` makes
`/fire` robust, which is what the dispatch-bridge / autonomous-loop-vision needed to actually fire
reliably.
