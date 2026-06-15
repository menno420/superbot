"""Track 2 PR 4 — resource_health inspector.

Covers every status code via a fake ``discord.Guild`` fixture and a
fake ``bindings_db.list_for_guild`` stub. Pins:

* Each :class:`BindingKind` (CHANNEL, ROLE, CATEGORY, THREAD, MEMBER)
  produces a finding.
* Status codes: ok / missing / not_configured / unbound /
  stale_binding / wrong_type / permission_blocked / hierarchy_blocked.
* Severity mapping per status.
* Per-finding ``target_id`` field is populated where applicable.
* The inspector is read-only (no DB writes, no Discord create calls).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import pytest

from core.runtime.subsystem_schema import BindingKind, BindingSpec, SubsystemSchema
from services import resource_health
from services.resource_health import (
    HIERARCHY_BLOCKED,
    MISSING,
    NOT_CONFIGURED,
    OK,
    PERMISSION_BLOCKED,
    SEV_ERROR,
    SEV_INFO,
    SEV_WARN,
    STALE_BINDING,
    UNBOUND,
    UNKNOWN,
    WRONG_TYPE,
    ResourceHealthFinding,
    inspect,
)

# ---------------------------------------------------------------------------
# Fake Discord guild + resources
# ---------------------------------------------------------------------------


@dataclass
class _FakeRole:
    id: int
    name: str
    position: int = 1

    def __ge__(self, other):  # used by ``role >= bot_top_role``
        return self.position >= other.position

    def __gt__(self, other):
        return self.position > other.position


class _FakePerms:
    def __init__(
        self,
        *,
        view_channel: bool = True,
        send_messages: bool = True,
        embed_links: bool = True,
        connect: bool = True,
        manage_roles: bool = True,
    ):
        self.view_channel = view_channel
        self.send_messages = send_messages
        self.embed_links = embed_links
        self.connect = connect
        self.manage_roles = manage_roles


class _FakeTextChannel(discord.TextChannel):
    """A bare ``isinstance``-compatible TextChannel that ducks attribute access."""

    def __init__(self, *, channel_id: int, name: str, perms: _FakePerms):
        # Skip discord.py's __init__ chain — we only need attribute access.
        self.id = channel_id
        self.name = name
        self._perms = perms

    def permissions_for(self, member):  # type: ignore[override]
        return self._perms


class _FakeCategory(discord.CategoryChannel):
    def __init__(self, *, channel_id: int, name: str, perms: _FakePerms):
        self.id = channel_id
        self.name = name
        self._perms = perms

    def permissions_for(self, member):  # type: ignore[override]
        return self._perms


@dataclass
class _FakeBotMember:
    top_role: _FakeRole
    guild_permissions: _FakePerms


class _FakeGuild:
    def __init__(
        self,
        guild_id: int = 1,
        *,
        channels: dict[int, object] | None = None,
        roles: dict[int, _FakeRole] | None = None,
        threads: dict[int, object] | None = None,
        members: dict[int, object] | None = None,
        me: _FakeBotMember | None = None,
    ):
        self.id = guild_id
        self._channels = channels or {}
        self._roles = roles or {}
        self._threads = threads or {}
        self._members = members or {}
        self.me = me

    def get_channel(self, cid):
        return self._channels.get(cid)

    def get_role(self, rid):
        return self._roles.get(rid)

    def get_thread(self, tid):
        return self._threads.get(tid)

    def get_member(self, mid):
        return self._members.get(mid)


# ---------------------------------------------------------------------------
# Schema fixtures
# ---------------------------------------------------------------------------


def _spec(name: str, kind: BindingKind, required: bool = True) -> BindingSpec:
    return BindingSpec(
        name=name,
        kind=kind,
        required=required,
        hint="",
        capability_required=f"xp.{name}.bind",
    )


def _row(
    subsystem: str,
    name: str,
    *,
    target_id: int | None = 100,
    status: str = "bound",
    kind: BindingKind = BindingKind.CHANNEL,
):
    return {
        "guild_id": 1,
        "subsystem": subsystem,
        "binding_name": name,
        "kind": kind.value,
        "target_id": target_id,
        "status": status,
    }


@pytest.fixture
def _isolate_schemas():
    """Yield a registry override; restore on exit."""

    def _install(schemas):
        return patch.object(
            resource_health,
            "all_schemas",
            return_value=schemas,
        )

    return _install


# ---------------------------------------------------------------------------
# Sanity: empty registry → empty findings
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inspect_empty_registry_returns_empty_tuple(_isolate_schemas):
    with (
        _isolate_schemas({}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        result = await inspect(_FakeGuild())
    assert result == ()


# ---------------------------------------------------------------------------
# Per-status coverage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_required_binding(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL, required=True),),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert len(findings) == 1
    assert findings[0].status == MISSING
    assert findings[0].severity == SEV_ERROR


@pytest.mark.asyncio
async def test_not_configured_optional_binding(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL, required=False),),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert findings[0].status == NOT_CONFIGURED
    assert findings[0].severity == SEV_INFO


@pytest.mark.asyncio
async def test_unbound_row_with_null_target(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=None)],
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert findings[0].status == UNBOUND
    assert findings[0].severity == SEV_WARN
    assert findings[0].target_id is None


@pytest.mark.asyncio
async def test_unbound_row_with_unresolved_status(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=42, status="unresolved")],
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert findings[0].status == UNBOUND


@pytest.mark.asyncio
async def test_stale_channel_binding(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    # Row says channel 999 is bound; the guild does not contain channel 999.
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=999)],
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert findings[0].status == STALE_BINDING
    assert findings[0].severity == SEV_ERROR
    assert findings[0].target_id == 999


@pytest.mark.asyncio
async def test_wrong_type_channel_kind_resolves_to_category(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    cat = _FakeCategory(channel_id=100, name="Mod", perms=_FakePerms())
    guild = _FakeGuild(channels={100: cat})
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=100)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == WRONG_TYPE
    assert findings[0].severity == SEV_ERROR


@pytest.mark.asyncio
async def test_channel_permission_blocked_when_send_missing(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    ch = _FakeTextChannel(
        channel_id=100,
        name="general",
        perms=_FakePerms(send_messages=False),
    )
    guild = _FakeGuild(
        channels={100: ch},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(),
        ),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=100)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == PERMISSION_BLOCKED
    assert findings[0].severity == SEV_ERROR
    assert "send_messages" in findings[0].message


@pytest.mark.asyncio
async def test_channel_ok(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    ch = _FakeTextChannel(channel_id=100, name="general", perms=_FakePerms())
    guild = _FakeGuild(
        channels={100: ch},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(),
        ),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "announce", target_id=100)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == OK
    assert findings[0].severity == SEV_INFO


@pytest.mark.asyncio
async def test_role_hierarchy_blocked(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("vip", BindingKind.ROLE),),
    )
    target = _FakeRole(id=200, name="VIP", position=20)  # ABOVE bot
    guild = _FakeGuild(
        roles={200: target},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(),
        ),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "vip", target_id=200, kind=BindingKind.ROLE)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == HIERARCHY_BLOCKED
    assert findings[0].severity == SEV_ERROR


@pytest.mark.asyncio
async def test_role_permission_blocked_when_manage_roles_missing(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("vip", BindingKind.ROLE),),
    )
    target = _FakeRole(id=200, name="VIP", position=5)  # below bot
    guild = _FakeGuild(
        roles={200: target},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(manage_roles=False),
        ),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "vip", target_id=200, kind=BindingKind.ROLE)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == PERMISSION_BLOCKED
    assert "Manage Roles" in findings[0].message


@pytest.mark.asyncio
async def test_role_ok(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("vip", BindingKind.ROLE),),
    )
    target = _FakeRole(id=200, name="VIP", position=5)
    guild = _FakeGuild(
        roles={200: target},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(),
        ),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[_row("xp", "vip", target_id=200, kind=BindingKind.ROLE)],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == OK


@pytest.mark.asyncio
async def test_category_ok(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="moderation",
        bindings=(_spec("category", BindingKind.CATEGORY),),
    )
    cat = _FakeCategory(channel_id=300, name="Mod", perms=_FakePerms())
    guild = _FakeGuild(
        channels={300: cat},
        me=_FakeBotMember(
            top_role=_FakeRole(id=999, name="Bot", position=10),
            guild_permissions=_FakePerms(),
        ),
    )
    with (
        _isolate_schemas({"moderation": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[
                _row(
                    "moderation", "category", target_id=300, kind=BindingKind.CATEGORY
                ),
            ],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == OK


@pytest.mark.asyncio
async def test_thread_stale(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce_thread", BindingKind.THREAD),),
    )
    guild = _FakeGuild()  # no threads in cache
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[
                _row("xp", "announce_thread", target_id=400, kind=BindingKind.THREAD),
            ],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == STALE_BINDING


@pytest.mark.asyncio
async def test_member_ok(_isolate_schemas):
    schema = SubsystemSchema(
        subsystem="moderation",
        bindings=(_spec("contact", BindingKind.MEMBER),),
    )
    member = SimpleNamespace(id=500)
    member.__str__ = lambda self=member: "ContactUser#0001"  # type: ignore[assignment]
    guild = _FakeGuild(members={500: member})
    with (
        _isolate_schemas({"moderation": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[
                _row("moderation", "contact", target_id=500, kind=BindingKind.MEMBER),
            ],
        ),
    ):
        findings = await inspect(guild)
    assert findings[0].status == OK


# ---------------------------------------------------------------------------
# Aggregate behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inspect_returns_findings_sorted_by_subsystem_then_name(_isolate_schemas):
    schemas = {
        "xp": SubsystemSchema(
            subsystem="xp",
            bindings=(
                _spec("z_last", BindingKind.CHANNEL),
                _spec("a_first", BindingKind.CHANNEL),
            ),
        ),
        "moderation": SubsystemSchema(
            subsystem="moderation",
            bindings=(_spec("category", BindingKind.CATEGORY),),
        ),
    }
    with (
        _isolate_schemas(schemas),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        findings = await inspect(_FakeGuild())
    # Subsystem order is alphabetised; binding order is declared (within a
    # schema, the spec tuple is the source of truth).
    assert [(f.subsystem, f.binding_name) for f in findings] == [
        ("moderation", "category"),
        ("xp", "z_last"),
        ("xp", "a_first"),
    ]


@pytest.mark.asyncio
async def test_db_failure_yields_findings_using_no_rows(_isolate_schemas):
    """If the DB read fails the inspector still returns findings for
    every declared binding — they look like ``missing`` /
    ``not_configured`` since no rows are available."""
    schema = SubsystemSchema(
        subsystem="xp",
        bindings=(_spec("announce", BindingKind.CHANNEL),),
    )
    with (
        _isolate_schemas({"xp": schema}),
        patch(
            "services.resource_health.bindings_db.list_for_guild",
            new_callable=AsyncMock,
            side_effect=RuntimeError("db down"),
        ),
    ):
        findings = await inspect(_FakeGuild())
    assert len(findings) == 1
    assert findings[0].status == MISSING  # required spec + no row available


# ---------------------------------------------------------------------------
# Module invariants — pure read, no DB writes, no Discord create
# ---------------------------------------------------------------------------


def test_resource_health_module_has_no_db_write_imports():
    import services.resource_health as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # Allowed: ``from utils.db import bindings as bindings_db``.
    # Forbidden: any other ``utils.db`` import — bindings_db.list_for_guild
    # is the only DB API we call, and it is read-only.
    forbidden_writes = (
        "upsert_with_audit",
        "clear_with_audit",
        "set_value_with_audit",
        "delete_active_bindings_for_guild",
    )
    for needle in forbidden_writes:
        assert needle not in text, (
            f"services.resource_health imports {needle}; it must remain "
            "read-only (no DB mutations)."
        )


def test_resource_health_module_has_no_discord_create_calls():
    import services.resource_health as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    forbidden_creates = (
        "ensure_channel",
        "ensure_role",
        "ensure_category",
        "create_text_channel",
        "create_role",
        "create_category",
    )
    for needle in forbidden_creates:
        assert needle not in text, (
            f"services.resource_health references {needle}; it must remain "
            "read-only (no Discord resource creation)."
        )


def test_resource_health_finding_is_frozen():
    """The dataclass must be frozen so consumers can put it in sets/dicts
    and so the contract value can't be mutated downstream."""
    finding = ResourceHealthFinding(
        subsystem="xp",
        binding_name="announce",
        kind=BindingKind.CHANNEL,
        status=OK,
        severity=SEV_INFO,
        message="ok",
    )
    with pytest.raises((AttributeError, TypeError)):
        finding.status = STALE_BINDING  # type: ignore[misc]


def test_status_codes_and_severities_match_documented_set():
    from services.resource_health import SEVERITIES, STATUS_CODES

    assert STATUS_CODES == frozenset(
        {
            OK,
            NOT_CONFIGURED,
            MISSING,
            UNBOUND,
            STALE_BINDING,
            WRONG_TYPE,
            PERMISSION_BLOCKED,
            HIERARCHY_BLOCKED,
            UNKNOWN,
        },
    )
    assert SEVERITIES == frozenset({SEV_INFO, SEV_WARN, SEV_ERROR})
