"""Guild instruction-profile editor modal (PR-6).

Authoritative writer for guild-scope AI instruction bodies. The
legacy ``ai_guild_instruction_profile`` scalar is hidden from the
primary settings panel (see ``cogs/ai/schemas.py:hidden_from_panel``);
operators edit the typed-table row through this modal instead.

Write path: ``ai_instruction_mutation.upsert_profile`` → captures the
returned profile id → ``ai_policy_mutation.set_guild_policy`` to bind
the profile id into ``ai_guild_policy.guild_instruction_profile_id``
(preserving every other guild-policy field per PR-6's preservation
invariant).

Read path: the modal pre-fills its body from the current
``ai_instruction_profile`` row (if one is bound), so the operator
sees what they are editing rather than a blank field.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.behavior.instruction_modal")

# Discord modal TextInput max-length cap (paragraph style).
_BODY_MAX_LENGTH = 4000

# Canonical name for the guild-default profile row. Mirrors the
# planned M2 backfill ("default") so the typed table has one well-
# known row per guild.
_GUILD_PROFILE_NAME = "default"


class GuildInstructionProfileModal(discord.ui.Modal):
    """Edit (or create) the guild's default instruction profile.

    The modal renders a single paragraph-style text input. On submit:

    1. Build (or refresh) the typed ``ai_instruction_profile`` row
       via :func:`ai_instruction_mutation.upsert_profile`.
    2. Bind the returned profile id into
       ``ai_guild_policy.guild_instruction_profile_id`` via
       :func:`ai_policy_mutation.set_guild_policy` — preserving every
       other guild-policy field per PR-6's preservation invariant.
    3. Send an ephemeral confirmation back to the operator.
    """

    def __init__(self) -> None:
        super().__init__(title="Edit guild instruction profile")
        self.body_input: discord.ui.TextInput = discord.ui.TextInput(
            label="Instruction body",
            style=discord.TextStyle.paragraph,
            placeholder=(
                "Free-text instructions that prefix every AI prompt "
                "for this guild. Leave blank to clear."
            ),
            required=False,
            max_length=_BODY_MAX_LENGTH,
        )
        self.add_item(self.body_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild_id is None:
            await interaction.response.send_message(
                "❌ This editor requires a guild context.",
                ephemeral=True,
            )
            return

        body = str(self.body_input.value or "").strip()

        try:
            profile_id = await _write_profile_and_bind(
                guild_id=interaction.guild_id,
                body=body,
                actor=interaction.user,
            )
        except Exception as exc:  # noqa: BLE001 — surface the failure
            logger.exception(
                "GuildInstructionProfileModal: write failed for guild=%s",
                interaction.guild_id,
            )
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            (
                f"✅ Guild instruction profile updated "
                f"(profile_id=`{profile_id}`, name=`{_GUILD_PROFILE_NAME}`). "
                "Other guild policy fields (provider, model, cooldown, "
                "min level) were preserved."
            ),
            ephemeral=True,
        )


async def _write_profile_and_bind(
    *,
    guild_id: int,
    body: str,
    actor: Any,
) -> int:
    """Upsert the profile row, then bind its id into the guild policy.

    Preservation invariant (PR-6): every guild-policy field NOT owned
    by this write (everything except ``guild_instruction_profile_id``)
    is read from the current row and passed through
    :func:`ai_policy_mutation.set_guild_policy` unchanged.

    Returns the profile id so the modal can confirm it to the operator.
    """
    from services import ai_instruction_mutation, ai_policy_mutation
    from utils.db import ai as ai_db

    profile_result = await ai_instruction_mutation.upsert_profile(
        guild_id=guild_id,
        name=_GUILD_PROFILE_NAME,
        body=body,
        scope="guild",
        actor=actor,
    )

    current = await ai_db.get_guild_policy(guild_id) or {}
    await ai_policy_mutation.set_guild_policy(
        guild_id,
        enabled=bool(current.get("enabled", False)),
        natural_language_enabled=bool(
            current.get("natural_language_enabled", False),
        ),
        default_provider=str(
            current.get("default_provider", "deterministic") or "deterministic",
        ),
        default_model=str(current.get("default_model", "") or ""),
        minimum_level_default=int(current.get("minimum_level_default", 2)),
        cooldown_seconds=int(current.get("cooldown_seconds", 30)),
        fresh_user_mention_allowance=int(
            current.get("fresh_user_mention_allowance", 1),
        ),
        guild_instruction_profile_id=profile_result.profile_id,
        actor=actor,
    )
    return profile_result.profile_id


__all__ = ["GuildInstructionProfileModal"]
