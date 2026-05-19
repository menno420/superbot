"""Platform flag manager view — Phase 6.5a.

Editable companion to ``!platform flags`` (which stays read-only).
Every mutation routes through :class:`services.rollout_mutation.
RolloutMutationPipeline`, the canonical write path that validates
flags/states/scopes, writes to ``feature_flag_state`` plus an audit
row, invalidates the feature-flag cache, and emits an event.

**No direct DB writes.** Tests pin this contract via a grep over
this module.

Scope of this PR:

* Per-guild enable/disable through ``set_flag_state(scope="guild")``.
* Read-only render of every declared flag's default, effective
  value, source, and owner (mirrors ``build_flags_embed``).

Explicit non-goals (per the roadmap):

* No reset/delete of guild overrides — the pipeline does not expose
  a delete path today, and inventing a direct DB delete here would
  bypass audit/cache invalidation. The button is omitted entirely
  (better than a confusingly disabled control).
* No rollout-percent slider.
* No global-scope mutation.
* No environment-tier editing.
* No slash command.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from utils.ui_constants import ADMIN_COLOR
from views.base import HubView

logger = logging.getLogger("bot.views.diagnostic.flag_manager")


# Max flags renderable in one Discord select.
_MAX_FLAGS_PER_SELECT = 25


def _sorted_flag_names() -> list[str]:
    """All declared feature flags, sorted for deterministic UI ordering."""
    from core.runtime import feature_flags

    return sorted(feature_flags.declared_names())


async def _resolve_flag_details(
    flag_name: str,
    guild_id: int | None,
) -> dict[str, Any]:
    """Read-only snapshot of a flag's declaration + effective resolution.

    Returns a dict with keys ``name``, ``default``, ``effective``,
    ``source``, ``owner``, ``description``, ``removal_target``,
    ``has_guild_override``. Resolution errors are caught and surfaced
    as ``source="error:<exc>"`` so the embed never crashes.
    """
    from core.runtime import feature_flags
    from utils.db import feature_flag_state as ff_db

    flag = feature_flags.get(flag_name)
    if flag is None:
        return {
            "name": flag_name,
            "default": "?",
            "effective": "?",
            "source": "unregistered",
            "owner": "?",
            "description": "Flag is no longer declared.",
            "removal_target": "",
            "has_guild_override": False,
        }
    try:
        decision = await feature_flags.resolve_with_provenance(flag_name, guild_id)
        effective = "on" if decision.value else "off"
        source = decision.source
    except Exception as exc:  # noqa: BLE001 — diagnostics must not raise
        effective = "?"
        source = f"error:{type(exc).__name__}"

    has_guild_override = False
    if guild_id is not None:
        try:
            row = await ff_db.get_guild_override(flag_name, guild_id)
            has_guild_override = row is not None
        except Exception as exc:  # noqa: BLE001 — non-fatal
            logger.debug(
                "Could not read guild override for %r/%d: %s",
                flag_name,
                guild_id,
                exc,
            )

    return {
        "name": flag_name,
        "default": "on" if flag.default_value else "off",
        "effective": effective,
        "source": source,
        "owner": flag.owner,
        "description": flag.description,
        "removal_target": flag.removal_target,
        "has_guild_override": has_guild_override,
    }


def build_flag_manager_overview_embed() -> discord.Embed:
    """Pre-selection overview embed."""
    embed = discord.Embed(
        title="🚩 Flag Manager",
        description=(
            "Pick a flag from the dropdown to view its current state and "
            "enable/disable it for this guild. Every mutation routes "
            "through the rollout pipeline (validated + audited + cache "
            "invalidated)."
        ),
        color=ADMIN_COLOR,
    )
    embed.set_footer(
        text=(
            "Read-only by default. Enable/Disable only mutate the per-guild "
            "override — global flag state and rollout percent are unchanged."
        ),
    )
    return embed


def build_flag_detail_embed(details: dict[str, Any]) -> discord.Embed:
    """Render a flag's read-only details as the manager embed."""
    color = ADMIN_COLOR
    title = f"🚩 {details['name']}"
    description = details.get("description") or "_No description._"
    embed = discord.Embed(title=title, description=description, color=color)
    embed.add_field(name="Default", value=f"`{details['default']}`", inline=True)
    embed.add_field(name="Effective", value=f"`{details['effective']}`", inline=True)
    embed.add_field(name="Source", value=f"`{details['source']}`", inline=True)
    embed.add_field(name="Owner", value=f"`{details['owner']}`", inline=True)
    embed.add_field(
        name="Guild override",
        value="`yes`" if details["has_guild_override"] else "`none`",
        inline=True,
    )
    removal = details.get("removal_target")
    if removal:
        embed.add_field(name="Removal target", value=removal, inline=True)
    embed.set_footer(
        text=(
            "Enable/Disable writes a per-guild override through "
            "RolloutMutationPipeline.set_flag_state."
        ),
    )
    return embed


