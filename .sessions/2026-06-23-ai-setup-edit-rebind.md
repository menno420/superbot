# 2026-06-23 — AI-setup Edit: re-pick target for `bind` suggestions (self-initiated)

> **Status:** `in-progress` — **self-initiated follow-on** (Q-0172, flagged below) completing #1386's Edit
> affordance. #1386 added Accept/Deny/Edit; Edit renames a `create` suggestion but only *explains* on a
> `bind` one. This lets Edit on a `bind` suggestion **re-pick the existing target** via a channel/role
> select, in place. Stays propose-only (apply remains the gated Final Review — Q-0199). PR this session;
> auto-merge on green (Q-0127).

> **Run type:** `manual · self-initiated (contained follow-on)`
> **⚑ Self-initiated:** completes the Edit feature shipped in #1386 — the follow-on the #1386 / Q-0199
> session cards both named. Contained, reversible, propose-only, test-covered (Q-0172 "build freely").

## The gap (from #1386)

`per_recommendation.py` `_edit`: for `create` it opens a rename modal; for `bind` (binds an existing
channel/role/category) it sends an ephemeral "can't rename — Deny + rebind". So the operator can't
*correct the AI's pick* of an existing resource without leaving the walkthrough.

## Plan

- Factor `_swap_and_accept(old, edited)` out of `apply_edit`; add `apply_retarget(old, *, target_id,
  target_name)` (re-`dataclasses.replace` the `target_id`/`target_name`, keeping `mode="bind"`).
- `_edit` on a `bind` rec of a selectable kind (`channel`/`category`/`role`) → opens `_RepickTargetView`
  (a `discord.ui.ChannelSelect` with the kind's channel types, or `RoleSelect`, + Cancel). On select →
  `apply_retarget` → advance. Kinds that can't be selected (`thread`/`member`) keep the explain ephemeral.
- No DB / Discord writes (the module's zero-write contract tests stay green); the re-targeted op still
  applies only through the gated Final Review.
- Tests: bind+channel opens the re-pick view; the select callback retargets+accepts+advances;
  `apply_retarget` swaps id/name into the draft + accepts; unsupported kind still explains.

(Close-out enders at session close.)
