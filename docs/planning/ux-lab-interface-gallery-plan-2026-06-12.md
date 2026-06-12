# UX Lab — design + implementation plan (the interface gallery cog)

> **Status:** `plan` — owner-commissioned design (2026-06-12). **Not yet scheduled**:
> implementation slotting + audience are open in router **Q-0116**; the decade queue
> ([reconciliation pass](reconciliation-pass-2026-06-12.md) §4) is unchanged until the
> owner steers. Cross-check every library claim against source before implementing —
> the verified-facts section below is dated and pinned to discord.py 2.7.1.
> Capture/origin: [`../ideas/ux-lab-interface-gallery-2026-06-12.md`](../ideas/ux-lab-interface-gallery-2026-06-12.md).

---

## 0. Mission

One admin-gated panel (`!uxlab`) that makes every Discord UX pattern SuperBot could use
**visible, clickable, and comparable** — so the owner picks layouts by looking at them,
agents reuse named patterns instead of inventing panels, and platform limits stay
verifiable against the live library. Three product roles in one cog:

| Role | What it does | Who it serves |
|---|---|---|
| **Gallery** | Browse every interaction/layout pattern, each with a visible fake reaction + a spec card | The owner's compare-and-choose loop; agents needing a shared vocabulary |
| **Probe bench** | Press-a-button re-verification of platform limits against the installed library | The platform-limits doc; any session about to lean on a cap |
| **Mock studio** | Clickable mockups of approved-but-unbuilt features (Q-0108–Q-0112 lane) | Design review of the safety/community family plan before it is built |

**The spine property: the lab never mutates anything.** No DB reads/writes, no guild
mutations, no audit events, no settings. All "state" is in-memory view state; all output
is messages in the invoking channel. Enforced by an AST fence test (§7), not by promise.

---

## 1. Verified platform facts (pinned 2026-06-12, discord.py 2.7.1)

Everything below was verified by **introspecting the installed library** this session.
The probe bench (§6) exists to re-verify these on demand — when a probe disagrees with
this table, trust the probe, fix the table (and `docs/operations/discord-platform-limits.md`).

| Fact | Value | Source |
|---|---|---|
| Legacy `View` component ceiling | 25 items (5 action rows × 5) | platform-limits doc §1 |
| **Components V2 (`LayoutView`) child ceiling** | **40 total (nested count)** | `LayoutView` raises `ValueError('maximum number of children exceeded (40)')` |
| **CV2 text budget** | **4000 display characters across all items** | `LayoutView` docstring + validation |
| CV2 top-level items | `ActionRow`, `Section`, `TextDisplay`, `MediaGallery`, `File`, `Separator`, `Container` | `discord.ui` exports, all `versionadded: 2.6` |
| `Section` shape | ≤3 `TextDisplay`s + 1 accessory (`Thumbnail` or `Button`) | class docstring |
| `MediaGallery` | ≤10 `MediaGalleryItem`s | class docstring |
| `Container` | nestable, `accent_colour`, `spoiler` | `__init__` signature |
| CV2 message shape | replaces `content`/`embeds`; polls/stickers unavailable; attachments must be referenced by a component | Discord docs — **probe-verify** (P-09) |
| **Modals** | `Label` (2.6+) wraps a component inside a modal — **selects in modals are now possible**; which select types work is probe P-07/P-08 | `ui.Label.__init__(text, component, description)` |
| Button styles | `primary`, `secondary`, `success`, `danger`, `link`, `premium` (SKU-gated) | `discord.ButtonStyle` |
| Select types | `Select` (string, 2–25 options), `UserSelect`, `RoleSelect`, `ChannelSelect`, `MentionableSelect` | `discord.ui` exports |
| Embeds | 10/message; 6000 chars combined; field/footer/title caps | platform-limits doc §2 |
| Bot attachments | ~8 MiB cap; alt text via attachment `description` | platform-limits doc §3 |

