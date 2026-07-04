"""Pin the ``btd6:*`` custom_ids on the persistent panel (menu Layout B).

Discord does not re-render existing anchor messages at restart — the
rendered button row is whatever was posted historically; routing matches
by ``custom_id``. So the ids reused from the old flat layout must stay
present on :class:`BTD6PanelView` or clicks on old anchors fall through
to "interaction failed".

The 2026-07-01 Layout-B redesign (category hub — design study
``docs/btd6/btd6-menu-layout-design-2026-07-01.md``) **kept** the ids that map
cleanly (ask / events / maps / strategy / status / admin) and **retired** the
Layout-A leaf ids that were folded into ephemeral sub-panels (towers / heroes /
modes / leaderboards / paragon / ct). Retiring those is an intentional
back-compat break: an old anchor still showing those buttons needs a one-time
re-post (``!btd6menu``). This test pins the new contract and the retired set so
the drop stays deliberate and documented.
"""

from __future__ import annotations

from views.btd6.panel import BTD6PanelView

# Reused from the old flat layout — keep these so existing anchors keep routing.
_KEPT_CUSTOM_IDS = frozenset(
    {
        "btd6:ask",
        "btd6:events",
        "btd6:maps",
        "btd6:strategy",
        "btd6:status",
        "btd6:admin",
    },
)

# Introduced by Layout B (the two new subdivision buttons + the universal Help
# control auto-attached to every SUBSYSTEM panel by
# views.navigation.attach_standard_nav — btd6 is a top-level hub with no
# parent_hub, so it gets Help but no Back-to-hub button).
_NEW_CUSTOM_IDS = frozenset(
    {
        "btd6:units",
        "btd6:rounds",
        "nav:help",
    },
)

# Retired in Layout B — folded into the Units / Live Events / Maps & Modes
# sub-panels. Deliberately absent from the top level (see module docstring).
_RETIRED_CUSTOM_IDS = frozenset(
    {
        "btd6:towers",
        "btd6:heroes",
        "btd6:modes",
        "btd6:leaderboards",
        "btd6:paragon",
        "btd6:ct",
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


def test_every_kept_custom_id_present() -> None:
    ids = _view_custom_ids()
    missing = _KEPT_CUSTOM_IDS - ids
    assert (
        not missing
    ), f"Removed a reused custom_id would break existing anchors: {missing}"


def test_every_new_custom_id_present() -> None:
    ids = _view_custom_ids()
    missing = _NEW_CUSTOM_IDS - ids
    assert not missing, f"Missing Layout-B custom_ids: {missing}"


def test_retired_ids_are_absent() -> None:
    # The retirement is intentional (folded into sub-panels). If one reappears,
    # either it was re-added by accident or the layout changed again — make the
    # decision explicit rather than silent.
    ids = _view_custom_ids()
    present = _RETIRED_CUSTOM_IDS & ids
    assert not present, (
        f"Retired Layout-A custom_ids reappeared on the top-level panel: "
        f"{present}. They belong in the hub sub-panels now."
    )


def test_subsystem_name_pinned() -> None:
    # The persistent-view registry routes on SUBSYSTEM. Renaming it
    # would orphan every BTD6 anchor.
    assert BTD6PanelView.SUBSYSTEM == "btd6"


def test_no_unknown_custom_ids() -> None:
    # Any new ID should be explicitly added to the sets above so future
    # readers see the scope change.
    ids = _view_custom_ids()
    extra = ids - (_KEPT_CUSTOM_IDS | _NEW_CUSTOM_IDS)
    assert not extra, (
        f"Undeclared custom_ids on BTD6PanelView: {extra}. Add them to "
        "_KEPT_CUSTOM_IDS or _NEW_CUSTOM_IDS in this test file."
    )
