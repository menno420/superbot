"""InvalidSettingsView — settings whose current value fails coercion (S5).

Walks every declared ``SettingSpec`` for the calling guild and reports
the ones that
:func:`services.settings_resolution.resolve_setting` flags as
``valid=False``.  In v1 that covers two cases:

* The KV row contains a value that cannot be coerced to the declared
  ``value_type`` (e.g. ``"abc"`` for an ``int`` spec).
* The KV row's coerced value is rejected by the spec's
  ``validator`` (raised ``ValueError`` or ``TypeError``).

Both cases fall back to the declared default at the resolver layer,
so production behaviour is safe.  This view surfaces the gap so an
operator can fix it.
"""

from __future__ import annotations

import discord

from views.base import HubView


async def build_invalid_embed(
    interaction: discord.Interaction,
) -> discord.Embed:
    embed = discord.Embed(
        title="⚠️ Invalid settings",
        description=(
            "Settings whose current KV value failed coercion or "
            "validation.  Resolver fell back to the declared default "
            "for runtime safety; fix the underlying KV row via the "
            "subsystem page's edit/reset control."
        ),
        color=discord.Color.orange(),
    )

    guild_id = interaction.guild_id
    if guild_id is None:
        embed.add_field(
            name="Result",
            value="*Run this from within a guild — DM has no scalar values to resolve.*",
            inline=False,
        )
        return embed

    from core.runtime.subsystem_schema import all_schemas
    from services.settings_resolution import resolve_setting

    invalid: list[str] = []
    scanned = 0
    for sub_name, schema in sorted(all_schemas().items()):
        for spec in schema.settings:
            scanned += 1
            try:
                resolution = await resolve_setting(guild_id, sub_name, spec.name)
            except Exception as exc:  # noqa: BLE001 — soft-fail per row
                invalid.append(
                    f"`{sub_name}.{spec.name}` — resolver raised {type(exc).__name__}",
                )
                continue
            if resolution is None or resolution.valid:
                continue
            diag = f" ({resolution.diagnostics[0]})" if resolution.diagnostics else ""
            invalid.append(
                f"`{sub_name}.{spec.name}` = `{resolution.raw!r}` "
                f"→ fallback to `{resolution.default!r}`{diag}",
            )

    if not invalid:
        embed.add_field(
            name="Result",
            value=f"*✅ No invalid settings.  ({scanned} setting(s) scanned.)*",
            inline=False,
        )
        return embed

    embed.add_field(
        name=f"Invalid settings ({len(invalid)} of {scanned} scanned)",
        value="\n".join(invalid)[:1024],
        inline=False,
    )
    embed.set_footer(text="S6 introduces the edit flow that fixes these in place.")
    return embed


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_invalid.back",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.hub import SettingsHubView

        view = await SettingsHubView.create(
            interaction.user,
            interaction.guild_id,
        )
        await interaction.response.edit_message(
            embed=SettingsHubView.build_embed(),
            view=view,
        )


class InvalidSettingsView(HubView):
    """Read-only diagnostic panel listing invalid resolutions."""

    def __init__(self, author) -> None:
        super().__init__(author)
        self.add_item(_BackToHubButton())


__all__ = ["InvalidSettingsView", "build_invalid_embed"]
