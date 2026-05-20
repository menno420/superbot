"""Game-panel structural invariants — narrowed by PR 1.

The Phase 7 Option A "panels are pure routers" doctrine is being
superseded by PRs 4–6, which make ``RPSPanelView``,
``BlackjackPanelView``, and the new ``DeathmatchPanelView`` actionable
launchers. The strict tests that pinned the exact custom_id set and
the instruction-only embed bodies were moved out so PRs 4–6 are not
blocked.

What remains here:

* Engine-internal imports stay forbidden in the panel modules — panels
  call helpers/views, never engine internals (``blackjack_engine``,
  persistence layers, etc.) directly.
* The "no Practice/Replay/Best-of button yet" invariants stay as
  regression alarms — those labels aren't planned in PRs 4–6 either
  and a future addition should be deliberate.
* The Rules button must still exist as a read-only diagnostic surface
  (looked up by label, not custom_id, to stay forward-compatible with
  PR 4/5 button-naming changes).
* ``build_help_menu_view`` must still return the panel class as the
  view component.

The new actionability invariant lives in
``tests/unit/help/test_help_actionability_contract.py``.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import discord
import pytest

from views.games import blackjack_panel, rps_panel


def _author(id_: int = 1) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    member.display_name = "Test"
    return member


def _find_rules_button(view: discord.ui.View) -> discord.ui.Button | None:
    for child in view.children:
        if not isinstance(child, discord.ui.Button):
            continue
        if "rules" in (child.label or "").lower():
            return child
    return None


# ---------------------------------------------------------------------------
# Module-level invariants — engine internals stay out of panels
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path",
    [
        Path(blackjack_panel.__file__),
        Path(rps_panel.__file__),
    ],
    ids=["blackjack_panel", "rps_panel"],
)
def test_panel_modules_do_not_import_game_engines(module_path: Path):
    """Panels may import view classes (``_RpsView``, ``BlackjackView``,
    ``_Duel``) and orchestration helpers, but must not reach into the
    engine internals (persistence, raw db, engine math) directly.
    """
    src = module_path.read_text()
    head = src.split("\ndef ", 1)[0]  # module-import section
    forbidden = [
        "blackjack_engine",
        "economy_service",
        "game_state_service",
        "from cogs.blackjack._persistence",
        "from cogs.blackjack._state",
        "from cogs.rps_tournament._persistence",
    ]
    for token in forbidden:
        assert token not in head, (
            f"{module_path.name} imports engine-internal token "
            f"{token!r} at module load — panels must call helpers, "
            "not reach into engine internals."
        )


# ---------------------------------------------------------------------------
# No-Practice/Replay/Best-of regression alarms
# ---------------------------------------------------------------------------


def test_blackjack_panel_has_no_practice_or_replay_button():
    """Practice / Replay / Change-Mode are not planned in PR 5. Any
    reintroduction should be deliberate with engine support."""
    view = blackjack_panel.BlackjackPanelView(_author())
    labels = [
        (c.label or "")
        for c in view.children
        if isinstance(c, discord.ui.Button)
    ]
    for token in ("Practice", "Replay", "Change Mode"):
        assert not any(token in lbl for lbl in labels), (
            f"BlackjackPanelView already exposes {token!r} — "
            "reintroduction should be deliberate with engine support."
        )


def test_rps_panel_has_no_replay_or_best_of_button():
    """Replay / Best-of selectors are not planned in PR 4. Any
    reintroduction should be deliberate."""
    view = rps_panel.RPSPanelView(_author())
    labels = [
        (c.label or "")
        for c in view.children
        if isinstance(c, discord.ui.Button)
    ]
    for token in ("Replay", "Best of"):
        assert not any(token in lbl for lbl in labels), (
            f"RPSPanelView already exposes {token!r} — reintroduction "
            "should be deliberate."
        )


# ---------------------------------------------------------------------------
# Rules button — still required as a read-only diagnostic
# ---------------------------------------------------------------------------


def test_blackjack_panel_exposes_rules_button():
    view = blackjack_panel.BlackjackPanelView(_author())
    assert _find_rules_button(view) is not None, (
        "BlackjackPanelView must keep a Rules button as the read-only "
        "diagnostic surface."
    )


def test_rps_panel_exposes_rules_button():
    view = rps_panel.RPSPanelView(_author())
    assert _find_rules_button(view) is not None, (
        "RPSPanelView must keep a Rules button as the read-only "
        "diagnostic surface."
    )


# ---------------------------------------------------------------------------
# Cog wiring — build_help_menu_view returns the panel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blackjack_cog_build_help_menu_view_returns_panel():
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog(bot=MagicMock())
    interaction = MagicMock()
    interaction.user = _author()
    embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, blackjack_panel.BlackjackPanelView)
    assert "Blackjack" in (embed.title or "")


@pytest.mark.asyncio
async def test_rps_cog_build_help_menu_view_returns_panel():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog(bot=MagicMock())
    interaction = MagicMock()
    interaction.user = _author()
    embed, view = await cog.build_help_menu_view(interaction)
    assert isinstance(view, rps_panel.RPSPanelView)
    title = embed.title or ""
    assert (
        "Rock-Paper-Scissors" in title
        or "Rock Paper Scissors" in title
        or "RPS" in title
    )
