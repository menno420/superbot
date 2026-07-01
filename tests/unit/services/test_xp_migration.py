"""Tests for services.xp_migration (batch import orchestration)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services import xp_migration


def _guild(gid: int = 1, members=None):
    return SimpleNamespace(id=gid, members=members or [])


def _import_result(raised: bool):
    return SimpleNamespace(raised=raised)


@pytest.mark.asyncio
async def test_import_levels_tallies_raised_and_unchanged():
    records = [(1, 3), (2, 13), (3, 4)]
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            side_effect=[
                _import_result(True),
                _import_result(False),  # already higher
                _import_result(True),
            ],
        ) as import_level,
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ) as audit,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            records,
            source="import:arcane",
            actor_id=42,
        )

    assert import_level.await_count == 3
    assert summary.total == 3
    assert summary.raised == 2
    assert summary.unchanged == 1
    # Exactly one summary audit action for the whole batch.
    assert audit.await_count == 1
    kwargs = audit.await_args.kwargs
    assert kwargs["subsystem"] == "xp"
    assert kwargs["mutation_type"] == "import_levels"
    assert kwargs["actor_id"] == 42
    assert kwargs["actor_type"] == "admin"


@pytest.mark.asyncio
async def test_import_levels_skips_role_sync_by_default():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch(
            "services.xp_migration._sync_level_roles",
            new_callable=AsyncMock,
        ) as sync,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            [(1, 3)],
            source="import:arcane",
        )
    sync.assert_not_awaited()
    assert summary.roles_succeeded == 0


@pytest.mark.asyncio
async def test_import_levels_runs_role_sync_when_requested():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ),
        patch(
            "services.xp_migration._sync_level_roles",
            new_callable=AsyncMock,
            return_value=(5, 4, 1),
        ) as sync,
    ):
        summary = await xp_migration.import_levels(
            _guild(),
            [(1, 3), (2, 13)],
            source="import:arcane",
            apply_roles=True,
        )
    sync.assert_awaited_once()
    assert (summary.roles_attempted, summary.roles_succeeded, summary.roles_failed) == (
        5,
        4,
        1,
    )


@pytest.mark.asyncio
async def test_import_levels_actor_type_system_without_actor():
    with (
        patch(
            "services.xp_migration.xp_service.import_level",
            new_callable=AsyncMock,
            return_value=_import_result(True),
        ),
        patch(
            "services.xp_migration.emit_audit_action",
            new_callable=AsyncMock,
        ) as audit,
    ):
        await xp_migration.import_levels(_guild(), [(1, 3)], source="import:arcane")
    assert audit.await_args.kwargs["actor_type"] == "system"


# --------------------------------------------------------------------------- #
# _sync_level_roles — reads guild config once, plans present members, one apply
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_sync_level_roles_applies_present_members_only():
    present = SimpleNamespace(id=1, roles=[], display_name="here")
    guild = _guild(members=[present])
    xp_roles = [{"role_id": 10, "role_name": "L5", "level_required": 5}]

    with (
        patch(
            "services.xp_migration.get_xp_threshold_roles",
            new_callable=AsyncMock,
            return_value=xp_roles,
        ),
        patch(
            "services.xp_migration.role_exemption_service.get_exempt_role_ids",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(xp=frozenset(), time=frozenset()),
        ),
        patch(
            "services.xp_migration.role_exemption_service.xp_roles_stack",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "services.xp_migration.xp_role_sync.plan_level_role_assignments",
            side_effect=lambda g, m, lvl, **kw: [f"assign-{m.id}"],
        ) as planner,
        patch(
            "services.xp_migration.role_automation.apply",
            new_callable=AsyncMock,
            return_value=SimpleNamespace(attempted=1, succeeded=1, failed=0),
        ) as apply,
    ):
        # user 1 present, user 99 absent from guild.members
        attempted, succeeded, failed = await xp_migration._sync_level_roles(
            guild,
            [(1, 5), (99, 7)],
            "import:arcane",
        )

    # Only the present member is planned; the absent one is skipped.
    assert planner.call_count == 1
    apply.assert_awaited_once()
    assert (attempted, succeeded, failed) == (1, 1, 0)


@pytest.mark.asyncio
async def test_sync_level_roles_noop_without_configured_roles():
    with patch(
        "services.xp_migration.get_xp_threshold_roles",
        new_callable=AsyncMock,
        return_value=[],
    ):
        assert await xp_migration._sync_level_roles(_guild(), [(1, 5)], "x") == (0, 0, 0)


# --------------------------------------------------------------------------- #
# scan_channel — read channel history → ScanPlan
# --------------------------------------------------------------------------- #
class _FakeMsg:
    def __init__(self, content, mentions=(), *, bot=True, webhook_id=None):
        self.content = content
        self.mentions = [SimpleNamespace(id=m) for m in mentions]
        self.author = SimpleNamespace(bot=bot)
        self.webhook_id = webhook_id


class _FakeChannel:
    def __init__(self, messages, cid=5, *, forbidden=False):
        self._messages = messages
        self.id = cid
        self._forbidden = forbidden

    def history(self, limit=None):  # noqa: ARG002 — mirrors discord signature
        messages = self._messages
        forbidden = self._forbidden

        class _It:
            def __init__(self):
                self._i = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if forbidden:
                    import discord

                    raise discord.Forbidden(
                        SimpleNamespace(status=403, reason="Forbidden"),
                        "no access",
                    )
                if self._i >= len(messages):
                    raise StopAsyncIteration
                msg = messages[self._i]
                self._i += 1
                return msg

        return _It()


def _arcane():
    from utils import xp_migration as xpm

    return xpm.FORMATS["arcane"]


@pytest.mark.asyncio
async def test_scan_channel_reduces_to_max_level_and_skips_non_bot():
    guild = SimpleNamespace(id=1)
    channel = _FakeChannel(
        [
            _FakeMsg("<@111> has reached level 3. GG!", [111]),
            _FakeMsg("<@111> has reached level 13. GG!", [111]),  # higher wins
            _FakeMsg("<@222> has reached level 4. GG!", [222]),
            _FakeMsg("random human chatter about level 99", [999], bot=False),  # skipped
            _FakeMsg("Arcane says hello (no level here)", []),  # no match
        ],
    )
    with patch(
        "services.xp_migration.resources.resolve_member",
        side_effect=lambda g, uid: SimpleNamespace(display_name=f"user{uid}"),
    ):
        plan = await xp_migration.scan_channel(guild, channel, _arcane(), None)

    assert plan is not None
    assert dict(plan.records) == {111: 13, 222: 4}
    assert plan.scanned_messages == 5
    assert plan.matched == 3  # two 111 level-ups + one 222; human + no-match excluded
    # sample sorted by level desc, display names resolved
    assert plan.sample[0] == ("user111", 13)


@pytest.mark.asyncio
async def test_scan_channel_forbidden_returns_none():
    guild = SimpleNamespace(id=1)
    channel = _FakeChannel([], forbidden=True)
    plan = await xp_migration.scan_channel(guild, channel, _arcane(), None)
    assert plan is None


@pytest.mark.asyncio
async def test_scan_channel_name_fallback_resolves_and_records_unresolved():
    guild = SimpleNamespace(id=1)
    channel = _FakeChannel(
        [
            _FakeMsg("KnownName has reached level 5. GG!", []),  # resolves
            _FakeMsg("GhostUser has reached level 7. GG!", []),  # no match → unresolved
        ],
    )

    def _by_name(g, name):
        return SimpleNamespace(id=777) if name == "KnownName" else None

    with (
        patch(
            "services.xp_migration.resources.resolve_member_by_name",
            side_effect=_by_name,
        ),
        patch(
            "services.xp_migration.resources.resolve_member",
            side_effect=lambda g, uid: SimpleNamespace(display_name="known"),
        ),
    ):
        plan = await xp_migration.scan_channel(guild, channel, _arcane(), None)

    assert plan is not None
    assert dict(plan.records) == {777: 5}
    assert plan.unresolved_names == ("GhostUser",)