class _FlagSelect(discord.ui.Select):
    def __init__(self, flag_names: list[str], selected: str | None) -> None:
        options: list[discord.SelectOption] = []
        for name in flag_names[:_MAX_FLAGS_PER_SELECT]:
            options.append(
                discord.SelectOption(
                    label=name[:100],
                    value=name,
                    default=(name == selected),
                ),
            )
        if not options:
            options.append(
                discord.SelectOption(
                    label="No flags declared",
                    value="__none__",
                    description="The feature-flag registry is empty.",
                ),
            )
        super().__init__(
            placeholder="Choose a flag…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="flag_manager:select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, FlagManagerView):
            return
        await view.handle_select(interaction, self.values[0])


class FlagManagerView(HubView):
    """Per-guild feature-flag editor.

    Construction is sync (no DB calls); render goes through
    :meth:`refresh` after mutation or selection.
    """

    SUBSYSTEM = "diagnostic"

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        guild_id: int | None,
    ) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.selected_flag: str | None = None
        self._flag_names = _sorted_flag_names()
        self.add_item(_FlagSelect(self._flag_names, self.selected_flag))

    def _replace_select(self) -> None:
        """Rebuild the flag select so the ``default=`` marker tracks state."""
        to_remove = [
            child
            for child in self.children
            if isinstance(child, discord.ui.Select)
            and child.custom_id == "flag_manager:select"
        ]
        for item in to_remove:
            self.remove_item(item)
        self.add_item(_FlagSelect(self._flag_names, self.selected_flag))

    async def handle_select(
        self,
        interaction: discord.Interaction,
        flag_name: str,
    ) -> None:
        if flag_name == "__none__":
            await interaction.response.send_message(
                "No flags are declared in this build.",
                ephemeral=True,
            )
            return
        self.selected_flag = flag_name
        self._replace_select()
        details = await _resolve_flag_details(flag_name, self.guild_id)
        await interaction.response.edit_message(
            embed=build_flag_detail_embed(details),
            view=self,
        )

    async def _apply_state(
        self,
        interaction: discord.Interaction,
        new_state: str,
    ) -> None:
        if not self.selected_flag or self.selected_flag == "__none__":
            await interaction.response.send_message(
                "Pick a flag from the dropdown before changing its state.",
                ephemeral=True,
            )
            return
        if self.guild_id is None:
            await interaction.response.send_message(
                "Guild context is required to set a per-guild override.",
                ephemeral=True,
            )
            return

        # Local imports — keep the heavy pipeline + DB modules out of
        # this view's import time.
        from services.rollout_mutation import (
            RolloutMutationError,
            RolloutMutationPipeline,
        )

        pipeline = RolloutMutationPipeline()
        try:
            await pipeline.set_flag_state(
                flag_name=self.selected_flag,
                scope="guild",
                state=new_state,
                actor_id=interaction.user.id,
                actor_type="platform_owner",
                guild_id=self.guild_id,
            )
        except RolloutMutationError as exc:
            await interaction.response.send_message(
                f"Mutation rejected by pipeline: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — UI must not crash
            logger.exception(
                "FlagManagerView: pipeline call failed unexpectedly "
                "(flag=%r, state=%r): %s",
                self.selected_flag,
                new_state,
                exc,
            )
            await interaction.response.send_message(
                f"Mutation failed: `{type(exc).__name__}`. See bot logs.",
                ephemeral=True,
            )
            return

        # Refresh the detail embed so the operator sees the new state /
        # source / override marker in place.
        details = await _resolve_flag_details(self.selected_flag, self.guild_id)
        await interaction.response.edit_message(
            embed=build_flag_detail_embed(details),
            view=self,
        )

    @discord.ui.button(
        label="✅ Enable for this guild",
        style=discord.ButtonStyle.success,
        custom_id="flag_manager:enable",
        row=1,
    )
    async def btn_enable(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self._apply_state(interaction, "on")

    @discord.ui.button(
        label="🛑 Disable for this guild",
        style=discord.ButtonStyle.danger,
        custom_id="flag_manager:disable",
        row=1,
    )
    async def btn_disable(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self._apply_state(interaction, "off")

    @discord.ui.button(
        label="🔄 Refresh",
        style=discord.ButtonStyle.secondary,
        custom_id="flag_manager:refresh",
        row=1,
    )
    async def btn_refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not self.selected_flag or self.selected_flag == "__none__":
            await interaction.response.edit_message(
                embed=build_flag_manager_overview_embed(),
                view=self,
            )
            return
        details = await _resolve_flag_details(self.selected_flag, self.guild_id)
        await interaction.response.edit_message(
            embed=build_flag_detail_embed(details),
            view=self,
        )

    @discord.ui.button(
        label="↩ Back to Platform",
        style=discord.ButtonStyle.secondary,
        custom_id="flag_manager:back",
        row=4,
    )
    async def btn_back(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        from views.diagnostic.platform_panel import (
            _PlatformHubView,
            build_platform_hub_embed,
        )

        new_view = _PlatformHubView(self._author)
        await interaction.response.edit_message(
            embed=build_platform_hub_embed(),
            view=new_view,
        )
