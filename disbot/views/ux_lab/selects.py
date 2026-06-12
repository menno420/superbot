"""UX Lab wing 2 — select menus: navigation, multi-select, pagination, entities.

Includes the canonical answer to the 25-option ceiling (category select →
paginated select → preview → confirm) that the server-management roadmap
names as a selector gap.
"""

from __future__ import annotations

import discord

from utils.ux_patterns import PatternCategory, PatternSpec, PatternStatus, register
from views.ux_lab.wing import ExhibitRender, ExhibitWingView

_CAT = PatternCategory.SELECTS
_SELECT_LIMITS = (
    "2–25 options per string select",
    "option label/value/description ≤ 100 chars",
    "1 select per action row",
)

_FAKE_ITEMS = tuple(f"item-{n:02d}" for n in range(1, 61))


def _header(title: str, body: str) -> discord.Embed:
    return discord.Embed(title=title, description=body, color=discord.Color.teal())


register(
    PatternSpec(
        pattern_id="category_select_single",
        title="Category select (navigation)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "hubs with 9+ dynamic children (hub-ui-standard threshold)",
            "the Games-hub child picker shape",
        ),
        anti_patterns=("≤8 static choices — visible buttons beat a closed menu",),
        limits=_SELECT_LIMITS,
        adopted_by=("views/games/hub.py GamesHubView",),
        notes="Pick a category — the panel content swaps in place.",
    ),
)

register(
    PatternSpec(
        pattern_id="settings_multi_select_preview",
        title="Multi-select → preview → apply",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "bulk settings toggles",
            "any multi-pick that mutates state — preview before apply",
        ),
        anti_patterns=("destructive bulk actions without the preview step",),
        limits=("min_values/max_values bound the pick count", *_SELECT_LIMITS),
        notes="Pick 1–3 modules, then Preview, then Apply (all fake).",
    ),
)

register(
    PatternSpec(
        pattern_id="select_paginated_over_25",
        title="Paginated select (lists beyond 25)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "role/channel/item lists longer than 25 (the selector-gap fix)",
        ),
        anti_patterns=(
            "silently slicing options[:25] — items become invisible "
            "(a real latent bug class here)",
        ),
        limits=("25 options per page — ◀ ▶ refill the menu", *_SELECT_LIMITS),
        notes="60 fake items, 3 pages. The page indicator lives on the placeholder.",
    ),
)

register(
    PatternSpec(
        pattern_id="entity_selects",
        title="Auto-populated entity selects",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "picking real users/roles/channels — Discord supplies the list, "
            "search included",
        ),
        anti_patterns=("fake string lists of members — entity selects are free",),
        limits=("Discord populates + searches; one select per row", *_SELECT_LIMITS),
        notes="Four entity types stacked. Picking only echoes — nothing mutates.",
    ),
)

register(
    PatternSpec(
        pattern_id="select_with_descriptions",
        title="Options with descriptions, emoji + default",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "choices needing a one-line explanation each (presets, modes)",
        ),
        anti_patterns=("descriptions that just repeat the label",),
        limits=_SELECT_LIMITS,
        notes="One option ships pre-selected (default=True) — note the check mark.",
    ),
)

register(
    PatternSpec(
        pattern_id="filter_then_list",
        title="Two-stage filter (hierarchy navigation)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "category → item hierarchies (channel categories, shop sections)",
        ),
        anti_patterns=("flat lists that fit one menu — don't add a stage",),
        limits=_SELECT_LIMITS,
        notes="The first select narrows what the second offers.",
    ),
)

register(
    PatternSpec(
        pattern_id="select_as_verb_picker",
        title="Target select + verb buttons (platform-manager shape)",
        category=_CAT,
        status=PatternStatus.STABLE,
        recommended_for=(
            "platform-manager panels: pick target, then Enable/Disable/Refresh "
            "(hub-ui-standard preset 4)",
        ),
        anti_patterns=("verbs the canonical pipeline doesn't expose",),
        limits=_SELECT_LIMITS,
        adopted_by=("views/diagnostic/flag_manager.py FlagManagerView",),
        notes="Pick a fake flag, then a verb — the result card names both.",
    ),
)

