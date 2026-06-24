"""Channels & log routing section — drafts channel bindings.

The wizard's first real planning section.  Lists every declared
``BindingSpec(kind=CHANNEL)`` across all registered subsystems, lets
the operator pick a channel for each via Discord's native
``ChannelSelect``, and stages a ``bind_channel`` SetupOperation in
the per-guild draft via :mod:`services.setup_draft`.

Flow:

1. Operator clicks "Channels & log routing".
2. Section reads the cached :class:`GuildSnapshot` from the hub
   (cached by the Server scan section in PR 4) when available; the
   snapshot powers the "Likely matches" hints next to each binding
   (scan classifier output from :mod:`views.setup.scan_panel`).
3. Operator picks one binding from a select.
4. A channel picker opens; the operator chooses a channel.
5. The pick stages a ``SetupOperation(kind="bind_channel", ...)``
   in the draft with metadata
   ``source="manual"|"scan"``, ``confidence``,
   ``reason``, ``risk="low"``, ``rollback_note=""``.
6. Nothing applies — Final Review owns the apply path.

No DB writes from this section beyond ``services.setup_draft``; no
Discord create calls (resource provisioning is a separate flow
landing in a later PR).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import discord

from services import setup_draft, setup_session
from services.guild_snapshot import GuildSnapshot
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView
from views.paginated_select import attach_windowed_select
from views.setup.scan_panel import (
    classify_snapshot,
    first_match,
)

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.channels")

SLUG = "channels"


# Map each known channel binding to a scan-classifier tag.  Drives the
# "Likely match: #..." hint we surface when the operator picks a binding
# whose name we recognise.
_BINDING_TO_TAG: dict[str, str] = {
    # logging
    "mod_channel": "likely_mod_log",
    "cleanup_channel": "likely_log",
    "debug_channel": "likely_log",
    "info_channel": "likely_log",
    "warning_channel": "likely_log",
    "error_channel": "likely_log",
    "audit_channel": "likely_log",
    # economy (binding name is ``log_channel`` — was wrongly keyed by the
    # legacy settings key ``economy_log_channel`` before the P0-3 retirement,
    # so this hint never fired).
    "log_channel": "likely_log",
    # xp (binding name is ``announce_channel`` — same legacy-key mismatch).
    "announce_channel": "likely_general",
}


# Maps each known binding to a :class:`services.channel_recommender.Intent`
# slug so the embed can surface the recommender's confidence + reason
# alongside the legacy "likely match" hint. Keeping these as two
# separate mappings (instead of derived from one) lets PR 8's intent
# catalogue evolve independently of the wizard's binding registry.
_BINDING_TO_INTENT: dict[str, str] = {
    "mod_channel": "mod_logs",
    "cleanup_channel": "logs",
    "debug_channel": "logs",
    "info_channel": "logs",
    "warning_channel": "logs",
    "error_channel": "logs",
    "audit_channel": "logs",
    "log_channel": "logs",
    "announce_channel": "general",
    "welcome_channel": "welcome",
}


_CONFIDENCE_GLYPH: dict[str, str] = {
    "high": "✅",
    "medium": "🟡",
    "low": "⬜",
}


# ---------------------------------------------------------------------------
# Binding discovery
# ---------------------------------------------------------------------------


def _all_channel_bindings() -> list[tuple[str, Any]]:
    """Return ``(subsystem, BindingSpec)`` for every declared CHANNEL binding."""
    from core.runtime.bindings import BindingKind
    from core.runtime.subsystem_schema import all_schemas

    out: list[tuple[str, Any]] = []
    for sub_name, schema in all_schemas().items():
        for binding in schema.bindings:
            if binding.kind == BindingKind.CHANNEL:
                out.append((sub_name, binding))
    return out


def _scan_match_for(snapshot: GuildSnapshot | None, binding_name: str) -> Any | None:
    """Return the snapshot ``ChannelMeta`` that the scan classifier
    associates with ``binding_name`` (or ``None`` if no match / no scan).
    """
    if snapshot is None:
        return None
    tag = _BINDING_TO_TAG.get(binding_name)
    if tag is None:
        return None
    return first_match(classify_snapshot(snapshot), tag)


def _recommendation_for(
    snapshot: GuildSnapshot | None,
    binding_name: str,
):
    """Return the top recommender pick for ``binding_name``, or ``None``.

    Layered on top of the legacy ``_scan_match_for`` so panels that
    have not opted into the recommender keep their existing hint
    behaviour; new code reads this helper for the richer payload
    (confidence + reason list).
    """
    if snapshot is None:
        return None
    intent_slug = _BINDING_TO_INTENT.get(binding_name)
    if intent_slug is None:
        return None
    from services.channel_recommender import top_pick

    return top_pick(intent_slug, snapshot)


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_channels_embed(snapshot: GuildSnapshot | None) -> discord.Embed:
    """Render the channels section's entry embed.

    Lists every declared CHANNEL binding grouped by subsystem with the
    "Likely match" hint when the scan classifier proposes a channel.
    """
    bindings = _all_channel_bindings()
    embed = discord.Embed(
        title="📡 Channels & log routing",
        description=(
            "Bind a channel for each subsystem's declared channel slot.  "
            "Each pick stages a `bind_channel` operation in the draft — "
            "nothing applies until Final review."
        ),
        color=discord.Color.blurple(),
    )
    if not bindings:
        embed.add_field(
            name="No channel bindings declared",
            value="_No registered subsystem currently declares a channel binding._",
            inline=False,
        )
        return embed

    grouped: dict[str, list[tuple[str, str]]] = {}
    for sub, binding in bindings:
        match = _scan_match_for(snapshot, binding.name)
        recommendation = _recommendation_for(snapshot, binding.name)
        required = " · *required*" if binding.required else ""
        if recommendation is not None:
            glyph = _CONFIDENCE_GLYPH.get(recommendation.confidence, "⬜")
            # Take the strongest single reason for compactness; the
            # full reason tuple is available to richer UI in follow-ups.
            top_reason = recommendation.reasons[0] if recommendation.reasons else ""
            match_str = (
                f" · {glyph} likely `#{recommendation.channel_name}` "
                f"({recommendation.confidence}"
                + (f" — {top_reason}" if top_reason else "")
                + ")"
            )
        elif match is not None:
            match_str = f" · likely `#{match.name}`"
        else:
            match_str = ""
        grouped.setdefault(sub, []).append(
            (binding.name, f"`{binding.name}`{required}{match_str}"),
        )

    for sub_name in sorted(grouped):
        lines = "\n".join(f"• {body}" for _, body in grouped[sub_name])
        embed.add_field(name=sub_name, value=lines, inline=False)

    embed.set_footer(text="Pick a binding from the select to choose a channel.")
    return embed


# ---------------------------------------------------------------------------
# Channel pick view
# ---------------------------------------------------------------------------


class _ChannelPickSelect(discord.ui.ChannelSelect):
    """Native channel picker — drafts a binding op on selection."""

    def __init__(
        self,
        *,
        subsystem: str,
        binding_name: str,
        scan_match_id: int | None,
    ) -> None:
        super().__init__(
            placeholder=f"Pick a channel for {subsystem}.{binding_name}",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.scan_match_id = scan_match_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.values:
            await interaction.response.send_message(
                "No channel picked.",
                ephemeral=True,
            )
            return
        picked = self.values[0]
        await _stage_channel_binding(
            interaction,
            subsystem=self.subsystem,
            binding_name=self.binding_name,
            target_id=picked.id,
            target_name=f"#{picked.name}",
            scan_match_id=self.scan_match_id,
        )


class _ChannelPickView(BaseView):
    """Native channel picker for one binding.  Drafts on pick."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        subsystem: str,
        binding_name: str,
        scan_match_id: int | None,
        timeout: int = 180,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.subsystem = subsystem
        self.binding_name = binding_name
        self.scan_match_id = scan_match_id
        self.add_item(
            _ChannelPickSelect(
                subsystem=subsystem,
                binding_name=binding_name,
                scan_match_id=scan_match_id,
            ),
        )


