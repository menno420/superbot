"""Characterization tests for the five Help render paths (Lane 8).

These pin **today's** behavior — Home (hub category index) · Advanced
(paginated subsystem browser) · typed routes (`resolve_route`) · the
generic command-list embed · dedicated panels (`build_help_menu_view`
dispatch + fallbacks) — so the future Help projection seam (help audit
§9) lands against a regression net instead of an untested surface.

**No behavior changes ride with these tests.** Where a pin encodes a
quirk (e.g. hub names shadow same-named subsystems in route priority),
that is deliberate: changing the quirk later must be a conscious,
test-visible decision. The Q-0055–Q-0059 overlay answers are design
posture only — nothing here implements or assumes overlay storage.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import discord
import pytest
from discord.ext import commands

from cogs.help.route import (
    HUB_PANEL_BUILDERS,
    HelpOpener,
    HelpRoute,
    build_not_found_embed,
    build_single_command_embed,
    open_route,
    resolve_route,
)
from cogs.help_cog import (
    _PAGE_SIZE,
    HelpPanelView,
    build_categories_overview_embed,
    build_cog_embed,
)
from utils.hub_registry import HUBS, hubs_for_tier
from utils.subsystem_registry import SUBSYSTEMS

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


def _command(name: str, **kwargs) -> commands.Command:
    """A real commands.Command so help rendering sees true attributes."""

    async def _cb(ctx):  # pragma: no cover — never invoked
        return None

    return commands.Command(_cb, name=name, **kwargs)


class _StubCog(commands.Cog):
    """Cog double: real Cog (for isinstance-free duck use) with canned
    commands and optional help hooks."""

    def __init__(
        self,
        cmds: list[commands.Command],
        *,
        hook=None,
        platform_hook=None,
    ) -> None:
        self._cmds = cmds
        if hook is not None:
            self.build_help_menu_view = hook
        if platform_hook is not None:
            self.build_platform_help_menu_view = platform_hook

    def get_commands(self):
        return list(self._cmds)


def _bot(cogs: dict[str, object] | None = None, command=None) -> SimpleNamespace:
    return SimpleNamespace(
        cogs=cogs or {},
        get_command=lambda name: command if command and command.name == name else None,
    )


def _opener(bot) -> HelpOpener:
    return HelpOpener(
        user=SimpleNamespace(id=1),
        guild=None,
        guild_id=99,
        client=bot,
        channel=None,
    )


_ALL_VISIBLE = set(SUBSYSTEMS)
_TOP_LEVEL = [name for name, meta in SUBSYSTEMS.items() if not meta.get("parent_hub")]


# ---------------------------------------------------------------------------
# Path 1 — Home: the hub category index
# ---------------------------------------------------------------------------


def test_home_lists_tier_visible_hubs_plus_permanent_advanced_row():
    embed = build_categories_overview_embed("user")
    field_names = [f.name for f in embed.fields]

    # One field per tier-visible hub, in registry order, + the permanent
    # Advanced row at the end.
    expected_hubs = hubs_for_tier("user")
    assert len(field_names) == len(expected_hubs) + 1
    for hub, field_name in zip(expected_hubs, field_names):
        assert hub.display_name in field_name
    assert field_names[-1] == "📋 Advanced / All Commands"


def test_home_user_tier_sees_exactly_the_user_hubs_today():
    """Characterization: the current user-tier Home composition. A new hub
    or tier change must consciously update this pin."""
    visible = {h.key for h in hubs_for_tier("user")}
    assert visible == {"games", "btd6", "economy", "community", "utility"}


def test_home_admin_tier_sees_every_registered_hub():
    visible = {h.key for h in hubs_for_tier("administrator")}
    assert visible == {h.key for h in HUBS}
    assert len(visible) == 10  # the reconciled hub count (surface map §1)


def test_home_hub_rows_carry_purpose_and_entry_command():
    embed = build_categories_overview_embed("administrator")
    by_name = {f.name: f.value for f in embed.fields}
    games_field = next(v for k, v in by_name.items() if "Games" in k)
    assert "`!games`" in games_field


# ---------------------------------------------------------------------------
# Path 2 — Advanced: the paginated top-level subsystem browser
# ---------------------------------------------------------------------------


async def test_advanced_lists_only_visible_top_level_subsystems():
    bot = _bot()
    embed, view = await open_route(
        HelpRoute(key="advanced", kind="advanced"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="administrator",
    )

    assert isinstance(view, HelpPanelView)
    text = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    # Parent-hub children never appear on Advanced — they are reachable
    # through their hub panel (and typed routes).
    for child in ("Blackjack", "XP & Levels"):
        assert child not in text
    # A first-page top-level subsystem does appear.
    first_page = _TOP_LEVEL[:_PAGE_SIZE]
    assert any(
        SUBSYSTEMS[name].get("display_name", name) in text for name in first_page
    )


async def test_advanced_respects_governance_visibility():
    bot = _bot()
    narrowed = _ALL_VISIBLE - {"ai"}
    embed, _view = await open_route(
        HelpRoute(key="advanced", kind="advanced"),
        _opener(bot),
        visible_subsystems=narrowed,
        member_tier="administrator",
    )
    text = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert SUBSYSTEMS["ai"]["display_name"] not in text


async def test_advanced_paginates_top_level_list_at_page_size():
    bot = _bot()
    embed, _view = await open_route(
        HelpRoute(key="advanced", kind="advanced"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="administrator",
    )
    pages = max(1, math.ceil(len(_TOP_LEVEL) / _PAGE_SIZE))
    if pages > 1:
        assert f"Page 1 of {pages}" in (embed.description or "")
    else:  # pragma: no cover — only if the registry shrinks below one page
        assert "Select a category" in (embed.description or "")


def test_advanced_top_level_set_today():
    """Characterization: the current top-level (non-child) subsystem set —
    the Advanced browser's source list. Re-parenting a subsystem must
    consciously update this pin (post-#626: spotlight is a community child)."""
    assert sorted(_TOP_LEVEL) == [
        "admin",
        "ai",
        "btd6",
        "channel",
        "community",
        "diagnostic",
        "economy",
        "games",
        "help",
        "moderation",
        "server_management",
        "settings",
        "utility",
    ]


# ---------------------------------------------------------------------------
# Path 3 — typed routes: resolve_route priority order
# ---------------------------------------------------------------------------


def test_route_advanced_aliases_win_first():
    bot = _bot()
    for name in ("advanced", "ALL", "Commands", "all commands"):
        assert resolve_route(name, bot=bot).kind == "advanced", name


def test_route_subsystem_alias_overrides_beat_hub_match():
    """`diagnostics`/`diag` must open the Diagnostics subsystem, not the
    Platform hub the `diagnostic` hub key would select."""
    bot = _bot()
    for name in ("diagnostics", "diag"):
        route = resolve_route(name, bot=bot)
        assert (route.kind, route.target) == ("subsystem", "diagnostic"), name
    route = resolve_route("rps", bot=bot)
    assert (route.kind, route.target) == ("subsystem", "rps_tournament")


def test_route_hub_aliases_and_forms():
    bot = _bot()
    assert resolve_route("mod", bot=bot).target == "moderation"
    assert resolve_route("platform", bot=bot).target == "diagnostic"
    # Hub key, display name, and entry command all resolve to the hub.
    for form in ("moderation", "Moderation & Safety", "modmenu"):
        route = resolve_route(form, bot=bot)
        assert (route.kind, route.target) == ("hub", "moderation"), form


def test_route_hub_name_shadows_same_named_subsystem():
    """Characterization of the priority quirk: keys that are both a hub and
    a subsystem (`games`, `settings`, …) resolve to the HUB. The subsystem
    row is reached through the hub panel, never by its bare name."""
    bot = _bot()
    for name in ("games", "settings", "economy"):
        assert resolve_route(name, bot=bot).kind == "hub", name


def test_route_subsystem_by_key_and_display_name():
    bot = _bot()
    for form in ("blackjack", "xp", "XP & Levels"):
        assert resolve_route(form, bot=bot).kind == "subsystem", form
    assert resolve_route("xp", bot=bot).target == "xp"


def test_route_falls_through_to_command_then_unknown():
    cmd = _command("ping")
    assert resolve_route("ping", bot=_bot(command=cmd)) == HelpRoute(
        key="ping",
        kind="command",
        target="ping",
    )
    assert resolve_route("zzz-nope", bot=_bot()).kind == "unknown"


# ---------------------------------------------------------------------------
# Path 4 — the generic command-list embed (subsystem fallback surface)
# ---------------------------------------------------------------------------


def test_generic_embed_filters_hidden_disabled_and_classified():
    cmds = [
        _command("visible", help="Does a thing.", aliases=["v"]),
        _command("ghost", hidden=True),
        _command("off"),
        _command("old", extras={"classification": "legacy_duplicate"}),
    ]
    cmds[2].enabled = False
    cog = _StubCog(cmds)

    embed = build_cog_embed(cog, "!", None)

    names = " ".join(f.name for f in embed.fields)
    assert "`!visible`" in names
    assert "(aliases: v)" in names
    for absent in ("ghost", "off", "old"):
        assert absent not in names
    body = next(f.value for f in embed.fields if "visible" in f.name)
    assert "Does a thing." in body
    assert "Usage: `!visible`" in body


def test_generic_embed_caps_fields_and_notes_overflow():
    cog = _StubCog([_command(f"cmd{i:02d}") for i in range(30)])
    embed = build_cog_embed(cog, "!", None)
    assert len(embed.fields) == 25  # 24 commands + 1 overflow note
    assert "… 6 more command(s)" in embed.fields[-1].name


def test_single_command_embed_shape():
    cmd = _command("ping", help="Pong.", aliases=["p"])
    embed = build_single_command_embed(cmd, "!")
    assert embed.title == "`!ping`"
    assert embed.description == "Pong."
    assert any("Aliases" == f.name for f in embed.fields)
    assert any("Usage" == f.name for f in embed.fields)


# ---------------------------------------------------------------------------
# Path 5 — dedicated panels: hook dispatch + fallbacks
# ---------------------------------------------------------------------------


def _panel_pair(title: str):
    async def hook(opener):
        return discord.Embed(title=title), discord.ui.View()

    return hook


async def test_subsystem_route_opens_the_cog_hook_panel():
    cog = _StubCog([_command("xpmenu")], hook=_panel_pair("XP PANEL"))
    bot = _bot(cogs={"XpCog": cog})

    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="user",
    )
    assert embed.title == "XP PANEL"
    assert view is not None


