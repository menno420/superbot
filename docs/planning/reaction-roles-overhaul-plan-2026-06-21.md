# Reaction Roles — Carl-bot parity + modern role-menu overhaul

> **Status:** `plan` — buildable spec (2026-06-21). Cross-check source before implementing;
> `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product. **Folio:**
> [`docs/subsystems/server-management.md`](../subsystems/server-management.md).
>
> **One-line goal:** bring SuperBot's self-assignable-role surface to **parity-plus** with
> Carl-bot — lead with native **buttons + dropdown menus** (Carl's are a secondary/premium
> add; emoji reactions are its core), keep emoji reaction-roles working for compatibility,
> layer Carl's modes (unique / verify / limit) on top, and route every assignment through an
> **audited mutation seam** — closing the documented architectural debt along the way.

---

## 1. Why this plan exists

Three things converged:

1. **Owner ask** — research how Carl-bot does reaction roles + what we're missing, then plan
   how to implement and improve on it.
2. **SuperBot already has a basic reaction-role feature** but it is the project's clearest
   piece of **documented architectural debt**: it writes to the DB directly (no audit), has no
   modes/limits, and its management panel is read-only. See
   [`audits/general-feature-layer-analysis-2026-06-05.md`](../audits/general-feature-layer-analysis-2026-06-05.md)
   ("reaction-role CRUD … use direct DB/Discord mutation paths") and
   [`audits/ui-view-adoption-audit.md`](../audits/ui-view-adoption-audit.md) (the
   `ReactionRolesPanel` is hand-rolled, P1).
3. **"Self-role menu / reaction-role setup" is already on the backlog**
   ([`building-roadmap/command-expansion-backlog.md`](../building-roadmap/command-expansion-backlog.md)
   §"Self-role menu; Reaction-role setup") and the
   [`server-management-status`](server-management-status-2026-06-05.md) remaining queue
   ("reaction roles / automation add_roles/remove_roles; role reorder; templates"). This plan
   **consolidates** that scattered backlog into one coherent, buildable arc — it is not
   net-new invention.

So this is a **fix-debt + ship-headline-feature** plan, not a greenfield one.

---

## 2. How Carl-bot does reaction roles (researched 2026-06-21)

Sources: [official docs](https://docs.carl.gg/) and the
[`carlbot-docs` source](https://github.com/CarlGroth/carlbot-docs/blob/master/roles/reaction-roles.md).

**Core model.** Members self-assign roles by reacting with an emoji on a bot-tracked message.
Carl is fundamentally **emoji-reaction based**; button/dropdown menus are a newer/secondary
surface, and timed roles are a Patreon perk.

**Setup methods** (three): post a new embed; turn an existing message into a reaction-role
message by ID; or use the most recent message in a channel. Plus all-in-one one-shot commands
(`rr aio`, `aiou`, `aiov`, `aioi`) and a standalone `embed` builder.

**Modes** (applied per message via `rr <mode> <msg_id>`):

| Mode | Behaviour |
|---|---|
| `normal` | React = add role, un-react = remove role (the default). |
| `unique` | Only one role per message; reacting auto-removes the member's previous pick. |
| `verify` | React **only adds** (never removes); the bot removes the reaction afterward. |
| `drop` | Inverse of verify — reacting **only removes** a role. |
| `reversed` | Reacting removes the role; un-reacting adds it. |
| `binding` | `verify` + `unique` — a single lifetime choice across linked messages. |
| `temp <time>` | Role auto-removed after a duration (**Patreon-only**). |

**Message controls:** `rr lock` (freeze distribution), `rr selfdestruct <time>` (auto-delete
message + roles after a period).

**Access restrictions:** `rr limit <n>` (cap how many roles a member can claim from a message),
`rr maxroles <role> <n>` (cap total members holding a role), role **blacklist/whitelist**
(`rr bl` / `rr wl` and their clears).

**Multi-message linking:** `rr link` makes "one role across all linked messages" work — Carl's
workaround for its **20-reaction-roles-per-message** Discord limit (their total cap is **250**).

**Management commands:** `rr setup/make`, `list/show`, `edit`, `add`, `addmany`, `remove`,
`move` (transfer roles between messages, including purged ones), `clear`, `colour`.

**Key limits to remember:** 20 reaction-roles per message (Discord's reaction cap), ~250 total.
`reversed`/`verify` exist precisely because **emoji reactions are clumsy** — stale reactions
linger, "remove your reaction to lose the role" is unintuitive, and adding a reaction needs the
emoji to be addable. **This is the weakness we improve on.**

---

## 3. What SuperBot has today (code-grounded)

Full inventory: the role subsystem is mature. Reaction roles specifically:

- **Schema:** `reaction_roles (guild_id, message_id, emoji, role_id)`, PK
  `(guild_id, message_id, emoji)` — bootstrap table in
  `disbot/utils/db/migrations.py:284`. CRUD in `disbot/utils/db/roles.py:201-240`.
- **Assignment:** raw listeners `on_raw_reaction_add` / `on_raw_reaction_remove` in
  `disbot/cogs/role_cog.py:546-594` → `member.add_roles` / `remove_roles`. **Emoji-only.**
- **Commands** (`role_cog.py:596-661`): `!reactroles <msg_id> <emoji> <@role>`,
  `!removereactrole <msg_id> <emoji>`, `!listreactroles`.
- **Panel:** `disbot/views/roles/reaction_panel.py` — **read-only** display + a refresh button;
  configuration is command-only.

**Adjacent role features already shipped** (do **not** rebuild these): time/tenure roles + XP
roles (`services/role_automation.py`, audited), per-role automation exemptions
(`services/role_exemption_service.py`, audited), role lifecycle create/edit/delete
(`services/role_lifecycle_service.py`, audited), diagnostics, and the entry/join role
(`welcome_service`). The role hub (`!roles`) already routes Create / Manage / Time / XP /
Reaction / Diagnostics panels.

### The three gaps vs. our own standards

1. **No audited seam.** Time/XP/exemption/lifecycle role writes all emit
   `audit.action_recorded`; reaction-role writes go straight to `utils/db/roles.py` from the
   cog. This violates the mutation contract (`docs/runtime_contracts.md` §9) and is the
   long-standing audit finding above.
2. **No interactive UI.** The panel can't add/edit/remove — operators must hand-type a message
   ID + emoji into a prefix command.
3. **Emoji-only, no menus, no modes, no limits** — the entire Carl feature surface (buttons,
   dropdowns, unique/verify, per-message limits) is absent.

---

## 3.5 UI direction — the owner's Carl reference is a **web dashboard** (2026-06-21)

The owner shared a screen recording of "the menu we need." **Important clarification it
settles:** that menu is **Carl-bot's web dashboard** (`carl.gg/dashboard`) opened in a phone
**browser** — *not* the Discord app. Everything in it is **HTML web-form UI**: a native
`Message type` `<select>` (the modes `normal / unique / verify / drop / reversed / limit /
binding / temp`, each with a live description), radio-button mode list, a numeric `limit` field,
two "Select option" role **multi-selects** (allow-list + blacklist), a `Show embed builder`
toggle, an `Add emoji` button, a yellow **"Get Premium"** upsell for `temp`, and Cancel/Create.

**This answers the "is this even possible in discord.py?" question — and the answer has two
halves:**

- **The *exact* screen is not a Discord UI at all**, so no Discord library (discord.py or
  otherwise) can render it. It's a **website** talking to the bot over an API. The bot's
  language is a red herring — Carl's backend is Python too; the recording is its *web frontend*
  (JS/HTML/CSS). discord.py can only render **Discord's own components** (buttons, string/role
  selects, modals — incl. label-wrapped selects) **inside Discord**, not an arbitrary scrolling
  web form with radio lists + multiple dropdowns on one page.
- **We are unusually well-placed to build this — and make it nicer.** SuperBot already ships a
  website + dashboard and a **Claude-Design React/Tailwind design system** (`design-system/`,
  `botsite/`, the dashboard control-API lanes). Carl's form looks **dated**; ours can be a clean,
  modern, mobile-smooth page on infrastructure we already own. That is the owner's
  "make it look nicer and work smoother" — realized on our design system, not by copying Carl's form.

**So the feature targets two complementary surfaces** (same audited service + data model
underneath — §4 PR 1 serves both):

| Surface | What it is | Status |
|---|---|---|
| **A — Web builder** (the video) | a reaction-role/menu builder **page in our own dashboard** (React/Tailwind), writing through the control-API → bot. The "nicer, smoother" target. | **gated on the control-API write side** (owner-paced + security review — already a tracked lane in `current-state.md`). Not the first buildable slice. |
| **B — In-Discord builder** (§4 PR 2) | a modern in-Discord builder using **buttons + select menus + modals** — laid out as a short multi-step flow (Discord's 5-row/25-option limits forbid one giant form), strictly nicer than Carl's emoji-reaction core. | **buildable now** — no web/control-API dependency. |

**Sequencing implication:** build B first (it's unblocked and delivers the feature in-Discord),
and add A as the polished web surface when the control-API write side opens. Both sit on the same
PR 1 foundation, so neither is wasted. The owner's "nicer/smoother" bar applies to **both** — B
uses our component design vocabulary (`docs/ux/pattern-library.md`), A uses the design system.

---

## 4. The plan — three PRs (foundation → headline → parity)

Per repo rule, a plan spans 2–3 PRs: **PR 1 fixes root causes/foundation; PR 2–3 build on top.**
PR 1 is a safe internal refactor (no UX change); the user-visible feature lands in PR 2.

### PR 1 — Audited seam + data model (foundation, low-risk)

**Goal:** route every reaction-role mutation through an audited service, and extend the data
model to support menus/modes — with **zero behaviour change** for existing emoji reaction-roles.

- **New `disbot/services/reaction_role_service.py`** — the audited writer, mirroring
  `role_exemption_service.py`: thin methods (`bind_emoji`, `unbind_emoji`, `assign`, `unassign`,
  list/read helpers) that wrap the existing `utils/db/roles.py` CRUD and emit
  `services.audit_events.emit_audit_action()` for operator config changes (binding add/remove)
  and, optionally, for member assignment (behind a flag — assignment volume may be high).
- **Route the cog through it.** The `role_cog.py` listeners + the three commands call the
  service instead of `db.*` directly. This **closes the audit-seam finding** and the
  `general-feature-layer-analysis` items.
- **Migration `078_reaction_role_menus.sql`** (next free number is 078; highest today is 077).
  Add the menu/mode data model. Recommended shape — a new pair of tables so menus and raw-emoji
  bindings coexist cleanly, rather than overloading `reaction_roles`:
  ```sql
  CREATE TABLE IF NOT EXISTS role_menus (
      menu_id     BIGSERIAL PRIMARY KEY,
      guild_id    BIGINT NOT NULL,
      channel_id  BIGINT NOT NULL,
      message_id  BIGINT,                       -- set once the menu message is posted
      title       TEXT   NOT NULL DEFAULT 'Pick your roles',
      description TEXT,
      style       TEXT   NOT NULL DEFAULT 'button',  -- 'button' | 'dropdown' | 'reaction'
      mode        TEXT   NOT NULL DEFAULT 'normal',  -- 'normal' | 'unique' | 'verify'
      max_roles   INT    NOT NULL DEFAULT 0,         -- 0 = unlimited (Carl's `rr limit`)
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
  );
  CREATE TABLE IF NOT EXISTS role_menu_options (
      menu_id  BIGINT NOT NULL REFERENCES role_menus(menu_id) ON DELETE CASCADE,
      role_id  BIGINT NOT NULL,
      emoji    TEXT,                              -- optional button/option emoji
      label    TEXT,                              -- optional override label
      position INT NOT NULL DEFAULT 0,
      PRIMARY KEY (menu_id, role_id)
  );
  ```
  The legacy `reaction_roles` table stays as-is (emoji surface = `style='reaction'` conceptually;
  no data migration needed in PR 1).
- **DB module** `disbot/utils/db/roles.py` (or a new `utils/db/role_menus.py` if `roles.py` is
  getting large) — typed CRUD for the two tables.
- **`disbot/guild_lifecycle.py`** — register `delete_for_guild` teardown for `role_menus`
  (cascade handles `role_menu_options`). Required for any new guild-keyed table
  (`docs/architecture.md` INV-I).
- **Tests:** service-level audit-emission test (mirror `test_role_exemption_service.py`); DB
  round-trip; a guild-teardown test asserting the new table is purged.

**Risk:** low. Internal refactor + additive schema; existing reaction-roles behave identically.

### PR 2 — Interactive role menus (the headline improvement = **Surface B**, §3.5)

**Goal:** the modern, native surface Carl lacks at its core — a button/dropdown role menu an
operator builds in-panel and deploys to a channel, re-attached on restart. This is the
**buildable-now in-Discord builder** (the web builder, Surface A, rides the control-API later).

- **`disbot/views/roles/role_menu_view.py`** — a `RoleMenuView(PersistentView)` that renders
  either buttons (one per role, ≤25) or a `discord.ui.Select` (multi-select up to `max_roles`).
  Click/select **toggles** the role with an **ephemeral confirmation** ("✅ Added **Gamer**").
  Mode enforcement is **server-side**: `unique` clears the member's other menu roles; `max_roles`
  caps selections — no stale reactions, no "un-react to remove" confusion. Follows the
  `PersistentView` contract (`docs/runtime_contracts.md` §3) so menus survive restarts via the
  persistent-view registry (`core/runtime/persistent_views.py`).
- **`disbot/views/roles/role_menu_builder.py`** — the operator builder panel (reached from the
  Reaction Roles panel / role hub): set title/description, pick roles
  (`views/selectors/` role selector — windowed via `attach_windowed_select`, the repo's
  >25-option pattern), choose button vs dropdown, choose mode, set the per-member limit, then
  **Post** (creates the `role_menus` row, sends the message, stores `message_id`).
- **All writes through `reaction_role_service`** (audited). The view is a thin UI over the
  service — no DB writes in views (`docs/architecture.md` layer rules).
- **Capability-gated** like the rest of the role hub (`manage_roles` / the role config
  capability); re-check authority at callback time (`.claude/rules/discord-views.md`).
- **Tests:** view-renders-from-menu-row; toggle adds/removes via the service; unique-mode clears
  siblings; persistent-view re-attach registration.

**Risk:** medium (new persistent view + runtime wiring) — scoped to the new tables, additive.

### PR 3 — Carl-parity modes + interactive emoji-panel + settings bridge

**Goal:** finish parity and close the read-only-panel finding.

- **Modes on the emoji surface too:** add `unique` / `verify` to the raw-reaction path in the
  service (verify = add-only + remove the reaction; unique = clear sibling emoji roles on this
  message). Stored per `role_menus` row (or a small `reaction_role_modes` map for legacy
  message-keyed bindings).
- **Convert `ReactionRolesPanel` to interactive** — add/edit/remove buttons (modal for
  message-id+emoji+role, picker for removal), and a list of deployed **menus** with edit/delete.
  Closes the `ui-view-adoption-audit` P1 finding (hand-rolled → standard add/edit/remove panel).
- **Settings bridge (optional):** wire the `reaction_roles_enabled` /
  role-menu-channel keys already anticipated in
  [`operator-settings-presets.md`](../setup-platform/operator-settings-presets.md) so the feature
  is toggleable per guild and presettable.
- **Stretch (beats Carl's paywall): free temporary roles.** Carl gates `temp` behind Patreon. We
  can offer it free by reusing the managed-task / scheduled-maintenance machinery — but it needs
  a `role_grants(guild_id, member_id, role_id, expires_at)` persistence table + a sweep loop.
  **Mark as a follow-up**, not in the parity core, to keep PR 3 bounded.

**Risk:** low-medium; mostly UI + small service additions on the PR 1/2 seam.

---

## 5. How we improve **on** Carl-bot (the "and improve on it" half)

| Dimension | Carl-bot | SuperBot (this plan) |
|---|---|---|
| Primary surface | Emoji reactions (buttons/menus secondary) | **Native buttons + dropdowns first**; emoji kept for compatibility |
| Stale-reaction problem | Inherent (reactions linger) | **None** — clicks are stateless, server-side toggle |
| Mobile / permission UX | Needs add-reaction perms, fiddly | One tap, ephemeral confirm; no reaction perms |
| Audit trail | None per assignment | **Every config change audited** (`audit.action_recorded` → `server_logging`) |
| Restart durability | Message-bound | **PersistentView** re-attach on boot |
| Timed roles | **Patreon-only** | **Free** (stretch, reuses tasks machinery) |
| Integration | Standalone | Unified role hub with time/XP roles + **exemptions**; capability-gated |
| Architecture | n/a | One audited service seam; layer-clean; CI-enforced invariants |

The headline: **Carl is constrained by its emoji-reaction legacy; we start from Discord's modern
component model**, so our default surface is strictly nicer, and we get auditability + restart
durability Carl can't offer.

---

## 6. Broader "other functions we're missing" — Carl-bot feature matrix

Beyond reaction roles, here is the full Carl-bot surface vs. SuperBot. **Most gaps are already
captured as ideas** — this plan routes/cross-references them, it does not re-capture them.

| Carl-bot feature | SuperBot status | Where captured / recommendation |
|---|---|---|
| **Reaction roles** | ✅ basic (emoji-only) | **← this plan** |
| **Automod** (spam, invites, caps, mentions) | ✅ shipped (`automod_cog`, Q-0108) | — |
| Automod **word-filter / link-filter / attachment-spam** | ❌ sub-gap | Small extension to `automod_cog` — add to the safety lane |
| **Logging** | ✅ shipped (`logging_cog`) | — |
| **Moderation** (+ image moderation) | ✅ shipped | — |
| **Levels** | ✅ shipped (`xp_cog`) | — |
| **Greetings / Welcome** | ✅ shipped (`welcome_cog`) | — |
| **Starboard / Hall of Fame** | ❌ missing | Captured: [`ideas/fun-and-ease-brainstorm-2026-06-09.md`](../ideas/fun-and-ease-brainstorm-2026-06-09.md) §B1 (quick-win; reuses the raw-reaction precedent this plan hardens) |
| **Custom commands / Tags & Triggers** | ❌ missing | Captured: [`ideas/community-platform-features-2026-06-12.md`](../ideas/community-platform-features-2026-06-12.md) §4 (Roadmap **Someday** — TagScript sandboxing risk) |
| **Suggestions** (community upvote/downvote board) | ❌ missing | Captured: [`ideas/superbot-vision-2026-06-10.md`](../ideas/superbot-vision-2026-06-10.md) AG-15 (tickets / suggestion box) |
| **Feeds / Notifications** (YouTube / Twitch / Reddit / RSS) | ⚠️ partial (media-youtube is content-fetch, not subscription pings) | Roadmap **Later** ([`roadmap.md`](../roadmap.md)) |
| **Tags / embeds builder** (user-facing) | ❌ minor gap | Fold a small `embed` builder into the role-menu builder / `utility_cog` |
| **Fun / Games** | ✅ extensive (blackjack, rps, mining, fishing, creature, …) | We **exceed** Carl here |

**Recommendation:** ship the reaction-role overhaul first (debt + headline feature in one), then
**starboard** is the highest-value, lowest-risk next Carl-parity item (already a captured
quick-win and it reuses the hardened raw-reaction seam). Custom commands and feeds stay
Someday/Later per their existing routing (sandboxing / external-poll cost).

---

## 7. Architecture & contracts checklist (binding)

- **Mutation seam:** all writes through `reaction_role_service`; emit `audit.action_recorded`
  (`docs/runtime_contracts.md` §9, `.claude/rules/mutation-and-db.md`). No `pool.execute` outside
  `utils/db/`.
- **Layers:** views never import cogs; service never imports views; DB only in `utils/db/`
  (`docs/architecture.md`).
- **PersistentView:** the role menu follows the §3 contract; registered in
  `core/runtime/persistent_views.py`.
- **Guild teardown:** new tables registered in `guild_lifecycle.py` (INV-I).
- **Settings/capability:** capability-gated like the role hub; optional `reaction_roles_enabled`
  via the settings schema.
- **Smoke test:** the role hub panels are pinned by
  [`smoke-test-checklist.md`](../smoke-test-checklist.md) ("TimeRoles / ReactionRoles return to
  RoleHubView") — keep the back-nav contract green when the panel becomes interactive.

## 8. Verification (before each PR ships)

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full          # black/isort/ruff + mypy + pytest
python3.10 scripts/check_docs.py --strict           # this plan must stay linked
```

## 9. Open questions for the owner (design calls, not blockers)

1. **Default surface:** lead operators toward **dropdown** (compact, one message, multi-select) or
   **buttons** (one tap, more visible)? Recommend dropdown as the default, buttons as a toggle.
2. **Audit member assignments?** Config changes: yes. Per-click member toggles could be high
   volume — recommend **off by default**, behind a flag.
3. **Free temp roles** (§4 PR 3 stretch) — worth the extra table + sweep loop, or defer?
4. **Surface priority (§3.5):** the owner's reference is the **web builder (Surface A)** but it's
   control-API-gated. Confirm: ship the **in-Discord builder (Surface B) first** (recommended —
   unblocked, delivers the feature now), then the web builder when the control-API write side
   opens? Or hold the whole feature for the web surface?

These are visualize-and-decide calls for the maintainer; none block PR 1 (the foundation), which
is pure debt-paydown and safe to build immediately.
