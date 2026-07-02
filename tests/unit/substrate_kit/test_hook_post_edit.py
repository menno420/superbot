"""Tests for the PostToolUse edit advisor (plan §5.B, Lane B7)."""

from engine.hooks.post_edit import evaluate_edit
from engine.lib.config import Config

BADGED = "> **Status:** `reference`\n\n# A doc\n"
UNBADGED = "# A doc with no badge\n"
GENERATED = "NOT SOURCE OF TRUTH — regenerate, do not edit\n\n# A pack\n"


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Generated-artifact warning — by path
# ---------------------------------------------------------------------------


def test_warns_under_state_dir_rendered(tmp_path):
    config = Config()
    _write(tmp_path, f"{config.state_dir}/rendered/current-state.md", BADGED)
    msg = evaluate_edit(
        tmp_path,
        config,
        f"{config.state_dir}/rendered/current-state.md",
    )
    assert msg is not None
    assert "generated artifact" in msg
    assert "edit the template/index" in msg


def test_warns_under_state_dir_contextpacks(tmp_path):
    config = Config()
    _write(tmp_path, f"{config.state_dir}/contextpacks/core.context.md", BADGED)
    msg = evaluate_edit(
        tmp_path,
        config,
        f"{config.state_dir}/contextpacks/core.context.md",
    )
    assert msg is not None
    assert "generated artifact" in msg


# ---------------------------------------------------------------------------
# Generated-artifact warning — by head marker
# ---------------------------------------------------------------------------


def test_warns_on_not_source_of_truth_marker(tmp_path):
    config = Config()
    _write(tmp_path, "anywhere/pack.md", GENERATED)
    msg = evaluate_edit(tmp_path, config, "anywhere/pack.md")
    assert msg is not None
    assert "generated artifact" in msg


def test_marker_beyond_first_12_lines_is_ignored(tmp_path):
    config = Config()
    text = "\n" * 13 + "NOT SOURCE OF TRUTH\n"
    _write(tmp_path, "notes/deep.txt", text)
    assert evaluate_edit(tmp_path, config, "notes/deep.txt") is None


# ---------------------------------------------------------------------------
# Missing-badge warning (docs-root .md only)
# ---------------------------------------------------------------------------


def test_warns_on_unbadged_docs_markdown(tmp_path):
    config = Config()
    _write(tmp_path, "docs/plain.md", UNBADGED)
    msg = evaluate_edit(tmp_path, config, "docs/plain.md")
    assert msg is not None
    assert "Status badge" in msg


def test_badged_docs_markdown_is_silent(tmp_path):
    config = Config()
    _write(tmp_path, "docs/good.md", BADGED)
    assert evaluate_edit(tmp_path, config, "docs/good.md") is None


def test_unbadged_markdown_outside_docs_root_is_silent(tmp_path):
    config = Config()
    _write(tmp_path, "notes/plain.md", UNBADGED)
    assert evaluate_edit(tmp_path, config, "notes/plain.md") is None


def test_non_markdown_under_docs_root_is_silent(tmp_path):
    config = Config()
    _write(tmp_path, "docs/data.json", "{}\n")
    assert evaluate_edit(tmp_path, config, "docs/data.json") is None


# ---------------------------------------------------------------------------
# Path tolerance — absolute / relative / missing
# ---------------------------------------------------------------------------


def test_absolute_path_is_accepted(tmp_path):
    config = Config()
    path = _write(tmp_path, "docs/plain.md", UNBADGED)
    msg = evaluate_edit(tmp_path, config, str(path))
    assert msg is not None
    assert "Status badge" in msg


def test_missing_file_is_none(tmp_path):
    config = Config()
    assert evaluate_edit(tmp_path, config, "docs/gone.md") is None


def test_file_outside_root_fails_open(tmp_path):
    config = Config()
    other = tmp_path / "elsewhere"
    other.mkdir()
    path = _write(other, "x.md", UNBADGED)
    # Root is a sibling dir: the file resolves outside it → no docs opinion.
    root = tmp_path / "project"
    root.mkdir()
    assert evaluate_edit(root, config, str(path)) is None