async def test_subsystem_hook_failure_falls_back_to_command_list():
    async def boom(opener):
        raise RuntimeError("panel exploded")

    cog = _StubCog([_command("xpmenu", help="Open XP menu.")], hook=boom)
    bot = _bot(cogs={"XpCog": cog})

    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="user",
    )
    # Fallback is the embed-only generic command list — Help never crashes.
    assert view is None
    assert "`!xpmenu`" in " ".join(f.name for f in embed.fields)


async def test_hub_route_uses_panel_builder_override_table():
    """The `diagnostic` hub routes through `build_platform_help_menu_view`
    (Platform Hub), NOT the generic hook (Diagnostics Hub)."""
    assert HUB_PANEL_BUILDERS == {"diagnostic": "build_platform_help_menu_view"}

    cog = _StubCog(
        [_command("platform")],
        hook=_panel_pair("WRONG: DIAGNOSTICS"),
        platform_hook=_panel_pair("PLATFORM HUB"),
    )
    bot = _bot(cogs={"DiagnosticCog": cog})

    embed, _view = await open_route(
        HelpRoute(key="platform", kind="hub", target="diagnostic"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="administrator",
    )
    assert embed.title == "PLATFORM HUB"


async def test_hub_hook_failure_renders_not_found():
    async def boom(opener):
        raise RuntimeError("hub exploded")

    cog = _StubCog([_command("games")], hook=boom)
    bot = _bot(cogs={"GamesCog": cog})

    embed, view = await open_route(
        HelpRoute(key="games", kind="hub", target="games"),
        _opener(bot),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="user",
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_unresolvable_host_cog_renders_not_found():
    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(_bot(cogs={})),  # no cog matches the entry points
        visible_subsystems=_ALL_VISIBLE,
        member_tier="user",
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_unknown_route_renders_not_found():
    embed, view = await open_route(
        HelpRoute(key="zzz", kind="unknown"),
        _opener(_bot()),
        visible_subsystems=_ALL_VISIBLE,
        member_tier="user",
    )
    assert view is None
    assert embed.description == build_not_found_embed("zzz").description