# ---------------------------------------------------------------------------
# Binding select (entry-point dropdown)
# ---------------------------------------------------------------------------


def _attach_binding_select(
    view: discord.ui.View,
    bindings: list[tuple[str, Any]],
    snapshot: GuildSnapshot | None,
) -> None:
    """Attach the declared-CHANNEL-binding picker to ``view``, paginated.

    More than Discord's 25-option select cap can be declared across all
    subsystems, so the options are *windowed* (◀/▶ nav) rather than
    front-truncated — every binding stays selectable (the #1040 class).
    Picking a binding opens its channel picker as an ephemeral.
    """
    index: dict[str, tuple[str, Any]] = {}
    options: list[discord.SelectOption] = []
    for sub, binding in bindings:
        key = f"{sub}::{binding.name}"
        label = f"{sub}.{binding.name}"
        match = _scan_match_for(snapshot, binding.name)
        description = (
            f"likely #{match.name}"[:100]
            if match is not None
            else (binding.hint or "")[:100]
        )
        options.append(
            discord.SelectOption(
                label=label[:100],
                value=key,
                description=description or None,
            ),
        )
        index[key] = (sub, binding)

    async def _on_pick(interaction: discord.Interaction, values: list[str]) -> None:
        key = values[0] if values else ""
        entry = index.get(key)
        if entry is None:
            await interaction.response.send_message(
                "No channel bindings declared by any subsystem.",
                ephemeral=True,
            )
            return
        sub, binding = entry
        match = _scan_match_for(snapshot, binding.name)
        picker = _ChannelPickView(
            interaction.user,
            subsystem=sub,
            binding_name=binding.name,
            scan_match_id=match.id if match is not None else None,
        )
        prefix = f"`{sub}.{binding.name}`"
        if match is not None:
            prefix += f" · scan suggests `#{match.name}`"
        await interaction.response.send_message(
            f"Pick a channel for {prefix}.",
            view=picker,
            ephemeral=True,
        )

    attach_windowed_select(
        view,
        options,
        _on_pick,
        placeholder="Pick a binding to set…",
        select_row=0,
        nav_row=1,
    )


