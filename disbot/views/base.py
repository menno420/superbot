from __future__ import annotations

import logging

import discord

logger = logging.getLogger("bot.views")


class BaseView(discord.ui.View):
    """Standard base for all SuperBot interactive panels.

    Enforces:
    - Invoker restriction (public=False, the default) or public access
    - Disable-on-timeout — never removes the view from the message
    - Message reference tracking for timeout editing
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        public: bool = False,
        timeout: int = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self._author = author
        self._public = public
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._public:
            return True
        if interaction.user.id != self._author.id:
            await interaction.response.send_message(
                "This panel isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        logger.error(
            "View error | view=%s item_type=%s custom_id=%r label=%r "
            "user=%s guild=%s channel=%s message=%s",
            type(self).__name__,
            type(item).__name__,
            getattr(item, "custom_id", None),
            getattr(item, "label", None),
            getattr(interaction.user, "id", None),
            interaction.guild_id,
            interaction.channel_id,
            interaction.message.id if interaction.message else None,
            exc_info=error,
        )
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "An error occurred. Please try again.",
                    ephemeral=True,
                )
            except Exception:
                pass
