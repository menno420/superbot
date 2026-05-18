from __future__ import annotations

import asyncio
import atexit
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
from services.webhook_reporter import WebhookReporter
from utils import db
from utils.synonyms import find_command as _find_synonym

# ---------------------------------------------------------------------------
# Logging — structured JSON when python-json-logger is available,
# falling back to plain text so the bot boots in minimal environments.
# ---------------------------------------------------------------------------
try:
    from pythonjsonlogger import jsonlogger as _jsonlogger

    _fmt: logging.Formatter = _jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
except ImportError:  # python-json-logger not installed — use stdlib formatter
    _fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
_root = logging.getLogger()
_root.setLevel(logging.INFO)

for _h in (
    logging.handlers.RotatingFileHandler(
        "bot.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    ),
    logging.StreamHandler(),
):
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

# ---------------------------------------------------------------------------
# Prevent multiple instances
# ---------------------------------------------------------------------------
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.pid")


def check_existing_instance() -> None:
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            if os.path.exists(f"/proc/{old_pid}"):
                logger.warning("Bot is already running (PID %d). Exiting.", old_pid)
                raise SystemExit(1)
        except (ValueError, FileNotFoundError):
            pass
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _remove_pid() -> None:
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


atexit.register(_remove_pid)

# ---------------------------------------------------------------------------
# Bot instance
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,
)

ALLOWED_CHANNELS = config.ALLOWED_CHANNELS

# Set by SIGTERM handler — channel guard rejects new commands during drain.
_shutting_down = False

# Application-owned background tasks.  Only these are cancelled on shutdown —
# discord.py-internal tasks are left alone to avoid library-level errors.
_APP_TASKS: list[asyncio.Task] = []


def _begin_shutdown(*_) -> None:
    global _shutting_down
    _shutting_down = True
    _remove_pid()


# ---------------------------------------------------------------------------
# Supervised app-task helper — Phase S2.4 / C-2
# Every entry-point-layer asyncio.create_task call should go through this
# helper so unhandled exceptions are loud (critical log + webhook alert)
# instead of escaping the event loop silently.
# ---------------------------------------------------------------------------


def _supervised_task(coro, *, name: str) -> asyncio.Task:
    """Spawn an app-owned background task with a death-detecting callback."""
    task = asyncio.create_task(coro, name=name)
    task.add_done_callback(_on_app_task_done)
    return task


def _on_app_task_done(task: asyncio.Task) -> None:
    """Done-callback: surface unhandled task exceptions instead of swallowing.

    Cancellations are normal during shutdown and ignored.  Real
    exceptions get a critical log + a webhook alert via the supervisor
    channel.  The webhook is scheduled in a new task because
    done_callback runs in the loop but cannot be ``await``-ed in.
    """
    if task.cancelled():
        return
    exc = task.exception()
    if exc is None:
        return
    logger.critical(
        "App task %r died: %s",
        task.get_name(),
        exc,
        exc_info=exc,
    )
    if reporter is not None:
        try:
            asyncio.create_task(
                reporter.on_app_task_died(task.get_name(), exc),
                name=f"_on_app_task_died:{task.get_name()}",
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


@bot.event
async def on_ready() -> None:
    bot.uptime = datetime.datetime.now(tz=datetime.timezone.utc)  # type: ignore[attr-defined]
    bot._reporter = reporter  # type: ignore[attr-defined]
    logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d server(s)", len(bot.guilds))
    logger.info("Loaded cogs: %s", ", ".join(bot.cogs.keys()))
    from core.runtime import live_update_scheduler, message_anchor_manager

    await message_anchor_manager.restore_anchors(bot)
    live_update_scheduler.setup(bot)
    if reporter:
        await reporter.on_startup(bot)


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
        # Governance check failures produce their own user-facing message.
        return

    in_allowed = ctx.channel.id in ALLOWED_CHANNELS
    is_force = ctx.command is not None and ctx.command.name == "force"

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

    # Only send user-facing replies in allowed channels.
    if not in_allowed and not is_force:
        return

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
        suggestion = _find_synonym(raw)
        if suggestion:
            await ctx.send(
                f"❓ Unknown command `{raw}`. Did you mean `{config.PREFIX}{suggestion}`?",
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
# Global check — restrict commands to allowed channels; block during shutdown
# ---------------------------------------------------------------------------


@bot.check
async def _channel_guard(ctx: commands.Context) -> bool:
    if _shutting_down:
        return False
    return ctx.guild is not None and (
        ctx.channel.id in ALLOWED_CHANNELS
        or (ctx.command is not None and ctx.command.name == "force")
    )


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
    from services import governance_service
    from utils.subsystem_registry import SUBSYSTEMS

    failed_exts: set[str] = set()
    for ext in config.INITIAL_EXTENSIONS:
        try:
            await bot.load_extension(ext)
            logger.info("✅ Loaded %s", ext)
        except Exception as exc:
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

    Runs forever until cancelled at shutdown.  Wrapped in ``_supervised_task``
    by main(), so a psutil failure surfaces as a CRITICAL log + webhook
    alert rather than vanishing silently.
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


async def main() -> None:
    # PID guard moved here from module level so test imports don't trigger it.
    check_existing_instance()

    from services.governance_exceptions import GovernanceError
    from utils.subsystem_registry import validate_registry

    try:
        validate_registry()
        logger.info("Registry validated and frozen.")
    except GovernanceError as exc:
        logger.critical("Registry validation failed — aborting startup: %s", exc)
        raise SystemExit(1) from exc

    await db.init()
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

            # Track app-owned tasks so shutdown only cancels OUR tasks,
            # not discord.py-internal ones (OPS-001 fix).  Health server
            # is supervised + gated on bind-ready (Phase S2.4 / O-2b):
            # if the bind fails, the bot aborts startup instead of
            # silently running with a wedged orchestration probe.
            health_ready = asyncio.Event()
            health_task = _supervised_task(
                start_health_server(bot, ready_event=health_ready),
                name="health_server",
            )
            _APP_TASKS.append(health_task)

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

            _APP_TASKS.append(session_gc.start())

            # Phase S3.3 / O-4: sample process RSS every 60s so slow
            # memory leaks surface in Prometheus before they OOM the
            # container.  Supervised so a psutil failure logs critical
            # + webhook-alerts rather than escaping silently.
            _APP_TASKS.append(
                _supervised_task(
                    _sample_process_memory(),
                    name="process_memory_sampler",
                ),
            )

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
                from core.runtime import command_surface_ledger

                command_surface_ledger.build_ledger(bot)
            except Exception as exc:
                logger.warning("Command-surface ledger build skipped: %s", exc)

            logger.info("Starting bot...")
            await bot.start(config.DISCORD_BOT_TOKEN)
    finally:
        # Cancel only application-owned tasks — never asyncio.all_tasks().
        for task in _APP_TASKS:
            if not task.done():
                task.cancel()
        # Graceful drain: give in-flight app coroutines up to 5 s to finish.
        if _shutting_down and _APP_TASKS:
            pending = {t for t in _APP_TASKS if not t.done()}
            if pending:
                _, still_pending = await asyncio.wait(pending, timeout=5.0)
                for t in still_pending:
                    t.cancel()
        await db.close()
        if reporter:
            await reporter.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("Critical startup error: %s", exc, exc_info=True)
