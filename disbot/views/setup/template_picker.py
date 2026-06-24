"""Setup-wizard template picker (PR-D).

The wizard launcher's **Choose Preset** button opens
:class:`TemplatePickerView`, which lists every operator-facing
:class:`AutomationTemplate` grouped by category. Picking one opens
:class:`TemplateConfigView`, which prompts for the template's required
overrides (channel id, role id) and routes the apply through
:class:`services.automation_mutation.AutomationMutationPipeline.create_rule`.

Rules are created **disabled** (``enabled=False`` per migration 032
line 74); the operator must flip them on via ``!automation enable``
once the scheduler is also activated by
``AUTOMATION_SCHEDULER_ENABLED=true``. That two-key activation
matches the safety policy in the reconciliation plan §7.

No DB writes from this module — every mutation routes through the
audited pipeline so the audit publisher records it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

from services.automation_templates import (
    TEMPLATES,
    AutomationTemplate,
    get_template,
)
from views.base import BaseView

logger = logging.getLogger("bot.views.setup.template_picker")


_CATEGORY_LABELS: dict[str, str] = {
    "onboarding": "Onboarding",
    "server_pulse": "Server pulse",
    "channels": "Channels",
    "uncategorized": "Other",
}


@dataclass(frozen=True)
class ApplyOutcome:
    """Outcome of :func:`apply_template_to_guild`."""

    ok: bool
    rule_id: int | None
    template_slug: str
    detail: str


def _category_label(category: str) -> str:
    return _CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def build_picker_embed() -> discord.Embed:
    """Embed listing categories and a hint about the activation policy."""
    embed = discord.Embed(
        title="📦 Choose a preset",
        description=(
            "Pick an automation template to install in this server.\n\n"
            "Every template is created **disabled** — once configured, "
            "flip it on via `!automation enable <name>` (the automation "
            "scheduler must also be activated server-side via "
            "`AUTOMATION_SCHEDULER_ENABLED=true`)."
        ),
        color=discord.Color.blurple(),
    )
    counts: dict[str, int] = {}
    for tmpl in TEMPLATES:
        counts[tmpl.category] = counts.get(tmpl.category, 0) + 1
    lines = [
        f"• **{_category_label(cat)}** — {n} template(s)"
        for cat, n in sorted(counts.items())
    ]
    if lines:
        embed.add_field(
            name="Available categories",
            value="\n".join(lines),
            inline=False,
        )
    embed.set_footer(text="Owner-gated. No rule runs until you enable it.")
    return embed


def _select_options() -> list[discord.SelectOption]:
    options: list[discord.SelectOption] = []
    # Discord caps Select options at 25; we currently have 14 onboarding
    # + server_pulse templates so we fit, but the slice is defensive.
    for tmpl in list(TEMPLATES)[:25]:
        label = f"[{_category_label(tmpl.category)}] {tmpl.display_name}"[:100]
        description = tmpl.description[:100]
        options.append(
            discord.SelectOption(
                label=label,
                description=description,
                value=tmpl.slug,
            ),
        )
    return options


class _TemplatePickerSelect(discord.ui.Select):
    """Single Select listing every known template across categories."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a template…",
            options=_select_options(),
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        slug = self.values[0]
        template = get_template(slug)
        if template is None:
            await interaction.response.send_message(
                f"Template `{slug}` not found.",
                ephemeral=True,
            )
            return
        config = TemplateConfigView(interaction.user, template=template)
        await interaction.response.send_message(
            embed=build_template_config_embed(template),
            view=config,
            ephemeral=True,
        )