**Two stale-doc corrections shipped with this design** (found while verifying):
`discord-platform-limits.md` §1 claimed CV2 has a 25-component budget (it is 40, with a
4000-char text budget); the session journal claimed modals cannot contain selects
(true pre-2.6, false on the 2.7 pin).

---

## 2. Architecture (binding-rule compliant)

```text
disbot/cogs/ux_lab_cog.py            # thin: !uxlab command + hub creation, nothing else
disbot/views/ux_lab/
  __init__.py
  home.py        # UxLabHomeView(HubView) — category nav, edit-in-place transitions
  buttons.py     # wing 1: button styles, layouts, confirm flows, wizards
  selects.py     # wing 2: all 5 select types, multi-select, paginated >25 pattern
  modals.py      # wing 3: text inputs, Label-wrapped selects, validation-fail flow
  embeds.py      # wing 4: embed card archetypes
  layout_v2.py   # wing 5: LayoutView/CV2 exhibits  ← experimental lineage, commented
  image_cards.py # wing 6: PIL exhibits (reuses existing renderers)
  mockups.py     # wing 7: approved-lane feature mockups (all marked MOCK)
  probes.py      # wing 8: the limit-verification bench
  compare.py     # wing 9: side-by-side A/B with verdict lines
disbot/utils/ux_patterns/
  __init__.py
  registry.py    # PatternSpec dataclass + REGISTRY + validation helpers
  builders.py    # pure embed/component builders shared by exhibits
```

Decisions and why:

- **No service layer.** Services exist for business logic and owned writes
  (`docs/ownership.md`); the lab has neither. A `ux_lab_service` would be ceremony.
  The cog routes; views render; `utils/ux_patterns/` holds data + pure builders.
- **`utils/ux_patterns/` is layer-legal**: utils may import stdlib + discord only
  (architecture table), and the registry/builders import exactly that. Per
  `docs/helper-policy.md`, pattern builders that future `views/` *and* potentially
  `services/`-adjacent renderers will reuse belong in `utils/` — this is the promotion
  home, not a grab-bag (each module has one owner and one purpose).
- **Canonical view lineage, no second framework** (rejection ledger §6): every wing
  view extends `HubView`/`BaseView`; navigation uses `views/navigation.py`
  (`transition_to` edit-in-place, `attach_back_button`) so the lab itself *demonstrates*
  the V-02 doctrine (breadcrumb header line, update-in-place, no dead ends).
