"""SubsystemSettingsView — per-subsystem read-only drill-down (S5).

Renders the long-term subsystem-page shape:

* Header: subsystem display name + visibility tier + emoji.
* Scalar settings — pulled from :mod:`services.settings_resolution`
  per-guild so the panel shows the *current* effective value, its
  provenance, validity, and declared default.
* Bindings — declared :class:`BindingSpec`s with kind + required +
  hint.  The S5 view does NOT call into bindings runtime — it just
  shows the declared shape.  S7 onward consumes
  :func:`core.runtime.bindings.get_binding` to surface the current
  bound resource.
* Resource requirements — declared :class:`ResourceRequirement`s with
  priority + suggested name.
* Related cog panel — if the subsystem declares panel-shaped
  ``entry_points`` (anything ending in ``menu``), they are listed
  for quick reference.
* "↩ Back to Hub" button.

S5 is strictly read-only.  No edit / reset / mutate controls.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from utils.subsystem_registry import SUBSYSTEMS
from views.base import HubView

logger = logging.getLogger("bot.views.settings.subsystem_view")


_FIELD_VALUE_CAP = 1000


def _truncate(text: str, *, limit: int = _FIELD_VALUE_CAP) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


async def _resolve_settings_block(
    guild_id: int | None,
    subsystem: str,
) -> list[str]:
    """Return one rendered line per declared SettingSpec.

    Uses :func:`services.settings_resolution.resolve_setting` so the
    rendered value reflects current cache / KV state, the
    provenance, and the validity flag.  When ``guild_id`` is None
    (DM invocation) the value column shows the declared default.
    """
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None or not schema.settings:
        return []
    lines: list[str] = []
    if guild_id is None:
        for spec in schema.settings:
            lines.append(
                f"`{spec.name}` — type=`{spec.value_type.__name__}` "
                f"default=`{spec.default!r}` *(no guild context)*",
            )
        return lines
    from services.settings_resolution import resolve_setting

    for spec in schema.settings:
        try:
            resolution = await resolve_setting(guild_id, subsystem, spec.name)
        except Exception as exc:  # noqa: BLE001 — fail-soft per panel field
            lines.append(
                f"`{spec.name}` — ❌ resolver raised: "
                f"{type(exc).__name__}: {exc!s:.80}",
            )
            continue
        if resolution is None:
            lines.append(f"`{spec.name}` — *(resolver returned None)*")
            continue
        validity = "valid" if resolution.valid else "**invalid**"
        prov = resolution.provenance
        lines.append(
            f"`{spec.name}` = `{resolution.value!r}` "
            f"(`{prov}`, default=`{resolution.default!r}`, {validity})",
        )
    return lines


def _bindings_block(subsystem: str) -> list[str]:
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None or not schema.bindings:
        return []
    out: list[str] = []
    for spec in schema.bindings:
        required = "required" if spec.required else "optional"
        cap = f"cap=`{spec.capability_required}`" if spec.capability_required else ""
        out.append(
            f"`{spec.name}` — kind=`{spec.kind.value}` ({required}) {cap}".rstrip(),
        )
    return out


def _resources_block(subsystem: str) -> list[str]:
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None or not schema.resource_requirements:
        return []
    out: list[str] = []
    for req in schema.resource_requirements:
        suggested = (
            f" → `{req.provisioning.suggested_name}`"
            if req.provisioning.suggested_name
            else ""
        )
        out.append(
            f"`{req.intent}` — kind=`{req.kind.value}` "
            f"priority=`{req.provisioning.priority.value}`"
            f"{suggested} (binding=`{req.binding_name}`)",
        )
    return out


def _related_commands_block(subsystem: str) -> list[str]:
    """List the subsystem's entry_points so the operator can jump to
    the existing cog panel (e.g. ``!xpmenu``).  Read-only — this is
    just a documentation aid.
    """
    meta = SUBSYSTEMS.get(subsystem)
    if not meta:
        return []
    entry_points = meta.get("entry_points") or ()
    if not entry_points:
        return []
    return [f"`!{ep}`" for ep in entry_points]


async def build_subsystem_embed(
    interaction: discord.Interaction,
    subsystem: str,
) -> discord.Embed:
    """Build the per-subsystem read-only embed for ``!settings``.

    Args:
        interaction: The interaction whose ``guild_id`` drives
            per-guild value resolution.  ``None`` (DM) renders the
            schema declaration only.
        subsystem: The SUBSYSTEMS key.
    """
    meta = SUBSYSTEMS.get(subsystem) or {}
    title_emoji = meta.get("emoji", "⚙️")
    display = meta.get("display_name", subsystem)
    tier = meta.get("visibility_tier", "—")
    desc = meta.get("description", "")

    guild_id = interaction.guild_id

    embed = discord.Embed(
        title=f"{title_emoji} {display}",
        description=(
            f"_{desc}_\n"
            f"visibility tier: `{tier}`  ·  "
            f"subsystem key: `{subsystem}`"
        ),
        color=discord.Color.blurple(),
    )

    setting_lines = await _resolve_settings_block(guild_id, subsystem)
    if setting_lines:
        embed.add_field(
            name="Scalar settings",
            value=_truncate("\n".join(setting_lines)),
            inline=False,
        )
    else:
        embed.add_field(
            name="Scalar settings",
            value="*none declared*",
            inline=False,
        )

    binding_lines = _bindings_block(subsystem)
    if binding_lines:
        embed.add_field(
            name="Bindings",
            value=_truncate("\n".join(binding_lines)),
            inline=False,
        )

    resource_lines = _resources_block(subsystem)
    if resource_lines:
        embed.add_field(
            name="Provisionable resources",
            value=_truncate("\n".join(resource_lines)),
            inline=False,
        )

    related = _related_commands_block(subsystem)
    if related:
        embed.add_field(
            name="Existing command panels",
            value=", ".join(related),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"Read-only · S5.  Edit / reset arrive in S6.  "
            f"guild_id={guild_id if guild_id is not None else 'DM'}"
        ),
    )
    return embed


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_subsystem.back_to_hub",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.hub import SettingsHubView

        view = SettingsHubView(interaction.user)
        await interaction.response.edit_message(
            embed=SettingsHubView.build_embed(),
            view=view,
        )


class SubsystemSettingsView(HubView):
    """Per-subsystem read-only drill-down panel."""

    def __init__(self, author: Any, subsystem: str) -> None:
        super().__init__(author)
        self.subsystem = subsystem
        self.add_item(_BackToHubButton())


__all__ = ["SubsystemSettingsView", "build_subsystem_embed"]
