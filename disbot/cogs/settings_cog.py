"""Settings Manager cog — S5 of the Global Settings & Customization Manager.

Lands the long-term Settings Manager navigation shape (hub +
subsystem dropdown + four diagnostic sub-panels) in **strictly
read-only** form.  Future milestones add edit / reset / mutate
flows (S6+), the logging create-or-select flow (S7), cleanup
expansion (S8), the access-policy manager (S9), and per-subsystem
setup packs (S10).

Hard limits for S5:

* No edit modals, no reset buttons that write, no resource
  creation, no binding mutation, no access-policy mutation, no
  cleanup-policy mutation, no setup wizard, no slash commands.
* The cog ALWAYS loads and registers in
  :data:`utils.subsystem_registry.SUBSYSTEMS` so help / admin /
  menu discoverability stays stable.
* The :data:`core.runtime.feature_flags.SETTINGS_MANAGER_COG_ENABLED`
  flag (default OFF) gates the runtime *behaviour* of ``!settings``
  and the ``build_help_menu_view`` hook.  When OFF, invocations
  return a clearly-worded disabled embed describing how to enable
  it.  This avoids the "command exists but mysteriously hidden"
  discoverability bug.

Pinned by ``tests/unit/invariants/test_settings_cog_read_only.py``:
no imports of mutation pipelines in ``disbot/cogs/settings*`` or
``disbot/views/settings/**``.
"""

from __future__ import annotations

import logging

import discord
from discord.ext import commands

from views.base import send_panel

logger = logging.getLogger("bot")


_FLAG_NAME = "settings.manager_cog.enabled"


def _disabled_embed() -> discord.Embed:
    """Return the embed shown when the feature flag is OFF.

    Surfaces the exact command an operator would run to flip the
    flag (via the rollout pipeline, when that command exists) so the
    discoverability gap can be closed in one step.
    """
    embed = discord.Embed(
        title="⚙️ Settings Manager — disabled",
        description=(
            "The Settings Manager cog is registered for discoverability, "
            "but its runtime behaviour is gated behind the "
            f"`{_FLAG_NAME}` feature flag, which defaults to **OFF**.\n\n"
            "When this flag is ON the `!settings` command opens the "
            "Settings hub (read-only browsing of every subsystem's "
            "scalar settings, bindings, resource requirements, and "
            "recent audit history).\n\n"
            "Flip the flag via the feature-flag mutation pipeline "
            "(future `!platform flags set …` command) or the "
            "`SUPERBOT_FF_SETTINGS__MANAGER_COG__ENABLED=on` env "
            "override."
        ),
        color=discord.Color.greyple(),
    )
    embed.set_footer(text="S5 — read-only Settings Manager shell (default OFF).")
    return embed


async def _is_enabled(guild_id: int | None) -> bool:
    """Resolve the gate flag for the given guild.

    Failures fall back to ``False`` (closed) — a flag-evaluator
    outage must not open a UI that is supposed to default OFF.
    """
    try:
        from core.runtime import feature_flags

        return await feature_flags.is_enabled(_FLAG_NAME, guild_id)
    except Exception as exc:  # noqa: BLE001 — gate is closed on any failure
        logger.warning(
            "settings_cog: feature_flag resolution raised %s; treating "
            "%s as OFF (gate closed).",
            exc,
            _FLAG_NAME,
        )
        return False


class SettingsCog(commands.Cog):
    """Read-only Settings Manager surface (S5).

    Public commands:

    * ``!settings`` — open the Settings hub.

    Public hooks:

    * ``build_help_menu_view`` — direct-navigation entry from
      :class:`cogs.help_cog.HelpPanelView` so picking *Settings
      Manager* from the help dropdown opens the hub in place.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.cooldown(rate=2, per=10, type=commands.BucketType.user)
    @commands.command(
        name="settings",
        help="Open the Settings Manager hub (read-only).",
    )
    @commands.has_permissions(administrator=True)
    async def settings_root(self, ctx: commands.Context) -> None:
        """Entry-point command for the Settings Manager subsystem.

        When the gate flag is OFF, returns the standard disabled
        embed.  When ON, opens the hub view.
        """
        guild_id = ctx.guild.id if ctx.guild else None
        if not await _is_enabled(guild_id):
            await ctx.send(embed=_disabled_embed())
            return
        from views.settings.hub import SettingsHubView

        view = SettingsHubView(ctx.author)
        await send_panel(ctx, embed=SettingsHubView.build_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook.

        Called by ``HelpPanelView._on_select`` when the operator
        picks *Settings Manager* from the help dropdown.  Returns
        the same ``(embed, view)`` shape that ``!settings`` would
        produce, with one exception: when the gate flag is OFF the
        returned view is a tiny "disabled" view with only a
        back-to-help button, so users see a coherent explanation
        instead of an interactive hub that does nothing.
        """
        guild_id = interaction.guild_id
        if not await _is_enabled(guild_id):
            return _disabled_embed(), _DisabledHelpHookView(interaction.user)
        from views.settings.hub import SettingsHubView

        view = SettingsHubView(interaction.user)
        return SettingsHubView.build_embed(), view


class _DisabledHelpHookView(discord.ui.View):
    """No-controls view shown in the help direct-nav path when the
    gate flag is OFF.  The help cog appends its own "↩ Back to Help"
    button to this view, so we deliberately ship an empty container
    rather than reach into the help view machinery from here.
    """

    def __init__(self, _author) -> None:  # noqa: ARG002 — kept for parity
        super().__init__(timeout=60)


async def setup(bot: commands.Bot) -> None:
    """discord.py extension entry point."""
    await bot.add_cog(SettingsCog(bot))


__all__ = ["SettingsCog", "setup"]
