"""Logging presets section — Phase 5 of the setup-wizard plan.

Offers the operator four preset choices for routing SuperBot's log
channels:

* **Single** — one shared ``superbot-logs`` channel; every supported
  logging binding points there.  ``create_channel`` ops with the same
  ``resource_name`` share the channel via
  :func:`core.runtime.guild_resources.ensure_channel` (name-based
  reuse — see the Phase 5 plan for the dispatcher-contract analysis).
* **Balanced** — ``bot-logs`` for general logs (debug / info / warning /
  error / audit / cleanup / economy) and ``mod-logs`` for moderation
  events.  Two channels; every supported binding bound to one or the
  other.
* **Detailed** — one channel per logging binding.  Maximum separation
  for guilds that prefer fine-grained inboxes.
* **Custom** — bypasses the presets and opens the existing
  per-binding channel picker (``views.setup.sections.channels``).
  No ops staged; operator binds each channel manually.

Constraints enforced here:

* Each preset's :func:`_preset_*_ops` returns **only**
  ``create_channel`` ops.  No ``set_setting``, no ``add_automation_rule``,
  no invented binding names.
* Binding names come from ``_LOGGING_BINDING_INTENTS`` (mirrors the
  ``logs`` / ``mod_logs`` intents the existing
  ``views.setup.sections.channels._BINDING_TO_INTENT`` map declares).
* The section's ``recommended_ops_builder`` defaults to the Balanced
  preset; that's what wires the wizard's ``Apply Recommended``
  one-click flow.  The Customize button opens the picker view so an
  operator can choose a different preset.
* Staging routes through
  :func:`services.setup_draft.replace_recommended_for_section` so
  swapping presets cleanly removes prior recommended rows (no stale
  pre-Phase-5 ops linger when the operator changes their mind).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import discord

from services import setup_access, setup_draft, setup_session
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.logging_presets")

SLUG = "logging_presets"


# ---------------------------------------------------------------------------
# Logging-binding catalogue
# ---------------------------------------------------------------------------
#
# Mirrors the ``logs`` / ``mod_logs`` intents declared in
# ``views.setup.sections.channels._BINDING_TO_INTENT``.  Kept as a
# narrow local map so the logging-presets module doesn't import the
# wider channels-section internals; adding a new logging binding
# requires updating both maps, which is small and intentional.


@dataclass(frozen=True)
class LoggingBinding:
    """One logging-related channel binding the wizard knows about.

    ``intent`` is ``"general_logs"`` or ``"mod_logs"``; the Balanced
    preset uses this to partition bindings between ``bot-logs`` and
    ``mod-logs``.
    """

    subsystem: str
    binding_name: str
    intent: str  # "general_logs" | "mod_logs"
    detailed_channel_name: str  # used by the Detailed preset


_LOGGING_BINDINGS: tuple[LoggingBinding, ...] = (
    LoggingBinding(
        subsystem="moderation",
        binding_name="mod_channel",
        intent="mod_logs",
        detailed_channel_name="mod-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="cleanup_channel",
        intent="general_logs",
        detailed_channel_name="cleanup-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="debug_channel",
        intent="general_logs",
        detailed_channel_name="debug-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="info_channel",
        intent="general_logs",
        detailed_channel_name="info-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="warning_channel",
        intent="general_logs",
        detailed_channel_name="warning-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="error_channel",
        intent="general_logs",
        detailed_channel_name="error-logs",
    ),
    LoggingBinding(
        subsystem="logging",
        binding_name="audit_channel",
        intent="general_logs",
        detailed_channel_name="audit-logs",
    ),
    LoggingBinding(
        subsystem="economy",
        binding_name="log_channel",
        intent="general_logs",
        detailed_channel_name="economy-logs",
    ),
)


def _supported_bindings() -> tuple[LoggingBinding, ...]:
    """Filter ``_LOGGING_BINDINGS`` to those whose subsystem +
    binding actually exists at runtime.

    The wizard ships with a static catalogue; sections that bind
    against unloaded subsystems would surface as ``not_yet_implemented``
    at apply time.  Filtering here lets the embed render an accurate
    "Bindings covered" preview.  The check is duck-typed against
    :mod:`core.runtime.subsystem_schema` so a future binding deletion
    surfaces immediately instead of staging an op that will fail.
    """
    try:
        from core.runtime.bindings import BindingKind
        from core.runtime.subsystem_schema import all_schemas
    except Exception:
        logger.exception(
            "logging_presets._supported_bindings: schema lookup failed",
        )
        return _LOGGING_BINDINGS

    runtime = all_schemas()
    out: list[LoggingBinding] = []
    for entry in _LOGGING_BINDINGS:
        schema = runtime.get(entry.subsystem)
        if schema is None:
            continue
        match = next(
            (
                b
                for b in schema.bindings
                if b.name == entry.binding_name and b.kind == BindingKind.CHANNEL
            ),
            None,
        )
        if match is None:
            continue
        out.append(entry)
    return tuple(out)


# ---------------------------------------------------------------------------
# Preset ops builders
# ---------------------------------------------------------------------------


def _build_create_op(
    entry: LoggingBinding,
    *,
    resource_name: str,
) -> SetupOperation:
    """One ``create_channel`` op covering ``entry``.

    The dispatcher's ``_apply_resource_create`` routes this through
    :class:`services.resource_provisioning.ResourceProvisioningPipeline`
    which, on a name match, returns the existing channel (see
    :func:`core.runtime.guild_resources.ensure_channel`) and binds it
    to the slot.  That's how the Single and Balanced presets share a
    channel across multiple bindings without inventing a
    ``bind_existing`` op shape.
    """
    return SetupOperation(
        kind="create_channel",
        subsystem=entry.subsystem,
        binding_name=entry.binding_name,
        resource_name=resource_name,
        resource_mode="create",
        target_kind="channel",
    )


def _preset_single_ops(
    bindings: tuple[LoggingBinding, ...],
    *,
    channel_name: str = "superbot-logs",
) -> list[SetupOperation]:
    """Stage N ``create_channel`` ops all pointing at ``channel_name``.

    The first op creates the channel; subsequent ops reuse it via
    name-based ensure_channel lookup and bind their slots to the
    same target.
    """
    return [_build_create_op(b, resource_name=channel_name) for b in bindings]


def _preset_balanced_ops(
    bindings: tuple[LoggingBinding, ...],
    *,
    general_name: str = "bot-logs",
    mod_name: str = "mod-logs",
) -> list[SetupOperation]:
    """Two-channel split: ``general_logs`` intent → ``bot-logs``,
    ``mod_logs`` intent → ``mod-logs``.
    """
    ops: list[SetupOperation] = []
    for b in bindings:
        name = mod_name if b.intent == "mod_logs" else general_name
        ops.append(_build_create_op(b, resource_name=name))
    return ops


def _preset_detailed_ops(
    bindings: tuple[LoggingBinding, ...],
) -> list[SetupOperation]:
    """One ``create_channel`` per binding using ``detailed_channel_name``."""
    return [
        _build_create_op(b, resource_name=b.detailed_channel_name) for b in bindings
    ]


# ---------------------------------------------------------------------------
# Recommended-ops builder — wires the wizard's ``Apply Recommended``
# one-click flow to the Balanced preset.
# ---------------------------------------------------------------------------


async def _recommended_logging_ops(
    guild: Any,
    **_kwargs: Any,
) -> list[SetupOperation]:
    """Default-preset ops used by the wizard / hub's Apply Recommended.

    Phase 2's :func:`call_recommended_ops_builder` passes ``guild`` /
    ``session`` / ``purpose`` / ``depth`` / ``section_slug``; this
    builder only needs ``guild`` and accepts the rest via ``**kwargs``
    so the adapter doesn't have to special-case its signature.

    The Balanced preset is the safest default — two purpose-built
    channels covering every supported binding.  Operators who want a
    different shape pick via the Customize → preset picker (the
    :class:`LoggingPresetsView`).
    """
    del guild
    bindings = _supported_bindings()
    if not bindings:
        return []
    return _preset_balanced_ops(bindings)


# ---------------------------------------------------------------------------
# Section card embed
# ---------------------------------------------------------------------------


def build_logging_presets_embed(
    supported: tuple[LoggingBinding, ...],
    *,
    current_preset: str | None = None,
) -> discord.Embed:
    """Render the picker embed.

    Surfaces each preset with the channel name(s) it would create and
    the binding count covered.  Highlights the operator's current pick
    when ``current_preset`` is provided.  The current pick is derived
    from the draft (see :func:`infer_current_preset`) when the section
    is reopened.
    """
    embed = discord.Embed(
        title="📜 Logging presets",
        description=(
            "Pick how SuperBot routes its log channels.  Every preset "
            "stages **`create_channel`** operations only — Final "
            "Review confirms before any channel is touched.  Switching "
            "presets cleanly removes the prior pick's staged rows."
        ),
        color=discord.Color.blurple(),
    )

    binding_count = len(supported)
    counts_by_intent = {
        intent: sum(1 for b in supported if b.intent == intent)
        for intent in ("general_logs", "mod_logs")
    }

    embed.add_field(
        name=("✅ Single" if current_preset == "single" else "Single"),
        value=(
            f"One channel `#superbot-logs`.  Binds **{binding_count}** "
            "logging slot(s).  Lowest overhead; everything in one inbox."
        ),
        inline=False,
    )
    embed.add_field(
        name=("✅ Balanced" if current_preset == "balanced" else "Balanced"),
        value=(
            f"`#bot-logs` for general logs "
            f"(**{counts_by_intent['general_logs']}** slot(s)) and "
            f"`#mod-logs` for moderation "
            f"(**{counts_by_intent['mod_logs']}** slot(s))."
        ),
        inline=False,
    )
    embed.add_field(
        name=("✅ Detailed" if current_preset == "detailed" else "Detailed"),
        value=(
            f"One channel per slot — **{binding_count}** purpose-built "
            "channels (`#audit-logs`, `#mod-logs`, `#debug-logs`, …)."
        ),
        inline=False,
    )
    embed.add_field(
        name="Custom",
        value=(
            "Skip the preset and bind each channel yourself via the "
            "**Customize** button below.  No operations staged."
        ),
        inline=False,
    )

    # Q-0109 privacy disclosure — server event logging can surface the
    # content of edited/deleted messages to staff. Off by default; opt in
    # per-category via !settings → Logging. Surfacing it here satisfies the
    # owner requirement that the wizard discloses it.
    embed.add_field(
        name="🔒 Privacy — server event logging",
        value=(
            "Server event logging (message edits/deletions, joins/leaves, "
            "role changes) is **off by default**.  If you enable message "
            "logging, **staff can see the content of messages members "
            "edited or deleted**.  Turn categories on per-server in "
            "`!settings → Logging`."
        ),
        inline=False,
    )

    embed.set_footer(
        text=(
            "Nothing applies until Final Review.  Switching presets "
            "replaces the prior pick — your staged custom bindings "
            "stay intact."
        ),
    )
    return embed


def infer_current_preset(
    draft_rows: list[Any],
) -> str | None:
    """Return ``"single"`` / ``"balanced"`` / ``"detailed"`` based on the
    recommended rows this section owns.

    Reads the typed :class:`services.setup_draft.DraftOperationRow`
    objects, filters to ``section_slug == SLUG`` AND
    ``staging_kind == "recommended"``, and infers the preset from the
    distinct ``resource_name`` values:

    * 1 unique name → single
    * 2 unique names matching (bot-logs, mod-logs) → balanced
    * N unique names (one per binding) → detailed

    Returns ``None`` when no rows or a non-preset pattern is found —
    the embed renders without a highlight.
    """
    own_rows = [
        row
        for row in draft_rows
        if getattr(row, "section_slug", None) == SLUG
        and getattr(row, "staging_kind", None) == "recommended"
    ]
    if not own_rows:
        return None
    names = {
        row.op.resource_name
        for row in own_rows
        if row.op.kind == "create_channel" and row.op.resource_name
    }
    if len(names) == 1:
        return "single"
    if names == {"bot-logs", "mod-logs"}:
        return "balanced"
    if len(names) >= 3:
        # Detailed uses one channel per binding, so unique-name count
        # tracks binding count.  3+ distinct names is detailed in
        # every realistic catalogue size.
        return "detailed"
    return None


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------


class LoggingPresetsView(BaseView):
    """Picker view with one button per preset.

    Mutating buttons (the three preset buttons) re-check
    :func:`services.setup_access.can_apply_setup` against a fresh
    session snapshot — same pattern as Phase 1's section card and
    Phase 3's wizard.  Custom delegates to the channels section's
    detail view.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        hub: SetupHubView | None,
        supported: tuple[LoggingBinding, ...],
        current_preset: str | None,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self._hub = hub
        self._supported = supported
        self.current_preset = current_preset
        self._populate_buttons()

    def _populate_buttons(self) -> None:
        for preset_key, label, emoji in (
            ("single", "Single channel", "📥"),
            ("balanced", "Balanced", "📚"),
            ("detailed", "Detailed", "🗂"),
        ):
            highlighted = preset_key == self.current_preset
            button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
                label=label,
                style=(
                    discord.ButtonStyle.success
                    if highlighted
                    else discord.ButtonStyle.secondary
                ),
                emoji=emoji,
                custom_id=f"setup_logging_preset:{preset_key}",
                row=0,
            )
            button.callback = self._make_preset_callback(preset_key)  # type: ignore[method-assign]
            self.add_item(button)

        customize: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Custom",
            style=discord.ButtonStyle.primary,
            emoji="🛠",
            custom_id="setup_logging_preset:custom",
            row=0,
        )
        customize.callback = self._on_custom  # type: ignore[method-assign]
        self.add_item(customize)

        cancel: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            custom_id="setup_logging_preset:cancel",
            row=1,
        )
        cancel.callback = self._on_cancel  # type: ignore[method-assign]
        self.add_item(cancel)

    async def _gate_apply(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use this from inside the server.",
                ephemeral=True,
            )
            return False
        session = None
        guild_id = interaction.guild_id
        if guild_id is not None:
            try:
                session = await setup_session.resume_session(guild_id)
            except Exception:
                logger.exception(
                    "logging_presets._gate_apply: resume failed",
                )
                session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "stage logging presets.  Ask the owner to grant you "
                "`/setup-delegate`.",
                ephemeral=True,
            )
            return False
        return True

    def _make_preset_callback(self, preset_key: str):
        async def _callback(interaction: discord.Interaction) -> None:
            if not await self._gate_apply(interaction):
                return
            guild_id = interaction.guild_id
            if guild_id is None:
                await interaction.response.send_message(
                    "This can only be used in a server.",
                    ephemeral=True,
                )
                return
            if not self._supported:
                await interaction.response.send_message(
                    "No logging bindings are available in this runtime.",
                    ephemeral=True,
                )
                return

            if preset_key == "single":
                ops = _preset_single_ops(self._supported)
            elif preset_key == "balanced":
                ops = _preset_balanced_ops(self._supported)
            elif preset_key == "detailed":
                ops = _preset_detailed_ops(self._supported)
            else:  # pragma: no cover — defensive; the picker only registers
                # the three preset slugs through this factory.
                await interaction.response.send_message(
                    f"Unknown preset {preset_key!r}.",
                    ephemeral=True,
                )
                return

            try:
                result = await setup_draft.replace_recommended_for_section(
                    guild_id,
                    SLUG,
                    ops,
                    actor_id=interaction.user.id,
                    labels={
                        idx: (
                            f"[{preset_key}] {op.subsystem}.{op.binding_name} "
                            f"→ #{op.resource_name}"
                        )
                        for idx, op in enumerate(ops)
                    },
                )
            except Exception:
                logger.exception(
                    "logging_presets: replace_recommended failed (preset=%s)",
                    preset_key,
                )
                await interaction.response.send_message(
                    "Could not stage the preset — see logs.",
                    ephemeral=True,
                )
                return

            try:
                await setup_session.unmark_section_skipped(guild_id, SLUG)
            except Exception:
                logger.exception("logging_presets: unmark skip failed")

            # Repaint with the new highlight.
            self.current_preset = preset_key
            self.clear_items()
            self._populate_buttons()
            embed = build_logging_presets_embed(
                self._supported,
                current_preset=preset_key,
            )
            await interaction.response.edit_message(embed=embed, view=self)

            staged = len(result.inserted_seqs)
            noun = "operation" if staged == 1 else "operations"
            extra = ""
            if result.conflicts:
                cn = len(result.conflicts)
                conflict_word = "row" if cn == 1 else "rows"
                extra = (
                    f"\n\n⚠️ Preserved **{cn} custom / preset {conflict_word}** "
                    "at conflicting slot(s); no overwrite."
                )
            await interaction.followup.send(
                f"✅ Staged **{staged} {noun}** for the **{preset_key}** "
                f"preset.  Open Final Review to apply.{extra}",
                ephemeral=True,
            )

        return _callback

    async def _on_custom(self, interaction: discord.Interaction) -> None:
        # Custom delegates to the channels section's detail picker so
        # operators who want fine-grained control don't have to leave
        # the wizard.  We don't gate _gate_apply here because the
        # channels section's mutating buttons already enforce it.
        from views.setup.sections.channels import _customize_run

        try:
            await _customize_run(interaction, self._hub)
        except Exception:
            logger.exception("logging_presets._on_custom: customize_run failed")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Could not open the channel picker — see logs.",
                    ephemeral=True,
                )

    async def _on_cancel(self, interaction: discord.Interaction) -> None:
        for child in self.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(view=self)
        self.stop()


