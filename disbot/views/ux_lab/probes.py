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

    def _build_items(self) -> None:
        self.clear_items()
        probes = (
            ("P-01 grid", self._probe_legacy_grid),
            ("P-02 26-option", self._probe_select_26),
            ("P-06 embed budget", self._probe_embed_budget),
        )
        for label, runner in probes:
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                row=0,
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
            style=discord.ButtonStyle.primary,
            row=1,
        )

        async def _modal_probe(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_LabelSelectModal())

        modal_btn.callback = _modal_probe  # type: ignore[method-assign]
        self.add_item(modal_btn)

        run_all: discord.ui.Button[discord.ui.View] = discord.ui.Button(
            label="Run all automated",
            emoji="🔬",
            style=discord.ButtonStyle.success,
            row=1,
        )

        async def _run_all(interaction: discord.Interaction) -> None:
            if not await safe_defer(interaction):
                return
            channel = interaction.channel
            if channel is None or not isinstance(channel, discord.abc.Messageable):
                return
            for probe in (
                self._probe_legacy_grid,
                self._probe_select_26,
                self._probe_embed_budget,
            ):
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