register(
    PatternSpec(
        pattern_id="search_via_modal",
        title="Search box for a select (modal-fed filter)",
        category=_CAT,
        status=PatternStatus.EXPERIMENTAL,
        requires_modal=True,
        recommended_for=(
            "long string lists where typing beats paging (item catalogues)",
        ),
        anti_patterns=("entity lists — UserSelect/RoleSelect already search",),
        limits=("modal round-trip costs one click vs native search", *_SELECT_LIMITS),
        notes="🔍 opens a modal; the select refills with matches.",
    ),
)


class _SearchModal(discord.ui.Modal, title="Filter the list"):
    query: discord.ui.TextInput[discord.ui.Modal] = discord.ui.TextInput(
        label="Search",
        placeholder="e.g. 4",
        max_length=20,
        required=False,
    )

    def __init__(self, wing: SelectsWingView) -> None:
        super().__init__()
        self._wing = wing

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self._wing.state["query"] = str(self.query.value).strip()
        await self._wing.rerender(interaction)


class SelectsWingView(ExhibitWingView):
    """Wing 2 — select menus."""

    WING_TITLE = "Selects"
    WING_EMOJI = "📋"

    def _exhibit_ids(self) -> tuple[str, ...]:
        return (
            "category_select_single",
            "settings_multi_select_preview",
            "select_paginated_over_25",
            "entity_selects",
            "select_with_descriptions",
            "filter_then_list",
            "select_as_verb_picker",
            "search_via_modal",
        )

    def _render_exhibit(self, pattern_id: str) -> ExhibitRender:
        render = {
            "category_select_single": self._ex_category,
            "settings_multi_select_preview": self._ex_multi_preview,
            "select_paginated_over_25": self._ex_paginated,
            "entity_selects": self._ex_entities,
            "select_with_descriptions": self._ex_descriptions,
            "filter_then_list": self._ex_filter_then_list,
            "select_as_verb_picker": self._ex_verb_picker,
            "search_via_modal": self._ex_search_modal,
        }[pattern_id]
        return render()

    # -- exhibits -------------------------------------------------------------

    def _ex_category(self) -> ExhibitRender:
        picked: str | None = self.state.get("picked")
        sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder="Open a category…",
            options=[
                discord.SelectOption(label=c, emoji=e)
                for c, e in (
                    ("Competitive", "⚔️"),
                    ("Activities", "🎲"),
                    ("Progression", "📈"),
                )
            ],
            row=0,
        )

        async def _pick(interaction: discord.Interaction) -> None:
            self.state["picked"] = sel.values[0]
            await self.rerender(interaction)

        sel.callback = _pick  # type: ignore[method-assign]
        body = (
            f"You're 'inside' **{picked}** now — same message, swapped content."
            if picked
            else "Pick a category. The panel updates in place (no new message)."
        )
        return ([_header("📂 Category navigation", body)], [sel])

    def _ex_multi_preview(self) -> ExhibitRender:
        picked: list[str] = self.state.get("picked", [])
        stage: str = self.state.get("stage", "picking")
        items: list[discord.ui.Item[discord.ui.View]] = []
        if stage == "picking":
            sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
                placeholder="Enable 1–3 modules…",
                min_values=1,
                max_values=3,
                options=[
                    discord.SelectOption(label=m, emoji="📦")
                    for m in ("Welcome", "Logging", "Automod", "Counters", "Events")
                ],
                row=0,
            )

            async def _pick(interaction: discord.Interaction) -> None:
                self.state["picked"] = list(sel.values)
                await self.rerender(interaction)

            sel.callback = _pick  # type: ignore[method-assign]
            items.append(sel)
            preview = self.demo_button(
                "Preview →",
                style=discord.ButtonStyle.primary,
                row=1,
                disabled=not picked,
            )

            async def _preview(interaction: discord.Interaction) -> None:
                self.state["stage"] = "preview"
                await self.rerender(interaction)

            preview.callback = _preview  # type: ignore[method-assign]
            items.append(preview)
            body = (
                "Pick modules (min 1, max 3), then **Preview**.\n"
                f"Currently picked: {', '.join(picked) or '—'}"
            )
        else:
            apply_btn = self.demo_button(
                "Apply",
                style=discord.ButtonStyle.success,
                row=0,
            )
            back = self.demo_button("◀ Edit picks", row=0)

            async def _apply(interaction: discord.Interaction) -> None:
                self.state.clear()
                await self.ack(
                    interaction,
                    f"✅ (fake) Enabled: **{', '.join(picked)}**. A real flow "
                    "writes through the audited settings pipeline here.",
                )

            async def _back(interaction: discord.Interaction) -> None:
                self.state["stage"] = "picking"
                await self.rerender(interaction)

            apply_btn.callback = _apply  # type: ignore[method-assign]
            back.callback = _back  # type: ignore[method-assign]
            items += [apply_btn, back]
            body = "**Preview — about to enable:**\n" + "\n".join(
                f"• 📦 {m}" for m in picked
            )
        return ([_header("☑️ Multi-select with preview", body)], items)

    def _ex_paginated(self) -> ExhibitRender:
        page: int = self.state.get("page", 0)
        pages = [_FAKE_ITEMS[i : i + 25] for i in range(0, len(_FAKE_ITEMS), 25)]
        page %= len(pages)
        sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder=f"Pick an item… (page {page + 1}/{len(pages)})",
            options=[discord.SelectOption(label=i) for i in pages[page]],
            row=0,
        )

        async def _pick(interaction: discord.Interaction) -> None:
            await self.ack(interaction, f"Picked **{sel.values[0]}** — no mutation.")

        sel.callback = _pick  # type: ignore[method-assign]
        prev = self.demo_button("◀ page", row=1)
        nxt = self.demo_button("page ▶", row=1)

        async def _prev(interaction: discord.Interaction) -> None:
            self.state["page"] = (page - 1) % len(pages)
            await self.rerender(interaction)

        async def _next(interaction: discord.Interaction) -> None:
            self.state["page"] = (page + 1) % len(pages)
            await self.rerender(interaction)

        prev.callback = _prev  # type: ignore[method-assign]
        nxt.callback = _next  # type: ignore[method-assign]
        return (
            [
                _header(
                    "📜 60 items, one select",
                    "A select holds 25 options; ◀ ▶ refill it per page. The page "
                    "lives on the **placeholder** so it survives the closed state.",
                ),
            ],
            [sel, prev, nxt],
        )

    def _ex_entities(self) -> ExhibitRender:
        items: list[discord.ui.Item[discord.ui.View]] = []
        makers: tuple[tuple[str, type], ...] = (
            ("member", discord.ui.UserSelect),
            ("role", discord.ui.RoleSelect),
            ("channel", discord.ui.ChannelSelect),
            ("user or role", discord.ui.MentionableSelect),
        )
        for row, (noun, cls) in enumerate(makers):
            sel = cls(placeholder=f"Pick a {noun}…", row=row)

            async def _pick(
                interaction: discord.Interaction,
                menu: discord.ui.Item[discord.ui.View] = sel,
                kind: str = noun,
            ) -> None:
                values = getattr(menu, "values", [])
                shown = ", ".join(str(v) for v in values) or "nothing"
                await self.ack(
                    interaction,
                    f"Resolved {kind}: **{shown}** — echo only, no mutation.",
                )

            sel.callback = _pick  # type: ignore[method-assign]
            items.append(sel)
        return (
            [
                _header(
                    "👥 Entity selects",
                    "User / Role / Channel / Mentionable — Discord populates and "
                    "searches these natively. Each occupies a full row.",
                ),
            ],
            items,
        )

    def _ex_descriptions(self) -> ExhibitRender:
        sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder="Pick a preset…",
            options=[
                discord.SelectOption(
                    label="Cozy",
                    emoji="🛋️",
                    description="Slow XP, no pings, weekly digest",
                ),
                discord.SelectOption(
                    label="Balanced",
                    emoji="⚖️",
                    description="The defaults most servers want",
                    default=True,
                ),
                discord.SelectOption(
                    label="Competitive",
                    emoji="🏁",
                    description="Fast XP, leaderboards everywhere",
                ),
            ],
            row=0,
        )

        async def _pick(interaction: discord.Interaction) -> None:
            await self.ack(interaction, f"Preset **{sel.values[0]}** (fake-)selected.")

        sel.callback = _pick  # type: ignore[method-assign]
        return (
            [
                _header(
                    "💬 Descriptions, emoji, default",
                    "Each option explains itself in ≤100 chars; **Balanced** ships "
                    "pre-selected via `default=True`.",
                ),
            ],
            [sel],
        )

    def _ex_filter_then_list(self) -> ExhibitRender:
        catalogue = {
            "Tools": ("Pickaxe", "Lantern", "Rope"),
            "Potions": ("Haste", "Glow", "Luck"),
            "Gear": ("Helmet", "Boots", "Gloves"),
        }
        category: str | None = self.state.get("category")
        items: list[discord.ui.Item[discord.ui.View]] = []
        cat_sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder="1 · Pick a category…",
            options=[discord.SelectOption(label=c) for c in catalogue],
            row=0,
        )

        async def _pick_cat(interaction: discord.Interaction) -> None:
            self.state["category"] = cat_sel.values[0]
            await self.rerender(interaction)

        cat_sel.callback = _pick_cat  # type: ignore[method-assign]
        items.append(cat_sel)
        if category:
            item_sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
                placeholder=f"2 · Pick from {category}…",
                options=[discord.SelectOption(label=i) for i in catalogue[category]],
                row=1,
            )

            async def _pick_item(interaction: discord.Interaction) -> None:
                await self.ack(
                    interaction,
                    f"Picked **{item_sel.values[0]}** from **{category}**.",
                )

            item_sel.callback = _pick_item  # type: ignore[method-assign]
            items.append(item_sel)
        body = (
            f"Stage 2 unlocked for **{category}** — the second menu only offers "
            "that category's items."
            if category
            else "Two-stage hierarchy: the second select appears once the first "
            "narrows it."
        )
        return ([_header("🗂️ Filter → list", body)], items)

    def _ex_verb_picker(self) -> ExhibitRender:
        target: str | None = self.state.get("target")
        sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
            placeholder="Pick a (fake) feature flag…",
            options=[
                discord.SelectOption(label=f, emoji="🚩")
                for f in ("spotlight_v2", "mining_events", "ai_summaries")
            ],
            row=0,
        )

        async def _pick(interaction: discord.Interaction) -> None:
            self.state["target"] = sel.values[0]
            await self.rerender(interaction)

        sel.callback = _pick  # type: ignore[method-assign]
        items: list[discord.ui.Item[discord.ui.View]] = [sel]
        for verb, style in (
            ("Enable", discord.ButtonStyle.success),
            ("Disable", discord.ButtonStyle.danger),
            ("Refresh", discord.ButtonStyle.secondary),
        ):
            btn = self.demo_button(verb, style=style, row=1, disabled=target is None)

            async def _act(
                interaction: discord.Interaction,
                action: str = verb,
            ) -> None:
                await self.ack(
                    interaction,
                    f"🚩 (fake) **{action}** → `{target}`. A real panel routes "
                    "this through the canonical flag pipeline (audited).",
                )

            btn.callback = _act  # type: ignore[method-assign]
            items.append(btn)
        body = (
            f"Target locked: `{target}` — now pick a verb."
            if target
            else "Pick the target first; the verb bank stays disabled until then."
        )
        return ([_header("🚩 Target + verb bank", body)], items)

    def _ex_search_modal(self) -> ExhibitRender:
        query: str = self.state.get("query", "")
        matches = tuple(i for i in _FAKE_ITEMS if query in i)[:25]
        items: list[discord.ui.Item[discord.ui.View]] = []
        search = self.demo_button("🔍 Search…", row=0)

        async def _open(interaction: discord.Interaction) -> None:
            await interaction.response.send_modal(_SearchModal(self))

        search.callback = _open  # type: ignore[method-assign]
        items.append(search)
        if matches:
            sel: discord.ui.Select[discord.ui.View] = discord.ui.Select(
                placeholder=(
                    f"{len(matches)} match(es)" + (f" for “{query}”" if query else "")
                ),
                options=[discord.SelectOption(label=m) for m in matches],
                row=1,
            )

            async def _pick(interaction: discord.Interaction) -> None:
                await self.ack(interaction, f"Picked **{sel.values[0]}**.")

            sel.callback = _pick  # type: ignore[method-assign]
            items.append(sel)
        body = (
            f"Filter: `{query or '(none)'}` → {len(matches)} of {len(_FAKE_ITEMS)} "
            "items shown. Try `4`."
        )
        return ([_header("🔍 Modal-fed filter", body)], items)
