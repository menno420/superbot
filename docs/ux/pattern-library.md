# SuperBot UX pattern library

> **Status:** `living-ledger` — **GENERATED, NOT SOURCE OF TRUTH.**
> The registry in `disbot/utils/ux_patterns/` (populated by the
> `views/ux_lab/` wings) is canonical; regenerate with
> `python3.10 scripts/export_pattern_library.py` after changing it
> (`tests/unit/docs/test_pattern_library_doc.py` pins the sync).
> Browse everything live: `!uxlab`.

## How to use this library

- **Plans and PRs reference patterns by id** — "the apply flow uses
  `settings_multi_select_preview`" replaces re-describing a layout.
- **Adopting a pattern?** Add your view to its `adopted_by` tuple in
  the wing module and regenerate — adoption is tracked, not assumed.
- **Verdicts** (`uxlab-verdict: <id> — adopt|reject|tweak — note`)
  from the ⚖️ Compare panel are routed here by the receiving session:
  adopt → keep/extend; reject → status `rejected` (kept as a warning);
  tweak → edit the exhibit, then re-judge.
- **Don't invent a near-duplicate** of a listed pattern — extend the
  exhibit instead (the whole point is one vocabulary).

## 🔘 Buttons

### `button_style_strip` — Button style strip

🟢 stable

- **Use for:** primary = the one main action; secondary = neutral/nav; success/danger = outcome-coloured verbs; link = external URLs (no callback fires)
- **Avoid for:** more than one primary button per panel; danger style for non-destructive actions
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view; premium style needs a SKU id — bots without SKUs skip it
- **Adopted by:** — (not adopted yet)
- **Notes:** Tap any button — the ephemeral names the style you pressed.

### `button_emoji_forms` — Emoji-only vs emoji+text vs text-only

🟢 stable

- **Use for:** emoji+text for primary surfaces (clear at any width); emoji-only for dense paginators (◀ ▶) with obvious meaning
- **Avoid for:** emoji-only for non-universal verbs — screen readers announce the raw emoji name
- **Limits:** label ≤ 80 chars; 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** — (not adopted yet)
- **Notes:** Accessibility: emoji-only buttons need an obvious, universal glyph.

### `home_panel_4` — 4-button home (the V-03 Help Home shape)

🟠 experimental

- **Use for:** top-level hubs with ≤4 clear categories; the planned Help Home (Play / Server & Info / My Stuff / Manage)
- **Avoid for:** hubs whose categories exceed one row — regroup first
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** — (not adopted yet)
- **Notes:** Owner vision V-03/Q-0078. Click a category — the panel swaps in place and the breadcrumb updates (V-02 doctrine).

### `dense_action_row` — Dense operator rows (5 actions + nav)

🟢 stable

- **Use for:** operator/admin panels trading density for power (hub-ui-standard preset 3)
- **Avoid for:** member-facing hubs — keep those ≤8 visible choices
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** — (not adopted yet)
- **Notes:** Counters update in place — watch the embed, not the buttons.

### `danger_confirm_then_result` — Danger action → confirm panel → result

🟢 stable

- **Use for:** destructive admin actions (delete/purge/reset); any action that is hard to reverse
- **Avoid for:** read-only actions — confirmation there is pure friction
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** views/channels (delete flows)
- **Notes:** The doctrine pattern: the danger verb never executes on first click.

### `confirm_via_modal` — Type-to-confirm modal (highest friction)

🟢 stable · modal

- **Use for:** truly destructive, bulk, or irreversible operations (e.g. purge ALL settings)
- **Avoid for:** routine confirmations — reserve typing for the genuinely scary
- **Limits:** modal text input ≤ 4000 chars; modal opens only from an interaction
- **Adopted by:** — (not adopted yet)
- **Notes:** Type the channel name exactly; a mismatch shows the validation path.

### `wizard_next_back` — Multi-step wizard (Next / Back / Cancel / Save)

🟢 stable

- **Use for:** guided setup flows where each step is ONE decision (hub-ui-standard preset 5)
- **Avoid for:** flows with optional steps a user may want to jump between
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** — (not adopted yet)
- **Notes:** Progress header + one decision per step; Save renders the summary.

### `paginator_classic` — Paginator (◀ ▶ + page indicator + jump select)

🟢 stable

- **Use for:** any list longer than one screen; leaderboards, logs
- **Avoid for:** 3-item lists — show them outright
- **Limits:** jump select caps at 25 pages — chunk beyond that; 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** views/ux_lab/wing.py (this browser)
- **Notes:** Wrap-around paging; the jump select teleports.

### `toggle_pills` — Toggle pills (per-item on/off buttons)

