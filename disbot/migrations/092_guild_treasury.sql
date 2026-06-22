-- Guild treasury — the bot's first SERVER-OWNED (collective) coin pool.
--
-- Every existing coin balance is individual (the per-(user, guild) `xp.coins`
-- column). The treasury is the collective counterpart: ONE row per guild holding
-- a shared balance that members contribute to (a coin sink) and that server
-- managers disburse from (a governance-gated grant). It is the seam between the
-- economy (where the coins come from) and governance (who may spend them).
--
-- Plain balance row — no accrual, no ticker. The audited contribute/disburse
-- policy lives in services/treasury_service.py; the per-user coin legs route
-- through services.economy_service (economy_audit_log is the money trail).
--
-- `updated_at` is the unix timestamp of the last balance change (diagnostics
-- only; the balance itself is authoritative).
CREATE TABLE IF NOT EXISTS guild_treasury (
    guild_id    BIGINT NOT NULL PRIMARY KEY,
    balance     BIGINT NOT NULL DEFAULT 0,
    updated_at  BIGINT NOT NULL DEFAULT 0
);
