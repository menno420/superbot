"""UX Lab wing 3 — modal patterns: inputs, validation, preview-save, Label.

Includes the discord.py 2.6+ capability check: a ``Label``-wrapped select
inside a modal (the journal's old "modals are text-input only" rule is stale
on the 2.7 pin — this exhibit is the living proof either way).
"""

from __future__ import annotations

from typing import cast

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.MODALS
_MODAL_LIMITS = (
    "text input ≤ 4000 chars (paragraph) / 256 (short label)",
    "modals open only from an interaction (button/select/slash)",
    "a modal cannot open another modal from its on_submit",
)


def _header(title: str, body: str) -> discord.Embed:
    return discord.Embed(title=title, description=body, color=discord.Color.purple())


register(
    PatternSpec(
        pattern_id="modal_short_long",
        title="Short + paragraph inputs",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=(
            "rename / re-describe flows",
            "any free-text capture ≤ 2 fields",
        ),
        anti_patterns=("forms over ~4 fields — split into a wizard",),
        limits=_MODAL_LIMITS,
        notes="Required short field + optional paragraph; submit echoes both.",
    ),
)

register(
    PatternSpec(
        pattern_id="modal_label_select",
        title="Select inside a modal (Label, 2.6+)",
        category=_CAT,
        status=PatternStatus.EXPERIMENTAL,
        requires_modal=True,
        recommended_for=(
            "pick + describe in ONE round-trip (reason select + details)",
        ),
        anti_patterns=("entity picks — User/Role selects belong on views, not modals",),
        limits=(
            "Label text ≤ 45 chars, description ≤ 100",
            "probe P-07: verify which select types Discord accepts here",
            *_MODAL_LIMITS,
        ),
        notes=(
            "The capability the old 'modals are text-only' rule predates. "
            "If this modal renders with a working dropdown, the pin supports it."
        ),
    ),
)

register(
    PatternSpec(
        pattern_id="modal_validation_fail",
        title="Validation failure path",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=("numeric/state inputs that can be wrong",),
        anti_patterns=("silently clamping bad input — name the rule that failed",),
        limits=(
            "a failed modal cannot reopen itself — the error must carry "
            "enough context to retry",
            *_MODAL_LIMITS,
        ),
        notes="Enter anything non-numeric (or >100) to see the failure shape.",
    ),
)

register(
    PatternSpec(
        pattern_id="modal_preview_save",
        title="Modal → preview card → Save/Edit loop",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=(
            "anything user-visible after saving (welcome text, home embeds)",
        ),
        anti_patterns=("saving free text without showing it rendered first",),
        limits=_MODAL_LIMITS,
        adopted_by=("Home-message embed builder (Q-0059 mandatory preview)",),
        notes="Edit reopens the modal **prefilled** — drafts never retype.",
    ),
)

register(
    PatternSpec(
        pattern_id="modal_report_form",
        title="Report / feedback form",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=("member reports, suggestion boxes, contact-staff",),
        anti_patterns=("collecting more than the handling flow actually reads",),
        limits=_MODAL_LIMITS,
        notes="Submit renders the mod-queue card a staff channel would receive.",
    ),
)

register(
    PatternSpec(
        pattern_id="modal_template_editor",
        title="Template editor with variable preview",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=(
            "custom commands (trigger → template)",
            "welcome-message templates with {user}-style variables",
        ),
        anti_patterns=("free-form code-like templates without a rendered preview",),
        limits=_MODAL_LIMITS,
        notes="Uses {user} and {server} variables; submit shows them substituted.",
    ),
)


class _ShortLongModal(discord.ui.Modal, title="Rename the (fake) channel"):
    name: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="New name",
        placeholder="lounge",
        max_length=100,
    )
    topic: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Topic (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1024,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        topic = str(self.topic.value).strip() or "(unchanged)"
        await interaction.response.send_message(
            f"✅ (fake) Renamed to **#{self.name.value}** · topic: {topic}",
            ephemeral=True,
        )


class _LabelSelectModal(discord.ui.Modal, title="Report a message"):
    reason: discord.ui.Label[discord.ui.Modal] = discord.ui.Label(
        text="Reason",
        description="Why are you reporting this?",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="Spam", emoji="📣"),
                discord.SelectOption(label="Harassment", emoji="🚫"),
                discord.SelectOption(label="Other", emoji="❓"),
            ],
        ),
    )
    details: discord.ui.Label[discord.ui.Modal] = discord.ui.Label(
        text="Details",
        component=discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        ),
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        select = cast("discord.ui.Select[discord.ui.Modal]", self.reason.component)
        details = cast("discord.ui.TextInput[discord.ui.Modal]", self.details.component)
        picked = select.values[0] if select.values else "(none)"
        await interaction.response.send_message(
            f"📨 Reason **{picked}** · details: "
            f"{str(details.value).strip() or '—'}\n"
            "A select rendered inside a modal — the 2.6+ Label capability, "
            "live-verified by submitting this.",
            ephemeral=True,
        )