🟢 stable

- **Use for:** small fixed rule/flag sets (the automod rule-card shape, Q-0108)
- **Avoid for:** more than ~8 toggles — use a multi-select instead
- **Limits:** 5 buttons per action row; 5 rows / 25 components per view
- **Adopted by:** — (not adopted yet)
- **Notes:** Style flips success/secondary; the embed mirrors the state.

### `persistent_panel` — Persistent panel (survives restarts)

🟢 stable

- **Use for:** long-lived anchors (setup launcher, staff hubs) that must keep working after a deploy
- **Avoid for:** per-user stateful panels — PersistentViews must be stateless
- **Limits:** timeout=None + static custom_ids + boot-time registration; no instance state — fetch everything from the interaction
- **Adopted by:** views/setup launcher; views/ai/panel; views/moderation
- **Notes:** Posts a REAL registered PersistentView: press → restart the bot → press again.

### `timeout_behavior` — Disable-on-timeout (BaseView lifecycle)

🟢 stable

- **Use for:** every ephemeral panel — it is BaseView's default
- **Limits:** Discord keeps components clickable forever unless disabled
- **Adopted by:** views/base.py BaseView.on_timeout (bot-wide)
- **Notes:** Spawns a 15-second panel; watch the buttons grey out when the view times out instead of silently dying.

## 📋 Selects

### `category_select_single` — Category select (navigation)

🟢 stable

- **Use for:** hubs with 9+ dynamic children (hub-ui-standard threshold); the Games-hub child picker shape
- **Avoid for:** ≤8 static choices — visible buttons beat a closed menu
- **Limits:** 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** views/games/hub.py GamesHubView
- **Notes:** Pick a category — the panel content swaps in place.

### `settings_multi_select_preview` — Multi-select → preview → apply

🟢 stable

- **Use for:** bulk settings toggles; any multi-pick that mutates state — preview before apply
- **Avoid for:** destructive bulk actions without the preview step
- **Limits:** min_values/max_values bound the pick count; 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** Pick 1–3 modules, then Preview, then Apply (all fake).

### `select_paginated_over_25` — Paginated select (lists beyond 25)

🟢 stable

- **Use for:** role/channel/item lists longer than 25 (the selector-gap fix)
- **Avoid for:** silently slicing options[:25] — items become invisible (a real latent bug class here)
- **Limits:** 25 options per page — ◀ ▶ refill the menu; 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** 60 fake items, 3 pages. The page indicator lives on the placeholder.

### `entity_selects` — Auto-populated entity selects

🟢 stable

- **Use for:** picking real users/roles/channels — Discord supplies the list, search included
- **Avoid for:** fake string lists of members — entity selects are free
- **Limits:** Discord populates + searches; one select per row; 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** Four entity types stacked. Picking only echoes — nothing mutates.

### `select_with_descriptions` — Options with descriptions, emoji + default

🟢 stable

- **Use for:** choices needing a one-line explanation each (presets, modes)
- **Avoid for:** descriptions that just repeat the label
- **Limits:** 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** One option ships pre-selected (default=True) — note the check mark.

### `filter_then_list` — Two-stage filter (hierarchy navigation)

🟢 stable

- **Use for:** category → item hierarchies (channel categories, shop sections)
- **Avoid for:** flat lists that fit one menu — don't add a stage
- **Limits:** 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** The first select narrows what the second offers.

### `select_as_verb_picker` — Target select + verb buttons (platform-manager shape)

🟢 stable

- **Use for:** platform-manager panels: pick target, then Enable/Disable/Refresh (hub-ui-standard preset 4)
- **Avoid for:** verbs the canonical pipeline doesn't expose
- **Limits:** 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** views/diagnostic/flag_manager.py FlagManagerView
- **Notes:** Pick a fake flag, then a verb — the result card names both.

### `search_via_modal` — Search box for a select (modal-fed filter)

🟠 experimental · modal

- **Use for:** long string lists where typing beats paging (item catalogues)
- **Avoid for:** entity lists — UserSelect/RoleSelect already search
- **Limits:** modal round-trip costs one click vs native search; 2–25 options per string select; option label/value/description ≤ 100 chars; 1 select per action row
- **Adopted by:** — (not adopted yet)
- **Notes:** 🔍 opens a modal; the select refills with matches.

## ⌨️ Modals

### `modal_short_long` — Short + paragraph inputs

🟢 stable · modal

- **Use for:** rename / re-describe flows; any free-text capture ≤ 2 fields
- **Avoid for:** forms over ~4 fields — split into a wizard
- **Limits:** text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** — (not adopted yet)
- **Notes:** Required short field + optional paragraph; submit echoes both.

