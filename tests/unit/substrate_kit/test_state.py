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


def test_transaction_is_reentrant_single_flush(tmp_path):
    # Q-0223 tail ①: a helper's inner transaction inside a caller's outer one
    # must not flush mid-way — only the outermost exit writes the file.
    path = tmp_path / "state.json"
    backend = JsonStateBackend(path)
    backend.set("a", 0)
    with backend.transaction():
        backend.set("a", 1)
        with backend.transaction():
            backend.set("b", 2)
        # inner exited — disk must still hold the pre-transaction document
        assert json.loads(path.read_text(encoding="utf-8"))["a"] == 0
        assert "b" not in json.loads(path.read_text(encoding="utf-8"))
    reread = JsonStateBackend(path)
    assert reread.get("a") == 1
    assert reread.get("b") == 2


def test_nested_transaction_inner_error_rolls_back_inner_only(tmp_path):
    path = tmp_path / "state.json"
    backend = JsonStateBackend(path)
    with backend.transaction():
        backend.set("outer", 1)
        with pytest.raises(RuntimeError):  # noqa: PT012, SIM117
            with backend.transaction():
                backend.set("inner", 2)
                raise RuntimeError("boom")
        assert backend.get("inner") is None  # inner leg rolled back
        assert backend.get("outer") == 1  # outer leg survives
    reread = JsonStateBackend(path)
    assert reread.get("outer") == 1
    assert reread.get("inner") is None


def test_nested_transaction_outer_error_rolls_back_everything(tmp_path):
    path = tmp_path / "state.json"
    backend = JsonStateBackend(path)
    backend.set("a", 1)
    with pytest.raises(RuntimeError):  # noqa: PT012, SIM117
        with backend.transaction():
            with backend.transaction():
                backend.set("a", 999)
            raise RuntimeError("boom")
    assert backend.get("a") == 1
    assert JsonStateBackend(path).get("a") == 1
