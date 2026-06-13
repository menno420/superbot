# 2026-06-13 — Server event logging v1 (band slot 5, Q-0109)

> **Status:** `complete`

**PR:** #774 (`claude/hopeful-dijkstra-u2fyv2`) — opened ready at first push, merged
in-turn on CI green.
**Band:** the second Q-0107 [band queue](../docs/planning/reconciliation-pass-2026-06-12-night.md) slot 5.

## Context

Continuation prompt: "continue where the last agent ended." The previous session
merged automod v1 (#772, slot 4), so the live band-queue item was **slot 5 — server
event logging v1 (Q-0109)**. Open-PR check first (#771/#766/#704 were ledger/idea/owner
PRs — none claimed the lane).

## What shipped

Owner scope (Q-0109): log **message edits/deletions · member joins/leaves · role
grants/revocations**; owner-configurable single-vs-per-category channel; deleted-message
privacy disclosed in the wizard.

The key design call: **extend the existing `logging` subsystem, don't register a new
one.** Logging events *are* logging — folding them into the existing subsystem reused the
schema, the binding-based Routes panel, the `BindingMutationPipeline`, and the
`resolve_log_channel` route table, and **tripped none of the new-subsystem pinned-surface
cascade** the automod session paid (hub roster · help-surface-map · discoverability ·
settings `###` section). This is the whole-session win.

1. **`services/server_logging_config.py`** (new) — `EventLoggingPolicy` read model over
   `logging_*` KV settings (no migration), mirroring `automod_config`. Master switch = the
   **existing** `logging.enabled`; per-category flags (messages/members/roles) all default
   OFF. `should_log(category)` is the one gate.
2. **`services/server_logging.py`** — five `format_*_embed` builders + five fail-safe
   `log_*` handlers (gate → resolve → send, counted) + `resolve_event_channel`; four new
   routes on the shared route table (`events` + `message_log`/`member_log`/`role_log`,
   falling back to `events` — **never `mod`**). `_log_event_if_enabled` factors the
   gate+post; `ensure_log_channel` generalised to a per-kind default-name map.
3. **`cogs/logging_cog.py`** — five `@commands.Cog.listener()` methods (cheap structural
   filters → delegate) + the `!logging status` event summary. `on_member_join` coexists
   with autorole's.
4. **`cogs/logging/schemas.py`** — schema **v3**: 3 flags + `event_routing` enum
   (`allowed_values`) + 4 channel bindings + 4 resource reqs. `select_view`/`provision_view`/
   `routes_panel` route tables extended in lockstep (a consistency test pins all four).
5. **Privacy:** the `messages_enabled` hint + the wizard's logging-presets section.
6. **Root-fix:** the Routes panel hardcoded "(via mod fallback)" — now names the real
   fallback target (event routes fall back to `events`).

**Verification:** `check_quality --full` green (9238 passed) · `check_architecture
--mode strict` 0 errors · `check_docs --strict` + `check_current_state_ledger --strict`
clean · live boot on Galaxy Bot (real Postgres): `✅ Loaded cogs.logging_cog`,
`server_logging` subscribed, `Logged in`/on_ready, **0 ERROR/CRITICAL**.

## Process notes — the enforcement web for "add a setting"

Adding scalar settings/bindings to an *existing* subsystem still trips two enforced
surfaces beyond the schema itself, both caught only by the full suite (not
`check_architecture`):
- **`test_settings_keys_package_structure.py`** requires `settings_keys/__init__.py` to
  re-export **every** UPPER_CASE constant in a submodule (I initially assumed a curated
  subset — wrong; the existing partial-looking list was complete for the old key set).
- **`test_settings_customization_doc.py`** requires every `SettingSpec`/`BindingSpec`
  name **and** every `settings_keys.__all__` constant to appear in the
  `settings-customization-command-map.md` doc.
Both are good guards; just know they fire. The schema's own per-spec exact-set tests and
the route-table consistency/acyclicity tests also needed updates.

## 💡 Session idea (Q-0089)

**Event-logging digest / throttle mode** — a per-guild `logging_event_digest` option that,
above a threshold, **batches passive events into one rolling embed (or a short rate-limit
window)** instead of one embed per event. Why I believe in it: message-edit/delete logging
on a busy `#general` will *flood* the log channel and hit Discord's send rate limits — the
single biggest reason an operator turns event logging back off. v1 ships honest 1:1
delivery (correct, simple); a digest mode is what makes it survivable at scale, and it
composes cleanly with the existing fail-safe `_post_event_embed` seam (buffer + flush on a
timer rather than send-immediately). Dedup-checked `docs/ideas/` +
`server-safety-and-automod-2026-06-12.md`: not captured. **Sibling follow-up** (smaller):
extend the family plan's *shared exempt roles/channels valve* (rule #2) to the passive
layer — logging is a reactive feature and v1 is the one that doesn't yet read the exempt
shape, so a `#bot-spam` channel's deletes can't be excluded. Captured for logging v2.

## ⟲ Previous-session review (Q-0102) — the automod v1 session (#772)

**Did well:** shipped automod v1 cleanly as the twin of `cleanup` (its exact precedent),
with the family plan as the lane entry doc, and — crucially — *named* the new-subsystem
pinned-surface cascade as recurring friction and filed a concrete fix (extend
`new_subsystem.py` / add a surface-checklist test). Honest, well-scoped, well-recorded.

**Missed / could improve:** its ⟲ improvement framed the cascade as "make *creating* a
subsystem cheaper." But the higher-leverage question is **"do you need a new subsystem at
all?"** automod genuinely did (it has its own pipeline stage + identity); this session's
logging events genuinely did *not* (they extend an existing domain) — and extending paid
**zero** cascade tax. The framing "reduce the tax" can quietly push agents toward always
minting a subsystem; the cheaper move is often to extend one.

**Concrete system improvement (initiated here):** I added a one-line decision rubric to the
family plan §3 — *"before registering a new `SubsystemSchema`, ask whether the feature
extends an existing subsystem's domain; if so, extend its schema (no pinned-surface
cascade) rather than mint a new subsystem (full cascade). New subsystem only when the
feature has its own identity/pipeline/lifecycle (automod = yes; logging events = no)."*
This is the internal mirror of the automod session's own observation, pointed one level
up. (Docs guidance only — within free-rein scope; no CLAUDE.md rule change, so no router
Q-block needed.)

## Docs audit (Q-0104)

`check_current_state_ledger --strict` clean (ledger has #774; trimmed #715–#728 to the
archive to clear the soft ratchet); `check_docs --strict` clean (every spec/binding/key in
the customization map; subsystem doc + ownership + family plan reachable). No owner
decisions made this session (Q-0109 was already answered) — nothing new for the router.
