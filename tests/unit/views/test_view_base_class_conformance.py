"""Drift pin for views that extend ``discord.ui.View`` directly.

The architecture checker (``scripts/check_architecture.py``) emits a
``baseview_inheritance`` warning for every view that extends ``discord.ui.View``
directly instead of ``BaseView`` / ``HubView`` / ``PersistentView`` (game-state
views under ``views/rps`` and ``views/blackjack`` are exempt by config).  Those
warnings are tracked UI-adoption debt, not errors.

This test PINS the exact current set so the debt cannot grow silently: adding a
new direct subclass fails here — forcing the author to either use a base view or
consciously extend the allowlist — and migrating one off the list also fails,
ratcheting the debt down.  It reuses the checker's own logic (so the exemptions
stay in one place) rather than re-deriving the AST scan.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_architecture.py"

# Frozen inventory of views that extend ``discord.ui.View`` directly today. The
# rule is "this set may shrink, never grow without review". rps/blackjack
# game-state views are exempt in the checker config and so do not appear here.
_KNOWN_DIRECT_VIEW_SUBCLASSES = frozenset(
    {
        ("views/btd6/admin_panel.py", "BTD6AdminView"),
        ("views/btd6/strategy_review.py", "StrategyReviewView"),
        # RS10 migrations (consolidated plan Batch 9 + follow-ons): the
        # economy family (4 views, 2026-06-10) and the mining family
        # (2 views, same day) moved onto BaseView — ratchet 17 → 13 → 11.
        # The remaining entries are NOT lifecycle duplication: the settings
        # selects + roles removes are ephemeral capability/pipeline-gated
        # follow-ups (no local interaction_check/on_timeout); btd6 panels
        # carry bespoke admin checks; rank_view has a documented direct
        # subclass reason. Migrate only with a concrete gain.
        # Relocated (not new debt): the `!list` paginator moved from
        # cogs/channel_cog.py to views/channels/list_panel.py in the P0-4
        # channel-ownership convergence (cogs/ are not scanned by this ratchet,
        # so it surfaced on the move). It is an ephemeral inline paginator with
        # its own author interaction_check + on_timeout — migrate only with a
        # concrete gain.
        ("views/channels/list_panel.py", "_ChannelListPaginatorView"),
        ("views/roles/management_panel.py", "_DeleteRoleView"),
        ("views/roles/time_roles_panel.py", "_TimeRemoveView"),
        ("views/roles/xp_roles_panel.py", "_XpRemoveView"),
        ("views/settings/edit_channel.py", "ChannelSettingSelectView"),
        ("views/settings/edit_enum.py", "EnumSettingSelectView"),
        ("views/settings/edit_number_presets.py", "NumericPresetsView"),
        ("views/settings/edit_role.py", "RoleSettingSelectView"),
        ("views/setup/launcher.py", "SetupLauncherView"),
        ("views/xp/rank_view.py", "_RankView"),
    },
)


@pytest.fixture(scope="module")
def _checker():
    spec = importlib.util.spec_from_file_location("check_architecture_drift", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _current_direct_subclasses(checker) -> set[tuple[str, str]]:
    rules = checker._load("canonical_helpers.yaml")
    violations = checker.check_baseview_inheritance(checker._all_files(), rules)
    return {
        (str(v.file.relative_to(checker.DISBOT_ROOT)), v.message.split("`")[1])
        for v in violations
    }


def test_direct_view_subclasses_match_known_inventory(_checker):
    current = _current_direct_subclasses(_checker)

    added = current - _KNOWN_DIRECT_VIEW_SUBCLASSES
    removed = _KNOWN_DIRECT_VIEW_SUBCLASSES - current

    assert not added, (
        "New view(s) extend discord.ui.View directly — extend BaseView / HubView / "
        "PersistentView instead, or consciously add to the allowlist: "
        f"{sorted(added)}"
    )
    assert not removed, (
        "View(s) no longer extend discord.ui.View directly (nice!) — remove them "
        "from _KNOWN_DIRECT_VIEW_SUBCLASSES to ratchet the debt down: "
        f"{sorted(removed)}"
    )
