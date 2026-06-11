"""The BTD6 grounding-probe dev tool stays wired to the real build path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).parents[3]
_DISBOT = _REPO / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "btd6_probe",
        _REPO / "scripts" / "btd6_probe.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_probe_returns_grounding_for_entity_question():
    module = _load_module()
    ctx = await module.probe("dart monkey")
    assert ctx.facts  # fixture grounding fired through the real build()


def test_main_prints_facts_and_summary(capsys):
    module = _load_module()
    assert module.main(["dart monkey"]) == 0
    out = capsys.readouterr().out
    assert "[btd6_tower]" in out
    assert "source_summary:" in out


def test_main_flags_zero_facts(capsys):
    module = _load_module()
    assert module.main(["hello there"]) == 0
    out = capsys.readouterr().out
    assert "ZERO grounding facts" in out


def test_route_leg_flags_general_path_miss(capsys):
    """--route makes a routing miss visible — the facts view alone showed 5
    healthy facts for a question the live pipeline never grounded
    (BUG-0002, 2026-06-11)."""
    module = _load_module()
    assert module.main(["--route", "hello there"]) == 0
    out = capsys.readouterr().out
    assert "task: general.nl_answer" in out
    assert "NOT routed to btd6.answer" in out


def test_route_leg_reports_workflow_match_and_profiles(capsys):
    module = _load_module()
    assert (
        module.main(
            ["--route", "if I have 20K by round 50, how much would I have by round 60?"],
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "task: btd6.answer" in out
    assert "round-cash workflow: MATCH" in out
    assert "starting_balance=20000.0" in out
    assert "compatible_default" in out  # default profile engages (BUG-0001r)