### `modal_label_select` — Select inside a modal (Label, 2.6+)

🟠 experimental · modal

- **Use for:** pick + describe in ONE round-trip (reason select + details)
- **Avoid for:** entity picks — User/Role selects belong on views, not modals
- **Limits:** Label text ≤ 45 chars, description ≤ 100; probe P-07: verify which select types Discord accepts here; text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** — (not adopted yet)
- **Notes:** The capability the old 'modals are text-only' rule predates. If this modal renders with a working dropdown, the pin supports it.

### `modal_validation_fail` — Validation failure path

🟢 stable · modal

- **Use for:** numeric/state inputs that can be wrong
- **Avoid for:** silently clamping bad input — name the rule that failed
- **Limits:** a failed modal cannot reopen itself — the error must carry enough context to retry; text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** — (not adopted yet)
- **Notes:** Enter anything non-numeric (or >100) to see the failure shape.

### `modal_preview_save` — Modal → preview card → Save/Edit loop

🟢 stable · modal

- **Use for:** anything user-visible after saving (welcome text, home embeds)
- **Avoid for:** saving free text without showing it rendered first
- **Limits:** text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** Home-message embed builder (Q-0059 mandatory preview)
- **Notes:** Edit reopens the modal **prefilled** — drafts never retype.

### `modal_report_form` — Report / feedback form

🟢 stable · modal

- **Use for:** member reports, suggestion boxes, contact-staff
- **Avoid for:** collecting more than the handling flow actually reads
- **Limits:** text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** — (not adopted yet)
- **Notes:** Submit renders the mod-queue card a staff channel would receive.

### `modal_template_editor` — Template editor with variable preview

🟢 stable · modal

- **Use for:** custom commands (trigger → template); welcome-message templates with {user}-style variables
- **Avoid for:** free-form code-like templates without a rendered preview
- **Limits:** text input ≤ 4000 chars (paragraph) / 256 (short label); modals open only from an interaction (button/select/slash); a modal cannot open another modal from its on_submit
- **Adopted by:** — (not adopted yet)
- **Notes:** Uses {user} and {server} variables; submit shows them substituted.

## 🪧 Embed archetypes

### `info_card` — Info card

🟢 stable

- **Use for:** read-only facts with one next-step hint
- **Avoid for:** burying an action the user must take — use a panel
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** ≤3 fields, footer carries the next step.

### `success_card` — Success card

🟢 stable

- **Use for:** mutation results — say WHAT changed, not just 'done'
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Green + the object's new state.

### `warning_card` — Warning card

🟢 stable

- **Use for:** approaching limits, degraded modes
- **Avoid for:** warnings without a recommended action
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** States the limit AND the next action.

### `error_card` — Error card

🟢 stable

- **Use for:** failures — name the cause and the fix
- **Avoid for:** 'Something went wrong' with no cause
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Cause + fix, never just 'failed'.

### `audit_log_compact` — Compact audit line

🟢 stable

- **Use for:** server-logging feeds (Q-0109) — high volume, one-line scan
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** services/server_logging (shape candidate)
- **Notes:** Author line = event type; description = who/what/old→new.

### `moderation_case` — Moderation case card

🟢 stable

- **Use for:** mod actions with review context (prior cases inline)
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Everything a reviewing mod needs without clicking away.

### `user_profile` — User profile card

🟢 stable

- **Use for:** the /myprofile read-only card (plan PR A there)
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Identity top, numbers middle, flair last.

### `leaderboard_fields` — Leaderboard — field rows

🟢 stable

- **Use for:** short boards (≤10) where mentions/emoji matter
- **Avoid for:** long boards — rows wrap badly on mobile
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Compare with the code-block variant (next exhibit).

### `leaderboard_table` — Leaderboard — code-block table

🟢 stable

- **Use for:** aligned numeric boards; mobile-stable up to ~40 chars wide
- **Avoid for:** rows needing mentions/emoji — code blocks render them raw
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Monospace wins for numbers; loses mentions.

### `setup_summary` — Setup final-review summary

🟢 stable

- **Use for:** the draft-lane Final Review (numbered, nothing applied yet)
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** setup wizard Final Review (shape)
- **Notes:** Numbered staged ops + explicit 'nothing applied' line.

### `ai_answer_with_sources` — AI answer with provenance

🟢 stable

- **Use for:** every AI answer — answer, method, sources, in that order
- **Avoid for:** AI prose with no provenance block
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** The answer-with-evidence contract, as a card.

### `before_after_diff` — Before/after comparison

🟢 stable

