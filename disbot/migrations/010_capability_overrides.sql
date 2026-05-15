-- Execution policy overrides (independent of visibility, ISSUE-008)
CREATE TABLE IF NOT EXISTS capability_execution_overrides (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    capability TEXT NOT NULL,
    scope_type TEXT NOT NULL CHECK (scope_type IN ('channel', 'category', 'guild')),
    scope_id BIGINT NOT NULL,
    allowed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (guild_id, capability, scope_type, scope_id)
);
CREATE INDEX IF NOT EXISTS idx_capability_overrides_guild ON capability_execution_overrides (guild_id);
