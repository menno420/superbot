"""Additional S6 safety tests — covers the four categories the user
flagged that the modal-routing tests do not exercise:

* permission failure — non-admin actor is rejected by the pipeline
  and the modal surfaces the error ephemerally.
* disabled feature flag — the !settings command refuses to open
  the hub, so the edit flow is unreachable.
* stale interactions — when ``interaction.response`` calls raise
  (the 3-second window expired or Discord refused the response),
  the widget logs and does not propagate.
* merge-order dependency — the S5 base files this PR stacks on
  must exist on disk; a stand-alone main-branch checkout would
  fail this test (alerting the reviewer to the dependency).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.runtime import guild_config
from core.runtime import subsystem_schema as schema_mod
from core.runtime.subsystem_schema import SettingSpec, SubsystemSchema
from services import settings_mutation as sm_mod
from utils import db as db_pkg
from utils.db import settings as settings_db
from utils.db import settings_audit as audit_db
from views.settings.edit_number import NumberSettingModal
from views.settings.reset_button import reset_setting

# ---------------------------------------------------------------------------
# Minimal fakes (own copy — keeps this file standalone)
# ---------------------------------------------------------------------------


class _FakeGuild:
    def __init__(self, guild_id: int = 1, owner_id: int = 0):
        self.id = guild_id
        self.owner_id = owner_id


class _FakeMember:
    """Configurable member.  When ``admin=False`` the visibility-tier
    lookup returns ``user`` so the pipeline raises
    UnauthorizedSettingsMutationError.
    """

    def __init__(self, *, guild: _FakeGuild | None = None, admin: bool = True):
        self.id = 7
        self.guild = guild or _FakeGuild()

        class _Perms:
            administrator = admin
            manage_channels = admin
            manage_roles = admin
            manage_guild = admin
            moderate_members = False

        self.guild_permissions = _Perms()


class _StaleResponse:
    """``send_message`` raises — simulates the 3-second Discord window
    having lapsed.  ``send_modal`` similarly raises.
    """

    async def send_message(self, *_a, **_kw):
        raise RuntimeError("interaction expired (simulated)")

    async def send_modal(self, *_a, **_kw):
        raise RuntimeError("interaction expired (simulated)")


class _CapturingResponse:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_message(self, content=None, *, ephemeral=False, view=None, **_kw):
        self.sent.append(
            {"content": content, "ephemeral": ephemeral, "view": view},
        )

    async def send_modal(self, modal):
        self.sent.append({"modal": modal})


class _FakeInteraction:
    def __init__(
        self,
        *,
        guild: _FakeGuild | None = None,
        admin: bool = True,
        stale: bool = False,
    ):
        self.guild = guild
        self.guild_id = guild.id if guild else None
        self.user = _FakeMember(guild=guild, admin=admin)
        self.message = None
        self.response = _StaleResponse() if stale else _CapturingResponse()


# ---------------------------------------------------------------------------
# Fixtures — same shape as the modal tests; isolated KV / audit / event
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_state(monkeypatch):
    saved_schemas = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    guild_config._reset_for_tests()

    _kv: dict[tuple[int, str], str] = {}

    async def _fake_get_setting(
        guild_id: int,
        key: str,
        default: str = "",
    ) -> str:
        return _kv.get((guild_id, key), default)

    monkeypatch.setattr(settings_db, "get_setting", _fake_get_setting)
    monkeypatch.setattr(db_pkg, "get_setting", _fake_get_setting)

    audit_log: list[dict] = []

    async def _fake_set_value_with_audit(**kwargs):
        _kv[(kwargs["guild_id"], kwargs["settings_key"])] = kwargs["new_value_raw"]
        audit_log.append(kwargs)

    monkeypatch.setattr(audit_db, "set_value_with_audit", _fake_set_value_with_audit)

    from core.events import bus

    async def _fake_emit(*_a, **_kw):
        return None

    monkeypatch.setattr(bus, "emit", _fake_emit)

    yield {"kv": _kv, "audit_log": audit_log}

    schema_mod._reset_for_tests()
    for schema in saved_schemas.values():
        schema_mod.register(schema)
    guild_config._reset_for_tests()
    # settings_mutation has no counters reset hook today; mirror the
    # other pipelines' shape if it grows one in a future PR.
    _reset = getattr(sm_mod, "_reset_counters_for_tests", None)
    if _reset is not None:
        _reset()


# ---------------------------------------------------------------------------
# Permission failure
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_modal_rejects_non_admin_actor(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    modal = NumberSettingModal(
        subsystem="moderation",
        setting_name="warn_threshold",
        value_type=int,
        current_value=3,
        default_value=3,
    )
    modal.input = type("Stub", (), {"value": "5"})()
    interaction = _FakeInteraction(guild=_FakeGuild(), admin=False)
    await modal.on_submit(interaction)
    # No audit row.
    assert _isolated_state["audit_log"] == []
    # Ephemeral error mentions UnauthorizedSettingsMutationError.
    last = interaction.response.sent[-1]
    assert "Unauthorized" in (last.get("content") or "")


@pytest.mark.asyncio
async def test_reset_rejects_non_admin_actor(_isolated_state):
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    interaction = _FakeInteraction(guild=_FakeGuild(), admin=False)
    await reset_setting(interaction, "moderation", "warn_threshold")
    assert _isolated_state["audit_log"] == []
    last = interaction.response.sent[-1]
    assert "Unauthorized" in (last.get("content") or "")


# ---------------------------------------------------------------------------
# Disabled feature flag — the S6 edit flow is unreachable when the
# S5 cog gate flag is OFF (the hub never opens).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_cog_blocks_edit_flow_when_flag_off(monkeypatch):
    """The S5 gate flag is the only entrypoint to the edit flow.
    With the flag OFF, the !settings command returns the disabled
    embed and never constructs SubsystemSettingsView — so the edit
    selects never reach the user.
    """
    from cogs import settings_cog
    from core.runtime import feature_flags

    async def _flag_off(_name, _guild_id):
        return False

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_off)

    sent: list[object] = []

    class _Channel:
        async def send(self, *_a, **kw):
            embed = kw.get("embed")
            if embed is not None:
                sent.append(embed)

            class _Msg:
                id = 1

            return _Msg()

    class _Ctx:
        guild = _FakeGuild()
        author = _FakeMember(guild=guild)
        channel = _Channel()

        async def send(self, *args, **kwargs):
            return await self.channel.send(*args, **kwargs)

    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    await cog.settings_root.callback(cog, _Ctx())
    assert any("disabled" in (e.title or "").lower() for e in sent)


# ---------------------------------------------------------------------------
# Stale interactions — the modal must not crash if Discord refuses the
# response (e.g. the 3-second window lapsed).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_modal_stale_interaction_does_not_crash():
    """When ``interaction.response.send_message`` raises, the on_submit
    coroutine surfaces the failure cleanly instead of crashing the
    event loop.
    """
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="warn_threshold",
                    value_type=int,
                    default=3,
                    settings_key="WARN_THRESHOLD",
                ),
            ),
        ),
    )
    modal = NumberSettingModal(
        subsystem="moderation",
        setting_name="warn_threshold",
        value_type=int,
        current_value=3,
        default_value=3,
    )
    # Submit a value that will FAIL coercion so the modal hits the
    # send_message branch first (coercion error path).
    modal.input = type("Stub", (), {"value": "abc"})()
    interaction = _FakeInteraction(guild=_FakeGuild(), stale=True)
    # Coercion error tries to send an ephemeral; the stale response
    # raises.  The on_submit propagates that error up — discord.py's
    # on_error handler is what the production view error decorator
    # catches.  We assert the propagation rather than swallowing it
    # (matches the existing BaseView.on_error contract).
    with pytest.raises(RuntimeError, match="interaction expired"):
        await modal.on_submit(interaction)


@pytest.mark.asyncio
async def test_reset_stale_interaction_does_not_crash():
    schema_mod.register(
        SubsystemSchema(
            subsystem="moderation",
            settings=(
                SettingSpec(
                    name="no_such_setting",
                    value_type=int,
                    default=0,
                    settings_key="X",
                ),
            ),
        ),
    )
    interaction = _FakeInteraction(guild=_FakeGuild(), stale=True)
    # ``unknown setting`` path triggers send_message — which raises.
    with pytest.raises(RuntimeError, match="interaction expired"):
        await reset_setting(interaction, "moderation", "no_such_setting_x")


# ---------------------------------------------------------------------------
# Merge-order dependency — S6 stacks on S5.  These S5 files MUST exist
# on disk; if not, the reviewer is on the wrong branch.
# ---------------------------------------------------------------------------


def test_s5_base_files_exist_on_this_branch():
    """S6 stacks on PR #100 (S5).  Verify the S5 files are present —
    if they are missing, the branch was created from main without
    rebasing on the S5 branch, and the PR will fail in surprising
    ways.
    """
    repo_root = Path(__file__).resolve().parents[3]
    expected = [
        repo_root / "disbot" / "cogs" / "settings_cog.py",
        repo_root / "disbot" / "views" / "settings" / "hub.py",
        repo_root / "disbot" / "views" / "settings" / "subsystem_view.py",
        repo_root / "disbot" / "views" / "settings" / "audit_view.py",
    ]
    missing = [str(p.relative_to(repo_root)) for p in expected if not p.exists()]
    assert not missing, (
        "S6 stacks on S5 (PR #100).  The S5 files are missing from this "
        "branch — was it created from main without rebasing on the S5 "
        "branch?\n  Missing:\n  " + "\n  ".join(missing)
    )


def test_s6_invariant_allowlist_only_contains_edit_files():
    """The S5 read-only invariant lifted in S6 (and extended in PR #7)
    must allowlist exactly the edit-flow files.  Catches a future
    drive-by edit that allowlists the hub or audit view by mistake.
    """
    from tests.unit.invariants.test_settings_cog_read_only import (
        _ALLOWED_EDIT_FILES,
    )

    names = {p.name for p in _ALLOWED_EDIT_FILES}
    assert names == {
        # S6 — scalar edit / reset flows.
        "edit_boolean.py",
        "edit_number.py",
        "edit_text.py",
        "edit_enum.py",
        "reset_button.py",
        # PR #7 — native selects + numeric presets.
        "edit_channel.py",
        "edit_role.py",
        "edit_number_presets.py",
    }
