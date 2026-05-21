"""MissingBindingsView — bindings whose status is not ``bound`` (S5).

Read-only diagnostic that surfaces every declared :class:`BindingSpec`
for the calling guild whose runtime status is anything other than
``bound`` — typically ``unresolved`` (no binding row yet),
``missing`` (the target disappeared from Discord), or ``invalid``
(kind drift).
"""

from __future__ import annotations

import discord

from views.base import HubView


async def build_missing_bindings_embed(
    interaction: discord.Interaction,
) -> discord.Embed:
    embed = discord.Embed(
        title="🔗 Missing bindings",
        description=(
            "Declared bindings whose runtime status is not `bound`.  "
            "Includes unresolved slots (no row yet), targets that "
            "disappeared from Discord, and kind-drift cases.  Bind "
            "controls land alongside the setup wizard's binding "
            "section (planned)."
        ),
        color=discord.Color.gold(),
    )

    guild_id = interaction.guild_id
    if guild_id is None:
        embed.add_field(
            name="Result",
            value="*Run this from within a guild — DM has no per-guild binding state.*",
            inline=False,
        )
        return embed

    from core.runtime.bindings import get_binding
    from core.runtime.subsystem_schema import all_schemas

    rows: list[str] = []
    scanned = 0
    for sub_name, schema in sorted(all_schemas().items()):
        for spec in schema.bindings:
            scanned += 1
            try:
                value = await get_binding(guild_id, sub_name, spec.name)
            except Exception as exc:  # noqa: BLE001 — soft-fail per row
                rows.append(
                    f"`{sub_name}.{spec.name}` — get_binding raised "
                    f"{type(exc).__name__}",
                )
                continue
            if value.is_bound:
                continue
            required_marker = "**required**" if spec.required else "optional"
            rows.append(
                f"`{sub_name}.{spec.name}` ({required_marker}) — "
                f"status=`{value.status.value}` kind=`{spec.kind.value}`",
            )

    if not rows:
        embed.add_field(
            name="Result",
            value=f"*✅ Every binding is bound.  ({scanned} binding(s) scanned.)*",
            inline=False,
        )
        return embed

    embed.add_field(
        name=f"Unbound or invalid bindings ({len(rows)} of {scanned} scanned)",
        value="\n".join(rows)[:1024],
        inline=False,
    )
    return embed


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_missing_bindings.back",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.hub import SettingsHubView

        view = SettingsHubView(interaction.user)
        await interaction.response.edit_message(
            embed=SettingsHubView.build_embed(),
            view=view,
        )


class MissingBindingsView(HubView):
    """Read-only diagnostic panel listing unbound + invalid bindings."""

    def __init__(self, author) -> None:
        super().__init__(author)
        self.add_item(_BackToHubButton())


__all__ = ["MissingBindingsView", "build_missing_bindings_embed"]
