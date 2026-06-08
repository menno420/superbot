---
description: "View layer rules triggered before editing disbot/views files"
globs:
  - "disbot/views/**/*.py"
---

# Discord views — rules triggered before editing view files

## Read these first
- `docs/architecture.md` — layer boundary: views may not import cogs.
  The one rule with zero tolerance for new violations: `services → views` is blocked.
- `docs/runtime_contracts.md` § 6 — interaction lifecycle.
- `docs/helper-policy.md` — before adding any utility function to views/.

## Hard rules
- **Always** extend `BaseView`, `HubView`, or `PersistentView` for Discord UI views.
  Exception: game-state views (`views/rps/`, `views/blackjack/`) may extend
  `discord.ui.View` directly when specialized lifecycle is required — add a comment.
- **Always** re-check authority/capability at the callback execution time.
  Opening a panel does not authorize later callbacks.
- **Never** import from `cogs/` in view code.
- **Never** put a utility function needed by other layers in `views/`.
  If `services/` and `views/` both need a function, it belongs in `utils/`.

## Before adding a utility function
Read `docs/helper-policy.md` — even one shared function in the wrong layer
becomes a source of architectural violations.
