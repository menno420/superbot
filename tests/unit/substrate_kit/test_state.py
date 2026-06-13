"""Tests for the state-backend interface + JSON backend (atomicity, rollback)."""

import json

import pytest
from engine.lib.state import JsonStateBackend, default_state


def test_default_state_shape():
    s = default_state("pid")
    assert s["project_id"] == "pid"
    assert s["mode"] == "guided"
    assert s["stance"] == "analysis"
    assert s["session_count"] == 0
    assert s["graduation"]["criteria"]["blocking_questions"] == 0


def test_set_get_persists_across_instances(tmp_path):
    path = tmp_path / ".substrate" / "state.json"
    JsonStateBackend(path).set("x", 1)
    assert path.exists()
    assert JsonStateBackend(path).get("x") == 1


def test_atomic_write_leaves_no_tmp(tmp_path):
    path = tmp_path / "state.json"
    JsonStateBackend(path).set("k", "v")
    assert not (tmp_path / "state.json.tmp").exists()
    assert json.loads(path.read_text(encoding="utf-8"))["k"] == "v"


def test_transaction_commits_once(tmp_path):
    path = tmp_path / "state.json"
    backend = JsonStateBackend(path)
    with backend.transaction():
        backend.set("a", 1)
        backend.set("b", 2)
    reread = JsonStateBackend(path)
    assert reread.get("a") == 1
    assert reread.get("b") == 2


def test_transaction_rolls_back_on_error(tmp_path):
    path = tmp_path / "state.json"
    backend = JsonStateBackend(path)
    backend.set("a", 1)
    with pytest.raises(RuntimeError):  # noqa: PT012, SIM117
        with backend.transaction():
            backend.set("a", 999)
            raise RuntimeError("boom")
    assert backend.get("a") == 1  # in-memory rolled back
    assert JsonStateBackend(path).get("a") == 1  # disk never saw 999


def test_query_by_prefix(tmp_path):
    backend = JsonStateBackend(tmp_path / "s.json")
    backend.set("slot_a", 1)
    backend.set("slot_b", 2)
    backend.set("other", 3)
    assert set(backend.query("slot_")) == {"slot_a", "slot_b"}


def test_migrate_sets_version(tmp_path):
    backend = JsonStateBackend(tmp_path / "s.json")
    backend.migrate(1)
    assert backend.get("version") == 1
