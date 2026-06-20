# Idea — a guard for `discord.ui.View` subclasses mislayered in `cogs/`

> **Status:** `ideas` — session idea (Q-0089), 2026-06-14 night executor.
> **Lane:** tooling / architecture invariant. Small/safe grooming-lane candidate.
> **Progress:** *partially built* — direct-View half DONE (PR #1163, 2026-06-20); residence
> half routed for an owner decision (see ▶ Update below).
>
> **▶ Update 2026-06-20 (dispatch run, PR #1163): the *direct-View debt* half is DONE.**
> `check_architecture.py:check_baseview_inheritance` + its conformance ratchet
> (`tests/unit/views/test_view_base_class_conformance.py`) now scan **`cogs/`** as well as
> `views/`, and the 5 existing cog-layer direct-`discord.ui.View` classes are pinned in the
> frozenset. So the idea's concrete observed gap — *"a `discord.ui.View` subclass in a cog is
> neither flagged as direct-View debt nor required to extend `BaseView`"* — is closed: a new
> cog-layer direct-`discord.ui.View` class now fails the ratchet.
>
> **▶ Update 2026-06-20 (dispatch run, PR #1166): the two copies of the direct-View allowlist are
> now pinned together.** The same set is enumerated twice — the arch conformance frozenset (above)
> and the warn-only consistency-linter `panel_base_class` allowlist
> (`architecture_rules/consistency_exceptions.yml`). A new parity test
> (`tests/unit/views/test_panel_base_class_allowlist_parity.py`) fails CI the instant they diverge,
> so a one-sided ratchet can no longer silently desync them. The *direct-View* half is now both
> caught (the ratchet) and drift-proofed across its two homes (the parity guard).
>
> **▶ What remains = the broader *residence* guard (the "no views defined in cogs at all"
> stance) — needs an OWNER decision before it's built.** Inventory taken this run: **38**
> view/modal classes currently live under `disbot/cogs/` (most correctly extend
> `HubView`/`PersistentView`/`BaseView`/`discord.ui.Modal` — they're a cog's own hub/panel,
> not direct-View debt). A residence ratchet that declares all 38 "must move to `views/`" is a
> cross-cutting architectural call (for many — a cog's own hub panel — `views/` residence is a
> judgment call, not an obvious win), so it is **routed for owner input, not built unilaterally**
> (act-vs-ask: architectural/cross-cutting → ask). Decision needed: *is "Discord view/modal
> classes must be defined under `views/`, never inline in `cogs/`" a rule worth a 38-class
> warn-then-ratchet guard?* If yes, build it warn-only first (38-entry inventory pin, same
> pattern as the baseview ratchet) then ratchet to error as classes migrate.

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