# ---------------------------------------------------------------------------
# Section entry points
# ---------------------------------------------------------------------------


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """``Customize`` callback for the section card.

    Opens the :class:`LoggingPresetsView` picker.  Operators who want
    to skip the preset entirely click that view's ``Custom`` button
    which delegates to the channels section's detailed picker.
    """
    guild_id = interaction.guild_id
    supported = _supported_bindings()
    draft_rows = []
    if guild_id is not None:
        try:
            draft_rows = await setup_draft.list_rows(guild_id)
        except Exception:
            logger.exception("logging_presets.customize: list_rows failed")
    current = infer_current_preset(draft_rows)
    embed = build_logging_presets_embed(supported, current_preset=current)
    view = LoggingPresetsView(
        interaction.user,
        hub=hub,
        supported=supported,
        current_preset=current,
    )
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Section entry — opens the standard section card.

    The card surfaces ``Apply Recommended`` (Balanced preset) and
    ``Customize`` (the four-preset picker).  Skip and Hub work as in
    every other section card.
    """
    from views.setup.section_card import show

    detected = (
        "Logging presets stage create_channel ops only; Final Review "
        "confirms before any channel is touched.  Apply Recommended "
        "stages the **Balanced** preset (one general log channel + "
        "one mod log channel).  Customize opens the picker so you "
        "can choose Single / Balanced / Detailed / Custom."
    )
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: object = None,
    draft_rows: object = None,
) -> discord.Embed:
    """Wizard-native detail embed for the logging-presets step."""
    del session, guild
    supported = _supported_bindings()
    rows = list(draft_rows) if draft_rows is not None else []
    current = infer_current_preset(rows)
    return build_logging_presets_embed(supported, current_preset=current)


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: object = None,
) -> LoggingPresetsView:
    """Wizard-native detail view for the logging-presets step."""
    del section, guild, session
    return LoggingPresetsView(
        author,
        hub=None,
        supported=_supported_bindings(),
        current_preset=None,
    )


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Logging presets",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="📜",
        # Renders right after channels (order 40); both touch
        # channel bindings so neighbouring them in the wizard
        # makes the step order intuitive.
        order=45,
        # Both kinds stage through Final Review; ``create_channel`` is
        # what every preset emits, ``bind_channel`` is reserved for
        # future operator-picked existing channels in the Custom path.
        op_kinds=frozenset({"create_channel", "bind_channel"}),
        description_if_skipped=(
            "SuperBot keeps the existing channel routing.  You can "
            "still bind individual log channels via `!settings` or "
            "the Channels section."
        ),
        depths=frozenset({"quick", "standard", "advanced"}),
        recommended_ops_builder=_recommended_logging_ops,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "LoggingBinding",
    "LoggingPresetsView",
    "SLUG",
    "build_logging_presets_embed",
    "infer_current_preset",
    "run",
]
