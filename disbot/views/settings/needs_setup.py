"""NeedsSetupView — subsystems whose declared shape is missing setup (S5).

Read-only diagnostic that lists subsystems whose
:class:`SubsystemSchema` declares required bindings or required
resource requirements.  In v1 the "needs setup" signal is the set
of declared *required* binding slots — the actual binding-row
status (bound vs unresolved) lives on the
:class:`MissingBindingsView`.  This panel is the planning view: it
shows what each subsystem *expects* to be configured before it
can fully function.
"""

from __future__ import annotations

import discord

from utils.subsystem_registry import SUBSYSTEMS
from views.base import HubView


def _gather_required_bindings() -> dict[str, list[str]]:
    """Return ``{subsystem: [required binding names]}``."""
    from core.runtime.subsystem_schema import all_schemas

    out: dict[str, list[str]] = {}
    for name, schema in sorted(all_schemas().items()):
        required = [b.name for b in schema.bindings if b.required]
        if required:
            out[name] = required
    return out


def _gather_required_resources() -> dict[str, list[str]]:
    """Return ``{subsystem: [required resource intents]}``."""
    from core.runtime.resource_specs import ProvisioningPriority
    from core.runtime.subsystem_schema import all_schemas

    out: dict[str, list[str]] = {}
    for name, schema in sorted(all_schemas().items()):
        required = [
            r.intent
            for r in schema.resource_requirements
            if r.provisioning.priority == ProvisioningPriority.REQUIRED
        ]
        if required:
            out[name] = required
    return out


async def build_needs_setup_embed(
    interaction: discord.Interaction,
) -> discord.Embed:
    del interaction  # guild-independent view — uses declarations only
    embed = discord.Embed(
        title="📋 Needs setup",
        description=(
            "Subsystems whose schema declares **required** bindings or "
            "resource requirements.  This shows what _should_ be "
            "configured; the *bound vs unresolved* status of each slot "
            "lives in the **Missing bindings** view."
        ),
        color=discord.Color.gold(),
    )
    bindings = _gather_required_bindings()
    resources = _gather_required_resources()

    if not bindings and not resources:
        embed.add_field(
            name="Result",
            value="*No subsystem declares any required bindings or resources.*",
            inline=False,
        )
        return embed

    if bindings:
        lines = [
            f"`{sub}` — required: {', '.join(f'`{b}`' for b in names)}"
            for sub, names in sorted(bindings.items())
        ]
        embed.add_field(
            name=f"Required bindings ({sum(len(v) for v in bindings.values())})",
            value="\n".join(lines)[:1024],
            inline=False,
        )

    if resources:
        lines = [
            f"`{sub}` — required: {', '.join(f'`{r}`' for r in names)}"
            for sub, names in sorted(resources.items())
        ]
        embed.add_field(
            name=f"Required resources ({sum(len(v) for v in resources.values())})",
            value="\n".join(lines)[:1024],
            inline=False,
        )

    # Display-only count to give an at-a-glance read of subsystem coverage.
    declared_subs = {s for s in SUBSYSTEMS}
    embed.set_footer(
        text=(
            f"{len(bindings)} subsystem(s) with required bindings · "
            f"{len(resources)} with required resources · "
            f"{len(declared_subs)} subsystems total."
        ),
    )
    return embed


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_needs_setup.back",
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


class NeedsSetupView(HubView):
    """Read-only diagnostic panel listing required bindings + resources."""

    def __init__(self, author) -> None:
        super().__init__(author)
        self.add_item(_BackToHubButton())


__all__ = ["NeedsSetupView", "build_needs_setup_embed"]
