"""UX Lab wing 1 — button styles, layouts, confirmation flows, wizards.

Every exhibit is interactive and fake: callbacks mutate only the view's
in-memory ``state`` and re-render in place, or answer with an ephemeral.
Nothing touches the database or guild state (CI-fenced).
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from views.base import BaseView
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.BUTTONS
_ROW_LIMITS = ("5 buttons per action row", "5 rows / 25 components per view")


def _header(title: str, body: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=body,
        color=discord.Color.blurple(),
    )


register(
    PatternSpec(
        pattern_id="button_style_strip",
        title="Button style strip",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "primary = the one main action",
            "secondary = neutral/nav",
            "success/danger = outcome-coloured verbs",
            "link = external URLs (no callback fires)",
        ),
        anti_patterns=(
            "more than one primary button per panel",
            "danger style for non-destructive actions",
        ),
        limits=(
            *_ROW_LIMITS,
            "premium style needs a SKU id — bots without SKUs skip it",
        ),
        notes="Tap any button — the ephemeral names the style you pressed.",
    ),
)

register(
    PatternSpec(
        pattern_id="button_emoji_forms",
        title="Emoji-only vs emoji+text vs text-only",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "emoji+text for primary surfaces (clear at any width)",
            "emoji-only for dense paginators (◀ ▶) with obvious meaning",
        ),
        anti_patterns=(
            "emoji-only for non-universal verbs — screen readers announce "
            "the raw emoji name",
        ),
        limits=("label ≤ 80 chars", *_ROW_LIMITS),
        notes="Accessibility: emoji-only buttons need an obvious, universal glyph.",
    ),
)

register(
    PatternSpec(
        pattern_id="home_panel_4",
        title="4-button home (the V-03 Help Home shape)",
        category=_CAT,
        status=PatternStatus.EXPERIMENTAL,
        recommended_for=(
            "top-level hubs with ≤4 clear categories",
            "the planned Help Home (Play / Server & Info / My Stuff / Manage)",
        ),
        anti_patterns=("hubs whose categories exceed one row — regroup first",),
        limits=_ROW_LIMITS,
        notes=(
            "Owner vision V-03/Q-0078. Click a category — the panel swaps in "
            "place and the breadcrumb updates (V-02 doctrine)."
        ),
    ),
)

register(
    PatternSpec(
        pattern_id="dense_action_row",
        title="Dense operator rows (5 actions + nav)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "operator/admin panels trading density for power "
            "(hub-ui-standard preset 3)",
        ),
        anti_patterns=("member-facing hubs — keep those ≤8 visible choices",),
        limits=_ROW_LIMITS,
        notes="Counters update in place — watch the embed, not the buttons.",
    ),
)

register(
    PatternSpec(
        pattern_id="danger_confirm_then_result",
        title="Danger action → confirm panel → result",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "destructive admin actions (delete/purge/reset)",
            "any action that is hard to reverse",
        ),
        anti_patterns=("read-only actions — confirmation there is pure friction",),
        limits=_ROW_LIMITS,
        adopted_by=("views/channels (delete flows)",),
        notes="The doctrine pattern: the danger verb never executes on first click.",
    ),
)

register(
    PatternSpec(
        pattern_id="confirm_via_modal",
        title="Type-to-confirm modal (highest friction)",
        category=_CAT,
        status=PatternStatus.STABLE,
        requires_modal=True,
        recommended_for=(
            "truly destructive, bulk, or irreversible operations "
            "(e.g. purge ALL settings)",
        ),
        anti_patterns=(
            "routine confirmations — reserve typing for the genuinely scary",
        ),
        limits=(
            "modal text input ≤ 4000 chars",
            "modal opens only from an interaction",
        ),
        notes="Type the channel name exactly; a mismatch shows the validation path.",
    ),
)

register(
    PatternSpec(
        pattern_id="wizard_next_back",
        title="Multi-step wizard (Next / Back / Cancel / Save)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "guided setup flows where each step is ONE decision "
            "(hub-ui-standard preset 5)",
        ),
        anti_patterns=("flows with optional steps a user may want to jump between",),
        limits=_ROW_LIMITS,
        notes="Progress header + one decision per step; Save renders the summary.",
    ),
)

register(
    PatternSpec(
        pattern_id="paginator_classic",
        title="Paginator (◀ ▶ + page indicator + jump select)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=("any list longer than one screen", "leaderboards, logs"),
        anti_patterns=("3-item lists — show them outright",),
        limits=("jump select caps at 25 pages — chunk beyond that", *_ROW_LIMITS),
        adopted_by=("views/ux_lab/wing.py (this browser)",),
        notes="Wrap-around paging; the jump select teleports.",
    ),
)

register(
    PatternSpec(
        pattern_id="toggle_pills",
        title="Toggle pills (per-item on/off buttons)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "small fixed rule/flag sets (the automod rule-card shape, Q-0108)",
        ),
        anti_patterns=("more than ~8 toggles — use a multi-select instead",),
        limits=_ROW_LIMITS,
        notes="Style flips success/secondary; the embed mirrors the state.",
    ),
)

register(
    PatternSpec(
        pattern_id="timeout_behavior",
        title="Disable-on-timeout (BaseView lifecycle)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=("every ephemeral panel — it is BaseView's default",),
        limits=("Discord keeps components clickable forever unless disabled",),
        adopted_by=("views/base.py BaseView.on_timeout (bot-wide)",),
        notes=(
            "Spawns a 15-second panel; watch the buttons grey out when the "
            "view times out instead of silently dying."
        ),
    ),
)


class _ConfirmDeleteModal(discord.ui.Modal, title="Confirm: delete #demo-channel"):
    """Type-to-confirm — the highest-friction confirmation shape."""

    answer: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Type the channel name to confirm",
        placeholder="demo-channel",
        max_length=100,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if str(self.answer.value).strip() == "demo-channel":
            await interaction.response.send_message(
                "✅ (fake) **#demo-channel deleted.** A real flow would call the "
                "audited mutation service here.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"❌ Validation failed: `{self.answer.value}` ≠ `demo-channel`. "
                "Nothing happened — exactly the point of type-to-confirm.",
                ephemeral=True,
            )


class _TimeoutDemoView(BaseView):
    """Short-lived panel demonstrating disable-on-timeout."""

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author, timeout=15)
        for label in ("I do something", "Me too"):
            self.add_item(
                discord.ui.Button(label=label, style=discord.ButtonStyle.primary),
            )


class ButtonsWingView(ExhibitWingView):
    """Wing 1 — buttons."""

    WING_TITLE = "Buttons"
    WING_EMOJI = "🔘"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "button_style_strip",
            "button_emoji_forms",
            "home_panel_4",
            "dense_action_row",
            "danger_confirm_then_result",
            "confirm_via_modal",
            "wizard_next_back",
            "paginator_classic",
            "toggle_pills",
            "timeout_behavior",
        )

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        render = {
            "button_style_strip": self._ex_style_strip,
            "button_emoji_forms": self._ex_emoji_forms,
            "home_panel_4": self._ex_home_panel,
            "dense_action_row": self._ex_dense_row,
            "danger_confirm_then_result": self._ex_danger_confirm,
            "confirm_via_modal": self._ex_confirm_modal,
            "wizard_next_back": self._ex_wizard,
            "paginator_classic": self._ex_paginator,
            "toggle_pills": self._ex_toggle_pills,
            "timeout_behavior": self._ex_timeout,
        }[pattern_id]
        return render()

    # -- exhibits -------------------------------------------------------------

    def _ex_style_strip(self) -> ExhibitRender:
        items: list[discord.ui.Item[discord.ui.View]] = []
        styles = (
            ("Primary", discord.ButtonStyle.primary),
            ("Secondary", discord.ButtonStyle.secondary),
            ("Success", discord.ButtonStyle.success),
            ("Danger", discord.ButtonStyle.danger),
        )
        for label, style in styles:
            btn = self.demo_button(label, style=style, row=0)

            async def _cb(
                interaction: discord.Interaction,
                pressed: str = label,
            ) -> None:
                await self.ack(interaction, f"You pressed the **{pressed}** style.")

            btn.callback = _cb  # type: ignore[method-assign]
            items.append(btn)
        items.append(
            discord.ui.Button(
                label="Link → discord.dev",
                style=discord.ButtonStyle.link,
                url="https://discord.com/developers/docs/components/overview",
                row=1,
            ),
        )
        items.append(
            self.demo_button("Disabled", row=1, disabled=True),
        )
        items.append(
            self.demo_button("Premium (SKU-gated — N/A here)", row=1, disabled=True),
        )
        return (
            [
                _header(
                    "🔘 Every button style",
                    "Row 1: the four interactive styles — tap them.\n"
                    "Row 2: a link button (opens a URL, **no callback fires**), "
                    "a disabled button, and the premium style placeholder "
                    "(needs a SKU; bots without one cannot send it).",
                ),
            ],
            items,
        )

    def _ex_emoji_forms(self) -> ExhibitRender:
        items: list[discord.ui.Item[discord.ui.View]] = []
        forms = (
            ("⛏️", "Mine", "emoji + text — clearest"),
            ("⛏️", None, "emoji only — compact, weakest for a11y"),
            (None, "Mine", "text only — always readable"),
        )
        for emoji, label, meaning in forms:
            btn: discord.ui.Button[discord.ui.View] = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=discord.ButtonStyle.secondary,
                row=0,
            )

            async def _cb(
                interaction: discord.Interaction,
                desc: str = meaning,
            ) -> None:
                await self.ack(interaction, f"That form is: **{desc}**.")

            btn.callback = _cb  # type: ignore[method-assign]
            items.append(btn)
        return (
            [
                _header(
                    "⛏️ The three label forms",
                    "Same action, three labels. Tap each — the ephemeral states "
                    "the trade-off. Default to emoji+text on primary surfaces.",
                ),
            ],
            items,
        )

    def _ex_home_panel(self) -> ExhibitRender:
        picked: str | None = self.state.get("picked")
        items: list[discord.ui.Item[discord.ui.View]] = []
        for emoji, label in (
            ("🎮", "Play"),
            ("🏠", "Server & Info"),
            ("🎒", "My Stuff"),
            ("🛠️", "Manage"),
        ):
            btn = self.demo_button(
                label,
                emoji=emoji,
                style=(
                    discord.ButtonStyle.primary
                    if picked == label
                    else discord.ButtonStyle.secondary
                ),
                row=0,
            )

            async def _cb(
                interaction: discord.Interaction,
                chosen: str = label,
            ) -> None:
                self.state["picked"] = chosen
                await self.rerender(interaction)

            btn.callback = _cb  # type: ignore[method-assign]
            items.append(btn)
        crumb = f"🧪 UX Lab › Home › **{picked}**" if picked else "🧪 UX Lab › Home"
        body = f"{crumb}\n\n" + (
            f"You are 'inside' **{picked}** — same message, new content, "
            "breadcrumb updated. No new message was posted."
            if picked
            else "The owner-vision Help Home: four top-level doors. "
            "Click one — the panel swaps **in place** (V-02)."
        )
        return ([_header("🏠 4-button home", body)], items)

    def _ex_dense_row(self) -> ExhibitRender:
        counts: dict[str, int] = self.state.setdefault("counts", {})
        items: list[discord.ui.Item[discord.ui.View]] = []
        for verb in ("Reload", "Sync", "Prune", "Export", "Audit"):
            btn = self.demo_button(verb, row=0)

            async def _cb(
                interaction: discord.Interaction,
                pressed: str = verb,
            ) -> None:
                counts[pressed] = counts.get(pressed, 0) + 1
                await self.rerender(interaction)

            btn.callback = _cb  # type: ignore[method-assign]
            items.append(btn)
        tally = (
            " · ".join(f"{v} ×{n}" for v, n in counts.items())
            if counts
            else "none yet — press some verbs"
        )
        return (
            [
                _header(
                    "🛠️ Dense operator row",
                    "A full 5-button action row (the operator-hub density "
                    f"ceiling).\n**Fake invocations:** {tally}",
                ),
            ],
            items,
        )

    def _ex_danger_confirm(self) -> ExhibitRender:
        stage: str = self.state.get("stage", "idle")
        items: list[discord.ui.Item[discord.ui.View]] = []
        if stage == "idle":
            btn = self.demo_button(
                "Delete 14 messages",
                style=discord.ButtonStyle.danger,
                emoji="🗑️",
                row=0,
            )

            async def _arm(interaction: discord.Interaction) -> None:
                self.state["stage"] = "confirming"
                await self.rerender(interaction)

            btn.callback = _arm  # type: ignore[method-assign]
            items.append(btn)
            body = "Press the danger verb. **Nothing executes on first click.**"
        elif stage == "confirming":
            confirm = self.demo_button(
                "Yes, delete them",
                style=discord.ButtonStyle.danger,
                row=0,
            )
            cancel = self.demo_button("Cancel", row=0)

            async def _confirm(interaction: discord.Interaction) -> None:
                self.state["stage"] = "done"
                await self.rerender(interaction)

            async def _cancel(interaction: discord.Interaction) -> None:
                self.state["stage"] = "idle"
                await self.rerender(interaction)

            confirm.callback = _confirm  # type: ignore[method-assign]
            cancel.callback = _cancel  # type: ignore[method-assign]
            items += [confirm, cancel]
            body = (
                "⚠️ **You are about to (fake-)delete 14 messages in #general.**\n"
                "The confirm step restates scope + count — never just 'Are you sure?'."
            )
        else:
            reset = self.demo_button("Reset demo", row=0)

            async def _reset(interaction: discord.Interaction) -> None:
                self.state.clear()
                await self.rerender(interaction)

            reset.callback = _reset  # type: ignore[method-assign]
            items.append(reset)
            body = (
                "✅ (fake) Deleted 14 messages. A real flow now posts the result "
                "card + an audit entry through the mutation service."
            )
        return ([_header("🗑️ Danger → confirm → result", body)], items)

    def _ex_confirm_modal(self) -> ExhibitRender:
        btn = self.demo_button(
            "Delete #demo-channel…",
            style=discord.ButtonStyle.danger,
            emoji="⌨️",
            row=0,
        )

        async def _open(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_ConfirmDeleteModal())

        btn.callback = _open  # type: ignore[method-assign]
        return (
            [
                _header(
                    "⌨️ Type-to-confirm",
                    "Opens a modal that requires typing `demo-channel` exactly. "
                    "Try a typo first to see the validation path.",
                ),
            ],
            [btn],
        )

    def _ex_wizard(self) -> ExhibitRender:
        steps = (
            ("Pick a name", "The (fake) role will be called **@Night Crew**."),
            ("Pick a colour", "Going with **indigo** — tasteful."),
            ("Hoist it?", "Yes — members show separately in the sidebar."),
        )
        step: int = self.state.get("step", 0)
        saved: bool = self.state.get("saved", False)
        items: list[discord.ui.Item[discord.ui.View]] = []
        if saved:
            body = "💾 **Saved (fake).** Summary:\n" + "\n".join(
                f"{i + 1}. {t} — {d}" for i, (t, d) in enumerate(steps)
            )
            reset = self.demo_button("Restart wizard", row=0)

            async def _restart(interaction: discord.Interaction) -> None:
                self.state.clear()
                await self.rerender(interaction)

            reset.callback = _restart  # type: ignore[method-assign]
            items.append(reset)
        else:
            title, detail = steps[step]
            progress = " → ".join(
                f"**{i + 1}**" if i == step else str(i + 1) for i in range(len(steps))
            )
            body = f"Step {progress}\n\n**{title}**\n{detail}"
            back = self.demo_button("◀ Back", row=0, disabled=step == 0)
            nxt = self.demo_button(
                "Next ▶" if step < len(steps) - 1 else "Save 💾",
                style=discord.ButtonStyle.primary,
                row=0,
            )
            cancel = self.demo_button("Cancel", style=discord.ButtonStyle.danger, row=0)

            async def _back(interaction: discord.Interaction) -> None:
                self.state["step"] = max(0, step - 1)
                await self.rerender(interaction)

            async def _next(interaction: discord.Interaction) -> None:
                if step < len(steps) - 1:
                    self.state["step"] = step + 1
                else:
                    self.state["saved"] = True
                await self.rerender(interaction)

            async def _cancel(interaction: discord.Interaction) -> None:
                self.state.clear()
                await self.rerender(interaction)

            back.callback = _back  # type: ignore[method-assign]
            nxt.callback = _next  # type: ignore[method-assign]
            cancel.callback = _cancel  # type: ignore[method-assign]
            items += [back, nxt, cancel]
        return ([_header("🧙 Wizard flow", body)], items)

    def _ex_paginator(self) -> ExhibitRender:
        pages = tuple(
            f"Page **{n}** — imagine 10 leaderboard rows." for n in range(1, 7)
        )
        page: int = self.state.get("page", 0)
        items: list[discord.ui.Item[discord.ui.View]] = []
        prev = self.demo_button("◀", row=0)
        indicator = self.demo_button(f"{page + 1}/{len(pages)}", row=0, disabled=True)
        nxt = self.demo_button("▶", row=0)

        async def _prev(interaction: discord.Interaction) -> None:
            self.state["page"] = (page - 1) % len(pages)
            await self.rerender(interaction)

        async def _next(interaction: discord.Interaction) -> None:
            self.state["page"] = (page + 1) % len(pages)
            await self.rerender(interaction)

        prev.callback = _prev  # type: ignore[method-assign]
        nxt.callback = _next  # type: ignore[method-assign]
        items += [prev, indicator, nxt]
        jump: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder="Jump to page…",
            options=[
                discord.SelectOption(label=f"Page {n + 1}", value=str(n))
                for n in range(len(pages))
            ],
            row=1,
        )

        async def _jump(interaction: discord.Interaction) -> None:
            self.state["page"] = int(jump.values[0])
            await self.rerender(interaction)

        jump.callback = _jump  # type: ignore[method-assign]
        items.append(jump)
        return (
            [_header("📖 Classic paginator", pages[page])],
            items,
        )

    def _ex_toggle_pills(self) -> ExhibitRender:
        rules = ("Spam", "Invites", "Caps", "Mentions")
        flags: dict[str, bool] = self.state.setdefault(
            "flags",
            {r: r in ("Spam", "Invites") for r in rules},
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
        lines = "\n".join(f"{'🟢' if flags[r] else '⚫'} **{r}** filter" for r in rules)
        return (
            [
                _header(
                    "🚦 Toggle pills",
                    f"The automod rule-card shape (Q-0108):\n{lines}\n\n"
                    "Button style and embed mirror the same state.",
                ),
            ],
            items,
        )

    def _ex_timeout(self) -> ExhibitRender:
        btn = self.demo_button(
            "Spawn a 15-second panel",
            style=discord.ButtonStyle.primary,
            emoji="⏱️",
            row=0,
        )

        async def _spawn(interaction: discord.Interaction) -> None:
            view = _TimeoutDemoView(self._author)
            await interaction.response.send_message(
                embed=_header(
                    "⏱️ This panel times out in 15 s",
                    "Don't touch it — watch the buttons disable themselves "
                    "(BaseView.on_timeout). Stale-but-clickable panels are the "
                    "failure this prevents.",
                ),
                view=view,
                ephemeral=True,
            )
            view.message = await interaction.original_response()

        btn.callback = _spawn  # type: ignore[method-assign]
        return (
            [
                _header(
                    "⏱️ Disable-on-timeout",
                    "Spawns an ephemeral demo panel with `timeout=15`.",
                ),
            ],
            [btn],
        )
