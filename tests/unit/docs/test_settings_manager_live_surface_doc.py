"""Sentinel: the live Settings Manager UI surface must not claim "strictly read-only".

S5 shipped the read-only navigation; S6 added scalar edit/reset; PR #7 added
native channel/role selects and numeric presets.  Yet several docstrings and
embed bodies kept the old "strictly read-only" wording, which contradicted the
live behaviour and confused operators.  This test scans the same file set as
``tests/unit/invariants/test_settings_cog_read_only.py`` and asserts that the
forbidden phrasings are gone — case-insensitive substring match.

When a follow-on PR genuinely needs to call a surface "read-only" (e.g. an
audit-only view that does not yet have a write surface), prefer
"read-only diagnostic" or "navigation-only" — phrasings that don't claim the
whole Settings Manager is read-only.
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"
_DOCS = _REPO_ROOT / "docs"

_SETTINGS_UI_FILES = [
    _DISBOT / "cogs" / "settings_cog.py",
    _DISBOT / "views" / "settings" / "__init__.py",
    _DISBOT / "views" / "settings" / "hub.py",
    _DISBOT / "views" / "settings" / "subsystem_view.py",
    _DISBOT / "views" / "settings" / "audit_view.py",
    _DISBOT / "views" / "settings" / "edit_boolean.py",
    _DISBOT / "views" / "settings" / "edit_text.py",
    _DISBOT / "views" / "settings" / "edit_enum.py",
    _DISBOT / "views" / "settings" / "edit_number.py",
    _DISBOT / "views" / "settings" / "edit_number_presets.py",
    _DISBOT / "views" / "settings" / "edit_channel.py",
    _DISBOT / "views" / "settings" / "edit_role.py",
    _DISBOT / "views" / "settings" / "reset_button.py",
]

# Phrasings that misrepresent the live surface.  Case-insensitive.
_FORBIDDEN_PHRASES = (
    "strictly read-only",
    "strictly read only",
    "no edit modals",
    "no reset buttons that write",
)


def test_settings_ui_does_not_claim_strictly_read_only():
    """Every live Settings Manager UI file must drop the stale "strictly
    read-only" wording.  S6 / PR #7 have shipped scalar edit + reset; the
    docstrings and embed bodies must reflect that reality.
    """
    violations: list[tuple[str, str]] = []
    for path in _SETTINGS_UI_FILES:
        assert path.exists(), f"sentinel references missing file: {path}"
        text = path.read_text().lower()
        for phrase in _FORBIDDEN_PHRASES:
            if phrase in text:
                violations.append((str(path.relative_to(_REPO_ROOT)), phrase))
    assert not violations, (
        "Stale 'strictly read-only' phrasing found in Settings Manager UI "
        "surface — S6 / PR #7 already shipped scalar edit + reset.  Update "
        "the docstring / embed body to match the live behaviour:\n\n"
        + "\n".join(f"  {p}: {q!r}" for p, q in violations)
    )


def test_settings_roadmap_marks_s6_landed():
    """The roadmap doc must reflect that S6 and PR #7 have landed.

    PRs 7-N continue extending the surface; the roadmap is the source of
    truth for "where are we" questions and must not list S6 as a future
    milestone.
    """
    roadmap = (_DOCS / "setup-platform" / "settings-customization-roadmap.md").read_text()
    # Must contain explicit landed marker for S6 in the milestone table.
    assert "| S6 " in roadmap, (
        "Roadmap milestone table is missing the S6 row entirely."
    )
    # Find the S6 row and assert it carries a landed marker (bold "landed").
    s6_row = next(
        (line for line in roadmap.splitlines() if line.strip().startswith("| S6 ")),
        None,
    )
    assert s6_row is not None, "Roadmap S6 row could not be located."
    assert "landed" in s6_row.lower(), (
        f"Roadmap S6 row does not mark the milestone as landed: {s6_row!r}"
    )
