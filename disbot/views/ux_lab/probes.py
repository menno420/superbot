"""UX Lab wing 8 — the platform-limit probe bench (PR A subset).

Each probe attempts a crafted send and reports ✅/❌ with the exact error,
the installed library version, and today's date — the copy-paste artifact
that keeps ``docs/operations/discord-platform-limits.md`` honest. Probe
messages clean themselves up via ``delete_after``.
"""

from __future__ import annotations

import datetime as dt

import discord

from core.runtime.interaction_helpers import safe_defer
from utils.ux_patterns import (
    PatternCategory,
    PatternSpec,
    PatternStatus,
    ProbeResult,
    register,
)
from views.base import HubView
from views.navigation import ParentBuilder, transition_to
from views.ux_lab.modals import _LabelSelectModal

_CAT = PatternCategory.PROBE
_PROBE_MSG_TTL = 45  # seconds before a probe's demo message self-deletes


def _probe_spec(pattern_id: str, title: str, expect: str, notes: str = "") -> None:
    register(
        PatternSpec(
            pattern_id=pattern_id,
            title=title,
            category=_CAT,
            status=PatternStatus.STABLE,
            recommended_for=("re-verifying the platform-limits doc on demand",),
            limits=(expect,),
            notes=notes,
        ),
    )


_probe_spec(
    "probe_legacy_grid_25",
    "P-01 · legacy 5×5 component grid",
    "expect PASS — 25 items is the legacy View ceiling",
)
_probe_spec(
    "probe_select_26_options",
    "P-02 · select with 26 options",
    "expect FAIL — 25 options is the per-select cap",
    notes="Reports WHICH layer rejected it (library construction vs API).",
)
_probe_spec(
    "probe_embed_budget",
    "P-06 · 10 embeds near the 6000-char total",
    "expect PASS at ≤6000 combined; the cap is the message total, not per-embed",
)
_probe_spec(
    "probe_modal_label_select",
    "P-07 · Label-wrapped select inside a modal",
    "expect PASS on discord.py ≥2.6 — submit the modal to complete the probe",
    notes="Manual probe: it must open AND accept a submission.",
)
_probe_spec(
    "probe_cv2_40_children",
    "P-03 · LayoutView with exactly 40 children",
    "expect PASS — 40 is the CV2 ceiling (verified in library source)",
)
_probe_spec(
    "probe_cv2_41_children",
    "P-04 · LayoutView with 41 children",
    "expect FAIL at library construction — ValueError('… exceeded (40)')",
)
_probe_spec(
    "probe_cv2_text_budget",
    "P-05 · CV2 display-text budget (4000 chars)",
    "expect PASS at 4000 combined; the probe reports which layer rejects 4001",
)
_probe_spec(
    "probe_cv2_content_exclusive",
    "P-09 · CV2 + content= mutual exclusion",
    "expect FAIL — a CV2 message replaces content/embeds entirely",
)
_probe_spec(
    "probe_modal_entity_select",
    "P-08 · entity select (UserSelect) inside a modal",
    "UNKNOWN — exactly what this probe exists to pin down",
    notes="Manual probe: open it; rejection at construction/open is the answer.",
)
_probe_spec(
    "probe_attachment_alt_text",
    "P-10 · attachment alt-text round-trip",
    "expect PASS — description field ≤1024 chars survives upload",
)


def _stamp() -> str:
    return f"discord.py {discord.__version__} · {dt.date.today().isoformat()}"