class _ValidationModal(discord.ui.Modal, title="Set warn threshold"):
    threshold: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Warnings before timeout (1–100)",
        placeholder="5",
        max_length=4,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = str(self.threshold.value).strip()
        if not raw.isdigit() or not 1 <= int(raw) <= 100:
            await interaction.response.send_message(
                f"❌ **`{raw}` is not a number between 1 and 100.**\n"
                "Nothing was saved. Press the button to try again — the error "
                "names the rule, so the retry needs no guesswork.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"✅ (fake) Warn threshold set to **{raw}**.",
            ephemeral=True,
        )


class _DraftModal(discord.ui.Modal, title="Welcome message draft"):
    def __init__(self, wing: ModalsWingView, *, prefill: str) -> None:
        super().__init__()
        self.text: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
            label="Welcome text",
            style=discord.TextStyle.paragraph,
            default=prefill or None,
            placeholder="Welcome {user} to {server}!",
            max_length=500,
        )
        self.add_item(self.text)
        self._wing = wing

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self._wing.state["draft"] = str(self.text.value)
        await self._wing.rerender(interaction)


class _ReportFormModal(discord.ui.Modal, title="Contact the staff"):
    subject: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Subject",
        max_length=100,
    )
    body: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="What happened?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        card = discord.Embed(
            title=f"📨 Staff inbox — {self.subject.value}",
            description=str(self.body.value),
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow(),
        )
        card.set_footer(text="The card a real staff channel would receive (fake)")
        await interaction.response.send_message(embed=card, ephemeral=True)


class _TemplateModal(discord.ui.Modal, title="Custom command editor"):
    trigger: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Trigger",
        placeholder="!hello",
        max_length=32,
    )
    template: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Response template",
        style=discord.TextStyle.paragraph,
        default="Hey {user}, welcome to {server}! 🎉",
        max_length=500,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        rendered = (
            str(self.template.value)
            .replace("{user}", interaction.user.display_name)
            .replace("{server}", interaction.guild.name if interaction.guild else "?")
        )
        await interaction.response.send_message(
            f"**`{self.trigger.value}` would answer:**\n{rendered}",
            ephemeral=True,
        )


class ModalsWingView(ExhibitWingView):
    """Wing 3 — modals."""

    WING_TITLE = "Modals"
    WING_EMOJI = "⌨️"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "modal_short_long",
            "modal_label_select",
            "modal_validation_fail",
            "modal_preview_save",
            "modal_report_form",
            "modal_template_editor",
        )

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        if pattern_id == "modal_preview_save":
            return self._ex_preview_save()
        launchers: dict[str, tuple[str, str, type[discord.ui.Modal]]] = {
            "modal_short_long": (
                "📝 Two inputs",
                "Required short field + optional paragraph.",
                _ShortLongModal,
            ),
            "modal_label_select": (
                "🧩 Select in a modal",
                "A Label-wrapped dropdown — pick a reason **inside** the modal.",
                _LabelSelectModal,
            ),
            "modal_validation_fail": (
                "🚧 Validation path",
                "Enter junk on purpose; the failure names the rule.",
                _ValidationModal,
            ),
            "modal_report_form": (
                "📨 Report form",
                "Subject + paragraph; submit renders the staff-queue card.",
                _ReportFormModal,
            ),
            "modal_template_editor": (
                "🔤 Template editor",
                "{user}/{server} variables, shown substituted on submit.",
                _TemplateModal,
            ),
        }
        title, body, modal_cls = launchers[pattern_id]
        btn = self.demo_button(
            "Open the modal",
            style=discord.ButtonStyle.primary,
            emoji="⌨️",
            row=0,
        )

        async def _open(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(modal_cls())

        btn.callback = _open  # type: ignore[method-assign]
        return ([_header(title, body)], [btn])

    def _ex_preview_save(self) -> ExhibitRender:
        draft: str = self.state.get("draft", "")
        items: list[discord.ui.Item[discord.ui.View]] = []
        edit = self.demo_button(
            "Edit draft…" if draft else "Write the draft…",
            style=discord.ButtonStyle.primary,
            emoji="✏️",
            row=0,
        )

        async def _edit(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_DraftModal(self, prefill=draft))

        edit.callback = _edit  # type: ignore[method-assign]
        items.append(edit)
        embeds = [
            _header(
                "💾 Preview before save",
                "Write a draft; it renders below **before** anything saves. "
                "Edit reopens the modal prefilled.",
            ),
        ]
        if draft:
            preview = discord.Embed(
                title="👋 Preview — as members would see it",
                description=draft.replace("{user}", "**AstroFox**").replace(
                    "{server}",
                    "**Demo Server**",
                ),
                color=discord.Color.green(),
            )
            embeds.append(preview)
            save = self.demo_button("Save", style=discord.ButtonStyle.success, row=0)

            async def _save(interaction: discord.Interaction) -> None:
                self.state.clear()
                await self.ack(
                    interaction,
                    "✅ (fake) Saved. A real flow writes through the audited "
                    "settings seam — preview was mandatory (Q-0059 precedent).",
                )

            save.callback = _save  # type: ignore[method-assign]
            items.append(save)
        return (embeds, items)
