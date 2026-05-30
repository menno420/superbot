"""420 — a small self-contained delight subsystem (PR #420). 🍃

Two surfaces, no cross-cog reach and no state mutation:

* ``!420`` (alias ``!fourtwenty``) opens a 🍃-themed panel with rotating
  "wisdom" and number trivia, mirroring the General cog's panel shape.
* A passive :class:`core.runtime.message_pipeline.MessageStage`
  (``FourTwentyStage``) watches every message and drops a 🍃 reaction +
  one-liner when someone types ``420`` / ``4:20`` / ``blaze it`` /
  ``four twenty``.  The stage is **observe-only**: it never deletes,
  never short-circuits, and self-rate-limits per channel so it can never
  become noise.  It runs at ``order=50`` (the passive tier) — after the
  auto-mod (10/15/20) and rewards (30/40) tiers so it never leafs a
  message that's about to be deleted, but **before** the AI
  natural-language stage (``order=70``), which
  short-circuits the pipeline on a bot mention.  Sitting ahead of it is
  what lets ``@bot … 420 …`` messages still get their 🍃.

Design notes
------------
* Message detection goes through the platform ``MessageStage`` pipeline,
  not a raw ``on_message`` listener — that's the sanctioned hook and
  keeps us off the "five concurrent on_message handlers" footgun the
  pipeline was built to retire.
* The balance/score "lands on 420" wink was intentionally left out:
  ``economy.balance_changed`` / ``xp.awarded`` carry no channel to react
  in (see events_catalogue), so a clean cross-system version would need
  a payload change — deliberately deferred to its own PR.
* Nothing here writes to the DB or mutates economy/XP, so there is no
  mutation-pipeline or audit obligation.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time

import discord
from discord.ext import commands

from core.runtime.message_pipeline import (
    MessagePipelineContext,
    StageResult,
)
from core.runtime.message_pipeline import register as register_stage
from core.runtime.message_pipeline import unregister as unregister_stage
from views.base import BaseView, send_panel

logger = logging.getLogger("bot")

_CONTENT_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "json",
    "four_twenty_content.json",
)

_FOUR_TWENTY_COLOR = discord.Color.from_rgb(0x4C, 0xAF, 0x50)  # leafy green
_LEAF = "🍃"

# Stage ordering: observe-only, so it can sit anywhere — but it must run
# BEFORE the AI natural-language stage (order=70), which short-circuits the
# pipeline when it handles a bot mention.  At the old order=95 a message
# like "@bot blaze it" was consumed by AI before we ever saw it, so the
# egg silently never fired on mentions.  order=50 (the "passive" tier) keeps
# us after the auto-mod (10/15/20) and rewards (30/40) tiers — so we never
# leaf a message counting/cleanup is about to delete — yet ahead of AI.
# See the canonical stage-order table in core/runtime/message_pipeline.py.
FOUR_TWENTY_STAGE_NAME = "four_twenty"
FOUR_TWENTY_STAGE_ORDER = 50

# Per-channel cooldown (seconds) so the easter egg can never be spammed
# into noise — at most one wink per channel per window.
_EGG_COOLDOWN_SECONDS = 90.0

# Match a standalone 420 / 4:20 / 4-20, or the phrases "blaze it" /
# "four twenty". ``\b`` around the number avoids firing on 1420, 4200,
# IDs, prices, etc. Case-insensitive.
_TRIGGER_RE = re.compile(
    r"(?<!\d)4[:\-\s]?20(?!\d)|blaze\s*it|four[\s\-]?twenty",
    re.IGNORECASE,
)

_EGG_LINES = [
    f"{_LEAF} Ayy, 420. Stay leafy.",
    f"{_LEAF} 4:20 spotted — take a deep breath.",
    f"{_LEAF} Blaze it (responsibly). Vibes acknowledged.",
    f"{_LEAF} The sacred number appears. Snacks recommended.",
    f"{_LEAF} 420 detected. Keeping it mellow.",
]


def _load_content() -> dict:
    try:
        with open(_CONTENT_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to load four_twenty_content.json: %s", exc)
        return {}


class FourTwentyStage:
    """Observe-only stage: 🍃-react when a message mentions 420.

    Never deletes and never short-circuits — it returns an empty
    :class:`StageResult` in every path so the pipeline always continues
    to downstream stages. A best-effort ``add_reaction`` + optional
    one-liner is the entire side effect; any failure is swallowed so the
    egg can never break message handling.
    """

    name = FOUR_TWENTY_STAGE_NAME
    order = FOUR_TWENTY_STAGE_ORDER

    def __init__(self) -> None:
        # channel_id -> monotonic timestamp of last wink
        self._last_fired: dict[int, float] = {}

    def _on_cooldown(self, channel_id: int) -> bool:
        now = time.monotonic()
        last = self._last_fired.get(channel_id)
        if last is not None and (now - last) < _EGG_COOLDOWN_SECONDS:
            return True
        self._last_fired[channel_id] = now
        return False

    async def process(self, ctx: MessagePipelineContext) -> StageResult:
        message = ctx.message
        content = message.content or ""
        if not content or not _TRIGGER_RE.search(content):
            return StageResult()
        # Per-channel rate-limit so a chatty channel can't spam winks.
        channel = message.channel
        if self._on_cooldown(channel.id):
            return StageResult()
        try:
            await message.add_reaction(_LEAF)
            # Occasionally add a one-liner; usually just the quiet react.
            if random.random() < 0.5:
                await channel.send(random.choice(_EGG_LINES))
        except discord.HTTPException as exc:
            logger.debug("420 easter-egg side effect failed: %s", exc)
        return StageResult()


def _overview_embed() -> discord.Embed:
    return discord.Embed(
        title=f"{_LEAF} 420",
        description=(
            "Take it easy. Pick an option below.\n\n"
            "**🍃 Wisdom** — a little relaxed wisdom\n"
            "**🔢 420 Fact** — number trivia for the curious\n\n"
            "_Tip: drop a `420` in chat and watch what happens._"
        ),
        color=_FOUR_TWENTY_COLOR,
    )


class FourTwentyCog(commands.Cog):
    """Hosts the ``!420`` command, its panel, and the passive stage."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        content = _load_content()
        self._wisdom: list[str] = content.get("wisdom", [])
        self._facts: list[str] = content.get("facts", [])
        self._stage = FourTwentyStage()

    async def cog_load(self) -> None:
        register_stage(self._stage)

    async def cog_unload(self) -> None:
        unregister_stage(FOUR_TWENTY_STAGE_NAME)

    @commands.cooldown(rate=3, per=10, type=commands.BucketType.user)
    @commands.command(
        name="420",
        aliases=["fourtwenty", "fourtwenty420"],
        help="Open the 🍃 420 panel — rotating wisdom and number trivia.",
    )
    async def four_twenty(self, ctx: commands.Context) -> None:
        """Entry-point command for the 420 subsystem panel.

        Anchors the subsystem_registry ``entry_points`` list so Help can
        map ``"four_twenty"`` → this cog.
        """
        view = _FourTwentyPanelView(ctx.author, self)
        await send_panel(ctx, embed=_overview_embed(), view=view)

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help-menu direct-navigation hook (governance already resolved)."""
        view = _FourTwentyPanelView(interaction.user, self)  # type: ignore[arg-type]
        return _overview_embed(), view


class _FourTwentyPanelView(BaseView):
    """Interactive 🍃 panel — mirrors the General cog's panel pattern.

    Public so the panel can be shared in a channel; each button edits the
    same message in place with a result embed.
    """

    def __init__(self, author: discord.Member | discord.User, cog: FourTwentyCog):
        super().__init__(author, public=True, timeout=300)
        self._cog = cog

    def _random_or_empty(self, pool: list[str], label: str) -> str:
        return random.choice(pool) if pool else f"No {label} available right now."

    @discord.ui.button(label="🍃 Wisdom", style=discord.ButtonStyle.green, row=0)
    async def wisdom_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title=f"{_LEAF} 420 Wisdom",
            description=self._random_or_empty(self._cog._wisdom, "wisdom"),
            color=_FOUR_TWENTY_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔢 420 Fact", style=discord.ButtonStyle.blurple, row=0)
    async def fact_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="🔢 420 Fact",
            description=self._random_or_empty(self._cog._facts, "facts"),
            color=_FOUR_TWENTY_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="↩ Overview", style=discord.ButtonStyle.secondary, row=1)
    async def overview_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(embed=_overview_embed(), view=self)


async def setup(bot):
    await bot.add_cog(FourTwentyCog(bot))
