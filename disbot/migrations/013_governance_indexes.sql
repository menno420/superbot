-- Migration 013: Governance audit and panel anchor index improvements.
--
-- Adds query-pattern indexes for future admin dashboards and audit tools:
--   "what did actor X change?"  → idx_governance_audit_actor
--   "what changed for subsystem Y?" → idx_governance_audit_subsystem
--   "fetch active anchors for guild" → idx_panel_anchors_guild

CREATE INDEX IF NOT EXISTS idx_governance_audit_actor
    ON governance_audit_log (guild_id, actor_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_governance_audit_subsystem
    ON governance_audit_log (guild_id, subsystem, occurred_at DESC)
    WHERE subsystem IS NOT NULL;

-- Supports db.get_user_subsystem_anchors() which filters by guild_id + subsystem
-- in addition to the existing UNIQUE(user_id, channel_id, subsystem) index.
CREATE INDEX IF NOT EXISTS idx_panel_anchors_guild
    ON panel_anchors (guild_id, subsystem)
    WHERE NOT is_stale;
