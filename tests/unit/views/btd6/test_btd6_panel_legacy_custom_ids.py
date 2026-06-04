"""Pin every historical ``btd6:*`` custom_id on the persistent panel.

Discord does not re-render existing anchor messages at restart — the
rendered button row is whatever was posted historically; routing
matches by ``custom_id``. So even after the PR 2 hub refactor, every
legacy custom_id must still be present on :class:`BTD6PanelView` or
clicks on old anchors fall through to "interaction failed".

This regression test catches accidental removal during future layout
changes.
"""

from __future__ import annotations

from views.btd6.panel import BTD6PanelView

# Legacy custom_ids that exist on production anchors. NEVER remove
# without a migration that re-renders all anchor messages.
_LEGACY_CUSTOM_IDS = frozenset(
    {
        "btd6:ask",
        "btd6:towers",
        "btd6:heroes",
        "btd6:modes",
        "btd6:status",
        "btd6:admin",
    },
)

# New custom_ids introduced by PR 2.
_NEW_CUSTOM_IDS = frozenset(
    {
        "btd6:events",
        "btd6:leaderboards",
        "btd6:paragon",
        "btd6:ct",
        "btd6:maps",
    },
)


def _view_custom_ids() -> set[str]:
    view = BTD6PanelView()
    return {c.custom_id for c in view.children if getattr(c, "custom_id", None)}


def test_zero_arg_construction() -> None:
    # message_anchor_manager.restore_anchors calls view_cls() at startup
    # with zero args — the persistent-view constructor must remain
    # zero-arg or every BTD6 anchor goes stale on restart.
    view = BTD6PanelView()
    assert view is not None


def test_every_legacy_custom_id_present() -> None:
    ids = _view_custom_ids()
    missing = _LEGACY_CUSTOM_IDS - ids
    assert (
        not missing
    ), f"Removed legacy custom_ids would break existing anchors: {missing}"


def test_every_new_custom_id_present() -> None:
    ids = _view_custom_ids()
    missing = _NEW_CUSTOM_IDS - ids
    assert not missing, f"Missing PR 2 custom_ids: {missing}"


def test_subsystem_name_pinned() -> None:
    # The persistent-view registry routes on SUBSYSTEM. Renaming it
    # would orphan every BTD6 anchor.
    assert BTD6PanelView.SUBSYSTEM == "btd6"


def test_no_unknown_custom_ids() -> None:
    # Any new ID introduced after PR 2 should be explicitly added to
    # the regression sets above so future readers see the scope grow.
    ids = _view_custom_ids()
    extra = ids - (_LEGACY_CUSTOM_IDS | _NEW_CUSTOM_IDS)
    assert not extra, (
        f"Undeclared custom_ids on BTD6PanelView: {extra}. Add them to "
        "_LEGACY_CUSTOM_IDS or _NEW_CUSTOM_IDS in this test file."
    )
