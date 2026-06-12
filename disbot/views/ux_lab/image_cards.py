"""UX Lab wing 6 — PIL-generated image cards.

Reuse first: the mining inventory/stat renderers and the gear paper-doll
compositor are exhibited with sample data, not re-implemented. The three
*candidate* cards (welcome / leaderboard image / event poster) come from
``utils/ux_patterns/image_builders.py``. Every render runs in
``asyncio.to_thread`` (CPU-bound), reports duration + bytes against the
8 MiB bot cap, and attaches alt text — the platform-limits doc §4 rules,
demonstrated live.
"""

from __future__ import annotations

import asyncio
import io
import time
from collections.abc import Callable

import discord

from core.runtime.interaction_helpers import safe_defer
from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from utils.ux_patterns.image_builders import (
    render_event_poster,
    render_leaderboard_image,
    render_welcome_card,
)
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.IMAGE
_IMG_LIMITS = (
    "~8 MiB bot attachment cap (413 above)",
    "JPEG/WebP for composites; PNG only for transparency/pixel art",
    "PIL is CPU-bound — render inside asyncio.to_thread",
    "alt text via the attachment description field (≤1024 chars)",
)

_SAMPLE_INVENTORY: list[tuple[str, int]] = [
    ("stone", 240),
    ("iron ore", 87),
    ("gold ore", 31),
    ("diamond", 6),
    ("magma shard", 2),
]
_SAMPLE_LOADOUT: dict[str, str] = {
    "tool": "iron pickaxe",
    "light": "lantern",
    "helmet": "iron helmet",
    "chestplate": "iron chestplate",
    "leggings": "iron leggings",
    "boots": "iron boots",
    "weapon": "iron sword",
    "shield": "wooden shield",
    "charm": "lucky charm",
}


def _img_spec(
    pattern_id: str,
    title: str,
    *,
    status: PatternStatus,
    recommended_for: tuple[str, ...],
    adopted_by: tuple[str, ...] = (),
    notes: str = "",
) -> None:
    register(
        PatternSpec(
            pattern_id=pattern_id,
            title=title,
            category=_CAT,
            status=status,
            requires_pil=True,
            recommended_for=recommended_for,
            adopted_by=adopted_by,
            limits=_IMG_LIMITS,
            notes=notes or "🎨 Render draws the card with sample data.",
        ),
    )


_img_spec(
    "pil_inventory_card",
    "Inventory card (shipped renderer)",
    status=PatternStatus.STABLE,
    recommended_for=("compact item-quantity grids beyond embed-field comfort",),
    adopted_by=("views/mining/main_panel.py (live since #665)",),
)
_img_spec(
    "pil_stat_card",
    "Stat card (shipped renderer)",
    status=PatternStatus.STABLE,
    recommended_for=("profile-style number walls with a custom look",),
    adopted_by=("views/mining/character_panel.py (live since #665)",),
)
_img_spec(
    "pil_character_paperdoll",
    "Gear paper-doll compositor (shipped renderer)",
    status=PatternStatus.STABLE,
    recommended_for=("equipment visualisation; sprite packs drop in by file",),
    adopted_by=("mining gear panel (live since #702)",),
    notes="Placeholder shapes render where no sprite PNG exists — the owner "
    "pack upgrades it without code changes.",
)
_img_spec(
    "pil_welcome_card",
    "Welcome card (Q-0110 phase-2 candidate)",
    status=PatternStatus.EXPERIMENTAL,
    recommended_for=("the welcome service's phase-2 card (vs embed-only v1)",),
    notes="Uses the no-network initials disc — the avatar-download fallback "
    "path a real implementation needs anyway.",
)
_img_spec(
    "pil_leaderboard_image",
    "Leaderboard image (candidate)",
    status=PatternStatus.EXPERIMENTAL,
    recommended_for=("a flashier monthly-winners post; NOT the live board",),
)
_img_spec(
    "pil_event_poster",
    "Event poster (Q-0112 candidate)",
    status=PatternStatus.EXPERIMENTAL,
    recommended_for=("scheduled-event announcements above the RSVP buttons",),
)


