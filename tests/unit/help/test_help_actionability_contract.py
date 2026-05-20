"""PR 1 — Help/Games Actionability Contract.

Replaces the discoverability-only floor with an actionability invariant:
every visible game subsystem's Help/Games panel must contain at least
one button that starts a real action (modal, select, playable view).

Router-only panels (which only swap an embed in place with "type
``!command``" instructions) and empty ``discord.ui.View()`` returns are
no longer acceptable.

Classification categories (one per terminal button):

* ``action_modal``     — opens a :class:`discord.ui.Modal`
* ``action_new_view``  — spawns a new playable view (e.g. ``_RpsView``,
  ``BlackjackView``, ``DeathmatchPanelView``) via
  ``interaction.response.edit_message(view=<other>)``
* ``action_external``  — sends a new message, opens a select, or
  delegates to a follow-up flow
* ``navigation``       — Back/Overview/Cancel — moves inside the hub
  graph (allowed, skipped from the action-count requirement)
* ``read_only``        — Rules/Stats/Status/Leaderboard — informational
  surface (allowed alongside an action button)
* ``instruction_only`` — only swaps to a ``"type !command"`` embed
  (FAILS the contract)
* ``empty_view``       — ``build_help_menu_view`` returned a View with
  no buttons (FAILS)
* ``unknown``          — could not classify under the current stub

Strict targets: ``blackjack``, ``rps_tournament`` (display "Rock
Paper Scissors"), ``deathmatch``, ``mining``, ``counting``, ``chain``.

xfail markers identify the known regressions PRs 4–6 will fix:

* ``rps_tournament`` → PR 4 (``RPSPanelView`` becomes actionable)
* ``blackjack``      → PR 5 (``BlackjackPanelView`` becomes actionable)
* ``deathmatch``     → PR 6 (``DeathmatchPanelView`` replaces empty View)

The strict=True xfails turn into hard failures (xpass) once the
underlying panels become actionable, prompting the implementer to
remove the marker and let the test pass cleanly.

Owner/admin dangerous operations that must remain prefix-only should
be added to ``COMMAND_REFERENCE_ALLOWLIST`` with a one-line
justification.
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


# ---------------------------------------------------------------------------
# Classification constants
# ---------------------------------------------------------------------------

ACTION_MODAL = "action_modal"
ACTION_NEW_VIEW = "action_new_view"
ACTION_EXTERNAL = "action_external"
NAVIGATION = "navigation"
READ_ONLY = "read_only"
INSTRUCTION_ONLY = "instruction_only"
EMPTY_VIEW = "empty_view"
UNKNOWN = "unknown"

ACTION_CLASSES = frozenset({ACTION_MODAL, ACTION_NEW_VIEW, ACTION_EXTERNAL})

# Labels signalling pure navigation inside the hub graph.
NAVIGATION_LABEL_TOKENS = (
    "back",
    "overview",
    "cancel",
    "close",
    "↩",
    "◀",
)

# Labels signalling a read-only diagnostic surface.
READ_ONLY_LABEL_TOKENS = (
    "rules",
    "help",
    "stats",
    "status",
    "leaderboard",
    "info",
)

# Owner/admin dangerous operations that may stay prefix-only — entries
# here intentionally bypass the actionability contract. Add a one-line
# justification per entry. Empty today; populated only when a real case
# arises.
COMMAND_REFERENCE_ALLOWLIST: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Stub interaction
# ---------------------------------------------------------------------------


def _stub_interaction(user_id: int = 111, guild_id: int = 222) -> MagicMock:
    """A best-effort stand-in for :class:`discord.Interaction`.

    Mocks ``response.send_modal``/``edit_message``/``send_message`` and
    ``followup.send`` as :class:`AsyncMock` so the classifier can read
    ``await_count`` and ``call_args`` after the callback returns.
    """
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = SimpleNamespace(
        id=user_id,
        display_name="tester",
        display_avatar=SimpleNamespace(url="http://x"),
        guild_permissions=SimpleNamespace(administrator=True),
        mention="<@111>",
        bot=False,
    )
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.guild_id = guild_id
    interaction.channel = MagicMock()
    interaction.channel.id = 333
    interaction.channel.mention = "#test"
    interaction.client = MagicMock()
    interaction.message = MagicMock(id=444)
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.send_modal = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _label_matches(label: str, tokens: tuple[str, ...]) -> bool:
    lower = (label or "").lower()
    return any(token in lower for token in tokens)


def _embed_is_instruction_only(embed: discord.Embed | None) -> bool:
    """An embed is instruction-only when its visible text is dominated
    by typed-command examples (``!`` or ``/`` prefixed tokens) with no
    playable affordance signals.
    """
    if embed is None:
        return False
    parts: list[str] = []
    if embed.description:
        parts.append(embed.description)
    for f in embed.fields:
        parts.append(f.name or "")
        parts.append(f.value or "")
    if embed.footer and embed.footer.text:
        parts.append(embed.footer.text)
    text = "\n".join(parts)
    if "!" not in text and "/" not in text:
        return False
    affordance_signals = (
        "press ",
        "click ",
        "tap ",
        "pick ",
        "use the buttons",
        "use the menu",
        "your move",
        "your turn",
        "your hand",
        "your hp",
        "rock",
        "paper",
        "scissors",
        "accept",
        "decline",
    )
    lower = text.lower()
    if any(sig in lower for sig in affordance_signals):
        return False
    return True


async def _classify_button(
    button: discord.ui.Button, panel: discord.ui.View
) -> str:
    """Classify a single button by running its callback against a stub
    interaction and inspecting the recorded calls.
    """
    label = button.label or ""
    custom_id = button.custom_id or ""
    if custom_id in COMMAND_REFERENCE_ALLOWLIST:
        return READ_ONLY
    if _label_matches(label, NAVIGATION_LABEL_TOKENS):
        return NAVIGATION

    interaction = _stub_interaction()
    try:
        await button.callback(interaction)  # type: ignore[misc]
    except Exception:
        # Callback raised — likely needs richer guild/db state. Fall
        # through to inspect whether any response method was *attempted*
        # before the failure.
        pass

    if interaction.response.send_modal.await_count > 0:
        return ACTION_MODAL
    if interaction.response.send_message.await_count > 0:
        return ACTION_EXTERNAL
    if interaction.followup.send.await_count > 0:
        return ACTION_EXTERNAL

    if interaction.response.edit_message.await_count > 0:
        args, kwargs = interaction.response.edit_message.call_args
        new_view = kwargs.get("view")
        new_embed = kwargs.get("embed")
        if new_view is not None and new_view is not panel:
            return ACTION_NEW_VIEW
        if _label_matches(label, READ_ONLY_LABEL_TOKENS):
            return READ_ONLY
        if _embed_is_instruction_only(new_embed):
            return INSTRUCTION_ONLY
        return UNKNOWN

    return UNKNOWN


async def classify_panel(panel: discord.ui.View) -> dict[str, str]:
    """Classify every :class:`discord.ui.Button` child of ``panel``."""
    result: dict[str, str] = {}
    for child in panel.children:
        if not isinstance(child, discord.ui.Button):
            continue
        key = child.custom_id or child.label or f"<unnamed:{id(child)}>"
        result[key] = await _classify_button(child, panel)
    return result


def _panel_has_action(classification: dict[str, str]) -> bool:
    return any(c in ACTION_CLASSES for c in classification.values())


def _punchlist(
    subsystem: str,
    embed: discord.Embed,
    view: discord.ui.View,
    cls: dict[str, str],
) -> str:
    button_count = sum(
        1 for c in view.children if isinstance(c, discord.ui.Button)
    )
    return (
        f"Subsystem {subsystem!r} panel is not actionable.\n"
        f"  view type:       {type(view).__name__}\n"
        f"  buttons total:   {button_count}\n"
        f"  classifications: {cls}\n"
        f"  embed title:     {embed.title!r}\n"
        f"  fail reason:     no button classifies as action_*\n"
        f"  expected:        at least one button opens a modal, spawns "
        f"a new playable view, or sends a real action message."
    )


# ---------------------------------------------------------------------------
# Cog construction
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _panel_construction_patches(subsystem: str):
    """Context manager patching DB / external calls that some panels
    invoke during ``build_help_menu_view`` / ``build_embed``.

    The actionability contract is about button shape, not DB state, so
    we stub out reads with empty/default results so the panel can be
    constructed without a live pool.
    """
    patches: list = []
    if subsystem == "chain":
        patches.append(
            patch(
                "cogs.chain_cog.db.get_all_chain_channels",
                new=AsyncMock(return_value=[]),
            )
        )
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)
        yield


async def _build_panel_for(
    subsystem: str,
) -> tuple[discord.Embed, discord.ui.View]:
    """Instantiate the canonical cog for ``subsystem`` and call its
    ``build_help_menu_view``.
    """
    interaction = _stub_interaction()
    if subsystem == "blackjack":
        from cogs.blackjack_cog import BlackjackCog

        cog = BlackjackCog(MagicMock())
    elif subsystem in ("rps_tournament", "rps"):
        from cogs.rps_tournament_cog import RPSTournamentCog

        cog = RPSTournamentCog(MagicMock())
    elif subsystem in ("deathmatch", "dm"):
        from cogs.deathmatch_cog import Deathmatch

        cog = Deathmatch(MagicMock())
    elif subsystem == "mining":
        from cogs.mining_cog import MiningCog

        cog = MiningCog(MagicMock())
    elif subsystem == "counting":
        from cogs.counting_cog import CountingCog

        cog = CountingCog(MagicMock())
    elif subsystem == "chain":
        from cogs.chain_cog import ChainCog

        cog = ChainCog(MagicMock())
    else:
        raise NotImplementedError(
            f"No cog mapping for actionability target {subsystem!r}. "
            "Update _build_panel_for when adding a new Games child."
        )

    with _panel_construction_patches(subsystem):
        embed, view = await cog.build_help_menu_view(interaction)
    return embed, view


# ---------------------------------------------------------------------------
# Per-subsystem actionability tests
# ---------------------------------------------------------------------------


_RPS_XFAIL = pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 4 — RPSPanelView becomes actionable "
        "(Quick Play / Bet Match / Challenge Player / Bot Match / "
        "Tournament). Remove this xfail when PR 4 lands."
    ),
)
_BLACKJACK_XFAIL = pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 5 — BlackjackPanelView becomes actionable "
        "(Solo Free / Solo Bet / Challenge Player / Tournament / "
        "Status). Remove this xfail when PR 5 lands."
    ),
)
_DEATHMATCH_XFAIL = pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 6 — DeathmatchPanelView replaces the empty "
        "discord.ui.View() and adds Fight Bot / Challenge Player. "
        "Remove this xfail when PR 6 lands."
    ),
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "subsystem",
    [
        pytest.param("rps_tournament", marks=_RPS_XFAIL),
        pytest.param("blackjack", marks=_BLACKJACK_XFAIL),
        pytest.param("deathmatch", marks=_DEATHMATCH_XFAIL),
        pytest.param("mining"),
        pytest.param("counting"),
        pytest.param("chain"),
    ],
)
async def test_games_subsystem_panel_is_actionable(subsystem: str) -> None:
    embed, view = await _build_panel_for(subsystem)
    button_count = sum(
        1 for c in view.children if isinstance(c, discord.ui.Button)
    )
    assert button_count > 0, (
        f"Subsystem {subsystem!r} returned a panel with zero Button "
        f"children — Help → Games → {subsystem} cannot reach any "
        "action."
    )
    cls = await classify_panel(view)
    assert _panel_has_action(cls), _punchlist(subsystem, embed, view, cls)


# ---------------------------------------------------------------------------
# Regression catches — specific known failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 5 — BlackjackPanelView.btn_classic no longer "
        "renders a 'type !blackjack <bet>' instruction-only embed. "
        "Remove this xfail when PR 5 lands."
    ),
)
async def test_blackjack_classic_button_is_actionable_not_instruction_only() -> None:
    from views.games import blackjack_panel

    panel = blackjack_panel.BlackjackPanelView(
        SimpleNamespace(id=111, display_name="tester")
    )
    btn = next(
        c
        for c in panel.children
        if isinstance(c, discord.ui.Button)
        and (c.custom_id or "").endswith(":classic")
    )
    klass = await _classify_button(btn, panel)
    assert klass in ACTION_CLASSES, (
        f"BlackjackPanelView 'Classic' button classifies as {klass!r}; "
        "must be action_* (PR 5 wires Solo Free / Solo Bet to "
        "BlackjackView directly)."
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 4 — RPSPanelView.btn_single no longer renders a "
        "'type !rps' instruction-only embed. Remove this xfail when PR "
        "4 lands."
    ),
)
async def test_rps_single_button_is_actionable_not_instruction_only() -> None:
    from views.games import rps_panel

    panel = rps_panel.RPSPanelView(
        SimpleNamespace(id=111, display_name="tester")
    )
    btn = next(
        c
        for c in panel.children
        if isinstance(c, discord.ui.Button)
        and (c.custom_id or "").endswith(":single")
    )
    klass = await _classify_button(btn, panel)
    assert klass in ACTION_CLASSES, (
        f"RPSPanelView 'Single Round' button classifies as {klass!r}; "
        "must be action_* (PR 4 wires Quick Play to _RpsView directly)."
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 4 — RPSPanelView.btn_tournament no longer "
        "renders a 'type !rpsregister' instruction-only embed. Remove "
        "this xfail when PR 4 lands."
    ),
)
async def test_rps_tournament_button_is_actionable_not_instruction_only() -> None:
    from views.games import rps_panel

    panel = rps_panel.RPSPanelView(
        SimpleNamespace(id=111, display_name="tester")
    )
    btn = next(
        c
        for c in panel.children
        if isinstance(c, discord.ui.Button)
        and (c.custom_id or "").endswith(":tournament")
    )
    klass = await _classify_button(btn, panel)
    assert klass in ACTION_CLASSES, (
        f"RPSPanelView 'Tournament' button classifies as {klass!r}; "
        "must be action_* (PR 4 wires Tournament to admin setup modal / "
        "Join/Status flow)."
    )


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Resolved in PR 6 — Deathmatch.build_help_menu_view no longer "
        "returns an empty discord.ui.View(). Remove this xfail when PR "
        "6 lands with DeathmatchPanelView."
    ),
)
async def test_deathmatch_panel_is_not_empty_view() -> None:
    from cogs.deathmatch_cog import Deathmatch

    cog = Deathmatch(MagicMock())
    _embed, view = await cog.build_help_menu_view(_stub_interaction())
    has_buttons = any(isinstance(c, discord.ui.Button) for c in view.children)
    assert has_buttons, (
        "Deathmatch.build_help_menu_view returns an empty View "
        f"(type={type(view).__name__}); PR 6 adds DeathmatchPanelView "
        "with Fight Bot / Challenge Player / Rules / Leaderboard "
        "buttons."
    )


# ---------------------------------------------------------------------------
# Coverage gate — the strict target list must mirror SUBSYSTEMS
# ---------------------------------------------------------------------------


def _games_subsystems_from_registry() -> set[str]:
    """All visible subsystems with ``parent_hub == "games"``."""
    from utils.subsystem_registry import SUBSYSTEMS

    return {
        name
        for name, meta in SUBSYSTEMS.items()
        if meta.get("parent_hub") == "games"
        and meta.get("visibility_mode") != "internal"
    }


def test_actionability_targets_match_registry_games_children() -> None:
    """The strict actionability target list must equal the set of
    visible Games-hub children in SUBSYSTEMS.

    If a new game is added without updating the parametrize list, the
    contract would silently skip it. This test is the alarm: it forces
    the new game into the test_games_subsystem_panel_is_actionable
    parameter list.
    """
    registry_games = _games_subsystems_from_registry()
    expected = {
        "blackjack",
        "rps_tournament",
        "deathmatch",
        "mining",
        "counting",
        "chain",
    }
    new_in_registry = registry_games - expected
    removed_from_registry = expected - registry_games
    assert not new_in_registry, (
        "New Games subsystems found that are not covered by the "
        f"actionability contract: {sorted(new_in_registry)}. Add them "
        "to test_games_subsystem_panel_is_actionable's parameter list."
    )
    assert not removed_from_registry, (
        "Games subsystems referenced by the actionability contract no "
        f"longer exist in SUBSYSTEMS: {sorted(removed_from_registry)}. "
        "Remove them from test_games_subsystem_panel_is_actionable."
    )
