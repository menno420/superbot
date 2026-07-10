"""Drift pin for views that extend ``discord.ui.View`` directly.

The architecture checker (``scripts/check_architecture.py``) emits a
``baseview_inheritance`` warning for every view that extends ``discord.ui.View``
directly instead of ``BaseView`` / ``HubView`` / ``PersistentView`` (game-state
views under ``views/rps`` and ``views/blackjack`` are exempt by config).  The
scan covers both ``views/`` and ``cogs/`` (cog-layer panels were a blind spot
until 2026-06-20).  Those warnings are tracked UI-adoption debt, not errors.

Since 2026-07-10 (shift-plan Q2) the checker's *warn path* recognizes the
justifying-comment convention (``# Extends discord.ui.View directly (not
BaseView): <reason>`` right above the class) and stays silent for documented
views — all 13 inventory entries below now carry it, so day-to-day
``check_architecture`` output is clean.  This test therefore scans with
``respect_justifying_comments=False``: it PINS the **raw** direct-View set so
the debt cannot grow silently even behind a self-written comment — adding a new
direct subclass fails here, forcing the author to either use a base view or
consciously extend the allowlist (comment AND allowlist entry AND
``consistency_exceptions.yml`` reason, kept in lockstep by
``test_panel_base_class_allowlist_parity.py``) — and migrating one off the list
also fails, ratcheting the debt down.  It reuses the checker's own logic (so the
exemptions stay in one place) rather than re-deriving the AST scan.
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
        # selects are ephemeral capability/pipeline-gated follow-ups (no local
        # interaction_check/on_timeout); btd6 panels carry bespoke admin checks;
        # rank_view has a documented direct subclass reason. Migrate only with a
        # concrete gain.
        # Relocated (not new debt): the `!list` paginator moved from
        # cogs/channel_cog.py to views/channels/list_panel.py in the P0-4
        # channel-ownership convergence. It is an ephemeral inline paginator with
        # its own author interaction_check + on_timeout — migrate only with a
        # concrete gain.
        ("views/channels/list_panel.py", "_ChannelListPaginatorView"),
        # _DeleteRoleView retired 2026-06-18: the role-delete picker moved onto
        # the shared BaseView-based PaginatedSelectView (fixes the >25-roles
        # #1040 truncation and ratchets this debt down). _TimeRemoveView,
        # _XpRemoveView and EnumSettingSelectView followed (2026-06-18): the
        # time/xp threshold-remove pickers and the enum-setting edit picker are
        # now PaginatedSelectView (windowed, BaseView-based).
        ("views/settings/edit_channel.py", "ChannelSettingSelectView"),
        ("views/settings/edit_number_presets.py", "NumericPresetsView"),
        ("views/settings/edit_role.py", "RoleSettingSelectView"),
        ("views/setup/launcher.py", "SetupLauncherView"),
        ("views/xp/rank_view.py", "_RankView"),
        # Cog-layer direct-View classes (the ratchet was extended to scan
        # `cogs/` too, 2026-06-20 — `views/` was the only tracked layer before,
        # so a cog-layer `discord.ui.View` panel passed the arch checker
        # silently). These 5 are the same set the consistency linter's rule 3
        # (`panel_base_class`) triaged in #1128; the reasons live in
        # `architecture_rules/consistency_exceptions.yml`. All are documented
        # specialized-lifecycle exceptions (game-state turn views, invoker-locked
        # ephemeral confirm/select views, a deliberately empty container) where
        # BaseView adds no concrete gain — migrate only with one.
        ("cogs/deathmatch_cog.py", "_DuelView"),
        ("cogs/deathmatch_cog.py", "_ChallengeView"),
        ("cogs/logging/provision_view.py", "LogChannelProvisionView"),
        ("cogs/logging/select_view.py", "LogChannelSelectView"),
        ("cogs/settings_cog.py", "_DisabledHelpHookView"),
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
    violations = checker.check_baseview_inheritance(
        checker._all_files(),
        rules,
        # Raw inventory: the ratchet must see documented views too (a justifying
        # comment silences the day-to-day warning, not this review gate).
        respect_justifying_comments=False,
    )
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
