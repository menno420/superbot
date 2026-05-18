-- Migration 021: CHECK constraints for resource_validation_cache.
--
-- Migration 020 created the table with TEXT columns for ``kind`` and
-- ``status`` so the application's enum values land as strings.  This
-- migration adds DB-level CHECK constraints so type-confusion writes
-- (a typo, a future enum drift) fail at the database boundary
-- instead of producing a corrupt cache row the platform later treats
-- as "unknown".
--
-- Forward-only and idempotent: the ``IF NOT EXISTS``-style guard
-- around each ALTER tolerates re-application on databases where the
-- constraint already exists (e.g. a re-run after a migration replay).
--
-- The constraint values match the Python enums:
--   ``core.resources.types.ResourceKind``    — channel, role, category, thread
--   ``core.resources.status.ResourceStatus`` — bound, unresolved, missing, invalid
-- The Phase 2a-hardening invariant test
-- ``tests/unit/invariants/test_resource_kind_alignment.py`` guards
-- the Python-side enums from drift.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   information_schema.table_constraints
        WHERE  constraint_name = 'resource_validation_cache_kind_check'
        AND    table_name      = 'resource_validation_cache'
    ) THEN
        ALTER TABLE resource_validation_cache
            ADD CONSTRAINT resource_validation_cache_kind_check
            CHECK (kind IN ('channel', 'role', 'category', 'thread'));
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM   information_schema.table_constraints
        WHERE  constraint_name = 'resource_validation_cache_status_check'
        AND    table_name      = 'resource_validation_cache'
    ) THEN
        ALTER TABLE resource_validation_cache
            ADD CONSTRAINT resource_validation_cache_status_check
            CHECK (status IN ('bound', 'unresolved', 'missing', 'invalid'));
    END IF;
END$$;
