"""Tests for ``scripts/check_generated_artifacts_fresh.py`` — the generated-artifact
freshness umbrella.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure stdlib, so
it runs in CI with no extra dependencies — including the live guard that builds each
registered artifact fresh and confirms the committed copies are currently in sync.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_generated_artifacts_fresh.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_generated_artifacts_fresh_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# set-drift primitive
# ---------------------------------------------------------------------------
def test_set_drift_reports_added_and_removed(mod):
    findings = mod._set_drift(
        "artifact",
        "things",
        committed={"a", "b", "stale"},
        fresh={"a", "b", "new"},
        refresh_hint="re-run gen",
    )
    messages = " ".join(f.message for f in findings)
    assert len(findings) == 2  # one added, one removed
    assert "'new'" in messages
    assert "'stale'" in messages
    assert all(f.artifact == "artifact" and f.surface == "things" for f in findings)


def test_set_drift_silent_when_identical(mod):
    assert mod._set_drift("a", "s", {"x", "y"}, {"x", "y"}, "hint") == []


def test_fmt_sample_truncates_deterministically(mod):
    sample = mod._fmt_sample({f"v{i}" for i in range(10)}, limit=3)
    assert sample.startswith("'v0', 'v1', 'v2'")
    assert "(+7 more)" in sample


# ---------------------------------------------------------------------------
# env-var name extractor
# ---------------------------------------------------------------------------
def test_env_names_extracts_table_rows(mod):
    doc = (
        "# Environment variables\n\n"
        "| Variable | Layers | Usages |\n"
        "|---|---|---|\n"
        "| `DATABASE_URL` | utils | `disbot/utils/db/pool.py:41` |\n"
        "| `YOUTUBE_API_KEY` | services | `disbot/services/x.py:22` |\n"
        "Prose mentioning `not_a_var` and `lower_case` should not match.\n"
    )
    assert mod._env_names(doc) == {"DATABASE_URL", "YOUTUBE_API_KEY"}


def test_env_names_ignores_line_number_churn(mod):
    """A shifted code line-number must NOT register as drift (it is volatile)."""
    before = "| `DATABASE_URL` | utils | `disbot/utils/db/pool.py:41` |\n"
    after = "| `DATABASE_URL` | utils | `disbot/utils/db/pool.py:99` |\n"
    assert mod._env_names(before) == mod._env_names(after) == {"DATABASE_URL"}


# ---------------------------------------------------------------------------
# context-pack line extractor
# ---------------------------------------------------------------------------
def test_pack_lines_drops_generated_date_and_blanks(mod):
    text = (
        "# Pack\n"
        "\n"
        "> Generated: 2026-06-10 · Subsystem key: `x`\n"
        "Real content line.\n"
    )
    lines = mod._pack_lines(text)
    assert "Real content line." in lines
    assert not any(line_.startswith("> Generated:") for line_ in lines)
    assert "" not in lines


def test_pack_lines_date_only_delta_is_not_drift(mod):
    a = "# Pack\n> Generated: 2026-06-10 · key\nBody.\n"
    b = "# Pack\n> Generated: 2026-06-17 · key\nBody.\n"
    assert mod._pack_lines(a) == mod._pack_lines(b)


# ---------------------------------------------------------------------------
# registry + live freshness (the load-bearing guard)
# ---------------------------------------------------------------------------
def test_registry_paths_exist(mod):
    for artifact in mod.REGISTRY:
        # the committed path may be a glob (context packs) — check the dir for those
        path = mod.REPO_ROOT / artifact.committed
        target = path.parent if "*" in artifact.committed else path
        assert target.exists(), f"{artifact.label}: {artifact.committed} missing"


def test_committed_artifacts_are_currently_fresh(mod):
    """The committed generated artifacts must be in sync with their generators.

    If this fails, a source change shipped without re-running the named generator —
    regenerate the flagged artifact rather than weakening this guard.
    """
    findings = mod.check_all()
    assert findings == [], "\n".join(
        f"[{d.artifact}] {d.surface}: {d.message}" for d in findings
    )


def test_main_warn_only_exits_zero_when_fresh(mod, capsys):
    assert mod.main([]) == 0
    assert "OK" in capsys.readouterr().out


def test_main_list_prints_registry(mod, capsys):
    assert mod.main(["--list"]) == 0
    out = capsys.readouterr().out
    assert "dashboard.json" in out
    assert "site.json" in out
    assert "env-vars.md" in out
    assert "context-packs" in out


# ---------------------------------------------------------------------------
# site.json artifact (the public subset — plan §5 / §2.2)
# ---------------------------------------------------------------------------
def test_site_json_is_registered(mod):
    labels = {a.label for a in mod.REGISTRY}
    assert "site.json" in labels


def test_site_json_committed_is_fresh(mod):
    # The committed botsite/data/site.json must be in sync with the producer.
    findings = mod.drift_site_json()
    assert findings == [], "\n".join(
        f"[{d.surface}] {d.message}" for d in findings
    )
