"""Tests for the Stop-hook session-close advisor (plan §5.B, Lane B7)."""

from datetime import date

from engine.hooks.stop_check import evaluate_stop
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state

COMPLETE_LOG = (
    "# 2026-07-02-test session\n"
    "> **Status:** `complete`\n"
    "💡 Session idea: one genuine idea.\n"
    "⟲ Previous-session review: looked fine.\n"
)


def _init(root, **overrides):
    config = Config()
    save_config(root, config)
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
        for key, value in overrides.items():
            backend.set(key, value)
    return config, backend


def _mined_today():
    return {"active_count": 0, "last_mined": date.today().isoformat()}


def _write_log(root, config, text=COMPLETE_LOG):
    sessions = root / config.sessions_dir
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / "2026-07-02-test.md").write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# All clean
# ---------------------------------------------------------------------------


def test_all_clean_returns_empty(tmp_path):
    config, backend = _init(tmp_path, reflection_buffer=_mined_today())
    _write_log(tmp_path, config)
    assert evaluate_stop(tmp_path, config, backend) == []


# ---------------------------------------------------------------------------
# Each advisory fires on its own
# ---------------------------------------------------------------------------


def test_missing_session_log_advises(tmp_path):
    config, backend = _init(tmp_path, reflection_buffer=_mined_today())
    lines = evaluate_stop(tmp_path, config, backend)
    assert len(lines) == 1
    assert "no session log" in lines[0]


def test_incomplete_session_log_names_missing_markers(tmp_path):
    config, backend = _init(tmp_path, reflection_buffer=_mined_today())
    _write_log(tmp_path, config, "> **Status:** `in-progress`\n")
    lines = evaluate_stop(tmp_path, config, backend)
    assert len(lines) == 1
    assert "is missing" in lines[0]
    assert "Session idea" in lines[0]
    assert "Previous-session review" in lines[0]


def test_open_blocking_questions_advise(tmp_path):
    config, backend = _init(
        tmp_path,
        reflection_buffer=_mined_today(),
        open_questions=["q-verify-command"],
    )
    _write_log(tmp_path, config)
    lines = evaluate_stop(tmp_path, config, backend)
    assert len(lines) == 1
    assert "blocking question(s) open" in lines[0]
    assert "q-verify-command" in lines[0]


def test_compaction_due_advises(tmp_path):
    config, backend = _init(
        tmp_path,
        reflection_buffer=_mined_today(),
        session_count=20,
    )
    _write_log(tmp_path, config)
    lines = evaluate_stop(tmp_path, config, backend)
    assert len(lines) == 1
    assert "compaction due" in lines[0]


def test_unmined_reflections_advise(tmp_path):
    config, backend = _init(tmp_path)  # default buffer: last_mined None
    _write_log(tmp_path, config)
    lines = evaluate_stop(tmp_path, config, backend)
    assert lines == [
        "reflections unmined this session — run bootstrap reflect --mine",
    ]


# ---------------------------------------------------------------------------
# Combination + fail open
# ---------------------------------------------------------------------------


def test_multiple_advisories_stack(tmp_path):
    config, backend = _init(tmp_path, open_questions=["q-x"], session_count=20)
    lines = evaluate_stop(tmp_path, config, backend)
    assert len(lines) == 4  # log missing, open q, compaction, unmined
    assert any("no session log" in line for line in lines)
    assert any("blocking question" in line for line in lines)
    assert any("compaction due" in line for line in lines)
    assert any("reflections unmined" in line for line in lines)


def test_broken_backend_fails_open(tmp_path):
    class _NoData:
        pass

    config = Config()
    save_config(tmp_path, config)
    _write_log(tmp_path, config)
    lines = evaluate_stop(tmp_path, config, _NoData())
    # State-based checks degrade to empty state; the run never raises.
    assert isinstance(lines, list)
    assert any("reflections unmined" in line for line in lines)
