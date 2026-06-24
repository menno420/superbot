# 2026-06-24 — Essential Setup cutover (primary `!setup`, separate channel, on-join)

> **Status:** `complete`

## Arc

Owner-directed (in-session): the new Essential Setup wizard needed three changes before it
could be the real setup experience. All three shipped:

1. **Command swap.** Essential Setup is now the primary **`!setup` / `/setup`** (was
   `!quicksetup`, kept as a prefix alias alongside `essentialsetup`). The old section-list /
   draft → Final Review wizard moved to **`!setupadvanced` / `/setup-advanced`** (its
   `/setup-*` helper commands + on-join launcher are unchanged).
2. **Separate setup channel.** Essential Setup now posts into the private `#superbot-setup`
   channel and replies with a pointer, instead of rendering in the channel where the command
   was run. New opener `open_essential_setup_in_setup_channel()` reuses
   `services.setup_channel.ensure_setup_channel` and mirrors `open_setup_workspace`'s
   `(channel, message, reason)` contract. Graceful fallback: if the bot lacks Manage Channels,
   the flow opens inline (with a one-line hint) so setup still works.
3. **On server join.** The on-join launcher's **Start Setup** button now opens Essential Setup
   (was the advanced wizard), and its gate broadened from owner-only to the setup-admin ladder
   (owner / administrator / delegated) to match the `!setup` command's accessibility. Launcher
   embed copy reworded to describe the quick flow + `/setup-advanced`.

## Shipped (files)

- `disbot/views/setup/essential_setup.py` — new `open_essential_setup_in_setup_channel()`; both
  entry points post to `#superbot-setup` + pointer reply, fall back inline.
- `disbot/cogs/quicksetup_cog.py` — `quicksetup` → `setup` (prefix aliases `quicksetup`/
  `essentialsetup`; slash `setup`). File/class names kept (`QuickSetupCog`) to avoid
  extension-list churn; docstring made explicit.
- `disbot/cogs/setup_cog.py` — `setup` → `setupadvanced` (`/setup-advanced`); two advanced
  subcommand replies repointed to `/setup-advanced`.
- `disbot/views/setup/launcher.py` — `_start` opens Essential Setup; gate → `is_setup_admin`;
  embed copy reworded.
- Config/guards: `command_reachability_exceptions.yml` (setup→setupadvanced), `extension_roles.yaml`
  notes, `EXPECTED_SLASH_SURFACE` pin, `test_command_reachability.py` assertions; regenerated
  `extension-taxonomy-crosswalk.md` + dashboard `site.json` / `dashboard.json` / `data.js`.
- Tests: `test_essential_setup.py` (+5 channel/fallback tests), `test_setup_cog.py` (method
  renames + 3 rewritten `_start` tests). Docs: plan tracker + current-state (S1) + two command maps.

## Verification

- `check_quality.py --full` green (12489 passed after the artifact regen); `check_architecture.py
  --mode strict` 0 errors; `check_docs.py --strict` ✓; `setup_wizard_sim` VERDICT **PASS**;
  jargon ratchet at 154 (essential_setup.py stays jargon-clean — not a baseline file).
- Live boot not run (deterministic UI rename + channel-post path; the command-surface ledger test
  confirms `/setup` + `/setup-advanced` register and `/quicksetup` is gone).

## Decisions made alone

- **Broadened the launcher Start-Setup gate** owner-only → setup-admin (owner/admin/delegated) for
  parity with the admin-gated `!setup` command. Reversible; flagged here for ratification.
- **Kept the `quicksetup_cog.py` file + `QuickSetupCog` class names** (only the command changed) to
  avoid `config.INITIAL_EXTENSIONS` / cog-registration churn. The plan's PR 3 can rename if wanted.
- **Graceful inline fallback** (vs. the advanced wizard's hard "grant Manage Channels" block) — the
  Essential flow's whole point is "it just works", so it degrades to in-channel rather than refusing.

## Flagged for maintainer / known limits

- The on-join launcher is now a **mixed** surface: Start Setup → Essential (new), but its other
  buttons (Readiness / Smart Suggestions / Choose Preset / View Summary) still open the *advanced*
  draft system. That's the intended interim state — the plan's PR 2/PR 3 reorganize extras/advanced.
- Slash-command rename takes effect on the next slash sync (`!syncslash`), as with any rename.

## Context delta

- **Needed but not pointed to:** the `extension_roles.yaml` → generated `extension-taxonomy-crosswalk.md`
  link and the dashboard `site.json`/`data.js` generated-artifact freshness tests — both keyed on the
  command surface, so a command rename silently fails `test_*_artifacts_fresh` until regenerated. The
  context map pointed me at importers but not at "renaming a command means regenerate two artifact sets."
- **Pointed to but didn't need:** the setup-platform folio's resource-provisioning docs — this change
  was command surface + channel plumbing, not the provisioning lane.
- **Discovered by hand:** the reachability checker auto-exempts `@commands.has_permissions(administrator=True)`
  (decorator scan), so the new `!setup` needs no allowlist entry, but the advanced wizard (gates inside
  the body) still does — the exemption follows the *gating style*, not the command.

## ⟲ Previous-session review

The prior `setup-copy-jargon-guard` / polish sessions built the spine well but left it behind a
`!quicksetup` name that no one would discover as "setup" — the natural finish was always the cutover to
`!setup`, which this session did. Improvement surfaced: the generated-artifact freshness tests (site.json
/ crosswalk) are an easy trip-wire on *any* command rename; a one-line note in the command-surface map
("rename a command → re-run export_dashboard_data.py + extension_crosswalk.py") would save the next agent
the full-suite round-trip. Captured below.

## 💡 Session idea

A tiny `scripts/`-level "command rename checklist" (or a `check_quality` hint): when the diff renames a
`@commands.command`/`@app_commands.command` name, print the regen commands (`export_dashboard_data.py`,
`extension_crosswalk.py`) + the pins to update (`EXPECTED_SLASH_SURFACE`, reachability YAML). The rename
surface is mechanical but spread across 5 non-obvious homes; a checklist makes it un-missable.

## 🛠 Friction → guard

The full CI mirror's only red was 4 generated-artifact freshness tests (dashboard `site.json`) — a
command rename invalidates them but nothing upstream warns you. Shipped guard: none enforcing this run
(regenerated + documented the regen in the command-surface map). Proposed (idea above): a rename-aware
hint in `check_quality` / the command-surface map so the next rename regenerates artifacts up-front
instead of discovering it via a 4-minute red suite.

## 📤 Run report

- **Did:** cut Essential Setup over to the primary `!setup`/`/setup`, gave it a separate `#superbot-setup`
  channel, and made it the on-join Start-Setup flow; renamed the old wizard to `!setupadvanced`. ·
  **Outcome:** shipped (pushed to branch)
- **Shipped:** no PR opened — pushed to `claude/determined-gates-nscc6z`; the remote env gates PR creation
  on an explicit ask. Offered to open one.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** ratify the launcher Start-Setup gate broadening (owner-only → admin) —
  minor, reversible.
- **⚑ Owner manual steps:** run `!syncslash` after deploy so `/setup` + `/setup-advanced` replace
  `/quicksetup` + the old `/setup` in Discord.
- **⚑ Self-initiated:** none (owner-directed task).
- **↪ Next:** setup step-0 server-type preset (needs a direct-apply preset path) · PR 2 extras menu +
  "Check my setup" · PR 3 retire dead/legacy sections + rework the Advanced editor.
