from __future__ import annotations

import logging

import discord
from discord.ext import commands

from config import is_platform_owner

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
    """Return ``True`` when the interacting user holds Discord administrator
    (or is the configured platform owner).

    Matches the ``@has_permissions(administrator=True)`` bar used by the typed
    admin commands.  Use it as a panel-callback authority re-check: a panel's
    entry point may not be admin-gated (e.g. opened via the Help menu), and
    :class:`BaseView` only locks a panel to its invoker, not to an authority.

    The configured **platform owner** (``config.BOT_OWNER_USER_ID``) always
    passes, so the bot owner can use admin config panels (AI, command access,
    setup) in any guild even without Discord permissions there.
    """
    if is_platform_owner(getattr(interaction.user, "id", None)):
        return True
    perms = getattr(interaction.user, "guild_permissions", None)
    return bool(perms is not None and perms.administrator)


def member_is_admin(member: object) -> bool:
    """Return ``True`` when ``member`` holds Discord administrator (or is the
    configured platform owner).

    The member-object counterpart of :func:`interaction_is_admin`, for view
    helpers that hold a ``discord.Member`` / ``discord.User`` rather than an
    ``Interaction``.  Both share the same single-source platform-owner check so
    the bot owner passes every admin config gate regardless of guild role.
    """
    if is_platform_owner(getattr(member, "id", None)):
        return True
    perms = getattr(member, "guild_permissions", None)
    return bool(perms is not None and getattr(perms, "administrator", False))


class BaseView(discord.ui.View):
    """Standard base for all SuperBot interactive panels.

    Enforces:
    - Invoker restriction (public=False, the default) or public access
    - Disable-on-timeout — never removes the view from the message
    - Message reference tracking for timeout editing
    - Standard nav: when the subclass declares ``SUBSYSTEM`` (and leaves
      ``STANDARD_NAV`` True), a 📚 Help button — and a ↩ Back-to-hub button
      when the subsystem has a ``parent_hub`` — are auto-attached on every
      construction, so a panel reached by *any* command stays one click from
      Help and its mother hub and never loses them on a redraw (owner
      directive 2026-06-23).
    """

    # Declared by panels that should carry standard nav (mirrors the
    # PersistentView contract). Empty ⇒ no auto-nav (confirmations, transient
    # sub-views). Set STANDARD_NAV = False to opt a SUBSYSTEM panel out.
    SUBSYSTEM: str = ""
    STANDARD_NAV: bool = True

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
        # Optional help-nav image card (visual card engine H3): a
        # ``build_help_menu_view`` hook that renders a showpiece image card sets
        # this so every help-nav render site forwards it (the same card the
        # direct command shows). Default ``None`` = embed-only, the historical
        # behaviour for every panel. See ``views.navigation.help_nav_card``.
        self.help_nav_card: discord.File | None = None
        from views.navigation import attach_standard_nav

        attach_standard_nav(self)

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
