"""Phase 9b tests — LoggingRoutesView + cog wiring + table consistency.

Covers:

* The routes embed renders all seven routes (mod / cleanup / debug /
  info / warning / error / audit) with their current binding state
  surfaced (own binding / mod fallback / unset).
* The view exposes a single route select + Set / Create / Refresh /
  Back action buttons.
* Set / Create with no route selected sends an ephemeral and does not
  open a sub-view.
* Set / Create after a route is chosen delegates to the existing
  ``_open_select`` / ``_open_provision`` helpers with the right kind.
* The route tables in ``server_logging`` and the two view modules
  stay in sync — a future edit that adds a route to one but not the
  others fails this consistency test.
* ``LoggingPanelView`` now exposes a Routes button.
* The ``!logging routes`` subcommand is registered.
* ``!logging set`` and ``!logging create`` now accept all seven kinds.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.logging.routes_panel import (
    _ROUTE_DISPLAY_ORDER,
    LoggingRoutesView,
    build_routes_embed,
)


def _author(id_: int = 7) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    member.display_name = "Op"
    return member


def _guild() -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = 42
    return g


def _interaction() -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = _author()
    interaction.guild = _guild()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Route-table consistency — pin that the three tables agree.
# ---------------------------------------------------------------------------


def test_route_tables_are_in_sync_across_modules():
    """A future edit must update all three tables together or fail this test."""
    from cogs.logging.provision_view import (
        _KIND_TO_BINDING as PROVISION_KIND_TO_BINDING,
    )
    from cogs.logging.select_view import _KIND_TO_BINDING as SELECT_KIND_TO_BINDING
    from services.server_logging import _ROUTE_TO_BINDING

    assert set(_ROUTE_TO_BINDING) == set(SELECT_KIND_TO_BINDING)
    assert set(_ROUTE_TO_BINDING) == set(PROVISION_KIND_TO_BINDING)
    for k in _ROUTE_TO_BINDING:
        assert _ROUTE_TO_BINDING[k] == SELECT_KIND_TO_BINDING[k]
        assert _ROUTE_TO_BINDING[k] == PROVISION_KIND_TO_BINDING[k]


def test_route_display_order_covers_every_route():
    """The Routes embed render-order must include every known route."""
    from services.server_logging import _ROUTE_TO_BINDING

    assert set(_ROUTE_DISPLAY_ORDER) == set(_ROUTE_TO_BINDING)


def test_route_labels_cover_every_kind():
    """Every route kind must have an explicit human label in BOTH view modules.

    Regression guard for the Routes "Set Channel" crash: the Q-0109 event
    routes (``events`` / ``message_log`` / ``member_log`` / ``role_log``) were
    added to ``_KIND_TO_BINDING`` but not to ``select_view._KIND_TO_LABEL``, so
    ``_LogChannelSelect`` raised ``KeyError`` building its placeholder and the
    view surfaced the generic "An error occurred" ephemeral. The existing
    binding-table pin (:func:`test_route_tables_are_in_sync_across_modules`)
    never caught it because it checks ``_KIND_TO_BINDING`` only — this closes
    the gap for the label map too.
    """
    from cogs.logging.provision_view import _KIND_TO_LABEL as PROVISION_LABELS
    from cogs.logging.select_view import _KIND_TO_LABEL as SELECT_LABELS
    from services.server_logging import _ROUTE_TO_BINDING

    for kind in _ROUTE_TO_BINDING:
        assert kind in SELECT_LABELS, f"select_view._KIND_TO_LABEL missing {kind!r}"
        assert (
            kind in PROVISION_LABELS
        ), f"provision_view._KIND_TO_LABEL missing {kind!r}"


@pytest.mark.parametrize(
    "kind", ["mod", "cleanup", "events", "message_log", "member_log", "role_log"],
)
def test_select_view_constructs_for_every_route(kind: str):
    """The Routes 'Set Channel' path must build the picker without raising.

    Repro for the live crash: picking an event route and clicking Set Channel
    ran ``_open_select`` → ``LogChannelSelectView(user, kind)`` →
    ``_LogChannelSelect(kind)``, which indexed ``_KIND_TO_LABEL[kind]`` and
    raised ``KeyError`` for the four event routes. Constructing the view for
    every route must now succeed with a non-empty placeholder.
    """
    from cogs.logging.select_view import LogChannelSelectView

    view = LogChannelSelectView(_author(), kind)
    selects = [c for c in view.children if isinstance(c, discord.ui.ChannelSelect)]
    assert selects, "expected a ChannelSelect child"
    assert selects[0].placeholder and "channel" in selects[0].placeholder.lower()


# ---------------------------------------------------------------------------
# Routes embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routes_embed_lists_every_route():
    guild = _guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        embed = await build_routes_embed(guild)
    routes_field = next(f for f in embed.fields if f.name == "Routes")
    for kind in _ROUTE_DISPLAY_ORDER:
        assert f"`{kind}`" in routes_field.value


@pytest.mark.asyncio
async def test_routes_embed_marks_unset_routes():
    guild = _guild()
    with patch(
        "services.server_logging.resolve_log_channel",
        new_callable=AsyncMock,
        return_value=None,
    ):
        embed = await build_routes_embed(guild)
    routes_field = next(f for f in embed.fields if f.name == "Routes")
    assert "unset" in routes_field.value


@pytest.mark.asyncio
async def test_routes_embed_when_no_guild_context():
    embed = await build_routes_embed(None)
    field_names = [f.name for f in embed.fields]
    assert "No guild context" in field_names


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_has_one_select_and_four_buttons():
    view = LoggingRoutesView(_author())
    selects = [c for c in view.children if isinstance(c, discord.ui.Select)]
    buttons = [c for c in view.children if isinstance(c, discord.ui.Button)]
    assert len(selects) == 1
    assert len(buttons) == 4


def test_view_button_custom_ids():
    view = LoggingRoutesView(_author())
    custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "logging_routes.set",
        "logging_routes.create",
        "logging_routes.refresh",
        "logging_routes.back",
    }


def test_view_initial_state_no_route_selected():
    view = LoggingRoutesView(_author())
    assert view.selected_kind is None


# ---------------------------------------------------------------------------
# Action buttons — guarded by selected_kind
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_without_route_selected_sends_ephemeral():
    view = LoggingRoutesView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "logging_routes.set"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_without_route_selected_sends_ephemeral():
    view = LoggingRoutesView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "logging_routes.create"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_set_delegates_to_open_select_with_chosen_kind():
    view = LoggingRoutesView(_author())
    view.selected_kind = "error"
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "logging_routes.set"
    )
    with patch("cogs.logging.panel._open_select", new_callable=AsyncMock) as fake_open:
        await btn.callback(interaction)  # type: ignore[union-attr,misc]
    fake_open.assert_awaited_once()
    _args, kwargs = fake_open.call_args
    assert kwargs["kind"] == "error"


@pytest.mark.asyncio
async def test_create_delegates_to_open_provision_with_chosen_kind():
    view = LoggingRoutesView(_author())
    view.selected_kind = "audit"
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "logging_routes.create"
    )
    with patch(
        "cogs.logging.panel._open_provision", new_callable=AsyncMock,
    ) as fake_open:
        await btn.callback(interaction)  # type: ignore[union-attr,misc]
    fake_open.assert_awaited_once()
    _args, kwargs = fake_open.call_args
    assert kwargs["kind"] == "audit"


@pytest.mark.asyncio
async def test_back_button_returns_to_logging_panel():
    view = LoggingRoutesView(_author())
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "logging_routes.back"
    )
    with patch(
        "cogs.logging.panel.build_panel_embed",
        new_callable=AsyncMock,
        return_value=discord.Embed(title="Logging"),
    ):
        await btn.callback(interaction)  # type: ignore[union-attr,misc]
    # safe_edit on the interaction was reached.
    # We don't assert on response.edit_message directly because safe_edit
    # uses interaction.edit_original_response after defer; the key signal
    # is no crash and no ephemeral.
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# LoggingPanelView Routes button
# ---------------------------------------------------------------------------


def test_logging_panel_has_routes_button():
    from cogs.logging.panel import LoggingPanelView

    view = LoggingPanelView(_author())
    custom_ids = {
        c.custom_id  # type: ignore[attr-defined]
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "logging_panel.routes" in custom_ids


# ---------------------------------------------------------------------------
# Cog wiring — !logging routes / set / create accept all seven kinds
# ---------------------------------------------------------------------------


def test_logging_routes_subcommand_registered():
    from cogs.logging_cog import LoggingCog

    sub = LoggingCog.logging_grp.get_command("routes")
    assert sub is not None
    assert sub.name == "routes"


def test_logging_set_and_create_subcommands_still_registered():
    """Existing subcommands must not regress."""
    from cogs.logging_cog import LoggingCog

    assert LoggingCog.logging_grp.get_command("set") is not None
    assert LoggingCog.logging_grp.get_command("create") is not None


def test_logging_set_source_references_route_table():
    """A future addition to the route table should automatically be
    accepted by ``!logging set`` (no per-route allowlist in the cog).
    """
    import inspect

    from cogs.logging_cog import LoggingCog

    src = inspect.getsource(LoggingCog.logging_set.callback)
    # The set subcommand reads ``_ROUTE_TO_BINDING`` rather than
    # hard-coding ``("mod", "cleanup")`` — pin the indirection.
    assert "_ROUTE_TO_BINDING" in src


def test_logging_create_source_references_route_table():
    import inspect

    from cogs.logging_cog import LoggingCog

    src = inspect.getsource(LoggingCog.logging_create.callback)
    assert "_ROUTE_TO_BINDING" in src
