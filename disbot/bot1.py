from __future__ import annotations

import asyncio
import datetime
import logging
import logging.handlers
import os
import signal
import time
import uuid

import discord
from discord.ext import commands

import config
from core.runtime import lifecycle as _lifecycle
from services import runtime as _runtime
from services.runtime import BOOT_ID, install_boot_id_logging
from services.webhook_reporter import WebhookReporter
from utils import command_resolution, db
from utils.synonyms import COMMAND_SYNONYMS

# ---------------------------------------------------------------------------
# Logging — structured JSON when python-json-logger is available,
# falling back to plain text so the bot boots in minimal environments.
# Every record carries ``boot_id`` via :class:`services.runtime.BootIdFilter`
# so multi-replica deploys are debuggable.
# ---------------------------------------------------------------------------
try:
    from pythonjsonlogger import jsonlogger as _jsonlogger

    _fmt: logging.Formatter = _jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(boot_id)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
except ImportError:  # python-json-logger not installed — use stdlib formatter
    _fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | boot=%(boot_id)s | %(message)s",
    )
_root = logging.getLogger()
_log_level = getattr(logging, config.LOG_LEVEL, logging.INFO)
if not isinstance(_log_level, int):
    _log_level = logging.INFO
_root.setLevel(_log_level)

_handlers: list[logging.Handler] = [
    logging.handlers.RotatingFileHandler(
        "bot.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    ),
    logging.StreamHandler(),
]
install_boot_id_logging(_handlers)
for _h in _handlers:
    _h.setFormatter(_fmt)
    _root.addHandler(_h)

logger = logging.getLogger("bot")

# ---------------------------------------------------------------------------
# Webhook reporter
# ---------------------------------------------------------------------------
reporter: WebhookReporter | None = (
    WebhookReporter(config.WEBHOOK_URL) if config.WEBHOOK_URL else None
)
if not config.WEBHOOK_URL:
    logger.warning("DISCORD_WEBHOOK_URL not set — webhook logging disabled.")

logger.info("Boot identity: boot_id=%s", BOOT_ID)

# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class _SuperBot(commands.Bot):
    """``commands.Bot`` + the deploy-declared extra owner accounts (Q-0245).

    ``is_owner`` is the seam every ``_is_bot_owner_from_ctx``-style operator
    bypass rides (core.runtime.command_access). Short-circuiting through
    ``config.is_platform_owner`` keeps the "who is the bot owner?" rule in
    exactly one place — the owner's declared test account (EXTRA_OWNER_USER_IDS)
    then clears both owner seams identically, while discord.py's normal
    application-owner lookup stays the fallback.
    """

    async def is_owner(self, user: discord.abc.User) -> bool:
        if user is not None and config.is_platform_owner(getattr(user, "id", None)):
            return True
        return await super().is_owner(user)


bot = _SuperBot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,
    # Widen discord.py's in-memory message cache from the 1000 default so
    # server-logging's message-delete/edit embeds carry content for a longer
    # window; deletes older than the cache fall to the raw-event path, which
    # logs the event with content marked unavailable (services.server_logging).
    max_messages=5000,
    # Resolve case variants (``!Help``, ``!BAN``) at the source.  Lowercasing
    # can never change *which* command is meant — there are no two commands
    # differing only by case — so this is always safe and frees the typo
    # resolver (utils.command_resolution) to handle genuine misspellings only.
    case_insensitive=True,
)


def _begin_shutdown(*_) -> None:
    """SIGTERM handler: route through the lifecycle service so command
    admission (``_channel_guard``) and any future observers see one
    canonical "draining" signal instead of a module-local bool (LP-2).
    """
    _lifecycle.request_shutdown(reason="sigterm")


# ---------------------------------------------------------------------------
# Supervised app-task helper — Phase S2.4 / C-2 (PR-02c, final form)
#
# PR-02c removes the historical ``_APP_TASKS`` mirror and the
# ``_supervised_task`` compatibility wrapper.  Callers now use
# ``core.runtime.tasks.spawn`` directly with the
# ``_on_app_task_died_webhook`` on_error hook, which is the canonical
# entry-point for app-owned background tasks.  The canonical task
# supervisor (``core.runtime.tasks``) handles strong refs, metrics,
# the cancellation/clean-exit filter, and ERROR-level logging; this
# module's hook layers the CRITICAL log + webhook follow-up on top.
# ---------------------------------------------------------------------------

from core.runtime import tasks as _runtime_tasks  # noqa: E402


def _on_app_task_died_webhook(
    task: asyncio.Task,
    exc: BaseException,
) -> None:
    """``tasks.spawn`` on_error hook: CRITICAL log + webhook follow-up.

    Invoked by ``core.runtime.tasks._on_done`` only for tasks that
    raised a non-cancellation exception (cancellations and clean exits
    are filtered there).  The webhook follow-up is itself scheduled
    through ``tasks.spawn`` so it inherits managed-task lifecycle —
    no bare ``asyncio.create_task`` callsites in this module other
    than the one-shot health-bind coordination at the
    ``asyncio.wait`` callsite below.
    """
    logger.critical(
        "App task %r died: %s",
        task.get_name(),
        exc,
        exc_info=exc,
    )
    if reporter is None:
        return
    try:
        _runtime_tasks.spawn(
            f"on_app_task_died:{task.get_name()}",
            reporter.on_app_task_died(task.get_name(), exc),
        )
    except RuntimeError:
        # No running loop (e.g., during shutdown) — log only.
        logger.debug("Could not schedule app-task webhook (no loop).")


def _identity_contract_strict() -> bool:
    """Return True if STRICT identity-contract enforcement is active.

    Phase S5.1: STRICT is now the **default**.  When True and the
    startup validator reports any fatal-tier identity-contract
    finding, the orchestrator emits the webhook alert and raises
    ``SystemExit(1)`` so the bot refuses to start on drift.  When
    False (explicit opt-out), findings are advisory: they surface in
    logs, the ``identity_contract_findings_total`` metric, and
    ``!platform identity``, but startup continues.

    Two opt-out paths:

      1. ``STRICT_DISABLED=1/true/yes/on`` — the canonical escape
         hatch introduced in S5.1.  Use this in an emergency when a
         fatal-tier finding is blocking a deploy and you need to ship
         a fix without first un-jamming the abort.  Remove ASAP.
      2. ``IDENTITY_CONTRACT_STRICT=false/0/no/off`` — the legacy
         pre-S5.1 opt-out, honored for operators who explicitly set
         their env config to advisory mode.  An unset or truthy value
         here falls through to the new default.

    See ``docs/runtime_contracts.md`` §12 for the runbook.
    """
    disabled = os.getenv("STRICT_DISABLED", "").strip().lower()
    if disabled in ("1", "true", "yes", "on"):
        return False
    legacy = os.getenv("IDENTITY_CONTRACT_STRICT", "").strip().lower()
    return legacy not in ("0", "false", "no", "off")


