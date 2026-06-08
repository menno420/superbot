-- Migration 059: widen setup_draft_operations.op_kind CHECK for the role-tier
-- and role-template setup operations (server-management PR11 fix + PR13).
--
-- Two op kinds reach services.setup_operations and the setup-draft Python gate
-- but were never added to this table's defence-in-depth CHECK (migration 035):
--
--   * set_role_threshold  — staged by the PR11 roles setup section. It was
--     wired into the dispatcher (services.setup_operations) and the
--     services.setup_draft risk map, but NOT into
--     utils.db.setup_draft._KNOWN_OP_KINDS nor this CHECK — so staging a
--     time/XP auto-role tier raised ValueError at the Python gate and would
--     have hit this CHECK. This migration closes that latent gap so the
--     shipped roles section can actually persist a draft.
--   * create_managed_role — server-management PR13 role templates: create a
--     standalone operator role through RoleLifecycleService (the audited
--     manual-role owner), staged through Final Review like every other op.
--
-- The Python _KNOWN_OP_KINDS allowlist in utils.db.setup_draft remains the
-- authoritative validator; this CHECK is defence-in-depth. A drift-guard test
-- (tests/unit/db/test_setup_draft_op_kind_parity.py) now pins the dispatcher,
-- the Python gate, and this CHECK to one set so the class of gap can't recur.
--
-- Behaviour-preserving for every existing row: the new set is a strict
-- superset of migration 035's list.

DO $$
BEGIN
    -- Drop the inline CHECK from migration 035 (PostgreSQL auto-named it
    -- <table>_<column>_check) if present, then re-add the widened version.
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'setup_draft_operations_op_kind_check'
          AND conrelid = 'setup_draft_operations'::regclass
    ) THEN
        ALTER TABLE setup_draft_operations
            DROP CONSTRAINT setup_draft_operations_op_kind_check;
    END IF;

    ALTER TABLE setup_draft_operations
        ADD CONSTRAINT setup_draft_operations_op_kind_check
        CHECK (op_kind IN (
            'bind_channel', 'bind_role', 'bind_category', 'bind_thread',
            'bind_member', 'clear_binding', 'set_setting',
            'create_channel', 'create_role', 'create_category',
            'add_automation_rule', 'enable_automation_rule',
            'disable_automation_rule',
            'set_cleanup_policy', 'set_cog_routing',
            'set_role_threshold', 'create_managed_role'
        ));
END;
$$;
