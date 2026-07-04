"""Tests for the SessionStart orientation composer (plan §5.B, Lane B7)."""

from engine.hooks.session_start import compose_orientation
from engine.lib.config import Config, save_config
from engine.lib.state import JsonStateBackend, default_state
from engine.loop.reflections import REFLECTIONS_FILENAME, add_reflection


def _init(root, *, mode="guided", config=None, **overrides):
    config = config or Config()
    save_config(root, config)
    backend = JsonStateBackend(root / config.state_dir / "state.json")
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
        backend.set("mode", mode)
        for key, value in overrides.items():
            backend.set(key, value)
    return config, backend


def _add_lessons(root, config, count):
    path = root / config.state_dir / REFLECTIONS_FILENAME
    for n in range(count):
        add_reflection(
            path,
            lesson=f"lesson {n}",
            evidence=f"log:{n}",
            tags=["test"],
            buffer_size=10,
        )


# ---------------------------------------------------------------------------
# Depth: guided → standard
# ---------------------------------------------------------------------------


def test_guided_standard_renders_core_sections(tmp_path):
    config, backend = _init(tmp_path)
    text = compose_orientation(tmp_path, config, backend)
    assert "# Session orientation" in text
    assert "mode: guided" in text
    assert "In-scope actions" in text  # stance briefing
    assert "Active practices:" in text
    assert "Questions this session" in text


def test_guided_quota_suffix_counts_hidden_pending(tmp_path):
    # 13 bank questions pending, guided quota 3 → "(+10 more later)".
    config, backend = _init(tmp_path)
    text = compose_orientation(tmp_path, config, backend)
    assert "(+10 more later)" in text


def test_guided_trigger_block_mandates(tmp_path):
    config, backend = _init(tmp_path, open_questions=["q-verify-command"])
    text = compose_orientation(tmp_path, config, backend)
    assert "MANDATORY" in text
    assert "blocking question(s) open" in text


def test_standard_caps_lessons_at_three(tmp_path):
    config, backend = _init(tmp_path)
    _add_lessons(tmp_path, config, 5)
    text = compose_orientation(tmp_path, config, backend)
    assert "Learned lessons" in text
    assert text.count("- [R-") == 3


# ---------------------------------------------------------------------------
# Depth: active → full
# ---------------------------------------------------------------------------


def test_active_full_uncaps_lessons(tmp_path):
    config, backend = _init(tmp_path, mode="active")
    _add_lessons(tmp_path, config, 5)
    text = compose_orientation(tmp_path, config, backend)
    assert text.count("- [R-") == 5


def test_active_full_asks_everything_no_suffix(tmp_path):
    config, backend = _init(tmp_path, mode="active")
    text = compose_orientation(tmp_path, config, backend)
    assert "Questions this session" in text
    assert "more later" not in text


def test_full_gauges_advisory_lists_only_over_cap(tmp_path):
    config = Config()
    config.economy["gauges"] = [
        {"name": "pile", "kind": "count_cap", "glob": "docs/*.md", "cap": 0},
        {"name": "calm", "kind": "count_cap", "glob": "notes/*.md", "cap": 99},
    ]
    config, backend = _init(tmp_path, mode="active", config=config)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# hi\n", encoding="utf-8")
    text = compose_orientation(tmp_path, config, backend)
    assert "Economy advisory" in text
    assert "pile" in text
    assert "calm" not in text


def test_gauges_section_skipped_when_none_over(tmp_path):
    config, backend = _init(tmp_path, mode="active")
    text = compose_orientation(tmp_path, config, backend)
    assert "Economy advisory" not in text


# ---------------------------------------------------------------------------
# Depth: observe → minimal (observe imposes nothing)
# ---------------------------------------------------------------------------


def test_observe_minimal_omits_imposing_sections(tmp_path):
    config, backend = _init(
        tmp_path,
        mode="observe",
        slot_values={"owner_profile": {"value": "short bullets"}},
    )
    _add_lessons(tmp_path, config, 2)
    text = compose_orientation(tmp_path, config, backend)
    assert "mode: observe" in text
    assert "In-scope actions" not in text  # no stance briefing
    assert "How the owner works" not in text
    assert "Learned lessons" not in text
    assert "Active practices" not in text
    assert "Questions this session" not in text


def test_observe_minimal_trigger_block_is_advisory(tmp_path):
    config, backend = _init(tmp_path, mode="observe", open_questions=["q-x"])
    text = compose_orientation(tmp_path, config, backend)
    assert "Trigger advisory (non-mandatory)" in text
    assert "MANDATORY" not in text


def test_observe_workflow_proposal_when_due(tmp_path):
    config, backend = _init(tmp_path, mode="observe", session_count=5)
    text = compose_orientation(tmp_path, config, backend)
    assert "Proposed workflow" in text
    assert "guided" in text
    assert "active" in text


def test_observe_no_proposal_before_due(tmp_path):
    config, backend = _init(tmp_path, mode="observe", session_count=2)
    text = compose_orientation(tmp_path, config, backend)
    assert "Proposed workflow" not in text


# ---------------------------------------------------------------------------
# Section order + resilience
# ---------------------------------------------------------------------------


def test_user_style_renders_before_lessons(tmp_path):
    config, backend = _init(
        tmp_path,
        slot_values={"owner_profile": {"value": "Short bullets, no fluff."}},
    )
    _add_lessons(tmp_path, config, 1)
    text = compose_orientation(tmp_path, config, backend)
    assert "How the owner works" in text
    assert "Short bullets, no fluff." in text
    assert text.index("How the owner works") < text.index("Learned lessons")


def test_user_style_skipped_when_unfilled(tmp_path):
    config, backend = _init(tmp_path)
    text = compose_orientation(tmp_path, config, backend)
    assert "How the owner works" not in text


def test_corrupt_reflections_file_does_not_break_composition(tmp_path):
    config, backend = _init(tmp_path)
    state_dir = tmp_path / config.state_dir
    (state_dir / REFLECTIONS_FILENAME).write_text("{not json", encoding="utf-8")
    text = compose_orientation(tmp_path, config, backend)
    assert "# Session orientation" in text
    assert "Learned lessons" not in text


def test_raising_section_is_dropped_not_fatal(tmp_path, monkeypatch):
    def _boom(*_args, **_kwargs):
        raise RuntimeError("gauge meltdown")

    monkeypatch.setattr("engine.hooks.session_start.economy_gauges", _boom)
    config, backend = _init(tmp_path, mode="active")
    text = compose_orientation(tmp_path, config, backend)
    assert "# Session orientation" in text
    assert "Questions this session" in text  # later sections still render


def test_empty_backend_fails_open(tmp_path):
    config = Config()
    save_config(tmp_path, config)
    backend = JsonStateBackend(tmp_path / config.state_dir / "state.json")
    text = compose_orientation(tmp_path, config, backend)
    assert "# Session orientation" in text
