"""Track 2 PR 6 — readiness_repair previews + apply.

Covers:

* ``build_previews`` translates each finding status into the right
  ``RepairPreview.action``.
* ``RepairPreview`` rejects unknown action tokens at construction.
* ``apply_repair`` routes each action through the right mutation
  pipeline service (without performing real DB writes — pipelines
  are mocked at the call site).
* Owner gating: ``create_*`` previews refuse non-owner actor_ids.
* Advisory previews (``open_settings_editor`` /
  ``open_permissions_hint``) return ``OUTCOME_SKIPPED`` without
  touching any pipeline.
* The track-6 placeholder ``create_automation_rule`` returns
  ``OUTCOME_NO_OP``.
* Module is read-only at the import surface: no direct ``utils.db``
  write imports, no direct Discord resource-create calls — every
  write must go through a pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.subsystem_schema import BindingKind
from services.readiness_repair import (
    BIND_EXISTING_CHANNEL,
    BIND_EXISTING_ROLE,
    CLEAR_STALE_BINDING,
    CREATE_AUTOMATION_RULE,
    CREATE_MISSING_CHANNEL,
    CREATE_MISSING_ROLE,
    ENABLE_LOGGING,
    OPEN_PERMISSIONS_HINT,
    OPEN_SETTINGS_EDITOR,
    OUTCOME_NO_OP,
    OUTCOME_OK,
    OUTCOME_PIPELINE_ERROR,
    OUTCOME_SKIPPED,
    OUTCOME_UNAUTHORIZED,
    REPAIR_ACTIONS,
    RepairPreview,
    apply_repair,
    build_previews,
)
from services.resource_health import (
    HIERARCHY_BLOCKED,
    MISSING,
    NOT_CONFIGURED,
    OK,
    PERMISSION_BLOCKED,
    STALE_BINDING,
    UNBOUND,
    UNKNOWN,
    WRONG_TYPE,
    ResourceHealthFinding,
)


def _finding(status: str, *, target_id: int | None = 100, kind=BindingKind.CHANNEL):
    return ResourceHealthFinding(
        subsystem="logging",
        binding_name="mod_channel",
        kind=kind,
        status=status,
        severity="error",
        message=f"{status} on logging.mod_channel",
        target_id=target_id,
    )


# ---------------------------------------------------------------------------
# RepairPreview construction
# ---------------------------------------------------------------------------


def test_repair_preview_rejects_unknown_action():
    with pytest.raises(ValueError, match="unknown repair action"):
        RepairPreview(
            action="totally_made_up",
            finding=_finding(STALE_BINDING),
            description="should fail",
        )


def test_repair_preview_accepts_every_documented_action():
    for action in REPAIR_ACTIONS:
        preview = RepairPreview(
            action=action,
            finding=_finding(STALE_BINDING),
            description="ok",
        )
        assert preview.action == action


# ---------------------------------------------------------------------------
# build_previews mapping
# ---------------------------------------------------------------------------


def test_build_previews_clears_stale_bindings():
    findings = (_finding(STALE_BINDING, target_id=42),)
    previews = build_previews(findings)
    assert len(previews) == 1
    assert previews[0].action == CLEAR_STALE_BINDING
    assert "Clear stale binding" in previews[0].description
    assert "42" in previews[0].description


@pytest.mark.parametrize("status", [UNBOUND, NOT_CONFIGURED, WRONG_TYPE, MISSING])
def test_build_previews_open_settings_editor_for_actionable_misconfig(status):
    findings = (_finding(status),)
    previews = build_previews(findings)
    assert len(previews) == 1
    assert previews[0].action == OPEN_SETTINGS_EDITOR
    assert previews[0].is_advisory is True


@pytest.mark.parametrize("status", [PERMISSION_BLOCKED, HIERARCHY_BLOCKED])
def test_build_previews_open_permissions_hint_for_manual_fixes(status):
    findings = (_finding(status),)
    previews = build_previews(findings)
    assert len(previews) == 1
    assert previews[0].action == OPEN_PERMISSIONS_HINT
    assert previews[0].is_advisory is True


@pytest.mark.parametrize("status", [OK, UNKNOWN])
def test_build_previews_skips_ok_and_unknown(status):
    findings = (_finding(status),)
    previews = build_previews(findings)
    assert previews == ()


def test_build_previews_preserves_finding_count_for_mixed_input():
    findings = (
        _finding(STALE_BINDING),
        _finding(OK),  # dropped
        _finding(UNBOUND),
        _finding(UNKNOWN),  # dropped
        _finding(PERMISSION_BLOCKED),
    )
    previews = build_previews(findings)
    assert [p.action for p in previews] == [
        CLEAR_STALE_BINDING,
        OPEN_SETTINGS_EDITOR,
        OPEN_PERMISSIONS_HINT,
    ]


# ---------------------------------------------------------------------------
# apply_repair — advisory previews are no-ops
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_advisory_settings_editor_returns_skipped():
    preview = RepairPreview(
        action=OPEN_SETTINGS_EDITOR,
        finding=_finding(UNBOUND),
        description="advisory",
        is_advisory=True,
    )
    result = await apply_repair(
        preview, guild=MagicMock(), actor_id=1, guild_owner_id=1
    )
    assert result.outcome == OUTCOME_SKIPPED
    assert result.applied is False
    assert result.mutation_id is None


@pytest.mark.asyncio
async def test_apply_advisory_permissions_hint_returns_skipped():
    preview = RepairPreview(
        action=OPEN_PERMISSIONS_HINT,
        finding=_finding(PERMISSION_BLOCKED),
        description="advisory",
        is_advisory=True,
    )
    result = await apply_repair(
        preview, guild=MagicMock(), actor_id=1, guild_owner_id=1
    )
    assert result.outcome == OUTCOME_SKIPPED


# ---------------------------------------------------------------------------
# apply_repair — owner gating on create_*
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_create_missing_channel_refuses_non_owner():
    preview = RepairPreview(
        action=CREATE_MISSING_CHANNEL,
        finding=_finding(MISSING),
        description="create",
        requires_owner=True,
    )
    result = await apply_repair(
        preview, guild=MagicMock(), actor_id=2, guild_owner_id=1
    )
    assert result.outcome == OUTCOME_UNAUTHORIZED
    assert "guild-owner" in (result.error or "")


@pytest.mark.asyncio
async def test_apply_create_missing_role_refuses_non_owner():
    preview = RepairPreview(
        action=CREATE_MISSING_ROLE,
        finding=_finding(MISSING, kind=BindingKind.ROLE),
        description="create",
        requires_owner=True,
    )
    result = await apply_repair(
        preview, guild=MagicMock(), actor_id=2, guild_owner_id=1
    )
    assert result.outcome == OUTCOME_UNAUTHORIZED


# ---------------------------------------------------------------------------
# apply_repair — routes through the right pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_clear_stale_binding_calls_binding_mutation_pipeline():
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=CLEAR_STALE_BINDING,
        finding=_finding(STALE_BINDING, target_id=42),
        description="clear",
    )
    fake_member = MagicMock(id=99)
    pipeline_mock = MagicMock()
    pipeline_mock.clear_binding = AsyncMock(
        return_value=MagicMock(mutation_id="mut-clear"),
    )

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "core.runtime.subsystem_schema.get_schema",
            return_value=MagicMock(),
        ),
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=99,
            guild_owner_id=1,
        )

    pipeline_mock.clear_binding.assert_awaited_once()
    assert result.outcome == OUTCOME_OK
    assert result.applied is True
    assert result.mutation_id == "mut-clear"


@pytest.mark.asyncio
async def test_apply_bind_existing_channel_calls_set_binding():
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=BIND_EXISTING_CHANNEL,
        finding=_finding(UNBOUND),
        description="bind",
        payload={"target_id": 4242},
    )
    fake_member = MagicMock(id=99)
    pipeline_mock = MagicMock()
    pipeline_mock.set_binding = AsyncMock(
        return_value=MagicMock(mutation_id="mut-bind"),
    )

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=99,
            guild_owner_id=1,
        )

    pipeline_mock.set_binding.assert_awaited_once()
    call = pipeline_mock.set_binding.await_args
    # 5 positional args: guild, subsystem, binding_name, kind, target_id, actor
    assert call.args[1] == "logging"  # subsystem
    assert call.args[2] == "mod_channel"  # binding_name
    assert call.args[4] == 4242  # target_id from payload
    assert result.outcome == OUTCOME_OK


@pytest.mark.asyncio
async def test_apply_bind_existing_channel_rejects_missing_target_id():
    """Without ``payload['target_id']`` the apply must surface a
    pipeline_error instead of silently calling the pipeline with junk."""
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=BIND_EXISTING_CHANNEL,
        finding=_finding(UNBOUND),
        description="bind",
        # payload deliberately empty
    )
    fake_member = MagicMock(id=99)
    pipeline_mock = MagicMock()
    pipeline_mock.set_binding = AsyncMock()

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=99,
            guild_owner_id=1,
        )

    pipeline_mock.set_binding.assert_not_awaited()
    assert result.outcome == OUTCOME_PIPELINE_ERROR
    assert "target_id" in (result.error or "")


@pytest.mark.asyncio
async def test_apply_create_missing_channel_calls_provisioning_pipeline():
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=CREATE_MISSING_CHANNEL,
        finding=_finding(MISSING),
        description="create",
        requires_owner=True,
        payload={"custom_name": "bot-audit-log"},
    )
    fake_member = MagicMock(id=1)
    pipeline_mock = MagicMock()
    pipeline_mock.provision = AsyncMock(
        return_value=MagicMock(mutation_id="mut-create"),
    )

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "services.resource_provisioning.ResourceProvisioningPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=1,
            guild_owner_id=1,
        )

    pipeline_mock.provision.assert_awaited_once()
    # ResourceProvisioningPipeline.provision(guild, request, actor, confirmed=True)
    request = pipeline_mock.provision.await_args.args[1]
    assert request.subsystem == "logging"
    assert request.binding_name == "mod_channel"
    assert request.custom_name == "bot-audit-log"
    assert pipeline_mock.provision.await_args.kwargs["confirmed"] is True
    assert result.outcome == OUTCOME_OK
    assert result.mutation_id == "mut-create"


@pytest.mark.asyncio
async def test_apply_enable_logging_calls_settings_mutation_pipeline():
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=ENABLE_LOGGING,
        finding=_finding(MISSING),
        description="enable",
    )
    fake_member = MagicMock(id=99)
    pipeline_mock = MagicMock()
    pipeline_mock.set_value = AsyncMock(
        return_value=MagicMock(mutation_id="mut-set"),
    )

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "services.settings_mutation.SettingsMutationPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=99,
            guild_owner_id=1,
        )

    pipeline_mock.set_value.assert_awaited_once()
    args = pipeline_mock.set_value.await_args.args
    assert args[1] == "logging"
    assert args[2] == "enabled"
    assert args[3] is True
    assert result.outcome == OUTCOME_OK


@pytest.mark.asyncio
async def test_apply_create_automation_rule_returns_no_op_placeholder():
    """Track-6 placeholder: legal preview, but no apply handler."""
    preview = RepairPreview(
        action=CREATE_AUTOMATION_RULE,
        finding=_finding(MISSING),
        description="automation",
        requires_owner=True,
    )
    result = await apply_repair(
        preview, guild=MagicMock(), actor_id=1, guild_owner_id=1
    )
    assert result.outcome == OUTCOME_NO_OP
    assert "future track" in (result.error or "")


@pytest.mark.asyncio
async def test_apply_propagates_pipeline_failure_as_pipeline_error():
    from services import readiness_repair as rr

    preview = RepairPreview(
        action=CLEAR_STALE_BINDING,
        finding=_finding(STALE_BINDING),
        description="clear",
    )
    fake_member = MagicMock(id=99)
    pipeline_mock = MagicMock()
    pipeline_mock.clear_binding = AsyncMock(side_effect=RuntimeError("db down"))

    with (
        patch.object(rr, "_bridge_actor", return_value=fake_member),
        patch(
            "core.runtime.subsystem_schema.get_schema",
            return_value=MagicMock(),
        ),
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline_mock,
        ),
    ):
        result = await apply_repair(
            preview,
            guild=MagicMock(id=1),
            actor_id=99,
            guild_owner_id=1,
        )

    assert result.outcome == OUTCOME_PIPELINE_ERROR
    assert "db down" in (result.error or "")


# ---------------------------------------------------------------------------
# Module invariants
# ---------------------------------------------------------------------------


def test_readiness_repair_module_has_no_db_write_imports():
    import services.readiness_repair as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # No DB primitive imported at the module level — all writes must
    # go through services.binding_mutation / settings_mutation /
    # resource_provisioning, which are imported lazily inside handlers.
    forbidden_db = ("from utils.db import", "import utils.db")
    for needle in forbidden_db:
        assert needle not in text, (
            f"services.readiness_repair must not import DB primitives at "
            f"the module level; found {needle!r}."
        )


def test_readiness_repair_module_has_no_direct_discord_create_calls():
    import services.readiness_repair as mod

    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    # Direct Discord create calls would bypass the provisioning
    # pipeline (no audit row, no event emission). The only allowed
    # creates are via ResourceProvisioningPipeline.provision().
    forbidden_creates = (
        "create_text_channel",
        "create_voice_channel",
        "create_role",
        "create_category",
    )
    for needle in forbidden_creates:
        assert needle not in text, (
            f"services.readiness_repair must not call {needle} directly; "
            "route through services.resource_provisioning instead."
        )
