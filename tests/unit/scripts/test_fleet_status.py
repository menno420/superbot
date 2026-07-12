"""Tests for the pure parser in scripts/fleet_status.py (network paths untested)."""

import importlib.util
import pathlib

_SPEC = importlib.util.spec_from_file_location(
    "fleet_status",
    pathlib.Path(__file__).resolve().parents[3] / "scripts" / "fleet_status.py",
)
fleet_status = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fleet_status)  # type: ignore[union-attr]

FIXTURE = """# some-repo · status
updated: 2026-07-12T21:44:07Z
phase: ORDER 003 closeout — merge verification, kit re-render check
health: green
kit: v1.8.0
last-shipped: #45 — auth fix
blockers: none
orders: acked=001,002,003 done=001,002,003
⚑ needs-owner: provision the six host env secrets
notes: nothing else
"""


def test_parses_conventional_header_fields():
    fields = fleet_status.parse_status_header(FIXTURE)
    assert fields["updated"] == "2026-07-12T21:44:07Z"
    assert fields["phase"].startswith("ORDER 003 closeout")
    assert fields["health"] == "green"
    assert fields["kit"] == "v1.8.0"
    assert fields["blockers"] == "none"
    assert fields["orders"].startswith("acked=001")


def test_flags_owner_ask_lines():
    assert fleet_status.parse_status_header(FIXTURE).get("owner_flag") == "⚑"
    assert "owner_flag" not in fleet_status.parse_status_header("updated: x\n")


def test_truncates_long_values_and_ignores_late_lines():
    long_phase = "phase: " + "y" * 500
    fields = fleet_status.parse_status_header(f"updated: t\n{long_phase}\n")
    assert len(fields["phase"]) <= 140
    late = "\n".join([""] * 80 + ["health: green"])
    assert "health" not in fleet_status.parse_status_header(late)


def test_markdown_heading_prefix_is_tolerated():
    fields = fleet_status.parse_status_header("## updated: 2026-07-12\n")
    assert fields["updated"] == "2026-07-12"
