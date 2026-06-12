# UX Lab / Interface Gallery — a living Discord-UX sandbox cog

> **Status:** `ideas` — owner-commissioned brainstorm capture (2026-06-12). **Not
> approved for implementation as code yet** — the design is structured in
> [`../planning/ux-lab-interface-gallery-plan-2026-06-12.md`](../planning/ux-lab-interface-gallery-plan-2026-06-12.md)
> (owner-commissioned design session, 2026-06-12); scheduling + audience are open in
> router **Q-0116**. Source code and binding contracts win over anything here.

---

## 1. Owner intent (the ask, 2026-06-12)

> "I want this to eventually produce a testing cog, that just focuses on showing a lot
> of different types of UX, different interfaces, button styles, menu layouts — the
> purpose is that I can freely browse through the different styles and layouts so I can
> then compare to what the bot already has and which parts I would change into something
> new. It should include the most kinds of advanced button/interaction style messages and
> embeds that are possible; they shouldn't necessarily have to link to any real functions
> but they should have some kind of reaction or link to show how it would function. …
> design the most versatile and inclusive UX testing cog."

The maintainer is the **vision/taste layer** of this project (collaboration model): he
decides *which* UI shapes are right by **looking at them**, not by reading component
specs. Today there is no surface where he can look at a pattern that doesn't exist yet.
Every UX decision (Q-0078 help home, Q-0110 welcome embed-vs-card, the V-02 navigation
doctrine) is currently made from prose descriptions. The UX Lab closes that gap: a
browsable, clickable, zero-risk gallery of every interaction pattern SuperBot could use.

## 2. The idea in one paragraph

One admin-gated command (`!uxlab`) opens a hub that exhibits **every Discord interaction
and layout pattern available to the pinned library** — button styles and confirm flows,
all five select types, modals (including the new Label-wrapped selects-in-modals),
embed card archetypes, Components V2 layouts (containers / sections / media galleries),
PIL-generated image cards, and **clickable mockups of approved-but-unbuilt features**
(automod, logging, welcome, events — the Q-0108–Q-0112 lane). Every exhibit reacts
visibly when clicked, states which real feature it could serve, and carries registry
metadata (`pattern_id`, status, limits, anti-patterns) so the best patterns graduate
into an official **pattern library** future cogs reuse instead of inventing one-off
panels. A built-in **probe bench** re-verifies Discord's platform limits against the
live library on demand. Nothing in the lab ever writes to the database or mutates guild
state — enforced by an AST fence test, not by promise.

## 3. Why this is durable value, not a toy

1. **It converts UX decisions from prose to perception.** The owner's open decisions
   (welcome embed vs PIL card — Q-0110 phase 2; logging channel routing — Q-0109;
   the 4-button Help Home — V-03/Q-0078) become *clickable A/B choices* instead of
   paragraph descriptions. The mock studio renders the approved safety/community lane
   before a line of it is built, so the family plan (decade slot 8) gets reviewed by
   clicking, not imagining.
2. **It gives agents a shared design vocabulary.** "Use `danger_confirm_then_result`"
   replaces re-describing a confirmation flow in every plan. The hub-ui-standard's five
   presets get concrete, named, rendered instances. Future cogs stop inventing
   inconsistent panels — the exact drift class the hub-ui-standard documents.
3. **It keeps platform truth verifiable.** `docs/operations/discord-platform-limits.md`
   warns its numbers change without notice — and indeed this design session found its
   Components V2 budget wrong (25 → actually 40; corrected same PR). The probe bench
   turns "re-verify before shipping" from a doc instruction into a button press whose
   output is dated and library-versioned.
4. **It is the Components V2 evidence generator.** discord.py 2.7.1 (pinned) fully
   supports LayoutView/Container/Section/TextDisplay/MediaGallery/File/Separator —
   verified by introspection this session. Whether SuperBot's *real* panels adopt CV2 is
   an architectural decision (new view lineage beside BaseView) that should be made by
   looking at rendered CV2 layouts and probe results — which the lab produces.

## 4. What it is NOT (scope fences from the binding docs)

- **Not a second panel/router framework** — the rejection ledger
  (`docs/planning/superbot-ideas-lab-2026-06-05.md` §6) bans that. The lab is a normal
  subsystem on the canonical `BaseView`/`HubView` lineage + `views/navigation.py`
  transitions; its CV2 wing extends `discord.ui.LayoutView` as an explicitly-commented
  experimental exemption, not a parallel base-class family.
- **Not a settings surface, not a feature** — it mutates nothing, owns no tables, emits
  no audit events. The zero-write property is the design's spine.
- **Not auto-adoption of Components V2** — the lab demos CV2; adopting it for real
  panels stays a separate ADR-shaped decision informed by the lab's evidence.
- **Not member-facing** (initially) — it's a workbench for the owner/staff and for
  design-review sessions; hidden from Help. Audience question open in Q-0116.

## 5. Verified platform facts this capture rests on (2026-06-12)

Verified by direct introspection of the **installed discord.py 2.7.1** (the pinned
runtime dep), not from memory or external docs:

- `discord.ui` exports the full CV2 set: `LayoutView`, `Container` (accent colour +
  spoiler), `Section` (≤3 `TextDisplay`s + a `Thumbnail`/`Button` accessory),
  `TextDisplay`, `MediaGallery` (≤10 items), `File`, `Separator`, `ActionRow`, plus
  `Label` for modals.
- `LayoutView` enforces **max 40 total children** and **4000 display characters**
  across all items. (The repo's platform-limits doc said CV2 had a 25-component
  budget — corrected in this session's PR; 25 is the *legacy* `View` ceiling.)
- **Modals can now contain selects**: `Label` (added 2.6) wraps a component inside a
  modal — the journal's "a Modal cannot contain a Select" rule predates the pin and was
  corrected this session. Which select types modals accept in practice is exactly the
  kind of fact the probe bench exists to pin down.
- `ButtonStyle` includes `premium` (SKU-gated — exhibit shown disabled with a note).
- Five select types: `Select` (string), `UserSelect`, `RoleSelect`, `ChannelSelect`,
  `MentionableSelect`.

## 6. Where the full design lives

The complete design — architecture, pattern-registry schema, the exhibit inventory per
wing, the probe bench, mock studio, compare mode, PR slicing (A/B/C), tests, and
acceptance criteria — is
[`../planning/ux-lab-interface-gallery-plan-2026-06-12.md`](../planning/ux-lab-interface-gallery-plan-2026-06-12.md).

## 7. Lifecycle state

- **Intake:** owner-commissioned brainstorm + design, 2026-06-12 (this file).
- **Map:** new subsystem `ux_lab`; building/interface lane; low risk (additive,
  zero-write, admin-gated); medium size (3 PRs).
- **Route:** structured plan (above) + a `docs/roadmap.md` 🖥️ Building/interface
  horizon + router **Q-0116** (scheduling + audience).
- **Outcome target:** implemented (PR A → C), then `docs/ux/pattern-library.md`
  becomes the durable export.
