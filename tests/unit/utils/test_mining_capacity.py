"""Mining Vault v2 (Slice A) — pure cap math for the pack soft-cap and the
upgradeable vault.

These pin the math the service/view/cog layers all share: distinct-type counts,
the vault capacity + upgrade-cost ladders, the soft-cap status thresholds, and
the gentle warning copy.  All pure — no DB, no Discord (the math is the contract).
"""

from __future__ import annotations

import pytest

from utils.mining import capacity

# ---------------------------------------------------------------------------
# Distinct-type counting (caps measure KINDS, not quantity)
# ---------------------------------------------------------------------------


def test_distinct_types_counts_kinds_not_quantity():
    # 9 999 of one ore is ONE type; zero-quantity rows don't count.
    assert capacity.distinct_types({"stone": 9999}) == 1
    assert capacity.distinct_types({"stone": 5, "iron": 2, "gold": 0}) == 2
    assert capacity.distinct_types({}) == 0


def test_projected_distinct_only_grows_for_a_new_type():
    inv = {"stone": 3, "iron": 1}
    # Topping up an existing type consumes no new slot.
    assert capacity.projected_distinct_types(inv, "stone") == 2
    # A genuinely new type adds one.
    assert capacity.projected_distinct_types(inv, "diamond") == 3
    # A re-acquired zero-quantity row counts as new.
    assert capacity.projected_distinct_types({"stone": 0}, "stone") == 1
    # No grant => unchanged.
    assert capacity.projected_distinct_types(inv, None) == 2


# ---------------------------------------------------------------------------
# Vault capacity + upgrade-cost ladders
# ---------------------------------------------------------------------------


def test_vault_capacity_rises_per_level_and_clamps_at_max():
    assert capacity.vault_capacity(0) == capacity.BASE_VAULT_CAP
    assert capacity.vault_capacity(1) == (
        capacity.BASE_VAULT_CAP + capacity.VAULT_SLOTS_PER_LEVEL
    )
    top = capacity.vault_capacity(capacity.MAX_VAULT_LEVEL)
    # Above the ceiling and below the floor both clamp.
    assert capacity.vault_capacity(capacity.MAX_VAULT_LEVEL + 5) == top
    assert capacity.vault_capacity(-3) == capacity.BASE_VAULT_CAP


def test_vault_upgrade_cost_rises_then_is_none_at_max():
    c0 = capacity.vault_upgrade_cost(0)
    c1 = capacity.vault_upgrade_cost(1)
    assert c0 is not None and c1 is not None
    assert c1 > c0  # each tier costs more (a real sink)
    # At the top tier there is nothing to buy.
    assert capacity.vault_upgrade_cost(capacity.MAX_VAULT_LEVEL) is None


# ---------------------------------------------------------------------------
# CapStatus thresholds
# ---------------------------------------------------------------------------


def test_cap_status_thresholds():
    below = capacity.CapStatus(used=3, cap=10)
    assert not below.at_cap and not below.over_cap
    assert below.remaining == 7

    at = capacity.CapStatus(used=10, cap=10)
    assert at.at_cap and not at.over_cap
    assert at.remaining == 0

    over = capacity.CapStatus(used=12, cap=10)
    assert over.at_cap and over.over_cap
    assert over.remaining == 0  # never negative


def test_pack_status_uses_the_soft_cap():
    inv = {f"item{i}": 1 for i in range(capacity.PACK_SOFT_CAP)}
    status = capacity.pack_status(inv)
    assert status.cap == capacity.PACK_SOFT_CAP
    assert status.used == capacity.PACK_SOFT_CAP
    assert status.at_cap


def test_vault_status_uses_level_capacity():
    vault = {"a": 1, "b": 2}
    status = capacity.vault_status(vault, level=2)
    assert status.used == 2
    assert status.cap == capacity.vault_capacity(2)


# ---------------------------------------------------------------------------
# Warning copy (gentle nudges only — None below the threshold)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("used", "cap", "expect_warning"),
    [(0, 40, False), (39, 40, False), (40, 40, True), (41, 40, True)],
)
def test_pack_warning_fires_only_at_or_over_cap(used, cap, expect_warning):
    warning = capacity.pack_warning(capacity.CapStatus(used=used, cap=cap))
    assert (warning is not None) is expect_warning
    if warning:
        assert "Vault" in warning  # nudges toward the vault


@pytest.mark.parametrize(
    ("used", "cap", "expect_warning"),
    [(0, 30, False), (30, 30, False), (31, 30, True)],
)
def test_vault_warning_fires_only_over_cap(used, cap, expect_warning):
    # The vault warning is gentler than the pack's: it fires only when OVER
    # capacity (deposits are never blocked — owner: no hard cap).
    warning = capacity.vault_warning(capacity.CapStatus(used=used, cap=cap))
    assert (warning is not None) is expect_warning
    if warning:
        assert "vaultupgrade" in warning
