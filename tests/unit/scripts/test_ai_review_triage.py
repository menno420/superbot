"""Tests for ``scripts/ai_review_triage.py`` — the review-log → work-list bridge.

Pins the classification (preset / fix / infra), the question dedup, and the report
shape so the triage output stays trustworthy as the backlog grows.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "ai_review_triage.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("ai_review_triage_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _entry(**kw):
    base = {
        "id": 1,
        "kind": "unknown",
        "reason_code": "grounding_failed",
        "task": "btd6.answer",
        "question": "can glue deal with a ddt",
        "answer": "",
        "correction": "",
    }
    base.update(kw)
    return base


def test_classify_correction_is_preset(mod) -> None:
    e = _entry(kind="correction", reason_code="reply", correction="no, MOAB Glue does")
    assert mod.classify(e) == mod.ACTION_PRESET


def test_classify_correction_without_text_is_not_preset(mod) -> None:
    # A bare 👎 (reaction) carries no correction text → it's still a fix candidate.
    e = _entry(kind="correction", reason_code="reaction", correction="")
    assert mod.classify(e) == mod.ACTION_FIX


def test_classify_provider_failure_is_infra(mod) -> None:
    assert mod.classify(_entry(reason_code="provider_unavailable")) == mod.ACTION_INFRA
    assert mod.classify(_entry(reason_code="errored")) == mod.ACTION_INFRA


def test_classify_grounding_gap_is_fix(mod) -> None:
    assert mod.classify(_entry(reason_code="no_route_matched")) == mod.ACTION_FIX


def test_domain_of_maps_task(mod) -> None:
    assert mod.domain_of(_entry(task="btd6.answer")) == "btd6"
    assert mod.domain_of(_entry(task="projmoon.answer")) == "projmoon"
    assert mod.domain_of(_entry(task="general.nl_answer")) == "general"
    assert mod.domain_of(_entry(task="")) == "unrouted"


def test_load_entries_accepts_wrapper_and_bare_list(mod) -> None:
    wrapped = json.dumps({"schema": "ai_review_export", "entries": [_entry()]})
    bare = json.dumps([_entry(), _entry(id=2)])
    assert len(mod.load_entries(wrapped)) == 1
    assert len(mod.load_entries(bare)) == 2


def test_load_entries_rejects_bad_shape(mod) -> None:
    with pytest.raises(ValueError):
        mod.load_entries(json.dumps(42))


def test_dedupe_collapses_same_question_keeps_ids(mod) -> None:
    entries = [
        _entry(id=1, question="Can glue deal with a DDT?"),
        _entry(id=2, question="can glue deal with a ddt"),
        _entry(id=3, question="how much cash on round 10"),
    ]
    items = mod.dedupe(entries)
    assert len(items) == 2
    # Most-repeated first: the glue question (x2) leads.
    assert items[0].count == 2
    assert sorted(items[0].ids) == [1, 2]


def test_item_action_prefers_preset_when_any_correction(mod) -> None:
    # Same question logged twice: once as an unknown, once as a correction.
    entries = [
        _entry(id=1, kind="unknown", question="q", correction=""),
        _entry(id=2, kind="correction", reason_code="reply", question="q", correction="fix"),
    ]
    items = mod.dedupe(entries)
    assert len(items) == 1
    assert items[0].action == mod.ACTION_PRESET
    assert items[0].correction == "fix"


def test_build_report_counts_and_actions(mod) -> None:
    entries = [
        _entry(id=1, reason_code="grounding_failed"),
        _entry(id=2, kind="correction", reason_code="reply", question="x", correction="y"),
        _entry(id=3, reason_code="provider_unavailable", question="z"),
    ]
    report = mod.build_report(entries)
    assert report["total_entries"] == 3
    assert report["unique_questions"] == 3
    assert report["by_action"]["fix"] == 1
    assert report["by_action"]["preset"] == 1
    assert report["by_action"]["infra"] == 1


def test_render_text_and_scaffold_are_strings(mod) -> None:
    entries = [
        _entry(id=1),
        _entry(id=2, kind="correction", reason_code="reply", question="x", correction="y"),
    ]
    report = mod.build_report(entries)
    text = mod.render_text(report)
    assert "AI review backlog triage" in text
    scaffold = mod.render_scaffold(report)
    assert "GroundingProbe(" in scaffold  # the btd6 fix stub
    assert "preset from" in scaffold  # the preset candidate stub


def test_main_reads_file_and_emits_json(mod, tmp_path, capsys) -> None:
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps({"entries": [_entry()]}),
        encoding="utf-8",
    )
    rc = mod.main([str(export), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["total_entries"] == 1


def test_main_empty_stdin_errors(mod, monkeypatch) -> None:
    import io

    monkeypatch.setattr(sys, "stdin", io.StringIO("   "))
    assert mod.main([]) == 2


def test_main_bad_json_errors(mod, tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert mod.main([str(bad)]) == 2
