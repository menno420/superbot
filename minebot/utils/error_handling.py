# utils/error_handling.py
import discord
from discord.ext import commands
from helpers.embed_helper import error_embed
from utils.logging import log_error, log_warning
import traceback

async def handle_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CommandNotFound):
        log_warning(f"Command not found: {ctx.message.content}")
        return await ctx.send(embed=error_embed("❌ Command not found."))

    if isinstance(error, commands.MissingRequiredArgument):
        log_warning(f"Missing arguments in command: {ctx.command}")
        return await ctx.send(embed=error_embed("❌ Missing required arguments."))

    if isinstance(error, commands.MissingPermissions):
        log_warning(f"Missing permissions: User {ctx.author} tried {ctx.command}")
        return await ctx.send(embed=error_embed("❌ You don't have permission to execute this command."))

    if isinstance(error, commands.NotOwner):
        log_warning(f"Non-owner user {ctx.author} attempted owner-only command: {ctx.command}")
        return await ctx.send(embed=error_embed("❌ You are not allowed to use this command."))

    error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    log_error(f"Unexpected error from user '{ctx.author}' in command '{ctx.command}':\n{error_traceback}")

    await ctx.send(embed=error_embed("⚠️ An unexpected error occurred. Please contact an admin."))

def setup_global_error_handler(bot):
    @bot.event
    async def on_command_error(ctx, error):
        await handle_command_error(ctx, error)
