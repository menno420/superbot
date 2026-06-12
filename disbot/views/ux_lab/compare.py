"""UX Lab wing 9 — side-by-side compare with verdict lines.

The owner's core loop made first-class: pick two patterns, flip between
them **in place** (same message, same data), then record a verdict. The
verdict modal dogfoods the Label-wrapped select (pick adopt/reject/tweak
inside the modal) and emits a copy-paste line — zero persistence by design;
the pattern-library doc is the durable ledger, updated by the session that
receives the lines.
"""

from __future__ import annotations

import discord

from utils.ux_patterns import (
    REGISTRY,
    PatternCategory,
    PatternSpec,
    PatternStatus,
    register,
    specs_for,
)
from views.base import HubView
from views.navigation import ParentBuilder, transition_to
from views.ux_lab.wing import ExhibitWingView

register(
    PatternSpec(
        pattern_id="compare_ab_verdict",
        title="A/B compare with verdict capture",
        category=PatternCategory.MOCKUP,
        status=PatternStatus.STABLE,
        recommended_for=(
            "design reviews: two candidate layouts, one message, flip + judge",
        ),
        limits=("verdicts are copy-paste lines, never persisted (zero-write fence)",),
        notes="The verdict modal itself dogfoods the Label+Select capability.",
    ),
)

# Categories whose exhibits render meaningfully as embeds-only previews.
_COMPARABLE = (
    PatternCategory.BUTTONS,
    PatternCategory.SELECTS,
    PatternCategory.MODALS,
    PatternCategory.EMBEDS,
    PatternCategory.LAYOUT_V2,
    PatternCategory.IMAGE,
    PatternCategory.MOCKUP,
)


def _wing_for(category: PatternCategory) -> type[ExhibitWingView]:
    # Local import: compare is a sibling of every wing; importing lazily
    # keeps module import order simple (home imports compare last).
    from views.ux_lab.buttons import ButtonsWingView
    from views.ux_lab.embeds import EmbedsWingView
    from views.ux_lab.image_cards import ImageWingView
    from views.ux_lab.layout_v2 import LayoutWingView
    from views.ux_lab.mockups import MockupsWingView
    from views.ux_lab.modals import ModalsWingView
    from views.ux_lab.selects import SelectsWingView

    return {
        PatternCategory.BUTTONS: ButtonsWingView,
        PatternCategory.SELECTS: SelectsWingView,
        PatternCategory.MODALS: ModalsWingView,
        PatternCategory.EMBEDS: EmbedsWingView,
        PatternCategory.LAYOUT_V2: LayoutWingView,
        PatternCategory.IMAGE: ImageWingView,
        PatternCategory.MOCKUP: MockupsWingView,
    }[category]


async def _noop_home(
    interaction: discord.Interaction,
) -> tuple[discord.Embed, discord.ui.View]:  # pragma: no cover — never clicked
    return discord.Embed(), discord.ui.View()


def render_pattern_preview(
    pattern_id: str,
    author: discord.Member | discord.User,
) -> list[discord.Embed]:
    """A pattern's exhibit embeds (spec card dropped) for embeds-only preview.

    Interactivity is intentionally omitted — the compare panel says where to
    go press the real thing (its wing).
    """
    spec = REGISTRY[pattern_id]
    if spec.category is PatternCategory.PROBE:
        return [discord.Embed(description="Probes have no preview — use the bench.")]
    wing_cls = _wing_for(spec.category)
    wing = wing_cls(author, home_builder=_noop_home)
    ids = wing._exhibit_ids()
    if pattern_id in ids:
        wing._index = ids.index(pattern_id)
    embeds, _view = wing.build()
    return embeds[:-1] or embeds  # drop the spec card, keep at least one


class _VerdictModal(discord.ui.Modal, title="Record a verdict"):
    """Label+Select verdict choice + free-text note → a copy-paste line."""

    choice: discord.ui.Label[discord.ui.Modal] = discord.ui.Label(
        text="Verdict",
        component=discord.ui.Select(
            options=[
                discord.SelectOption(label="adopt", emoji="👍"),
                discord.SelectOption(label="reject", emoji="👎"),
                discord.SelectOption(label="tweak", emoji="📝"),
            ],
        ),
    )
    note: discord.ui.Label[discord.ui.Modal] = discord.ui.Label(
        text="Note (optional)",
        component=discord.ui.TextInput(required=False, max_length=200),
    )

    def __init__(self, panel: CompareView, pattern_id: str) -> None:
        super().__init__()
        self._panel = panel
        self._pattern_id = pattern_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        from typing import cast  # noqa: PLC0415 — submit-path only

        select = cast("discord.ui.Select[discord.ui.Modal]", self.choice.component)
        note_input = cast("discord.ui.TextInput[discord.ui.Modal]", self.note.component)
        verdict = select.values[0] if select.values else "tweak"
        note = str(note_input.value).strip()
        line = f"uxlab-verdict: {self._pattern_id} — {verdict}" + (
            f" — {note}" if note else ""
        )
        self._panel.verdicts.append(line)
        await interaction.response.send_message(
            "Copy-paste this into the session chat / router so an agent "
            f"routes it into the pattern library:\n```\n{line}\n```",
            ephemeral=True,
        )


