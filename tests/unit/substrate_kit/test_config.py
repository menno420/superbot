"""Tests for the substrate-kit config (the two-interpreter schema)."""

from pathlib import Path

from engine.lib.config import Config, config_path, load_config, save_config


def test_defaults_have_two_interpreters():
    c = Config()
    assert c.interpreter  # defaults to the running interpreter
    assert c.interpreter_for_checks is None  # host sets this (e.g. python3.10)
    assert c.state_dir == ".substrate"
    assert len(c.project_id) == 12
    assert c.cadence["reconciliation_prs"] == 20


def test_project_id_is_unique_per_install():
    assert Config().project_id != Config().project_id


def test_from_dict_ignores_unknown_keys():
    c = Config.from_dict({"project_id": "abc", "not_a_field": 1})
    assert c.project_id == "abc"


def test_save_and_load_roundtrip(tmp_path: Path):
    original = Config(project_id="proj12345678", interpreter_for_checks="python3.10")
    save_config(tmp_path, original)
    assert config_path(tmp_path).exists()
    loaded = load_config(tmp_path)
    assert loaded.project_id == "proj12345678"
    assert loaded.interpreter_for_checks == "python3.10"


def test_load_missing_returns_defaults(tmp_path: Path):
    assert load_config(tmp_path).state_dir == ".substrate"
