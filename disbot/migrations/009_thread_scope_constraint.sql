-- Migration 009: Add 'thread' to subsystem_visibility scope_type constraint (ISSUE-016)
--
-- The scope resolver now walks thread → channel → category → guild, so the DB
-- must permit rows with scope_type = 'thread' to be inserted (e.g. for future
-- admin tooling or direct configuration).
--
-- cleanup_policies intentionally keeps its constraint unchanged: the cleanup
-- resolver explicitly skips thread scope (see governance/cleanup.py).

DO $$
BEGIN
    -- Drop old constraint if it exists under the original name
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'subsystem_visibility_scope_type_check'
          AND conrelid = 'subsystem_visibility'::regclass
    ) THEN
        ALTER TABLE subsystem_visibility
            DROP CONSTRAINT subsystem_visibility_scope_type_check;
    END IF;

    -- Add updated constraint that includes 'thread'
    ALTER TABLE subsystem_visibility
        ADD CONSTRAINT subsystem_visibility_scope_type_check
        CHECK (scope_type IN ('guild', 'category', 'channel', 'thread', 'role'));
END;
$$;
