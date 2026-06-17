# Session — per-action moderation DMs (Q-0147 standing DM policy)

> **Status:** `complete`

## What I'm about to do (born-red declaration, Q-0133)

Scheduled dispatch, empty work order. The live ▶ Next action names **moderation-DM config** as the
next ungated startable: per-action moderation DMs on the existing `moderation_service` seam, off by
default ([moderation-dm-config-plan-2026-06-17](../planning/moderation-dm-config-plan-2026-06-17.md),
Q-0147). Bug-book OPEN entries are infra-side (BUG-0011 Hermes/Telegram, needs live repro) or already
fixed (BUG-0010), so this is the right buildable slice.

**Planned slice (one PR, `disbot`-runtime, no migration):**
Turn the moderation `dm_on_action` master switch into an owner-controlled **per-action** DM policy:
1. `MOD_DM_ACTIONS` settings key (`moderation_dm_actions`) + re-export.
2. `moderation_config`: `DEFAULT_DM_ACTIONS`, a `dm_actions` field on `ModerationPolicy`, a
   `dm_action_set` parsed/validated property, and resolution in `load_policy`.
3. `moderation_service._notify_target`: gate on master **and** per-action membership.
4. `cogs/moderation/schemas.py`: a `dm_actions` `SettingSpec` (the "clear way to configure which
   actions trigger a DM" Q-0147 requires) + relabel `dm_on_action`'s hint as the master switch.
5. Tests covering master-off, master-on+in-list, master-on+not-in-list, closed-DM fail-open, and the
   `dm_action_set` parse/reject-unknown-token path.

**Deliberate deviation from the plan (documented):** the plan defaults `dm_actions` to `"warn,timeout"`.
But today, with `dm_on_action=True`, **all four** notify-eligible actions (warn/timeout/kick/ban) DM —
two existing service tests pin that. Defaulting to `"warn,timeout"` would silently stop kick/ban DMs
for guilds that already enabled the master switch (a behaviour change for configured guilds). So the
default is **`"warn,timeout,kick,ban"`** — the master switch keeps exactly today's behaviour and the
new field lets an owner *narrow* it. `auto_delete` is intentionally **not** in the vocabulary: it is a
system action that never reaches `_notify_target`, so listing it would be dead/misleading config (the
owner's "auto-delete → DM no" is structurally guaranteed).

Off by default (master `dm_on_action=False` unchanged), fail-open, no migration, no new mutation path.

## What shipped (PR #1023)

**Runtime (additive, behaviour-preserving when the master switch is off / left at default):**
- `utils/settings_keys/moderation.py` — `MOD_DM_ACTIONS = "moderation_dm_actions"`, re-exported from
  `__init__.py` (import + `__all__`).
- `services/moderation_config.py` — `DM_NOTIFY_ACTIONS = (warn, timeout, kick, ban)`,
  `DEFAULT_DM_ACTIONS = "warn,timeout,kick,ban"`, a `dm_actions` field on `ModerationPolicy`, a
  `dm_action_set` property + module-level `parse_dm_actions` helper (split/lower/strip, keep only
  known tokens — fail-safe), resolved in `load_policy`.
- `services/moderation_service.py` — `_notify_target` gate is now
  `if not policy.dm_on_action or action not in policy.dm_action_set: return`.
- `cogs/moderation/schemas.py` — `_validate_dm_actions` (rejects unknown tokens at edit time) + the
  `dm_actions` `SettingSpec`; `dm_on_action` hint relabelled the master switch; schema v6→v7.

**Tests:** service per-action gate (in-list DMs, excluded action doesn't); config `dm_action_set`
parse/normalize/reject-unknown (parametrized) + the default-set assertion; schema spec shape +
default-parity + the version/name-set guards updated; the generic settings round-trip helpers
(`test_settings_edit/reset_round_trip`) taught about constrained-csv str specs. `check_quality --full`
green (10443), arch strict 0 errors, check_docs ✓, ledger ✓.

**Docs:** plan marked SHIPPED; `settings-customization-command-map.md` updated (the stale-doc guard
requires the new key + spec name); current-state ▶ Next action de-staled + #1023 ledger entry.

## ▶ Handoff — what's next

The moderation-DM ungated slice is **done**. The next scheduled empty fire has **no named ungated
code slice left** in the band-#1020 queue — the realistic options are: (a) own a small **plan-first**
lane (image-mod #941 and security tiers #929 are both open `needs-hermes-review` carve-outs awaiting a
*human* merge, so they're not pure-code-startable); (b) a genuinely-asked uncovered **BTD6
deterministic-floor** shape (boss tier-HP comparison, paragon-ability lookup) — the proven #1008–#1012
lane, but candidates are thin (don't invent filler); or (c) wait for the owner to greenlight a
dashboard write / manifest-PR4 slice. **myprofile PR C** (join-time onboarding) stays owner-gated on
Q-0147's DM-strangers question. No continuation issue opened (none consumed now) — this handoff in
current-state ▶ Next action is the live state.

## 💡 Session idea (Q-0089)

**A `settings-doc-sync` check that auto-fails when a new moderation/subsystem `SettingSpec` name or
`MOD_*`/`*_KEY` constant is absent from `settings-customization-command-map.md`.** This session hit
exactly that wall: adding `dm_actions` reddened two *docs* tests (`test_settings_customization_doc`)
because the command-map doc is a hand-maintained mirror of the schema. The stale-doc guard catches the
*omission* but only after a full `check_quality --full` run; a fast targeted pre-commit check (or a
`scripts/check_settings_doc_sync.py` surfaced in the Stop hook when `cogs/*/schemas.py` or
`settings_keys/*` is touched) would flag it at edit time, the way `claude_post_edit.py` already flags
formatter drift. Genuinely worth having — every new setting will keep tripping this doc, so make the
feedback loop tight. *(Captured here; a future session can promote it to `docs/ideas/` if it recurs.)*

## ⟲ Previous-session review (Q-0102)

**Previous session: #1013 (dashboard Phase E — control-API read endpoints).** Did well: tight scoping
discipline — it explicitly *settled scope mid-build* to ship slice 1 (Phase E reads) as one complete
reviewable PR and deferred R3 hardening + Phase C to follow-ups, exactly the "complete shippable
function, not the smallest slice, but don't cram" balance CLAUDE.md asks for; the born-red card's
"what I'm about to do" was unusually concrete. Could have done better: the card lists slices 2–4 as
"planned" but the "what shipped" section only covers slice 1 — a reader has to infer 2–4 became
separate PRs; a one-line "slices 2–4 → PR #s / deferred" reconciliation in the *same* card would close
that loop. **System improvement it surfaces:** the recurring friction this session and #1013 both touch
is **schema/settings changes rippling into hand-maintained mirror docs + generic parametrized tests**
(the round-trip harness, the command-map doc). That's the same root as the 💡 idea above — the project
would benefit from treating "a new SettingSpec" as a first-class event with a single checklist (key +
re-export + schema + doc + round-trip sample), enforced by one fast check, so each new setting stops
costing a CI round-trip to discover the four places it must appear.

## Doc audit (Q-0104)

`check_current_state_ledger --strict` ✓ (#1023 present), `check_docs --strict` ✓ (plan re-badged
`historical`/SHIPPED; command-map doc synced). No owner decision was made this session (Q-0147 already
decided the policy), so no router entry needed. Nothing captured only in chat that belongs in a doc.

## Bug-book

No bug-book entries changed: BUG-0011 (Hermes/Telegram crash-loop) is infra-side and needs a live
foreground repro, not buildable here; BUG-0010 is already FIXED. No new bug found this session.
