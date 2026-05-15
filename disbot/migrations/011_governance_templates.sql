-- Governance templates for multi-server governance configuration (ISSUE-034)
-- Templates store a serialized set of governance overrides that can be
-- exported from one guild and applied to another.

CREATE TABLE IF NOT EXISTS governance_templates (
    template_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_by_guild_id BIGINT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    payload     JSONB NOT NULL DEFAULT '{}'
);

-- Track which templates have been applied to which guilds
CREATE TABLE IF NOT EXISTS governance_template_applications (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guild_id    BIGINT NOT NULL,
    template_id BIGINT NOT NULL REFERENCES governance_templates(template_id) ON DELETE CASCADE,
    applied_at  TIMESTAMPTZ DEFAULT NOW(),
    applied_by  BIGINT,
    UNIQUE (guild_id, template_id)
);

CREATE INDEX IF NOT EXISTS idx_governance_templates_guild ON governance_templates (created_by_guild_id);
CREATE INDEX IF NOT EXISTS idx_template_applications_guild ON governance_template_applications (guild_id);
