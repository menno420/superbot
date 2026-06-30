from __future__ import annotations

import json
import logging
import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.interaction_helpers import safe_defer
from core.runtime.permission_checks import app_admin_or_owner
from utils.ui_constants import ERROR_COLOR, INFO_COLOR, SUCCESS_COLOR

logger = logging.getLogger("bot")

_MISSING_TOKEN_HELP = (
    "The Hermes→Claude dispatch bridge is not configured.\n\n"
    "Set these env vars on Railway (or in `.env` locally):\n"
    "```\n"
    "CLAUDE_ROUTINE_FIRE_URL=https://api.anthropic.com/v1/claude_code/routines/<id>/fire\n"
    "CLAUDE_ROUTINE_TOKEN=sk-ant-oat01-…\n"
    "CLAUDE_ROUTINE_BETA=experimental-cc-routine-2026-04-01\n"
    "CLAUDE_ROUTINE_VERSION=2023-06-01\n"
    "```\n"
    "See `docs/operations/hermes-dispatch-bridge.md` for the full setup runbook."
)


def _build_work_order(task: str, context: str, notes: str, cls: str) -> str:
    parts = [f"TASK: {task}"]
    if context:
        parts.append(f"CONTEXT: {context}")
    parts.append(
        "ACCEPTANCE: fix is confirmed by CI green and the described bug no longer occurs",
    )
    parts.append(f"CLASS: {cls}")
    if notes:
        parts.append(f"NOTES: {notes}")
    return "\n".join(parts)


async def _fire_work_order(work_order: str) -> dict:
    """POST work_order to the Claude Code Routine /fire endpoint.

    Returns the parsed JSON response dict, or raises RuntimeError with a
    human-readable message on config / network / API errors.
    """
    fire_url = os.getenv("CLAUDE_ROUTINE_FIRE_URL", "")
    token = os.getenv("CLAUDE_ROUTINE_TOKEN", "")
    beta = os.getenv("CLAUDE_ROUTINE_BETA", "experimental-cc-routine-2026-04-01")
    version = os.getenv("CLAUDE_ROUTINE_VERSION", "2023-06-01")

    if not fire_url or not token:
        raise RuntimeError("missing_config")

    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": beta,
        "anthropic-version": version,
        "Content-Type": "application/json",
    }
    payload = json.dumps({"text": work_order})

    timeout = aiohttp.ClientTimeout(total=15)
    async with (
        aiohttp.ClientSession() as session,
        session.post(
            fire_url,
            headers=headers,
            data=payload,
            timeout=timeout,
        ) as resp,
    ):
        body = await resp.text()
        if resp.status not in (200, 201, 202):
            raise RuntimeError(f"API error {resp.status}: {body[:200]}")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"raw": body}


class HermesCog(commands.Cog):
    """Discord-side entry point for the Hermes → Claude Code dispatch bridge.

    Lets admins submit bug reports or arbitrary work orders from Discord,
    which are forwarded to the Claude Code Routine /fire endpoint and
    resolved autonomously (CI-gated, self-merging for fixes per Q-0113).
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="bugreport",
        description="Report a bug — Hermes dispatches a Claude Code session to fix it automatically.",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.describe(
        title="Short one-line description of the bug",
        description="What happens, what should happen, and where (file/command/feature if known)",
        notes="Optional: extra context, related PR numbers, gotchas",
    )
    async def bugreport_slash(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        notes: str = "",
    ) -> None:
        """Submit a bug report that fires an autonomous fix session."""
        await safe_defer(interaction, ephemeral=True)

        work_order = _build_work_order(
            task=title,
            context=description,
            notes=notes,
            cls="fix",
        )

        try:
            result = await _fire_work_order(work_order)
        except RuntimeError as exc:
            if str(exc) == "missing_config":
                embed = discord.Embed(
                    title="Hermes bridge not configured",
                    description=_MISSING_TOKEN_HELP,
                    color=ERROR_COLOR,
                )
            else:
                embed = discord.Embed(
                    title="Dispatch failed",
                    description=f"The routine API returned an error:\n```{exc}```",
                    color=ERROR_COLOR,
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        session_url = result.get("claude_code_session_url", "")
        embed = discord.Embed(
            title="Bug report dispatched",
            description=(
                f"**Task:** {title}\n\n"
                f"A Claude Code session has been queued to investigate and fix this.\n"
                f"It will open a PR on a `claude/` branch and self-merge on green CI."
            ),
            color=SUCCESS_COLOR,
        )
        if session_url:
            embed.add_field(name="Watch the session", value=session_url, inline=False)
        embed.set_footer(text="CLASS: fix — self-merges on green CI (Q-0113)")
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info("Hermes bug report dispatched by %s: %s", interaction.user, title)

    @app_commands.command(
        name="dispatch",
        description="Send a raw Hermes work order to the Claude Code Routine (owner only).",
    )
    @app_commands.default_permissions(administrator=True)
    @app_admin_or_owner()
    @app_commands.describe(
        work_order=(
            "The full work order text. Include TASK/CONTEXT/ACCEPTANCE/CLASS/NOTES fields, "
            "or just describe the task and the routine will orient itself."
        ),
    )
    async def dispatch_slash(
        self,
        interaction: discord.Interaction,
        work_order: str,
    ) -> None:
        """Fire an arbitrary work order at the Claude Code Routine."""
        await safe_defer(interaction, ephemeral=True)

        try:
            result = await _fire_work_order(work_order)
        except RuntimeError as exc:
            if str(exc) == "missing_config":
                embed = discord.Embed(
                    title="Hermes bridge not configured",
                    description=_MISSING_TOKEN_HELP,
                    color=ERROR_COLOR,
                )
            else:
                embed = discord.Embed(
                    title="Dispatch failed",
                    description=f"The routine API returned an error:\n```{exc}```",
                    color=ERROR_COLOR,
                )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        session_url = result.get("claude_code_session_url", "")
        embed = discord.Embed(
            title="Work order dispatched",
            description="The Claude Code Routine has received your work order.",
            color=INFO_COLOR,
        )
        if session_url:
            embed.add_field(name="Watch the session", value=session_url, inline=False)
        embed.add_field(
            name="Work order",
            value=f"```{work_order[:900]}```",
            inline=False,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info("Hermes dispatch by %s: %s", interaction.user, work_order[:120])


async def setup(bot):
    await bot.add_cog(HermesCog(bot))
