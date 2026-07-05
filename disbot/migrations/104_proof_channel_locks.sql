-- Migration 104: proof-channel timed-lock persistence (`proof_channel_locks`).
--
-- A timed prize lock (`!timedprize` / the Timed Prize modal) grants a winner
-- exclusive access to the proof channel and schedules an auto-unlock after N
-- minutes. Before this table the unlock deadline lived ONLY in an in-memory
-- `asyncio.sleep` task, so a process restart (or cog reload) lost the timer
-- while the winner's Discord permission overwrite persisted — the channel
-- stayed locked to that winner indefinitely (Stage-2 walk bug #8).
--
-- This table persists the deadline so a boot-time reconcile sweep can unlock
-- any channel whose deadline already passed and reschedule the ones still
-- pending. The PLAIN `+prize` lock is intentionally indefinite and is NOT
-- persisted here — only timed locks write a row.
--
-- The write boundary is cogs/proof_channel_cog.py (rows are written when a
-- timed lock is set and deleted when the channel is unlocked); CRUD primitives
-- live in utils/db/proof_channel_locks.py; per-guild teardown is wired in
-- guild_lifecycle.py::_teardown_proof_channel_locks. One active timed lock per
-- channel (PK guild_id, channel_id) — a re-lock UPSERTs. Rollback by dropping
-- the table (no readers exist outside those modules).

CREATE TABLE IF NOT EXISTS proof_channel_locks (
    guild_id   BIGINT      NOT NULL,
    channel_id BIGINT      NOT NULL,
    winner_id  BIGINT      NOT NULL,
    unlock_at  TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (guild_id, channel_id)
);

-- The boot reconcile sweep scans by deadline (expired-first).
CREATE INDEX IF NOT EXISTS idx_proof_channel_locks_unlock_at
    ON proof_channel_locks (unlock_at);
