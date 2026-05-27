"""Unit tests for services.bot_knowledge_service.

The service composes ``bot_*`` reference blocks for the AI cog. PR1
verifies:

* Intent gating (catalog block only on meta-questions, audit block
  only on why-no-reply questions).
* Trigger regex correctness (URLs, dates, fractions, ``and/or`` do
  NOT trigger the slash regex; bare punctuation does NOT trigger the
  prefix regex).
* Tier filtering (user, moderator, administrator; owner remains
  hidden in PR1; unknown caller tier defaults to user; unknown
  command visibility tier is dropped).
* Hard size bounds (entry cap, character cap).
* Audit privacy (current-channel preferred; cautious wording on
  guild fallback; inaccessible channels redacted; other users' rows
  filtered).
* ``resolve_user_tier`` mapping from Discord permissions.
"""

from __future__ import annotations

import datetime as _datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.runtime import command_descriptions
from core.runtime.command_descriptions import (
    CommandDescription,
    CommandDescriptionCatalog,
)
from services import bot_knowledge_service
from services.bot_knowledge_service import (
    looks_like_audit_question,
    looks_like_command_question,
    resolve_user_tier,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _entry(
    qualified_name: str,
    *,
    kind: str = "prefix",
    description: str = "desc",
    signature: str = "",
    subsystem: str | None = "economy",
    visibility_tier: str | None = "user",
) -> CommandDescription:
    display = f"!{qualified_name}" if kind == "prefix" else f"/{qualified_name}"
    return CommandDescription(
        qualified_name=qualified_name,
        display_name=display,
        kind=kind,
        description=description,
        signature=signature,
        subsystem=subsystem,
        visibility_tier=visibility_tier,
        requires_perms=(),
    )


def _catalog(entries: tuple[CommandDescription, ...]) -> CommandDescriptionCatalog:
    return CommandDescriptionCatalog(
        entries=entries,
        built_at=_datetime.datetime(2026, 5, 27, tzinfo=_datetime.timezone.utc),
        skipped_count=0,
        hidden_skipped=0,
        error_skipped=0,
    )


@pytest.fixture(autouse=True)
def _reset_catalog():
    command_descriptions._reset_for_tests()
    yield
    command_descriptions._reset_for_tests()


def _install_catalog(monkeypatch, entries: tuple[CommandDescription, ...]) -> None:
    cat = _catalog(entries)
    monkeypatch.setattr(command_descriptions, "get_cached_catalog", lambda: cat)


# ---------------------------------------------------------------------------
# Intent triggers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "what does !btd6 ask do",
        "what is the command for daily",
        "help me",
        "how do i use the panel",
        "can you do something",
        "!btd6 ask",
        "foo !btd6 ask",
        "/btd6 ask",
        "can I use /btd6 ask",
    ],
)
def test_looks_like_command_question_matches(text: str) -> None:
    assert looks_like_command_question(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "hello there",
        "see https://x.test/path",
        "file at /etc/hosts",
        "date 2026/05/27",
        "1/2 of users",
        "and/or",
        "wow!",
        "yes!!",
        "hi! how are you",
        "",
    ],
)
def test_looks_like_command_question_ignores_non_command_text(text: str) -> None:
    assert looks_like_command_question(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "why didn't you reply",
        "why didnt you reply",
        "why no response",
        "why no reply",
        "you ignored me",
        "you denied me",
        "did not respond",
        "didnt reply",
        "you didn't reply to me",
    ],
)
def test_looks_like_audit_question_matches(text: str) -> None:
    assert looks_like_audit_question(text) is True


@pytest.mark.parametrize(
    "text",
    [
        "hello",
        "what does !btd6 ask do",
        "",
    ],
)
def test_looks_like_audit_question_ignores_non_audit_text(text: str) -> None:
    assert looks_like_audit_question(text) is False


# ---------------------------------------------------------------------------
# resolve_user_tier
# ---------------------------------------------------------------------------


def _member(*, administrator: bool = False, manage_guild: bool = False):
    perms = SimpleNamespace(administrator=administrator, manage_guild=manage_guild)
    return SimpleNamespace(guild_permissions=perms)


def test_resolve_user_tier_admin() -> None:
    assert resolve_user_tier(_member(administrator=True)) == "administrator"


def test_resolve_user_tier_moderator() -> None:
    assert resolve_user_tier(_member(manage_guild=True)) == "moderator"


def test_resolve_user_tier_user() -> None:
    assert resolve_user_tier(_member()) == "user"


def test_resolve_user_tier_dm_member_has_no_guild_permissions() -> None:
    """A DMChannel author has no ``guild_permissions`` attribute."""
    bare = SimpleNamespace()
    assert resolve_user_tier(bare) == "user"


