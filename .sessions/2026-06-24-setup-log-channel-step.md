# Session — 2026-06-24 · Essential Setup step "Choose a log channel"

> **Status:** `in-progress` — born-red hold. Additive direct-apply step on the existing
> `EssentialFlow`; no new cog/command/artifact → no registration fan-out.

**Trigger:** owner-directed (chat, 2026-06-24): *"Continue the Essential Setup spine — add the
'Choose a log channel' step (binding write via BindingMutationPipeline — lazy-import it; + optional
auto-create via ChannelLifecycleService), per the PR-1 note in
docs/planning/setup-wizard-restructure-plan-2026-06-24.md."* This is the next ▶ follow-on the
steps-3-4 session left turn-key.

## What I'm about to do

Append a **"Choose a log channel"** `_StepView` to `EssentialFlow._steps`, inserted in plan order
(after *Block spam*, before *Set up a help desk* — plan §5 step 4). One screen: pick an existing
channel **or** toggle "make a #server-log for me", then Save. On Save it applies immediately
(direct lane): turns on `logging.enabled` via the audited `SettingsMutationPipeline` and points all
server-logging at the chosen channel by writing `logging.mod_channel` through
`BindingMutationPipeline` (lazy-imported — it's on the setup-view no-top-level-import list). The
auto-create path runs `ChannelLifecycleService.create_channels(["server-log"])` first, then binds the
new channel. Plain-language copy (jargon guard stays 154 — new copy adds 0). + tests.

<!-- close-out (what shipped / misses / enders / context delta) written as the final step -->
