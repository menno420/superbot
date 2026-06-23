# 2026-06-23 — AI-setup Edit: re-pick target for `bind` suggestions (self-initiated)

> **Status:** `complete` — **self-initiated follow-on** (Q-0172, flagged below) completing #1386's Edit
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

## Close-out

**Verification:** `mypy disbot/` clean (824 files); full pytest **12202 passed**; `check_architecture
--mode strict` 0 errors; `check_quality --check-only` green; the module's zero-write contract tests
(`test_module_has_no_db_imports`, `test_module_has_no_direct_discord_create_calls`) stay green
(ChannelSelect/RoleSelect are not resource creates); ledger + `check_docs --strict` pass (Q-0104).

**mypy note:** discord.py's `Select` is generic per value-type (the default `Select` is `Select[str]`, so
`.values` types as `str`); the kind is chosen at runtime, so the re-pick select is held as one `Any`-typed
handle rather than a `RoleSelect | ChannelSelect` union (the house pattern elsewhere subclasses a single
select type — not possible when the type is runtime-chosen).

**💡 Session idea (Q-0089):** *Re-pick should pre-filter the select to the same category, when the binding
implies one.* The current ChannelSelect lists all text/news channels; for a binding whose AI pick sat
under a specific category (e.g. a staff category), defaulting/scoping the picker to that category would
make the correction faster. Bounded follow-on on the same seam. (Captured.)

**⟲ Previous-session review (Q-0102):** the previous session (Q-0199 router record) correctly applied its
own surfaced lesson — *close a small durable-home gap immediately rather than queueing it for
reconciliation* — which is exactly why this Edit follow-on was reachable as "where I left off" (the gap
was named, not buried). It did well to keep that PR docs-only and tightly scoped. Nothing it missed of
note. **System improvement (applied):** this session flagged its self-initiated nature on the card's
`⚑ Self-initiated:` line (Q-0172 accountability) *before* building — making unprompted work auditable at a
glance is the discipline that lets the chain self-initiate safely. Keep doing that on every unprompted PR.

**Claim** `docs/owner/claims/claude__ai-setup-edit-rebind.md` deleted at close (Q-0126).