- **Use for:** permission/setting changes — scan the delta
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** Two embeds, same field order, delta in bold.

### `embed_color_strip` — Subsystem colour strip

🟢 stable

- **Use for:** checking palette readability on light + dark themes
- **Limits:** one embed per colour — strip + spec card = 10 (the cap); title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** View this on both themes and on a phone before approving colours.

### `embed_budget_edge` — Deliberately maximal embed

🟢 stable

- **Use for:** seeing what the 25-field ceiling feels like (then paginating)
- **Avoid for:** shipping anything this dense to members
- **Limits:** title 256 · description 4096 · 25 fields · field value 1024; 10 embeds / 6000 chars total per message
- **Adopted by:** — (not adopted yet)
- **Notes:** If a panel needs this, it wants pagination.

## 🧱 Components V2 (experimental)

### `cv2_text_only` — Text-display message (no embed chrome)

🟠 experimental · CV2

- **Use for:** long-form markdown without the embed frame
- **Avoid for:** content that needs fields/columns — embeds still win there
- **Limits:** 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_section_accessory` — Sections with thumbnail / button accessory

🟠 experimental · CV2

- **Use for:** list rows with a per-row image or action
- **Limits:** ≤3 text displays per section + exactly 1 accessory; 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_container_dashboard` — Container dashboard (accent colour card)

🟠 experimental · CV2

- **Use for:** rich status cards without embeds; the 'future panel' look
- **Limits:** 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_media_gallery` — Media gallery grid

🟠 experimental · CV2

- **Use for:** image sets (welcome banners, screenshots) in one grid
- **Limits:** ≤10 items per gallery; 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_file_display` — Inline file component

🟠 experimental · CV2