signal.signal(signal.SIGTERM, _begin_shutdown)

# ---------------------------------------------------------------------------
# Bot events
# ---------------------------------------------------------------------------


# Bot-awareness PR3: one-shot guard so the post-ready startup-health snapshot
# is reported exactly once per process — a gateway reconnect re-fires on_ready
# and must not re-report. Mirrors lifecycle._startup_duration_observed.
_startup_health_reported = False

# One-shot guard so the diff-gated command-tree auto-sync
# (services.command_tree_sync) runs exactly once per process — a gateway
# reconnect re-fires on_ready and must not re-sync.
_commands_auto_synced = False


async def _report_startup_health() -> None:
    """Collect + cache the settled-startup health snapshot (best-effort).

    Runs off the on_ready path via the managed task supervisor (INV-K) so it
    never blocks readiness; every failure is isolated and swallowed so a
    health-reporting hiccup can never affect the running bot. Panel-only —
    the snapshot is cached for ``!platform startup`` and logged at INFO, with
    no webhook/admin-channel push.
    """
    try:
        from services import health_snapshot_service
        from services.health_contracts import HealthAudience, HealthSnapshotRequest

        snapshot = await health_snapshot_service.collect_snapshot(
            HealthSnapshotRequest(
                purpose="startup",
                audience=HealthAudience.PLATFORM_OWNER,
                # Collect a *fresh* consistency report rather than the
                # process-local cache, which is guaranteed empty this early
                # (collect_report only runs from !platform consistency / the
                # platform panel, never at boot). Reading the empty cache made
                # the consistency subsystem UNKNOWN-and-required, which dragged
                # the whole startup snapshot to "degraded" with no attention
                # list on every boot — a false alarm. Bounded by
                # CONSISTENCY_TIMEOUT and off the readiness path, so it cannot
                # block startup; it also primes the cache for later sync reads.
                include_fresh_consistency=True,
            ),
            bot=bot,
        )
        health_snapshot_service.record_startup_snapshot(snapshot)
        logger.info(
            "Startup health: %s — %s",
            snapshot.status.value,
            snapshot.summary,
        )
        # When not healthy, name the actual findings in the log so the
        # degradation is diagnosable from logs alone — without the DB or the
        # `!platform consistency` Discord command. The aggregate summary only
        # names which *subsystems* need attention; this prints the per-finding
        # severity + subsystem + message (already bounded + secret-scrubbed at
        # adapter time), so a log-only operator can see exactly what fired.
        if snapshot.status.value != "healthy" and snapshot.findings:
            for finding in snapshot.findings:
                logger.info(
                    "Startup health finding: [%s] %s — %s",
                    finding.severity.value,
                    finding.related_subsystem or "?",
                    finding.message,
                )
        # Bot-awareness PR6: persist this snapshot's findings (best-effort, off
        # the readiness path) so recurrence survives restarts, then run the
        # 30-day retention sweep. Both calls are internally best-effort; the
        # extra guard covers the function-local imports themselves.
        try:
            from services import health_findings_service
            from services.runtime import BOOT_ID

            recorded = await health_findings_service.record_findings(
                snapshot,
                session_id=str(BOOT_ID),
            )
            pruned = await health_findings_service.run_retention()
            logger.info(
                "Startup health findings: recorded=%d pruned=%d",
                recorded,
                pruned,
            )
        except Exception:
            logger.warning("startup health findings persistence failed", exc_info=True)
    except Exception:
        logger.warning("startup health snapshot failed", exc_info=True)


def _maybe_report_startup_health() -> None:
    """Spawn the startup-health report once per process (reconnect-safe).

    Extracted from ``on_ready`` so the one-shot guard is unit-testable
    without booting: a gateway reconnect re-fires ``on_ready`` and must not
    re-spawn the report.
    """
    global _startup_health_reported
    if _startup_health_reported:
        return
    _startup_health_reported = True
    _runtime_tasks.spawn("startup:health_report", _report_startup_health())


def _maybe_auto_sync_commands() -> None:
    """Spawn the diff-gated command-tree auto-sync once per process.

    Reconnect-safe (a gateway reconnect re-fires ``on_ready``). Runs off the
    on_ready path via the task supervisor and is fully non-fatal — see
    ``services.command_tree_sync``. Kill-switch: ``AUTO_SYNC_COMMANDS=0``.
    """
    global _commands_auto_synced
    if _commands_auto_synced:
        return
    _commands_auto_synced = True
    from services import command_tree_sync

    _runtime_tasks.spawn(
        "startup:command_sync",
        command_tree_sync.auto_sync_if_changed(
            bot,
            enabled=command_tree_sync.env_enabled(config.AUTO_SYNC_COMMANDS),
        ),
    )


@bot.event
async def on_ready() -> None:
    bot.uptime = datetime.datetime.now(tz=datetime.timezone.utc)  # type: ignore[attr-defined]
    bot._reporter = reporter  # type: ignore[attr-defined]
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d server(s)", len(bot.guilds))
    logger.info("Loaded cogs: %s", ", ".join(bot.cogs.keys()))
    from core.runtime import live_update_scheduler, message_anchor_manager

    await message_anchor_manager.restore_anchors(bot)
    # Re-bind a persistent view to every posted role menu (data-driven, keyed on
    # the role_menus rows rather than per-user anchors) so self-role clicks
    # survive a restart. Idempotent — guarded against on_ready re-fires.
    from views.roles.role_menu_view import reattach_role_menus

    await reattach_role_menus(bot)
    live_update_scheduler.setup(bot)
    if reporter:
        await reporter.on_startup(bot)
    # LP-2: surface "ready to serve" as a lifecycle phase. Only transition
    # when no shutdown was requested mid-startup; otherwise stay in DRAINING.
    if _lifecycle.get_phase() is _lifecycle.Phase.STARTING:
        _lifecycle.set_phase(_lifecycle.Phase.RUNNING, reason="on_ready")
    # Bot-awareness PR3: post-ready startup-health snapshot, exactly once.
    _maybe_report_startup_health()
    # Diff-gated command-tree auto-sync — push a changed slash tree to Discord on
    # deploy (no manual !syncslash), exactly once per process. Non-fatal.
    _maybe_auto_sync_commands()


@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    from guild_lifecycle import teardown

    await teardown(guild.id)


@bot.event
async def on_interaction(interaction: discord.Interaction) -> None:
    from core.runtime import interaction_router

    await interaction_router.dispatch(interaction)