class TemplatePickerView(BaseView):
    """Owner-gated picker — lists every template via a single Select."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.add_item(_TemplatePickerSelect())


# ---------------------------------------------------------------------------
# Per-template configuration view
# ---------------------------------------------------------------------------


def build_template_config_embed(
    template: AutomationTemplate,
    *,
    outcome: ApplyOutcome | None = None,
) -> discord.Embed:
    """Render the per-template embed.

    Three states: pre-apply (lists details + required overrides),
    post-apply success (green, names the rule id), post-apply
    failure (red, names the error).
    """
    if outcome is not None and outcome.ok:
        return discord.Embed(
            title=f"✅ Installed: {template.display_name}",
            description=(
                f"`automation_rules.id = {outcome.rule_id}` created "
                f"**disabled**. Flip on via "
                f"`!automation enable {template.slug}`."
            ),
            color=discord.Color.green(),
        )
    if outcome is not None and not outcome.ok:
        return discord.Embed(
            title=f"❌ Could not install: {template.display_name}",
            description=outcome.detail,
            color=discord.Color.red(),
        )

    embed = discord.Embed(
        title=f"📦 {template.display_name}",
        description=template.description,
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Category",
        value=_category_label(template.category),
        inline=True,
    )
    embed.add_field(name="Trigger", value=template.trigger_kind, inline=True)
    embed.add_field(name="Action", value=template.action_kind, inline=True)
    if template.required_overrides:
        embed.add_field(
            name="Required overrides",
            value=", ".join(f"`{k}`" for k in template.required_overrides),
            inline=False,
        )
    else:
        embed.add_field(
            name="Required overrides",
            value="_None — applies with defaults._",
            inline=False,
        )
    embed.set_footer(
        text="Rules are created disabled. You enable them after review.",
    )
    return embed


class _ChannelPick(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer

        view = self.view
        if isinstance(view, TemplateConfigView):
            view.selected_channel_id = self.values[0].id
        await safe_defer(interaction)


class _RolePick(discord.ui.RoleSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a role…",
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer

        view = self.view
        if isinstance(view, TemplateConfigView):
            view.selected_role_id = self.values[0].id
        await safe_defer(interaction)


class TemplateConfigView(BaseView):
    """Single-template config + apply panel.

    Attributes:
        template: the :class:`AutomationTemplate` being configured.
        selected_channel_id: filled in by :class:`_ChannelPick`.
        selected_role_id: filled in by :class:`_RolePick`.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        template: AutomationTemplate,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=public, timeout=timeout)
        self.template = template
        self.selected_channel_id: int | None = None
        self.selected_role_id: int | None = None
        if "channel_id" in template.required_overrides:
            self.add_item(_ChannelPick())
        if "role_id" in template.required_overrides:
            self.add_item(_RolePick())

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.success, row=2)
    async def _apply(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        # Validate required overrides are filled.
        missing: list[str] = []
        if "channel_id" in self.template.required_overrides:
            if self.selected_channel_id is None:
                missing.append("channel_id")
        if "role_id" in self.template.required_overrides:
            if self.selected_role_id is None:
                missing.append("role_id")
        if missing:
            await interaction.response.send_message(
                "Pick a value for the required override(s) first: "
                + ", ".join(f"`{m}`" for m in missing),
                ephemeral=True,
            )
            return

        outcome = await apply_template_to_guild(
            template=self.template,
            guild_id=guild.id,
            guild_owner_id=guild.owner_id or 0,
            channel_id=self.selected_channel_id,
            role_id=self.selected_role_id,
            actor_id=interaction.user.id,
        )
        await interaction.response.send_message(
            embed=build_template_config_embed(self.template, outcome=outcome),
            ephemeral=True,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, row=2)
    async def _cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        del button
        await interaction.response.send_message(
            f"Cancelled — `{self.template.slug}` was NOT installed.",
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# Apply helper (routes through the audited mutation pipeline)
# ---------------------------------------------------------------------------


async def apply_template_to_guild(
    *,
    template: AutomationTemplate,
    guild_id: int,
    guild_owner_id: int,
    channel_id: int | None,
    role_id: int | None,
    actor_id: int,
) -> ApplyOutcome:
    """Create one ``automation_rules`` row from a template (disabled).

    Routes through :class:`AutomationMutationPipeline.create_rule` so
    audit + event emission happen consistently. The pipeline already
    creates rules with ``enabled=False`` by default (migration 032
    line 74); we never override.
    """
    from services.automation_mutation import (
        AutomationMutationPipeline,
        InvalidAutomationConfigError,
    )

    trigger_overrides: dict[str, Any] = {}
    action_overrides: dict[str, Any] = {}
    if channel_id is not None:
        # Channel-id can appear in either side depending on the
        # action kind; the registry validator will reject any that
        # don't apply.
        if "channel_id" in template.default_action_config:
            action_overrides["channel_id"] = channel_id
        if "channel_id" in template.default_trigger_config:
            trigger_overrides["channel_id"] = channel_id
    if role_id is not None:
        if "role_id" in template.default_action_config:
            action_overrides["role_id"] = role_id
        if "role_id" in template.default_trigger_config:
            trigger_overrides["role_id"] = role_id

    pipeline = AutomationMutationPipeline()
    try:
        result = await pipeline.create_rule(
            guild_id=guild_id,
            guild_owner_id=guild_owner_id,
            name=template.slug,
            trigger_kind=template.trigger_kind,
            action_kind=template.action_kind,
            trigger_config=template.merged_trigger_config(trigger_overrides),
            action_config=template.merged_action_config(action_overrides),
            actor_id=actor_id,
            actor_type="platform_owner",
        )
    except InvalidAutomationConfigError as exc:
        logger.warning(
            "template apply rejected for slug=%s guild=%d: %s",
            template.slug,
            guild_id,
            exc,
        )
        return ApplyOutcome(
            ok=False,
            rule_id=None,
            template_slug=template.slug,
            detail=f"Validation failed: {exc}",
        )
    except Exception as exc:
        logger.exception(
            "template apply crashed for slug=%s guild=%d",
            template.slug,
            guild_id,
        )
        return ApplyOutcome(
            ok=False,
            rule_id=None,
            template_slug=template.slug,
            detail=f"{type(exc).__name__}: {exc}",
        )

    return ApplyOutcome(
        ok=True,
        rule_id=result.rule_id,
        template_slug=template.slug,
        detail="created disabled",
    )


__all__ = [
    "ApplyOutcome",
    "TemplateConfigView",
    "TemplatePickerView",
    "apply_template_to_guild",
    "build_picker_embed",
    "build_template_config_embed",
]
