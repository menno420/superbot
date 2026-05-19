"""Help route model + resolver (shared by typed Help and the dropdown).

Both the ``!help <name>`` command and the Help dropdown call
:func:`resolve_route` so the same name produces the same destination
regardless of entry point. The opener is :func:`open_route` in this
module; the cog wires it into the two entry points.

Routes have five kinds:

- ``hub``       — open a mother-hub panel via the host cog's
                  ``build_help_menu_view`` (or the override named in
                  :data:`HUB_PANEL_BUILDERS`).
- ``subsystem`` — open a subsystem panel via ``build_help_menu_view``
                  with a command-list embed fallback when the hook is
                  missing or raises.
- ``advanced``  — open the legacy paginated ``HelpPanelView``.
- ``command``   — render a single-command help embed.
- ``unknown``   — render the "not found" fallback embed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

import discord
from discord.ext import commands

from utils.hub_registry import HUBS, get_hub
from utils.subsystem_registry import SUBSYSTEMS, all_subsystems_sorted
from utils.ui_constants import UTILITY_COLOR

logger = logging.getLogger("bot")

# Aliases that route to the legacy paginated subsystem browser.
ADVANCED_ALIASES = frozenset({"advanced", "all", "commands", "all commands"})

# Hub aliases beyond the registered key / display_name / entry_command.
# Keep this small — it's a typed-name shorthand, not a second registry.
HUB_ALIAS_OVERRIDES: dict[str, str] = {
    "mod": "moderation",
    "platform": "diagnostic",
}

# Subsystem aliases that must NOT collide with a hub. ``diagnostics`` /
# ``diag`` open the Diagnostics Hub via the subsystem route (it uses
# ``build_help_menu_view`` which returns ``_DiagnosticsHubView``);
# routing them through the hub key ``diagnostic`` would instead open
# Platform Hub via ``build_platform_help_menu_view``.
SUBSYSTEM_ALIAS_OVERRIDES: dict[str, str] = {
    "diagnostics": "diagnostic",
    "diag": "diagnostic",
}

# Hubs whose dedicated Help builder is NOT ``build_help_menu_view``.
# Keep this minimal — additions require a source-grounded justification.
# The Platform / Diagnostics hub is the canonical example: its host cog
# ``DiagnosticCog`` exposes ``build_help_menu_view`` (Diagnostics Hub)
# for Admin → Diagnostics and ``build_platform_help_menu_view`` (Platform
# Hub) for the Help "Platform / Diagnostics" entry.
HUB_PANEL_BUILDERS: dict[str, str] = {
    "diagnostic": "build_platform_help_menu_view",
}


@dataclass(frozen=True)
class HelpRoute:
    """Resolved Help destination. ``target`` meaning depends on ``kind``.

    - ``hub``       → hub key from :data:`utils.hub_registry.HUBS`.
    - ``subsystem`` → subsystem key from :data:`SUBSYSTEMS`.
    - ``command``   → canonical command name (after alias resolution).
    - ``advanced`` / ``unknown`` → ``None``.
    """

    key: str
    kind: Literal["hub", "subsystem", "advanced", "command", "unknown"]
    target: str | None = None


@dataclass(frozen=True)
class HelpOpener:
    """Metadata-only adapter passed to ``build_help_menu_view`` hooks.

    Source-verified that every cog's hook reads only ``.user``, ``.guild``,
    ``.guild_id``, ``.client``, ``.channel`` (some via ``help_ctx_shim``,
    which exposes the same fields). Hooks that need ``.response``,
    ``.followup``, ``.data``, or the interaction lifecycle would raise on
    this adapter — :func:`open_route` catches those errors and falls
    back to the command-list embed so Help never crashes.

    ``HelpInteractionContext`` is an equally acceptable name; this stayed
    as ``HelpOpener`` only because it was shorter for callers.
    """

    user: discord.Member | discord.User
    guild: discord.Guild | None
    guild_id: int | None
    client: commands.Bot
    channel: discord.abc.Messageable | None

    @classmethod
    def from_interaction(cls, interaction: discord.Interaction) -> HelpOpener:
        return cls(
            user=interaction.user,
            guild=interaction.guild,
            guild_id=interaction.guild_id,
            client=interaction.client,  # type: ignore[arg-type]
            channel=interaction.channel,  # type: ignore[arg-type]
        )

    @classmethod
    def from_ctx(cls, ctx: commands.Context) -> HelpOpener:
        return cls(
            user=ctx.author,
            guild=ctx.guild,
            guild_id=ctx.guild.id if ctx.guild else None,
            client=ctx.bot,
            channel=ctx.channel,
        )


def build_single_command_embed(
    cmd: commands.Command,
    prefix: str,
) -> discord.Embed:
    """Render the single-command help embed used by ``!help <command>``."""
    embed = discord.Embed(
        title=f"`{prefix}{cmd.name}`",
        description=cmd.help or "No description.",
        color=UTILITY_COLOR,
    )
    if cmd.aliases:
        embed.add_field(
            name="Aliases",
            value=", ".join(f"`{a}`" for a in cmd.aliases),
        )
    sig = f" {cmd.signature}" if cmd.signature else ""
    embed.add_field(
        name="Usage",
        value=f"`{prefix}{cmd.name}{sig}`",
        inline=False,
    )
    return embed


def build_not_found_embed(name: str) -> discord.Embed:
    """Render the not-found fallback embed used when no route matches."""
    return discord.Embed(
        title="📚 Help",
        description=f"No command or category named `{name}` found.",
        color=UTILITY_COLOR,
    )


def resolve_route(name: str, *, bot: commands.Bot) -> HelpRoute:
    """Resolve a typed/selected name to a :class:`HelpRoute`.

    The resolver is the only place Help routing logic lives. Both the
    typed ``!help <name>`` command and the Help dropdown call this so the
    same name produces the same destination regardless of entry point.

    Priority:
      1. Advanced aliases (``advanced``, ``all``, ``commands``, ...).
      2. Subsystem alias overrides (``diagnostics`` / ``diag``) — these
         must run before the hub match so they aren't captured by the
         Platform / Diagnostics hub.
      3. Hub aliases (key / display_name / entry_command + a small
         shorthand table for ``mod`` and ``platform``).
      4. Subsystem key / display_name.
      5. Command name (after alias resolution).
      6. Unknown — caller renders the not-found fallback.
    """
    n = name.strip().lower()

    if n in ADVANCED_ALIASES:
        return HelpRoute(key=name, kind="advanced")

    if n in SUBSYSTEM_ALIAS_OVERRIDES:
        return HelpRoute(
            key=name,
            kind="subsystem",
            target=SUBSYSTEM_ALIAS_OVERRIDES[n],
        )

    if n in HUB_ALIAS_OVERRIDES:
        return HelpRoute(key=name, kind="hub", target=HUB_ALIAS_OVERRIDES[n])

    for hub in HUBS:
        entry = hub.entry_command.lstrip("!").lower()
        if n == hub.key.lower() or n == hub.display_name.lower() or n == entry:
            return HelpRoute(key=name, kind="hub", target=hub.key)

    for sname, meta in SUBSYSTEMS.items():
        if n == sname.lower() or n == meta.get("display_name", "").lower():
            return HelpRoute(key=name, kind="subsystem", target=sname)

    cmd = bot.get_command(name)
    if cmd is not None:
        return HelpRoute(key=name, kind="command", target=cmd.name)

    return HelpRoute(key=name, kind="unknown")


async def open_route(
    route: HelpRoute,
    opener: HelpOpener,
    *,
    visible_subsystems: set[str],
    member_tier: str,
    prefix: str = "!",
) -> tuple[discord.Embed, discord.ui.View | None]:
    """Build the ``(embed, view)`` pair for a resolved :class:`HelpRoute`.

    Returns ``view=None`` when the destination is an embed-only surface
    (single-command help, not-found fallback, command-list fallback for
    subsystems whose hook raised). The caller decides whether to send a
    new message or edit in place.

    Imports of ``HelpPanelView``, ``_build_page_embed``, ``build_cog_embed``,
    and ``_cog_for_subsystem`` are function-local to avoid an import
    cycle with ``cogs.help_cog`` (where the cog and views live).
    """
    from cogs.help_cog import (
        HelpPanelView,
        _build_page_embed,
        _cog_for_subsystem,
        build_cog_embed,
    )

    if route.kind == "advanced":
        visible_list = [
            name
            for name, meta in all_subsystems_sorted()
            if name in visible_subsystems and not meta.get("parent_hub")
        ]
        view = HelpPanelView(visible_list, page=0)
        embed = _build_page_embed(opener.client, visible_list, 0, member_tier)
        return embed, view

    if route.kind == "hub":
        if route.target is None:
            return build_not_found_embed(route.key), None
        hub = get_hub(route.target)
        if hub is None:
            return build_not_found_embed(route.key), None
        cog = _cog_for_subsystem(opener.client, hub.key)
        if cog is None:
            return build_not_found_embed(hub.display_name), None
        builder_name = HUB_PANEL_BUILDERS.get(hub.key, "build_help_menu_view")
        builder = getattr(cog, builder_name, None)
        if not callable(builder):
            return build_not_found_embed(hub.display_name), None
        try:
            embed, sub_view = await builder(opener)
        except Exception as exc:  # noqa: BLE001 — Help must never crash on hook
            logger.warning(
                "Help hub builder failed | hub=%r builder=%r: %s",
                hub.key,
                builder_name,
                exc,
                exc_info=True,
            )
            return build_not_found_embed(hub.display_name), None
        return embed, sub_view

    if route.kind == "subsystem":
        if route.target is None:
            return build_not_found_embed(route.key), None
        cog = _cog_for_subsystem(opener.client, route.target)
        if cog is None:
            return build_not_found_embed(route.key), None
        builder = getattr(cog, "build_help_menu_view", None)
        if callable(builder):
            try:
                embed, sub_view = await builder(opener)
                return embed, sub_view
            except Exception as exc:  # noqa: BLE001 — fall back to command list
                logger.warning(
                    "Help subsystem builder failed | subsystem=%r: %s",
                    route.target,
                    exc,
                    exc_info=True,
                )
        return build_cog_embed(cog, prefix, route.target), None

    if route.kind == "command":
        if route.target is None:
            return build_not_found_embed(route.key), None
        cmd = opener.client.get_command(route.target)
        if cmd is None:
            return build_not_found_embed(route.key), None
        return build_single_command_embed(cmd, prefix), None

    return build_not_found_embed(route.key), None
