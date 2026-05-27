"""Regression tests for shop-select interaction ACK safety.

Pre-fix `_ShopSelect.callback` and `_ShopPanelSelect.callback` ran
`db.has_item` + `db.get_coins` + `economy_service.debit` + `db.add_item`
all before any `interaction.response.*` call. Under realistic
economy-service latency the 3-second interaction-token window expired
and the user saw "Interaction Failed".

The fix keeps the cheap balance/has-item checks as immediate
`response.send_message` replies (they're user-facing validation
feedback that doesn't need a defer round-trip) and inserts
`safe_defer` immediately before `economy_service.debit`. Final
replies route through `safe_followup` (standalone shop) or
`safe_edit` (panel context).

Scope note: these tests pin ACK ordering only. They do NOT assert
duplicate-purchase prevention — that race exists at the
read-then-write boundary regardless of ACK behaviour and needs a
service-level idempotency guard, which is out of scope here.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


def _interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 1
    interaction.user.mention = "<@1>"
    interaction.guild = MagicMock()
    interaction.guild_id = 99
    interaction.client = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    interaction.message = MagicMock()
    interaction.message.id = 4242
    return interaction


def _mock_select(item_name: str = "car") -> MagicMock:
    """Mock the bound Select so `callback(self, interaction)` can run."""
    select = MagicMock()
    select._user_id = 1
    select._guild_id = 99
    select.values = [item_name]
    select._shop_view = MagicMock()
    return select


# ---------------------------------------------------------------------------
# _ShopSelect (standalone shop)
# ---------------------------------------------------------------------------


async def test_shop_select_already_owned_uses_immediate_response():
    from views.economy.shop_panel import _ShopSelect

    select = _mock_select("car")
    interaction = _interaction()

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer") as defer,
    ):
        mock_db.has_item = AsyncMock(return_value=True)
        await _ShopSelect.callback(select, interaction)

    interaction.response.send_message.assert_awaited_once()
    assert "already own" in interaction.response.send_message.await_args.args[0]
    defer.assert_not_called()


async def test_shop_select_insufficient_balance_uses_immediate_response():
    from views.economy.shop_panel import _ShopSelect

    select = _mock_select("car")
    interaction = _interaction()

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer") as defer,
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=10)
        await _ShopSelect.callback(select, interaction)

    interaction.response.send_message.assert_awaited_once()
    assert "Need" in interaction.response.send_message.await_args.args[0]
    defer.assert_not_called()


async def test_shop_select_happy_path_defers_before_debit():
    from views.economy.shop_panel import _ShopSelect

    select = _mock_select("car")
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, **_kw):
        order.append("defer")
        return True

    async def _debit(*_a, **_kw):
        order.append("debit")
        return 0

    async def _followup(*_a, **_kw):
        order.append("followup")
        return MagicMock()

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer", AsyncMock(side_effect=_defer)),
        patch(
            "views.economy.shop_panel.safe_followup",
            AsyncMock(side_effect=_followup),
        ),
        patch("views.economy.shop_panel.economy_service") as mock_econ,
        patch("views.economy.shop_panel.post_log_embed", AsyncMock()),
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=100000)
        mock_db.add_item = AsyncMock()
        mock_econ.debit = AsyncMock(side_effect=_debit)
        await _ShopSelect.callback(select, interaction)

    assert order == ["defer", "debit", "followup"], order
    interaction.response.send_message.assert_not_called()


# ---------------------------------------------------------------------------
# _ShopPanelSelect (panel context — edits the panel in place)
# ---------------------------------------------------------------------------


async def test_shop_panel_select_already_owned_uses_immediate_response():
    from views.economy.shop_panel import _ShopPanelSelect

    select = _mock_select("car")
    interaction = _interaction()

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer") as defer,
    ):
        mock_db.has_item = AsyncMock(return_value=True)
        await _ShopPanelSelect.callback(select, interaction)

    interaction.response.send_message.assert_awaited_once()
    defer.assert_not_called()


async def test_shop_panel_select_happy_path_uses_safe_edit_after_defer():
    from views.economy.shop_panel import _ShopPanelSelect

    select = _mock_select("car")
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, **_kw):
        order.append("defer")
        return True

    async def _debit(*_a, **_kw):
        order.append("debit")
        return 0

    async def _edit(*_a, **_kw):
        order.append("safe_edit")
        return True

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer", AsyncMock(side_effect=_defer)),
        patch("views.economy.shop_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch("views.economy.shop_panel.economy_service") as mock_econ,
        patch("views.economy.shop_panel.post_log_embed", AsyncMock()),
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=100000)
        mock_db.add_item = AsyncMock()
        mock_econ.debit = AsyncMock(side_effect=_debit)
        await _ShopPanelSelect.callback(select, interaction)

    assert order == ["defer", "debit", "safe_edit"], order
    # Panel context must NOT use response.edit_message directly — it
    # always routes through safe_edit so post-defer routing works.
    interaction.response.edit_message.assert_not_called()
    interaction.response.send_message.assert_not_called()
