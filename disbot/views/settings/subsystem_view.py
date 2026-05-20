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


def attach_back_to_settings_button(
    view: discord.ui.View,
    author: discord.Member | discord.User,
    subsystem: str,
) -> None:
    """Append a "↩ Back to Settings" control to a sub-view opened from this panel.

    Mirrors :func:`cogs.help_cog._attach_back_to_help_button` and
    :func:`cogs.admin_cog.attach_back_to_admin_button`.  The button
    rebuilds a fresh :class:`SubsystemSettingsView` on click so the
    embed reflects current setting / binding state.  No-op if the
    sub-view already has 25 components (Discord cap).
    """
    if len(view.children) >= 25:
        logger.warning(
            "Back-to-settings button skipped — %s already has 25 children.",
            type(view).__name__,
        )
        return

    btn = discord.ui.Button(  # type: ignore[var-annotated]
        label="↩ Back to Settings",
        custom_id="settings:back",
        style=discord.ButtonStyle.secondary,
        row=4,
    )

    async def _back_callback(interaction: discord.Interaction) -> None:
        new_view = SubsystemSettingsView(author, subsystem)
        embed = await build_subsystem_embed(interaction, subsystem)
        await interaction.response.edit_message(embed=embed, view=new_view)

    btn.callback = _back_callback  # type: ignore[method-assign]
    view.add_item(btn)