- **The CV2 wing is the one sanctioned exception**: `LayoutView` is a sibling of
  `discord.ui.View`, so `layout_v2.py` classes cannot extend `BaseView`. They extend
  `discord.ui.LayoutView` directly with the standard "intentional divergence" comment
  (the same carve-out game-state views use) + an entry in the BaseView-conformance
  ratchet's disposition notes. **Extracting a shared `BaseLayoutView` is explicitly
  deferred** until/unless CV2 is adopted for real panels (that adoption is ADR-shaped,
  decided on the lab's evidence — not by this plan).
- **Gating:** command `@commands.has_permissions(administrator=True)`; every callback
  re-checks via `views/base.interaction_is_admin` (capability-authority panel-callback
  rule). Registered via `scripts/new_subsystem.py`, hidden from Help (workbench, not a
  member feature) — audience widening is Q-0116's call.
- **Lifecycle:** the hub is a normal `HubView` (180 s timeout — and the disable-on-
  timeout behavior is itself exhibit B-10). One exhibit (PR B) demonstrates a
  `PersistentView` through the canonical `core/runtime/persistent_views.py` registration
  so restart-survival is visible; it is registered like any other persistent view, no
  parallel mechanism.

---

## 3. The pattern registry (the durable artifact)

```python
class PatternCategory(Enum):
    BUTTONS, SELECTS, MODALS, EMBEDS, LAYOUT_V2, IMAGE, MOCKUP, PROBE

class PatternStatus(Enum):
    STABLE, EXPERIMENTAL, DEPRECATED, REJECTED

@dataclass(frozen=True)
class PatternSpec:
    pattern_id: str                  # "danger_confirm_then_result" — the shared vocabulary
    title: str                       # "Danger action → confirm → result"
    category: PatternCategory
    status: PatternStatus
    uses_components_v2: bool
    requires_pil: bool
    requires_modal: bool
    recommended_for: tuple[str, ...] # "destructive admin actions", "settings apply"
    anti_patterns: tuple[str, ...]   # "never for read-only actions (adds friction)"
    limits: tuple[str, ...]          # the platform caps this pattern leans on
    adopted_by: tuple[str, ...]      # real views using it — grows as patterns graduate
    notes: str
```

- `REGISTRY: dict[str, PatternSpec]` + a renderer mapping `pattern_id → builder`.
- Every exhibit panel shows its **spec card** (an embed of the metadata) next to the
  rendered pattern — this satisfies "every demo states what real feature it could be
  used for" and "states its limits" by construction.
- The registry is the source for the eventual **`docs/ux/pattern-library.md`** export
  (PR C): the doc is generated/pinned from the registry the same way other doc-pin
  tests work, so doc and code cannot drift.
- Future plans/PRs reference patterns by id ("the settings apply flow uses
  `settings_multi_select_preview`") — and a pattern's `adopted_by` tuple records where
  it landed, giving the periodic REVIEW pass a real adoption signal.

---

## 4. Gallery inventory (the inclusive list)

Wing exhibits, each with a named `pattern_id`, a visible reaction, and a spec card.
This inventory is the design's "most versatile and inclusive" core — drawn from the
owner brainstorm, the ChatGPT draft, the hub-ui-standard audit table, the
server-management roadmap's selector gaps, and the V-02/V-03 vision doctrine.

### Wing 1 — Buttons (`buttons.py`)

| id | Exhibit | Reaction |
|---|---|---|
| B-01 `button_style_strip` | All 6 styles incl. disabled + `premium` (shown disabled, SKU note) + link button | Click → ephemeral "you pressed X" |
| B-02 `button_emoji_forms` | Emoji-only vs emoji+text vs text-only (a11y note: emoji-only needs a text fallback) | Click → swaps the form in place |
| B-03 `home_panel_4` | The V-03 4-button home shape (Play / Server & Info / My Stuff / Manage) | Click → fake category page, breadcrumb updates |
| B-04 `dense_action_row` | 5-button dense row + a second nav row (operator-hub density) | Counters update in place |
| B-05 `danger_confirm_then_result` | Danger → confirm panel (the doctrine pattern) | Confirm → fake "done" result card; Cancel → back |
| B-06 `confirm_via_modal` | Danger → type-to-confirm modal (for truly destructive ops) | Match → fake result; mismatch → validation error |
| B-07 `wizard_next_back` | Multi-step wizard: Next/Back/Cancel/Save with progress header | Steps swap in place; Save → summary embed |
| B-08 `paginator_classic` | ◀ ▶ page buttons + page indicator + jump-to select | Pages swap in place |
| B-09 `toggle_pills` | A row of on/off toggle buttons re-rendering state (the automod-rule shape) | Style flips success/secondary |
| B-10 `timeout_behavior` | Short-timeout view demonstrating disable-on-timeout | Wait 15 s → buttons grey out |

### Wing 2 — Selects (`selects.py`)

| id | Exhibit | Reaction |
|---|---|---|
| S-01 `category_select_single` | String select as navigation (GamesHub shape) | Pick → fake child page |
| S-02 `settings_multi_select_preview` | Multi-select (min/max) → **Preview selected → Apply** confirmation | Preview embed lists picks; Apply → fake success |
| S-03 `select_paginated_over_25` | **The >25 pattern**: category select → paginated select (◀ ▶ re-fills options) | Solves the server-mgmt 25-truncation gap |
| S-04 `entity_selects` | `UserSelect` / `RoleSelect` / `ChannelSelect` / `MentionableSelect`, one per page | Pick → echoes the resolved entity, no mutation |
| S-05 `select_with_descriptions` | Option descriptions + emojis + a default-selected option | Pick → spec card highlights caps (100-char) |
| S-06 `filter_then_list` | Two-stage filter: select narrows, second select picks (hierarchy filtering) | Both swap in place |
| S-07 `select_as_verb_picker` | Platform-manager shape: target select + verb button bank | Verb → fake pipeline-result card |
| S-08 `search_via_modal` | Button → modal text input → select re-filled with "matches" | The search-inside-a-select emulation |

### Wing 3 — Modals (`modals.py`)

| id | Exhibit | Reaction |
|---|---|---|
| M-01 `modal_short_long` | Short + paragraph inputs, required/optional, placeholders, length caps | Submit → echo embed |
| M-02 `modal_label_select` | **`Label`-wrapped string select inside a modal** (2.6+ capability) | Submit → echo; doubles as probe evidence |
| M-03 `modal_validation_fail` | Server-side validation failure → ephemeral error → reopen hint | Shows the failure UX honestly |
| M-04 `modal_preview_save` | Modal → preview card → Save/Edit loop (the Q-0059 home-embed shape) | Edit reopens prefilled |
| M-05 `modal_report_form` | Report/feedback form (reason select + details paragraph) | Submit → fake mod-queue card |
| M-06 `modal_template_editor` | Custom-command shape: trigger + template + preview rendering `{user}` vars | Submit → rendered preview |

### Wing 4 — Embeds (`embeds.py`)

Card archetypes, each one embed with realistic sample data + a "use for / don't use
for" spec card: `info_card` · `success_card` · `warning_card` · `error_card` ·
`audit_log_compact` (the server-logging shape, Q-0109) · `moderation_case` ·
`user_profile` (the myprofile PR-A shape) · `leaderboard_table` (code-block alignment
vs field columns, both shown) · `setup_summary` (wizard final-review shape) ·
`ai_answer_with_sources` (provenance footer) · `before_after_diff` (the draft-lane
Final Review shape) · `color_strip` (one embed per standard palette colour — the
light/dark-theme readability check). Plus E-13 `embed_budget_edge`: a deliberately
maximal embed (25 fields, 6000-char total) to *see* what dense actually looks like.

### Wing 5 — Components V2 (`layout_v2.py`, all `EXPERIMENTAL`)

| id | Exhibit |
|---|---|
| V2-01 `cv2_text_only` | Pure `TextDisplay` message (markdown, no embed chrome) |
| V2-02 `cv2_section_accessory` | `Section` ×3 text + `Thumbnail`; sibling with a `Button` accessory |
| V2-03 `cv2_container_dashboard` | `Container` with accent colour: header text, separator, action row — the "rich card without embeds" |
| V2-04 `cv2_media_gallery` | `MediaGallery` with 1 / 4 / 10 items (grid behavior) |
| V2-05 `cv2_file_display` | `File` component rendering an attached text file inline |
| V2-06 `cv2_settings_page` | A settings-page recreation in CV2 (the direct comparison target for today's `SettingsHubView`) |
| V2-07 `cv2_mobile_compact` | The same content twice: dense vs compact — for a phone-vs-desktop look |
| V2-08 `cv2_interactive_mix` | Buttons + select *inside* containers/sections (interaction parity check) |

Every V2 exhibit footer states: "CV2 message — no content/embeds/polls; 40-child /
4000-char budget; adoption for real panels is a separate ADR decision."

### Wing 6 — PIL image cards (`image_cards.py`)

**Reuse first** (helper-policy): the mining inventory + stat-card renderers (#665) and
the gear paper-doll compositor (#702) already exist — the wing exhibits them with
sample data rather than re-implementing. New prototypes: `welcome_card` (avatar circle
composite — the Q-0110 phase-2 preview, shown beside the embed-only variant),
`leaderboard_image` (top-10 with avatars), `event_poster`. Every exhibit reports
render time, output bytes vs the 8 MiB cap, format choice (JPEG/WebP per the limits
doc §4), runs under `asyncio.to_thread`, and sets attachment alt text (a11y demo).

### Wing 7 — Mock studio (`mockups.py`) — the approved-lane preview

Clickable, clearly-bannered **MOCK** panels for the Q-0108–Q-0112 family, so the
family plan (decade slot 8) is reviewed on rendered UI:

- `mock_automod_rules` — 4 rule cards (spam/links/caps/mentions, the Q-0108 set) with
  toggle pills + a threshold modal; state is view-local only.
- `mock_logging_routing` — the Q-0109 open choice rendered: single-channel vs
  per-category routing, switchable live to *feel* both.
- `mock_welcome_ab` — Q-0110's exact decision: embed-only vs PIL-card welcome,
  side-by-side with the same fake member.
- `mock_event_rsvp` — Sesh-style event card with RSVP buttons + an NL-parse preview
  ("friday 8pm" → parsed time card, Q-0112 shape).
- `mock_feed_summary` — YouTube notification card with optional AI-summary block
  (Q-0041 posture).
- `mock_counters` — fake "📊 Members: 1,234" voice-channel preview card.
- `mock_custom_command` — trigger → template → rendered-preview flow.
- `mock_security_alerts` — raid alert + account-age warning cards (tiers 1+2 only,
  per Q-0111; tiers 3+4 deliberately absent — they were declined).

### Wing 8 — Probe bench (`probes.py`)

Each probe = one button: attempt a crafted send → report ✅/❌ with the exact
exception, the installed library version, and today's date (copy-paste-ready for the
limits doc). Probes: P-01 legacy 5×5 grid · P-02 26-option select (expect failure) ·
P-03 40-child LayoutView (expect pass) · P-04 41-child (expect `ValueError`) ·
P-05 4000-char CV2 text budget edge · P-06 10-embed / 6000-char message ·
P-07 modal + `Label`+string-select · P-08 modal + `Label`+entity-selects (which types
does Discord accept?) · P-09 CV2 + `content=` mutual exclusion (expect API error) ·
P-10 attachment alt-text round-trip. A `Run all` button posts a dated summary table —
the artifact that keeps `discord-platform-limits.md` honest over time.

### Wing 9 — Compare (`compare.py`)

The owner's core loop, made first-class: pick two pattern ids (or "pattern vs a live
panel archetype" — sample-data recreations of today's `SettingsHubView` /
`GamesHubView` / Help home shapes from the hub-ui-standard audit table) → the panel
renders A, a swap button flips to B in place (same data both sides) → a **Verdict**
button emits a copy-paste markdown line
(`uxlab-verdict: <pattern_id> — adopt|reject|tweak — <note>`) the owner pastes into
chat/the router. Zero persistence by design; the durable ledger is the pattern
library doc, updated by the session that receives the verdicts.

---

## 5. UX of the lab itself

- `!uxlab` → Home: a `HubView` with one row of category buttons (wings grouped:
  Core components · Layouts & media · Mockups · Bench), a wing select, and a
  breadcrumb header (`🧪 UX Lab › Buttons › Danger confirm`). All transitions are
  edit-in-place (`transition_to`); Home button everywhere; no dead ends — the lab
  obeys (and exhibits) the V-02 doctrine and the hub-ui-standard thresholds.
- Every exhibit page: rendered pattern (top) + spec card (bottom) + `Prev / Next /
  Wing home` nav, so the owner can flip through a wing like a catalogue.
- A `🔢 status` line on Home shows registry counts by category/status — the lab
  self-reports its coverage.

## 6. Slash front door

`/uxlab` as a single slash front door to the same panel (command-integration
standard: slash = front doors to panels, never one-per-sub-action). Typed `!uxlab`
stays first-class.

---

## 7. Tests (CI-verifiable without Discord)

1. **Zero-write AST fence** — `tests/unit/invariants/test_ux_lab_zero_write.py`:
   across `cogs/ux_lab_cog.py`, `views/ux_lab/`, `utils/ux_patterns/` — no
   `utils.db` / `services` / `governance` imports, no `emit_audit_action`, no
   `pool.`/`conn.` tokens. (The `test_game_wager_write_boundary` precedent, inverted:
   that fence forces writes *through* a seam; this one forbids writes entirely.)
2. **Registry integrity** — unique `pattern_id`s; every spec has a renderer and every
   renderer a spec; metadata completeness (non-empty `recommended_for`, `limits`).
3. **Construction smoke** — every legacy exhibit view instantiates with ≤25 children;
   every CV2 exhibit instantiates under the 40/4000 budget (the library raises at
   construction, so plain instantiation is the test).
4. **Spec-card render** — spec cards stay within embed caps via the existing
   `clamp_embed` path.
5. **(PR C) doc-pin** — `docs/ux/pattern-library.md` ↔ registry sync test, same
   pattern as the other doc-pin tests.

Cog-size ceiling (800 LOC) is respected by construction — the cog is thin; wings are
view modules.

---

## 8. PR slicing (3 PRs, Q-0107 "real slice" bar)

| PR | Scope | Why this cut |
|---|---|---|
| **A — foundation + core wings** | `utils/ux_patterns/` (registry + builders) · home hub · wings 1–4 (buttons/selects/modals/embeds) · probes P-01/02/06/07 · AST fence + registry/smoke tests · `scripts/new_subsystem.py` registration · slash front door | Immediately useful: the owner can browse the full legacy-component catalogue day one; the registry vocabulary exists from the first PR |
| **B — CV2 + image wings** | wing 5 (`layout_v2.py` + ratchet disposition note) · CV2 probes P-03/04/05/08/09/10 · wing 6 (PIL, reusing #665/#702 renderers + welcome-card prototype) · PersistentView exhibit · platform-limits doc updated from probe output | The experimental lane, isolated so a CV2/library surprise can't block the stable gallery |
| **C — mock studio + compare + export** | wing 7 (mockups) · wing 9 (compare + verdicts) · `docs/ux/pattern-library.md` seeded from the registry + doc-pin test · adoption guide section | The decision-making layer; ideally lands **before or with** the safety-lane family plan so Q-0108–Q-0112 UX is reviewed by clicking |

All three are additive, admin-gated, zero-write — the low-risk lane where larger PRs
are acceptable. Live verification each PR: boot the test bot (always safe), walk the
new wings, screenshot for the PR body.

## 9. Acceptance criteria

- One command opens the gallery; every exhibit reacts visibly to interaction.
- Every exhibit shows its spec card: intended real use, limits, anti-patterns, status.
- Probes report pass/fail with exact errors against the installed library, dated.
- Zero-mutation is CI-enforced (AST fence), not asserted in prose.
- Pattern ids appear in at least one subsequent plan/PR as the design vocabulary
  (the adoption signal that the lab is working).
- `docs/ux/pattern-library.md` exists (PR C) and cannot drift from the registry.

## 10. Open questions (router **Q-0116**) + explicit non-decisions

- **Scheduling:** where do PRs A–C sit relative to the decade queue? Recommendation:
  PR A as an owner-steered near-term slice; PR C before/with the family plan (slot 8)
  so the safety-lane UX review happens on rendered panels. Owner's call — the queue
  doc says steered swaps are by design.
- **Audience:** admin-gated (recommended — staff can browse) vs owner-only.
- **Non-decision (pinned):** the lab does **not** decide CV2 adoption for real
  panels. That is a future ADR, taken on the lab's rendered evidence + probe results.
  No session should cite this plan as authority to migrate live panels to LayoutView.
