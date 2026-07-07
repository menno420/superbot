# Channel-level, role-scoped access is missing — live bot AND the frozen rebuild design

> **Status:** `ideas` — capture only, not approved for implementation. Owner-raised 2026-07-07
> ("it's currently not easily possible to add certain role restrictions to certain channels"),
> researched the same day against both the live bot and the rebuild's frozen K6 design.
> **Subsystem:** none (cross-cutting authority-model gap; confirmed in both the live governance
> stack and the rebuild's K6 authority engine).
>
> **Priority flag: this one is time-sensitive, unlike most items in this backlog.** K6 (the
> rebuild's authority engine) has **not been built yet** (canonical plan
> [`rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md) §5 step
> 9 — "not started"), and per the plan's own build-order note, K6 sits **on the strand-1 chain**:
> S8 (K7, the workflow engine) consumes K4+K5+K6, so a missing K6 primitive is not a cheap
> after-the-fact patch — it is upstream of everything K7/K8 build on. This is the one item from
> this session's sweep worth raising **before** the next K6-touching session, not filed for later.

## The gap, confirmed at both layers

**Live bot today** — three separate systems handle "who can do what where," and none of them can
express "only role X in channel Y":

- **Command-channel admission** (`disbot/core/runtime/command_access.py:189-259`) — a guild-wide,
  per-command *channel allow-list*. No role dimension at all.
- **Cog routing** (`disbot/services/command_routing.py:57-79`) — per-channel/per-category on/off
  toggle for a whole cog. Also role-blind.
- **Governance visibility/tier** (`disbot/governance/capability.py`,
  `disbot/governance/models.py:89-106`) — an ordinal rank (`user < mod < admin < owner`-like)
  resolved from a member's roles but collapsed into one tier string. It answers "does this member's
  *rank* clear the bar," never "is this member specifically in role X."
- **Access Map** (`disbot/services/access_projection.py`) — explicitly documented as composing only
  the three systems above ("no policy of its own"), so it inherits the same blind spot rather than
  closing it; it even notes it "cannot model live Discord channel-permission overrides"
  (`access_projection.py:396-397`).

The one place a *specific role* could plausibly be targeted — `ChannelLifecycleService`'s
`overwrite_target_id`/`"role"` parameter (`disbot/services/channel_lifecycle_service.py:102-103,
521-527`), which edits real Discord channel permission overwrites — is wired, but **every live
caller hardcodes `@everyone`** (`disbot/cogs/channel_cog.py:498-529`'s `!lock`/`!unlock`,
`disbot/views/channels/restrict_panel.py:147-178`). There is no `!channel lock @role` command or UI
path today, even though the plumbing underneath could support it.

**The frozen rebuild design (K6)** has the identical shape, not an improvement:

- `resolve_authority` classifies every authority check into exactly `Lane{CAPABILITY, TIER}`
  (canonical plan §2.1 K6 row; `rebuild-gate0-worklist-2026-07-04.md:75-79`) — still capability-name
  or ordinal-tier, never a specific role.
- Channel admission is formalized as `ChannelAccessDecision`/`AccessMode{all_channels,
  selected_channels, disabled_except_bootstrap}` — **the same guild-wide, role-blind allow-list
  model as today's `command_access.py`**, verbatim value strings preserved on purpose.
- `BindingSpec.authority_ref` (design spec §2.5) reuses the same capability/tier authority for who
  may *configure* a binding — still not "who may use the feature this binding points at."

So this isn't a bug to fix in the old bot and forget — it's a primitive the frozen grammar doesn't
have, and the rebuild is currently on track to carry the exact same gap forward.

## What "restriction" could mean — two distinct asks worth separating

1. **A convenience command to manage Discord's own native channel permission overwrites for an
   arbitrary role** ("`!channel restrict #farming @Farmers`" — a common feature in other mod bots).
   This is mostly a UI/command gap today: the service-layer plumbing (`overwrite_target_id`) already
   supports an arbitrary role, it's just never exposed past `@everyone`.
2. **A bot-level declarative concept**: a subsystem's channel binding (or a command/feature) says
   "only role X may interact with this," enforced by the bot's own authority check — independent of,
   and layered on top of, raw Discord permissions (so it still works even if the channel is
   otherwise visible to everyone, e.g. a channel that's *readable* by all but where only a
   "Farmers" role can run farm commands). Neither the live governance stack nor the frozen K6 design
   has this primitive at all.

Both are real gaps; (2) is the foundational one and the reason this needs deciding before K6/K7/K8
lock in, since it's an authority-model shape question, not a feature to bolt on later.

## Design sketch (for whoever picks this up)

1. **Add a role-scoped lane to the authority model** — e.g. `Lane.ROLE_SET` alongside
   `CAPABILITY`/`TIER` in `resolve_authority`'s classification, so a `BindingSpec.authority_ref` or a
   `CommandSpec` can declare "requires membership in one of these Discord role IDs" as a first-class
   alternative to a capability name or an ordinal tier, resolved into the same `AuthorityDecision`
   shape everything else already consumes.
2. **Extend `ChannelAccessDecision`/`AccessMode`** with a role-scoped variant (or let the existing
   allow-list model carry a per-entry role-set instead of being purely guild-wide), so "this
   channel's bot features are gated to role X" is expressible without inventing a second system next
   to it.
3. **Re-check at interaction time, not just panel-open** — this needs to follow the same rule
   already established for authority elsewhere in the design (a user losing the role mid-session
   must be denied on the next click, not just at initial admission).
4. **Separately, expose the existing overwrite plumbing properly** — a `!channel restrict <channel>
   <role>` command/UI path that lets `overwrite_target_id` target an arbitrary role, not just
   `@everyone`. This is the smaller, live-bot-only half and could ship independently of the K6 work
   above if there's appetite to fix it before the rebuild even starts.

## Recommended routing

This should be raised explicitly with whoever writes K6's Phase-B per-step plan (canonical plan §5
step 9, not yet started) — ideally *before* that plan is written, since retrofitting a role-scoped
authority lane after K7/K8 are built against the current `Lane{CAPABILITY,TIER}` shape is
substantially more expensive than adding it now. Given the "frozen grammar" discipline this repo
uses, this is the kind of finding that would normally become a numbered amendment (like the
canonical plan's §11 A-series) at the next review pass that touches K6 — flagging it here so it
doesn't have to be rediscovered from scratch then.
