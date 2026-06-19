"""Automation diagnostics + management panel.

Renders the snapshot registered as ``automation_scheduler`` in
:mod:`services.diagnostics_service` (scheduler uptime, last tick,
failure counters, poll interval) alongside the per-guild
``automation_rules`` list (id, name, enabled state, trigger / action
kind, next run, failure streak, last error).

Beyond display, the panel lets administrators safely operate on
individual rules:

* **Enable / Disable** — flips ``enabled`` via
  :meth:`services.automation_mutation.AutomationMutationPipeline.set_enabled`.
* **Delete** — drops the rule (cascades to ``automation_runs``) via
  :meth:`services.automation_mutation.AutomationMutationPipeline.delete_rule`.

Every action is fully audited: the pipeline emits the canonical
audit row + event before returning, the same path
``!automation enable/disable/delete`` uses.  This panel is purely an
interactive façade — no DB writes happen here directly.

Pin: the rule select is rebuilt from the live DB on every
**Refresh** so the panel never operates on a stale view.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from views.base import HubView
from views.paginated_select import SelectWindow, attach_windowed_select

logger = logging.getLogger("bot.views.diagnostic.automation_panel")


_TRUNC_FIELD = 1000


def _truncate(text: str, *, limit: int = _TRUNC_FIELD) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def _format_scheduler_lines(snap: dict[str, Any]) -> list[str]:
    running = snap.get("running")
    status = "🟢 running" if running else "🔴 stopped"
    lines = [f"**Status:** {status}"]
    if "poll_interval_seconds" in snap:
        lines.append(f"**Poll interval:** `{snap['poll_interval_seconds']}s`")
    if "failure_threshold" in snap:
        lines.append(f"**Failure threshold:** `{snap['failure_threshold']}`")
    for key in (
        "ticks",
        "rules_evaluated",
        "rules_fired",
        "rules_failed",
        "rules_disabled_for_failure_streak",
        "last_tick_at",
        "last_fire_at",
    ):
        if key in snap:
            lines.append(f"**{key.replace('_', ' ').title()}:** `{snap[key]}`")
    return lines


def _format_rule_line(rule: dict[str, Any]) -> str:
    rid = rule.get("id", "?")
    name = rule.get("name") or "(unnamed)"
    enabled = bool(rule.get("enabled"))
    state = "🟢 on" if enabled else "⚪ off"
    tk = rule.get("trigger_kind") or "?"
    ak = rule.get("action_kind") or "?"
    next_run = rule.get("next_run_at")
    failure_count = rule.get("failure_count") or 0
    last_error = rule.get("last_error") or ""
    next_run_text = str(next_run) if next_run else "—"
    line = (
        f"`#{rid}` **{name}** ({state})  "
        f"trigger=`{tk}` action=`{ak}`  next=`{next_run_text}`  "
        f"fails=`{failure_count}`"
    )
    if last_error:
        line += f"\n  ↳ _last_error:_ `{_truncate(last_error, limit=200)}`"
    return line


async def _fetch_rules(guild_id: int) -> tuple[list[dict[str, Any]], str | None]:
    """Return ``(rules, error)`` for a guild.

    Errors are returned rather than raised so the panel can render a
    degraded embed instead of failing the interaction.
    """
    try:
        from utils.db import automation as _automation_db

        rules = await _automation_db.list_rules_for_guild(guild_id)
        return list(rules), None
    except Exception as exc:  # noqa: BLE001 — defensive boundary
        logger.exception("automation_panel: list_rules failed")
        return [], f"{type(exc).__name__}: {exc}"


def _fetch_scheduler_snapshot() -> tuple[dict[str, Any], str | None]:
    """Pull the registered ``automation_scheduler`` snapshot, defensively."""
    try:
        from services import diagnostics_service

        return dict(diagnostics_service.snapshot("automation_scheduler")), None
    except KeyError:
        return (
            {},
            "scheduler not registered (services.automation_scheduler not started)",
        )
    except Exception as exc:  # noqa: BLE001 — defensive boundary
        logger.exception("automation_panel: snapshot failed")
        return {}, f"{type(exc).__name__}: {exc}"


def _build_panel_embed(
    *,
    guild: discord.Guild | None,
    snapshot: dict[str, Any],
    snapshot_error: str | None,
    rules: list[dict[str, Any]],
    rules_error: str | None,
) -> discord.Embed:
    title = "🤖 Automation panel"
    color = discord.Color.blurple()
    if snapshot_error or rules_error:
        color = discord.Color.orange()

    description_lines: list[str] = []
    if snapshot_error:
        description_lines.append(f"⚠️ Scheduler snapshot: {snapshot_error}")
    if snapshot:
        description_lines.extend(_format_scheduler_lines(snapshot))
    if not description_lines:
        description_lines.append("_No scheduler state._")

    embed = discord.Embed(
        title=title,
        description="\n".join(description_lines),
        color=color,
    )

    if guild is None:
        embed.add_field(
            name="Rules",
            value="_Open this panel from inside a guild to see its rules._",
            inline=False,
        )
        return embed

    if rules_error:
        embed.add_field(
            name="Rules",
            value=f"⚠️ {rules_error}",
            inline=False,
        )
        return embed

    if not rules:
        embed.add_field(
            name="Rules",
            value="_No automation rules in this guild._",
            inline=False,
        )
        return embed

    rule_lines = [_format_rule_line(r) for r in rules[:25]]
    text = "\n".join(rule_lines)
    embed.add_field(
        name=f"Rules ({len(rules)})",
        value=_truncate(text),
        inline=False,
    )
    if len(rules) > 25:
        embed.set_footer(
            text=(
                f"Showing first 25 of {len(rules)} rules — the select "
                "menu is capped at the same limit."
            ),
        )
    return embed


def build_automation_embed_sync(
    *,
    guild: discord.Guild | None,
    snapshot: dict[str, Any],
    snapshot_error: str | None,
    rules: list[dict[str, Any]],
    rules_error: str | None,
) -> discord.Embed:
    """Public synchronous variant for tests that pre-fetch state."""
    return _build_panel_embed(
        guild=guild,
        snapshot=snapshot,
        snapshot_error=snapshot_error,
        rules=rules,
        rules_error=rules_error,
    )


async def build_automation_embed(guild: discord.Guild | None) -> discord.Embed:
    """Top-level builder used by the cog's read-only entry point."""
    snapshot, snap_err = _fetch_scheduler_snapshot()
    if guild is None:
        return _build_panel_embed(
            guild=None,
            snapshot=snapshot,
            snapshot_error=snap_err,
            rules=[],
            rules_error=None,
        )
    rules, rules_err = await _fetch_rules(guild.id)
    return _build_panel_embed(
        guild=guild,
        snapshot=snapshot,
        snapshot_error=snap_err,
        rules=rules,
        rules_error=rules_err,
    )


