# Idea — a guard for `discord.ui.View` subclasses mislayered in `cogs/`

> **Status:** `ideas` — session idea (Q-0089), 2026-06-14 night executor.
> **Lane:** tooling / architecture invariant. Small/safe grooming-lane candidate.

## The gap

The baseview-conformance ratchet (`tests/unit/views/test_view_base_class_conformance.py`
→ `check_architecture.py:check_baseview_inheritance`) only scans `disbot/views/`. So a
`discord.ui.View` subclass **defined in a `cogs/*.py` file** is completely invisible to it —
neither flagged as direct-View debt nor required to extend `BaseView`.

Observed this session: `_ChannelListPaginatorView` (the `!list` paginator) had lived in
`cogs/channel_cog.py` for a long time. It is view/rendering code that the F-3 convention
says belongs in `views/channels/`, but nothing detected the mislayering — it surfaced
**only by accident** when the P0-4 convergence pushed the cog over the 800-LOC ceiling and
forced an extraction. A cog that stays under the ceiling could hide such a view forever.

## The guard

`scripts/check_layer_residence.py` (or a new case in the existing architecture checker):
flag any class that subclasses `discord.ui.View` / `discord.ui.Modal` (directly or via a
known base) whose **module path is under `disbot/cogs/`**. The cog layer hosts command
dispatchers and Discord-facing surfaces; UI views/modals belong in `views/<sub>/`.

- Start in **warn** mode (there may be other pre-existing offenders — RPS/blackjack inline
  views, etc.), inventory them, then ratchet to error like the baseview test does.
- Pairs naturally with the cog-size test: both exist to keep view/persistence code OUT of
  cogs; this one catches the case the size ceiling misses.

## Why it's worth having

It closes a real blind spot in the layering enforcement (the ratchet trusts `views/` to be
the only home for views, but doesn't *enforce* that cogs aren't a second home). Cheap,
stdlib-AST, verifiable against ground truth. Carries the standard "unverified — confirm a
few times, delete if it proves noisy" provenance header when built.
