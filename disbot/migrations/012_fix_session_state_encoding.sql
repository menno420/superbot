-- Migration 012: Repair double-encoded JSONB values.
--
-- Prior to the BUG-001 fix, db.set_session_state() and db.write_governance_audit()
-- manually called json.dumps() before handing values to asyncpg.  asyncpg then
-- applied the registered JSONB codec (also json.dumps), resulting in values stored as
-- JSON strings wrapping JSON objects: '"{\\"key\\":\\"val\\"}"' instead of '{"key":"val"}'.
--
-- This migration re-parses those string values into proper JSONB objects.
-- It is idempotent: rows already storing valid JSONB objects have
-- jsonb_typeof(value) != 'string' and are left completely untouched.

-- Repair runtime_session_state
UPDATE runtime_session_state
SET value = value::text::jsonb
WHERE jsonb_typeof(value) = 'string';

-- Repair governance_audit_log new_value column
UPDATE governance_audit_log
SET new_value = new_value::text::jsonb
WHERE new_value IS NOT NULL
  AND jsonb_typeof(new_value) = 'string';

-- Repair governance_audit_log old_value column
UPDATE governance_audit_log
SET old_value = old_value::text::jsonb
WHERE old_value IS NOT NULL
  AND jsonb_typeof(old_value) = 'string';
