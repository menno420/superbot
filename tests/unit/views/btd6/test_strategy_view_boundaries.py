"""PR-F boundary regressions for the strategy memory views."""

from __future__ import annotations

from pathlib import Path

_STRATEGY_VIEW_DIR = (
    Path(__file__).resolve().parents[4] / "disbot" / "views" / "btd6"
)


_FORBIDDEN_DB_WRITES = (
    "insert_strategy",
    "update_strategy_state",
    "record_strategy_audit",
    "delete_strategy",
)

_FORBIDDEN_AI_TABLES = (
    "ai_channel_policy",
    "ai_category_policy",
    "ai_role_policy",
    "ai_instruction_profile",
)


def _strategy_view_files() -> list[Path]:
    return [
        p
        for p in _STRATEGY_VIEW_DIR.glob("strategy*.py")
        if p.is_file()
    ]


def test_no_strategy_view_imports_db_write_helpers():
    """Strategy views must route every write through
    ``btd6_strategy_mutation``."""
    for path in _strategy_view_files():
        src = path.read_text()
        for sym in _FORBIDDEN_DB_WRITES:
            assert sym not in src, (
                f"{path.name} must not call DB write helper {sym}; "
                "use services.btd6_strategy_mutation instead"
            )


def test_no_strategy_view_references_ai_policy_tables():
    """Strategy views are BTD6 territory; AI policy tables are
    off-limits."""
    for path in _strategy_view_files():
        src = path.read_text()
        for sym in _FORBIDDEN_AI_TABLES:
            assert sym not in src, (
                f"{path.name} must not reference AI policy table {sym}"
            )


def test_no_strategy_view_invokes_ai_approve_from_ui():
    """``ai_approve_guild`` is the system-actor approval path; it
    must not be reachable from a user-facing UI."""
    for path in _strategy_view_files():
        src = path.read_text()
        assert "ai_approve_guild" not in src, (
            f"{path.name} must not invoke ai_approve_guild from the UI"
        )