@bot.event
async def on_command(ctx: commands.Context) -> None:
    ctx._request_id = str(uuid.uuid4())  # type: ignore[attr-defined]
    # Phase S3.1: stamp start time so on_command_completion can observe
    # end-to-end command latency.
    ctx._cmd_start = time.monotonic()  # type: ignore[attr-defined]
    cog_name = type(ctx.cog).__name__ if ctx.cog else "unknown"
    logger.info(
        "CMD %s/%s",
        cog_name,
        ctx.command.qualified_name if ctx.command else "?",
        extra={
            "request_id": ctx._request_id,  # type: ignore[attr-defined]
            "guild_id": ctx.guild.id if ctx.guild else None,
            "user_id": ctx.author.id,
            "channel_id": ctx.channel.id,
        },
    )
    if reporter:
        await reporter.on_command(ctx)


@bot.event
async def on_command_completion(ctx: commands.Context) -> None:
    from services import metrics as _metrics

    cog_name = type(ctx.cog).__name__ if ctx.cog else "unknown"
    cmd_name = ctx.command.qualified_name if ctx.command else "unknown"
    _metrics.command_total.labels(
        cog=cog_name,
        command=cmd_name,
        result="success",
    ).inc()
    # Phase S3.1: observe end-to-end command latency.  If on_command did
    # not run (e.g. bot.event was not invoked in test fixtures), fall back
    # to a zero-duration observation to keep the metric well-defined.
    started_at = getattr(ctx, "_cmd_start", None)
    if started_at is not None:
        elapsed = time.monotonic() - started_at
        _metrics.command_latency_seconds.labels(
            cog=cog_name,
            command=cmd_name,
        ).observe(elapsed)
        # Phase S3.2: record into the slow-path ring buffer if over threshold.
        from core.runtime import slow_path_log

        slow_path_log.maybe_record("command", f"{cog_name}.{cmd_name}", elapsed * 1000)
    logger.info(
        "CMD ✅ %s/%s",
        cog_name,
        cmd_name,
        extra={
            "request_id": getattr(ctx, "_request_id", None),
            "guild_id": ctx.guild.id if ctx.guild else None,
        },
    )
    if reporter:
        await reporter.on_command_success(ctx)
    await _maybe_cleanup_successful_command(ctx)


async def _maybe_cleanup_successful_command(ctx: commands.Context) -> None:
    if ctx.guild is None or ctx.author.bot or not getattr(ctx, "message", None):
        return
    from services import governance_service

    try:
        gctx = governance_service.GovernanceContext.from_ctx(ctx)
        policy = await governance_service.resolve_cleanup_policy(gctx)
        if not policy.delete_message:
            return
        await ctx.message.delete(delay=policy.delete_after_seconds)
    except discord.NotFound:
        return
    except discord.Forbidden:
        logger.warning(
            "Cleanup failed for successful command in guild=%s channel=%s: missing Manage Messages",
            ctx.guild.id if ctx.guild else None,
            ctx.channel.id if ctx.channel else None,
        )
    except discord.HTTPException as exc:
        logger.warning("Cleanup failed for successful command: %s", exc)


# ---------------------------------------------------------------------------
# Fuzzy command resolution support.
#
# We build a ``token -> canonical command name`` map from the LIVE command
# surface (primary names + aliases) plus the hand-maintained synonym table,
# then derive the auto-correct allowlist once.  The cache is keyed on the
# command-surface size so it rebuilds transparently if cogs (un)load.
# ---------------------------------------------------------------------------
_resolution_cache: tuple[int, dict[str, str], frozenset[str]] | None = None


def _build_token_map() -> dict[str, str]:
    """Map every known token (name, alias, synonym) to its canonical command.

    Primary command names win over aliases/synonyms on collision so a real
    command is never shadowed by another command's alias.
    """
    token_map: dict[str, str] = {}
    # Synonyms first (lowest precedence)...
    for canonical, synonyms in COMMAND_SYNONYMS.items():
        for syn in synonyms:
            token_map.setdefault(syn.lower(), canonical)
    # ...then aliases...
    for cmd in bot.commands:
        for alias in getattr(cmd, "aliases", ()) or ():
            token_map[alias.lower()] = cmd.name
    # ...then primary names (highest precedence).
    for cmd in bot.commands:
        token_map[cmd.name.lower()] = cmd.name
    return token_map


def _resolution_inputs() -> tuple[dict[str, str], frozenset[str]]:
    global _resolution_cache
    surface_size = len(bot.all_commands)
    if _resolution_cache is None or _resolution_cache[0] != surface_size:
        token_map = _build_token_map()
        auto_set = command_resolution.derive_auto_correct_set(token_map)
        _resolution_cache = (surface_size, token_map, auto_set)
    return _resolution_cache[1], _resolution_cache[2]


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    from services import metrics as _metrics

    cog_name = type(ctx.cog).__name__ if ctx.cog else "unknown"
    cmd_name = ctx.command.qualified_name if ctx.command else "unknown"
    result = "denied" if isinstance(error, commands.CheckFailure) else "error"
    _metrics.command_total.labels(cog=cog_name, command=cmd_name, result=result).inc()
    if reporter:
        await reporter.on_command_error(ctx, error)

    if isinstance(error, commands.CheckFailure):
        # Check failures (channel-access denial, governance subsystem
        # denial) produce their own user-facing message at the layer
        # that raised them.  Stay silent here so the operator does
        # not see a duplicate / generic "unexpected error" reply on
        # top of the specific denial feedback.
        return

    # Log ALL non-check errors regardless of channel so bugs are never invisible.
    if not isinstance(
        error,
        (
            commands.MissingPermissions,
            commands.BotMissingPermissions,
            commands.CommandNotFound,
            commands.MissingRequiredArgument,
            commands.BadArgument,
            commands.CommandOnCooldown,
        ),
    ):
        logger.error(
            "CMD ❌ | %s | %s | %s | %s: %s",
            ctx.command,
            ctx.author,
            ctx.guild,
            type(error).__name__,
            error,
            exc_info=True,
        )

    # PR-4: user-facing replies are surfaced in every channel.  The
    # legacy ``in_allowed = ctx.channel.id in ALLOWED_CHANNELS`` gate
    # that suppressed replies outside hardcoded channel IDs was the
    # root cause of the "command vanished" UX — operators in fresh
    # guilds saw nothing when a command failed.  Channel-access denial
    # now comes from the resolver layer with its own feedback, so the
    # error handler is free to surface every other failure mode.

    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You do not have permission to use this command.",
            delete_after=10,
        )
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(
            f"❌ I'm missing permissions to do that: `{error.missing_permissions}`",
            delete_after=10,
        )
    elif isinstance(error, commands.CommandNotFound):
        raw = ctx.invoked_with or ""
        token_map, auto_set = _resolution_inputs()
        resolution = command_resolution.classify(raw, token_map, auto_set)
        prefix = ctx.prefix or config.PREFIX

        # Loop-breaker (BUG-0014): an AUTO correction is only safe to
        # re-dispatch when it points at a *registered* command that *differs*
        # from what the user typed. Re-dispatching a correction that is
        # unregistered (e.g. a stale synonym whose canonical has no command)
        # or identical to the raw token just re-enters CommandNotFound →
        # re-resolves to the same phantom → an infinite "assumed from" spam
        # loop that only stops on restart. An unsafe AUTO correction falls
        # through to the generic not-found reply instead of re-dispatching.
        auto_safe = (
            resolution.outcome is command_resolution.Outcome.AUTO
            and resolution.command is not None
            and resolution.command.lower() != raw.lower()
            and bot.get_command(resolution.command) is not None
        )
        if auto_safe:
            # Rewrite the mistyped token and re-dispatch through the full
            # command pipeline (process_commands), so permission checks and
            # cooldowns still run — never ctx.invoke, which would bypass them.
            corrected = resolution.command
            rest = ctx.message.content[len(prefix) + len(raw) :]
            ctx.message.content = f"{prefix}{corrected}{rest}"
            await ctx.send(
                f"↩️ Ran `{prefix}{corrected}` — assumed from `{prefix}{raw}`.",
                delete_after=8,
            )
            await bot.process_commands(ctx.message)
        elif (
            resolution.outcome is command_resolution.Outcome.SUGGEST
            and resolution.command
        ):
            await ctx.send(
                f"❓ Unknown command `{raw}`. "
                f"Did you mean `{prefix}{resolution.command}`?",
                delete_after=15,
            )
        else:
            await ctx.send(
                "❌ Command not found. Use `!help` for available commands.",
                delete_after=10,
            )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(
            f"⚠️ Missing argument: `{error.param.name}`. Use `!help {ctx.command}` for usage.",
            delete_after=10,
        )
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Bad argument: {error}", delete_after=10)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏰ This command is on cooldown. Try again in **{error.retry_after:.1f}s**.",
            delete_after=8,
        )
    else:
        await ctx.send(
            "⚠️ An unexpected error occurred. Please try again.",
            delete_after=10,
        )


