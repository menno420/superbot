-- Migration 069: allow actor_type='setup_delegate' in the settings + resource
-- provisioning audit CHECK constraints (P0-3 arc PR 3, Q-0098).
--
-- Q-0098 grants a server-owner-delegated, possibly NON-administrator member
-- ("setup delegate") the authority to APPLY staged setup operations. The
-- governance capability resolver authorizes such a write under a bounded
-- actor_type="setup_delegate", and the settings + resource-provisioning audit
-- rows must record that discriminator so a delegated apply is never
-- indistinguishable from an administrator write. Migrations 029 / 030 shipped
-- those CHECK constraints WITHOUT 'setup_delegate', so this migration widens
-- them.
--
-- The original CHECKs are table-level and PostgreSQL-auto-named (not
-- <table>_<column>_check), so we locate each by its definition referencing
-- actor_type and drop it dynamically, then re-add an explicitly-named widened
-- constraint. Idempotent: a re-run finds and drops the named constraint added
-- below and re-adds it. Behaviour-preserving for every existing row — the new
-- set is a strict superset of migrations 029 / 030.
--
-- A drift-guard test pins each widened set to the Python pipeline frozenset:
--   tests/unit/invariants/test_settings_mutation_audit_alignment.py
--   tests/unit/invariants/test_resource_provisioning_audit_alignment.py

DO $$
DECLARE
    con record;
BEGIN
    -- settings_mutation_audit (migration 029): drop the inline actor_type CHECK
    -- (auto-named) and re-add a named, widened version.
    FOR con IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'settings_mutation_audit'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%actor_type%'
    LOOP
        EXECUTE format(
            'ALTER TABLE settings_mutation_audit DROP CONSTRAINT %I',
            con.conname
        );
    END LOOP;
    ALTER TABLE settings_mutation_audit
        ADD CONSTRAINT settings_mutation_audit_actor_type_check
        CHECK (actor_type IN
            ('user', 'moderator', 'admin', 'system', 'backfill', 'setup_delegate'));

    -- resource_provisioning_audit (migration 030): same treatment.
    FOR con IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'resource_provisioning_audit'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%actor_type%'
    LOOP
        EXECUTE format(
            'ALTER TABLE resource_provisioning_audit DROP CONSTRAINT %I',
            con.conname
        );
    END LOOP;
    ALTER TABLE resource_provisioning_audit
        ADD CONSTRAINT resource_provisioning_audit_actor_type_check
        CHECK (actor_type IN
            ('user', 'moderator', 'admin', 'system', 'backfill', 'setup_delegate'));
END;
$$;
