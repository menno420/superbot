"""Inventory display-logic coverage (Q-0209 completion-cert punch #7).

The inventory unit's only prior tests covered the Economy→Inventory navigation
lifecycle; the completion certificate flagged the **display logic** itself —
`_build_combined_inventory` (merge of the two inventory tables, category
grouping, rarest-first sort, drop-empty) and `_CategoryView` pagination
boundaries — as untested. These pin that logic so the merge/sort/empty/page
paths can't silently regress.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.inventory_cog import (
    _SORT_MODES,
    UnifiedInventoryView,
    _build_combined_inventory,
    _CategoryView,
    _sort_items,
)


def _member(uid: int = 1) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = uid
    m.display_name = "tester"
    m.display_avatar = MagicMock(url="https://example/avatar.png")
    return m


def _patch_inventories(eco: dict, mine: dict):
    """Patch the two DB reads `_build_combined_inventory` depends on."""
    return patch.multiple(
        "cogs.inventory_cog.db",
        get_inventory=AsyncMock(return_value=eco),
        get_mining_inventory=AsyncMock(return_value=mine),
    )


# ---------------------------------------------------------------------------
# _build_combined_inventory — merge / group / sort / drop-empty
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_merges_both_tables_and_sums_overlapping_keys():
    # "toolkit" is in both the economy and mining tables → quantities sum.
    with _patch_inventories(eco={"toolkit": 2}, mine={"toolkit": 3, "stone": 5}):
        grouped = await _build_combined_inventory(1, 99)

    tools = {k: q for k, q, _ in grouped["Tools"]}
    assert tools["toolkit"] == 5  # 2 + 3 summed across the two tables
    mats = {k: q for k, q, _ in grouped["Mining Materials"]}
    assert mats["stone"] == 5


@pytest.mark.asyncio
async def test_groups_by_catalogue_category_and_sorts_rarest_first():
    with _patch_inventories(
        eco={},
        mine={"stone": 1, "diamond": 1, "gold": 1, "iron": 1},
    ):
        grouped = await _build_combined_inventory(1, 99)

    # All four are Mining Materials; order must be Epic→Rare→Uncommon→Common.
    keys = [k for k, _, _ in grouped["Mining Materials"]]
    assert keys == ["diamond", "gold", "iron", "stone"]


@pytest.mark.asyncio
async def test_unknown_item_falls_into_other_category():
    with _patch_inventories(eco={"mystery_widget": 1}, mine={}):
        grouped = await _build_combined_inventory(1, 99)

    assert "Other" in grouped
    assert grouped["Other"][0][0] == "mystery_widget"


@pytest.mark.asyncio
async def test_zero_and_negative_quantities_are_dropped():
    with _patch_inventories(eco={"car": 0}, mine={"stone": -3, "gold": 2}):
        grouped = await _build_combined_inventory(1, 99)

    # Only the positive-qty gold survives; the empty categories never appear.
    assert grouped == {
        "Mining Materials": [("gold", 2, grouped["Mining Materials"][0][2])],
    }


@pytest.mark.asyncio
async def test_empty_inventories_return_no_categories():
    with _patch_inventories(eco={}, mine={}):
        grouped = await _build_combined_inventory(1, 99)
    assert grouped == {}


# ---------------------------------------------------------------------------
# _CategoryView — pagination boundaries
# ---------------------------------------------------------------------------


def _items(n: int) -> list[tuple[str, int, dict]]:
    return [(f"item{i}", i + 1, {"emoji": "📦", "rarity": "Common"}) for i in range(n)]


def _hub() -> MagicMock:
    hub = MagicMock(spec=UnifiedInventoryView)
    hub.target = _member()
    return hub


def test_total_pages_rounds_up_for_a_partial_last_page():
    view = _CategoryView(_member(), "Tools", _items(9), hub=_hub())
    # 9 items @ 8/page → 2 pages.
    assert view._total_pages == 2


def test_single_page_when_items_fit():
    view = _CategoryView(_member(), "Tools", _items(8), hub=_hub())
    assert view._total_pages == 1
    # No prev/next when there is only one page — just the Back button.
    labels = [getattr(c, "label", "") for c in view.children]
    assert not any("Prev" in lab or "Next" in lab for lab in labels)
    assert any("Back" in lab for lab in labels)


def test_empty_category_still_renders_one_page():
    view = _CategoryView(_member(), "Tools", [], hub=_hub())
    assert view._total_pages == 1
    embed = view.build_embed()
    assert embed.description == "Nothing here."


def test_page_footer_reports_position():
    view = _CategoryView(_member(), "Tools", _items(20), hub=_hub())
    assert view._total_pages == 3
    embed = view.build_embed()
    assert "Page 1/3" in embed.footer.text


@pytest.mark.asyncio
async def test_next_and_prev_clamp_at_the_boundaries():
    view = _CategoryView(_member(), "Tools", _items(20), hub=_hub())
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    # Prev at page 0 stays at 0.
    await view._prev_page(interaction)
    assert view._page == 0
    # Walk to the last page and confirm Next clamps there.
    await view._next_page(interaction)
    await view._next_page(interaction)
    await view._next_page(interaction)  # one past the end
    assert view._page == view._total_pages - 1 == 2


# ---------------------------------------------------------------------------
# _sort_items + _CategoryView sort cycle (completion-cert punch #5)
# ---------------------------------------------------------------------------


def _mixed() -> list[tuple[str, int, dict]]:
    # Deliberately unordered; distinct rarities, quantities, and names.
    return [
        ("stone", 5, {"rarity": "Common"}),
        ("diamond", 1, {"rarity": "Epic"}),
        ("iron", 9, {"rarity": "Uncommon"}),
        ("gold", 3, {"rarity": "Rare"}),
    ]


def test_sort_by_rarity_is_rarest_first():
    keys = [k for k, _, _ in _sort_items(_mixed(), "rarity")]
    assert keys == ["diamond", "gold", "iron", "stone"]


def test_sort_by_quantity_is_highest_first():
    keys = [k for k, _, _ in _sort_items(_mixed(), "quantity")]
    assert keys == ["iron", "stone", "gold", "diamond"]


def test_sort_by_name_is_alphabetical():
    keys = [k for k, _, _ in _sort_items(_mixed(), "name")]
    assert keys == ["diamond", "gold", "iron", "stone"]


def test_sort_breaks_ties_deterministically_by_key():
    # Two Commons with equal quantity must order by key, not input order.
    items = [("zeta", 2, {"rarity": "Common"}), ("alpha", 2, {"rarity": "Common"})]
    assert [k for k, _, _ in _sort_items(items, "rarity")] == ["alpha", "zeta"]
    assert [k for k, _, _ in _sort_items(items, "quantity")] == ["alpha", "zeta"]


def test_unknown_rarity_sorts_last():
    items = [("mystery", 1, {}), ("gold", 1, {"rarity": "Rare"})]
    assert [k for k, _, _ in _sort_items(items, "rarity")] == ["gold", "mystery"]


def test_category_view_defaults_to_rarity_sort():
    view = _CategoryView(_member(), "Mining Materials", _mixed(), hub=_hub())
    assert view._sort == "rarity"
    assert [k for k, _, _ in view._items] == ["diamond", "gold", "iron", "stone"]


def test_sort_button_present_with_multiple_items_absent_with_one():
    many = _CategoryView(_member(), "Tools", _mixed(), hub=_hub())
    assert any("Sort:" in getattr(c, "label", "") for c in many.children)
    one = _CategoryView(_member(), "Tools", _mixed()[:1], hub=_hub())
    assert not any("Sort:" in getattr(c, "label", "") for c in one.children)


@pytest.mark.asyncio
async def test_cycle_sort_advances_mode_resets_page_and_reorders():
    view = _CategoryView(_member(), "Mining Materials", _mixed(), hub=_hub())
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    view._page = 0
    await view._cycle_sort(interaction)
    # rarity → quantity (the next mode in the cycle).
    assert view._sort == _SORT_MODES[1] == "quantity"
    assert [k for k, _, _ in view._items] == ["iron", "stone", "gold", "diamond"]
    assert view._page == 0
    assert "Sorted by Quantity" in view.build_embed().footer.text
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_cycle_sort_wraps_back_to_rarity():
    view = _CategoryView(_member(), "Mining Materials", _mixed(), hub=_hub())
    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()
    for _ in range(len(_SORT_MODES)):
        await view._cycle_sort(interaction)
    assert view._sort == "rarity"  # full cycle returns to the default
