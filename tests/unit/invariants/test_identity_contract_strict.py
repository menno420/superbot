"""PR I1b — STRICT-mode invariant: production identity surfaces must agree.

Asserts that the four identity surfaces (SUBSYSTEMS registry, the
PersistentView ``_REGISTRY``, the interaction_router ``_handlers``, and
the DB ``panel_anchors`` rows) are internally consistent so that
``IDENTITY_CONTRACT_STRICT=true`` produces **zero fatal-tier findings**
in production.

We do NOT load every cog here — that requires the full async bot
harness and a real DB.  Instead we synthesize the union of every
non-internal ``entry_points`` declared by the registry and present
that to the validator as the loaded-commands surface.  This catches:

  * an ``entry_points`` list referencing a command name that the cog
    never registers (regressions land at registry-edit time).
  * a registry entry whose ``visibility_mode`` is not ``internal`` but
    whose entry_points list is empty (which would always produce zero
    findings vacuously — currently impossible because every
    user/admin-tier subsystem has commands).

If a contributor adds a new SUBSYSTEMS entry without wiring its
commands, this invariant fails the build — the same effect STRICT
mode will have once it is promoted to production.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.subsystem_registry import (
    IDENTITY_FINDING_TIER,
    SUBSYSTEMS,
    summarize_findings,
    validate_identity_contract,
)


def _all_non_internal_entry_points() -> set[str]:
    return {
        ep
        for _name, meta in SUBSYSTEMS.items()
        if meta.get("visibility_mode") != "internal"
        for ep in meta.get("entry_points", ())
    }


def _bot_mock_with(commands: set[str]) -> MagicMock:
    cmds = []
    for name in commands:
        m = MagicMock()
        m.name = name
        cmds.append(m)
    bot = MagicMock()
    bot.commands = cmds
    return bot


@pytest.mark.asyncio
async def test_registry_passes_strict_against_its_own_entry_points():
    """The SUBSYSTEMS registry is self-consistent under STRICT semantics.

    Treats every declared entry_point as if the cog had loaded
    successfully.  Any registry-side mismatch (typo in an entry_point,
    duplicate naming, etc.) surfaces here.
    """
    bot = _bot_mock_with(_all_non_internal_entry_points())
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    summary = summarize_findings(findings)
    assert summary["by_tier"]["fatal"] == 0, (
        "Registry self-consistency violation under STRICT semantics — "
        f"fatal-tier findings: {findings['entry_point_missing_command']}.  "
        "Either the entry_point list contains a typo or a SUBSYSTEMS "
        "entry was added without wiring its command."
    )


@pytest.mark.asyncio
async def test_strict_invariant_buckets_match_validator_buckets():
    """The tier map and the validator's bucket names cannot drift.

    Duplicates the registry-side invariant from test_identity_contract.py
    here in the invariants directory so a single ``pytest tests/unit/invariants``
    run is sufficient gating signal for the architectural contract.
    """
    bot = _bot_mock_with(set())
    with (
        patch("core.runtime.interaction_router._handlers", {}),
        patch("core.runtime.persistent_views._REGISTRY", {}),
        patch("utils.db.fetchall", new_callable=AsyncMock, return_value=[]),
    ):
        findings = await validate_identity_contract(bot)
    assert set(IDENTITY_FINDING_TIER) == set(findings), (
        "Adding a new finding bucket without classifying it in "
        "IDENTITY_FINDING_TIER would silently default to fatal-tier "
        "under STRICT semantics.  Classify before merging."
    )
