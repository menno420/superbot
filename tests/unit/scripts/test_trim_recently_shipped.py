"""Tests for ``scripts/trim_recently_shipped.py`` — the Recently-shipped trim actuator.

All on synthetic in-memory fixtures (never the real ledger files); the pure ``trim`` core,
the entry count, and the floor-pointer recompute are exercised. The known hazard — the
non-monotonic grouped band bullets — is pinned by an explicit test.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "trim_recently_shipped.py"


@pytest.fixture(scope="module")
def tr():
    spec = importlib.util.spec_from_file_location("trim_recently_shipped_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cs(*bullets: str, floor: str = "(#600 … #535)") -> str:
    # Built without textwrap.dedent: the injected multi-bullet body carries un-indented
    # continuation lines, which would zero out dedent's common-prefix and leave the headers
    # indented (so the `## ` header lookup would miss).
    body = "\n".join(bullets)
    return (
        "# Current State\n\n"
        "## Recently shipped (newest first)\n\n"
        "> Convention note.\n\n"
        f"{body}\n"
        f"- **Older merges {floor} → [archive](current-state-archive.md).** trailing prose.\n\n"
        "> Older than this: see trackers.\n\n"
        "## Next candidates\n\n"
        "- something\n"
    )


def _archive(*bullets: str) -> str:
    body = "\n".join(bullets)
    head = "# Archive\n\n## Recently shipped — archived (newest first)\n\n"
    return head + (body + "\n" if body else "")


# --- counting -----------------------------------------------------------------------------


def test_live_entry_count_excludes_floor_pointer(tr):
    cs = _cs("- **#700 (a)** desc", "- **#699 (b)** desc")
    assert tr.live_entry_count(cs) == 2


def test_count_ignores_continuation_lines(tr):
    cs = _cs("- **#700 (a)** first line\n  continued indented line", "- **#699 (b)** d")
    assert tr.live_entry_count(cs) == 2


# --- no-op below budget -------------------------------------------------------------------


def test_no_trim_at_or_under_budget(tr):
    cs = _cs("- **#700 (a)** d", "- **#699 (b)** d")
    new_cs, new_arch, moved = tr.trim(cs, _archive(), budget=2)
    assert moved == []
    assert new_cs == cs


# --- trimming -----------------------------------------------------------------------------


def test_trims_oldest_bottom_bullet_over_budget(tr):
    cs = _cs("- **#702 (a)** d", "- **#701 (b)** d", "- **#700 (c)** d")
    new_cs, new_arch, moved = tr.trim(cs, _archive("- **#699 (z)** old"), budget=2)
    assert len(moved) == 1
    assert "#700" in moved[0]
    # The oldest live bullet left current-state…
    assert "#700 (c)" not in new_cs
    assert "#702 (a)" in new_cs and "#701 (b)" in new_cs
    # …and landed at the top of the archive (newest archived).
    arch_body = new_arch.split("archived (newest first)", 1)[1]
    assert arch_body.index("#700 (c)") < arch_body.index("#699 (z)")


def test_trim_preserves_continuation_lines_of_moved_bullet(tr):
    cs = _cs(
        "- **#702 (a)** d",
        "- **#701 (b)** d",
        "- **#700 (c)** first\n  indented continuation kept",
    )
    new_cs, new_arch, moved = tr.trim(cs, _archive(), budget=2)
    assert "indented continuation kept" not in new_cs
    assert "indented continuation kept" in new_arch


def test_never_deletes_total_bullet_count_conserved(tr):
    cs = _cs(
        "- **#704 (a)** d",
        "- **#703 (b)** d",
        "- **#702 (c)** d",
        "- **#701 (d)** d",
    )
    arch = _archive("- **#700 (z)** d")
    new_cs, new_arch, moved = tr.trim(cs, arch, budget=2)
    live_after = new_cs.count("\n- **#")
    arch_after = new_arch.count("\n- **#")
    # 4 live + 1 archived = 5 total before; still 5 after (2 moved, none deleted).
    assert len(moved) == 2
    assert live_after + arch_after == 5


# --- floor pointer recompute --------------------------------------------------------------


def test_floor_pointer_recomputed_from_true_archive_span(tr):
    cs = _cs(
        "- **#702 (a)** d",
        "- **#701 (b)** d",
        "- **#700 (c)** d",
        floor="(#600 … #535)",
    )
    arch = _archive("- **#599 (z)** d", "- **#535 (y)** oldest")
    new_cs, _, _ = tr.trim(cs, arch, budget=2)
    # After moving #700, the archive spans #700 … #535 → the floor pointer must say so.
    assert "(#700 … #535)" in new_cs
    assert "(#600 … #535)" not in new_cs


def test_non_monotonic_band_bullet_floor_uses_max_number(tr):
    # The known hazard: a grouped band carries a number newer than its base. Moving
    # "#690 · #721" must push the floor HIGH up to #721, not #690.
    cs = _cs(
        "- **#725 (a)** d",
        "- **#724 (b)** d",
        "- **#690 · #721 (c) band)** non-monotonic",
        floor="(#680 … #535)",
    )
    arch = _archive("- **#679 (z)** d", "- **#535 (y)** d")
    new_cs, _, moved = tr.trim(cs, arch, budget=2)
    assert len(moved) == 1
    assert "(#721 … #535)" in new_cs


def test_floor_pointer_ignores_stray_pr_refs_in_prose(tr):
    # BUG-0020: the recompute must read only the *bullet headers'* leading PR cluster, never a
    # free-floating "#N" in prose — a high "band-#9999" parenthetical note or a low "#1" rank
    # token in a continuation line must NOT widen the span beyond the real bullets (#700 … #535).
    cs = _cs(
        "- **#702 (a)** d",
        "- **#701 (b)** d",
        "- **#700 (c)** d",
        floor="(#600 … #535)",
    )
    arch = _archive(
        "- **#599 (z)** d",
        "  trimmed from band-#9999 — a stray high ref in a note, ranked #1 overall",
        "- **#535 (y)** oldest",
    )
    new_cs, _, _ = tr.trim(cs, arch, budget=2)
    # The moved #700 makes the true archive span #700 … #535; the prose #9999 / #1 are ignored.
    assert "(#700 … #535)" in new_cs
    assert "#9999" not in new_cs and "(#9999" not in new_cs


# --- idempotence --------------------------------------------------------------------------


def test_apply_is_idempotent(tr):
    cs = _cs("- **#702 (a)** d", "- **#701 (b)** d", "- **#700 (c)** d")
    arch = _archive("- **#699 (z)** d")
    once_cs, once_arch, moved1 = tr.trim(cs, arch, budget=2)
    twice_cs, twice_arch, moved2 = tr.trim(once_cs, once_arch, budget=2)
    assert moved1 and moved2 == []
    assert twice_cs == once_cs
    assert twice_arch == once_arch