class _OpenRelatedPanelButton(discord.ui.Button):
    """Route from a subsystem settings page to the related cog panel.

    At click time, look up the cog that owns the subsystem and call
    its :func:`build_help_menu_view` hook (the same hook the help
    menu uses).  When the cog or hook is missing, render a fallback
    embed listing the subsystem's entry_points so the operator can
    still discover the typed commands.
    """

    def __init__(self, subsystem: str) -> None:
        self.subsystem = subsystem
        super().__init__(
            label="Open Panel",
            emoji="🪟",
            style=discord.ButtonStyle.blurple,
            custom_id="settings_subsystem.open_panel",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer, safe_edit

        if not await safe_defer(interaction):
            return
        bot = interaction.client
        cog = _resolve_cog_for_subsystem(bot, self.subsystem)
        hook = getattr(cog, "build_help_menu_view", None) if cog else None
        if not callable(hook):
            fallback = _build_no_panel_embed(self.subsystem)
            await safe_edit(interaction, embed=fallback, view=self.view)
            return
        try:
            sub_embed, sub_view = await hook(interaction)
        except Exception as exc:  # noqa: BLE001 — navigation must not crash panel
            logger.warning(
                "Settings → cog panel open failed (subsystem=%r): %s",
                self.subsystem,
                exc,
                exc_info=True,
            )
            msg = str(exc)[:200]
            embed = discord.Embed(
                title="Could not open cog panel",
                description=f"`{self.subsystem}` → `{type(exc).__name__}`: {msg}",
                color=discord.Color.orange(),
            )
            await safe_edit(interaction, embed=embed, view=self.view)
            return
        attach_back_to_settings_button(sub_view, interaction.user, self.subsystem)
        await safe_edit(interaction, embed=sub_embed, view=sub_view)


def _resolve_cog_for_subsystem(bot: Any, subsystem: str) -> Any:
    """Find the cog matching ``subsystem`` by entry-point intersection.

    Delegates to :func:`cogs.help_cog._cog_for_subsystem` so the
    settings-to-cog navigation uses the exact same resolution logic
    the help menu uses — no parallel router.
    """
    try:
        from cogs.help_cog import _cog_for_subsystem
    except Exception:  # noqa: BLE001 — help cog must be loaded for this path
        return None
    try:
        return _cog_for_subsystem(bot, subsystem)
    except Exception:  # noqa: BLE001 — never crash navigation
        return None


def _build_no_panel_embed(subsystem: str) -> discord.Embed:
    """Fallback embed shown when no cog hook exists for the subsystem."""
    meta = SUBSYSTEMS.get(subsystem) or {}
    display = meta.get("display_name", subsystem)
    entry_points = list(meta.get("entry_points") or ())
    embed = discord.Embed(
        title=f"No interactive panel for {display}",
        description=(
            "This subsystem does not expose a panel hook.  Use the "
            "typed commands below to interact with it."
        ),
        color=discord.Color.orange(),
    )
    if entry_points:
        embed.add_field(
            name="Typed commands",
            value=", ".join(f"`!{ep}`" for ep in entry_points),
            inline=False,
        )
    else:
        embed.add_field(
            name="Typed commands",
            value="*(no entry_points declared)*",
            inline=False,
        )
    embed.set_footer(text="Click ↩ Back to Hub to return to Settings.")
    return embed


# ---------------------------------------------------------------------------
# S6 edit + reset selects.  Dispatch to the widget appropriate for the
# SettingSpec.value_type / allowed_values shape.  See the per-widget
# modules under :mod:`views.settings.edit_*` for the mutation paths.
# ---------------------------------------------------------------------------


def _editable_specs(subsystem: str) -> list:
    """Return SettingSpec instances we can edit (subset that has a settings_key)."""
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None:
        return []
    return [spec for spec in schema.settings if spec.settings_key]


class _EditSettingSelect(discord.ui.Select):
    """Select listing every editable SettingSpec for the subsystem.

    Picking a setting dispatches to the appropriate edit widget:
    bool toggles directly; int/float/str-without-allowed_values pop
    a modal; str-with-allowed_values shows an enum select view.
    """

    def __init__(self, subsystem: str, specs: list) -> None:
        self.subsystem = subsystem
        # Cap to Discord's 25-option limit; surface what we can.
        options: list[discord.SelectOption] = []
        for spec in specs[:25]:
            options.append(
                discord.SelectOption(
                    label=spec.name[:100],
                    value=spec.name,
                    description=f"type={spec.value_type.__name__}"[:100],
                ),
            )
        super().__init__(
            placeholder="Edit a setting…",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        name = self.values[0]
        from core.runtime.subsystem_schema import get_schema
        from services.settings_resolution import resolve_setting

        schema = get_schema(self.subsystem)
        spec = None
        if schema is not None:
            for s in schema.settings:
                if s.name == name:
                    spec = s
                    break
        if spec is None:
            await interaction.response.send_message(
                f"❌ Unknown setting `{self.subsystem}.{name}`.",
                ephemeral=True,
            )
            return

        guild_id = interaction.guild_id
        current = spec.default
        if guild_id is not None:
            resolution = await resolve_setting(guild_id, self.subsystem, name)
            if resolution is not None:
                current = resolution.value

        parent_msg = interaction.message

        # Dispatch by explicit input_hint first (PR #7); fall through
        # to the value_type / allowed_values rules so settings that
        # don't opt into the new modes keep their existing widget.
        hint = (spec.input_hint or "").strip().lower()
        if hint == "channel":
            from views.settings.edit_channel import ChannelSettingSelectView

            view = ChannelSettingSelectView(self.subsystem, name, parent_msg)
            await interaction.response.send_message(
                f"Pick a channel for `{self.subsystem}.{name}` "
                f"(current=`{current!r}`):",
                view=view,
                ephemeral=True,
            )
            return
        if hint == "role":
            from views.settings.edit_role import RoleSettingSelectView

            view = RoleSettingSelectView(self.subsystem, name, parent_msg)
            await interaction.response.send_message(
                f"Pick a role for `{self.subsystem}.{name}` "
                f"(current=`{current!r}`):",
                view=view,
                ephemeral=True,
            )
            return
        if hint == "numeric_presets" and spec.presets:
            from views.settings.edit_number_presets import NumericPresetsView

            view = NumericPresetsView(
                subsystem=self.subsystem,
                setting_name=name,
                value_type=spec.value_type,
                current_value=current,
                default_value=spec.default,
                presets=spec.presets,
                parent_message=parent_msg,
            )
            await interaction.response.send_message(
                f"Pick a value for `{self.subsystem}.{name}` "
                f"(current=`{current!r}`, default=`{spec.default!r}`):",
                view=view,
                ephemeral=True,
            )
            return

        # Default routing — unchanged from S6.
        if spec.value_type is bool:
            from views.settings.edit_boolean import toggle_setting

            await toggle_setting(interaction, self.subsystem, name, parent_msg)
            return
        if spec.value_type is str and spec.allowed_values:
            from views.settings.edit_enum import EnumSettingSelectView

            view = EnumSettingSelectView(
                self.subsystem,
                name,
                spec.allowed_values,
                current,
                parent_msg,
            )
            await interaction.response.send_message(
                f"Pick a new value for `{self.subsystem}.{name}`:",
                view=view,
                ephemeral=True,
            )
            return
        if spec.value_type is int or spec.value_type is float:
            from views.settings.edit_number import NumberSettingModal

            modal = NumberSettingModal(
                self.subsystem,
                name,
                spec.value_type,
                current,
                spec.default,
                parent_msg,
            )
            await interaction.response.send_modal(modal)
            return
        # Free-form string.
        from views.settings.edit_text import TextSettingModal

        modal = TextSettingModal(
            self.subsystem,
            name,
            current,
            spec.default,
            parent_msg,
        )
        await interaction.response.send_modal(modal)


class _ResetSettingSelect(discord.ui.Select):
    """Select listing every resettable SettingSpec for the subsystem."""

    def __init__(self, subsystem: str, specs: list) -> None:
        self.subsystem = subsystem
        options: list[discord.SelectOption] = []
        for spec in specs[:25]:
            options.append(
                discord.SelectOption(
                    label=f"Reset {spec.name}"[:100],
                    value=spec.name,
                    description=f"default={spec.default!r}"[:100],
                ),
            )
        super().__init__(
            placeholder="Reset a setting to its default…",
            min_values=1,
            max_values=1,
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.reset_button import reset_setting

        name = self.values[0]
        await reset_setting(
            interaction,
            self.subsystem,
            name,
            interaction.message,
        )


def _editable_bindings(subsystem: str) -> list:
    """Return BindingSpec instances editable by the Settings Manager.

    The Settings Manager binding-edit widget supports channel / role /
    category / thread targets; ``MEMBER`` bindings (rare) are filtered
    out so the dropdown only offers slots the widget can actually edit.
    """
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None:
        return []
    editable_kinds = {"channel", "role", "category", "thread"}
    return [
        spec
        for spec in schema.bindings
        if getattr(spec.kind, "value", str(spec.kind)) in editable_kinds
    ]


def _provisionable_resources(subsystem: str) -> list:
    """Return ResourceRequirement instances that map to an editable binding.

    A resource requirement is launchable from the Settings Manager only
    when its ``binding_name`` points at a declared, editable
    BindingSpec.  Requirements without a binding cross-link are skipped
    because we have no slot to write back into.
    """
    from core.runtime.subsystem_schema import get_schema

    schema = get_schema(subsystem)
    if schema is None:
        return []
    binding_names = {spec.name for spec in _editable_bindings(subsystem)}
    return [
        req
        for req in schema.resource_requirements
        if req.binding_name and req.binding_name in binding_names
    ]


class _EditBindingSelect(discord.ui.Select):
    """Select listing every editable BindingSpec for the subsystem.

    Picking a binding opens the appropriate :class:`BindingEditView`
    for that binding's kind.
    """

    def __init__(self, subsystem: str, specs: list) -> None:
        self.subsystem = subsystem
        options: list[discord.SelectOption] = []
        for spec in specs[:25]:
            kind_value = getattr(spec.kind, "value", str(spec.kind))
            options.append(
                discord.SelectOption(
                    label=spec.name[:100],
                    value=spec.name,
                    description=f"kind={kind_value}"[:100],
                ),
            )
        super().__init__(
            placeholder="Edit a binding…",
            min_values=1,
            max_values=1,
            options=options,
            row=3,
        )
        self._specs_by_name = {spec.name: spec for spec in specs}

    async def callback(self, interaction: discord.Interaction) -> None:
        name = self.values[0]
        spec = self._specs_by_name.get(name)
        if spec is None:
            await interaction.response.send_message(
                f"❌ Unknown binding `{self.subsystem}.{name}`.",
                ephemeral=True,
            )
            return
        kind_value = getattr(spec.kind, "value", str(spec.kind))
        parent_msg = interaction.message
        from views.settings.edit_binding import BindingEditView

        try:
            view = BindingEditView(
                self.subsystem,
                name,
                kind_value,
                parent_msg,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                f"❌ Cannot edit binding: {exc}",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Pick a {kind_value} for `{self.subsystem}.{name}`:",
            view=view,
            ephemeral=True,
        )


class _ProvisionResourceSelect(discord.ui.Select):
    """Select listing provisionable resource requirements for the subsystem.

    Picking a resource opens the :class:`ProvisionResourceView` with the
    Use-existing / Create-new actions for that slot.
    """

    def __init__(self, subsystem: str, requirements: list) -> None:
        self.subsystem = subsystem
        options: list[discord.SelectOption] = []
        for req in requirements[:25]:
            kind_value = getattr(req.kind, "value", str(req.kind))
            options.append(
                discord.SelectOption(
                    label=f"{req.binding_name} ({kind_value})"[:100],
                    value=req.binding_name,
                    description=(req.description or req.intent)[:100],
                ),
            )
        super().__init__(
            placeholder="Provision a resource…",
            min_values=1,
            max_values=1,
            options=options,
            row=4,
        )
        self._requirements_by_binding = {req.binding_name: req for req in requirements}

    async def callback(self, interaction: discord.Interaction) -> None:
        binding_name = self.values[0]
        req = self._requirements_by_binding.get(binding_name)
        if req is None:
            await interaction.response.send_message(
                f"❌ Unknown resource requirement `{binding_name}`.",
                ephemeral=True,
            )
            return
        kind_value = getattr(req.kind, "value", str(req.kind))
        from views.settings.provision_resource import ProvisionResourceView

        view = ProvisionResourceView(
            self.subsystem,
            binding_name,
            kind_value,
            interaction.message,
        )
        await interaction.response.send_message(
            f"Provision `{self.subsystem}.{binding_name}` ({kind_value}): "
            "pick an existing resource or create a new one.",
            view=view,
            ephemeral=True,
        )


class SubsystemSettingsView(HubView):
    """Per-subsystem panel: read-only embed + edit/reset/binding/provision selects."""

    def __init__(self, author: Any, subsystem: str) -> None:
        super().__init__(author)
        self.subsystem = subsystem
        self.add_item(_BackToHubButton())
        self.add_item(_OpenRelatedPanelButton(subsystem))
        specs = _editable_specs(subsystem)
        if specs:
            self.add_item(_EditSettingSelect(subsystem, specs))
            self.add_item(_ResetSettingSelect(subsystem, specs))
        bindings = _editable_bindings(subsystem)
        if bindings:
            self.add_item(_EditBindingSelect(subsystem, bindings))
        resources = _provisionable_resources(subsystem)
        if resources:
            self.add_item(_ProvisionResourceSelect(subsystem, resources))


__all__ = [
    "SubsystemSettingsView",
    "attach_back_to_settings_button",
    "build_subsystem_embed",
]
