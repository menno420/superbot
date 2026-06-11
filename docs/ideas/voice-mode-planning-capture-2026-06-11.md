# Voice-mode planning capture — 2026-06-11

> **Status:** `ideas` — capture only, not an implementation plan or approval.
>
> **Source:** maintainer voice-mode brainstorm with ChatGPT while testing whether casual spoken planning can produce useful SuperBot ideas.
>
> **Purpose:** preserve the useful ideas from the session, classify them by likely owner/risk/horizon, and make them groomable through the normal `docs/ideas` lifecycle. Source code, binding architecture docs, `docs/current-state.md`, accepted plans, and maintainer decisions win over this capture.

---

## 1. Session outcome

The session produced a broad set of product and UX ideas. The strongest recurring direction was:

> Make SuperBot feel more unified, easier to navigate, and more alive, while preserving modular subsystem ownership.

Most ideas fall into three groups:

1. **Immediate UX cleanup candidates** — small improvements that make existing systems easier to use.
2. **Subsystem expansion ideas** — larger improvements to mining, chopping, setup, help, AI settings, and games.
3. **Long-term RPG/world/AI vision** — future-facing ideas that should stay modular and capture-only until a dedicated planning pass.

This capture should not interrupt active implementation lanes unless one of these ideas exposes a blocker, safety issue, architectural conflict, or owner-priority change.

---

## 2. Setup and settings improvements

### 2.1 Smarter setup wizard

**Idea:** Improve the setup wizard so it asks fewer questions and handles more technical details automatically.

**Desired direction:**

- Guided wizard, not fully silent automation.
- Minimal input from the server owner.
- Smart defaults.
- Optional AI-based recommendations.
- Clearer explanation of what each setup choice does.

**Likely owner:** setup / settings / binding / resource-provisioning platform.

**State:** `captured` → needs repo verification before planning.

**Architecture notes:**

- Reuse the existing setup, settings, binding, and provisioning pipelines.
- Do not create a separate AI setup system that bypasses existing mutation ownership.
- AI should advise or prefill where useful, but deterministic services should still own writes.

**Suggested next step:** audit the current setup wizard surface and identify which steps still require too much owner input or have weak explanations.

### 2.2 Centralized settings navigation

**Idea:** Settings feel fragmented across cogs and panels. Users should be able to reach everything from a clearer central place.

**Desired direction:**

- Keep subsystem-specific ownership.
- Use a central settings hub as the routing surface.
- Each subsystem should ideally have one consolidated settings panel.
- Avoid scattering one feature's settings across multiple unrelated menus.

**Likely owner:** settings hub + subsystem panels.

**State:** `captured`.

**Architecture notes:**

- This should be a hub-first routing improvement, not a new settings backend.
- Each subsystem remains responsible for its own settings specs, validation, and writes.
- The central hub should make discovery easier without taking ownership away from subsystem services.

**Suggested next step:** inventory all settings entry points and identify panels where related options are split across multiple routes.

### 2.3 AI settings clarity

**Idea:** AI settings need clearer guidance and more current explanations.

**Desired direction:**

- Better labels.
- Short explanations for each option.
- Current available modes, providers, tools, and workflow profiles explained in plain language.
- Optional recommended setup helper, such as "what should I use?" or "recommended defaults".

**Likely owner:** AI settings panel / AI config surface.

**State:** `captured`.

**Architecture notes:**

- This strongly overlaps with the existing AI panel rework idea.
- Prefer folding this into that effort instead of creating a second AI settings cleanup plan.
- Any AI recommendations should remain read-only/advisory until the user confirms a settings mutation.

---

## 3. Help and command UX

### 3.1 Modernized help menu

**Idea:** Improve the help menu with a more dynamic, interactive dropdown-based structure.

**Desired direction:**

- Layered dropdowns.
- Category dropdown plus sub-option dropdown where useful.
- Text guidance above or below dropdowns.
- Faster navigation.
- More customizable help experience.

**Likely owner:** Help system / help projection / hub UI.

**State:** `captured` → needs repo verification before planning.

**Architecture notes:**

- Reuse the existing Help projection and route resolver.
- Do not create a second Help resolver or a parallel command catalogue.
- Keep customization display-only unless routed through the existing Help overlay/settings seams.