# ---------------------------------------------------------------------------
# Catalog block — tier filtering, bounds, subsystem rules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gather_includes_catalog_only_on_meta_intent(monkeypatch) -> None:
    _install_catalog(monkeypatch, (_entry("daily", description="get reward"),))

    blocks_no = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=2,
        user_id=3,
        user_text="hello there",
        user_tier="user",
        accessible_channel_ids=frozenset(),
    )
    assert blocks_no == ()

    blocks_yes = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=2,
        user_id=3,
        user_text="what does !btd6 ask do",
        user_tier="user",
        accessible_channel_ids=frozenset(),
    )
    assert len(blocks_yes) == 1
    assert blocks_yes[0].kind == "bot_command_catalog"


@pytest.mark.asyncio
async def test_catalog_filters_to_user_tier(monkeypatch) -> None:
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", visibility_tier="user"),
            _entry("warn", visibility_tier="administrator"),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="user",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert "!daily" in block.text
    assert "!warn" not in block.text


@pytest.mark.asyncio
async def test_catalog_admin_sees_administrator_and_lower_tiers(monkeypatch) -> None:
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", visibility_tier="user"),
            _entry("warn", visibility_tier="moderator"),
            _entry("config", visibility_tier="administrator"),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="administrator",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert "!daily" in block.text
    assert "!warn" in block.text
    assert "!config" in block.text


@pytest.mark.asyncio
async def test_catalog_administrator_does_not_see_owner_tier(monkeypatch) -> None:
    """PR1 cannot resolve the owner tier, so even an administrator
    must NOT see owner-tier entries."""
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", visibility_tier="user"),
            _entry("owner_only", visibility_tier="owner"),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="administrator",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert "!daily" in block.text
    assert "!owner_only" not in block.text


@pytest.mark.asyncio
async def test_unknown_caller_tier_defaults_to_user_does_not_raise(
    monkeypatch,
) -> None:
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", visibility_tier="user"),
            _entry("warn", visibility_tier="administrator"),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="gibberish",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    # Unknown tier defaults DOWN to user — admin-only entries stay hidden.
    assert "!daily" in block.text
    assert "!warn" not in block.text


@pytest.mark.asyncio
async def test_unknown_command_visibility_tier_is_hidden(monkeypatch) -> None:
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", visibility_tier="user"),
            _entry("weird", visibility_tier="ultra"),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="administrator",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert "!daily" in block.text
    assert "!weird" not in block.text


@pytest.mark.asyncio
async def test_catalog_hides_entries_with_unknown_subsystem(monkeypatch) -> None:
    _install_catalog(
        monkeypatch,
        (
            _entry("daily", subsystem="economy", visibility_tier="user"),
            _entry("ghost", subsystem=None, visibility_tier=None),
        ),
    )

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="user",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert "!daily" in block.text
    assert "!ghost" not in block.text


@pytest.mark.asyncio
async def test_catalog_truncates_at_entry_cap(monkeypatch) -> None:
    entries = tuple(_entry(f"cmd{i:03d}") for i in range(60))
    _install_catalog(monkeypatch, entries)

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="user",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    visible_count = block.text.count("\n- !cmd")
    assert visible_count == 40
    assert "40 of 60" in block.text


@pytest.mark.asyncio
async def test_catalog_truncates_at_char_cap(monkeypatch) -> None:
    long_desc = "lorem ipsum dolor sit amet " * 20  # ≈ 540 chars
    entries = tuple(_entry(f"cmd{i:03d}", description=long_desc) for i in range(30))
    _install_catalog(monkeypatch, entries)

    block = (
        await bot_knowledge_service.gather(
            guild_id=1,
            channel_id=2,
            user_id=3,
            user_text="help",
            user_tier="user",
            accessible_channel_ids=frozenset(),
        )
    )[0]
    assert len(block.text) <= 4500  # margin over the 4000-char cap header
    assert "Showing" in block.text  # truncation notice present


@pytest.mark.asyncio
async def test_catalog_returns_none_when_catalog_unbuilt(monkeypatch) -> None:
    monkeypatch.setattr(command_descriptions, "get_cached_catalog", lambda: None)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=2,
        user_id=3,
        user_text="help",
        user_tier="user",
        accessible_channel_ids=frozenset(),
    )
    assert blocks == ()


# ---------------------------------------------------------------------------
# Audit block — current-channel preference, fallback wording, redaction
# ---------------------------------------------------------------------------


def _audit_row(
    *,
    user_id: int = 42,
    channel_id: int = 100,
    decision: str = "denied",
    reason_code: str = "below_min_level",
    task: str = "general.nl_answer",
    route: str = "general",
    created_at: _datetime.datetime | None = None,
) -> dict:
    return {
        "user_id": user_id,
        "channel_id": channel_id,
        "decision": decision,
        "reason_code": reason_code,
        "task": task,
        "route": route,
        "created_at": created_at
        or _datetime.datetime(2026, 5, 27, 12, 0, tzinfo=_datetime.timezone.utc),
    }


def _audit_mock(side_effect):
    """Build an AsyncMock that consults ``side_effect`` per-call."""
    return AsyncMock(side_effect=side_effect)


