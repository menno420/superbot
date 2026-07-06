"""Role templates section — preview a built-in role bundle, stage creation.

Server-management PR13.  Surfaces the deterministic
:mod:`services.setup_role_templates` catalogue inside the setup wizard:

* the operator picks a built-in template (community hierarchy, moderation
  team, time/XP progression, …);
* the section previews it against the guild's current roles — which roles
  already exist (skipped) vs. which would be created;
* **"Stage new roles"** drafts one ``create_managed_role`` SetupOperation per
  missing role (carrying the role's cosmetic spec + any optional auto-role
  tier).

**Final Review remains the only apply gate** — this section never calls
``apply_operations`` and never imports a mutation pipeline; creation flows
through the audited ``RoleLifecycleService`` at apply time (the
``test_setup_operations_invariants`` AST check and
``test_role_templates_section`` both pin that).  Templates create roles for an
existing guild and **never grant permissions** — configure those separately
(e.g. the moderator-tier role in ``!settings → Moderation``).
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

import discord

from services import setup_draft, setup_session
from services import setup_role_templates as role_templates
from services.setup_operations import SetupOperation
from services.setup_role_templates import RoleSuggestion, RoleTemplate, TemplatePlan
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.role_templates")

SLUG = "role_templates"
SUBSYSTEM = "roles"

_MAX_PREVIEW_LINES = 12


def _normalise_name(name: str) -> str:
    """Slugify a role name for use as a per-role draft-slot discriminator."""
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "role"


def _op_label(s: RoleSuggestion) -> str:
    label = f"create role @{s.name}"
    if s.time_days:
        label += f" +{s.time_days}d"
    if s.xp_level:
        label += f" +L{s.xp_level}"
    return label


# ---------------------------------------------------------------------------
# Planning helper (reads the guild's current roles; pure delegation otherwise)
# ---------------------------------------------------------------------------


def _compute_plan(guild: discord.Guild, template: RoleTemplate) -> TemplatePlan:
    """Resolve ``template`` against the guild's live roles via role_templates."""
    existing: dict[str, int] = {}
    for role in getattr(guild, "roles", []) or []:
        name = getattr(role, "name", None)
        rid = getattr(role, "id", None)
        if name and rid is not None:
            existing[name.lower()] = rid
    me = getattr(guild, "me", None)
    perms = getattr(me, "guild_permissions", None)
    bot_can_manage = bool(getattr(perms, "manage_roles", False))
    return role_templates.plan_template(
        template,
        existing_roles=existing,
        bot_can_manage_roles=bot_can_manage,
    )


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def build_role_templates_embed() -> discord.Embed:
    """The picker embed — explains templates and lists the built-in catalogue."""
    embed = discord.Embed(
        title="🧩 Role templates",
        description=(
            "Pick a built-in template below to preview a set of roles, then "
            "stage the ones you don't have yet. **Staging creates nothing** — "
            "**Final review** applies the draft.\n\n"
            "Templates only *create roles* (for an existing server); they never "
            "grant permissions — set those up separately."
        ),
        color=discord.Color.blurple(),
    )
    for t in role_templates.list_templates():
        tiers = sum(1 for s in t.suggestions if s.time_days or s.xp_level)
        tier_note = f" · {tiers} auto-role tier(s)" if tiers else ""
        embed.add_field(
            name=f"{t.display_name} · {t.role_count} roles",
            value=f"{t.description}{tier_note}",
            inline=False,
        )
    embed.set_footer(
        text="Pick a template to preview · Final review applies staged roles.",
    )
    return embed


