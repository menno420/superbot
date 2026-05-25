"""M2 pin — the AI audit channel has exactly one owner.

The M1 ``audit_log_channel`` BindingSpec (stored in
``subsystem_bindings``) is the canonical owner. M2 must NOT add an
``audit_log_channel_id`` column to ``ai_guild_policy`` or
duplicate the binding into the typed policy tables.

Failing this test means a future change re-introduced a second
source of truth — fix the duplication before merging.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


_MIGRATION = Path(__file__).resolve().parents[3] / "disbot" / "migrations" / (
    "039_ai_policy.sql"
)


def test_ai_policy_migration_does_not_define_audit_log_channel_column():
    """Comments referencing the rule are fine; what we forbid is an
    actual ``audit_log_channel`` / ``audit_log_channel_id`` column
    declaration in the migration body."""
    text = _MIGRATION.read_text(encoding="utf-8")
    # Strip SQL comments before scanning so the explanatory header
    # ("-- audit_log_channel binding is not migrated here") does not
    # trip the column check.
    code_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.split("--", 1)[0]
        if stripped.strip():
            code_lines.append(stripped)
    code = "\n".join(code_lines).lower()
    forbidden = re.compile(
        r"\baudit_log_channel(?:_id)?\b\s+(?:bigint|text|integer|channel|int)",
    )
    assert not forbidden.search(code), (
        "ai_policy migration declares an audit_log_channel column — "
        "the M1 BindingSpec is the single owner"
    )


def test_utils_db_ai_does_not_reference_audit_log_channel():
    db_path = Path(__file__).resolve().parents[3] / "disbot" / "utils" / "db" / "ai.py"
    text = db_path.read_text(encoding="utf-8")
    # Comments mentioning the rule are fine; what we forbid is any
    # SQL column / parameter / dict key named audit_log_channel.
    forbidden = re.compile(r"audit_log_channel\s*[:=]|['\"]audit_log_channel['\"]")
    assert not forbidden.search(text), (
        "utils/db/ai.py touches an audit_log_channel column — the M1 "
        "BindingSpec is the single owner"
    )


def test_ai_subsystem_schema_keeps_binding_only():
    """The AI SubsystemSchema must keep ``audit_log_channel`` as a
    BindingSpec, never as a SettingSpec or as an extra column shim."""
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    binding_names = {b.name for b in AI_CONFIG_SCHEMA.bindings}
    setting_names = {s.name for s in AI_CONFIG_SCHEMA.settings}
    assert "audit_log_channel" in binding_names
    assert "audit_log_channel" not in setting_names
    assert "audit_log_channel_id" not in setting_names
