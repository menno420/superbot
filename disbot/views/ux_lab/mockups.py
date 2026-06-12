"""UX Lab wing 7 — mock studio: the approved-but-unbuilt features, clickable.

Every panel here is a **MOCK** of a Q-0108–Q-0112 lane feature (automod ·
logging · welcome · events · feeds · counters · custom commands · security
tiers 1+2) so the family plan's UX decisions are reviewed on rendered,
pressable panels instead of prose. State is view-local; nothing is wired to
real services — the banner on every page says so.
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from utils.ux_patterns.image_builders import render_welcome_card
from views.ux_lab.modals import _TemplateModal
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.MOCKUP
_MOCK_LIMITS = ("MOCK — view-local state only; no service, no DB, no writes",)


def _mock_spec(
    pattern_id: str,
    title: str,
    *,
    recommended_for: tuple[str, ...],
    notes: str = "",
    extra_limits: tuple[str, ...] = (),
) -> None:
    register(
        PatternSpec(
            pattern_id=pattern_id,
            title=title,
            category=_CAT,
            status=PatternStatus.EXPERIMENTAL,
            recommended_for=recommended_for,
            limits=(*extra_limits, *_MOCK_LIMITS),
            notes=notes,
        ),
    )


_mock_spec(
    "mock_automod_rules",
    "Automod rule panel (Q-0108)",
    recommended_for=("the automod v1 config surface (all 4 approved rule types)",),
    notes="Toggle rules; Edit thresholds opens the numbers modal.",
)
_mock_spec(
    "mock_logging_routing",
    "Logging channel routing (Q-0109)",
    recommended_for=("the logging v1 owner choice: one channel vs per-category",),
    notes="Flip the mode — this exact toggle is the open design question, rendered.",
)
_mock_spec(
    "mock_welcome_ab",
    "Welcome: embed vs PIL card (Q-0110)",
    recommended_for=("the v1 (embed) vs phase-2 (card) decision, side by side",),
    notes="Embed shows inline; Card renders the real PIL prototype on demand.",
)
_mock_spec(
    "mock_event_rsvp",
    "Event RSVP card (Q-0112)",
    recommended_for=("the scheduler's RSVP surface + the NL-parse preview",),
    notes="RSVP counts update live (fake). NL preview parses a canned example.",
)
_mock_spec(
    "mock_feed_summary",
    "Feed notification + AI summary (Q-0041)",
    recommended_for=("YouTube-first feed posts; the optional AI-summary block",),
    notes="Toggle the summary block on/off to feel both shapes.",
)
_mock_spec(
    "mock_counters",
    "Dynamic server counters",
    recommended_for=("the statdock-style voice-channel counter quick-win",),
    extra_limits=("real channel renames are rate-limited (~2/10 min)",),
    notes="Simulate joins; note the rename-rate caveat a real one must respect.",
)
_mock_spec(
    "mock_custom_command",
    "Custom command editor",
    recommended_for=("admin-created trigger → template commands",),
    notes="Reuses the template-editor modal; preview renders {user}/{server}.",
)
_mock_spec(
    "mock_security_alerts",
    "Security alerts — tiers 1+2 only (Q-0111)",
    recommended_for=("raid detection + account-age alerts (the approved tiers)",),
    notes="Tiers 3+4 (alt detection / VPN blocking) were DECLINED — "
    "deliberately absent.",
)

_MOCK_BANNER = "🧪 **MOCK** — nothing here is wired; state resets on navigation."


def _mock_header(title: str, body: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=f"{_MOCK_BANNER}\n\n{body}",
        color=discord.Color.dark_gold(),
    )


class MockupsWingView(ExhibitWingView):
    """Wing 7 — mock studio."""

    WING_TITLE = "Mock studio"
    WING_EMOJI = "🎭"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "mock_automod_rules",
            "mock_logging_routing",
            "mock_welcome_ab",
            "mock_event_rsvp",
            "mock_feed_summary",
            "mock_counters",
            "mock_custom_command",
            "mock_security_alerts",
        )

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        render = {
            "mock_automod_rules": self._ex_automod,
            "mock_logging_routing": self._ex_logging,
            "mock_welcome_ab": self._ex_welcome_ab,
            "mock_event_rsvp": self._ex_event_rsvp,
            "mock_feed_summary": self._ex_feed_summary,
            "mock_counters": self._ex_counters,
            "mock_custom_command": self._ex_custom_command,
            "mock_security_alerts": self._ex_security,
        }[pattern_id]
        return render()

    # -- exhibits -------------------------------------------------------------

    def _ex_automod(self) -> ExhibitRender:
        rules = ("Spam", "Invite links", "Caps", "Mass mentions")
        flags: dict[str, bool] = self.state.setdefault(
            "flags",
            dict.fromkeys(rules, True),
        )
        thresholds: dict[str, int] = self.state.setdefault(
            "thresholds",
            {"Spam": 5, "Caps": 70, "Mass mentions": 4},
        )
        items: list[discord.ui.Item[discord.ui.View]] = []
        for rule in rules:
            on = flags[rule]
            btn = self.demo_button(
                f"{rule}: {'ON' if on else 'off'}",
                style=(
                    discord.ButtonStyle.success if on else discord.ButtonStyle.secondary
                ),
                row=0,
            )

            async def _flip(
                interaction: discord.Interaction,
                name: str = rule,
            ) -> None:
                flags[name] = not flags[name]
                await self.rerender(interaction)

            btn.callback = _flip  # type: ignore[method-assign]
            items.append(btn)

        edit = self.demo_button("Edit thresholds…", emoji="🎚️", row=1)

        async def _edit(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_ThresholdModal(self, thresholds))

        edit.callback = _edit  # type: ignore[method-assign]
        items.append(edit)

        lines = []
        for rule in rules:
            mark = "🟢" if flags[rule] else "⚫"
            extra = f" · threshold **{thresholds[rule]}**" if rule in thresholds else ""
            lines.append(f"{mark} **{rule}**{extra}")
        body = (
            "\n".join(lines)
            + "\n\nEscalation: warn → timeout (existing moderation escalation "
            "stays the authority — Q-0108)."
        )
        return ([_mock_header("🛡️ Automod rules", body)], items)

    def _ex_logging(self) -> ExhibitRender:
        per_category: bool = self.state.get("per_category", False)
        toggle = self.demo_button(
            f"Mode: {'per-category' if per_category else 'single channel'}",
            style=discord.ButtonStyle.primary,
            emoji="🔀",
            row=0,
        )

        async def _flip(interaction: discord.Interaction) -> None:
            self.state["per_category"] = not per_category
            await self.rerender(interaction)

        toggle.callback = _flip  # type: ignore[method-assign]
        if per_category:
            routing = (
                "✏️ message edits/deletes → **#log-messages**\n"
                "🚪 joins/leaves → **#log-members**\n"
                "🎭 role changes → **#log-roles**"
            )
        else:
            routing = "✏️ 🚪 🎭 everything → **#server-log**"
        body = (
            f"{routing}\n\nThis exact toggle is the Q-0109 design choice — "
            "flip it and judge which routing you'd actually read."
        )
        return ([_mock_header("📜 Server logging routes", body)], [toggle])

    def _ex_welcome_ab(self) -> ExhibitRender:
        embeds = [
            _mock_header(
                "👋 Welcome — embed (v1) vs PIL card (phase 2)",
                "Below is the **embed-only v1** (Q-0110 approved). Press "
                "**Render the card** to see the phase-2 PIL candidate with "
                "the same data.",
            ),
        ]
        welcome = discord.Embed(
            title="👋 Welcome, AstroFox!",
            description="You are member **#1235** of **Demo Server** — "
            "say hi in #general!",
            color=discord.Color.green(),
        )
        welcome.set_footer(text="embed-only v1 — zero render cost")
        embeds.append(welcome)
        card_btn = self.demo_button(
            "Render the card version",
            style=discord.ButtonStyle.primary,
            emoji="🎨",
            row=0,
        )

        async def _card(interaction: discord.Interaction) -> None:
            import asyncio  # noqa: PLC0415 — callback-local
            import io  # noqa: PLC0415

            from core.runtime.interaction_helpers import safe_defer  # noqa: PLC0415

            if not await safe_defer(interaction, ephemeral=True):
                return
            png = await asyncio.to_thread(render_welcome_card)
            if png is None:
                await interaction.followup.send(
                    "Pillow unavailable — the embed v1 IS the fallback.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                "The phase-2 card, same data:",
                file=discord.File(
                    io.BytesIO(png),
                    filename="welcome-ab.jpg",
                    description="Welcome card for AstroFox, member #1235",
                ),
                ephemeral=True,
            )

        card_btn.callback = _card  # type: ignore[method-assign]
        return (embeds, [card_btn])

    def _ex_event_rsvp(self) -> ExhibitRender:
        counts: dict[str, int] = self.state.setdefault(
            "rsvp",
            {"yes": 4, "maybe": 2, "no": 1},
        )
        card = discord.Embed(
            title="🎬 Movie Night",
            description="**Friday 20:00 CET** · hosted by AstroFox\n"
            f"✅ {counts['yes']} going · ❔ {counts['maybe']} maybe · "
            f"❌ {counts['no']} can't",
            color=discord.Color.purple(),
        )
        items: list[discord.ui.Item[discord.ui.View]] = []
        for key, emoji, style in (
            ("yes", "✅", discord.ButtonStyle.success),
            ("maybe", "❔", discord.ButtonStyle.secondary),
            ("no", "❌", discord.ButtonStyle.danger),
        ):
            btn = self.demo_button(emoji, style=style, row=0)

            async def _rsvp(
                interaction: discord.Interaction,
                bucket: str = key,
            ) -> None:
                counts[bucket] += 1
                await self.rerender(interaction)

            btn.callback = _rsvp  # type: ignore[method-assign]
            items.append(btn)
        nl_btn = self.demo_button("NL parse preview…", emoji="🗣️", row=1)

        async def _nl(interaction: discord.Interaction) -> None:
            await self.ack(
                interaction,
                '🗣️ "movie night friday 8pm" → **Friday 2026-06-19, 20:00 '
                "CET** (mock parser — the real one is the Q-0112 NL lane, "
                "Q-0082-metered).",
            )

        nl_btn.callback = _nl  # type: ignore[method-assign]
        items.append(nl_btn)
        return (
            [
                _mock_header(
                    "📅 Event RSVP",
                    "Press an RSVP — counts update in place.",
                ),
                card,
            ],
            items,
        )

    def _ex_feed_summary(self) -> ExhibitRender:
        with_summary: bool = self.state.get("summary", True)
        notif = discord.Embed(
            title="▶️ New video: «Top 10 Paragon Moments»",
            description="**BTD6 Central** just uploaded · 14:32",
            color=discord.Color.red(),
        )
        if with_summary:
            notif.add_field(
                name="🤖 AI summary (optional block)",
                value="Countdown of paragon plays; #1 is a triple-Navarch "
                "save on round 163. Spoiler-light, watch from 9:40 for the "
                "finale. *(canned text — the real one is Q-0082-metered)*",
                inline=False,
            )
        toggle = self.demo_button(
            f"AI summary: {'ON' if with_summary else 'off'}",
            style=(
                discord.ButtonStyle.success
                if with_summary
                else discord.ButtonStyle.secondary
            ),
            row=0,
        )

        async def _flip(interaction: discord.Interaction) -> None:
            self.state["summary"] = not with_summary
            await self.rerender(interaction)

        toggle.callback = _flip  # type: ignore[method-assign]
        return (
            [
                _mock_header(
                    "📺 Feed notification (YouTube-first, Q-0041)",
                    "Toggle the summary block — the per-feed opt-in decision, "
                    "rendered.",
                ),
                notif,
            ],
            [toggle],
        )

    def _ex_counters(self) -> ExhibitRender:
        members: int = self.state.get("members", 1234)
        preview = discord.Embed(
            description=(
                "🔊 *(voice channel, locked)*\n"
                f"## 📊 Members: {members:,}\n"
                "-# the statdock pattern: a renamed, join-locked voice channel"
            ),
            color=discord.Color.blurple(),
        )
        sim = self.demo_button(
            "Simulate a join",
            style=discord.ButtonStyle.primary,
            emoji="➕",
            row=0,
        )

        async def _join(interaction: discord.Interaction) -> None:
            self.state["members"] = members + 1
            await self.rerender(interaction)

        sim.callback = _join  # type: ignore[method-assign]
        return (
            [
                _mock_header(
                    "📊 Dynamic counters",
                    "A real implementation batches renames — Discord allows "
                    "~2 channel renames per 10 minutes, so counters update "
                    "lazily, not per join.",
                ),
                preview,
            ],
            [sim],
        )

    def _ex_custom_command(self) -> ExhibitRender:
        btn = self.demo_button(
            "Open the editor",
            style=discord.ButtonStyle.primary,
            emoji="🔤",
            row=0,
        )

        async def _open(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_TemplateModal())

        btn.callback = _open  # type: ignore[method-assign]
        return (
            [
                _mock_header(
                    "🔤 Custom commands",
                    "Trigger → template → rendered preview (the safe-subset "
                    "TagScript posture from the community-features capture). "
                    "Admin-only creation in the real thing.",
                ),
            ],
            [btn],
        )

    def _ex_security(self) -> ExhibitRender:
        which: str = self.state.get("alert", "raid")
        if which == "raid":
            alert = discord.Embed(
                title="🚨 Raid suspected",
                description="**14 accounts** joined in 90 s (threshold 10/120 s).\n"
                "Suggested action: enable slow join-gate for 30 min.",
                color=discord.Color.red(),
            )
        else:
            alert = discord.Embed(
                title="⚠️ Young account joined",
                description="**SuspiciousNewcomer** — account age **2 days** "
                "(threshold 7). Watching; no action taken.",
                color=discord.Color.orange(),
            )
        items: list[discord.ui.Item[discord.ui.View]] = []
        for key, label in (("raid", "Raid alert"), ("age", "Account-age alert")):
            btn = self.demo_button(
                label,
                style=(
                    discord.ButtonStyle.primary
                    if which == key
                    else discord.ButtonStyle.secondary
                ),
                row=0,
            )

            async def _show(
                interaction: discord.Interaction,
                pick: str = key,
            ) -> None:
                self.state["alert"] = pick
                await self.rerender(interaction)

            btn.callback = _show  # type: ignore[method-assign]
            items.append(btn)
        return (
            [
                _mock_header(
                    "🛡️ Security — tiers 1+2 (Q-0111)",
                    "Alt detection and VPN blocking (tiers 3+4) were "
                    "**declined** and are deliberately absent from this mock.",
                ),
                alert,
            ],
            items,
        )


class _ThresholdModal(discord.ui.Modal, title="Automod thresholds (mock)"):
    """Numbers-only modal feeding the automod mock's view-local state."""

    def __init__(self, wing: MockupsWingView, thresholds: dict[str, int]) -> None:
        super().__init__()
        self._wing = wing
        self._thresholds = thresholds
        self.spam: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
            label="Spam: msgs per 10 s",
            default=str(thresholds.get("Spam", 5)),
            max_length=3,
        )
        self.caps: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
            label="Caps: % uppercase",
            default=str(thresholds.get("Caps", 70)),
            max_length=3,
        )
        self.add_item(self.spam)
        self.add_item(self.caps)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        for key, field in (("Spam", self.spam), ("Caps", self.caps)):
            raw = str(field.value).strip()
            if raw.isdigit() and 0 < int(raw) <= 100:
                self._thresholds[key] = int(raw)
        await self._wing.rerender(interaction)
