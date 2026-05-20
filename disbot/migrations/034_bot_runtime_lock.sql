-- Migration 034: bot_runtime_lock (runtime instance guard).
--
-- One row per logical bot identity (currently ``lock_name = 'discord_bot'``).
-- The row records which boot is the active holder of the runtime lock,
-- so a second replica that wins ``pg_try_advisory_lock`` collision can
-- observe and log the holder's ``boot_id`` before exiting cleanly.
--
-- Why both a Postgres advisory lock AND a row?
-- -------------------------------------------
-- ``pg_try_advisory_lock`` is the authoritative mutual-exclusion mechanism
-- (cheap, session-scoped, ignored by ``pg_dump``). The row exists purely
-- for observability + heartbeat freshness: a healthy holder bumps
-- ``heartbeat_at`` every 30 s, and a stale row (``heartbeat_at`` older
-- than the configured TTL) is reclaimable by the next boot even if the
-- previous session leaked the advisory lock (e.g. died without
-- ``pg_advisory_unlock``).
--
-- Schema
-- ------
-- lock_name     short identifier; one row per logical bot identity.
-- boot_id       UUID of the holding process.
-- acquired_at   timestamp the current holder first won the lock.
-- heartbeat_at  refreshed every 30 s by a supervised task.
--
-- Rollback
-- --------
-- ``DROP TABLE IF EXISTS bot_runtime_lock`` removes the table. The bot
-- falls back to the legacy filesystem PID file (still single-host) when
-- the table is missing.
--
-- Forward-only and idempotent.

CREATE TABLE IF NOT EXISTS bot_runtime_lock (
    lock_name     TEXT         PRIMARY KEY,
    boot_id       UUID         NOT NULL,
    acquired_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    heartbeat_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
