"""Characterization tests for the five Help render paths (Lane 8 + Batch 6).

These pin the behavior of — Home (hub category index) · Advanced
(paginated subsystem browser) · typed routes (`resolve_route`) · the
generic command-list embed · dedicated panels (`build_help_menu_view`
dispatch + fallbacks). The #642 net pinned the pre-seam divergence;
the **Batch 6 projection seam (HLP-2) consciously changed the pins**
marked below: every path now consumes one
:class:`services.help_projection.HelpProjection`, so

* typed/dropdown hub + subsystem routes return not-found for targets the
  projection hides (pre-seam they opened regardless of governance);
* the typed single-command route applies the same display filter as the
  command-list embed (pre-seam it skipped classification/hidden/disabled);
* Home hides a hub whose host subsystem is governance-hidden (pre-seam
  Home was tier-only).

Where a pin encodes a quirk (e.g. hub names shadow same-named subsystems
in route priority), that remains deliberate: changing it must be a
conscious, test-visible decision. The HLP-3 section at the end pins the
guild overlay (Q-0055–Q-0059) flowing through the same seam: overlay
hides behave exactly like governance hides at every render path, renames
are presentation-only, and an absent overlay is byte-identical.
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
from governance.models import VisibilityResult
from services.help_projection import HelpProjection
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


def _projection(visible: set[str], tier: str) -> HelpProjection:
    """The audience projection every render path consumes (HLP-2)."""
    return HelpProjection.from_visibility(
        VisibilityResult(
            visible_subsystems=visible,
            member_tier=tier,
            resolved_from={},
            traces={},
        ),
    )


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
        projection=_projection(_ALL_VISIBLE, "administrator"),
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
        projection=_projection(narrowed, "administrator"),
    )
    text = " ".join(f"{f.name} {f.value}" for f in embed.fields)
    assert SUBSYSTEMS["ai"]["display_name"] not in text


async def test_advanced_paginates_top_level_list_at_page_size():
    bot = _bot()
    embed, _view = await open_route(
        HelpRoute(key="advanced", kind="advanced"),
        _opener(bot),
        projection=_projection(_ALL_VISIBLE, "administrator"),
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
        projection=_projection(_ALL_VISIBLE, "user"),
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
        projection=_projection(_ALL_VISIBLE, "user"),
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
        projection=_projection(_ALL_VISIBLE, "administrator"),
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
        projection=_projection(_ALL_VISIBLE, "user"),
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_unresolvable_host_cog_renders_not_found():
    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(_bot(cogs={})),  # no cog matches the entry points
        projection=_projection(_ALL_VISIBLE, "user"),
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_unknown_route_renders_not_found():
    embed, view = await open_route(
        HelpRoute(key="zzz", kind="unknown"),
        _opener(_bot()),
        projection=_projection(_ALL_VISIBLE, "user"),
    )
    assert view is None
    assert embed.description == build_not_found_embed("zzz").description


# ---------------------------------------------------------------------------
# Batch 6 (HLP-2) — effective-access unification across the five paths.
# One projection decides; every path observes the same decision.
# ---------------------------------------------------------------------------


def test_home_hides_hub_whose_host_subsystem_is_governance_hidden():
    """Path 1: pre-seam Home was tier-only (the resolved governance set was
    discarded — audit §3). Now a hub disappears when its host subsystem is
    hidden in this scope."""
    projection = _projection(_ALL_VISIBLE - {"games"}, "user")
    embed = build_categories_overview_embed(projection=projection)
    names = " ".join(f.name for f in embed.fields)
    assert "Games" not in names
    assert "Economy" in names  # unaffected sibling


async def test_advanced_and_typed_route_agree_on_hidden_subsystem():
    """Paths 2+3: a governance-hidden subsystem is absent from Advanced AND
    its typed route renders not-found — the same decision, not two filters."""
    narrowed = _ALL_VISIBLE - {"ai"}
    projection = _projection(narrowed, "administrator")
    assert "ai" not in projection.advanced_subsystems()

    embed, view = await open_route(
        HelpRoute(key="ai", kind="subsystem", target="ai"),
        _opener(_bot()),
        projection=projection,
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_typed_hub_route_checks_target_against_projection():
    """Path 3: pre-seam, a typed hub route opened the panel regardless of
    governance (audit §3 'no target check'). Now hidden = not-found,
    indistinguishable from a nonexistent name."""
    cog = _StubCog([_command("games")], hook=_panel_pair("GAMES HUB"))
    bot = _bot(cogs={"GamesCog": cog})

    visible_projection = _projection(_ALL_VISIBLE, "user")
    embed, view = await open_route(
        HelpRoute(key="games", kind="hub", target="games"),
        _opener(bot),
        projection=visible_projection,
    )
    assert embed.title == "GAMES HUB"

    hidden_projection = _projection(_ALL_VISIBLE - {"games"}, "user")
    embed, view = await open_route(
        HelpRoute(key="games", kind="hub", target="games"),
        _opener(bot),
        projection=hidden_projection,
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_typed_hub_route_applies_the_hub_tier_floor():
    """Path 3: pre-seam, `!help settings` opened the admin hub panel for
    user-tier members. The projection applies the same tier floor Home
    always used."""
    cog = _StubCog([_command("settings")], hook=_panel_pair("SETTINGS HUB"))
    bot = _bot(cogs={"SettingsCog": cog})

    embed, view = await open_route(
        HelpRoute(key="settings", kind="hub", target="settings"),
        _opener(bot),
        projection=_projection(_ALL_VISIBLE, "user"),
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_typed_command_route_applies_the_shared_display_filter():
    """Paths 3+4: pre-seam, `!help <cmd>` rendered ledger-hidden /
    Discord-hidden / disabled commands the command-list embed filtered out.
    One filter now (`services.help_projection.command_display_state`)."""
    projection = _projection(_ALL_VISIBLE, "user")

    visible_cmd = _command("ping", help="Pong.")
    embed, view = await open_route(
        HelpRoute(key="ping", kind="command", target="ping"),
        _opener(_bot(command=visible_cmd)),
        projection=projection,
    )
    assert embed.title == "`!ping`"

    for hidden_cmd in (
        _command("ghost", hidden=True),
        _command("old", extras={"classification": "legacy_duplicate"}),
    ):
        embed, view = await open_route(
            HelpRoute(key=hidden_cmd.name, kind="command", target=hidden_cmd.name),
            _opener(_bot(command=hidden_cmd)),
            projection=projection,
        )
        assert view is None, hidden_cmd.name
        assert "No command or category named" in (embed.description or "")


async def test_dedicated_panel_dispatch_respects_the_projection():
    """Path 5: the dedicated-panel hook never fires for a hidden target —
    the dispatch seam (open_route) applies the decision before the builder
    is consulted."""
    calls: list[str] = []

    async def hook(opener):
        calls.append("built")
        return discord.Embed(title="XP PANEL"), discord.ui.View()

    cog = _StubCog([_command("xpmenu")], hook=hook)
    bot = _bot(cogs={"XpCog": cog})

    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(bot),
        projection=_projection(_ALL_VISIBLE - {"xp"}, "user"),
    )
    assert view is None
    assert calls == []  # the builder was never invoked
    assert "No command or category named" in (embed.description or "")


# ---------------------------------------------------------------------------
# HLP-3 — the guild overlay flows through the same seam (hide + rename)
# ---------------------------------------------------------------------------


def _overlay_projection(visible: set[str], tier: str, *rows):
    from services.help_overlay import GuildHelpOverlay, HelpOverlayRow

    overlay = GuildHelpOverlay(
        guild_id=1,
        rows=tuple(HelpOverlayRow(**r) for r in rows),
    )
    return HelpProjection.from_visibility(
        VisibilityResult(
            visible_subsystems=visible,
            member_tier=tier,
            resolved_from={},
            traces={},
        ),
        overlay=overlay,
    )


def test_home_hides_overlay_hidden_hub_and_renders_renames():
    projection = _overlay_projection(
        _ALL_VISIBLE,
        "user",
        {"entity_kind": "hub", "entity_key": "economy", "display_hidden": True},
        {"entity_kind": "hub", "entity_key": "games", "display_name": "Arcade"},
    )
    embed = build_categories_overview_embed(projection=projection)
    names = " ".join(f.name for f in embed.fields)
    assert "Economy" not in names  # overlay display-hide
    assert "Arcade" in names and "Games" not in names  # overlay rename
    # The rename is presentation-only: the entry command stays canonical.
    arcade_row = next(f for f in embed.fields if "Arcade" in f.name)
    assert "`!games`" in arcade_row.value


async def test_typed_route_treats_overlay_hidden_like_any_hidden_target():
    """Hide unification: an overlay-hidden subsystem types as not-found —
    the same fallback as governance-hidden and nonexistent names."""
    cog = _StubCog([_command("xpmenu")], hook=_panel_pair("XP PANEL"))
    bot = _bot(cogs={"XpCog": cog})

    projection = _overlay_projection(
        _ALL_VISIBLE,
        "user",
        {"entity_kind": "subsystem", "entity_key": "xp", "display_hidden": True},
    )
    embed, view = await open_route(
        HelpRoute(key="xp", kind="subsystem", target="xp"),
        _opener(bot),
        projection=projection,
    )
    assert view is None
    assert "No command or category named" in (embed.description or "")


async def test_advanced_and_cog_embed_render_overlay_renames():
    projection = _overlay_projection(
        _ALL_VISIBLE,
        "administrator",
        {
            "entity_kind": "subsystem",
            "entity_key": "economy",
            "display_name": "Bank",
            "description": "Coins and trading",
        },
    )
    # Path 2 — the Advanced page embed shows the effective name.
    from cogs.help_cog import _build_page_embed

    embed = _build_page_embed(
        _bot(),
        projection.advanced_subsystems(),
        0,
        "administrator",
        projection=projection,
    )
    text = " ".join(f.value for f in embed.fields)
    assert "**Bank** — Coins and trading" in text

    # Path 4 — the command-list embed title takes the effective name.
    cog = _StubCog([_command("economymenu", help="Open the menu.")])
    cog_embed = build_cog_embed(cog, "!", "economy", projection=projection)
    assert "Bank" in (cog_embed.title or "")


def test_help_panel_view_options_render_overlay_renames():
    projection = _overlay_projection(
        _ALL_VISIBLE,
        "administrator",
        {"entity_kind": "subsystem", "entity_key": "economy", "display_name": "Bank"},
    )
    view = HelpPanelView(
        projection.advanced_subsystems(),
        page=0,
        projection=projection,
    )
    select = next(c for c in view.children if isinstance(c, discord.ui.Select))
    by_value = {opt.value: opt.label for opt in select.options}
    assert by_value["economy"] == "Bank"


def test_overlay_absent_keeps_render_paths_byte_identical():
    """Default-byte: a projection without overlay renders exactly like one
    with an empty overlay across Home and Advanced."""
    from services.help_overlay import EMPTY_OVERLAY

    vis = VisibilityResult(
        visible_subsystems=_ALL_VISIBLE,
        member_tier="administrator",
        resolved_from={},
        traces={},
    )
    bare = HelpProjection.from_visibility(vis)
    empty = HelpProjection.from_visibility(vis, overlay=EMPTY_OVERLAY)

    bare_home = build_categories_overview_embed(projection=bare)
    empty_home = build_categories_overview_embed(projection=empty)
    assert [(f.name, f.value) for f in bare_home.fields] == [
        (f.name, f.value) for f in empty_home.fields
    ]
    # Q-0059 frame: absent home row keeps the default frame byte-identical.
    assert bare_home.title == empty_home.title == "📚 Help Menu"
    assert bare_home.description == empty_home.description
    assert bare_home.color == empty_home.color


def test_home_message_customizes_the_home_frame():
    """Q-0059 (migration 067): a home row swaps title/body/color; hub
    fields are untouched; stored mentions render suppressed."""
    from services.help_overlay import GuildHelpOverlay, HomeMessage

    vis = VisibilityResult(
        visible_subsystems=_ALL_VISIBLE,
        member_tier="administrator",
        resolved_from={},
        traces={},
    )
    default = HelpProjection.from_visibility(vis)
    custom = HelpProjection.from_visibility(
        vis,
        overlay=GuildHelpOverlay(
            guild_id=1,
            home=HomeMessage(
                title="Welcome to @everyone's server",
                body="Start here!",
                color=0x57F287,
            ),
        ),
    )

    default_home = build_categories_overview_embed(projection=default)
    custom_home = build_categories_overview_embed(projection=custom)

    assert "Welcome to" in custom_home.title
    assert "@everyone" not in custom_home.title  # mention suppression
    assert custom_home.description == "Start here!"
    assert custom_home.color.value == 0x57F287
    # The category fields themselves are identical — only the frame changed.
    assert [(f.name, f.value) for f in custom_home.fields] == [
        (f.name, f.value) for f in default_home.fields
    ]
