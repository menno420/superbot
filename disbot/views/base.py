from __future__ import annotations

import logging

import discord
from discord.ext import commands

logger = logging.getLogger("bot.views")

# Canonical interaction lifecycle doctrine:
#
# - General interactive panels should inherit BaseView.
# - Ephemeral hub/navigation panels should inherit HubView.
# - Persistent cross-restart views should inherit PersistentView
#   (defined in core/runtime/persistent_views.py).
# - Game-state views may extend discord.ui.View directly when
#   specialized timeout cleanup, state coupling, or gameplay
#   lifecycle ownership is required.
#
# Divergence from these patterns should be intentional and documented.


async def send_panel(
    ctx: commands.Context,
    *,
    embed: discord.Embed,
    view: BaseView,
    file: discord.File | None = None,
) -> discord.Message:
    """Send ``embed`` + ``view`` in ``ctx.channel`` and bind the message to view.

    Centralises the ``msg = await ctx.send(...); view.message = msg`` pattern
    so panel commands stay one line.  Binding ``view.message`` is what lets
    :meth:`BaseView.on_timeout` edit the message to disable the buttons when
    the view expires.

    *file* is an optional attachment (e.g. a rendered hero-card image the embed
    references via ``attachment://``); omitted keeps the embed-only behaviour
    byte-identical.

    Returns the sent message so callers that still need the reference can
    use it directly.
    """
    if file is not None:
        msg = await ctx.send(embed=embed, view=view, file=file)
    else:
        msg = await ctx.send(embed=embed, view=view)
    view.message = msg
    return msg


async def handle_view_error(
    view: discord.ui.View,
    interaction: discord.Interaction,
    error: Exception,
    item: discord.ui.Item,  # type: ignore[type-arg]
) -> None:
    """Standard view-error handler: rich-context log + generic ephemeral.

    Used by :meth:`BaseView.on_error`, :meth:`PersistentView.on_error`, and
    the blackjack view subclasses (which extend ``discord.ui.View`` directly).
    Channel-management views in ``views/channels/`` keep their own
    ``on_error`` because they intentionally surface ``type(error).__name__``
    to admins for diagnosability.
    """
    # response_done distinguishes "raised before first response" from
    # "raised after defer" — these need different remediation in callbacks
    # (the former is a missing safe_defer; the latter is a service bug).
    response_done = interaction.response.is_done()
    logger.error(
        "View error | view=%s item_type=%s custom_id=%r label=%r "
        "user=%s guild=%s channel=%s message=%s response_done=%s",
        type(view).__name__,
        type(item).__name__,
        getattr(item, "custom_id", None),
        getattr(item, "label", None),
        getattr(interaction.user, "id", None),
        interaction.guild_id,
        interaction.channel_id,
        interaction.message.id if interaction.message else None,
        response_done,
        exc_info=error,
    )
    if not response_done:
        try:
            await interaction.response.send_message(
                "An error occurred. Please try again.",
                ephemeral=True,
            )
        except Exception:
            pass


def interaction_is_admin(interaction: discord.Interaction) -> bool:
    """Return ``True`` when the interacting user holds Discord administrator.

    Matches the ``@has_permissions(administrator=True)`` bar used by the typed
    admin commands.  Use it as a panel-callback authority re-check: a panel's
    entry point may not be admin-gated (e.g. opened via the Help menu), and
    :class:`BaseView` only locks a panel to its invoker, not to an authority.
    """
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms is not None and perms.administrator)


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
            except Exception as exc:
                logger.debug(
                    "%s.on_timeout: message.edit failed (msg=%s): %s",
                    type(self).__name__,
                    self.message.id,
                    exc,
                )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        await handle_view_error(self, interaction, error, item)


class HubView(BaseView):
    """Interactive panel hub with the standard 180-second timeout.

    Centralises the ``timeout=180`` default that every hub view duplicated.
    Subclasses pass only ``author`` (or ``author, public=True`` for shared
    panels) — the timeout no longer needs to be repeated per cog.

    Use this for any view that anchors a panel command (e.g. ``!adminmenu``,
    ``!channelmenu``).  For one-off views with different timeouts (e.g. a
    20-second confirmation prompt) keep extending :class:`BaseView` directly.
    """

    DEFAULT_TIMEOUT = 180

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        public: bool = False,
    ) -> None:
        super().__init__(author, public=public, timeout=self.DEFAULT_TIMEOUT)
