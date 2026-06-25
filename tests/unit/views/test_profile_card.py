"""Read-only ``/myprofile`` profile card (myprofile PR A).

Pins the schema-driven composition of the profile embed, the empty state, the
preference-key convention, the owner-lock, and — the load-bearing invariant —
that PR A imports **no mutation pipeline** (it is read-only; writes arrive in
PR B). The accessors are patched so these stay pure unit tests (no cache/DB).
"""

from __future__ import annotations

import ast
import pathlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import participation_schema
from core.runtime.participation_schema import (
    ParticipationSchema,
    PreferenceSpec,
    PreferenceValueType,
    SubscriptionSpec,
    VisibilityIntent,
)
from utils.user_config_accessors import (
    ParticipationState,
    PreferenceResult,
    VisibilityState,
)
from views.profile import (
    ProfileHomeView,
    build_profile_embed,
    preference_key,
)

_PV = "views.profile.profile_view"


@pytest.fixture(autouse=True)
def _clean_registry():
    """Isolate the participation registry for each test."""
    saved = participation_schema.all_schemas()
    participation_schema._reset_for_tests()
    yield
    participation_schema._reset_for_tests()
    for schema in saved.values():
        participation_schema.register(schema)


def _fake_user(user_id: int = 7, name: str = "Ada") -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        display_name=name,
        display_avatar=SimpleNamespace(url="http://avatar"),
    )


def _sample_schema() -> ParticipationSchema:
    return ParticipationSchema(
        subsystem="xp",
        subscriptions=(
            SubscriptionSpec(
                name="participation",
                description="Earn XP from messages",
                default_enabled=True,
            ),
            SubscriptionSpec(
                name="beta",
                description="Beta features",
                default_enabled=True,
                requires_optin=True,  # effective default off
            ),
        ),
        visibility_intents=(
            VisibilityIntent(name="xp.rank.public", description="Show my rank"),
        ),
        preference_specs=(
            PreferenceSpec(
                name="rank_embed_style",
                description="Rank embed style",
                value_type=PreferenceValueType.ENUM,
                default="standard",
                allowed_values=("standard", "compact"),
            ),
        ),
    )


# ---------------------------------------------------------------------------
# preference_key convention
# ---------------------------------------------------------------------------


def test_preference_key_namespaces_by_subsystem():
    assert preference_key("xp", "rank_embed_style") == "xp.rank_embed_style"
    # Two subsystems with the same short name never collide.
    assert preference_key("games", "style") != preference_key("xp", "style")


# ---------------------------------------------------------------------------
# build_profile_embed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_registry_renders_honest_empty_state():
    embed = await build_profile_embed(_fake_user(), guild_id=99)
    assert len(embed.fields) == 1
    assert "No participation-aware features" in embed.fields[0].name


@pytest.mark.asyncio
async def test_card_composes_one_section_per_subsystem():
    participation_schema.register(_sample_schema())
    with (
        patch(
            f"{_PV}.get_participation",
            new=AsyncMock(return_value=ParticipationState.OPTED_IN),
        ),
        patch(f"{_PV}.is_subscribed", new=AsyncMock(return_value=True)),
        patch(
            f"{_PV}.get_preference",
            new=AsyncMock(return_value=PreferenceResult(value="compact", found=True)),
        ),
        patch(
            f"{_PV}.get_visibility", new=AsyncMock(return_value=VisibilityState.HIDDEN),
        ),
    ):
        embed = await build_profile_embed(_fake_user(), guild_id=99)

    assert len(embed.fields) == 1  # one subsystem
    body = embed.fields[0].value
    assert "opted in" in body
    assert "Earn XP from messages" in body
    assert "Beta features" in body
    assert "Rank embed style" in body
    assert "compact" in body
    assert "hidden" in body


@pytest.mark.asyncio
async def test_unset_values_show_defaults_not_explicit():
    participation_schema.register(_sample_schema())
    with (
        patch(
            f"{_PV}.get_participation",
            new=AsyncMock(return_value=ParticipationState.NOT_SET),
        ),
        patch(
            f"{_PV}.is_subscribed",
            new=AsyncMock(side_effect=lambda *a, **k: k["default"]),
        ),
        patch(
            f"{_PV}.get_preference",
            new=AsyncMock(return_value=PreferenceResult(value="standard", found=False)),
        ),
        patch(
            f"{_PV}.get_visibility", new=AsyncMock(return_value=VisibilityState.DEFAULT),
        ),
    ):
        embed = await build_profile_embed(_fake_user(), guild_id=99)

    body = embed.fields[0].value
    assert "not set (default)" in body
    # requires_optin subscription is effectively off by default
    assert "⬜ Beta features" in body
    # opt-out subscription defaults on
    assert "✅ Earn XP from messages" in body
    assert "(default)" in body  # preference shows default provenance


@pytest.mark.asyncio
async def test_subscription_effective_default_passed_to_accessor():
    """A requires_optin spec must pass default=False to is_subscribed."""
    participation_schema.register(_sample_schema())
    spy = AsyncMock(return_value=False)
    with (
        patch(
            f"{_PV}.get_participation",
            new=AsyncMock(return_value=ParticipationState.NOT_SET),
        ),
        patch(f"{_PV}.is_subscribed", new=spy),
        patch(
            f"{_PV}.get_preference",
            new=AsyncMock(return_value=PreferenceResult(value="standard", found=False)),
        ),
        patch(
            f"{_PV}.get_visibility", new=AsyncMock(return_value=VisibilityState.DEFAULT),
        ),
    ):
        await build_profile_embed(_fake_user(), guild_id=99)

    defaults = {c.args[3]: c.kwargs["default"] for c in spy.await_args_list}
    assert defaults["participation"] is True  # opt-out → default on
    assert defaults["beta"] is False  # requires_optin → effective off


# ---------------------------------------------------------------------------
# ProfileHomeView — owner lock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_view_is_owner_locked():
    author = _fake_user(user_id=1)
    view = ProfileHomeView(author, guild_id=99)

    # Same user passes the lock.
    ok = SimpleNamespace(user=SimpleNamespace(id=1), response=AsyncMock())
    assert await view.interaction_check(ok) is True

    # A different user is rejected.
    intruder = SimpleNamespace(
        user=SimpleNamespace(id=2),
        response=SimpleNamespace(send_message=AsyncMock()),
    )
    assert await view.interaction_check(intruder) is False


# ---------------------------------------------------------------------------
# Card ↔ editor navigation — hero-image attachment hygiene
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_manage_clears_the_hero_card_when_opening_the_editor():
    """Opening the (image-less) editor must drop the card, not strand it.

    Discord keeps the prior attachment when ``attachments`` is omitted on an
    edit, so the profile hero image would linger as a stray image under the
    settings panel. ``manage`` passes ``attachments=[]`` to clear it.
    """
    view = ProfileHomeView(_fake_user(user_id=1), guild_id=99)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=1),
        response=SimpleNamespace(edit_message=AsyncMock()),
    )

    await view.manage.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    assert interaction.response.edit_message.await_args.kwargs["attachments"] == []


# ---------------------------------------------------------------------------
# Read-only invariant — no mutation pipeline import (AST pin)
# ---------------------------------------------------------------------------


def test_profile_view_imports_no_mutation_pipeline():
    src = pathlib.Path("disbot/views/profile/profile_view.py").read_text()
    tree = ast.parse(src)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    assert not any(
        "mutation" in mod for mod in imported
    ), f"PR A profile card must be read-only; found mutation import in {imported}"
