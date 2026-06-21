# Channel-deployed component-menu primitive (role menus · starboard · polls)

> **Status:** `ideas` — capture only, not a plan, not approval. Source + binding contracts win.
> **Subsystem:** role
>
> **Session idea (2026-06-21, Q-0089, from the Carl-bot reaction-roles overhaul plan).**

## The pattern

The reaction-roles overhaul plan ([`planning/reaction-roles-overhaul-plan-2026-06-21.md`](../planning/reaction-roles-overhaul-plan-2026-06-21.md))
needs a `PersistentView` an operator **deploys to an arbitrary channel**: build it in a panel →
post the message → store its `message_id` → re-attach on restart → toggle state server-side. That
exact shape recurs in at least three captured features:

- **Role menus** (this plan, PR 2).
- **Starboard** ([`fun-and-ease-brainstorm-2026-06-09.md`](./fun-and-ease-brainstorm-2026-06-09.md) §B1) — a posted, persisted highlight message that accrues reactions.
- **Polls / suggestion board** ([`superbot-vision-2026-06-10.md`](./superbot-vision-2026-06-10.md) AG-15) — a posted message with vote components.

Today each would hand-roll "post a message, remember its id, re-bind the view on boot." We already
have the *pieces* — `core/runtime/persistent_views.py` and `core/runtime/message_anchor_manager.py`
— but no single seam for **"an operator-deployed, DB-persisted component message in a guild channel."**

## The idea

A small shared primitive (`views/` or `core/runtime/`) — provisionally `deploy_component_message(...)`
+ a `deployed_messages(guild_id, channel_id, message_id, kind, ref_id)` registry — that owns the
post → persist `message_id` → re-attach-on-boot lifecycle, so role-menu / starboard / poll features
are each ~"define the view + the toggle handler," not "re-implement message persistence." Build it
**as part of** reaction-roles PR 2 (first real consumer), then starboard reuses it for free — the
classic "extract the second time you'd copy it" rule, but the second consumer is already on the
backlog so the extraction is justified at consumer #1.

**Why it's worth having:** it turns "modernize emoji reactions → components" from a per-feature
rewrite into a one-time platform capability, and gives every deployed message restart-durability +
guild-teardown for free (the INV-I hook lives in one place, not three).

→ relates `core/runtime/persistent_views.py` · `core/runtime/message_anchor_manager.py` ·
`planning/reaction-roles-overhaul-plan-2026-06-21.md` · `ideas/fun-and-ease-brainstorm-2026-06-09.md` §B1.