class CompareView(HubView):
    """Pick a category → pick A and B → flip in place → record verdicts."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        home_builder: ParentBuilder,
    ) -> None:
        super().__init__(author)
        self._home_builder = home_builder
        self._category: PatternCategory | None = None
        self._a: str | None = None
        self._b: str | None = None
        self._showing_b = False
        self.verdicts: list[str] = []
        self._rebuild_items()

    # -- rendering ------------------------------------------------------------

    def build(self) -> tuple[list[discord.Embed], CompareView]:
        self._rebuild_items()
        header = discord.Embed(
            title="⚖️ Compare",
            color=discord.Color.dark_teal(),
        )
        embeds: list[discord.Embed] = [header]
        if self._a and self._b:
            shown = self._b if self._showing_b else self._a
            other = self._a if self._showing_b else self._b
            header.description = (
                f"Showing **{'B' if self._showing_b else 'A'} · `{shown}`** "
                f"(other side: `{other}`). Embeds-only preview — press the "
                "real thing in its wing."
            )
            embeds.extend(render_pattern_preview(shown, self._author)[:8])
        else:
            header.description = (
                "Pick a category, then patterns **A** and **B**. The panel "
                "flips between them in place — same message, fair judgement."
            )
        if self.verdicts:
            tail = discord.Embed(
                title="🗳️ Session verdicts (copy these out — not persisted)",
                description="\n".join(f"`{v}`" for v in self.verdicts[-10:]),
                color=discord.Color.gold(),
            )
            embeds.append(tail)
        return embeds, self

    def _rebuild_items(self) -> None:
        self.clear_items()
        cat_sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder=(
                f"Category: {self._category.value}"
                if self._category
                else "1 · Pick a category…"
            ),
            options=[
                discord.SelectOption(label=c.value) for c in _COMPARABLE if specs_for(c)
            ],
            row=0,
        )

        async def _pick_cat(interaction: discord.Interaction) -> None:
            self._category = PatternCategory(cat_sel.values[0])
            self._a = self._b = None
            self._showing_b = False
            await self._rerender(interaction)

        cat_sel.callback = _pick_cat  # type: ignore[method-assign]
        self.add_item(cat_sel)

        if self._category:
            specs = specs_for(self._category)[:25]
            for row, (slot, current) in enumerate(
                (("A", self._a), ("B", self._b)),
                start=1,
            ):
                sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
                    placeholder=(
                        f"{slot}: {current}" if current else f"2 · Pick pattern {slot}…"
                    ),
                    options=[discord.SelectOption(label=s.pattern_id) for s in specs],
                    row=row,
                )

                async def _pick(
                    interaction: discord.Interaction,
                    menu: discord.ui.Select[discord.ui.View] = sel,
                    which: str = slot,
                ) -> None:
                    if which == "A":
                        self._a = menu.values[0]
                        self._showing_b = False
                    else:
                        self._b = menu.values[0]
                    await self._rerender(interaction)

                sel.callback = _pick  # type: ignore[method-assign]
                self.add_item(sel)

        if self._a and self._b:
            flip = discord.ui.Button(  # type: ignore[var-annotated]
                label=f"Show {'A' if self._showing_b else 'B'}",
                style=discord.ButtonStyle.primary,
                emoji="🔁",
                row=3,
            )

            async def _flip(interaction: discord.Interaction) -> None:
                self._showing_b = not self._showing_b
                await self._rerender(interaction)

            flip.callback = _flip  # type: ignore[method-assign]
            self.add_item(flip)

            verdict = discord.ui.Button(  # type: ignore[var-annotated]
                label="Verdict…",
                style=discord.ButtonStyle.success,
                emoji="🗳️",
                row=3,
            )

            async def _verdict(interaction: discord.Interaction) -> None:
                shown = self._b if self._showing_b else self._a
                if shown is None:  # unreachable: button exists only with A+B
                    return
                await interaction.response.send_modal(_VerdictModal(self, shown))

            verdict.callback = _verdict  # type: ignore[method-assign]
            self.add_item(verdict)

        home_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="UX Lab",
            emoji="🏠",
            style=discord.ButtonStyle.secondary,
            row=4,
        )

        async def _home(interaction: discord.Interaction) -> None:
            await transition_to(interaction, builder=self._home_builder)

        home_btn.callback = _home  # type: ignore[method-assign]
        self.add_item(home_btn)

    async def _rerender(self, interaction: discord.Interaction) -> None:
        embeds, _ = self.build()
        if interaction.response.is_done():
            await interaction.edit_original_response(embeds=embeds, view=self)
        else:
            await interaction.response.edit_message(embeds=embeds, view=self)
