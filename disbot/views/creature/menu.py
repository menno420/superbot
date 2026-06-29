"""The Creatures menu — the interactive hub panel (completion cert #1, Q-0209).

``CreatureMenuView`` is the "make the menu a place" panel the Creatures completion
certificate called for (`docs/planning/feature-completion/units/creature.md` #1):
one author-restricted :class:`HubView` whose buttons route into the existing
creature flows —

* **🐾 Catch** — runs one wild encounter *in place* (shares
  ``creature_workflow.catch`` with the ``!catch`` command);
* **📖 Dex** — opens the interactive dex browser (filter by element);
* **⚔️ Challenge** — pick a trainer (UserSelect) → the existing
  :class:`CreatureBattleChallengeView` accept/decline flow;
* **🏆 Ladder** — the server's PvP win ladder;
* **📖 How to play** — the rules card.

Reached from the Help hub (``CreatureCog.build_help_menu_view``) and the
``!creatures`` command. Mirrors :mod:`views.fishing.menu` and
:mod:`views.games.deathmatch_panel` — a panel whose buttons spawn real flows.
Declares ``SUBSYSTEM = "creature"`` so :func:`views.navigation.attach_standard_nav`
auto-attaches **📚 Help** + **↩ Games** (the never-stranded directive).
"""

from __future__ import annotations

import discord

from core.runtime import guild_resources as resources
from services import creature_workflow, game_xp_service
from utils import db
from views.base import HubView
from views.creature.embeds import (
    ELEMENTS,
    build_battletop_embed,
    build_catch_result_embed,
    build_dex_embed,
    build_menu_embed,
    build_rules_embed,
)


async def load_progress(user_id: int, guild_id: int) -> tuple[int, int, dict[str, int]]:
    """Return ``(caught_unique, level, collection_log)`` for the menu/dex renders."""
    from utils.creatures import CREATURES

    log = await db.get_creature_collection(user_id, guild_id)
    xp_map = await db.get_game_xp(user_id, guild_id)
    level = creature_workflow.creature_level_from_xp(
        xp_map.get(game_xp_service.GAME_CREATURE, 0),
    )
    known = {c.name for c in CREATURES}
    caught_unique = sum(1 for name in log if name in known)
    return caught_unique, level, log


async def _menu_embed(user_id: int, guild_id: int) -> discord.Embed:
    caught_unique, level, _ = await load_progress(user_id, guild_id)
    return build_menu_embed(caught_unique, level)


class CreatureMenuView(HubView):
    """The author-restricted Creatures hub (Catch · Dex · Challenge · Ladder)."""

    SUBSYSTEM = "creature"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(label="Catch", emoji="🐾", style=discord.ButtonStyle.success)
    async def catch_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        result = await creature_workflow.catch(self._author.id, self.guild_id)
        embed = build_catch_result_embed(self._author.display_name, result)
        # Keep the menu so the player can immediately catch again or browse the dex.
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Dex", emoji="📖", style=discord.ButtonStyle.secondary)
    async def dex_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        _count, level, log = await load_progress(self._author.id, self.guild_id)
        embed = build_dex_embed(self._author.display_name, log, level)
        view = CreatureDexView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(
        label="Challenge",
        emoji="⚔️",
        style=discord.ButtonStyle.primary,
    )
    async def challenge_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        embed = discord.Embed(
            title="⚔️ Challenge a trainer",
            description=(
                "Pick the trainer you want to battle. They'll get an Accept / "
                "Decline prompt; teams are level-normalized, so your collection and "
                "type matchups decide it."
            ),
            color=discord.Color.red(),
        )
        view = CreatureChallengeSelectView(self._author, self.guild_id)
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

    @discord.ui.button(label="Ladder", emoji="🏆", style=discord.ButtonStyle.secondary)
    async def ladder_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        rows = await db.top_battlers(self.guild_id)
        guild = interaction.guild

        def _name(user_id: int) -> str:
            member = resources.resolve_member(guild, user_id) if guild else None
            return member.display_name if member else f"User {user_id}"

        embed = build_battletop_embed(rows, _name)
        # Keep the menu so the player can challenge / catch straight after.
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="How to play",
        emoji="📖",
        style=discord.ButtonStyle.secondary,
    )
    async def rules_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await interaction.response.send_message(
            embed=build_rules_embed(),
            ephemeral=True,
        )


