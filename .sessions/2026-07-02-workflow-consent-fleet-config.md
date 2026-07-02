# 2026-07-02 — Stop fleet sessions re-prompting for multi-agent-workflow consent

> **Status:** `complete`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** #1669
> **Session type:** owner-directed config fix — "why does each session keep asking permission to start a
> workflow, and can we add it to always-allowed?"

## What I'm about to do (born-red placeholder)

Commit the multi-agent-workflow **usage-consent** flag into the one repo scope the runtime actually honors,
so ephemeral remote fleet sessions stop re-prompting on every boot. Diagnosis traced to the running binary;
mechanism + decision written below. Docs/config-only — no `disbot/`, no runtime code.

## The question (owner, 2026-07-02)

> "Why does each [fleet] session keep asking me for permission to start a workflow? Is that a recently added
> requirement by Anthropic? Previously an ultracode session could start without explicit permission — can we
> add these things to the always-allowed list?"

## The finding (verified against the running binary, not memory — Q-0120)

The prompt is **not a tool permission**. It is the **multi-agent-workflow usage-consent gate** — a one-time
"this can spawn many agents / consume many tokens, OK?" acknowledgement shown before the first `Workflow`
(ultracode) run. In `/opt/claude-code/bin/claude` (the actual running CLI, a 248 MB compiled binary — the
`/opt/node22` npm copy is a stale Mar-31 build that predates the feature): the keys are
`skipWorkflowUsageWarning` · `recordWorkflowUsageConsent` · `workflowNeedsUsageConsentPrompt`
(telemetry `tengu_workflow_usage_warning`).

**Why it returns every session.** On *accept*, the runtime persists `skipWorkflowUsageWarning: true` to
`~/.claude/settings.json` (**user** scope). Fleet sessions run in **ephemeral remote containers**: that file
is wiped when the container is reclaimed, and each fresh clone boots with no user settings → the gate
reappears. Confirmed: this container started with **no `~/.claude/settings.json`**.

**Recently added?** Yes — it ships with the newer multi-agent Workflow/ultracode feature. It's a *usage
acknowledgement, not a permission*, so: (a) it isn't in the allow-list and adding `Workflow`/`Task`/`Agent`
to `permissions.allow` would **not** silence it; (b) `permissions.defaultMode` is already `bypassPermissions`
here, so those tools are *already* permission-allowed — the consent gate is a separate mechanism.

**The catch that breaks the naive fix.** The consent reader is:
```js
function Vyn(){return!!(yn("userSettings")?.skipWorkflowUsageWarning
  || yn("localSettings")?.skipWorkflowUsageWarning
  || yn("flagSettings")?.skipWorkflowUsageWarning
  || yn("policySettings")?.skipWorkflowUsageWarning)}
```
It honors the flag from **user / local / flag / policy** scopes — **never committed *project* settings**
(`.claude/settings.json`). So dropping it in the shared project settings would be *silently ignored*. The
only repo-committable scope it honors is **`localSettings` = `.claude/settings.local.json`** — which this
repo **gitignores** (`.gitignore:106`), so it never reaches a fresh clone.

## The fix

Make `.claude/settings.local.json` a **tracked, shared** file carrying just `skipWorkflowUsageWarning: true`,
and un-gitignore it with an explanatory comment. This is the single repo-durable change the consent reader
actually reads → every fresh fleet clone boots pre-consented, zero web-UI work, fully reversible.

Cleaner long-term alternative (offered to owner, not applied): set the flag once at the **environment**
level in the code.claude.com env config / setup script (→ `flagSettings`/`userSettings` at boot), which
keeps `settings.local.json` personal. Owner can adopt that and I revert the un-gitignore.

## Provenance

Owner-directed in-session 2026-07-02 → router **Q-0218** (the Q-0106 exception: executable config is
owner-gated, but a change the maintainer directs in-session is applied directly with its provenance Q).

## What shipped

- `.gitignore` — un-ignore `.claude/settings.local.json` with a tracked-on-purpose comment.
- `.claude/settings.local.json` — now a tracked, shared `{ "skipWorkflowUsageWarning": true }` (dropped the
  stale one-off kit-review scratch permissions).
- `docs/owner/maintainer-question-router.md` — **Q-0218** provenance block.
- Diagnosis delivered in chat + this log; env-level alternative offered for the owner to adopt later.

Verified: `settings.local.json` valid JSON ✓ · no longer gitignored ✓ · `check_docs --strict` ✓. No Python
touched. **Not applied:** any change to in-flight fleet PRs (owner constraint) — e.g. #1666 Lane G's
"CI failure" is just its born-red gate holding correctly, left untouched.

## ⚑ Self-initiated

None beyond the owner's direct request. The change is owner-directed (Q-0218); the *mechanism* (un-gitignore
`settings.local.json` as the only reader-honored repo scope) is the unnamed prerequisite the goal implied
(Q-0014 "approving a goal approves the path to it").

## 💡 Session idea

**A `scripts/check_fleet_settings.py` guard (enforce, don't exhort — Q-0194).** This session's whole friction
was *silent*: the consent gate re-prompts with no error, and the naive fix (project settings) would have
failed *silently* because the reader ignores project scope. The durable defense is a tiny checker that asserts
the fleet's harness-critical invariants still hold — `.claude/settings.local.json` is **tracked** (not
re-gitignored by a future "cleanup") and still contains `skipWorkflowUsageWarning: true` — wired into
`code-quality`. It converts "a future session quietly breaks the fleet's consent skip" from an invisible
regression into a red check. Dedup-checked: no existing checker covers `.claude/settings.local.json`
(the `check_*` family covers docs/arch/ledger/session-gate/claims, not harness settings).

## ⟲ Previous-session review

Previous session (`2026-07-02-grammar-audit-prep.md`, the fleet substrate #1661/#1662) did the hard part
well: ground-truth extraction before judgment, one shared schema so N lane outputs compose, and a genuinely
useful Lane-G foundations addition. **What it could have anticipated:** it designed the *repo-doc* launch
preconditions (substrate present, docs-only boundary) but not the *harness/environment* preconditions each
fleet session actually hits — the workflow-consent re-prompt is exactly that class, and it's now costing the
owner a manual click per session. **System improvement:** the `BRIEF.md` "Launch preconditions" section (and
`HANDOFF-PROMPTS.md`) should carry a one-line **container preflight** — verify branch freshness *and* that
the workflow-consent flag is present — so operational friction is caught at launch, not discovered live.
(This session's `settings.local.json` fix removes the consent half of that friction for good.)

## 📊 Telemetry

- PR #1669 · config/docs-only · 3 files (`.gitignore`, `.claude/settings.local.json`, router Q-0218) + this log.
- Root cause traced to the running binary (`/opt/claude-code/bin/claude`), not to memory or the stale
  `/opt/node22` npm copy — the consent-reader scope list (`user/local/flag/policy`, not `project`) is the
  load-bearing fact.
- No runtime code; born-red gate held the PR until this flip.

## Doc audit (Q-0104)

`check_docs --strict` green (router + session card reachable, badges valid) · owner decision recorded in the
router (Q-0218) · `check_current_state_ledger --strict` re-run at close (see commit) · claim released.
