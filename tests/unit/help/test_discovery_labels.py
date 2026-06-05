"""Tests for help discovery labels (classification -> short surface label)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from cogs.help.route import discovery_label


def _cmd(classification=None):
    extras = {} if classification is None else {"classification": classification}
    return SimpleNamespace(extras=extras)


@pytest.mark.parametrize(
    "classification,expected",
    [
        (None, ""),  # no extras -> default -> no label
        ("primary_entrypoint", ""),  # canonical default -> no label
        ("panel_action", "opens panel"),
        ("power_user_shortcut", "typed-only"),
        ("internal_admin", "admin-only"),
        ("legacy_duplicate", "legacy"),
        ("deprecated", "deprecated"),
        ("totally_unknown", ""),  # unknown -> falls back to default -> no label
    ],
)
def test_discovery_label_maps_classification(classification, expected):
    assert discovery_label(_cmd(classification)) == expected