def build_template_preview_embed(
    template: RoleTemplate,
    plan: TemplatePlan,
) -> discord.Embed:
    """Render one template resolved against the guild (create vs. exists)."""
    embed = discord.Embed(
        title=f"🧩 {template.display_name}",
        description=template.description,
        color=discord.Color.blurple(),
    )
    lines: list[str] = []
    for p in plan.planned[:_MAX_PREVIEW_LINES]:
        s = p.suggestion
        attrs: list[str] = []
        if s.hoist:
            attrs.append("hoisted")
        if s.color:
            attrs.append(s.color)
        if s.time_days:
            attrs.append(f"{s.time_days}d tier")
        if s.xp_level:
            attrs.append(f"XP L{s.xp_level}")
        attr_str = f" ({', '.join(attrs)})" if attrs else ""
        if p.action == role_templates.ACTION_EXISTS:
            lines.append(f"✅ @{s.name}{attr_str} — already exists (skip)")
        else:
            lines.append(f"➕ @{s.name}{attr_str}")
    if len(plan.planned) > _MAX_PREVIEW_LINES:
        lines.append(f"_+{len(plan.planned) - _MAX_PREVIEW_LINES} more…_")
    embed.add_field(name="Roles", value="\n".join(lines) or "_(none)_", inline=False)
    embed.add_field(
        name="Summary",
        value=(
            f"➕ **{plan.create_count}** to create · "
            f"✅ {plan.exists_count} already exist"
        ),
        inline=False,
    )
    if plan.warnings:
        embed.add_field(
            name="⚠️ Heads up",
            value="\n".join(f"• {w}" for w in plan.warnings),
            inline=False,
        )
    embed.set_footer(
        text="“Stage new roles” adds them to the draft · Final review creates them.",
    )
    return embed


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


def _build_create_op(s: RoleSuggestion, *, template: RoleTemplate) -> SetupOperation:
    """Build one ``create_managed_role`` op for a template suggestion.

    ``binding_name`` carries a per-role slug only as a draft **slot key**
    discriminator: the replace-on-conflict index is
    ``(op_kind, subsystem, setting_name, binding_name)`` and does not include
    the role name, so without it every template role would collide on
    ``(create_managed_role, roles, '', '')`` and only the last would survive.
    The dispatcher reads ``resource_name`` + ``metadata['role_template']``,
    never ``binding_name``.
    """
    return SetupOperation(
        kind="create_managed_role",
        subsystem=SUBSYSTEM,
        binding_name=f"role:{_normalise_name(s.name)}",
        resource_name=s.name,
        resource_mode="create",
        metadata={
            "source": f"role_template:{template.slug}",
            "confidence": "high",
            "reason": f"{template.display_name}: {s.purpose or s.name}",
            "risk": "high",
            "rollback_note": (
                f"Delete @{s.name} in `!roles` or Discord role settings."
            ),
            "role_template": role_templates.suggestion_to_spec(
                s,
                template_slug=template.slug,
            ),
        },
    )


