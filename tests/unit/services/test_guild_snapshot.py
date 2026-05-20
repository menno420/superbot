"""Phase 9f / Track 5 PR 11 — guild_snapshot tests.

Pins:

* ``collect`` populates the documented fields from a fake guild.
* The frozen dataclass has exactly the field set we documented;
  any new field is a deliberate edit (caught by the field-name
  pin in :func:`test_documented_fields_match_expected`).
* No excluded field-name token (message_content, members,
  invites, permission_overwrites, etc.) appears anywhere in the
  serialized snapshot.
* Per-channel bot-permission booleans reflect what ``permissions_for``
  returns; the snapshot does **not** expose the raw permission
  matrix.
* Role ``bot_can_manage`` requires both Manage Roles AND the
  role sitting below the bot's top role.
"""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.guild_snapshot import (
    EXCLUDED_FIELD_TOKENS,
    CategoryMeta,
    ChannelMeta,
    GuildSnapshot,
    RoleMeta,
    collect,
    documented_field_names,
)
from services.resource_health import ResourceHealthFinding

# ---------------------------------------------------------------------------
# Fake guild factory
# ---------------------------------------------------------------------------


def _perms(**overrides):
    base = dict(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        manage_channels=True,
        manage_roles=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _channel(*, id, name, topic=None, parent=None, position=0, perms=None):
    perms = perms if perms is not None else _perms()
    ch = MagicMock()
    ch.id = id
    ch.name = name
    ch.topic = topic
    ch.category = parent
    ch.position = position
    ch.permissions_for = MagicMock(return_value=perms)
    return ch


def _category(*, id, name, position=0, perms=None):
    perms = perms if perms is not None else _perms()
    cat = MagicMock()
    cat.id = id
    cat.name = name
    cat.position = position
    cat.permissions_for = MagicMock(return_value=perms)
    return cat


def _role(*, id, name, position):
    role = MagicMock()
    role.id = id
    role.name = name
    role.position = position
    return role


def _me(*, top_role_position=10, manage_roles=True):
    top = SimpleNamespace(position=top_role_position)
    return SimpleNamespace(
        top_role=top,
        guild_permissions=_perms(manage_roles=manage_roles),
    )


def _guild(
    *,
    id=1,
    name="Test Guild",
    owner_id=99,
    text_channels=(),
    voice_channels=(),
    stage_channels=(),
    categories=(),
    roles=(),
    me=None,
):
    g = MagicMock()
    g.id = id
    g.name = name
    g.owner_id = owner_id
    g.text_channels = list(text_channels)
    g.voice_channels = list(voice_channels)
    g.stage_channels = list(stage_channels)
    g.categories = list(categories)
    g.roles = list(roles)
    g.me = me if me is not None else _me()
    return g


# ---------------------------------------------------------------------------
# Schema / readiness mocks (shared)
# ---------------------------------------------------------------------------


@pytest.fixture
def _mock_schemas():
    """Stub :func:`core.runtime.subsystem_schema.all_schemas`."""
    from core.runtime.subsystem_schema import (
        BindingKind,
        BindingSpec,
        SettingSpec,
        SubsystemSchema,
    )

    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(
                BindingSpec(
                    name="mod_channel",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="moderation log channel",
                    capability_required="logging.mod_channel.bind",
                ),
            ),
            settings=(
                SettingSpec(
                    name="enabled",
                    value_type=bool,
                    default=False,
                    settings_key="LOGGING_ENABLED",
                ),
            ),
        ),
    }
    with patch(
        "services.guild_snapshot.all_schemas",
        return_value=schemas,
        create=True,  # all_schemas is imported lazily
    ):
        # Lazy import lives inside helpers; patching at the
        # call-site module so the helper imports our stub.
        with (
            patch(
                "core.runtime.subsystem_schema.all_schemas",
                return_value=schemas,
            ),
        ):
            yield schemas


@pytest.fixture
def _mock_resource_health_empty():
    with patch(
        "services.guild_snapshot.inspect_resource_health",
        new_callable=AsyncMock,
        return_value=(),
    ) as mock:
        yield mock


# ---------------------------------------------------------------------------
# Static field set + EXCLUDED_FIELD_TOKENS
# ---------------------------------------------------------------------------


def test_documented_fields_match_expected():
    """Pin the closed field set so an accidental addition is caught."""
    assert set(documented_field_names()) == {
        "guild_id",
        "guild_name",
        "owner_id",
        "channels",
        "categories",
        "roles",
        "settings_snapshot",
        "bindings_snapshot",
        "readiness_findings",
    }


def test_excluded_tokens_cover_documented_privacy_categories():
    """The privacy-test token set must include each documented
    category from the module docstring."""
    must_include = {
        "message_content",
        "members",
        "member_count",
        "invites",
        "permission_overwrites",
    }
    assert must_include.issubset(EXCLUDED_FIELD_TOKENS)