# ---------------------------------------------------------------------------
# Global command-access guard
# ---------------------------------------------------------------------------
# The prefix admission gate lives in
# ``disbot/cogs/bootstrap_access_cog.py``.  That cog is intentionally
# loaded first (``config.INITIAL_EXTENSIONS[0]``) so the gate is
# installed before any other cog registers a command.  Pre-PR-4 a
# legacy ``@bot.check _channel_guard`` defined here was the default
# gate that the cog then displaced at boot; deleting the legacy
# definition leaves the cog as the single, canonical owner of the
# admission gate and removes the dead-code branch that confused
# readers ("is this the live check or the displaced one?").
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Governance enforcement guard (Phase 1.3 — ARCH-001 fix)
#
# Runs AFTER _channel_guard passes, BEFORE the cog handler is invoked.
# Every command that reaches this hook has already passed the channel whitelist
# check.  We resolve the subsystem for the command and gate on visibility.
#
# This converts governance from advisory (help-menu-only) to infrastructure:
# disabling a subsystem now blocks its commands, not just hides them.
# ---------------------------------------------------------------------------


@bot.before_invoke
async def _governance_guard(ctx: commands.Context) -> None:
    """Enforce subsystem visibility before every command invocation.

    Raises commands.CheckFailure (caught by on_command_error) when the
    command's owning subsystem is disabled for the invoking member.
    The !force admin override and unknown commands are exempted.
    """
    if ctx.command is None:
        return
    # !force is an explicit admin channel-restriction bypass — leave it alone.
    if ctx.command.name == "force":
        return
    # DM contexts have no guild governance.
    if ctx.guild is None:
        return

    from governance import GovernanceContext, resolve_command_policy

    gov_ctx = GovernanceContext.from_ctx(ctx)
    policy = await resolve_command_policy(gov_ctx, ctx.command.qualified_name)
    if policy.allowed:
        return

    # Send user-facing feedback before raising so the message arrives.
    if policy.feedback:
        try:
            await ctx.send(
                policy.feedback,
                delete_after=policy.cleanup.delete_after_seconds or 10,
            )
        except Exception:
            pass
    if policy.cleanup.delete_message and ctx.message:
        try:
            await ctx.message.delete(delay=policy.cleanup.delete_after_seconds or 5)
        except Exception:
            pass

    raise commands.CheckFailure(
        f"Subsystem disabled for command {ctx.command.qualified_name!r}",
    )


# ---------------------------------------------------------------------------
# !force — admin override
# ---------------------------------------------------------------------------


@bot.command()  # type: ignore[arg-type]
@commands.has_permissions(administrator=True)
async def force(ctx: commands.Context, command_name: str, *args) -> None:
    """Overrides channel restrictions and runs a command (admins only)."""
    cmd = bot.get_command(command_name)
    if cmd:
        await ctx.invoke(cmd, *args)
    else:
        await ctx.send("❌ Command not found.", delete_after=10)


# ---------------------------------------------------------------------------
# Load cogs
# ---------------------------------------------------------------------------


