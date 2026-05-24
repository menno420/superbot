"""Sanity check for ``docs/help-command-surface-map.md``.

Verifies the inventory doc exists, has the expected section headings,
and lists every committed subsystem and every committed hub.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils.hub_registry import HUBS
from utils.subsystem_registry import SUBSYSTEMS

REPO_ROOT = Path(__file__).resolve().parents[3]
DOC_PATH = REPO_ROOT / "docs" / "help-command-surface-map.md"
DISBOT_ROOT = REPO_ROOT / "disbot"

_SECTION_2_HEADING = "## 2. Subsystem inventory"
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_CLASS_NAME_RE = re.compile(r"^_?[A-Z]\w*$")


@pytest.fixture(scope="module")
def doc_text() -> str:
    assert DOC_PATH.exists(), f"missing inventory doc at {DOC_PATH}"
    return DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def disbot_source() -> str:
    """Concatenated text of every ``.py`` under ``disbot/`` for source greps."""
    chunks: list[str] = []
    for path in DISBOT_ROOT.rglob("*.py"):
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(chunks)


def _extract_panel_classes(doc_text: str) -> dict[str, list[str]]:
    """Parse §2's table; map subsystem key → panel-hook class names.

    Returns an empty list for rows whose panel-hook column carries no
    backtick-wrapped identifier (e.g. ``help_cog``'s "no panel hook"
    cell). The caller decides whether that's allowed for the row.
    """
    start = doc_text.index(_SECTION_2_HEADING)
    rest = doc_text[start:]
    next_heading = re.search(r"\n## ", rest[1:])
    section = rest if not next_heading else rest[: next_heading.start() + 1]

    out: dict[str, list[str]] = {}
    for line in section.splitlines():
        if not line.startswith("| `"):
            continue
        if "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        subsystem_match = _BACKTICK_RE.search(cells[0])
        if subsystem_match is None:
            continue
        subsystem_key = subsystem_match.group(1)
        candidates = _BACKTICK_RE.findall(cells[4])
        class_names = [n for n in candidates if _CLASS_NAME_RE.match(n)]
        out[subsystem_key] = class_names
    return out


def test_doc_has_required_section_headings(doc_text):
    """Section headings keep the doc navigable. Hub table, subsystem
    inventory, and the inconsistencies callout are the load-bearing
    sections — pin these three explicitly.
    """
    for heading in (
        "## 1. Mother hubs",
        "## 2. Subsystem inventory",
        "## 3. Known inconsistencies",
    ):
        assert heading in doc_text, f"missing required heading: {heading}"


def test_doc_lists_every_committed_hub(doc_text):
    """Every hub registered in :data:`HUBS` must appear in the doc so
    the inventory tracks reality. We match by hub key wrapped in
    backticks (the doc's table convention).
    """
    for hub in HUBS:
        assert f"`{hub.key}`" in doc_text, (
            f"hub {hub.key!r} missing from inventory doc"
        )


def test_doc_lists_every_subsystem_key(doc_text):
    """Every subsystem key in :data:`SUBSYSTEMS` must appear in the
    inventory table. Match by key wrapped in backticks.
    """
    for key in SUBSYSTEMS:
        assert f"`{key}`" in doc_text, (
            f"subsystem {key!r} missing from inventory doc"
        )


def test_doc_panel_hook_classes_exist_in_source(doc_text, disbot_source):
    """Every backtick-wrapped class name in the §2 "panel hook" column
    must resolve to a real ``class <Name>`` definition under ``disbot/``.

    Catches drift like PR #290's correction set, where ``ChainPanelView``
    / ``ChannelPanelView`` / ``CleanupHubView`` / ``CountingPanelView``
    were documented but the cogs instantiate ``_ChainMenuView`` /
    ``_ChannelManagerView`` / ``CleanupPanelView`` / ``_CountingHubView``.

    ``help`` is the documented exception — its row's panel-hook cell
    intentionally carries the prose "no panel hook (Help itself is the
    panel)" and therefore yields no class names.
    """
    panel_classes = _extract_panel_classes(doc_text)
    assert panel_classes, "failed to parse §2 panel-hook column"

    for subsystem_key, class_names in panel_classes.items():
        if not class_names:
            assert subsystem_key == "help", (
                f"subsystem {subsystem_key!r} has no panel-hook class name; "
                f"only the help row is allowed to be empty"
            )
            continue
        for class_name in class_names:
            pattern = re.compile(
                rf"^class\s+{re.escape(class_name)}\s*[(:]",
                re.MULTILINE,
            )
            assert pattern.search(disbot_source), (
                f"panel hook class {class_name!r} for subsystem "
                f"{subsystem_key!r} (docs/help-command-surface-map.md §2) "
                f"has no matching `class {class_name}` definition under "
                f"disbot/"
            )