### 3.2 Poll command modernization

**Idea:** The poll command feels outdated or clunky.

**Potential improvements:**

- Interactive poll creation menu.
- Cleaner command flow.
- Better voting UI.
- Templates for common poll types.
- More consistent panel behavior.

**Likely owner:** poll cog / poll views.

**State:** `captured` → needs repo verification.

**Suggested next step:** inspect whether the poll command uses older command-only UX or older view patterns, then decide whether it is a small UI polish or a dedicated poll-panel modernization.

### 3.3 Inventory and gear display consistency

**Idea:** Inventory and gear displays behave inconsistently.

**Desired direction:**

- Pick one clear user-facing pattern.
- Apply it consistently across inventory, gear, crafting, and equipment flows.
- Reduce confusion caused by mixed ephemeral/persistent behavior.

**Likely owner:** mining / gear / inventory views.

**State:** `captured`.

**Architecture notes:**

- Prefer a shared display/composition helper for inventory-like panels if it prevents duplication.
- Keep state mutations in existing workflow/services.
- UI should orchestrate existing read models instead of recalculating inventory/gear state.

---

## 4. Mining, crafting, chopping, and progression

### 4.1 Crafting category filters

**Idea:** Crafting should support category-based filters.

**Potential categories:**

- Tools
- Weapons
- Armor
- Materials
- Upgrades
- Consumables
- Special items

**Value:** Makes crafting easier to browse as the item catalogue grows.

**Likely owner:** mining crafting UI / recipe browser.

**State:** `captured`.

**Architecture notes:**

- Decide whether recipe categories are explicit metadata, item-type derived, or a small curated catalogue.
- Avoid hard-coding category rules in views if the recipe catalogue can own them.
- Preserve fuzzy recipe search as a complementary path.

### 4.2 Craft-and-equip shortcut

**Idea:** After crafting something, users should be able to equip it directly.

**Potential UX:**

- `Craft and equip` button where eligible.
- `Equip now` button after successful crafting.
- Warning if the item breaks a set bonus or replaces stronger gear.

**Likely owner:** mining workflow / gear picker.

**State:** `captured`; likely near-term quick-win candidate after repo verification.

**Architecture notes:**

- Crafting should still go through the existing crafting workflow.
- Equipping should still go through the gear/equipment service.
- The button should orchestrate existing flows, not duplicate crafting or equip logic inside a view.

### 4.3 Deeper mining progression

**Idea:** Expand mining beyond the current depth/progression cap.

**Desired direction:**

- More depth.
- More tiers.
- More rare materials.
- Scaling difficulty and rewards.
- Longer-term progression goals.

**Likely owner:** mining progression / economy balance.

**State:** `captured` → long-term.

**Risks:**

- Economy inflation.
- Progression becoming too slow or too grindy.
- Item catalogue growth creating UI complexity.
- Balance changes requiring simulation numbers before implementation.

### 4.4 Chopping expansion

**Idea:** Chopping should grow into a richer progression path, similar to mining.

**Possible additions:**

- Better axes.
- Rare wood types.
- Tool progression.
- Clearer chopping feedback.
- Unique materials used in crafting.
- Optional skill-based or event-based mechanics.

**Likely owner:** chopping / gathering subsystem, or games/mining if currently combined.

**State:** `captured` → needs repo verification.

**Production-readiness minimum:**

- Progression system.
- Better tools.
- Meaningful rewards.
- Clear feedback loop.

**Architecture notes:**

- Mirror mining only where the abstraction fits; do not blindly duplicate mining under another name.
- Shared gathering concepts may justify a small domain abstraction later, but only after source verification.

---

## 5. RPG, world, exploration, and AI story systems

### 5.1 World panel as a subsystem hub

**Idea:** A world panel could act as a central exploration layer that connects systems like mining, fishing, chopping, expeditions, pets, and RPG encounters.

**Desired direction:**

- One `World` interface.
- Subsystems remain modular.
- World panel routes to activities instead of owning all logic.
- Could eventually support areas, biomes, regions, maps, or activity zones.

**Likely owner:** new world/exploration hub, with existing systems as child activities.

