# Command Expansion Backlog

> **Status:** `plan` — command-expansion backlog; cross-check source.

Runtime impact: None  
Scope: Near-term command, panel, and gameplay improvements

This document lists command and panel ideas that should be considered during future implementation phases.

Items here are not approved implementation by themselves. They should be implemented only through the standard command integration rules in `command-integration-standard.md`.

## Priority themes

1. Every major cog should have a clear command panel.
2. Help should link to every major cog panel.
3. Cog panels should link back to Help.
4. Settings pages should link to related cog panels.
5. Game cogs should support mode selection and replay from the same menu.
6. Resource creation and settings changes must use platform pipelines.

## Missing or incomplete command panels

Future work should inspect all cogs and ensure each has a usable panel.

High-priority panels:

- Settings Manager panel
- Cleanup panel
- Logging panel
- Access Policy panel
- Role panel
- Economy panel
- Mining panel
- Blackjack panel
- RPS panel
- Counting panel
- Chain panel
- Proof Channel panel
- Leaderboard panel

If a cog currently lacks a panel, add one instead of adding isolated commands.

## Mining menu improvements

Current issue to address:

```text
!minemenu
  -> Mine button
      -> MiningView
          -> no clear path back to Help
```

Target flow:

```text
!minemenu
  -> Mine
      -> MiningView
          -> Mine again
          -> Back to Mining Menu
          -> Back to Help
          -> Open Settings, later if admin
```

Mining should eventually support:

- mine once;
- mine again;
- mining stats;
- mining cooldown display;
- rewards preview;
- inventory shortcut;
- economy shortcut;
- settings shortcut for admins;
- back to Help.

## Blackjack improvements

Blackjack should become a panel-driven game instead of only a one-off command flow.

Target entrypoint:

```text
!blackjack
```

or an existing cog panel route from Help.

Target panel actions:

- Start Classic Blackjack;
- Choose game mode;
- View rules;
- View balance/economy status, if economy integration exists;
- Replay same mode;
- Change mode;
- Back to Games panel;
- Back to Help.

Suggested game modes:

### Classic

Standard blackjack round.

### Quick Hand

Fast single-hand mode with minimal prompts.

### Best of 3

Short match format where the player and dealer play multiple hands.

### High Stakes

Higher minimum/maximum bet rules, if economy integration is enabled.

### Practice

No economy impact. Useful for testing and casual play.

Implementation notes:

- Economy-backed modes must validate balance and bet limits.
- Practice mode should not mutate economy state.
- Replay should preserve selected mode and default bet where safe.
- All game state should be isolated to the view/session.

## RPS improvements

RPS should support multiple replayable modes from one panel.

Target entrypoint:

```text
!rps
```

or Help -> Games -> RPS.

Target panel actions:

- Play vs bot;
- Challenge user;
- Choose mode;
- View rules;
- Replay same mode;
- Change mode;
- Back to Games panel;
- Back to Help.

Suggested game modes:

### Single Round

One rock-paper-scissors round.

### Best of 3

First to 2 wins.

### Best of 5

First to 3 wins.

### Timed Match

Players must choose within a time limit.

### Challenge Mode

Challenge another user directly.

### Tournament Mode

Bridge to the existing RPS tournament system where appropriate.

Implementation notes:

- Replay should not require retyping `!rps`.
- Challenge mode should handle declined or expired challenges cleanly.
- Tournament mode should reuse tournament services rather than duplicating tournament state.
- Buttons should disable after a round ends or timeout.

## General games panel

A future Games panel should route to:

- Blackjack;
- RPS;
- RPS Tournament;
- Deathmatch;
- other future games.

Suggested actions:

- Choose game;
- View active games;
- View tournaments;
- View game settings, admin-only;
- Back to Help.

## Cleanup command expansion

Cleanup should move from a narrow word-management panel to a full cleanup command panel.

Target panel:

```text
!cleanup
```

or:

```text
!settings cleanup
```

Target pages:

- Overview;
- Prohibited words;
- Scan history;
- Warning behavior;
- Exemptions;
- Channel policies;
- Test/preview cleanup rule;
- Cleanup logging status;
- Back to Settings;
- Back to Help.

Existing `!wordmenu` should become a subpage, not remain the only cleanup panel.

## Logging command expansion

Logging should have a dedicated panel.

Target panel:

```text
!logging
```

Target actions:

- Status;
- Test log;
- Choose existing mod log channel;
- Choose existing cleanup log channel;
- Create log channel later through ResourceProvisioningPipeline;
- Logging settings shortcut;
- Back to Settings;
- Back to Help.

## Access-policy command expansion

Access policy should have a dedicated admin panel.

Target panel:

```text
!settings access
```

Target actions:

- Select subsystem;
- Select channel/category;
- Enable here;
- Disable here;
- Inherit from parent;
- Preview effective policy;
- Explain why a command is blocked.

Access policy must reuse governance scope-chain logic.

## Role command expansion

Role system should expose a clear panel.

Target panel:

```text
!roles
```

or existing role command panel.

Target actions:

- Self-role menu;
- Reaction-role setup;
- Default role settings;
- Skip roles;
- XP/time role settings later;
- Role settings shortcut;
- Back to Help.

## Economy command expansion

Economy should expose a clear panel.

Target actions:

- Balance;
- Daily/work actions;
- Shop;
- Inventory;
- Transfer;
- Economy settings, admin-only;
- Economy logs, admin-only;
- Back to Help.

## Proof channel command expansion

Proof channel should expose a clear panel.

Target actions:

- Submit proof;
- View proof requirements;
- Staff review queue, admin/staff only;
- Proof settings, admin-only;
- Back to Help.

## Command quality checklist

Before adding a command to production, confirm:

- It belongs to a subsystem.
- It appears in Help or is intentionally internal.
- It has a panel if it is a major feature.
- It has a short, clear description.
- It uses service-layer logic.
- It does not directly mutate settings or bindings.
- It does not directly create resources.
- It has back navigation.
- It has manual smoke notes.
- It does not create duplicate abstractions.
