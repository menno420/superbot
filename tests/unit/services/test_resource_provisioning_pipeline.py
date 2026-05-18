"""Unit tests for services.resource_provisioning — S4.5.

Covers the 11-step pipeline contract: catalogue resolution, actor /
authority validation, bot-permission check, preview (no side
effects), confirmation gating, use_existing happy path, create happy
path, kind mismatch, Discord-API failure, binding failure (resource
NOT rolled back), audit row contents, best-effort event emission,
typed result.

Every DB / Discord / event-bus boundary is monkeypatched so the
tests never touch a real database, Discord guild, or asyncio loop
outside the pipeline itself.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from core.runtime import subsystem_schema as schema_mod
from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services import binding_mutation as bm_mod
from services import resource_provisioning as rp_mod
from services import resource_provisioning_catalogue as rpc_mod
from services.resource_provisioning import (
    DiscordProvisioningFailedError,
    InvalidActorTypeError,
    KindMismatchError,
    ProvisioningConfirmationRequired,
    ProvisioningPreview,
    ProvisioningRequest,
    ProvisioningResult,
    ResourceProvisioningPipeline,
    UnauthorizedProvisioningError,
    UndeclaredResourceError,
)
from utils.db import resource_provisioning_audit as audit_db

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@dataclass
class _FakePermissions:
    administrator: bool = True
    manage_channels: bool = True
    manage_roles: bool = True
    manage_guild: bool = True
    moderate_members: bool = False


@dataclass
class _FakeMe:
    guild_permissions: _FakePermissions


class _FakeRole:
    def __init__(self, role_id: int, name: str):
        self.id = role_id
        self.name = name


class _FakeChannel:
    """Minimal channel stub. ``type.value`` 0/2/5 indicate channel
    (text/voice/announcement) and 4 indicates category.
    """

    def __init__(self, channel_id: int, name: str, kind: str = "text"):
        self.id = channel_id
        self.name = name
        type_value = {"text": 0, "voice": 2, "announcement": 5, "category": 4}[kind]
        self.type = type("T", (), {"value": type_value})()
        self.category_id = None

    async def create(self):  # pragma: no cover — never used in tests
        return self


class _FakeCategory:
    def __init__(self, channel_id: int, name: str):
        self.id = channel_id
        self.name = name


class _FakeGuild:
    def __init__(
        self,
        guild_id: int,
        *,
        owner_id: int = 0,
        channels: list | None = None,
        roles: list | None = None,
        categories: list | None = None,
        permissions: _FakePermissions | None = None,
        create_raises: BaseException | None = None,
    ):
        self.id = guild_id
        self.owner_id = owner_id
        self.channels = list(channels or [])
        self.roles = list(roles or [])
        self.categories = list(categories or [])
        self.text_channels = [c for c in self.channels if c.type.value == 0]
        self.voice_channels = [c for c in self.channels if c.type.value == 2]
        self.me = _FakeMe(guild_permissions=permissions or _FakePermissions())
        self._next_id = 1_000_000
        self._create_raises = create_raises

    def get_channel(self, channel_id: int):
        for ch in self.channels:
            if ch.id == channel_id:
                return ch
        for ch in self.categories:
            if ch.id == channel_id:
                return ch
        return None

    def get_role(self, role_id: int):
        for r in self.roles:
            if r.id == role_id:
                return r
        return None

    async def create_text_channel(self, name, **_kwargs):
        if self._create_raises is not None:
            raise self._create_raises
        self._next_id += 1
        ch = _FakeChannel(self._next_id, name, kind="text")
        self.channels.append(ch)
        self.text_channels.append(ch)
        return ch

    async def create_voice_channel(self, name, **_kwargs):
        if self._create_raises is not None:
            raise self._create_raises
        self._next_id += 1
        ch = _FakeChannel(self._next_id, name, kind="voice")
        self.channels.append(ch)
        self.voice_channels.append(ch)
        return ch

    async def create_category(self, name, **_kwargs):
        if self._create_raises is not None:
            raise self._create_raises
        self._next_id += 1
        cat = _FakeCategory(self._next_id, name)
        self.categories.append(cat)
        return cat

    async def create_role(self, **kwargs):
        if self._create_raises is not None:
            raise self._create_raises
        self._next_id += 1
        role = _FakeRole(self._next_id, kwargs["name"])
        self.roles.append(role)
        return role


class _FakeMember:
    def __init__(self, member_id: int, *, guild: _FakeGuild, admin: bool = True):
        self.id = member_id
        self.guild = guild
        self.guild_permissions = _FakePermissions(administrator=admin)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    rpc_mod._reset_for_tests()

    audit_rows: list[dict] = []

    async def _fake_insert_audit(**kwargs):
        kwargs["id"] = len(audit_rows) + 1
        audit_rows.append(kwargs)
        return kwargs["id"]

    monkeypatch.setattr(audit_db, "insert_audit", _fake_insert_audit)

    binding_calls: list[dict] = []
    binding_raises: dict[str, BaseException | None] = {"exc": None}

    async def _fake_set_binding(
        self,
        guild,
        subsystem,
        binding_name,
        kind,
        target_id,
        actor,
    ):
        binding_calls.append(
            {
                "guild_id": guild.id,
                "subsystem": subsystem,
                "binding_name": binding_name,
                "kind": kind,
                "target_id": target_id,
                "actor_id": getattr(actor, "id", None),
            },
        )
        if binding_raises["exc"] is not None:
            raise binding_raises["exc"]
        return None

    monkeypatch.setattr(
        bm_mod.BindingMutationPipeline,
        "set_binding",
        _fake_set_binding,
    )

    emitted: list[dict] = []
    bus_raises: dict[str, bool] = {"flag": False}

    async def _fake_emit(event: str, /, **payload):
        if bus_raises["flag"]:
            raise RuntimeError("simulated bus failure")
        emitted.append({"event": event, **payload})

    from core.events import bus

    monkeypatch.setattr(bus, "emit", _fake_emit)

    yield {
        "audit_rows": audit_rows,
        "binding_calls": binding_calls,
        "binding_raises": binding_raises,
        "emitted": emitted,
        "bus_raises": bus_raises,
    }

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    rpc_mod._reset_for_tests()


def _register_logging_with_mod_channel():
    schema_mod.register(
        SubsystemSchema(
            subsystem="logging",
            bindings=(
                BindingSpec(
                    name="mod_channel",
                    kind=BindingKind.CHANNEL,
                    required=False,
                    hint="The mod log channel.",
                    capability_required="logging.settings.configure",
                ),
            ),
            resource_requirements=(
                ResourceRequirement(
                    kind=ResourceKind.CHANNEL,
                    intent="mod_log",
                    provisioning=ProvisioningHint(
                        priority=ProvisioningPriority.RECOMMENDED,
                        suggested_name="mod-logs",
                        suggested_category="Staff",
                    ),
                    binding_name="mod_channel",
                ),
            ),
        ),
    )
    rpc_mod.build_provisioning_catalogue()


def _register_proof_role():
    schema_mod.register(
        SubsystemSchema(
            subsystem="proof_channel",
            bindings=(
                BindingSpec(
                    name="approval_role",
                    kind=BindingKind.ROLE,
                    required=False,
                    hint="Approval role for prize claims.",
                    capability_required="proof_channel.access.grant",
                ),
            ),
            resource_requirements=(
                ResourceRequirement(
                    kind=ResourceKind.ROLE,
                    intent="approval_role",
                    provisioning=ProvisioningHint(
                        priority=ProvisioningPriority.OPTIONAL,
                        suggested_name="prize-approver",
                    ),
                    binding_name="approval_role",
                ),
            ),
        ),
    )
    rpc_mod.build_provisioning_catalogue()


# ---------------------------------------------------------------------------
# Catalogue resolution + early validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_undeclared_resource_when_catalogue_not_built():
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UndeclaredResourceError):
        await pipeline.provision(guild, request, actor, confirmed=True)


@pytest.mark.asyncio
async def test_undeclared_resource_when_pair_not_in_catalogue():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="no_such_binding",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UndeclaredResourceError):
        await pipeline.provision(guild, request, actor, confirmed=True)


@pytest.mark.asyncio
async def test_invalid_actor_type_raises():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(InvalidActorTypeError):
        await pipeline.provision(
            guild,
            request,
            actor,
            confirmed=True,
            actor_type="god_mode",
        )


@pytest.mark.asyncio
async def test_invalid_mode_raises():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="invalid",  # type: ignore[arg-type]
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UndeclaredResourceError):
        await pipeline.provision(guild, request, actor, confirmed=True)


# ---------------------------------------------------------------------------
# Authority validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthorized_when_actor_below_admin():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild, admin=False)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UnauthorizedProvisioningError):
        await pipeline.provision(guild, request, actor, confirmed=True)


@pytest.mark.asyncio
async def test_system_actor_bypasses_authority():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
        custom_name="mod-logs",
    )
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        request,
        None,
        confirmed=True,
        actor_type="system",
    )
    assert result.outcome == "success"


# ---------------------------------------------------------------------------
# Bot-permission check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bot_lacking_manage_channels_blocks_create(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(
        1,
        permissions=_FakePermissions(manage_channels=False),
    )
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
        custom_name="mod-logs",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UnauthorizedProvisioningError):
        await pipeline.provision(guild, request, actor, confirmed=True)
    # Audit row written with permission_blocked.
    assert any(
        r["outcome"] == "permission_blocked" for r in _isolated_state["audit_rows"]
    )
    # No binding write attempted.
    assert _isolated_state["binding_calls"] == []


@pytest.mark.asyncio
async def test_bot_lacking_manage_roles_blocks_role_create(_isolated_state):
    _register_proof_role()
    guild = _FakeGuild(
        1,
        permissions=_FakePermissions(manage_roles=False),
    )
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="proof_channel",
        binding_name="approval_role",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(UnauthorizedProvisioningError):
        await pipeline.provision(guild, request, actor, confirmed=True)
    assert any(
        r["outcome"] == "permission_blocked" for r in _isolated_state["audit_rows"]
    )


# ---------------------------------------------------------------------------
# Confirmation gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_without_confirmed_raises():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
    )
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(ProvisioningConfirmationRequired):
        await pipeline.provision(guild, request, actor, confirmed=False)


@pytest.mark.asyncio
async def test_use_existing_does_not_require_confirmation():
    _register_logging_with_mod_channel()
    existing_channel = _FakeChannel(999, "mod-logs", kind="text")
    guild = _FakeGuild(1, channels=[existing_channel])
    actor = _FakeMember(7, guild=guild)
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="use_existing",
        existing_id=999,
    )
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(guild, request, actor, confirmed=False)
    assert result.outcome == "success"


# ---------------------------------------------------------------------------
# preview()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_preview_create_happy_path():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
    )
    assert isinstance(preview, ProvisioningPreview)
    assert preview.allowed is True
    assert preview.action == "create_new"
    assert preview.target_name == "mod-logs"


@pytest.mark.asyncio
async def test_preview_returns_warning_when_resource_with_name_exists():
    _register_logging_with_mod_channel()
    existing = _FakeChannel(42, "mod-logs", kind="text")
    guild = _FakeGuild(1, channels=[existing])
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
    )
    assert preview.allowed is True
    assert any("already exists" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_preview_blocks_when_catalogue_not_built():
    guild = _FakeGuild(1)
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
        ),
    )
    assert preview.allowed is False
    assert preview.action == "blocked"


@pytest.mark.asyncio
async def test_preview_blocks_when_bot_lacks_permission():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(
        1,
        permissions=_FakePermissions(manage_channels=False),
    )
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
    )
    assert preview.allowed is False
    assert preview.action == "blocked"
    assert any("manage_channels" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_preview_use_existing_resolves_kind():
    _register_logging_with_mod_channel()
    existing = _FakeChannel(123, "old-channel", kind="text")
    guild = _FakeGuild(1, channels=[existing])
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="use_existing",
            existing_id=123,
        ),
    )
    assert preview.allowed is True
    assert preview.action == "reuse_existing"
    assert preview.target_name == "old-channel"


@pytest.mark.asyncio
async def test_preview_use_existing_with_unknown_id_blocks():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    pipeline = ResourceProvisioningPipeline()
    preview = await pipeline.preview(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="use_existing",
            existing_id=999,
        ),
    )
    assert preview.allowed is False
    assert preview.action == "blocked"


# ---------------------------------------------------------------------------
# provision() — create happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_channel_happy_path(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
        actor,
        confirmed=True,
    )
    assert isinstance(result, ProvisioningResult)
    assert result.outcome == "success"
    assert result.created is True
    assert result.binding_written is True
    assert result.event_emitted is True
    assert result.resource_id is not None
    # Audit row recorded the success.
    assert _isolated_state["audit_rows"][-1]["outcome"] == "success"
    # Binding pipeline was called with the new channel id.
    assert _isolated_state["binding_calls"][-1]["target_id"] == result.resource_id
    # Channel actually exists on the fake guild.
    assert any(ch.name == "mod-logs" for ch in guild.text_channels)


@pytest.mark.asyncio
async def test_create_role_happy_path(_isolated_state):
    _register_proof_role()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="proof_channel",
            binding_name="approval_role",
            mode="create",
        ),
        actor,
        confirmed=True,
    )
    assert result.outcome == "success"
    assert result.created is True
    assert any(r.name == "prize-approver" for r in guild.roles)
    assert _isolated_state["binding_calls"][-1]["kind"] == BindingKind.ROLE


@pytest.mark.asyncio
async def test_create_category_happy_path(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="cleanup",
            bindings=(
                BindingSpec(
                    name="staff_category",
                    kind=BindingKind.CATEGORY,
                    required=False,
                    hint="Staff-only category for cleanup tools.",
                    capability_required="cleanup.policy.configure",
                ),
            ),
            resource_requirements=(
                ResourceRequirement(
                    kind=ResourceKind.CATEGORY,
                    intent="staff_category",
                    provisioning=ProvisioningHint(
                        priority=ProvisioningPriority.RECOMMENDED,
                        suggested_name="Staff",
                    ),
                    binding_name="staff_category",
                ),
            ),
        ),
    )
    rpc_mod.build_provisioning_catalogue()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="cleanup",
            binding_name="staff_category",
            mode="create",
        ),
        actor,
        confirmed=True,
    )
    assert result.outcome == "success"
    assert any(c.name == "Staff" for c in guild.categories)


# ---------------------------------------------------------------------------
# provision() — use_existing happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_use_existing_happy_path(_isolated_state):
    _register_logging_with_mod_channel()
    existing = _FakeChannel(123, "pre-existing-logs", kind="text")
    guild = _FakeGuild(1, channels=[existing])
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="use_existing",
            existing_id=123,
        ),
        actor,
    )
    assert result.outcome == "success"
    assert result.created is False
    assert result.resource_id == 123
    # No new channel created on the fake guild.
    assert len(guild.text_channels) == 1


@pytest.mark.asyncio
async def test_use_existing_missing_id_declines(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    request = ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="use_existing",
        existing_id=None,
    )
    with pytest.raises(UndeclaredResourceError):
        await pipeline.provision(guild, request, actor)
    assert _isolated_state["audit_rows"][-1]["outcome"] == "declined"


@pytest.mark.asyncio
async def test_use_existing_unknown_id_declines(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(KindMismatchError):
        await pipeline.provision(
            guild,
            ProvisioningRequest(
                subsystem="logging",
                binding_name="mod_channel",
                mode="use_existing",
                existing_id=99999,
            ),
            actor,
        )
    assert _isolated_state["audit_rows"][-1]["outcome"] == "declined"


# ---------------------------------------------------------------------------
# Discord-API failure → discord_failed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_discord_create_failure_audits_discord_failed(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1, create_raises=RuntimeError("API outage"))
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    with pytest.raises(DiscordProvisioningFailedError):
        await pipeline.provision(
            guild,
            ProvisioningRequest(
                subsystem="logging",
                binding_name="mod_channel",
                mode="create",
                custom_name="mod-logs",
            ),
            actor,
            confirmed=True,
        )
    assert _isolated_state["audit_rows"][-1]["outcome"] == "discord_failed"
    # No binding write attempted.
    assert _isolated_state["binding_calls"] == []


# ---------------------------------------------------------------------------
# Binding failure → binding_failed; resource NOT rolled back
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_binding_failure_does_not_roll_back_resource(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    _isolated_state["binding_raises"]["exc"] = RuntimeError("bind DB down")
    pipeline = ResourceProvisioningPipeline()
    # The pipeline returns ProvisioningResult with outcome="binding_failed"
    # rather than raising — the resource has been created and the
    # operator may want to keep it.
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
        actor,
        confirmed=True,
    )
    assert result.outcome == "binding_failed"
    assert result.created is True
    assert result.binding_written is False
    assert result.event_emitted is False
    # Channel still exists on the guild — no rollback.
    assert any(ch.name == "mod-logs" for ch in guild.text_channels)
    # Audit row captured the failure.
    assert _isolated_state["audit_rows"][-1]["outcome"] == "binding_failed"
    assert _isolated_state["audit_rows"][-1]["resource_id"] == result.resource_id


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_emitted_on_success(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
        actor,
        confirmed=True,
    )
    assert len(_isolated_state["emitted"]) == 1
    payload = _isolated_state["emitted"][0]
    assert payload["event"] == "resource.provisioned"
    assert payload["guild_id"] == 1
    assert payload["subsystem"] == "logging"
    assert payload["binding_name"] == "mod_channel"
    assert payload["kind"] == "channel"
    assert payload["mode"] == "create"
    assert payload["created"] is True
    assert payload["resource_id"] == result.resource_id
    assert "occurred_at" in payload


@pytest.mark.asyncio
async def test_event_emission_failure_swallowed(_isolated_state):
    _register_logging_with_mod_channel()
    _isolated_state["bus_raises"]["flag"] = True
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
        actor,
        confirmed=True,
    )
    # Mutation still successful.
    assert result.outcome == "success"
    assert result.event_emitted is False


# ---------------------------------------------------------------------------
# Result + invariants
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_is_frozen():
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    result = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs",
        ),
        actor,
        confirmed=True,
    )
    with pytest.raises(Exception):
        result.outcome = "permission_blocked"  # type: ignore[misc]


@pytest.mark.asyncio
async def test_distinct_mutation_id_per_call(_isolated_state):
    _register_logging_with_mod_channel()
    guild = _FakeGuild(1)
    actor = _FakeMember(7, guild=guild)
    pipeline = ResourceProvisioningPipeline()
    r1 = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs-1",
        ),
        actor,
        confirmed=True,
    )
    r2 = await pipeline.provision(
        guild,
        ProvisioningRequest(
            subsystem="logging",
            binding_name="mod_channel",
            mode="create",
            custom_name="mod-logs-2",
        ),
        actor,
        confirmed=True,
    )
    assert r1.mutation_id != r2.mutation_id


def test_event_name_registered_in_catalogue():
    from core.events_catalogue import KNOWN_EVENTS

    assert "resource.provisioned" in KNOWN_EVENTS


def test_feature_flag_is_declared_and_default_off():
    from core.runtime.feature_flags import RESOURCE_PROVISIONING_PRIMARY

    assert RESOURCE_PROVISIONING_PRIMARY.name == "resource_provisioning.primary"
    assert RESOURCE_PROVISIONING_PRIMARY.default_value is False


def test_actor_type_allowlist_matches_documented_set():
    assert rp_mod._ALLOWED_ACTOR_TYPES == frozenset(
        {"user", "moderator", "admin", "system", "backfill"},
    )


def test_outcome_allowlist_matches_documented_set():
    assert rp_mod._ALLOWED_OUTCOMES == frozenset(
        {
            "success",
            "permission_blocked",
            "discord_failed",
            "binding_failed",
            "declined",
        },
    )


def test_kind_allowlist_matches_documented_set():
    assert rp_mod._ALLOWED_KINDS == frozenset(
        {"channel", "role", "category", "thread"},
    )


def test_mode_allowlist_matches_documented_set():
    assert rp_mod._ALLOWED_MODES == frozenset({"use_existing", "create"})


# ---------------------------------------------------------------------------
# Helper-level tests: ensure_role / ensure_category idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_role_returns_existing_when_name_matches():
    from core.runtime.guild_resources import ensure_role

    role = _FakeRole(50, "exists")
    guild = _FakeGuild(1, roles=[role])
    out = await ensure_role(guild, "exists")
    assert out is role


@pytest.mark.asyncio
async def test_ensure_role_creates_when_absent():
    from core.runtime.guild_resources import ensure_role

    guild = _FakeGuild(1)
    out = await ensure_role(guild, "freshly-created")
    assert out.name == "freshly-created"
    assert any(r.name == "freshly-created" for r in guild.roles)


@pytest.mark.asyncio
async def test_ensure_category_returns_existing_when_name_matches():
    from core.runtime.guild_resources import ensure_category

    cat = _FakeCategory(99, "Staff")
    guild = _FakeGuild(1, categories=[cat])
    out = await ensure_category(guild, "Staff")
    assert out is cat


@pytest.mark.asyncio
async def test_ensure_category_creates_when_absent():
    from core.runtime.guild_resources import ensure_category

    guild = _FakeGuild(1)
    out = await ensure_category(guild, "Brand New")
    assert out.name == "Brand New"
    assert any(c.name == "Brand New" for c in guild.categories)