**State:** `captured` → long-term product direction.

**Architecture notes:**

- This should be a composition/navigation layer, not a rewrite of mining/fishing/chopping.
- Each activity should retain its own service/data ownership.
- A future world hub could become a mother-hub child if it proves valuable.

### 5.2 AI-driven NPC interactions

**Idea:** Add dynamic NPC interactions to RPG/story systems.

**Potential behavior:**

- NPCs can talk to users.
- NPCs can offer quests, hints, trades, or warnings.
- AI can vary dialogue and outcomes.
- Encounters can feel less static.

**Likely owner:** AI + RPG/story subsystem.

**State:** `captured` → long-term, needs planning later.

**Risks:**

- AI inventing permanent facts.
- Uncontrolled rewards or state changes.
- Moderation/abuse concerns.
- Cost and latency.

**Architecture notes:**

- AI should narrate and personalize.
- Deterministic game services should own rewards, state changes, eligibility, cooldowns, and persistence.
- NPCs likely need structured profiles, allowed intents, and outcome contracts.

### 5.3 Dynamic morality / deception layer for NPCs

**Idea:** NPCs should not always be obviously good or bad. Some can deceive, surprise, help unexpectedly, or have hidden motives.

**Examples:**

- A friendly NPC may trick the player.
- A suspicious NPC may actually help.
- Choices may have delayed consequences.
- AI can vary tone while deterministic game state controls real outcomes.

**Likely owner:** RPG encounter engine + AI narration.

**State:** `captured` → long-term.

**Architecture notes:**

- Use deterministic encounter state for truth, reward, and consequences.
- AI can present uncertainty, flavor, and dialogue variation.
- Deception mechanics should be bounded and explainable enough that players do not feel cheated.

### 5.4 AI-generated visuals for adventures

**Idea:** Use generated visuals to make RPG adventures and expeditions more immersive.

**Potential use cases:**

- Expedition result cards.
- Character/pet scenes.
- Region visuals.
- Boss encounters.
- Story moments.

**Likely owner:** AI/media rendering layer + RPG/world systems.

**State:** `captured` → long-term.

**Risks:**

- Cost.
- Latency.
- Moderation.
- Storage and cleanup.
- Repeatability.

**Architecture notes:**

- Start owner/admin-gated or test-guild-only if explored.
- Prefer generated images as optional presentation assets, not required gameplay state.
- Consider PIL/template rendering for deterministic cards before expensive image generation.

---

## 6. Idle, pets, and engagement systems

### 6.1 Idle/clicker subsystem

**Idea:** Add an idle or clicker-style game where users earn passive rewards and return later to collect or continue progression.

**Possible loop:**

- User starts an activity.
- Bot records timestamp and chosen activity.
- User returns and claims rewards.
- Upgrades improve future gains.

**Likely owner:** new idle subsystem or games economy extension.

**State:** `captured`.

**Architecture notes:**

- Avoid background timers per user.
- Compute passive rewards on claim from timestamps.
- Cap offline rewards to prevent runaway economy growth.
- Use deterministic reward calculations that can be tested and simulated.

### 6.2 Virtual pet companion

**Idea:** Add a pet companion system where users care for and customize a pet.

**Possible features:**

- Feeding and care.
- Leveling.
- Customization.
- Pet cards rendered with PIL.
- Pet bonuses for RPG/mining/world activities.
- Personality or mood.

**Likely owner:** pets/companions subsystem, possibly tied to profile/game XP.

**State:** `captured`; aligned with prior pets/companions direction.

**Architecture notes:**

- Reuse profile/card rendering patterns if available.
- Keep pet bonuses bounded and transparent.
- Avoid coupling pets directly to every game subsystem; use a small bonus/read-model interface if needed.

---

## 7. Social, party, and PvP features

### 7.1 More PvP-style games

**Idea:** Expand competitive game options.

**Possible directions:**

- Duels.
- Tournaments.
- Competitive challenges.
- Party minigames.
- Ranked or casual modes.

**Likely owner:** games subsystem.

**State:** `captured` → future enhancement.

**Risks:**

- Moderation and anti-abuse limits.
- Clean state handling.
- Fairness and cooldown policy.
- Restart safety.

