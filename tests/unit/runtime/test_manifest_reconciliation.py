"""Unit tests for core.runtime.manifest_reconciliation — manifest spine slice 3.

The reconciliation is a pure projection over a CommandManifest (whose entries
already carry the panel join), so these construct manifest fixtures directly and
pin the ``dangling_panel_action`` finding, the clean case, and the to_dicts shape.
"""

from __future__ import annotations

from core.runtime import manifest_reconciliation as mr
from core.runtime.command_manifest import CommandManifest, CommandManifestEntry


def _cmd(
    name: str,
    subsystem: str | None,
    classification: str = "primary_entrypoint",
    panels: tuple[str, ...] = (),
) -> CommandManifestEntry:
    return CommandManifestEntry(
        qualified_name=name,
        kind="prefix",
        cog="C",
        subsystem=subsystem,
        classification=classification,
        classification_declared=True,
        visibility_tier=None,
        aliases=(),
        discord_hidden=False,
        panels=panels,
    )


def _manifest(*commands: CommandManifestEntry) -> CommandManifest:
    return CommandManifest(
        version=1,
        generated_at="2026-06-17T00:00:00+00:00",
        bot_build="",
        commands=tuple(commands),
    )


def test_clean_when_panel_action_has_a_panel():
    manifest = _manifest(
        _cmd("warn", "moderation", "panel_action", panels=("moderation",)),
        _cmd("ping", None),  # not a panel action — ignored
    )
    assert mr.reconcile(manifest) == ()


def test_dangling_panel_action_flagged():
    manifest = _manifest(
        _cmd("orphan", "ghost", "panel_action", panels=()),
    )
    findings = mr.reconcile(manifest)
    assert len(findings) == 1
    f = findings[0]
    assert f.kind == mr.DANGLING_PANEL_ACTION
    assert f.command == "orphan"
    assert f.subsystem == "ghost"
    assert "no registered panel" in f.detail


def test_non_panel_action_with_no_panels_is_not_flagged():
    # A normal command in a subsystem with no panel is fine — only panel_action
    # commands need a backing panel.
    manifest = _manifest(_cmd("xp", "xp", "primary_entrypoint", panels=()))
    assert mr.reconcile(manifest) == ()


def test_reconcile_to_dicts_shape():
    manifest = _manifest(_cmd("orphan", "ghost", "panel_action", panels=()))
    dicts = mr.reconcile_to_dicts(manifest)
    assert dicts == [
        {
            "kind": mr.DANGLING_PANEL_ACTION,
            "command": "orphan",
            "subsystem": "ghost",
            "detail": dicts[0]["detail"],
        },
    ]