- **Use for:** showing a generated text/log file inside the message body
- **Limits:** the attachment must be referenced by the component; 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_settings_page` — Settings page recreation (the SettingsHub comparison)

🟠 experimental · CV2

- **Use for:** judging whether real settings panels should adopt CV2
- **Avoid for:** adopting for real panels before the ADR decision
- **Limits:** 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

### `cv2_mobile_compact` — Dense vs compact (the phone check)

🟠 experimental · CV2

- **Use for:** checking a layout on desktop AND a phone before approving
- **Limits:** 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Render it, then open Discord on your phone — same message, different feel.

### `cv2_interactive_mix` — Interactive components inside containers

🟠 experimental · CV2

- **Use for:** verifying buttons/selects fire normally inside CV2
- **Limits:** 40 components total (nested count) per message; 4000 display characters across all text items; replaces content/embeds; polls/stickers unavailable
- **Adopted by:** — (not adopted yet)
- **Notes:** Press 📤 Render — the layout posts below (self-deletes).

## 🎨 PIL image cards

### `pil_inventory_card` — Inventory card (shipped renderer)

🟢 stable · PIL

- **Use for:** compact item-quantity grids beyond embed-field comfort
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** views/mining/main_panel.py (live since #665)
- **Notes:** 🎨 Render draws the card with sample data.

### `pil_stat_card` — Stat card (shipped renderer)

🟢 stable · PIL

- **Use for:** profile-style number walls with a custom look
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** views/mining/character_panel.py (live since #665)
- **Notes:** 🎨 Render draws the card with sample data.

### `pil_character_paperdoll` — Gear paper-doll compositor (shipped renderer)

🟢 stable · PIL

- **Use for:** equipment visualisation; sprite packs drop in by file
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** mining gear panel (live since #702)
- **Notes:** Placeholder shapes render where no sprite PNG exists — the owner pack upgrades it without code changes.

### `pil_welcome_card` — Welcome card (Q-0110 phase-2 candidate)

🟠 experimental · PIL

- **Use for:** the welcome service's phase-2 card (vs embed-only v1)
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** — (not adopted yet)
- **Notes:** Uses the no-network initials disc — the avatar-download fallback path a real implementation needs anyway.

### `pil_leaderboard_image` — Leaderboard image (candidate)

🟠 experimental · PIL

- **Use for:** a flashier monthly-winners post; NOT the live board
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** — (not adopted yet)
- **Notes:** 🎨 Render draws the card with sample data.

### `pil_event_poster` — Event poster (Q-0112 candidate)

🟠 experimental · PIL

- **Use for:** scheduled-event announcements above the RSVP buttons
- **Limits:** ~8 MiB bot attachment cap (413 above); JPEG/WebP for composites; PNG only for transparency/pixel art; PIL is CPU-bound — render inside asyncio.to_thread; alt text via the attachment description field (≤1024 chars)
- **Adopted by:** — (not adopted yet)
- **Notes:** 🎨 Render draws the card with sample data.

## 🎭 Mock studio / review patterns

### `compare_ab_verdict` — A/B compare with verdict capture

🟢 stable

- **Use for:** design reviews: two candidate layouts, one message, flip + judge
- **Limits:** verdicts are copy-paste lines, never persisted (zero-write fence)
- **Adopted by:** — (not adopted yet)
- **Notes:** The verdict modal itself dogfoods the Label+Select capability.

### `mock_automod_rules` — Automod rule panel (Q-0108)

🟠 experimental

- **Use for:** the automod v1 config surface (all 4 approved rule types)
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Toggle rules; Edit thresholds opens the numbers modal.

### `mock_logging_routing` — Logging channel routing (Q-0109)

🟠 experimental

- **Use for:** the logging v1 owner choice: one channel vs per-category
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Flip the mode — this exact toggle is the open design question, rendered.

### `mock_welcome_ab` — Welcome: embed vs PIL card (Q-0110)

🟠 experimental

- **Use for:** the v1 (embed) vs phase-2 (card) decision, side by side
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Embed shows inline; Card renders the real PIL prototype on demand.

### `mock_event_rsvp` — Event RSVP card (Q-0112)

🟠 experimental

- **Use for:** the scheduler's RSVP surface + the NL-parse preview
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** RSVP counts update live (fake). NL preview parses a canned example.

### `mock_feed_summary` — Feed notification + AI summary (Q-0041)

🟠 experimental

- **Use for:** YouTube-first feed posts; the optional AI-summary block
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Toggle the summary block on/off to feel both shapes.

### `mock_counters` — Dynamic server counters

🟠 experimental

- **Use for:** the statdock-style voice-channel counter quick-win
- **Limits:** real channel renames are rate-limited (~2/10 min); MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Simulate joins; note the rename-rate caveat a real one must respect.

### `mock_custom_command` — Custom command editor

🟠 experimental

- **Use for:** admin-created trigger → template commands
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Reuses the template-editor modal; preview renders {user}/{server}.

### `mock_security_alerts` — Security alerts — tiers 1+2 only (Q-0111)

🟠 experimental

- **Use for:** raid detection + account-age alerts (the approved tiers)
- **Limits:** MOCK — view-local state only; no service, no DB, no writes
- **Adopted by:** — (not adopted yet)
- **Notes:** Tiers 3+4 (alt detection / VPN blocking) were DECLINED — deliberately absent.

## 🔬 Limit probes

### `probe_legacy_grid_25` — P-01 · legacy 5×5 component grid

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS — 25 items is the legacy View ceiling
- **Adopted by:** — (not adopted yet)

### `probe_select_26_options` — P-02 · select with 26 options

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect FAIL — 25 options is the per-select cap
- **Adopted by:** — (not adopted yet)
- **Notes:** Reports WHICH layer rejected it (library construction vs API).

### `probe_embed_budget` — P-06 · 10 embeds near the 6000-char total

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS at ≤6000 combined; the cap is the message total, not per-embed
- **Adopted by:** — (not adopted yet)

### `probe_modal_label_select` — P-07 · Label-wrapped select inside a modal

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS on discord.py ≥2.6 — submit the modal to complete the probe
- **Adopted by:** — (not adopted yet)
- **Notes:** Manual probe: it must open AND accept a submission.

### `probe_cv2_40_children` — P-03 · LayoutView with exactly 40 children

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS — 40 is the CV2 ceiling (verified in library source)
- **Adopted by:** — (not adopted yet)

### `probe_cv2_41_children` — P-04 · LayoutView with 41 children

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect FAIL at library construction — ValueError('… exceeded (40)')
- **Adopted by:** — (not adopted yet)

### `probe_cv2_text_budget` — P-05 · CV2 display-text budget (4000 chars)

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS at 4000 combined; the probe reports which layer rejects 4001
- **Adopted by:** — (not adopted yet)

### `probe_cv2_content_exclusive` — P-09 · CV2 + content= mutual exclusion

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect FAIL — a CV2 message replaces content/embeds entirely
- **Adopted by:** — (not adopted yet)

### `probe_modal_entity_select` — P-08 · entity select (UserSelect) inside a modal

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** UNKNOWN — exactly what this probe exists to pin down
- **Adopted by:** — (not adopted yet)
- **Notes:** Manual probe: open it; rejection at construction/open is the answer.

### `probe_attachment_alt_text` — P-10 · attachment alt-text round-trip

🟢 stable

- **Use for:** re-verifying the platform-limits doc on demand
- **Limits:** expect PASS — description field ≤1024 chars survives upload
- **Adopted by:** — (not adopted yet)