# ---------------------------------------------------------------------------
# collect: happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_collect_returns_documented_fields(
    _mock_schemas, _mock_resource_health_empty
):
    g = _guild(
        text_channels=[
            _channel(id=100, name="general", topic="welcome", position=1),
        ],
        categories=[_category(id=200, name="Mod", position=1)],
        roles=[_role(id=300, name="@everyone", position=0)],
    )
    snap = await collect(g)
    assert isinstance(snap, GuildSnapshot)
    assert snap.guild_id == g.id
    assert snap.guild_name == g.name
    assert snap.owner_id == g.owner_id
    assert any(isinstance(c, ChannelMeta) for c in snap.channels)
    assert any(isinstance(cat, CategoryMeta) for cat in snap.categories)
    assert any(isinstance(r, RoleMeta) for r in snap.roles)
    # Settings/bindings snapshots include the stubbed schema entries.
    assert "logging.enabled" in snap.settings_snapshot
    assert "logging.mod_channel" in snap.bindings_snapshot
    # readiness empty because the mock returned ()
    assert snap.readiness_findings == ()


@pytest.mark.asyncio
async def test_collect_classifies_channel_types(
    _mock_schemas, _mock_resource_health_empty
):
    g = _guild(
        text_channels=[_channel(id=100, name="text-1")],
        voice_channels=[_channel(id=101, name="voice-1")],
        stage_channels=[_channel(id=102, name="stage-1")],
    )
    snap = await collect(g)
    by_id = {c.id: c.type for c in snap.channels}
    assert by_id[100] == "text"
    assert by_id[101] == "voice"
    assert by_id[102] == "stage"


@pytest.mark.asyncio
async def test_collect_renders_parent_category_name(
    _mock_schemas, _mock_resource_health_empty
):
    cat = _category(id=200, name="Mod")
    ch = _channel(id=100, name="mod-log", parent=cat)
    g = _guild(text_channels=[ch], categories=[cat])
    snap = await collect(g)
    text_ch = next(c for c in snap.channels if c.id == 100)
    assert text_ch.parent_category == "Mod"


@pytest.mark.asyncio
async def test_collect_per_channel_permissions_reflect_permissions_for(
    _mock_schemas, _mock_resource_health_empty
):
    locked = _channel(
        id=100,
        name="locked",
        perms=_perms(send_messages=False, embed_links=False),
    )
    sendable = _channel(id=101, name="ok")
    g = _guild(text_channels=[locked, sendable])
    snap = await collect(g)
    by_id = {c.id: c for c in snap.channels}
    assert by_id[100].bot_can_view is True
    assert by_id[100].bot_can_send is False
    assert by_id[100].bot_can_embed is False
    assert by_id[101].bot_can_send is True


@pytest.mark.asyncio
async def test_collect_role_can_manage_requires_position_below_bot(
    _mock_schemas, _mock_resource_health_empty
):
    above_bot = _role(id=300, name="High", position=20)
    below_bot = _role(id=301, name="Low", position=5)
    g = _guild(roles=[above_bot, below_bot], me=_me(top_role_position=10))
    snap = await collect(g)
    by_id = {r.id: r for r in snap.roles}
    assert by_id[300].bot_can_manage is False
    assert by_id[301].bot_can_manage is True


@pytest.mark.asyncio
async def test_collect_role_can_manage_false_when_bot_lacks_manage_roles(
    _mock_schemas, _mock_resource_health_empty
):
    role = _role(id=300, name="VIP", position=5)
    g = _guild(
        roles=[role],
        me=_me(top_role_position=10, manage_roles=False),
    )
    snap = await collect(g)
    assert snap.roles[0].bot_can_manage is False


@pytest.mark.asyncio
async def test_collect_swallows_resource_health_failure(_mock_schemas):
    g = _guild()
    with patch(
        "services.guild_snapshot.inspect_resource_health",
        new_callable=AsyncMock,
        side_effect=RuntimeError("db down"),
    ):
        snap = await collect(g)
    assert snap.readiness_findings == ()


@pytest.mark.asyncio
async def test_collect_includes_readiness_findings_when_inspection_succeeds(
    _mock_schemas,
):
    from core.runtime.subsystem_schema import BindingKind

    finding = ResourceHealthFinding(
        subsystem="logging",
        binding_name="mod_channel",
        kind=BindingKind.CHANNEL,
        status="ok",
        severity="info",
        message="ok",
    )
    g = _guild()
    with patch(
        "services.guild_snapshot.inspect_resource_health",
        new_callable=AsyncMock,
        return_value=(finding,),
    ):
        snap = await collect(g)
    assert snap.readiness_findings == (finding,)


# ---------------------------------------------------------------------------
# Privacy contract
# ---------------------------------------------------------------------------


def _all_keys(value):
    """Recursively yield every dict key inside a nested asdict output."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _all_keys(v)


@pytest.mark.asyncio
async def test_serialised_snapshot_contains_no_excluded_field_tokens(
    _mock_schemas, _mock_resource_health_empty
):
    """Privacy invariant: the asdict() output of a populated
    snapshot must not contain any key whose name matches an
    excluded-field token."""
    g = _guild(
        text_channels=[
            _channel(
                id=100,
                name="mod-log",
                topic="moderation log",
                parent=_category(id=200, name="Mod"),
            ),
        ],
        categories=[_category(id=200, name="Mod")],
        roles=[_role(id=300, name="VIP", position=5)],
    )
    snap = await collect(g)
    serialised = dataclasses.asdict(snap)

    every_key = list(_all_keys(serialised))
    for token in EXCLUDED_FIELD_TOKENS:
        assert not any(token in key for key in every_key), (
            f"Excluded token {token!r} appeared in serialised snapshot keys: "
            f"{[k for k in every_key if token in k]}"
        )
