"""Tests for services.reaction_role_service — the audited reaction-role seam.

Pins the finding this module closes: reaction-role config writes now emit
``audit.action_recorded`` (subsystem ``role``) like every other role mutation,
instead of going straight to the DB layer from the cog.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import reaction_role_service as rrs


@pytest.mark.asyncio
async def test_bind_emoji_persists_and_audits():
    with (
        patch.object(rrs.db, "add_reaction_role", new=AsyncMock()) as add_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.bind_emoji(1, 555, "🎮", 42, actor_id=99)

    add_mock.assert_awaited_once_with(1, 555, "🎮", 42)
    audit_mock.assert_awaited_once()
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "role"
    assert kwargs["mutation_type"] == "set_reaction_role"
    assert kwargs["target"] == "role:42"
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert "message=555" in kwargs["new_value"]
    assert "emoji=🎮" in kwargs["new_value"]


@pytest.mark.asyncio
async def test_unbind_emoji_reads_prev_role_then_removes_and_audits():
    with (
        patch.object(
            rrs.db,
            "get_reaction_role",
            new=AsyncMock(return_value=42),
        ) as get_mock,
        patch.object(rrs.db, "remove_reaction_role", new=AsyncMock()) as rm_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.unbind_emoji(1, 555, "🎮", actor_id=99)

    get_mock.assert_awaited_once_with(1, 555, "🎮")
    rm_mock.assert_awaited_once_with(1, 555, "🎮")
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["mutation_type"] == "remove_reaction_role"
    # The audit row names the role that *was* bound (resolved before removal).
    assert kwargs["target"] == "role:42"
    assert kwargs["new_value"] is None


@pytest.mark.asyncio
async def test_unbind_unknown_binding_audits_without_a_role():
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=None)),
        patch.object(rrs.db, "remove_reaction_role", new=AsyncMock()),
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        await rrs.unbind_emoji(1, 555, "❓", actor_id=99)

    # No role resolved → the audit target falls back, never raises.
    assert audit_mock.await_args.kwargs["target"] == "role:unknown"


@pytest.mark.asyncio
async def test_reads_pass_through_to_db():
    with (
        patch.object(
            rrs.db,
            "get_reaction_role",
            new=AsyncMock(return_value=7),
        ) as get_mock,
        patch.object(
            rrs.db,
            "get_all_reaction_roles",
            new=AsyncMock(return_value=[{"x": 1}]),
        ) as list_mock,
    ):
        assert await rrs.get_binding(1, 555, "🎮") == 7
        assert await rrs.list_bindings(1) == [{"x": 1}]

    get_mock.assert_awaited_once_with(1, 555, "🎮")
    list_mock.assert_awaited_once_with(1)


# ---------------------------------------------------------------------------
# PR 3 — per-message modes + the mode-aware emoji-surface handlers
# ---------------------------------------------------------------------------


class _Role:
    def __init__(self, rid: int) -> None:
        self.id = rid


class _Member:
    def __init__(self, role_ids: list[int]) -> None:
        self.roles = [_Role(r) for r in role_ids]


class _Guild:
    def __init__(self, gid: int = 1) -> None:
        self.id = gid


def _enabled(value: bool = True) -> AsyncMock:
    return AsyncMock(return_value=value)


@pytest.mark.asyncio
async def test_reaction_roles_enabled_defaults_true():
    with patch(
        "services.settings_resolution.resolve_value",
        new=AsyncMock(return_value=True),
    ) as resolve_mock:
        assert await rrs.reaction_roles_enabled(1) is True
    # The literal call the settings-parity invariant scans for.
    resolve_mock.assert_awaited_once_with(1, "role", "reaction_roles_enabled", True)


@pytest.mark.asyncio
async def test_handle_reaction_add_normal_adds_role():
    guild = _Guild(1)
    member = _Member([])
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=42)),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(True)),
        patch.object(
            rrs.db,
            "get_reaction_message_mode",
            new=AsyncMock(return_value="normal"),
        ),
        patch.object(
            rrs,
            "_apply",
            new=AsyncMock(return_value=rrs.RoleMenuOutcome(added=(42,))),
        ) as apply_mock,
    ):
        outcome, strip = await rrs.handle_reaction_add(guild, member, 555, "🎮")

    assert strip is False
    assert outcome is not None and outcome.added == (42,)
    assert apply_mock.await_args.kwargs["to_add"] == (42,)
    assert apply_mock.await_args.kwargs["to_remove"] == ()


@pytest.mark.asyncio
async def test_handle_reaction_add_unique_swaps_siblings():
    guild = _Guild(1)
    member = _Member([10, 42])  # holds a sibling (10) + the clicked role (42)
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=42)),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(True)),
        patch.object(
            rrs.db,
            "get_reaction_message_mode",
            new=AsyncMock(return_value="unique"),
        ),
        patch.object(
            rrs.db,
            "get_reaction_roles_for_message",
            new=AsyncMock(
                return_value=[{"role_id": 42}, {"role_id": 10}, {"role_id": 7}],
            ),
        ),
        patch.object(
            rrs,
            "_apply",
            new=AsyncMock(return_value=rrs.RoleMenuOutcome(added=(42,), removed=(10,))),
        ) as apply_mock,
    ):
        outcome, strip = await rrs.handle_reaction_add(guild, member, 555, "🎮")

    assert strip is False
    assert outcome is not None
    # Adds the clicked role, removes only the *held* sibling (10), not 7.
    assert apply_mock.await_args.kwargs["to_add"] == (42,)
    assert apply_mock.await_args.kwargs["to_remove"] == (10,)


@pytest.mark.asyncio
async def test_handle_reaction_add_verify_is_add_only_and_strips_reaction():
    guild = _Guild(1)
    member = _Member([])
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=42)),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(True)),
        patch.object(
            rrs.db,
            "get_reaction_message_mode",
            new=AsyncMock(return_value="verify"),
        ),
        patch.object(
            rrs,
            "_apply",
            new=AsyncMock(return_value=rrs.RoleMenuOutcome(added=(42,))),
        ) as apply_mock,
    ):
        outcome, strip = await rrs.handle_reaction_add(guild, member, 555, "🎮")

    assert strip is True  # caller removes the member's reaction
    assert outcome is not None
    assert apply_mock.await_args.kwargs["to_remove"] == ()


@pytest.mark.asyncio
async def test_handle_reaction_add_skips_when_disabled():
    member = _Member([])
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=42)),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(False)),
        patch.object(rrs, "_apply", new=AsyncMock()) as apply_mock,
    ):
        outcome, strip = await rrs.handle_reaction_add(_Guild(1), member, 555, "🎮")

    assert (outcome, strip) == (None, False)
    apply_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_reaction_add_unbound_emoji_is_noop():
    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=None)),
        patch.object(rrs, "_apply", new=AsyncMock()) as apply_mock,
    ):
        assert await rrs.handle_reaction_add(_Guild(1), _Member([]), 555, "❓") == (
            None,
            False,
        )
    apply_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_handle_reaction_remove_normal_removes_but_verify_does_not():
    member = _Member([42])
    common = {
        "get_reaction_role": AsyncMock(return_value=42),
    }
    with (
        patch.object(rrs.db, "get_reaction_role", new=common["get_reaction_role"]),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(True)),
        patch.object(
            rrs.db,
            "get_reaction_message_mode",
            new=AsyncMock(return_value="normal"),
        ),
        patch.object(
            rrs,
            "_apply",
            new=AsyncMock(return_value=rrs.RoleMenuOutcome(removed=(42,))),
        ) as apply_mock,
    ):
        out = await rrs.handle_reaction_remove(_Guild(1), member, 555, "🎮")
    assert out is not None and out.removed == (42,)
    assert apply_mock.await_args.kwargs["to_remove"] == (42,)

    with (
        patch.object(rrs.db, "get_reaction_role", new=AsyncMock(return_value=42)),
        patch.object(rrs, "reaction_roles_enabled", new=_enabled(True)),
        patch.object(
            rrs.db,
            "get_reaction_message_mode",
            new=AsyncMock(return_value="verify"),
        ),
        patch.object(rrs, "_apply", new=AsyncMock()) as verify_apply,
    ):
        assert await rrs.handle_reaction_remove(_Guild(1), member, 555, "🎮") is None
    verify_apply.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_message_mode_validates_and_audits():
    with (
        patch.object(rrs.db, "set_reaction_message_mode", new=AsyncMock()) as set_mock,
        patch(
            "services.audit_events.emit_audit_action",
            new=AsyncMock(return_value=True),
        ) as audit_mock,
    ):
        stored = await rrs.set_message_mode(
            guild_id=1,
            message_id=555,
            mode="bogus",  # invalid → coerced to 'normal'
            actor_id=99,
        )

    assert stored == "normal"
    set_mock.assert_awaited_once_with(1, 555, "normal")
    kwargs = audit_mock.await_args.kwargs
    assert kwargs["subsystem"] == "role"
    assert kwargs["mutation_type"] == "set_reaction_mode"
    assert kwargs["target"] == "reaction_message:555"


# ---------------------------------------------------------------------------
# PR 5 — pickup analytics recorded through the central _apply seam
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_pickups_increments_both_counters():
    with (
        patch.object(rrs.menus_db, "record_pickup", new=AsyncMock()) as pick_mock,
        patch.object(rrs.menus_db, "record_removal", new=AsyncMock()) as rm_mock,
    ):
        await rrs._record_pickups(1, (10, 20), (30,))

    assert pick_mock.await_count == 2
    rm_mock.assert_awaited_once_with(1, 30)


@pytest.mark.asyncio
async def test_record_pickups_swallows_errors():
    # Analytics is non-critical: a stats-write failure must never propagate (it
    # would otherwise abort the role assignment in _apply).
    with patch.object(
        rrs.menus_db,
        "record_pickup",
        new=AsyncMock(side_effect=RuntimeError("db down")),
    ):
        await rrs._record_pickups(1, (10,), ())  # must not raise