async def _stage_creations(
    interaction: discord.Interaction,
    *,
    template: RoleTemplate,
    plan: TemplatePlan,
) -> None:
    """Stage a ``create_managed_role`` op for each not-yet-existing role."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return

    to_create = plan.to_create
    if not to_create:
        await interaction.response.send_message(
            f"✅ Every role in **{template.display_name}** already exists — "
            "nothing to create.",
            ephemeral=True,
        )
        return

    staged = 0
    for planned in to_create:
        op = _build_create_op(planned.suggestion, template=template)
        try:
            await setup_draft.append(
                op,
                guild_id=guild.id,
                actor_id=interaction.user.id,
                label=_op_label(planned.suggestion),
                section_slug=SLUG,
            )
            staged += 1
        except Exception:
            logger.exception(
                "role_templates: setup_draft.append failed for %r",
                planned.suggestion.name,
            )

    if staged == 0:
        await interaction.response.send_message(
            "Could not stage the roles — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("role_templates: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("role_templates: setup_draft.count failed")
        pending = staged

    await interaction.response.send_message(
        f"✅ Staged **{staged}** new role(s) from **{template.display_name}** for "
        f"Final review. Pending operations: **{pending}**. Nothing is created "
        "until you apply.",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Detail view — template picker + stage button
# ---------------------------------------------------------------------------


class _TemplateSelect(discord.ui.Select):
    """Pick a built-in role template; drives the preview + stage button."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(
                label=t.display_name[:100],
                value=t.slug,
                description=f"{t.role_count} roles · {t.category}"[:100],
            )
            for t in role_templates.list_templates()
        ]
        super().__init__(
            placeholder="Pick a role template to preview…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, RoleTemplatesSectionView):
            await interaction.response.send_message(
                "This picker is no longer active — reopen the section.",
                ephemeral=True,
            )
            return
        await view.on_template_selected(interaction, self.values[0])


class RoleTemplatesSectionView(BaseView):
    """Detail view — a template picker (row 0) and a stage button (row 1).

    Used both as the section card's *Customize* target and the wizard-native
    step-detail view, so it stays within rows 0–3 (row 4 is reserved by
    ``views.setup.wizard_nav.render_step_detail``).  Selecting a template
    computes a fresh plan for the preview; the stage button **re-plans against
    the live guild** before staging so creation always reflects current roles.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self._selected_slug: str | None = None
        self._plan: TemplatePlan | None = None
        self._stage_button: discord.ui.Button | None = None
        self.add_item(_TemplateSelect())

    async def on_template_selected(
        self,
        interaction: discord.Interaction,
        slug: str,
    ) -> None:
        guild = interaction.guild
        template = role_templates.get_template(slug)
        if guild is None or template is None:
            await interaction.response.send_message(
                "Could not load that template.",
                ephemeral=True,
            )
            return
        self._selected_slug = slug
        self._plan = _compute_plan(guild, template)
        self._sync_stage_button()
        await interaction.response.edit_message(
            embed=build_template_preview_embed(template, self._plan),
            view=self,
        )

    def _sync_stage_button(self) -> None:
        n = self._plan.create_count if self._plan else 0
        if self._stage_button is None:
            self._stage_button = discord.ui.Button(  # type: ignore[var-annotated]
                style=discord.ButtonStyle.success,
                row=1,
            )
            self._stage_button.callback = self._on_stage  # type: ignore[method-assign]
            self.add_item(self._stage_button)
        self._stage_button.label = (
            f"Stage {n} new role{'s' if n != 1 else ''}"
            if n
            else "Nothing new to stage"
        )
        self._stage_button.disabled = n == 0

    async def _on_stage(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        template = role_templates.get_template(self._selected_slug or "")
        if guild is None or template is None:
            await interaction.response.send_message(
                "Pick a template first.",
                ephemeral=True,
            )
            return
        # Re-plan against the live guild before staging (a role may have been
        # created since the preview was rendered).
        plan = _compute_plan(guild, template)
        await _stage_creations(interaction, template=template, plan=plan)


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the template picker (the card's Customize target)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        embed=build_role_templates_embed(),
        view=RoleTemplatesSectionView(interaction.user),
        ephemeral=True,
    )


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Role-templates section entry — shows the section card.

    No auto-recommended path: creating roles is a deliberate choice the
    operator makes after previewing a template, never part of a blanket
    "apply all recommended" sweep.  ``recommended_ops_builder=None`` keeps the
    hub sweep from silently creating roles.
    """
    from views.setup.section_card import show

    detected = (
        "Built-in role bundles (community hierarchy, moderation team, time/XP "
        "progression, …). Click Customize to preview a template and stage the "
        "roles you don't have yet — Final review creates them. No permissions "
        "are ever granted."
    )
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
        recommended_ops_builder=None,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: Any = None,
    draft_rows: Any = None,
) -> discord.Embed:
    """Wizard-native detail embed for the role-templates step."""
    del guild, session, draft_rows
    return build_role_templates_embed()


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: Any = None,
) -> RoleTemplatesSectionView:
    """Wizard-native detail view for the role-templates step."""
    del section, guild, session
    return RoleTemplatesSectionView(author)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Role templates",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🧩",
        order=56,
        # ``create_managed_role`` is roles/template-specific (only this section
        # stages it), so it is safe to declare for accurate per-section
        # progress badges (unlike the shared ``set_setting`` / ``clear_binding``).
        op_kinds=frozenset({"create_managed_role"}),
        description_if_skipped=(
            "No template roles are created — the server keeps whatever roles it "
            "has. You can apply a role template later from `/setup` without "
            "re-running the whole wizard."
        ),
        depths=frozenset({"standard", "advanced"}),
        recommended_ops_builder=None,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "RoleTemplatesSectionView",
    "SLUG",
    "SUBSYSTEM",
    "build_role_templates_embed",
    "build_template_preview_embed",
    "run",
]