class ChannelsSectionView(BaseView):
    """Entry view: lists bindings, hosts the picker dropdown."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        snapshot: GuildSnapshot | None,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        _attach_binding_select(self, _all_channel_bindings(), snapshot)


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


async def _stage_channel_binding(
    interaction: discord.Interaction,
    *,
    subsystem: str,
    binding_name: str,
    target_id: int,
    target_name: str,
    scan_match_id: int | None,
) -> None:
    """Append a ``bind_channel`` op to the guild's draft."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return

    # Metadata: when the operator picks the scan's suggested channel,
    # tag the op as source="scan" with high confidence; otherwise it
    # is a manual pick.
    if scan_match_id is not None and target_id == scan_match_id:
        metadata = {
            "source": "scan",
            "confidence": "high",
            "reason": f"Scan classifier matched channel name for {binding_name}",
            "risk": "low",
            "rollback_note": "",
        }
    else:
        metadata = {
            "source": "manual",
            "confidence": "high",
            "reason": f"Operator picked {target_name} for {binding_name}",
            "risk": "low",
            "rollback_note": "",
        }

    op = SetupOperation(
        kind="bind_channel",
        subsystem=subsystem,
        binding_name=binding_name,
        target_id=target_id,
        target_name=target_name,
        target_kind="channel",
    )
    label = f"{subsystem}.{binding_name} → {target_name}"
    try:
        await setup_draft.append(
            op,
            guild_id=guild.id,
            actor_id=interaction.user.id,
            label=label,
            metadata=metadata,
        )
    except Exception:
        logger.exception("channels: setup_draft.append failed")
        await interaction.response.send_message(
            "Could not stage the binding — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("channels: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("channels: setup_draft.count failed")
        pending = 0

    await interaction.response.send_message(
        (
            f"✅ Staged for Final review: `{subsystem}.{binding_name}` → {target_name}.  "
            f"Pending operations: **{pending}**."
        ),
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry point
# ---------------------------------------------------------------------------


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Detailed channel picker — opened by the section card's Customize."""
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return

    # Pick up the snapshot that the Server scan section cached on the
    # hub view.  When absent (operator never ran the scan), the
    # classifier hints simply do not appear — the section still works.
    snapshot: GuildSnapshot | None = None
    if hub is not None:
        try:
            from views.setup.sections.server_scan import get_cached_snapshot

            snapshot = get_cached_snapshot(hub)
        except Exception:
            logger.exception("channels: snapshot lookup raised")

    embed = build_channels_embed(snapshot)
    view = ChannelsSectionView(interaction.user, snapshot=snapshot)
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )


async def _recommended_channel_ops(
    guild: discord.Guild,
) -> list[SetupOperation]:
    """Stage ``bind_channel`` ops for every binding whose intent has a
    high-confidence channel recommendation.

    Walks :data:`_BINDING_TO_INTENT`, fetches the recommender's top
    pick per binding, and stages a bind op when the confidence is
    ``high``. Medium / low picks are intentionally skipped — they're
    not safe to auto-stage without operator confirmation, but the
    embed still surfaces them so the operator can customise.
    """
    from services import guild_snapshot
    from services.channel_recommender import top_pick

    try:
        snapshot = await guild_snapshot.collect(guild)
    except Exception:
        logger.exception("channels._recommended_channel_ops: snapshot failed")
        return []

    bindings = _all_channel_bindings()
    ops: list[SetupOperation] = []
    for subsystem, binding in bindings:
        intent = _BINDING_TO_INTENT.get(binding.name)
        if intent is None:
            continue
        pick = top_pick(intent, snapshot)
        if pick is None or pick.confidence != "high":
            continue
        ops.append(
            SetupOperation(
                kind="bind_channel",
                subsystem=subsystem,
                binding_name=binding.name,
                target_id=pick.channel_id,
                target_name=pick.channel_name,
                target_kind="channel",
            ),
        )
    return ops


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Channels section entry — shows the section card.

    The detailed channel picker is reachable via the card's
    Customize button; Apply Recommended stages bind ops for every
    high-confidence intent pick.
    """
    from views.setup.section_card import show

    detected = (
        "Channel-binding recommendations are computed live from the "
        "guild snapshot. Apply Recommended only stages high-confidence "
        "picks; use Customize to choose manually."
    )
    # ``recommended_ops_builder`` is read from the registered
    # ``SetupSection`` field by ``section_card.show`` — no need to
    # pass it explicitly here.
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
    session: Any = None,
    draft_rows: Any = None,
) -> discord.Embed:
    """Wizard-native detail embed for the channels step."""
    try:
        from services import guild_snapshot

        snapshot: GuildSnapshot | None = await guild_snapshot.collect(guild)
    except Exception:
        logger.exception("channels._build_detail_embed: snapshot collect failed")
        snapshot = None
    return build_channels_embed(snapshot)


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: Any = None,
) -> ChannelsSectionView:
    """Wizard-native detail view for the channels step.

    The snapshot is fetched lazily inside the picker callback when
    needed; constructing the view itself only requires the author.
    Mirrors the snapshot-less fallback path the legacy
    ``_customize_run`` already handled.
    """
    return ChannelsSectionView(author, snapshot=None)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Channels & log routing",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="📡",
        order=40,
        op_kinds=frozenset({"bind_channel", "clear_binding"}),
        description_if_skipped=(
            "SuperBot keeps the current command-channel rules and may not "
            "have a dedicated log channel. Configure these later in "
            "`!settings`."
        ),
        depths=frozenset({"quick", "standard", "advanced"}),
        recommended_ops_builder=_recommended_channel_ops,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "ChannelsSectionView",
    "SLUG",
    "build_channels_embed",
    "run",
]