async def _load_cogs() -> None:
    from core.runtime import startup_outcome
    from services import governance_service
    from utils.subsystem_registry import SUBSYSTEMS

    failed_exts: set[str] = set()
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            startup_outcome.record_extension_success(ext)
            logger.info("✅ Loaded %s", ext)
        except Exception as exc:
            startup_outcome.record_extension_failure(ext, exc)
            failed_exts.add(ext)
            logger.error(
                "❌ Failed to load %s: %s: %s",
                ext,
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            if reporter:
                await reporter.on_cog_fail(ext, exc)

    if failed_exts:
        loaded_command_names = {cmd.name for cmd in bot.commands}
        failed_subsystems: set[str] = set()
        for name, meta in SUBSYSTEMS.items():
            entry_points = meta.get("entry_points", [])
            if entry_points and not any(
                ep in loaded_command_names for ep in entry_points
            ):
                failed_subsystems.add(name)
                logger.warning(
                    "Subsystem %r has no loaded commands — marking INTERNAL",
                    name,
                )
        if failed_subsystems:
            governance_service.register_failed_subsystems(failed_subsystems)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Process memory sampler — Phase S3.3 / O-4
# ---------------------------------------------------------------------------

PROCESS_MEMORY_SAMPLE_INTERVAL: int = 60  # seconds between RSS samples


async def _sample_process_memory() -> None:
    """Update the ``process_memory_rss_bytes`` gauge every interval.

    Runs forever until cancelled at shutdown.  Spawned via
    ``core.runtime.tasks.spawn`` with the
    ``_on_app_task_died_webhook`` on_error hook by main(), so a
    psutil failure surfaces as a CRITICAL log + webhook alert rather
    than vanishing silently.
    """
    import psutil

    from services import metrics as _metrics

    process = psutil.Process()
    while True:
        try:
            rss = process.memory_info().rss
            _metrics.process_memory_rss_bytes.set(rss)
        except Exception as exc:
            # Don't let one psutil hiccup take the supervised task down —
            # log + keep sampling.  Persistent failure means RSS metric
            # goes stale (visible in Grafana) before the next escalation.
            logger.warning("process_memory_rss sampler skipped tick: %s", exc)
        await asyncio.sleep(PROCESS_MEMORY_SAMPLE_INTERVAL)


# ---------------------------------------------------------------------------
# Lifecycle close-driver
# ---------------------------------------------------------------------------

LIFECYCLE_CLOSE_TIMEOUT_SECONDS: float = 20.0
_LIFECYCLE_CLOSE_POLL_INTERVAL: float = 0.5
_LIFECYCLE_CLOSE_WEBHOOK_TIMEOUT_SECONDS: float = 2.0

# Signals the runtime-lock heartbeat loop to stop. Module-level (not a
# main() local) so the close-driver can set it the instant shutdown
# begins — the heartbeat loop then treats a now-missing lock row as an
# intentional shutdown release rather than a hostile peer-reclaim.
# main() passes this same event to run_heartbeat_loop and re-sets it in
# its finally block (idempotent).
_heartbeat_stop: asyncio.Event = asyncio.Event()


def _should_drive_lifecycle_close() -> bool:
    """Single eligibility predicate for the close-driver.

    True iff a lifecycle request is pending AND the lifecycle module
    has already moved the phase into DRAINING.  Both
    ``request_shutdown`` and ``request_restart`` perform that
    STARTING/RUNNING → DRAINING transition themselves, so polling on
    this predicate covers shutdown and restart with one code path.
    """
    pending = _lifecycle.get_pending()
    phase = _lifecycle.get_phase()
    return pending is not None and phase is _lifecycle.Phase.DRAINING


async def _drive_close_on_lifecycle_request() -> None:
    """Turn any pending lifecycle request into ``bot.close()``.

    SIGTERM (``request_shutdown``) and ``!restart``
    (``request_restart``) both record intent via
    :mod:`core.runtime.lifecycle`; neither touches process control
    directly.  This watchdog is the single executor for both: it polls
    the lifecycle state, and when a request is pending and the phase
    has reached DRAINING, fires a best-effort close-beginning webhook
    and then awaits ``bot.close()`` with a bounded timeout.  ``main()``
    then unwinds through its existing finally block (heartbeat stop →
    task drain → runtime-lock release → DB close → reporter close →
    terminal phase) and the process exits cleanly.

    The driver does **not** distinguish shutdown vs restart — the
    finalizer makes that distinction via
    :func:`core.runtime.lifecycle.restart_requested` when choosing the
    terminal phase.  It also does not own any cleanup itself; that
    separation is what lets shutdown and restart share one code path
    without duplicating cleanup responsibility.

    On close-timeout the process is force-exited via ``os._exit(1)``
    so the orchestration platform respawns rather than leaving the
    runtime lock wedged until its 90 s TTL.
    """
    while True:
        try:
            await asyncio.sleep(_LIFECYCLE_CLOSE_POLL_INTERVAL)
        except asyncio.CancelledError:
            return
        if not _should_drive_lifecycle_close():
            continue
        pending = _lifecycle.get_pending()
        kind = pending.kind if pending else "<unknown>"
        actor = pending.actor if pending and pending.actor else "<unknown>"
        reason = pending.reason if pending else "<unknown>"
        logger.info(
            "Lifecycle %s requested by %s (reason=%r); closing bot (timeout %.1fs).",
            kind,
            actor,
            reason,
            LIFECYCLE_CLOSE_TIMEOUT_SECONDS,
        )
        # LP-4 fast deploy handoff: drop the runtime lock NOW — before the
        # slow bot.close() drain, the close-beginning webhook, and any
        # force-exit branch below — so the next replica reclaims within its
        # acquire-poll instead of waiting the ~90s stale TTL when the
        # platform SIGKILLs us mid-drain (the ~85s production downtime this
        # fixes). The release is idempotent + boot-scoped
        # (utils.db.runtime_lock.release), so main()'s finally re-runs it as
        # the canonical no-op net. Stop the heartbeat FIRST so its next tick
        # treats the now-missing row as this intentional shutdown release,
        # not a hostile peer-reclaim → os._exit. The lock is special among
        # teardown steps — it is the next-replica handoff signal, not local
        # cleanup like db/reporter close — so it (and only it) is dropped
        # here; everything else stays owned by main()'s finally.
        _heartbeat_stop.set()
        await _runtime.release_lock_best_effort()
        if reporter is not None and pending is not None:
            try:
                await asyncio.wait_for(
                    reporter.on_lifecycle_close_beginning(pending),
                    timeout=_LIFECYCLE_CLOSE_WEBHOOK_TIMEOUT_SECONDS,
                )
            except Exception as report_err:
                logger.debug(
                    "Lifecycle close-beginning webhook skipped: %s",
                    report_err,
                )
        from services import metrics as _metrics

        if pending is not None:
            _lifecycle.record_close_executing(pending)
            _metrics.lifecycle_close_driver_total.labels(kind=pending.kind).inc()
        kind_label = pending.kind if pending is not None else "unknown"
        close_started_at = time.monotonic()
        try:
            await asyncio.wait_for(
                bot.close(),
                timeout=LIFECYCLE_CLOSE_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            # Observe the timeout value so a single observation in the
            # topmost bucket is the canonical "force-exit" signature in
            # Prometheus.  Done before os._exit so the next scrape (if
            # it lands in the millisecond window before exit) sees it.
            _metrics.lifecycle_close_duration_seconds.labels(
                kind=kind_label,
            ).observe(LIFECYCLE_CLOSE_TIMEOUT_SECONDS)
            if pending is not None:
                _lifecycle.record_close_timeout(
                    pending,
                    timeout_seconds=LIFECYCLE_CLOSE_TIMEOUT_SECONDS,
                )
            if reporter is not None and pending is not None:
                try:
                    await asyncio.wait_for(
                        reporter.on_lifecycle_close_timeout(
                            pending,
                            timeout_seconds=LIFECYCLE_CLOSE_TIMEOUT_SECONDS,
                        ),
                        timeout=1.0,
                    )
                except Exception as report_err:
                    logger.debug(
                        "Lifecycle close-timeout webhook skipped: %s",
                        report_err,
                    )
            logger.critical(
                "bot.close() exceeded %.1fs timeout — force-exiting "
                "so the orchestration platform respawns.",
                LIFECYCLE_CLOSE_TIMEOUT_SECONDS,
            )
            os._exit(1)
        close_duration = time.monotonic() - close_started_at
        _metrics.lifecycle_close_duration_seconds.labels(
            kind=kind_label,
        ).observe(close_duration)
        if pending is not None:
            _lifecycle.record_close_completed(
                pending,
                duration_seconds=close_duration,
            )
        return


async def main() -> None:
    from services.governance_exceptions import GovernanceError
    from utils.subsystem_registry import validate_registry

    try:
        validate_registry()
        logger.info("Registry validated and frozen.")
    except GovernanceError as exc:
        logger.critical("Registry validation failed — aborting startup: %s", exc)
        raise SystemExit(1) from exc

    await db.init()

    # Acquire the runtime instance lock now that migrations (including
    # 034_bot_runtime_lock) have run. If another replica holds the lock
    # this raises ``SystemExit(0)`` — Railway treats that as a graceful
    # exit and does not crash-loop the loser. ``_runtime`` and
    # ``_heartbeat_stop`` are module-level so the close-driver can release
    # the lock + stop the heartbeat early (LP-4 fast handoff).
    await _runtime.acquire_lock_or_exit()

    from core import runtime
    from core.runtime import message_pipeline

    await runtime.setup()
    message_pipeline.setup(bot)
    # Phase 2 PR-11 — Server logging foundation.  Subscribes to
    # ``moderation.action_taken`` and posts structured embeds to the
    # configured per-guild log channel.  Default policy is OFF; the
    # service is inert until an operator opts in via
    # ``!logging enable`` / ``!logging set mod #channel``.
    from services import server_logging

    server_logging.setup(bot)
    if reporter:
        await reporter.start()
    try:
        async with bot:
            from core.runtime import session_gc
            from healthserver import start_health_server

            # PR-02c: app-owned tasks go directly through
            # ``core.runtime.tasks.spawn`` with the webhook-alert
            # ``on_error`` hook.  The supervisor's module-level
            # ``_TASKS`` set is the single owner; shutdown drain
            # iterates it via ``cancel_all()``.  Health server is
            # gated on bind-ready (Phase S2.4 / O-2b): if the bind
            # fails, the bot aborts startup instead of silently
            # running with a wedged orchestration probe.  Heartbeat
            # the runtime lock every 30 s so a healthy replica
            # retains ownership and a stale row is auto-reclaimed by
            # the next boot after the 90 s TTL.
            _runtime_tasks.spawn(
                "runtime_lock_heartbeat",
                _runtime.run_heartbeat_loop(_heartbeat_stop),
                on_error=_on_app_task_died_webhook,
            )

            health_ready = asyncio.Event()
            health_task = _runtime_tasks.spawn(
                "health_server",
                start_health_server(bot, ready_event=health_ready),
                on_error=_on_app_task_died_webhook,
            )

            # Wait for either the bind to succeed (ready_event set) or
            # the supervised task to die.  5 s is generous — bind is a
            # local syscall that completes in < 100 ms in the healthy
            # case.  Whichever signal fires first wins.
            done, _pending = await asyncio.wait(
                {
                    asyncio.create_task(health_ready.wait()),
                    health_task,
                },
                timeout=5.0,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if health_task in done and health_task.exception() is not None:
                bind_err = health_task.exception()
                logger.critical(
                    "Health server bind failed — aborting startup: %s",
                    bind_err,
                    exc_info=bind_err,
                )
                if reporter:
                    try:
                        await reporter.on_health_startup_failed(bind_err)
                    except Exception as report_err:
                        logger.debug(
                            "Health webhook post skipped: %s",
                            report_err,
                        )
                raise SystemExit(1)
            if not health_ready.is_set():
                logger.warning(
                    "Health server did not signal bind-ready within 5s; "
                    "continuing — probe traffic may be slow at first.",
                )

            # RC-7: register feature cleanup providers before the GC loop
            # starts.  session_gc only schedules; feature services own the
            # refund semantics (ADR-002).  bot1 is the composition root, so the
            # core→services wiring lives here rather than inside session_gc.
            from services import game_state_cleanup

            game_state_cleanup.install()

            # Navigation: wire the "↩ Back to Help" hook into the hub render
            # path so directly-invoked subsystem hubs (!modmenu, !economymenu,
            # …) get a Back button + seeded _back_target, like the !help route.
            # Composition-root wiring (cogs.help_cog → core.panel_manager).
            from cogs.help_cog import _attach_back_to_help_button
            from core.runtime import panel_manager as _panel_manager

            _panel_manager.register_back_to_help_attacher(_attach_back_to_help_button)

            # PR-02c: session_gc.start() now uses tasks.spawn
            # internally (PR-02b); calling it once registers the
            # GC loop with the canonical supervisor.
            session_gc.start()

            # Phase S3.3 / O-4: sample process RSS every 60s so slow
            # memory leaks surface in Prometheus before they OOM the
            # container.  Supervised so a psutil failure logs critical
            # + webhook-alerts rather than escaping silently.
            _runtime_tasks.spawn(
                "process_memory_sampler",
                _sample_process_memory(),
                on_error=_on_app_task_died_webhook,
            )

            # Turn any pending lifecycle request (SIGTERM shutdown or
            # !restart) into bot.close(). Cogs and signal handlers only
            # record intent; this watchdog is the single executor for
            # both shutdown and restart.  Bounded timeout falls back to
            # os._exit so a wedged close cannot hold the runtime lock
            # past its TTL.
            _runtime_tasks.spawn(
                "lifecycle_close_driver",
                _drive_close_on_lifecycle_request(),
                on_error=_on_app_task_died_webhook,
            )

            # Automation scheduler (Track 6 PR 18 / #211): gated behind
            # ``AUTOMATION_SCHEDULER_ENABLED=true``. ``spawn_scheduler``
            # returns ``None`` when the flag is off (default), so the
            # bot boots inert by default.
            #
            # PR-02b: the returned task is already supervised by
            # ``core.runtime.tasks.spawn`` inside ``spawn_scheduler`` —
            # the previous ``_APP_TASKS.append(scheduler_task)`` was a
            # double-supervision artifact.  Shutdown drain now runs
            # ``tasks.cancel_all()`` so the canonical supervisor is the
            # single owner of the scheduler's cancellation.
            from services.automation_scheduler import spawn_scheduler

            spawn_scheduler(bot)

            await _load_cogs()

            # Cross-check subsystem identity surfaces (C1 / INV-B):
            # SUBSYSTEMS keys vs bot commands vs PersistentView SUBSYSTEM
            # vs interaction_router prefixes vs panel_anchors rows.
            #
            # PR I1a: the orchestrator owns summary logging and metric
            # emission.  The validator emits per-finding WARNINGs for
            # diagnostic detail; here we add a tiered summary and bump
            # ``identity_contract_findings_total`` so drift is visible
            # in Prometheus.
            #
            # PR I1b: ``IDENTITY_CONTRACT_STRICT=true`` makes
            # fatal-tier findings abort startup after emitting the
            # webhook alert.  Default is off; production opts in by
            # setting the env var.  ``auto_healable`` and ``warn_only``
            # tiers never abort — they remain advisory until an operator
            # runs ``!platform identity --fix`` (PR I1b admin command).
            try:
                from services import metrics as _metrics
                from utils.subsystem_registry import (
                    summarize_findings,
                    validate_identity_contract,
                )

                findings = await validate_identity_contract(bot)
                summary = summarize_findings(findings)
                for kind, count in summary["by_kind"].items():
                    if count:
                        _metrics.identity_contract_findings_total.labels(
                            kind=kind,
                        ).inc(count)
                strict = _identity_contract_strict()
                fatal = summary["by_tier"]["fatal"]
                aborting = bool(strict and fatal)

                if summary["total"] == 0:
                    logger.info(
                        "Identity-contract: clean (all four surfaces agree). "
                        "STRICT=%s.",
                        "on" if strict else "off",
                    )
                else:
                    log_fn = logger.warning if fatal else logger.info
                    log_fn(
                        "Identity-contract findings | total=%d | fatal=%d | "
                        "auto_healable=%d | warn_only=%d | by_kind=%s | "
                        "STRICT=%s | abort=%s",
                        summary["total"],
                        fatal,
                        summary["by_tier"]["auto_healable"],
                        summary["by_tier"]["warn_only"],
                        summary["by_kind"],
                        "on" if strict else "off",
                        "yes" if aborting else "no",
                    )
                    if reporter:
                        try:
                            await reporter.on_identity_findings(
                                summary,
                                strict=strict,
                                aborting=aborting,
                            )
                        except Exception as exc:
                            logger.debug(
                                "Identity webhook post skipped: %s",
                                exc,
                            )
                if aborting:
                    logger.critical(
                        "Identity-contract: STRICT mode aborting startup "
                        "(%d fatal-tier finding(s)).  Inspect bot.log for "
                        "per-finding WARNINGs.",
                        fatal,
                    )
                    raise SystemExit(1)
            except SystemExit:
                # Strict-mode abort — propagate so main() exits cleanly.
                raise
            except Exception as exc:
                logger.warning("Identity-contract validation skipped: %s", exc)

            # Phase 2 PR-12 — Command Surface Ledger.  Walks the live
            # command surface (cogs + router prefixes) once and caches
            # the immutable snapshot for diagnostics / future
            # PanelRegistry consumers.  Failure is non-fatal: the bot
            # boots without the ledger and `!platform consistency`
            # reports the section as not-built.
            try:
                from core.runtime import command_surface_ledger, startup_outcome

                command_surface_ledger.build_ledger(bot)
                startup_outcome.record_success("command_surface_ledger")
            except Exception as exc:
                logger.warning("Command-surface ledger build skipped: %s", exc)
                from core.runtime import startup_outcome

                startup_outcome.record_failure("command_surface_ledger", exc)

            # Manifest spine slice 2 — project the registered persistent panels
            # into the typed PanelManifest (the L3 panel-editor's read artifact;
            # built from the runtime registry, not an AST guess). Built BEFORE
            # the command manifest so the latter can join each command to its
            # subsystem's panels. Non-fatal: a failure only means `!platform`
            # reports the panel manifest as not-built.
            try:
                from core.runtime import panel_manifest, startup_outcome

                panel_manifest.build_and_cache()
                startup_outcome.record_success("panel_manifest")
            except Exception as exc:
                logger.warning("Panel manifest build skipped: %s", exc)
                from core.runtime import startup_outcome

                startup_outcome.record_failure("panel_manifest", exc)

            # Manifest spine slice 1 — project the just-built ledger into the
            # typed, bot-owned CommandManifest (the reliable read artifact for
            # command management; AST stays drift-detection only). Reuses the
            # cached ledger, so no second surface walk; joins the panel manifest
            # (built just above) for each command's subsystem panels. Non-fatal:
            # a failure only means `!platform` reports the manifest as not-built.
            try:
                from core.runtime import command_manifest, startup_outcome

                command_manifest.build_and_cache_from_bot(bot)
                startup_outcome.record_success("command_manifest")
            except Exception as exc:
                logger.warning("Command manifest build skipped: %s", exc)
                from core.runtime import startup_outcome

                startup_outcome.record_failure("command_manifest", exc)

            # Command description catalog — enriches the ledger with
            # description / signature / display_name so the AI cog can
            # answer meta-questions accurately. Per-command exception
            # isolation keeps a single malformed command from failing
            # startup; failure here only degrades bot self-knowledge.
            try:
                from core.runtime import command_descriptions

                command_descriptions.build_catalog(bot)
            except Exception:
                logger.exception(
                    "command_descriptions: catalog build failed;"
                    " bot self-knowledge will be degraded",
                )

            try:
                from core.runtime import settings_registry, startup_outcome

                settings_registry.build_registry()
                startup_outcome.record_success("settings_registry")
            except Exception as exc:
                logger.warning("Settings registry build skipped: %s", exc)
                from core.runtime import startup_outcome

                startup_outcome.record_failure("settings_registry", exc)

            # S2 — Customization catalogue. Composes the command surface
            # ledger, settings registry, subsystem schemas, and live cog
            # help-hook signals into a frozen, read-only inventory.
            # Failure is non-fatal: the bot boots without the catalogue
            # and `!platform customization` reports it as not-built.
            try:
                from core.runtime import startup_outcome
                from services import customization_catalogue

                customization_catalogue.build_catalogue(bot)
                startup_outcome.record_success("customization_catalogue")
            except Exception as exc:
                logger.warning("Customization catalogue build skipped: %s", exc)
                from core.runtime import startup_outcome

                startup_outcome.record_failure("customization_catalogue", exc)

            # S2.5 — Resource provisioning catalogue. Frozen, read-only
            # cross-link of every ResourceRequirement with its
            # BindingSpec. Pure schema walk — no bot reference needed.
            # Failure is non-fatal: the bot boots without the catalogue
            # and `!platform provisioning` reports it as not-built.
            try:
                from core.runtime import startup_outcome
                from services import resource_provisioning_catalogue

                resource_provisioning_catalogue.build_provisioning_catalogue()
                startup_outcome.record_success("resource_provisioning_catalogue")
            except Exception as exc:
                logger.warning(
                    "Resource provisioning catalogue build skipped: %s",
                    exc,
                )
                from core.runtime import startup_outcome

                startup_outcome.record_failure(
                    "resource_provisioning_catalogue",
                    exc,
                )

            # LP-7: post the deterministic startup-outcome summary
            # before bot.start() so operators see boot health
            # immediately rather than waiting for on_ready (which is
            # what the legacy reporter.on_startup fires from).
            if reporter is not None:
                from core.runtime import startup_outcome as _startup_outcome

                try:
                    await reporter.on_startup_summary(
                        _startup_outcome.all_outcomes(),
                    )
                except Exception as report_err:  # noqa: BLE001 — observability never blocks boot
                    logger.debug(
                        "Startup summary webhook skipped: %s",
                        report_err,
                    )

            logger.info("Starting bot...")
            await bot.start(config.DISCORD_BOT_TOKEN)
    finally:
        # LP-2: mark the cleanup phase so observers see one canonical
        # "the bot is winding down" signal. The transition is recorded
        # in the lifecycle event buffer regardless of which exit path
        # we arrived through (normal return, SIGTERM, exception).
        _lifecycle.set_phase(
            _lifecycle.Phase.SHUTTING_DOWN,
            reason="main_finally",
        )
        # Signal the heartbeat loop to stop cleanly before cancelling
        # all app tasks. ``run_heartbeat_loop`` exits its wait early
        # when the event is set, which lets the lock release happen
        # before we tear down the DB pool.
        _heartbeat_stop.set()
        # PR-02c: drain through the canonical task supervisor.  Every
        # supervised app task is registered in ``tasks._TASKS``; the
        # historical ``_APP_TASKS`` mirror is gone — there is exactly
        # one owner now.  ``cancel_all`` returns the stable snapshot
        # of tasks that were still running at cancellation time, so we
        # await *exactly that set* rather than re-snapshotting after
        # the cancellation (which would race against done-callbacks).
        #
        # The drain runs on **every** exit path — normal return, SIGTERM,
        # uncaught exception — not just SIGTERM.  An app task that
        # ignores cancellation must still see ``CancelledError`` raised
        # before the loop closes, otherwise we'd leak a task into the
        # event-loop shutdown warning surface.
        cancelled = _runtime_tasks.cancel_all()
        if cancelled:
            _, still_pending = await asyncio.wait(cancelled, timeout=5.0)
            if still_pending:
                names = sorted(t.get_name() for t in still_pending)
                logger.warning(
                    "Shutdown drain timeout (%.1fs): %d task(s) did not "
                    "complete cancellation: %s",
                    5.0,
                    len(still_pending),
                    names,
                )
                for t in still_pending:
                    t.cancel()
        # Drop the lock row so the next replica reclaims immediately
        # rather than waiting the 90 s heartbeat TTL.
        try:
            await _runtime.release_lock_best_effort()
        except Exception:
            pass
        await db.close()
        if reporter:
            # Post the close-complete webhook BEFORE tearing down the
            # reporter's HTTP session.  Operators see a paired
            # "beginning" / "complete" lifecycle signal in the operator
            # channel; the gap between the two embeds is the close +
            # cleanup duration as observed end-to-end.  Wrapped in
            # wait_for so a stalled webhook cannot delay process exit.
            pending_for_webhook = _lifecycle.get_pending()
            if pending_for_webhook is not None:
                close_event = next(
                    (
                        event
                        for event in _lifecycle.get_recent_events()
                        if event.name == "close_executing"
                    ),
                    None,
                )
                duration_s = (
                    time.monotonic() - close_event.at
                    if close_event is not None
                    else None
                )
                try:
                    await asyncio.wait_for(
                        reporter.on_lifecycle_close_completed(
                            pending_for_webhook,
                            duration_seconds=duration_s,
                        ),
                        timeout=2.0,
                    )
                except Exception as report_err:
                    logger.debug(
                        "Lifecycle close-completed webhook skipped: %s",
                        report_err,
                    )
            await reporter.close()
        # LP-2 + LP-3: surface the terminal phase. A pending restart
        # request promotes the transition to RESTARTING so observers
        # (and the recent-event buffer) see that the process is exiting
        # specifically for a restart rather than a plain shutdown.
        if _lifecycle.restart_requested():
            _lifecycle.set_phase(
                _lifecycle.Phase.RESTARTING,
                reason="cleanup_complete_restart_pending",
            )
        else:
            _lifecycle.set_phase(
                _lifecycle.Phase.STOPPED,
                reason="cleanup_complete",
            )


# `!restart` exit contract: a clean exit 0 tells on-failure restart policies
# (Railway/Heroku-style supervisors — our prod) the process is DONE, so the
# bot never came back after `!restart` released the lock (live, 2026-06-10).
# A pending restart therefore exits nonzero on purpose so the platform
# relaunches us; a crash exits 1 (it used to fall through to 0 as well).
# Plain shutdown stays exit 0 — that one really is "done".
RESTART_EXIT_CODE = 42


def _exit_code_after_main(*, crashed: bool) -> int:
    """The process exit code once ``main()`` has finished or raised."""
    if crashed:
        return 1
    if _lifecycle.restart_requested():
        return RESTART_EXIT_CODE
    return 0


# How long to sleep before exiting when Discord rate-limits the login attempt.
# The sleep happens inside the still-running process so that Railway's
# immediate on-failure restart fires *after* the backoff has elapsed —
# preventing the rapid crash loop that deepens the Cloudflare 1015 ban.
_LOGIN_RATE_LIMIT_BACKOFF_S = 60


def _maybe_backoff_on_rate_limit(exc: BaseException) -> bool:
    """Sleep before exiting when a 429 is detected during startup login.

    Returns True if a backoff sleep was performed.
    """
    if isinstance(exc, discord.HTTPException) and exc.status == 429:
        logger.warning(
            "Login rate-limited (429); sleeping %ds before exit so the "
            "platform restart does not immediately re-trigger the ban.",
            _LOGIN_RATE_LIMIT_BACKOFF_S,
        )
        time.sleep(_LOGIN_RATE_LIMIT_BACKOFF_S)
        return True
    return False


if __name__ == "__main__":
    import sys

    _crashed = False
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("Critical startup error: %s", exc, exc_info=True)
        _crashed = True
        _maybe_backoff_on_rate_limit(exc)
    sys.exit(_exit_code_after_main(crashed=_crashed))
