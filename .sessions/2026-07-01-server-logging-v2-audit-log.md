# 2026-07-01 — Server event logging v2: Discord audit-log integration (Dyno parity)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Full CI mirror green (**13717 passed**, 48 skipped; ruff/black/isort/mypy clean; arch 0 new). PR #1624.

**Branch:** `claude/modest-knuth-5syw7s` (from `main` @ #1621).

## What I'm about to do (intentions)

The owner reported that SuperBot's server logging "catches other things than Dyno" despite
having the right settings/bindings enabled. Investigation confirmed the root cause is a
**coverage gap, not a misconfig**:

- **No Discord audit-log integration at all** — `grep on_audit_log_entry_create` returns zero
  hits. SuperBot only logs a moderation action when it was performed *through SuperBot's own
  commands* (the internal `moderation.action_taken` bus event, `moderation_service.py:226`). A
  ban/kick/timeout/channel-edit/role-change done via Discord's UI or another bot (Dyno) is
  **never logged**. `docs/server-logging.md:328` admits actor attribution "needs audit-log
  integration and is a phase-2 enhancement" — never built.
- **Only 5 gateway listeners exist** (`logging_cog.py:138-211`): message delete/edit, member
  join/leave, member role-update. No listeners for bans, channels, server-roles, voice,
  invites, emojis, server settings. Intents are already sufficient (`Intents.default()`).
- Passive listeners drop bot-authored events, and message delete/edit fire only for *cached*
  messages (old/uncached deletes → nothing logged).

Owner chose "build the full v2 (all 3 PRs)" — full parity this session.

**Plan (one branch, logical commits):**
1. **Audit-log layer** — `on_audit_log_entry_create` listener + `log_audit_entry` handler +
   `AuditLogAction`→embed map. New opt-in categories (`moderation` / `channels` / `server`) +
   repurpose `roles` to the audit-log path (actor attribution). Surface View-Audit-Log
   permission in `!logging status`.
2. **Passive completeness** — raw message delete/edit + bounded in-memory message cache;
   `voice` category (`on_voice_state_update`).
3. **Config UX + tests + docs** — SettingSpecs + panel/status for the new categories; extend
   ignore lists to audit actor/target; `server-logging.md` → v2; full test coverage.

All new behaviour behind the existing off-by-default master + per-category gating, so no guild
changes until opted in.

## What shipped

Server event logging **v2** — the Discord audit-log layer that makes SuperBot's logging match
what Dyno shows. Purely additive on top of v1; every new behaviour is off by default behind the
master + per-category gates, so no guild changes until it opts a category in.

1. **Audit-log layer** (`services/server_logging.py`) — `log_audit_entry(entry)` +
   `_AUDIT_ACTION_META` (~50 `AuditLogAction` names → category/icon/verb) + `format_audit_log_embed`
   (actor in author slot + Actor field, target, reason, compact before→after diff, `member_update`
   verb refinement, bulk-delete count). One `on_audit_log_entry_create` listener surfaces **every**
   administrative action by **anyone** (native UI / other bot / SuperBot), with the actor named.
2. **New categories** — `moderation` / `channels` / `server` (audit-log) + `voice` (passive
   `on_voice_state_update`); `roles` **repurposed** to the audit-log path so it finally names the
   actor (the phase-2 gap `docs/server-logging.md` called out). All wired through
   `server_logging_config` (policy + `load_policy`), `settings_keys/logging.py`, and
   `cogs/logging/schemas.py` (schema v5, editable via `!settings`).
3. **Routing** — the v2 categories reuse the combined `events_channel` (no new bindings);
   `resolve_event_channel` now falls back to `events` for unmapped categories (previously it silently
   dropped them in `per_category` mode — a latent bug fixed here).
4. **Message-delete completeness** — `on_raw_message_delete` catches uncached/older/post-restart
   deletes the cached `on_message_delete` path never saw (defers to it when the message *is* cached,
   so no double-log); `bot1.py` widens the message cache to `max_messages=5000`.
5. **Status health** — `!logging status` lists the new categories and shows an **Audit-log access**
   ✅/⚠️ line (the bot needs *View Audit Log* or the audit categories are silently inert — the exact
   "I enabled everything but nothing shows" trap).
6. **Tests (+27, `test_server_logging_audit_v2.py`)** — drift-guard (every mapped category real),
   gating (master/category/ignore-by-actor-or-target), uncategorised-skip, `member_role_update` role
   embed with actor, embed rendering + verb refinement, voice classification/skip, uncached-delete,
   and the three cog listeners. Updated the three v1 invariant tests for the new shape.
7. **Docs** — `server-logging.md` gains a full v2 section (categories table, routing, the View-Audit-Log
   requirement, known limits); command-map + env-vars + dashboard.json regenerated for the new keys.

**Verification:** `check_quality.py --check-only` green; `mypy disbot/` clean (878 files);
`check_architecture --mode strict` 0 new; full pytest green (see Status badge for count).

## Context delta

- **Needed but not pointed to:** the two doc/registration gates that fire when you add a
  `settings_key` — `utils/settings_keys/__init__.py` must re-export every constant
  (`test_init_re_exports_every_submodule_constant`) **and** the S0 command-map doc must name both the
  SettingSpec *and* the constant (`test_settings_customization_doc.py`, two separate tests). Nothing in
  the logging context map or `mutation-and-db.md` routes you to these; they only surface as a red full
  suite. Also: adding a line to `bot1.py` shifts line numbers in the **generated** `docs/operations/env-vars.md`
  (regenerate with `scan_env_usage.py --write-doc`) — a non-obvious coupling.
- **Pointed to but didn't need:** the `docs/subsystems/media-youtube.md` folio that the server_logging
  context map lists as "area folio — start here" is unrelated to logging (stale folio pointer for this file).
- **Discovered by hand:** `on_audit_log_entry_create` requires the bot's **View Audit Log** permission or
  the gateway event never fires (silent) — reverse-engineered from the discord.py gateway contract, not
  documented in-repo before this session. And `resolve_event_channel` returned `None` (not `events`) for a
  category missing from `_CATEGORY_TO_ROUTE`, which would have silently dropped every v2 event under
  `per_category` routing — found by reading the function, not from any doc.

## Decisions made alone (ratify if you disagree)

- **Additive, not a rewrite.** Kept v1's passive listeners intact and added v2 alongside, rather than
  unifying. Repurposed only `roles` to the audit-log path (its actor-attribution was the documented goal).
  Trade-off: a mod-deleted single message can log twice conceptually (passive content + — deliberately not —
  an audit entry; I excluded single `message_delete` from the audit map so it does **not** double).
- **v2 categories all route to the combined `events_channel`** (no per-category channels yet) to avoid a
  large binding/route/resource-spec boilerplate expansion. Per-category routing for v2 is a noted follow-up.
- **`moderation` audit category is separate from `logging.mod_channel`** (own actions vs everyone's) —
  keeps SuperBot's own actions from double-logging. Documented in `server-logging.md`.

## Flagged for maintainer (known limits)

- The audit categories are **silent without the bot's View Audit Log permission** — surfaced in
  `!logging status`, but if you tested with everything enabled and saw nothing, check that line first.
- **Single** message deletions log content (passive) but don't name the deleter; **bulk** deletes do.
- v2 categories share one `events_channel`; the setup wizard (`essential_setup.py`) still lists only the
  v1 categories — configure v2 via `!settings` / `!logging status` for now (both noted as follow-ups).
- Gateway-based ⇒ events during a restart/deploy are missed → filed the catch-up idea below.
- Couldn't watch the uploaded screen recording (no video decoder in-sandbox); the diagnosis is from the
  source + your description. `!logging status` counters confirm which branch you're hitting if it differs.

## 💡 Session idea (Q-0089)

[`audit-log-catchup-on-reconnect-2026-07-01.md`](../docs/ideas/audit-log-catchup-on-reconnect-2026-07-01.md)
— replay missed audit-log entries on reconnect so moderation/server logging is **gap-free across
restarts and deploys** (a per-guild high-water mark bounds the replay + dedups vs live delivery). The one
genuine blind spot every gateway logger has; directly strengthens what shipped this session.

## ⟲ Previous-session review (Q-0102)

Reviewed `2026-07-01-visual-comparison-cards.md`. **Did well:** it fixed at *seams* not per-card —
`image_safe` at the `CardCanvas.text()` boundary means no card can tofu again, and `avatar_disc` is one
reusable primitive; that's durable one-source-of-truth work, and it verified honestly by rendering PNGs
and reading them. **Could improve:** `fetch_avatar_png` is a per-render network call in the hot path with
no cache — a re-render (stat toggle, hub open) re-hits the CDN; it flagged this only implicitly. **System
improvement it surfaces:** visual verification is re-invented every session (render → eyeball) because
there's **no golden-image snapshot harness** — a `tests/golden/` render-and-diff fixture would make card
regressions catchable in CI instead of by manual inspection. (Left as an observation, not filed, to avoid
competing with this session's logging idea; worth a future Q-0089.)

## 🛠 Friction → guard (Q-0194)

**Friction:** adding a `settings_key` tripped **four** separate red tests only at the *full-suite* stage
(init re-export, two command-map doc tests, generated env-vars line-shift) — none surfaced by the
per-file context map or the pre-edit checks, so they cost a full 7-minute suite run to discover.
**Guard shipped (free-to-ship tier):** documented the exact checklist in the Context delta above so the
next agent adding a logging/settings key knows the four registration points up front. **Proposed
(owner-gated):** a lightweight `check_settings_key_registration.py` pre-push checker that, for every
`LOGGING_*`/`*_ENABLED`-style constant, asserts it is re-exported in `settings_keys/__init__.py` and named
in the command-map doc — turning the four scattered full-suite failures into one fast, local signal
("enforce, don't exhort"). Routed as a checker idea rather than applied inline to keep this PR focused.

