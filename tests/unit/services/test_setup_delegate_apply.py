"""Q-0098 — delegated-Setup apply authority (P0-3 arc PR 3).

``services.setup_operations.apply_operations`` is the sole minter of
``actor_type="setup_delegate"``. It resolves the effective actor_type via
``_resolve_apply_actor_type``, which re-verifies the live delegation against a
fresh SetupSession, then threads the resolved type to the three capability-gated
pipelines. These tests drive the REAL ``services.setup_access`` helpers (only
``resume_session`` is faked) so the owner/admin/delegate partition is exercised
end-to-end.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_operations import (
    SetupOperation,
    _resolve_apply_actor_type,
    apply_operations,
)


class _Guild:
    def __init__(self, gid: int = 1, owner_id: int = 99):
        self.id = gid
        self.owner_id = owner_id


class _Perms:
    def __init__(self, administrator: bool = False):
        self.administrator = administrator


class _Member:
    def __init__(self, mid: int, guild: _Guild, *, administrator: bool = False):
        self.id = mid
        self.guild = guild
        self.guild_permissions = _Perms(administrator)


class _Session:
    def __init__(self, delegated: tuple[int, ...] = ()):
        self.delegated_admins = tuple(delegated)


def _patch_resume(monkeypatch, session: _Session | None) -> AsyncMock:
    mock = AsyncMock(return_value=session)
    monkeypatch.setattr("services.setup_session.resume_session", mock)
    return mock


# ---------------------------------------------------------------------------
# _resolve_apply_actor_type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_resolves_to_user_without_session_read(monkeypatch):
    guild = _Guild(owner_id=99)
    owner = _Member(99, guild)
    resume = _patch_resume(monkeypatch, _Session())
    assert await _resolve_apply_actor_type(owner, guild, "user") == "user"
    # Owner clears the floor — no fresh-session read needed.
    resume.assert_not_awaited()


@pytest.mark.asyncio
async def test_administrator_resolves_to_user_without_session_read(monkeypatch):
    guild = _Guild(owner_id=99)
    admin = _Member(5, guild, administrator=True)
    resume = _patch_resume(monkeypatch, _Session())
    assert await _resolve_apply_actor_type(admin, guild, "user") == "user"
    resume.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_admin_delegate_resolves_to_setup_delegate(monkeypatch):
    guild = _Guild(owner_id=99)
    delegate = _Member(7, guild)  # not owner, not admin
    _patch_resume(monkeypatch, _Session(delegated=(7,)))
    assert await _resolve_apply_actor_type(delegate, guild, "user") == "setup_delegate"


@pytest.mark.asyncio
async def test_non_admin_non_delegate_resolves_to_user(monkeypatch):
    guild = _Guild(owner_id=99)
    member = _Member(8, guild)  # not owner, not admin, not delegated
    _patch_resume(monkeypatch, _Session(delegated=(7,)))
    assert await _resolve_apply_actor_type(member, guild, "user") == "user"


@pytest.mark.asyncio
async def test_delegation_lost_resolves_to_user(monkeypatch):
    # Member WAS delegated when Final Review opened, but the fresh session no
    # longer lists them — the live re-check returns "user" and the per-op floor
    # then denies the write.
    guild = _Guild(owner_id=99)
    delegate = _Member(7, guild)
    _patch_resume(monkeypatch, _Session(delegated=()))
    assert await _resolve_apply_actor_type(delegate, guild, "user") == "user"


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit", ["system", "backfill"])
async def test_explicit_non_user_actor_type_passes_through(monkeypatch, explicit):
    guild = _Guild(owner_id=99)
    member = _Member(7, guild)
    resume = _patch_resume(monkeypatch, _Session(delegated=(7,)))
    assert await _resolve_apply_actor_type(member, guild, explicit) == explicit
    resume.assert_not_awaited()


@pytest.mark.asyncio
async def test_session_read_failure_falls_back_to_user(monkeypatch):
    guild = _Guild(owner_id=99)
    delegate = _Member(7, guild)
    monkeypatch.setattr(
        "services.setup_session.resume_session",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    # Resolution never escalates on error — it returns "user" and the floor
    # governs.
    assert await _resolve_apply_actor_type(delegate, guild, "user") == "user"


@pytest.mark.asyncio
async def test_missing_actor_or_guild_passes_through():
    assert await _resolve_apply_actor_type(None, _Guild(), "user") == "user"
    assert await _resolve_apply_actor_type(_Member(7, _Guild()), None, "user") == "user"


# ---------------------------------------------------------------------------
# apply_operations threads the resolved actor_type to the binding pipeline
# ---------------------------------------------------------------------------


def _bind_op() -> SetupOperation:
    return SetupOperation(
        kind="bind_channel",
        subsystem="logging",
        binding_name="mod_log",
        target_kind="channel",
        target_id=555,
    )


@pytest.mark.asyncio
async def test_apply_threads_setup_delegate_to_binding_pipeline(monkeypatch):
    guild = _Guild(owner_id=99)
    delegate = _Member(7, guild)
    _patch_resume(monkeypatch, _Session(delegated=(7,)))

    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(return_value=MagicMock(mutation_id="m-1"))
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([_bind_op()], guild=guild, actor=delegate)

    assert len(batch.applied) == 1
    mock_pipeline.set_binding.assert_awaited_once()
    assert mock_pipeline.set_binding.await_args.kwargs["actor_type"] == "setup_delegate"


@pytest.mark.asyncio
async def test_apply_threads_user_for_owner(monkeypatch):
    guild = _Guild(owner_id=99)
    owner = _Member(99, guild)
    _patch_resume(monkeypatch, _Session())

    mock_pipeline = MagicMock()
    mock_pipeline.set_binding = AsyncMock(return_value=MagicMock(mutation_id="m-2"))
    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=mock_pipeline,
    ):
        batch = await apply_operations([_bind_op()], guild=guild, actor=owner)

    assert len(batch.applied) == 1
    assert mock_pipeline.set_binding.await_args.kwargs["actor_type"] == "user"
