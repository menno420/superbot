"""RC-5 — cleanup-policy scope validation.

``GovernanceMutationPipeline`` historically shared one ``_VALID_SCOPE_TYPES``
set between visibility and cleanup writes.  Visibility supports thread scope
(migration 009 added it to ``subsystem_visibility``), but ``cleanup_policies``
deliberately kept its non-thread CHECK constraint, so a thread cleanup write
passed service validation and then failed late at the DB.

These tests pin the split: visibility keeps thread; cleanup rejects it with a
clean ``GovernanceError`` *before* any DB access.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import governance.writes as writes
from governance.models import GovernanceContext
from services.governance_exceptions import GovernanceError


def test_cleanup_scope_set_excludes_thread_but_visibility_includes_it():
    """The two scope sets differ by exactly the thread scope."""
    assert "thread" in writes._VALID_VISIBILITY_SCOPE_TYPES
    assert "thread" not in writes._VALID_CLEANUP_SCOPE_TYPES
    assert (
        writes._VALID_CLEANUP_SCOPE_TYPES
        == writes._VALID_VISIBILITY_SCOPE_TYPES - {"thread"}
    )


def _db_that_must_not_be_touched() -> MagicMock:
    fake_db = MagicMock()
    fake_db.get.side_effect = AssertionError(
        "db.get() must not be called — cleanup scope must be rejected pre-DB",
    )
    return fake_db


@pytest.mark.asyncio
async def test_set_cleanup_policy_rejects_thread_before_db(monkeypatch):
    """A thread scope_type raises GovernanceError before any DB access."""
    fake_db = _db_that_must_not_be_touched()
    monkeypatch.setattr(writes, "db", fake_db)

    ctx = GovernanceContext(guild_id=1, member=None)
    pipeline = writes.GovernanceMutationPipeline()

    with pytest.raises(GovernanceError, match="thread"):
        await pipeline.set_cleanup_policy(ctx, "thread", 999)

    fake_db.get.assert_not_called()


@pytest.mark.asyncio
async def test_set_cleanup_policy_for_scope_wrapper_rejects_thread(monkeypatch):
    """The public module-level wrapper rejects thread scope pre-DB as well."""
    fake_db = _db_that_must_not_be_touched()
    monkeypatch.setattr(writes, "db", fake_db)

    ctx = GovernanceContext(guild_id=1, member=None)

    with pytest.raises(GovernanceError, match="thread"):
        await writes.set_cleanup_policy_for_scope(ctx, "thread", 999)

    fake_db.get.assert_not_called()


@pytest.mark.asyncio
async def test_set_cleanup_policy_rejects_unknown_scope_before_db(monkeypatch):
    """An entirely unknown scope_type is also rejected pre-DB (not just thread)."""
    fake_db = _db_that_must_not_be_touched()
    monkeypatch.setattr(writes, "db", fake_db)

    ctx = GovernanceContext(guild_id=1, member=None)
    pipeline = writes.GovernanceMutationPipeline()

    with pytest.raises(GovernanceError, match="cleanup policy"):
        await pipeline.set_cleanup_policy(ctx, "galaxy", 999)

    fake_db.get.assert_not_called()
