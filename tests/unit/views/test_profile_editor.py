"""Self-service profile editor (myprofile PR B).

Pins the load-bearing write contract: every editor action is **exactly one**
``ParticipationMutationPipeline`` call (mock-spy), typed mutation errors render
as ephemeral copy (never a crash), the unauthorized (actor != subject) path is
reachable copy, and — the AST invariant — the editor writes *only* through the
pipeline service (no direct ``utils.db`` writes).
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
from services.participation_mutation import (
    InvalidPreferenceValueError,
    UnauthorizedParticipationMutationError,
)
from utils.user_config_accessors import (
    ParticipationState,
    PreferenceResult,
    VisibilityState,
)
from views.profile import editor as editor_mod
from views.profile.editor import (
    ProfileEditorHomeView,
    ProfileSubsystemEditorView,
)

_ED = "views.profile.editor"


@pytest.fixture(autouse=True)
def _clean_registry():
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


def _schema() -> ParticipationSchema:
    return ParticipationSchema(
        subsystem="xp",
        subscriptions=(
            SubscriptionSpec(
                name="participation",
                description="Earn XP from messages",
                default_enabled=True,
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
            PreferenceSpec(
                name="digest",
                description="Digest enabled",
                value_type=PreferenceValueType.BOOL,
                default=False,
            ),
            PreferenceSpec(
                name="threshold",
                description="Notify threshold",
                value_type=PreferenceValueType.INT,
                default=5,
            ),
        ),
    )


def _interaction(user_id: int = 7) -> SimpleNamespace:
    return SimpleNamespace(
        user=SimpleNamespace(id=user_id),
        response=SimpleNamespace(
            edit_message=AsyncMock(),
            send_message=AsyncMock(),
            send_modal=AsyncMock(),
        ),
    )


async def _make_editor() -> ProfileSubsystemEditorView:
    participation_schema.register(_schema())
    with (
        patch(
            f"{_ED}.get_participation",
            new=AsyncMock(return_value=ParticipationState.OPTED_IN),
        ),
        patch(
            f"{_ED}.get_visibility",
            new=AsyncMock(return_value=VisibilityState.DEFAULT),
        ),
    ):
        return await ProfileSubsystemEditorView.create(_fake_user(), 99, "xp")


# ---------------------------------------------------------------------------
# Editor home
# ---------------------------------------------------------------------------


def test_home_lists_registered_subsystems():
    participation_schema.register(_schema())
    view = ProfileEditorHomeView(_fake_user(), 99)
    selects = [c for c in view.children if hasattr(c, "options")]
    assert selects, "expected a subsystem select"
    assert any(o.value == "xp" for o in selects[0].options)


def test_home_empty_state_when_no_registrants():
    view = ProfileEditorHomeView(_fake_user(), 99)
    embed = view.build_embed()
    assert "Nothing to manage yet" in embed.fields[0].name


# ---------------------------------------------------------------------------
# One pipeline call per action (mock-spy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_participation_toggle_is_one_pipeline_call():
    view = await _make_editor()  # current state OPTED_IN → opt out
    spy = AsyncMock()
    with (
        patch.object(editor_mod._PIPELINE, "set_participation", spy),
        patch.object(
            ProfileSubsystemEditorView,
            "create",
            new=AsyncMock(return_value=view),
        ),
        patch.object(view, "build_embed", new=AsyncMock(return_value="e")),
    ):
        await view._toggle_participation(_interaction())
    spy.assert_awaited_once()
    assert spy.await_args.kwargs["state"] == "opted_out"
    assert spy.await_args.kwargs["user_id"] == 7
    assert spy.await_args.kwargs["actor_id"] == 7


@pytest.mark.asyncio
async def test_visibility_toggle_flips_to_hidden_from_default():
    view = await _make_editor()  # visibility DEFAULT → hide
    spy = AsyncMock()
    with (
        patch.object(editor_mod._PIPELINE, "set_visibility", spy),
        patch.object(
            ProfileSubsystemEditorView,
            "create",
            new=AsyncMock(return_value=view),
        ),
        patch.object(view, "build_embed", new=AsyncMock(return_value="e")),
    ):
        await view._toggle_visibility(_interaction())
    spy.assert_awaited_once()
    assert spy.await_args.kwargs["visibility"] == "hidden"


@pytest.mark.asyncio
async def test_subscription_select_toggles_off_when_currently_on():
    view = await _make_editor()
    sub_select = next(
        c for c in view.children if getattr(c, "placeholder", "") == "Toggle a subscription…"
    )
    sub_select._values = ["participation"]
    spy = AsyncMock()
    with (
        patch(f"{_ED}.is_subscribed", new=AsyncMock(return_value=True)),
        patch.object(editor_mod._PIPELINE, "set_subscription", spy),
        patch.object(
            ProfileSubsystemEditorView,
            "create",
            new=AsyncMock(return_value=view),
        ),
        patch.object(view, "build_embed", new=AsyncMock(return_value="e")),
    ):
        await sub_select.callback(_interaction())
    spy.assert_awaited_once()
    assert spy.await_args.kwargs["enabled"] is False
    assert spy.await_args.kwargs["topic"] == "participation"


@pytest.mark.asyncio
async def test_bool_preference_select_toggles_value():
    view = await _make_editor()
    pref_select = next(
        c for c in view.children if getattr(c, "placeholder", "") == "Change a preference…"
    )
    pref_select._values = ["digest"]  # BOOL, default False
    spy = AsyncMock()
    with (
        patch(
            f"{_ED}.get_preference",
            new=AsyncMock(return_value=PreferenceResult(value=False, found=False)),
        ),
        patch.object(editor_mod._PIPELINE, "set_preference", spy),
        patch.object(
            ProfileSubsystemEditorView,
            "create",
            new=AsyncMock(return_value=view),
        ),
        patch.object(view, "build_embed", new=AsyncMock(return_value="e")),
    ):
        await pref_select.callback(_interaction())
    spy.assert_awaited_once()
    assert spy.await_args.kwargs["value"] is True
    assert spy.await_args.kwargs["key"] == "xp.digest"


@pytest.mark.asyncio
async def test_enum_preference_select_opens_chooser_no_write_yet():
    view = await _make_editor()
    pref_select = next(
        c for c in view.children if getattr(c, "placeholder", "") == "Change a preference…"
    )
    pref_select._values = ["rank_embed_style"]  # ENUM
    spy = AsyncMock()
    interaction = _interaction()
    with patch.object(editor_mod._PIPELINE, "set_preference", spy):
        await pref_select.callback(interaction)
    spy.assert_not_awaited()  # choosing the pref opens a chooser, no write
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_int_preference_select_opens_modal():
    view = await _make_editor()
    pref_select = next(
        c for c in view.children if getattr(c, "placeholder", "") == "Change a preference…"
    )
    pref_select._values = ["threshold"]  # INT → modal
    interaction = _interaction()
    await pref_select.callback(interaction)
    interaction.response.send_modal.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error handling — typed errors become ephemeral copy, no re-render
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthorized_mutation_renders_ephemeral_copy():
    view = await _make_editor()
    interaction = _interaction()
    with patch.object(
        editor_mod._PIPELINE,
        "set_participation",
        AsyncMock(side_effect=UnauthorizedParticipationMutationError("nope")),
    ):
        await view._toggle_participation(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs["ephemeral"] is True
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_invalid_preference_value_renders_ephemeral_copy():
    view = await _make_editor()
    pref_select = next(
        c for c in view.children if getattr(c, "placeholder", "") == "Change a preference…"
    )
    pref_select._values = ["digest"]
    interaction = _interaction()
    with (
        patch(
            f"{_ED}.get_preference",
            new=AsyncMock(return_value=PreferenceResult(value=False, found=False)),
        ),
        patch.object(
            editor_mod._PIPELINE,
            "set_preference",
            AsyncMock(side_effect=InvalidPreferenceValueError("bad")),
        ),
    ):
        await pref_select.callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_int_modal_rejects_non_numeric_without_writing():
    view = await _make_editor()
    spec = view._schema.preference_specs[2]  # threshold INT
    modal = editor_mod._PreferenceModal(view, spec)
    modal._field._value = "not-a-number"
    interaction = _interaction()
    spy = AsyncMock()
    with patch.object(editor_mod._PIPELINE, "set_preference", spy):
        await modal.on_submit(interaction)
    spy.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_int_modal_coerces_and_writes():
    view = await _make_editor()
    spec = view._schema.preference_specs[2]  # threshold INT
    modal = editor_mod._PreferenceModal(view, spec)
    modal._field._value = "42"
    spy = AsyncMock()
    with (
        patch.object(editor_mod._PIPELINE, "set_preference", spy),
        patch.object(
            ProfileSubsystemEditorView,
            "create",
            new=AsyncMock(return_value=view),
        ),
        patch.object(view, "build_embed", new=AsyncMock(return_value="e")),
    ):
        await modal.on_submit(_interaction())
    spy.assert_awaited_once()
    assert spy.await_args.kwargs["value"] == 42


# ---------------------------------------------------------------------------
# AST invariant — editor writes only through the pipeline service
# ---------------------------------------------------------------------------


def test_editor_writes_only_through_pipeline():
    src = pathlib.Path("disbot/views/profile/editor.py").read_text()
    tree = ast.parse(src)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
        elif isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
    # No direct DB-layer write import — every write rides the audited pipeline.
    assert not any(
        mod.startswith("utils.db") for mod in imported
    ), f"editor must write only through the pipeline; found db import in {imported}"
    assert "services.participation_mutation" in imported
