# 2026-07-02 — Stop fleet sessions re-prompting for multi-agent-workflow consent

> **Status:** `in-progress`
> **Branch:** `claude/review-recent-session-qcyc44` · **PR:** #(opening)
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

<!-- close-out enders (Q-0089 / Q-0102 / Q-0104) added at session end, then Status flipped to complete -->
