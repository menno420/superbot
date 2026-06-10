"""Regression tests for shop-select interaction ACK safety + workflow routing.

Pre-fix `_ShopSelect.callback` and `_ShopPanelSelect.callback` ran
`db.has_item` + `db.get_coins` + `economy_service.debit` + `db.add_item`
all before any `interaction.response.*` call. Under realistic
economy-service latency the 3-second interaction-token window expired
and the user saw "Interaction Failed".

The ACK fix keeps the cheap balance/has-item checks as immediate
`response.send_message` replies (user-facing validation feedback that
doesn't need a defer round-trip) and defers immediately before the
purchase. Final replies route through `safe_followup` (standalone shop)
or `safe_edit` (panel context).

RS01 (Q-0071) then replaced the view-level debit+add_item pair with one
call to ``services.shop_purchase_workflow.purchase_unique_item`` — coins
and inventory now commit or roll back together, and the duplicate-
purchase race the old scope note deferred is closed at the SQL level
(conditional upsert + conditional debit inside one transaction). The
pre-checks remain as cosmetic fast-paths only; a raced click renders the
same error copy from the workflow's result flags.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from services.shop_purchase_workflow import PurchaseResult


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


async def test_shop_select_happy_path_defers_before_purchase():
    from views.economy.shop_panel import _ShopSelect

    select = _mock_select("car")
    interaction = _interaction()

    order: list[str] = []

    async def _defer(_inter, **_kw):
        order.append("defer")
        return True

    async def _purchase(*_a, **_kw):
        order.append("purchase")
        return PurchaseResult(ok=True, price=10, new_balance=0)

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
        patch(
            "views.economy.shop_panel.shop_purchase_workflow",
        ) as mock_wf,
        patch("views.economy.shop_panel.post_log_embed", AsyncMock()),
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=100000)
        mock_wf.purchase_unique_item = AsyncMock(side_effect=_purchase)
        await _ShopSelect.callback(select, interaction)

    assert order == ["defer", "purchase", "followup"], order
    interaction.response.send_message.assert_not_called()


async def test_shop_select_raced_already_owned_renders_error_after_defer():
    """Pre-checks passed but the workflow says already-owned (raced click):
    the same copy is rendered as an ephemeral followup and no success
    embed is sent."""
    from views.economy.shop_panel import _ShopSelect

    select = _mock_select("car")
    interaction = _interaction()
    followups: list[tuple] = []

    async def _followup(_inter, *args, **kwargs):
        followups.append((args, kwargs))
        return MagicMock()

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer", AsyncMock(return_value=True)),
        patch(
            "views.economy.shop_panel.safe_followup",
            AsyncMock(side_effect=_followup),
        ),
        patch("views.economy.shop_panel.shop_purchase_workflow") as mock_wf,
        patch("views.economy.shop_panel.post_log_embed", AsyncMock()) as log,
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=100000)
        mock_wf.purchase_unique_item = AsyncMock(
            return_value=PurchaseResult(ok=False, already_owned=True, price=10),
        )
        await _ShopSelect.callback(select, interaction)

    assert len(followups) == 1
    args, kwargs = followups[0]
    assert "already own" in args[0]
    assert kwargs.get("ephemeral") is True
    log.assert_not_called()


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

    async def _purchase(*_a, **_kw):
        order.append("purchase")
        return PurchaseResult(ok=True, price=10, new_balance=0)

    async def _edit(*_a, **_kw):
        order.append("safe_edit")
        return True

    with (
        patch("views.economy.shop_panel.db") as mock_db,
        patch("views.economy.shop_panel.safe_defer", AsyncMock(side_effect=_defer)),
        patch("views.economy.shop_panel.safe_edit", AsyncMock(side_effect=_edit)),
        patch("views.economy.shop_panel.shop_purchase_workflow") as mock_wf,
        patch("views.economy.shop_panel.post_log_embed", AsyncMock()),
    ):
        mock_db.has_item = AsyncMock(return_value=False)
        mock_db.get_coins = AsyncMock(return_value=100000)
        mock_wf.purchase_unique_item = AsyncMock(side_effect=_purchase)
        await _ShopPanelSelect.callback(select, interaction)

    assert order == ["defer", "purchase", "safe_edit"], order
    # Panel context must NOT use response.edit_message directly — it
    # always routes through safe_edit so post-defer routing works.
    interaction.response.edit_message.assert_not_called()
    interaction.response.send_message.assert_not_called()