# ---------------------------------------------------------------------------
# Interactive controls
# ---------------------------------------------------------------------------


def _select_options(rules: list[dict[str, Any]]) -> list[discord.SelectOption]:
    """Build the rule-select options.

    Windowed by the caller (◀/▶ nav) rather than front-truncated, so a guild
    with more than Discord's 25-rule cap keeps every rule selectable (the
    #1040 class).
    """
    options: list[discord.SelectOption] = []
    for rule in rules:
        rid = rule.get("id")
        if rid is None:
            continue
        name = (rule.get("name") or f"rule-{rid}")[:90]
        enabled = bool(rule.get("enabled"))
        state = "on" if enabled else "off"
        description = (
            f"{state} · trigger={rule.get('trigger_kind') or '?'} · "
            f"action={rule.get('action_kind') or '?'}"
        )[:100]
        options.append(
            discord.SelectOption(
                label=f"#{rid} {name}",
                value=str(rid),
                description=description,
            ),
        )
    return options


async def _commit_set_enabled(
    interaction: discord.Interaction,
    *,
    rule_id: int,
    enabled: bool,
) -> tuple[bool, str]:
    """Flip the rule's ``enabled`` bit via the pipeline.  Returns ``(ok, msg)``."""
    from services.automation_mutation import (
        AutomationMutationError,
        AutomationMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        return False, "Action requires a guild context."

    try:
        result = await AutomationMutationPipeline().set_enabled(
            guild_id=guild.id,
            guild_owner_id=guild.owner_id or 0,
            rule_id=rule_id,
            enabled=enabled,
            actor_id=getattr(interaction.user, "id", None),
            actor_type="platform_owner",
        )
    except AutomationMutationError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # noqa: BLE001 — defensive UI boundary
        logger.exception(
            "automation_panel: set_enabled raised for rule_id=%d",
            rule_id,
        )
        return False, f"{type(exc).__name__}: {exc}"

    verb = "enabled" if enabled else "disabled"
    return True, f"Rule `#{result.rule_id}` {verb} (mutation `{result.mutation_id}`)."


async def _commit_delete(
    interaction: discord.Interaction,
    *,
    rule_id: int,
) -> tuple[bool, str]:
    """Delete the rule via the pipeline.  Returns ``(ok, msg)``."""
    from services.automation_mutation import (
        AutomationMutationError,
        AutomationMutationPipeline,
    )

    guild = interaction.guild
    if guild is None:
        return False, "Action requires a guild context."

    try:
        result = await AutomationMutationPipeline().delete_rule(
            guild_id=guild.id,
            guild_owner_id=guild.owner_id or 0,
            rule_id=rule_id,
            actor_id=getattr(interaction.user, "id", None),
            actor_type="platform_owner",
        )
    except AutomationMutationError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # noqa: BLE001 — defensive UI boundary
        logger.exception(
            "automation_panel: delete_rule raised for rule_id=%d",
            rule_id,
        )
        return False, f"{type(exc).__name__}: {exc}"

    return True, f"Rule `#{result.rule_id}` deleted (mutation `{result.mutation_id}`)."


def _attach_rule_select(
    view: AutomationPanelView,
    rules: list[dict[str, Any]],
) -> None:
    """(Re)attach the windowed rule picker to ``view``.

    Detaches any existing rule window first, so ``_rerender`` can swap in a
    fresh option list after a mutation.  The view holds the chosen id as
    ``view.selected_rule_id``; the Enable / Disable / Delete buttons read it.

    The full rule list can exceed Discord's 25-option cap, so the options are
    *windowed* (◀/▶ nav) rather than front-truncated (the #1040 class).
    """
    if view.rule_window is not None:
        view.rule_window.detach()
        view.rule_window = None

    options = _select_options(rules) or [
        discord.SelectOption(
            label="(no rules in this guild)",
            value="0",
            description="Create one via !automation or the wizard's preset picker.",
        ),
    ]

    async def _on_pick(interaction: discord.Interaction, values: list[str]) -> None:
        try:
            view.selected_rule_id = int(values[0]) if values else None
        except (TypeError, ValueError):
            view.selected_rule_id = None
        if not await safe_defer(interaction):
            return
        # No embed change on select — the button row acts on the current
        # selection.  Re-edit with the same embed so Discord keeps the picked
        # highlight.
        await safe_edit(
            interaction,
            embed=view.last_embed
            or _build_panel_embed(
                guild=interaction.guild,
                snapshot={},
                snapshot_error=None,
                rules=[],
                rules_error=None,
            ),
            view=view,
        )

    view.rule_window = attach_windowed_select(
        view,
        options,
        _on_pick,
        placeholder="Pick a rule…",
        select_row=0,
        nav_row=2,
    )


class AutomationPanelView(HubView):
    """Interactive admin panel for automation rule operations."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        rules: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(author)
        self.selected_rule_id: int | None = None
        self.last_embed: discord.Embed | None = None
        self.rule_window: SelectWindow | None = None
        _attach_rule_select(self, rules or [])

    # ------------------------------------------------------------------
    # Row 1 — actions on the selected rule
    # ------------------------------------------------------------------

    @discord.ui.button(
        label="Enable",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def btn_enable(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self._handle_set_enabled(interaction, enabled=True)

    @discord.ui.button(
        label="Disable",
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def btn_disable(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self._handle_set_enabled(interaction, enabled=False)

    @discord.ui.button(
        label="Delete",
        style=discord.ButtonStyle.danger,
        row=1,
    )
    async def btn_delete(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if self.selected_rule_id is None or self.selected_rule_id <= 0:
            await interaction.response.send_message(
                "Pick a rule from the dropdown first.",
                ephemeral=True,
            )
            return
        ok, msg = await _commit_delete(interaction, rule_id=self.selected_rule_id)
        await self._after_action(interaction, ok=ok, message=msg)

    @discord.ui.button(
        label="Refresh",
        style=discord.ButtonStyle.primary,
        row=1,
    )
    async def btn_refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if not await safe_defer(interaction):
            return
        await self._rerender(interaction)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _handle_set_enabled(
        self,
        interaction: discord.Interaction,
        *,
        enabled: bool,
    ) -> None:
        if self.selected_rule_id is None or self.selected_rule_id <= 0:
            await interaction.response.send_message(
                "Pick a rule from the dropdown first.",
                ephemeral=True,
            )
            return
        ok, msg = await _commit_set_enabled(
            interaction,
            rule_id=self.selected_rule_id,
            enabled=enabled,
        )
        await self._after_action(interaction, ok=ok, message=msg)

    async def _after_action(
        self,
        interaction: discord.Interaction,
        *,
        ok: bool,
        message: str,
    ) -> None:
        # Surface the outcome ephemerally so the operator sees a
        # confirmation even when the embed re-renders.
        await interaction.response.send_message(
            ("✅ " if ok else "❌ ") + message,
            ephemeral=True,
        )
        if ok:
            await self._rerender(interaction, use_followup=True)

    async def _rerender(
        self,
        interaction: discord.Interaction,
        *,
        use_followup: bool = False,
    ) -> None:
        guild = interaction.guild
        snapshot, snap_err = _fetch_scheduler_snapshot()
        if guild is None:
            rules: list[dict[str, Any]] = []
            rules_err: str | None = None
        else:
            rules, rules_err = await _fetch_rules(guild.id)
        embed = _build_panel_embed(
            guild=guild,
            snapshot=snapshot,
            snapshot_error=snap_err,
            rules=rules,
            rules_error=rules_err,
        )
        self.last_embed = embed
        # Rebuild the windowed select so it reflects the new rule list.
        _attach_rule_select(self, rules)
        self.selected_rule_id = None

        if use_followup and interaction.followup is not None:
            try:
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,  # type: ignore[union-attr]
                    embed=embed,
                    view=self,
                )
            except Exception:  # noqa: BLE001 — soft-fail
                logger.debug(
                    "automation_panel: followup edit failed",
                    exc_info=True,
                )
            return
        await safe_edit(interaction, embed=embed, view=self)


async def open_panel(
    interaction_or_ctx: Any,
    *,
    sender: Any | None = None,
) -> tuple[discord.Embed, AutomationPanelView]:
    """Build the initial embed + view for the automation panel.

    ``interaction_or_ctx`` may be a :class:`discord.Interaction` or
    :class:`discord.ext.commands.Context`.  Returns the embed and view
    so the caller can choose how to present them (``ctx.send`` for
    prefix commands, ``interaction.response.send_message`` for slash
    commands).
    """
    del sender  # reserved for future use
    guild = getattr(interaction_or_ctx, "guild", None)
    snapshot, snap_err = _fetch_scheduler_snapshot()
    if guild is None:
        rules: list[dict[str, Any]] = []
        rules_err: str | None = None
    else:
        rules, rules_err = await _fetch_rules(guild.id)
    embed = _build_panel_embed(
        guild=guild,
        snapshot=snapshot,
        snapshot_error=snap_err,
        rules=rules,
        rules_error=rules_err,
    )
    author = getattr(interaction_or_ctx, "user", None) or getattr(
        interaction_or_ctx,
        "author",
        None,
    )
    view = AutomationPanelView(author, rules)
    view.last_embed = embed
    return embed, view


__all__ = [
    "AutomationPanelView",
    "build_automation_embed",
    "build_automation_embed_sync",
    "open_panel",
]
