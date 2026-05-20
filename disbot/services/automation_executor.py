"""Automation executor — Phase 9g / Track 6 PR 17.

Per-action-kind dispatch from a single :func:`execute_rule` entry
point. Owns:

* The :class:`AutomationRunResult` shape consumed by the scheduler
  (Track 6 PR 18).
* The dispatch table that maps each documented ``action_kind`` to
  its async handler.
* The dry-run invariant: when ``dry_run=True`` no Discord-side
  side effect happens; the only DB write is the
  ``automation_runs`` row maintained by the caller (scheduler) via
  :func:`utils.db.automation.claim_run` / ``mark_running`` /
  ``finish_run``.

Per-action handlers are intentionally minimal in this PR:

* ``send_message`` — :meth:`channel.send`.
* ``assign_role`` / ``remove_role`` — :meth:`member.add_roles` /
  :meth:`member.remove_roles`.
* ``post_readiness_summary`` — builds the existing readiness embed
  and sends it.
* ``post_leaderboard_summary`` — placeholder result describing
  what *would* be posted; concrete leaderboard builder lands with
  Track 7 PR 22.
* ``bind_channel`` / ``create_channel`` — owner-only; route through
  the existing :mod:`services.binding_mutation` and
  :mod:`services.resource_provisioning` pipelines.
* ``notify_owner`` — DM the guild owner.

Failure isolation: every handler call is wrapped in a try/except.
A failing handler bumps the rule's ``failure_count`` and surfaces
the exception text in ``result_summary['error']``; it never
propagates into the scheduler loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import discord

from services.automation_registry import (
    KNOWN_ACTION_KINDS,
    get_action,
    validate_action_config,
)

logger = logging.getLogger("bot.services.automation_executor")


@dataclass(frozen=True)
class AutomationRunResult:
    """Outcome of one ``execute_rule`` call."""

    rule_id: int
    guild_id: int
    action_kind: str
    status: str  # "success" | "failure" | "skipped"
    dry_run: bool
    result_summary: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "success"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def execute_rule(
    rule: dict[str, Any],
    *,
    dry_run: bool = False,
    bot: Any | None = None,
    guild: discord.Guild | None = None,
    actor_id: int | None = None,
) -> AutomationRunResult:
    """Dispatch ``rule`` to its action handler.

    ``rule`` is the dict returned by :func:`utils.db.automation.get_rule`.
    The scheduler hands one row in per ``execute_rule`` call.

    ``bot`` and ``guild`` are passed through to handlers that need
    Discord-side context. ``actor_id`` is the operator id recorded
    on the rule (``rule['created_by']``) and is used for owner-gated
    actions.
    """
    rule_id = int(rule["id"])
    guild_id = int(rule["guild_id"])
    action_kind = str(rule.get("action_kind"))
    action_config = dict(rule.get("action_config") or {})

    if action_kind not in KNOWN_ACTION_KINDS:
        return AutomationRunResult(
            rule_id=rule_id,
            guild_id=guild_id,
            action_kind=action_kind,
            status="failure",
            dry_run=dry_run,
            error=f"unknown action_kind {action_kind!r}",
        )

    config_errors = validate_action_config(action_kind, action_config)
    if config_errors:
        return AutomationRunResult(
            rule_id=rule_id,
            guild_id=guild_id,
            action_kind=action_kind,
            status="failure",
            dry_run=dry_run,
            error="; ".join(config_errors),
        )

    handler = _HANDLERS.get(action_kind)
    if handler is None:
        return AutomationRunResult(
            rule_id=rule_id,
            guild_id=guild_id,
            action_kind=action_kind,
            status="failure",
            dry_run=dry_run,
            error=f"no executor handler for {action_kind!r}",
        )

    spec = get_action(action_kind)
    if spec is not None and spec.requires_owner and not dry_run:
        # We do not have the owner context here; gate via
        # actor_id present.  Track 8 wires the proper
        # ``setup_access.can_apply_setup`` resolution.
        if actor_id is None:
            return AutomationRunResult(
                rule_id=rule_id,
                guild_id=guild_id,
                action_kind=action_kind,
                status="failure",
                dry_run=dry_run,
                error=(
                    f"action {action_kind!r} requires owner authority but "
                    "no actor_id supplied to executor"
                ),
            )

    try:
        summary = await handler(
            rule=rule,
            config=action_config,
            dry_run=dry_run,
            bot=bot,
            guild=guild,
            actor_id=actor_id,
        )
    except Exception as exc:  # noqa: BLE001 — handler boundary
        logger.exception(
            "automation_executor: handler raised for rule_id=%d (action=%s)",
            rule_id,
            action_kind,
        )
        return AutomationRunResult(
            rule_id=rule_id,
            guild_id=guild_id,
            action_kind=action_kind,
            status="failure",
            dry_run=dry_run,
            error=f"{type(exc).__name__}: {exc}",
        )

    return AutomationRunResult(
        rule_id=rule_id,
        guild_id=guild_id,
        action_kind=action_kind,
        status="success",
        dry_run=dry_run,
        result_summary=summary or {},
    )


# ---------------------------------------------------------------------------
# Per-action handlers
# ---------------------------------------------------------------------------


async def _handle_send_message(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del rule, actor_id
    channel_id = int(config["channel_id"])
    template = str(config["template"])
    if dry_run or guild is None:
        return {
            "would_send_to": channel_id,
            "rendered_length": len(template),
            "dry_run": dry_run,
        }
    channel = guild.get_channel(channel_id)
    if channel is None:
        return {
            "skipped": True,
            "reason": f"channel {channel_id} not in cache",
        }
    if not isinstance(
        channel,
        (discord.TextChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        return {
            "skipped": True,
            "reason": f"channel {channel_id} is not a sendable text/voice/stage channel",
        }
    await channel.send(template)
    return {"sent_to": channel_id, "rendered_length": len(template)}


async def _handle_assign_role(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del bot, actor_id
    role_id = int(config["role_id"])
    member_id = int(rule.get("trigger_config", {}).get("member_id", 0))
    if dry_run or guild is None or member_id == 0:
        return {
            "would_assign_role": role_id,
            "to_member": member_id,
            "dry_run": dry_run,
        }
    from core.runtime.guild_resources import resolve_member, resolve_role

    role = resolve_role(guild, role_id=role_id)
    member = resolve_member(guild, member_id)
    if role is None or member is None:
        return {
            "skipped": True,
            "reason": "role or member missing in cache",
        }
    await member.add_roles(role, reason="automation:assign_role")
    return {"assigned_role": role_id, "to_member": member_id}


async def _handle_remove_role(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del bot, actor_id
    role_id = int(config["role_id"])
    member_id = int(rule.get("trigger_config", {}).get("member_id", 0))
    if dry_run or guild is None or member_id == 0:
        return {
            "would_remove_role": role_id,
            "from_member": member_id,
            "dry_run": dry_run,
        }
    from core.runtime.guild_resources import resolve_member, resolve_role

    role = resolve_role(guild, role_id=role_id)
    member = resolve_member(guild, member_id)
    if role is None or member is None:
        return {
            "skipped": True,
            "reason": "role or member missing in cache",
        }
    await member.remove_roles(role, reason="automation:remove_role")
    return {"removed_role": role_id, "from_member": member_id}


async def _handle_post_readiness_summary(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del rule, bot, actor_id
    channel_id = int(config["channel_id"])
    if dry_run or guild is None:
        return {
            "would_post_readiness_to": channel_id,
            "dry_run": dry_run,
        }
    from cogs.diagnostic._platform_embeds import build_setup_readiness_embed

    embed = await build_setup_readiness_embed(guild.id, guild=guild)
    channel = guild.get_channel(channel_id)
    if channel is None:
        return {"skipped": True, "reason": "channel not in cache"}
    if not isinstance(
        channel,
        (discord.TextChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        return {
            "skipped": True,
            "reason": "channel is not a sendable text/voice/stage channel",
        }
    await channel.send(embed=embed)
    return {"posted_readiness_to": channel_id}


async def _handle_post_leaderboard_summary(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    """Placeholder; concrete leaderboard builder lands in Track 7 PR 22."""
    del rule, bot, actor_id, guild
    return {
        "placeholder": True,
        "would_post_to": int(config["channel_id"]),
        "subsystem": str(config["subsystem"]),
        "dry_run": dry_run,
    }


async def _handle_bind_channel(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del rule, bot
    if dry_run or guild is None or actor_id is None:
        return {
            "would_bind": {
                "subsystem": config["subsystem"],
                "binding_name": config["binding_name"],
                "channel_id": config["channel_id"],
            },
            "dry_run": dry_run,
        }
    from core.runtime.subsystem_schema import BindingKind, get_schema
    from services.binding_mutation import BindingMutationPipeline

    schema = get_schema(str(config["subsystem"]))
    if schema is None:
        return {
            "skipped": True,
            "reason": f"subsystem {config['subsystem']!r} not registered",
        }
    from core.runtime.guild_resources import resolve_member

    actor = resolve_member(guild, actor_id)
    if actor is None:
        return {
            "skipped": True,
            "reason": f"actor {actor_id} not in guild cache",
        }
    result = await BindingMutationPipeline().set_binding(
        guild,
        str(config["subsystem"]),
        str(config["binding_name"]),
        BindingKind.CHANNEL,
        int(config["channel_id"]),
        actor,
    )
    return {
        "bound": True,
        "mutation_id": result.mutation_id,
        "target_id": int(config["channel_id"]),
    }


async def _handle_create_channel(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del rule, bot
    if dry_run or guild is None or actor_id is None:
        return {
            "would_create": {
                "subsystem": config["subsystem"],
                "binding_name": config["binding_name"],
                "name": config["name"],
            },
            "dry_run": dry_run,
        }
    from core.runtime.guild_resources import resolve_member
    from services.resource_provisioning import (
        ProvisioningRequest,
        ResourceProvisioningPipeline,
    )

    actor = resolve_member(guild, actor_id)
    if actor is None:
        return {
            "skipped": True,
            "reason": f"actor {actor_id} not in guild cache",
        }
    request = ProvisioningRequest(
        subsystem=str(config["subsystem"]),
        binding_name=str(config["binding_name"]),
        mode="create",
        custom_name=str(config["name"]),
    )
    result = await ResourceProvisioningPipeline().provision(
        guild,
        request,
        actor,
        confirmed=True,
    )
    return {
        "created": True,
        "mutation_id": result.mutation_id,
        "outcome": result.outcome,
    }


async def _handle_notify_owner(
    *,
    rule: dict[str, Any],
    config: dict[str, Any],
    dry_run: bool,
    bot: Any | None,
    guild: discord.Guild | None,
    actor_id: int | None,
) -> dict[str, Any]:
    del rule, bot, actor_id
    template = str(config["template"])
    if dry_run or guild is None or guild.owner is None:
        return {
            "would_dm_owner": True,
            "rendered_length": len(template),
            "dry_run": dry_run,
        }
    try:
        await guild.owner.send(template)
    except Exception as exc:  # noqa: BLE001 — DM may be closed
        return {
            "skipped": True,
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return {"dm_sent_to": guild.owner.id}


_HANDLERS = {
    "send_message": _handle_send_message,
    "assign_role": _handle_assign_role,
    "remove_role": _handle_remove_role,
    "post_readiness_summary": _handle_post_readiness_summary,
    "post_leaderboard_summary": _handle_post_leaderboard_summary,
    "bind_channel": _handle_bind_channel,
    "create_channel": _handle_create_channel,
    "notify_owner": _handle_notify_owner,
}


__all__ = [
    "AutomationRunResult",
    "execute_rule",
]
