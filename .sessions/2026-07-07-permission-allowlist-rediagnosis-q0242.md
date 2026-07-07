# 2026-07-07 — Permission-allowlist re-diagnosis (Q-0242): Q-0229's fix was unverified, and mostly unnecessary

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Config + docs only:
> `.claude/settings.json` and `docs/owner/maintainer-question-router.md`. No `disbot/` changes.

## What this session did

Continuing the rebuild-plan-review conversation: the owner reported the same recurring permission
prompt Q-0229 (2026-07-03) was supposed to have already fixed — `send_later` and `delete_trigger`
(Claude Code Remote's scheduling tools) still prompting on the mobile/web client, with live
screenshots from earlier in this same session as evidence.

Investigated rather than re-applying the same fix a third time: Q-0229 added bare `mcp__<server>`
allow entries, reasoning "matches every tool on that server" — a claim that was never live-verified.
This session's evidence refutes it: `delete_trigger` (no exact-name entry, only the bare wildcard)
prompted as expected, but `send_later` (which had **both** the bare wildcard **and** an exact
`mcp__Claude_Code_Remote__send_later` entry already committed in `.claude/settings.local.json`)
**also** prompted — which the bare-wildcard theory alone can't explain.

**Fix applied (owner-directed in-session; Q-0106 executable-config exception):** added explicit,
individually-named allow entries for all ten Claude Code Remote tools to `.claude/settings.json`
(the shared, committed project file, not the already-tried `settings.local.json` path) — additive
only, the existing bare wildcard entries were left in place. Recorded as **Q-0242** in the router,
including the honest caveat that this may still not fully resolve it if the action-scheduling tool
class (`create_trigger`/`update_trigger`/`delete_trigger`/`fire_trigger`/`send_later`) is
deliberately exempted from allowlist auto-approval on the interactive surface as a safety design —
in which case the fix is confirming a platform behavior, not a bug.

**The more useful finding turned out to be behavioral, not configuration-level.** Reviewing this
session's own usage: `send_later` was called three times (as a "check back on this PR" habit after
opening PRs #1784–#1786), and in **all three cases** the `subscribe_pr_activity` webhook delivered
the "PR has been merged" notification on its own, before the scheduled check-in ever fired — the
pending trigger was deleted as redundant each time. The tool never did anything load-bearing this
session. Recommended to the owner, and adopted going forward in this conversation: stop defaulting
to `send_later` after every PR open; rely on the webhook subscription (proven reliable this session)
and reserve `send_later`/Routines for cases that genuinely need them (a stalled PR with no activity,
or recurring work with no GitHub-event equivalent) rather than as a default habit.

## Shipped (this PR)

- **`.claude/settings.json`** — ten explicit `mcp__Claude_Code_Remote__*` allow entries added.
- **`docs/owner/maintainer-question-router.md`** — **Q-0242** records the re-diagnosis, supersedes
  Q-0229's unverified claim, and leaves an explicit instruction for the next session that hits this:
  verify before re-attempting the same fix a third time.
- **This session log.**
- No `disbot/` changes.

## 🛠 Friction → guard (Q-0194)

The friction was genuinely recurring (the owner: "tried to fix more times than I can count"), and
the guard applied is the router entry itself — Q-0242 explicitly tells the next session not to
re-apply the same unverified "bare wildcard" fix, and to check the live evidence before declaring
victory. The stronger guard, per the section above, is behavioral rather than config: reducing
actual usage of the friction-causing tool class is cheaper and more reliable than continuing to
chase allowlist syntax for it.

## ⟲ Previous-session review (Q-0102)

Previous card in this chain (`2026-07-07-rebuild-plan-review-and-automation-idea.md`, merged as
#1784/#1785/#1786) did solid research-backed idea capture, but it — and this session, until the
owner pushed back — both defaulted to scheduling a `send_later` check-in after every PR open without
questioning whether it was necessary. **Concrete improvement:** the default should be "does this PR
have an active subscription that will deliver the outcome anyway?" before reaching for a scheduled
check-in, not "schedule one for safety." This session corrects that going forward in the same
conversation; worth carrying into future sessions' habits generally, not just this one.

## 💡 Session idea (Q-0089)

Already delivered earlier in this conversation (the user-self-service-automation-scheduler,
channel-role-scoped-authority-gap, moderation-feature-gaps, and guild-config-backup-and-data-export
captures, all merged in #1786) — no new filler idea minted for this small config-fix follow-up.

## 📋 Docs audit (Q-0104)

`check_docs.py --strict` green. New owner decision (Q-0242) recorded in the router with full
provenance. `.claude/settings.json` validated as syntactically valid JSON.

## 📤 Run report

- **Did:** re-diagnosed a recurring permission-prompt problem instead of re-applying an unverified
  prior fix; added a concrete, narrower config fix; identified and adopted a behavioral change that
  addresses the root friction more reliably than the config fix alone. **Outcome:** shipped.
- **Shipped:** this PR — `.claude/settings.json` (10 new allow entries) + router Q-0242 + this log.
- **Run type:** `manual` (owner-directed, live conversation).
- **⚑ Owner decisions needed:** none blocking. If Claude Code Remote's scheduling tools still prompt
  after this fix, the router entry already tells the next session what to do (stop, don't re-fix the
  same way, check the environment-level permission lever Q-0229 pointed at).
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** the behavioral recommendation (stop defaulting to `send_later`) went beyond
  the owner's literal ask (a settings fix) — flagged here since it changes actual agent behavior
  going forward, not just a config file.
- **↪ Next:** none forced. If this exact prompt recurs after this fix, do not repeat the allowlist
  approach a third time — treat it as confirmed platform behavior per this log's caveat.