@pytest.mark.asyncio
async def test_gather_includes_audit_only_on_why_intent(monkeypatch) -> None:
    from services import ai_decision_audit_service

    queries: list[dict] = []

    async def query(guild_id, **kwargs):
        queries.append({"guild_id": guild_id, **kwargs})
        return [_audit_row(channel_id=100)]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks_no = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="hello",
        user_tier="user",
        accessible_channel_ids=frozenset(),
    )
    assert blocks_no == ()
    assert queries == []  # not even queried when intent is missing

    blocks_yes = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset(),
    )
    assert len(blocks_yes) == 1
    assert blocks_yes[0].kind == "bot_user_audit"


@pytest.mark.asyncio
async def test_audit_block_prefers_current_channel(monkeypatch) -> None:
    from services import ai_decision_audit_service

    current_row = _audit_row(channel_id=100, reason_code="here_reason")
    other_row = _audit_row(channel_id=200, reason_code="elsewhere_reason")

    async def query(_guild_id, **kwargs):
        if kwargs.get("channel_id") == 100:
            return [current_row]
        return [other_row]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100, 200}),
    )
    assert len(blocks) == 1
    text = blocks[0].text
    assert "in this channel" in text
    assert "here_reason" in text
    assert "Your most recent AI interaction in this channel" in text


@pytest.mark.asyncio
async def test_audit_block_falls_back_guild_wide(monkeypatch) -> None:
    from services import ai_decision_audit_service

    async def query(_guild_id, **kwargs):
        if kwargs.get("channel_id") == 100:
            return []  # nothing in current channel
        return [_audit_row(channel_id=200, reason_code="elsewhere_reason")]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100, 200}),
    )
    assert len(blocks) == 1
    text = blocks[0].text
    assert "<#200>" in text
    assert "I didn't find a recent non-reply for you in this channel" in text


@pytest.mark.asyncio
async def test_audit_block_guild_fallback_does_not_overclaim(monkeypatch) -> None:
    """Guild-fallback wording must not pretend to know the asker's
    actual last message — only that the most recent non-reply lives
    elsewhere in this guild."""
    from services import ai_decision_audit_service

    async def query(_guild_id, **kwargs):
        if kwargs.get("channel_id") == 100:
            return []
        return [_audit_row(channel_id=200)]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100, 200}),
    )
    text = blocks[0].text
    assert "your last message" not in text.lower()
    assert "definitely" not in text.lower()
    assert "I didn't find a recent non-reply for you in this channel" in text


@pytest.mark.asyncio
async def test_audit_block_inaccessible_channel_redacted(monkeypatch) -> None:
    from services import ai_decision_audit_service

    async def query(_guild_id, **kwargs):
        if kwargs.get("channel_id") == 100:
            return []
        return [_audit_row(channel_id=999)]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100}),  # 999 not in this set
    )
    text = blocks[0].text
    assert "in another channel (not accessible)" in text
    assert "999" not in text
    assert "<#" not in text


@pytest.mark.asyncio
async def test_audit_block_never_includes_other_users_rows(monkeypatch) -> None:
    """The audit query must be filtered by the asker's user_id, AND
    the implementation must drop any returned row whose ``user_id``
    doesn't match (defense-in-depth)."""
    from services import ai_decision_audit_service

    query_calls: list[dict] = []

    async def query(guild_id, **kwargs):
        query_calls.append({"guild_id": guild_id, **kwargs})
        # Mix a foreign user's row in to verify the filter works.
        return [
            _audit_row(user_id=999, channel_id=100),
            _audit_row(user_id=42, channel_id=100, reason_code="mine"),
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100}),
    )
    text = blocks[0].text
    assert "mine" in text
    assert "999" not in text
    # The audit service was asked to filter by the asker's user_id.
    assert all(call.get("user_id") == 42 for call in query_calls)


@pytest.mark.asyncio
async def test_audit_block_handles_missing_optional_fields(monkeypatch) -> None:
    """Audit rows with missing optional fields still render — the
    block falls back to ``unknown`` rather than raising."""
    from services import ai_decision_audit_service

    sparse_row = {
        "user_id": 42,
        "channel_id": 100,
        "decision": "denied",
        # No reason_code, no task, no route, no created_at.
    }

    async def query(_guild_id, **_kwargs):
        return [sparse_row]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100}),
    )
    text = blocks[0].text
    assert "reason=unknown" in text
    assert "task=unknown" in text
    assert "route=unknown" in text


@pytest.mark.asyncio
async def test_audit_block_only_replied_rows_returns_none(monkeypatch) -> None:
    from services import ai_decision_audit_service

    async def query(_guild_id, **_kwargs):
        return [_audit_row(decision="replied"), _audit_row(decision="allowed")]

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100}),
    )
    assert blocks == ()


@pytest.mark.asyncio
async def test_audit_block_swallows_query_failure(monkeypatch) -> None:
    """A failing audit query must not poison the AI reply path."""
    from services import ai_decision_audit_service

    async def query(_guild_id, **_kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(ai_decision_audit_service, "query", query)

    blocks = await bot_knowledge_service.gather(
        guild_id=1,
        channel_id=100,
        user_id=42,
        user_text="why didn't you reply",
        user_tier="user",
        accessible_channel_ids=frozenset({100}),
    )
    assert blocks == ()
