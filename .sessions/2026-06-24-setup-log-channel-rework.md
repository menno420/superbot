# Session — 2026-06-24 · "Choose a log channel" rework (two-channel + multi-select)

> **Status:** `in-progress` — born-red hold. Reworks the just-merged (#1429) moderation-only step;
> additive to `EssentialFlow` (no new cog/command/artifact).

**Trigger:** owner clarification (chat, 2026-06-24): the earlier "moderation only" answer (Q-0202) was
meant as the *first slice*, not a permanent cap. Owner wants owners to **choose a few important logging
types via a quick multi-select**, and chose a **two-channel** layout (moderation + activity) — "should
not become too much work for server owners, but they should have the option."

## What I'm about to do

Rework `LogChannelStep` from one-channel/moderation-only into a **two-channel + multi-select** step:
- **Multi-select** of activity types: members joining/leaving (default on) · role changes (default on) ·
  message edits/deletions (⚠️ shows content, default off).
- **Two channel pickers**: moderation/main channel + activity channel. **Leave blank → auto-create**
  `#mod-log` / `#server-log` (so accepting defaults is one tap).
- On Save (direct lane): `logging.enabled = True`; bind `mod_channel` → mod channel (moderation
  baseline, always on); if any activity type chosen, set the category flags + bind `events_channel` →
  activity channel. Auto-create via `ChannelLifecycleService.create_channels`; bindings via
  `BindingMutationPipeline` (both lazy-imported per the setup-view invariant).
- Supersede Q-0202 (router + plan); rework tests.

<!-- close-out (what shipped / misses / enders / context delta) written as the final step -->