def _render_inventory() -> bytes | None:
    from utils.mining_render import build_card_spec, render_inventory_card

    spec = build_card_spec(
        "AstroFox's satchel",
        _SAMPLE_INVENTORY,
        footer="UX Lab sample data",
    )
    return render_inventory_card(spec)


def _render_stat_card() -> bytes | None:
    from utils.mining_render import build_stat_card_spec, render_stat_card

    spec = build_stat_card_spec(
        "AstroFox",
        level=42,
        xp_bar="█████████░ 90%",
        location="Magma Chambers (-740m)",
        deepest="Crystal Hollow (-810m)",
        gear_lines=[("tool", "Iron Pickaxe (18/40)"), ("light", "Lantern")],
        coins=13_370,
        net_worth=21_205,
    )
    return render_stat_card(spec)


def _render_paperdoll() -> bytes | None:
    from utils.character_render import render_character_for

    return render_character_for(dict(_SAMPLE_LOADOUT))


_RENDERERS: dict[str, tuple[Callable[[], bytes | None], str, str]] = {
    # pattern_id -> (renderer, filename, alt text)
    "pil_inventory_card": (
        _render_inventory,
        "uxlab-inventory.png",
        "Inventory card: 5 sample items with quantities in coloured rows",
    ),
    "pil_stat_card": (
        _render_stat_card,
        "uxlab-stats.png",
        "Stat card for AstroFox: level 42, XP bar, location, gear, coins",
    ),
    "pil_character_paperdoll": (
        _render_paperdoll,
        "uxlab-paperdoll.png",
        "Paper-doll figure wearing a full sample iron loadout",
    ),
    "pil_welcome_card": (
        lambda: render_welcome_card(),
        "uxlab-welcome.jpg",
        "Welcome card greeting AstroFox as member #1235 of Demo Server",
    ),
    "pil_leaderboard_image": (
        lambda: render_leaderboard_image(),
        "uxlab-leaderboard.jpg",
        "Leaderboard image: top five members as horizontal score bars",
    ),
    "pil_event_poster": (
        lambda: render_event_poster(),
        "uxlab-poster.jpg",
        "Event poster for Movie Night, Friday 20:00 CET, hosted by AstroFox",
    ),
}


class ImageWingView(ExhibitWingView):
    """Wing 6 — PIL image cards."""

    WING_TITLE = "PIL cards"
    WING_EMOJI = "🎨"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return tuple(_RENDERERS)

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        renderer, filename, alt = _RENDERERS[pattern_id]
        header = discord.Embed(
            title=f"🎨 {pattern_id}",
            description=(
                "**🎨 Render** draws the card from sample data in a worker "
                "thread and posts it with alt text + size/time stats."
            ),
            color=discord.Color.dark_magenta(),
        )
        btn = self.demo_button(
            "🎨 Render the card",
            style=discord.ButtonStyle.primary,
            row=0,
        )

        async def _render(interaction: discord.Interaction) -> None:
            if not await safe_defer(interaction, ephemeral=True):
                return
            start = time.perf_counter()
            png = await asyncio.to_thread(renderer)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if png is None:
                await interaction.followup.send(
                    "Pillow isn't available in this runtime — the renderer "
                    "degraded to its embed fallback path (by design).",
                    ephemeral=True,
                )
                return
            file = discord.File(
                io.BytesIO(png),
                filename=filename,
                description=alt,
            )
            await interaction.followup.send(
                f"`{filename}` · **{len(png) / 1024:.0f} KB** "
                f"(cap ~8 MiB) · rendered in **{elapsed_ms:.0f} ms** · "
                f"alt text attached",
                file=file,
                ephemeral=True,
            )

        btn.callback = _render  # type: ignore[method-assign]
        return ([header], [btn])
