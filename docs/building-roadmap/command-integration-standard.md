# Command Integration Standard

> **Status:** `reference` — required panel/Help/settings wiring standard.

Runtime impact: None  
Scope: Future commands, panels, views, and cog menu integrations

This document defines how new commands should be integrated so they remain discoverable, panel-driven, testable, and compatible with SuperBot's platform architecture.

## Goals

Every new user-facing command should be:

- discoverable from `!help`;
- owned by the correct subsystem or cog;
- reachable from a cog command panel where appropriate;
- documented with a clear short description;
- routed through the correct service layer;
- safe to test manually;
- compatible with Settings Manager and future setup wizard flows.

## Mandatory command integration rules

### 1. Every user-facing cog should have a command panel

Every existing and future cog should have a clear command panel unless it is intentionally internal.

A cog command panel should:

- summarize what the cog does;
- list primary actions;
- use buttons and selects where practical;
- link to related settings where available;
- link back to Help or the previous parent panel;
- avoid dead-end views.

Expected panel families include Admin, Help, Platform, Settings, Cleanup, Logging, XP, Role, Economy, Mining, Blackjack, RPS, Counting, Chain, Proof Channel, and Leaderboard.

### 2. Help-menu discoverability is required

Every new user-facing command must be discoverable through `!help`.

Acceptable discovery paths:

- direct listing in Help;
- button from Help into the cog panel;
- subsystem dropdown or category section;
- admin-only section for admin commands;
- disabled/unavailable indicator if feature-gated.

A command should not exist as a hidden standalone command unless it is intentionally internal.

**Ship the button with the command (soft rule).** For a *member/operator-facing feature*, include the
discoverable entry point — a button on the relevant panel/hub, or a hub tile — in the **same PR** as the
command, not as a command-first v1 that predictably needs a follow-up. Owners navigate by UI, so a
working command alone reads as "half-done" to them even when it's fully tested. (Command-first is fine
for pure operator/CI tooling with no natural panel home.) Precedent: the XP-import feature shipped
command-only, and the immediate owner ask was "is this a button?" — one PR of churn a same-PR button
would have avoided.

### 3. Cog panels must support return navigation

Every command panel and subview should include a clear navigation path.

At minimum:

- back to parent panel;
- back to cog panel;
- back to Help where appropriate.

No feature view should trap the user in a dead-end state.

Example target flow:

```text
!minemenu
  -> Mine
      -> MiningView
          -> Mine again
          -> Back to Mining Menu
          -> Back to Help
```

The mining action view should be improved so it can return to the mining menu and Help.

### 4. Commands should be thin entrypoints

Commands should usually only:

1. validate basic context;
2. call shared service/runtime helpers;
3. send a panel, view, or result embed.

Commands should not directly own business logic that belongs in services, runtime modules, settings pipelines, binding pipelines, resource provisioning pipelines, or governance helpers.

### 5. Settings changes must use the settings pipeline

Future commands or buttons that change scalar settings must use `SettingsMutationPipeline`.

They must not write directly to legacy setting storage.

### 6. Binding changes must use the binding pipeline

Commands or buttons that change channel, role, or resource pointers must use `BindingMutationPipeline`.

They must not store Discord resource IDs as scalar settings.

### 7. Resource creation must use provisioning

Commands or buttons that create channels, roles, or categories must use `ResourceProvisioningPipeline`.

They must not call Discord create APIs directly except through approved legacy paths being migrated.

Resource creation must be previewed, explicitly confirmed, audited, and safely failed if permissions are missing.

### 8. Access control must reuse governance

Commands that control which cogs or features work in channels/categories must reuse governance scope-chain logic.

Do not create a second command allowlist system.

### 9. Slash command policy

Slash commands should eventually be limited mostly to front doors:

- `/help`
- `/settings`
- `/adminmenu`
- `/platform`
- `/minemenu`

Most feature work should remain button/menu-driven after the front door opens.

## Required metadata for new commands

Every new command should define or document:

- subsystem owner;
- short description;
- admin/user visibility;
- whether it opens a panel;
- related settings page, if any;
- required capability or permission;
- whether it mutates state;
- whether it creates resources;
- whether it is safe in DMs;
- whether it should appear in Help;
- whether it should appear in Admin/Platform menus.

## Panel requirements

A command panel should include:

- title and short description;
- primary actions;
- settings shortcut when relevant;
- help shortcut or back button;
- disabled-state messaging for unavailable features;
- clear error handling;
- no silent state changes.

## Game panel requirements

Game cogs should be replayable and mode-driven.

A game panel should generally include:

- choose mode;
- start game;
- replay same mode;
- change mode;
- view rules;
- back to game panel;
- back to Help.

Game flows should not require the user to retype commands after each round.

## Testing requirements

New commands and panels should include tests or manual smoke notes for:

- command exists;
- command appears in command surface ledger where applicable;
- command is discoverable through Help;
- panel opens without error;
- buttons route correctly;
- back buttons work;
- admin-only commands reject unauthorized users;
- state mutations go through the correct pipeline;
- no direct resource creation outside provisioning;
- no dead-end views.

## Manual smoke checklist

For a new command or panel, verify:

```text
!help
  -> subsystem appears
  -> opens cog panel
  -> cog panel opens feature
  -> feature can return to cog panel
  -> cog panel can return to Help
```

For admin/settings commands, verify `!adminmenu`, `!settings`, `!platform`, and `!help` route consistently where relevant.
