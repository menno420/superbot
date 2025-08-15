"""Error handling utilities."""

from __future__ import annotations

import traceback
import uuid
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from config import get_settings
from .logging_service import log_error


class UserFacingError(Exception):
    """Exception raised for expected user-visible errors."""


class ConfigError(Exception):
    """Configuration related error."""


class MigrationError(Exception):
    """Database migration error."""


def _redact(text: str) -> str:
    for secret in get_settings().secret_values():
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


def format_exception(exc: BaseException) -> str:
    """Return a redacted traceback string for the exception."""
    trace = "".join(traceback.format_exception(exc))
    return _redact(trace)


def setup_error_handlers(bot: commands.Bot) -> None:
    """Register global error handlers for commands and events."""

    @bot.event
    async def on_error(event_method: str, /, *_args: object, **_kwargs: object) -> None:
        log_error("Unhandled event error in %s", event_method, exc_info=True)

    @bot.event
    async def on_command_error(
        ctx: commands.Context[Any],
        error: commands.CommandError,
    ) -> None:
        err = getattr(error, "original", error)
        if isinstance(err, UserFacingError):
            await ctx.send(str(err))
            return
        code = uuid.uuid4().hex[:8]
        log_error("Command error %s", code, exc_info=err)
        await ctx.send(
            f"An unexpected error occurred. It's been logged. Code: {code}",
        )

    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        err = getattr(error, "original", error)
        if isinstance(err, UserFacingError):
            message = str(err)
        else:
            code = uuid.uuid4().hex[:8]
            log_error("App command error %s", code, exc_info=err)
            message = (
                "An unexpected error occurred. It's been logged. "
                f"Code: {code}"
            )
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
