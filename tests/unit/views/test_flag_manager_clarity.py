"""Flag-manager clarity tests — setup-wizard finalization PR2.

Covers the dropdown/embed clarity additions: friendly labels, operator-
first ordering, inactive/env-only markers, and the plain-language detail
warnings (no-consumer, env-only, feature_flag.primary OFF).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from views.diagnostic import flag_manager

# ---------------------------------------------------------------------------
# Constant + helpers
# ---------------------------------------------------------------------------


def test_no_consumer_set_contents():
    assert isinstance(flag_manager._NO_CONSUMER_FLAGS, frozenset)
    assert flag_manager._NO_CONSUMER_FLAGS == {
        "resources.unified",
        "settings.mutation.primary",
        "resource_provisioning.primary",
    }


def test_sorted_flag_names_operator_first_then_internal():
    names = flag_manager._sorted_flag_names()
    from core.runtime import feature_flags

    flags = feature_flags.all_flags()
    auds = [getattr(flags[n], "audience", "internal") for n in names]
    # Once an internal flag appears, no operator flag may follow it.
    seen_internal = False
    for aud in auds:
        if aud != "operator":
            seen_internal = True
        elif seen_internal:
            pytest.fail("operator flag appeared after an internal flag")
    operator = [n for n in names if getattr(flags[n], "audience", "") == "operator"]
    internal = [n for n in names if getattr(flags[n], "audience", "") != "operator"]
    assert operator == sorted(operator)
    assert internal == sorted(internal)
    # Sanity: nothing dropped.
    assert set(names) == set(flags)


def test_option_label_friendly_with_operator_prefix():
    op = MagicMock(label="YouTube context", audience="operator")
    internal = MagicMock(label="Bindings primary", audience="internal")
    op_label = flag_manager._option_label("youtube.context.enabled", op)
    assert op_label.startswith("🛠")
    assert "YouTube context" in op_label
    assert flag_manager._option_label("bindings.primary", internal).startswith("⚙")


def test_option_label_falls_back_to_key_when_no_label():
    flag = MagicMock(label="", audience="internal")
    assert "x.y.z" in flag_manager._option_label("x.y.z", flag)


def test_option_description_marks_inactive():
    desc = flag_manager._option_description(
        "resources.unified",
        MagicMock(db_editable=True),
    )
    assert "resources.unified" in desc  # raw key present
    assert "inactive" in desc


def test_option_description_marks_env_only():
    desc = flag_manager._option_description(
        "feature_flag.primary",
        MagicMock(db_editable=False),
    )
    assert "env-only" in desc


def test_option_description_plain_for_normal_flag():
    desc = flag_manager._option_description(
        "youtube.context.enabled",
        MagicMock(db_editable=True),
    )
    assert desc == "youtube.context.enabled"


# ---------------------------------------------------------------------------
# Detail-embed warnings
# ---------------------------------------------------------------------------


def _details(**overrides):
    base = {
        "name": "x.y",
        "label": "Example",
        "description": "desc",
        "default": "off",
        "effective": "off",
        "source": "default",
        "owner": "platform",
        "audience": "operator",
        "db_editable": True,
        "has_guild_override": False,
        "removal_target": "",
        "no_consumer": False,
        "primary_on": True,
    }
    base.update(overrides)
    return base


def _notes(embed) -> str:
    return next((f.value for f in embed.fields if f.name == "Notes"), "")


def test_embed_warns_no_consumer():
    embed = flag_manager.build_flag_detail_embed(
        _details(name="resources.unified", no_consumer=True),
    )
    assert "no consumer" in _notes(embed).lower()


def test_embed_warns_env_only_with_env_var_name():
    embed = flag_manager.build_flag_detail_embed(
        _details(name="feature_flag.primary", db_editable=False),
    )
    notes = _notes(embed)
    assert "env-only" in notes.lower()
    assert "SUPERBOT_FF_FEATURE_FLAG_PRIMARY" in notes


def test_embed_warns_when_primary_off_for_editable_flag():
    embed = flag_manager.build_flag_detail_embed(
        _details(db_editable=True, primary_on=False),
    )
    assert "feature_flag.primary` is off" in _notes(embed).lower()


def test_embed_has_no_notes_when_clean():
    embed = flag_manager.build_flag_detail_embed(
        _details(db_editable=True, primary_on=True, no_consumer=False),
    )
    assert "Notes" not in {f.name for f in embed.fields}


def test_embed_env_only_takes_priority_over_primary_off():
    """An env-only flag shows the env-only note, not the primary-off note
    (env-only is the more specific, actionable reason)."""
    embed = flag_manager.build_flag_detail_embed(
        _details(name="feature_flag.primary", db_editable=False, primary_on=False),
    )
    notes = _notes(embed).lower()
    assert "env-only" in notes
    assert "master switch is off" not in notes


# ---------------------------------------------------------------------------
# _resolve_flag_details enrichment (async)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_flag_details_includes_primary_and_no_consumer():
    fake_flag = MagicMock()
    fake_flag.default_value = False
    fake_flag.owner = "platform"
    fake_flag.description = "D"
    fake_flag.removal_target = ""
    fake_flag.audience = "internal"
    fake_flag.db_editable = True
    fake_flag.label = "L"

    async def fake_resolve(name, _guild):
        # feature_flag.primary resolves ON; the target flag resolves OFF.
        return MagicMock(value=(name == "feature_flag.primary"), source="default")

    with (
        patch("core.runtime.feature_flags.get", return_value=fake_flag),
        patch(
            "core.runtime.feature_flags.resolve_with_provenance",
            new=AsyncMock(side_effect=fake_resolve),
        ),
        patch(
            "utils.db.feature_flag_state.get_guild_override",
            new=AsyncMock(return_value=None),
        ),
    ):
        details = await flag_manager._resolve_flag_details("resources.unified", 123)

    assert details["primary_on"] is True
    assert details["no_consumer"] is True
