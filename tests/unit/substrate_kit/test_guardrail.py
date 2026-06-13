"""Tests for the live-loop guardrail (refuse the kit's own repo root)."""

from pathlib import Path

import pytest
from engine.lib.guardrail import UnsafeTargetError, assert_safe_target

# Non-temp fake roots so the temp-dir short-circuit doesn't mask the kit logic.
_KIT = Path("/fake/kitroot")


def test_kit_root_itself_is_unsafe():
    with pytest.raises(UnsafeTargetError):
        assert_safe_target(_KIT, _KIT)


def test_inside_kit_non_examples_is_unsafe():
    with pytest.raises(UnsafeTargetError):
        assert_safe_target(_KIT / "src" / "engine", _KIT)


def test_examples_subtree_is_safe():
    assert_safe_target(_KIT / "examples" / "demo", _KIT)


def test_dir_outside_kit_is_safe():
    assert_safe_target(Path("/fake/some-user-project"), _KIT)


def test_temp_dir_is_always_safe(tmp_path):
    assert_safe_target(tmp_path, _KIT)
