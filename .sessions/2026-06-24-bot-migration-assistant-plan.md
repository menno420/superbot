# Session — 2026-06-24 · bot-migration-assistant plan

> **Status:** `complete` — docs-only planning. Single push, born-red → ready.

**Trigger:** continuation of the bot-migration-assistant idea capture (PR #1415, merged). Owner chose
**capture idea + write a plan**, with the catalog seeded for **top general bots + ticket/support bots**.

## What changed

- **New plan** [`docs/planning/bot-migration-assistant-plan-2026-06-24.md`](../docs/planning/bot-migration-assistant-plan-2026-06-24.md)
  — a 3-PR buildable spec (PR 1 detect-report read-only · PR 2 replicate via Final Review · PR 3 retire
  owner-gated), grounded in verified seams: `SetupSection` registry (`services/setup_sections.py`),
  `guild_snapshot.collect()`, `utils/subsystem_registry.py` (the replace-target catalog), the setup
  advisor → draft → Final Review path, and `moderation_service.kick(member, *, reason, actor_id,
  channel)`. The hard Discord constraint (no cross-bot command introspection) drives the curated
  app-id-keyed catalog design. Initial catalog: MEE6 · Dyno · Carl-bot · ProBot · Ticket Tool ·
  Tickety/Helper.gg. 5 design Qs for the owner.
- **Idea routed** — `docs/ideas/bot-migration-assistant-2026-06-24.md` header now points to the plan.
- **Plan index** — S1 row added after `giveaway-system` (the sibling competitive-teardown plan).
- `check_docs --strict` green.

## Verified before writing (so the plan is grounded, not guessed)

- `member.bot` detection already in `security_cog`/`welcome_cog`; `intents.members` on in `bot1.py`.
- `SetupSection` fields (slug/label/run/op_kinds/recommended_ops_builder/depths) + import-time register.
- `kick()` signature confirmed (audited, hierarchy-checked, optional channel cleanup).
- `subsystem_registry` entry shape (display_name/visibility_tier/entry_points/capabilities) → the
  `replaces` keys can be test-pinned against it.

## 💡 Session idea (Q-0089)

**`check_competitor_catalog.py` — catalog↔registry key guard.** The plan's correctness hinges on every
catalog `replaces` value being a real `subsystem_registry` key (a typo silently maps a competitor
feature to nothing). That's the proven Q-0105 3-file disposable-tool shape: a stdlib check that loads the
catalog + the registry and fails on any `replaces` key not in the registry, plus a warn when a popular
catalog bot has *no* mapped feature. It's the migration-assistant analog of the existing
`check_dashboard_data` cog→subsystem resolution guard — write it alongside PR 1 so the catalog can't rot
as it grows (open question §9.5 names exactly this growth risk). Genuine; prevents a real silent-failure
class before the catalog has more than 6 entries.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` log: this session's own predecessor — the **bot-migration-assistant *idea capture***
(PR #1415, merged). Did well: it answered the owner honestly (named the one hard Discord constraint up
front instead of overselling), grounded the capture in real seams via two parallel `Explore` agents, and
followed the full born-red → ready → auto-merge workflow cleanly. What it could have done better: it
offered a "Build the whole thing" option in the follow-up question that included the *irreversible kick
path* in a single session — that would have violated the safety brake (irreversible/outward-facing work
asks first), so presenting it as a peer option was slightly off; the owner's "capture + plan" pick made
it moot, but the option set should have flagged PR 3 as owner-gated. **System improvement this surfaces:**
when a follow-up `AskUserQuestion` offers a "do it all now" option for a feature with an
irreversible/outward-facing phase, that option should *name the gate* in its description rather than
present unrestricted scope — a small discipline for option-writing that keeps the safety brake visible at
the decision point. Applied it here: PR 3 (retire) is explicitly owner-gated in both the plan and the PR.

## 📋 Doc audit (Q-0104)

Anything not in its durable home? No. Plan + design Qs live in the plan; the idea doc routes to it; the
plan index lists it; no owner *decision* was made (workflow-step + scope picks, not a product/arch
ruling), so no router Q-block is owed. `check_docs --strict` green. No `current-state.md` ledger change
(no merged runtime PR — both PRs this session are docs-only).

## Context delta

- **Surprise:** the seams are even more ready than the idea capture estimated — `kick()` already takes an
  `actor_id` + channel-cleanup, and the advisor/draft/Final Review path means *replication needs no new
  mutation primitive at all*. The only genuinely new code is the catalog + the snapshot's bot-roster read
  + the section UI.
- **For next session (if greenlit):** start at PR 1 (detect & report, read-only) + the
  catalog↔registry guard above. Resolve open Q §9.1 (catalog home: shared with V-14 teardown?) first —
  it's the one decision that shapes the data layer.

## ⚑ Self-initiated: none — owner-directed (the owner explicitly chose "capture idea + write a plan" and
the catalog scope). Plan is plan-first; build needs a greenlight.