### 7.2 Drawing-telephone party game

**Idea:** Add a drawing-telephone style game for group creativity.

**Possible implementation shape:**

- Discord bot coordinates the rounds.
- Users draw using a web-based canvas.
- Bot collects and rotates prompts/drawings.
- Results are revealed at the end.

**Likely owner:** games + possible web mini-app integration.

**State:** `captured` → higher complexity.

**Architecture notes:**

- This likely needs an external web surface.
- Do not force the drawing UI into Discord components alone.
- Treat the Discord bot as the game coordinator and reveal surface.

### 7.3 Co-op features

**Idea:** Add more cooperative gameplay so users can team up.

**Potential applications:**

- Co-op mining expeditions.
- Group bosses.
- Shared RPG quests.
- Team crafting projects.
- Guild/community objectives.

**Likely owner:** games/world systems.

**State:** `captured` → future enhancement.

**Value:** Strong engagement potential because it encourages users to interact with each other, not just the bot.

**Architecture notes:**

- Needs careful transaction boundaries for group rewards.
- Should define whether progress is per-user, per-party, per-guild, or per-event.
- Restart-safe session state is required before any long-running co-op flow.

---

## 8. Candidate routing

### 8.1 Best near-term candidates

These look most practical to move toward planning soon after source verification:

1. **Craft-and-equip shortcut**
   - Small, user-visible, likely high value.
   - Should reuse existing crafting/equipment flows.

2. **Crafting category filters**
   - Clear UX win.
   - Scales with the growing mining/gear item catalogue.

3. **AI settings clarity**
   - Directly tied to the existing AI panel rework idea.
   - Valuable before deeper AI expansion.

4. **Inventory/gear display consistency**
   - Reduces confusion.
   - Helps polish the new gear system.

5. **Help menu dropdown modernization**
   - Strong UX idea.
   - Must be checked against the existing help projection system first.

### 8.2 Best medium-term candidates

1. **Smarter setup wizard**
   - High platform value.
   - Needs careful integration with setup/settings/binding/provisioning.

2. **Chopping expansion**
   - Natural extension of mining-style progression.
   - Needs balance and data structure decisions.

3. **Poll command modernization**
   - Useful if current poll surface is old or inconsistent.
   - Probably isolated enough for a focused improvement.

4. **World panel as exploration hub**
   - Strong product direction.
   - Should start as a composition/navigation layer, not a full world engine.

### 8.3 Long-term candidates

Keep these as product/backlog ideas until underlying platform pieces are ready:

1. AI-driven NPC interactions.
2. Dynamic morality/deception NPC layer.
3. AI-generated adventure visuals.
4. Idle/clicker progression.
5. Virtual pet companion.
6. Drawing-telephone party game.
7. Co-op RPG/world systems.

---

## 9. Suggested next actions

### Move to planning soon

Create or update planning docs for:

- **Mining UX polish**
  - crafting filters;
  - craft-and-equip;
  - inventory/gear display consistency.

- **AI panel/settings rework**
  - clearer explanations;
  - centralized AI settings;
  - in-place navigation.

### Keep as captured ideas

Keep these under `docs/ideas/` or the relevant idea backlog:

- World panel.
- AI NPC interactions.
- Dynamic NPC morality/deception.
- AI-generated RPG visuals.
- Idle/clicker game.
- Drawing-telephone party game.
- Co-op systems.

### Needs repo verification before deciding

- Poll command modernization.
- Setup wizard improvements.
- Chopping expansion.
- Help menu dropdown modernization.

These depend on the current implementation details and may already overlap with shipped or planned work.

---

## 10. Suggested next voice-session format

For the next voice-mode planning test:

```text
1. Pick one area:
   AI / mining / help / setup / games / world

2. Throw out rough ideas for 10-15 minutes.

3. Classify each idea:
   quick win / planning candidate / long-term / risky / duplicate.

4. End with:
   top 3 next actions
   ideas to capture
   ideas to defer
```

Best next focused session topic:

> **Mining + gear UX polish** — crafting filters, craft-and-equip, inventory/gear consistency, chopping progression, and deeper mining progression.

This area produced the most concrete actionable ideas and is likely easiest to convert into a dedicated plan after source verification.
