"""Global error handling utilities."""

from __future__ import annotations

import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger(__name__)


def register_global_error_handler(bot: commands.Bot) -> None:
    """Register a global error handler on the bot."""

    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        message = _format_error(error)
        logger.error(
            "App command error in %s by %s: %s",
            getattr(interaction.command, "name", "unknown"),
            interaction.user,
            error,
            exc_info=error,
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            logger.warning("Failed to send error message for interaction")

    @bot.event
    async def on_command_error(
        ctx: commands.Context[Any],
        error: commands.CommandError,
    ) -> None:
        message = _format_error(error)
        logger.error(
            "Command error in %s by %s: %s",
            getattr(ctx.command, "qualified_name", "unknown"),
            getattr(ctx.author, "id", "unknown"),
            error,
            exc_info=error,
        )
        try:
            await ctx.send(message)
        except discord.HTTPException:
            logger.warning("Failed to send error message for text command")


def _format_error(error: Exception) -> str:
    if isinstance(error, commands.CommandOnCooldown | app_commands.CommandOnCooldown):
        return "This command is on cooldown."
    if isinstance(error, commands.BadArgument):
        return "Invalid argument provided."
    if isinstance(error, discord.Forbidden):
        return "I lack the required permissions."
    if isinstance(error, discord.HTTPException):
        return "A Discord API error occurred."
    return "An unexpected error occurred."
