from __future__ import annotations

import discord


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
                "This panel isn't yours.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