class ProbesBenchView(HubView):
    """The limit-verification bench: one button per probe + Run all."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        home_builder: ParentBuilder,
    ) -> None:
        super().__init__(author)
        self._home_builder = home_builder
        self._results: dict[str, ProbeResult] = {}
        self._build_items()

    # -- probes ---------------------------------------------------------------

    async def _probe_legacy_grid(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        try:
            view = discord.ui.View(timeout=_PROBE_MSG_TTL)
            for n in range(25):
                view.add_item(
                    discord.ui.Button(
                        label=str(n + 1),
                        style=discord.ButtonStyle.secondary,
                        disabled=True,
                        row=n // 5,
                    ),
                )
            await channel.send(
                "🧪 P-01: 25 components (5×5) — self-deletes.",
                view=view,
                delete_after=_PROBE_MSG_TTL,
            )
        except Exception as exc:  # noqa: BLE001 — the exception IS the result
            return ProbeResult(
                "probe_legacy_grid_25",
                "P-01 legacy 5×5 grid",
                False,
                f"{type(exc).__name__}: {str(exc)[:180]}",
            )
        return ProbeResult(
            "probe_legacy_grid_25",
            "P-01 legacy 5×5 grid",
            True,
            "sent — 25 items accepted (the legacy ceiling)",
        )

    async def _probe_select_26(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        pid, title = "probe_select_26_options", "P-02 select with 26 options"
        try:
            sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
                options=[
                    discord.SelectOption(label=f"option {n}") for n in range(1, 27)
                ],
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                True,
                f"rejected at library construction — {type(exc).__name__}: "
                f"{str(exc)[:140]}",
            )
        try:
            view = discord.ui.View(timeout=_PROBE_MSG_TTL)
            view.add_item(sel)
            await channel.send(
                "🧪 P-02: 26-option select — should never send.",
                view=view,
                delete_after=_PROBE_MSG_TTL,
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                True,
                f"rejected at the API — {type(exc).__name__}: {str(exc)[:140]}",
            )
        return ProbeResult(
            pid,
            title,
            False,
            "UNEXPECTED: Discord accepted 26 options — update the limits doc!",
        )

    async def _probe_embed_budget(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        pid, title = "probe_embed_budget", "P-06 embed budget (10 × ~590 chars)"
        try:
            filler = "x" * 560
            embeds = [
                discord.Embed(title=f"Embed {n + 1}/10", description=filler)
                for n in range(10)
            ]
            total = sum(len(e.title or "") + len(e.description or "") for e in embeds)
            await channel.send(embeds=embeds, delete_after=_PROBE_MSG_TTL)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                False,
                f"{type(exc).__name__}: {str(exc)[:180]}",
            )
        return ProbeResult(
            pid,
            title,
            True,
            f"sent — 10 embeds, {total} combined chars (≤6000 budget)",
        )

    async def _probe_cv2_40(self, channel: discord.abc.Messageable) -> ProbeResult:
        pid, title = "probe_cv2_40_children", "P-03 LayoutView · 40 children"
        try:
            view = discord.ui.LayoutView(timeout=_PROBE_MSG_TTL)
            for n in range(40):
                view.add_item(discord.ui.TextDisplay(f"-# item {n + 1}/40"))
            await channel.send(view=view, delete_after=_PROBE_MSG_TTL)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                False,
                f"{type(exc).__name__}: {str(exc)[:180]}",
            )
        return ProbeResult(pid, title, True, "sent — 40 children accepted")

    async def _probe_cv2_41(self, channel: discord.abc.Messageable) -> ProbeResult:
        pid, title = "probe_cv2_41_children", "P-04 LayoutView · 41 children"
        try:
            view = discord.ui.LayoutView(timeout=_PROBE_MSG_TTL)
            for n in range(41):
                view.add_item(discord.ui.TextDisplay(f"-# item {n + 1}/41"))
        except ValueError as exc:
            return ProbeResult(
                pid,
                title,
                True,
                f"rejected at library construction — ValueError: {str(exc)[:140]}",
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                False,
                f"{type(exc).__name__}: {str(exc)[:180]}",
            )
        try:
            await channel.send(view=view, delete_after=_PROBE_MSG_TTL)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                True,
                f"rejected at the API — {type(exc).__name__}: {str(exc)[:140]}",
            )
        return ProbeResult(
            pid,
            title,
            False,
            "UNEXPECTED: 41 children accepted — update the doc!",
        )

    async def _probe_cv2_text_budget(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        pid, title = "probe_cv2_text_budget", "P-05 CV2 text budget (4000)"
        try:
            at_limit = discord.ui.LayoutView(timeout=_PROBE_MSG_TTL)
            at_limit.add_item(discord.ui.TextDisplay("x" * 4000))
            await channel.send(view=at_limit, delete_after=_PROBE_MSG_TTL)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                False,
                f"4000 chars rejected — {type(exc).__name__}: {str(exc)[:140]}",
            )
        try:
            over = discord.ui.LayoutView(timeout=_PROBE_MSG_TTL)
            over.add_item(discord.ui.TextDisplay("x" * 4001))
            await channel.send(view=over, delete_after=_PROBE_MSG_TTL)
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                True,
                f"4000 sent OK; 4001 rejected — {type(exc).__name__}: {str(exc)[:120]}",
            )
        return ProbeResult(
            pid,
            title,
            False,
            "UNEXPECTED: 4001 chars accepted — update the doc!",
        )

    async def _probe_cv2_content_exclusive(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        pid, title = "probe_cv2_content_exclusive", "P-09 CV2 + content="
        try:
            view = discord.ui.LayoutView(timeout=_PROBE_MSG_TTL)
            view.add_item(discord.ui.TextDisplay("CV2 exclusivity probe"))
            await channel.send(
                "plain content alongside CV2",
                view=view,
                delete_after=_PROBE_MSG_TTL,
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                True,
                f"rejected as expected — {type(exc).__name__}: {str(exc)[:140]}",
            )
        return ProbeResult(
            pid,
            title,
            False,
            "UNEXPECTED: content + CV2 accepted together — update the doc!",
        )

    async def _probe_alt_text(
        self,
        channel: discord.abc.Messageable,
    ) -> ProbeResult:
        import io  # noqa: PLC0415 — tiny, probe-only

        pid, title = "probe_attachment_alt_text", "P-10 alt-text round-trip"
        alt = "UX Lab alt-text probe file"
        try:
            file = discord.File(
                io.BytesIO(b"alt-text probe\n"),
                filename="uxlab-alt-probe.txt",
                description=alt,
            )
            msg = await channel.send(
                "🧪 P-10: alt-text round-trip — self-deletes.",
                file=file,
                delete_after=_PROBE_MSG_TTL,
            )
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(
                pid,
                title,
                False,
                f"{type(exc).__name__}: {str(exc)[:180]}",
            )
        got = msg.attachments[0].description if msg.attachments else None
        if got == alt:
            return ProbeResult(pid, title, True, "description survived upload verbatim")
        return ProbeResult(
            pid,
            title,
            False,
            f"description came back as {got!r} (sent {alt!r})",
        )

    # -- rendering ------------------------------------------------------------

    def build(self) -> tuple[list[discord.Embed], ProbesBenchView]:
        embed = discord.Embed(
            title="🔬 Limit probe bench",
            description=(
                "Each probe attempts a crafted send and reports the exact "
                "outcome. Probe messages self-delete after "
                f"{_PROBE_MSG_TTL}s.\n**{_stamp()}**"
            ),
            color=discord.Color.gold(),
        )
        if self._results:
            for res in self._results.values():
                embed.add_field(
                    name=f"{'✅' if res.ok else '❌'} {res.title}",
                    value=res.detail[:1000],
                    inline=False,
                )
        else:
            embed.add_field(
                name="No results yet",
                value="Run a probe — results land here, dated and versioned.",
                inline=False,
            )
        return [embed], self

    def _automated_probes(self):  # noqa: ANN202 — (label, runner, row) triples
        return (
            ("P-01 grid", self._probe_legacy_grid, 0),
            ("P-02 26-option", self._probe_select_26, 0),
            ("P-06 embed budget", self._probe_embed_budget, 0),
            ("P-03 CV2 ×40", self._probe_cv2_40, 1),
            ("P-04 CV2 ×41", self._probe_cv2_41, 1),
            ("P-05 CV2 4000ch", self._probe_cv2_text_budget, 1),
            ("P-09 CV2+content", self._probe_cv2_content_exclusive, 2),
            ("P-10 alt-text", self._probe_alt_text, 2),
        )

    def _build_items(self) -> None:
        self.clear_items()
        for label, runner, row in self._automated_probes():
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                row=row,
            )

            async def _run(
                interaction: discord.Interaction,
                probe=runner,  # noqa: ANN001 — bound method capture
            ) -> None:
                if not await safe_defer(interaction):
                    return
                channel = interaction.channel
                if channel is None or not isinstance(
                    channel,
                    discord.abc.Messageable,
                ):
                    return
                result = await probe(channel)
                self._results[result.probe_id] = result
                embeds, _ = self.build()
                await interaction.edit_original_response(embeds=embeds, view=self)

            btn.callback = _run  # type: ignore[method-assign]
            self.add_item(btn)

        modal_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="P-07 modal+select (manual)",
            style=discord.ButtonStyle.secondary,
            row=2,
        )

        async def _modal_probe(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_LabelSelectModal())

        modal_btn.callback = _modal_probe  # type: ignore[method-assign]
        self.add_item(modal_btn)

        entity_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="P-08 modal+UserSelect (manual)",
            style=discord.ButtonStyle.secondary,
            row=2,
        )

        async def _entity_modal_probe(interaction: discord.Interaction) -> None:
            # Construction or open may be rejected at any layer — wherever it
            # fails IS the probe's answer, so report instead of raising.
            try:
                modal = discord.ui.Modal(title="P-08: entity select", timeout=120)
                modal.add_item(
                    discord.ui.Label(
                        text="Pick a member",
                        component=discord.ui.UserSelect(),
                    ),
                )

                async def _submitted(submit_interaction: discord.Interaction) -> None:
                    await submit_interaction.response.send_message(
                        "✅ P-08: Discord accepted a UserSelect inside a modal "
                        "(submission received) — update the limits doc.",
                        ephemeral=True,
                    )

                modal.on_submit = _submitted  # type: ignore[method-assign]
                await interaction.response.send_modal(modal)
            except Exception as exc:  # noqa: BLE001 — the failure IS the result
                await interaction.response.send_message(
                    f"❌ P-08 rejected — `{type(exc).__name__}: "
                    f"{str(exc)[:200]}` (that rejection is the probe's answer)",
                    ephemeral=True,
                )

        entity_btn.callback = _entity_modal_probe  # type: ignore[method-assign]
        self.add_item(entity_btn)

        run_all: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="Run all automated",
            emoji="🔬",
            style=discord.ButtonStyle.success,
            row=3,
        )

        async def _run_all(interaction: discord.Interaction) -> None:
            if not await safe_defer(interaction):
                return
            channel = interaction.channel
            if channel is None or not isinstance(channel, discord.abc.Messageable):
                return
            for _label, probe, _row in self._automated_probes():
                result = await probe(channel)
                self._results[result.probe_id] = result
            embeds, _ = self.build()
            await interaction.edit_original_response(embeds=embeds, view=self)

        run_all.callback = _run_all  # type: ignore[method-assign]
        self.add_item(run_all)

        home_btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="UX Lab",
            emoji="🏠",
            style=discord.ButtonStyle.secondary,
            row=4,
        )

        async def _home(interaction: discord.Interaction) -> None:
            await transition_to(interaction, builder=self._home_builder)

        home_btn.callback = _home  # type: ignore[method-assign]
        self.add_item(home_btn)