class _ElementFilterSelect(discord.ui.Select):
    """The dex browser's element filter — All + one option per element."""

    def __init__(self) -> None:
        options = [
            discord.SelectOption(label="All elements", value="", default=True),
        ]
        options += [
            discord.SelectOption(label=element, value=element) for element in ELEMENTS
        ]
        super().__init__(
            placeholder="Filter by element…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, CreatureDexView):
            return
        element = self.values[0] or None
        _, level, log = await load_progress(view._author.id, view.guild_id)
        embed = build_dex_embed(
            view._author.display_name,
            log,
            level,
            element=element,
        )
        # Reflect the active filter as the select's default for the next render.
        for option in self.options:
            option.default = option.value == self.values[0]
        await interaction.response.edit_message(embed=embed, view=view)


class CreatureDexView(HubView):
    """Interactive dex browser — filter the collection by element, ↩ back to menu.

    Completion cert #2: ``!dex`` was a static embed; this adds the browse/filter
    convenience the other activity games meet, while staying one click from the
    Creatures menu (◀ Back) and Help/↩ Games (standard nav).
    """

    SUBSYSTEM = "creature"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.add_item(_ElementFilterSelect())

    @discord.ui.button(
        label="Back",
        emoji="◀",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await open_creature_menu(interaction, self._author, self.guild_id)


class CreatureChallengeSelectView(HubView):
    """Pick an opponent → open the existing creature PvP challenge flow."""

    SUBSYSTEM = "creature"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id
        self.add_item(_OpponentSelect())

    @discord.ui.button(
        label="Back",
        emoji="◀",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def back_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        await open_creature_menu(interaction, self._author, self.guild_id)


class _OpponentSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose a trainer to battle…",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        # Lazy import — the challenge view lives under views.creature_battle; a
        # function-body import keeps this menu module's edge set small (and avoids
        # any import cycle as the creature surface grows).
        from views.creature_battle import CreatureBattleChallengeView

        view = self.view
        if not isinstance(view, CreatureChallengeSelectView):
            return
        opponent = self.values[0]
        challenger = interaction.user
        if not isinstance(opponent, discord.Member) or not isinstance(
            challenger,
            discord.Member,
        ):
            await interaction.response.send_message(
                "Both trainers must be server members.",
                ephemeral=True,
            )
            return
        if opponent.bot:
            await interaction.response.send_message(
                "🤖 You can't battle a bot — challenge a real trainer!",
                ephemeral=True,
            )
            return
        if opponent.id == challenger.id:
            await interaction.response.send_message(
                "🪞 You can't battle yourself — pick someone else!",
                ephemeral=True,
            )
            return
        challenge = CreatureBattleChallengeView(challenger, opponent, view.guild_id)
        await interaction.response.edit_message(
            content=(
                f"{opponent.mention} — {challenger.mention} challenges you to a "
                "creature battle! Teams are level-normalized; your collection and "
                "type matchups decide it."
            ),
            embed=None,
            view=challenge,
        )
        challenge.message = interaction.message


async def open_creature_menu(
    interaction: discord.Interaction,
    author: discord.Member | discord.User,
    guild_id: int,
) -> None:
    """Rebuild the Creatures menu in place — the dex/challenge views' ◀ back target.

    Mints a fresh, fully-navigable :class:`CreatureMenuView` and edits it back onto
    the panel message (clearing any challenge ``content`` the sub-views set).
    """
    view = CreatureMenuView(author, guild_id)
    embed = await _menu_embed(author.id, guild_id)
    await interaction.response.edit_message(content=None, embed=embed, view=view)
    view.message = interaction.message
