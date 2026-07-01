# 2026-07-01 — Karma reaction-to-thank (completion-first deepening)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1620](https://github.com/menno420/superbot/pull/1620) — Karma reaction-to-thank.
**Branch:** `claude/funny-franklin-jqv6ne` (from origin/main #1619).
**Run type:** `routine · dispatch`

## What this run did

Empty scheduled fire → advanced the next plan slice. Recent runs have been fishing-structure heavy
(tide pool / dock / structures sub-hub / boathouse), so I **diversified** to a non-fishing
completion-first deepening. Picked the **Karma** unit's rubric-C **"React-to-thank"** box
(`units/karma.md`, punch-list #2 sub-item) — a named best-in-class gap (Carl-bot has it),
self-contained and offline-shippable.

The `karma_service.give()` docstring already listed `"reaction"` as an anticipated `source` — this
extension was designed-for, so there is **no new mutation path**: the grant flows through the same
audited seam as `!thanks`, reusing the self-give guard, per-(giver→receiver) cooldown, and per-giver
daily cap for free.

## Shipped (PR #1620)

- **`utils/settings_keys/karma.py`** (+`__init__` export) — new `KARMA_REACTION_EMOJI` scalar key.
- **`services/karma_config.py`** — `DEFAULT_REACTION_EMOJI = ""` (off) + `MAX_REACTION_EMOJI_LEN`,
  a `reaction_emoji: str` field on the frozen `KarmaPolicy`, resolved in `load_policy` via
  `resolve_value` (same single-source-of-truth-default pattern as the other three specs).
- **`cogs/karma/schemas.py`** — a 4th `SettingSpec` (`reaction_emoji`, free-text, `_validate_reaction_emoji`
  = str + length-bounded; empty allowed), gated on `karma.settings.configure`.
- **`cogs/karma_cog.py`** — an `on_raw_reaction_add` listener (starboard-style fast gate: `guild_id`
  present → reactor-not-bot pre-filter → **one** policy read → emoji match → message fetch). Grants
  through `karma_service.give(source="reaction", policy=…)` (reuses the already-loaded policy — one DB
  read, not two). Skips bot authors + self-reactions; **swallows `KarmaError`** (cooldown/cap/self/
  disabled) silently — a reaction never spams the channel.
- **Tests (+11):** `test_karma_reaction.py` (9 listener cases: grant · feature-off · disabled · emoji
  mismatch · bot-reactor-pre-filter · DM · bot-author · self-reaction · blocked-grant-swallowed) +
  2 validator cases in `test_karma_schemas.py`; the schema default-drift test extended for the new spec.
- **De-staled docs my work touched:** the Karma completion cert (`units/karma.md` — rubric C box
  ticked, A/E/punch-list updated, 3-spec → 4-spec), the karma folio (`subsystems/karma.md` — PR-3
  reaction-grant marked shipped), the settings command-map doc, the S1 sector recently-shipped, and the
  regenerated dashboard/site artifacts (`export_dashboard_data.py`).

**Safety:** default off ⇒ **byte-identical** for every existing guild (no reaction silently mints
karma). Full CI mirror green (**13,664 passed**, 48 skipped); `check_architecture --mode strict` 0
errors; artifact-freshness OK; no migration. Self-merge on green.

## Decisions made alone (owner should be aware)

- **Default OFF (empty emoji), not a preset default emoji.** Silently granting karma on a common
  reaction (👍) would surprise operators; opt-in is the safe, byte-identical choice and matches how
  Carl-bot exposes its "thank" trigger. An operator sets `!settings → Karma → reaction_emoji` to turn
  it on.
- **Silent grants (no channel confirmation message).** A per-reaction confirmation would be spammy;
  the karma card reflects the new total. Matches the "in-place, not spammy" rubric-B item and the
  starboard listener's quiet style.

## ⚑ Self-initiated

`none` — this is a completion-first deepening of an already-started unit (Karma), which the S1
posture (Q-0209) explicitly treats as in-scope/prioritized, not a new-unit promotion.

## 💡 Session idea

**A "karma role reward" tier** (deferred breadth, karma cert punch-list #2): auto-grant a configurable
role at a karma threshold (e.g. "Trusted Helper" @ 50) through the existing `RoleLifecycleService`
audited seam, fired off the `EVT_KARMA_GRANTED` event the service already emits. Worth having because
it turns karma from a vanity number into a real progression hook, and the wiring (event → threshold
check → audited role grant) reuses seams that all exist today — a clean next deepening slice once the
owner greenlights karma-roles. (Already the folio's documented PR-3 deferral, now one item lighter
after this run.)

## ⟲ Previous-session review

The recent fishing-structure runs (tide pool → dock → structures sub-hub → boathouse, #1598–#1605)
were individually clean and well-tested, and the sub-hub (#1603) was the *right* move — it kept the
fishing menu lean as the structure count grew. The honest miss across the streak is **breadth
concentration**: four consecutive dispatch runs all deepened the *same* coral-structure lane, which
is exactly the kind of local-maximum a completion-first arc with 36 units should avoid — other units
(Karma, Economy, Treasury) had untouched offline punch-lists the whole time. **System improvement
this surfaces:** the dispatch orient step would benefit from a cheap "lane-recency" signal — e.g.
`dispatch_menu.py` (or the sector "▶ Next startable" block) flagging when the last N self-merged PRs
all touched one sub-area, nudging the next empty-fire run to diversify. This run did that manually by
reading the `.sessions/` log titles; encoding it would make it automatic.

## Doc audit (Q-0104)

- `check_current_state_ledger.py --strict` → exit 0 (28 merges newer than marker #1590 = benign lag,
  the reconciliation routine's job).
- `check_docs.py --strict` → passed (536 docs; top-level 20/20; recently-shipped 20/20).
- `check_generated_artifacts_fresh.py` → OK (4 artifacts fresh after re-export).
- New settings key documented in the command-map doc; cert + folio de-staled; no owner decision to
  route to the router (defaults were implementation choices within an approved completion lane).

## 📤 Run report

- **Run type:** `routine · dispatch`
- **What shipped:** Karma react-to-thank (opt-in trigger emoji → audited grant seam) — PR #1620.
- **⚑ Owner-decisions:** `none`
- **⚑ Owner-manual-steps:** `none` (no migration; merge auto-deploys via Railway).
- **⚑ Self-initiated:** `none` (completion-first deepening of an existing unit; in-scope by Q-0209).
- **Next ▶:** Karma is now one punch-list item lighter; its remaining offline gaps are the
  audit-consistency call (#3) + cog-integration tests (#4). Other untouched offline punch-lists:
  Economy (currency-name is a broad 173-usage refactor — needs a scoped plan, not a one-shot; admin
  balance panel #3 is cleaner) · Treasury · Karma admin-adjust panel. Fishing structures are
  well-covered — diversify next.

## Continuation steps for the next agent

1. Nothing is mid-flight — this PR is a complete, self-contained slice.
2. If picking up Karma: punch-list #3 (add generic `audit.action_recorded` alongside the domain log)
   and #4 (bot-recipient + event-catalogue cog tests) are both small + offline.
3. Consider the "lane-recency diversify" tooling nudge from the review above before the next empty fire.
