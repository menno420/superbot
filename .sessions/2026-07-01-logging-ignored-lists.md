# 2026-07-01 — Logging: ignored channels/users exclusion lists (completion deepening)

> **Status:** `in-progress`

**Run type:** `routine · dispatch`

## What I'm about to do

Empty work order (scheduled fire) → advance the next real S1 plan slice. Per
`docs/current-state/S1-bot.md` ▶ Next, the standing offline deepening is clearing the assessed
completion certs' punch-lists. Picking **Logging punch #1 — ignored channels / users exclusion
lists** (`[offline, deepening]`), the named best-in-class gap vs Carl-bot/Dyno
(`docs/planning/feature-completion/units/logging.md`).

**Scope:** add two per-guild scalar settings — `logging_ignored_channels` and `logging_ignored_users`
(comma-separated id CSV, default empty) — so an operator can log every category *except* in named
channels / for named users (e.g. "log all deletes except in #bot-testing"). Mirror the proven
`automod_config` exempt-list pattern exactly (`parse_id_csv` → `frozenset[int]`, tolerant read /
loud write validator). Wire the exclusion into the shared passive-event gate
(`_log_event_if_enabled`) so every category respects it; add the `event_skipped_ignored` counter;
add the two `SettingSpec`s to the logging schema (version 3→4); tests + docs.

Additive, default-off, byte-identical for every existing guild. Then flip this card to `complete`.

Also: deleted a stale claim file (`claude__ai-answer-storage-plan-3fvdit.md`) for already-merged
BTD6 track-length work (#1578) on sight (Q-0166).
