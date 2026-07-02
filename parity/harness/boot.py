"""Boot the REAL bot in-process, gateway-free — the harness composition root.

This replicates the behavior-relevant part of ``disbot/bot1.py``'s ``main()``
against the real module-level ``bot1.bot`` object (so the production
``on_command_error`` typo re-dispatch, the ``before_invoke`` governance
guard, ``on_interaction`` router, and the metrics listeners are all live),
stopping short of anything network- or process-management-shaped.

Included (behavior the goldens must capture):
    validate_registry → db.init (migrations) → runtime.setup() →
    message_pipeline.setup(bot) → server_logging.setup(bot) →
    game_state_cleanup.install() → the help back-button attacher →
    load all INITIAL_EXTENSIONS → READY + GUILD_CREATE via the real parser.

Deliberately skipped (process/ops, not behavior — documented deviations):
    the runtime instance lock + heartbeat, the health server, the
    process-memory sampler, the lifecycle close driver, the automation
    scheduler spawn (env-gated off in prod-default anyway), and
    ``discord.ext.tasks`` Loop scheduling (time-driven behavior is out of
    the command-in → output-out capture scope; loops are neutralized
    exactly like the boot smoke-test probe).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DISBOT = _REPO_ROOT / "disbot"

# Import-order contract: config raises without a token; tests use the same
# placeholder convention (tests/conftest.py).
os.environ.setdefault("DISCORD_BOT_TOKEN_PRODUCTION", "PARITY_PLACEHOLDER_TOKEN")
# Pin the platform-owner identity to the admin persona so owner-gated
# surfaces are drivable and `bot.is_owner` never needs an HTTP app lookup.
os.environ.setdefault("BOT_OWNER_USER_ID", "900000000000000101")
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from parity.harness.fake_http import (  # noqa: E402
    FakeHTTP,
    FakeWebhookAdapter,
    drain_dispatch_tasks,
)
from parity.harness.world import DEFAULT_PERSONAS, World  # noqa: E402

__all__ = ["Harness", "HarnessBootError"]


class HarnessBootError(RuntimeError):
    """The harness could not boot the real bot (env problem, not a golden)."""


class Harness:
    """A booted, gateway-free real bot plus its capture channels."""

    def __init__(self) -> None:
        self.bot: Any = None
        self.world: World | None = None
        self.http: FakeHTTP | None = None
        self.events: list[dict[str, Any]] = []
        self.extension_failures: dict[str, str] = {}
        self._spawned: set[asyncio.Task[Any]] = set()

    # ------------------------------------------------------------------ boot

    @classmethod
    async def start(cls, *, require_db: bool = True) -> Harness:
        self = cls()

        import discord
        from discord.ext import tasks as ext_tasks

        # --- neutralize time-driven schedulers (smoke-probe pattern) -------
        ext_tasks.Loop.start = lambda loop_self, *_a, **_k: loop_self  # type: ignore[method-assign]

        # discord.ui.View timeouts are WALL-CLOCK asyncio timers: a panel
        # opened by case N fires its timeout-disable edit ~180s later,
        # landing inside whatever case is running then (observed: a
        # bootstrap-access panel's disable-buttons edit contaminated a
        # later sweep golden). Timeout behavior is time-driven — out of
        # capture scope like ext.tasks loops (README deviations ledger) —
        # so views are forced non-expiring inside the harness.
        _orig_view_init = discord.ui.View.__init__

        def _no_timeout_view_init(view_self: Any, *, timeout: Any = 180.0) -> None:
            _orig_view_init(view_self, timeout=None)

        discord.ui.View.__init__ = _no_timeout_view_init  # type: ignore[method-assign]

        # delete_after=N schedules deletes on an N-second wall timer, which
        # lands them in whatever step happens to be running N seconds later.
        # For capture, the delete is attributed to the step that scheduled
        # it: the delay is dropped, the delete itself is still captured.
        _orig_delete = discord.Message.delete

        async def _instant_delete(
            msg_self: Any,
            *,
            delay: Any = None,
            **kw: Any,
        ) -> Any:
            return await _orig_delete(msg_self, delay=None, **kw)

        discord.Message.delete = _instant_delete  # type: ignore[method-assign]

        from core.runtime import tasks as runtime_tasks

        def _tracking_spawn(name: str, coro: Any, **kwargs: Any) -> asyncio.Task[Any]:
            # Run spawned work for real (a command's fire-and-forget side
            # effects are behavior) but keep it out of drain's way and
            # cancel it at close. Supervision/webhook-alerting is ops.
            task = asyncio.get_event_loop().create_task(coro, name=f"parity:{name}")
            self._spawned.add(task)
            task.add_done_callback(self._spawned.discard)
            return task

        runtime_tasks.spawn = _tracking_spawn  # type: ignore[assignment]

        # --- the real composition root ------------------------------------
        import bot1  # noqa: F401  (module-level handlers register here)

        bot = bot1.bot
        self.bot = bot
        # login() normally runs this: binds bot.loop / bot._ready to the
        # running loop so dispatch scheduling and wait_until_ready work.
        await bot._async_setup_hook()
        bot.owner_id = 900_000_000_000_000_101  # the admin persona (see world)

        world = World(bot)
        self.world = world
        # Pin Python wall-clock reads to the logical clock: services stamp
        # time.time() into rows/branches (e.g. the XP chat throttle), which
        # otherwise makes behavior depend on when the capture ran. Postgres
        # now() stays real (its values are normalized; in-SQL comparisons
        # are self-consistent). asyncio uses time.monotonic — untouched.
        import time as _time

        self._real_time = _time.time
        _time.time = lambda: world.clock.now.timestamp()  # type: ignore[assignment]
        http = FakeHTTP(
            ids=world.ids,
            clock=world.clock,
            bot_user_payload=world.bot_user_payload,
        )
        self.http = http
        bot.http = http
        bot._connection.http = http
        # CommandTree captured the real HTTPClient at Bot construction.
        bot.tree._http = http

        from discord.webhook import async_ as webhook_async

        webhook_async.async_context.set(FakeWebhookAdapter(http))  # type: ignore[arg-type]

        # --- bot1.main()'s behavior-relevant sequence ----------------------
        from services.governance_exceptions import GovernanceError
        from utils.subsystem_registry import validate_registry

        try:
            validate_registry()
        except GovernanceError as exc:  # pragma: no cover - registry is CI-green
            raise HarnessBootError(f"registry validation failed: {exc}") from exc

        if require_db:
            if not os.environ.get("DATABASE_URL"):
                raise HarnessBootError(
                    "DATABASE_URL unset — the parity harness needs Postgres "
                    "(the bot's behavior is DB-backed).",
                )
            from utils import db

            try:
                await db.init()
            except Exception as exc:  # noqa: BLE001 - env failure, not behavior
                raise HarnessBootError(f"Postgres unavailable: {exc}") from exc

        from core import runtime
        from core.runtime import message_pipeline

        await runtime.setup()
        message_pipeline.setup(bot)

        from services import server_logging

        server_logging.setup(bot)

        from services import game_state_cleanup

        game_state_cleanup.install()

        from cogs.help_cog import _attach_back_to_help_button
        from core.runtime import panel_manager as _panel_manager

        _panel_manager.register_back_to_help_attacher(_attach_back_to_help_button)

        import config

        for ext in config.INITIAL_EXTENSIONS:
            try:
                await bot.load_extension(ext)
            except Exception as exc:  # noqa: BLE001 - report, don't die
                self.extension_failures[ext] = f"{type(exc).__name__}: {exc}"

        # --- event tap (all catalogued events, real subscriptions) ---------
        from core.events import bus
        from core.events_catalogue import KNOWN_EVENTS

        def _make_tap(event_name: str) -> Any:
            async def _tap(**payload: Any) -> None:
                self.events.append({"event": event_name, "payload": payload})

            return _tap

        for _event in sorted(KNOWN_EVENTS):
            bus.on(_event, _make_tap(_event))

        # --- the fake world -------------------------------------------------
        world.install(DEFAULT_PERSONAS)
        await drain_dispatch_tasks(exclude=self._spawned)
        # Let one-shot boot tasks (slash auto-sync, orphan cleanups) finish
        # so their calls land in boot noise, not inside the first case.
        # Neutralized infinite loops just hit the timeout once, here.
        if self._spawned:
            await asyncio.wait(set(self._spawned), timeout=5.0)
        await drain_dispatch_tasks(exclude=self._spawned)
        # boot noise (on_ready sends etc.) is not case output
        http.calls.clear()
        self.events.clear()
        return self

    async def _settle(self, spawned_before: set[asyncio.Task[Any]]) -> None:
        """Wait for dispatch tasks AND anything this step spawned.

        A command's fire-and-forget side effects are behavior — they must
        be attributed to the step that caused them, never leak into the
        next case. A step-spawned task that outlives the timeout is a
        stall (captured as-is; the golden shows where the flow parked).
        """
        await drain_dispatch_tasks(exclude=self._spawned)
        new_tasks = {
            t for t in self._spawned if t not in spawned_before and not t.done()
        }
        if new_tasks:
            await asyncio.wait(new_tasks, timeout=2.5)
            await drain_dispatch_tasks(exclude=self._spawned)

    # ------------------------------------------------------------------ drive

    async def send_command(
        self,
        content: str,
        *,
        persona: str = "member",
        channel: str = "general",
        mentions: tuple[int, ...] = (),
    ) -> None:
        """Feed a member message through the real gateway parser and settle."""
        if self.world is None:
            raise RuntimeError("harness not started")
        payload = self.world.message_payload(
            content,
            persona=persona,
            channel=channel,
            mentions=mentions,
        )
        spawned_before = set(self._spawned)
        self.bot._connection.parse_message_create(payload)
        await self._settle(spawned_before)

    async def invoke_slash(
        self,
        name: str,
        options: list[dict[str, Any]] | None = None,
        *,
        persona: str = "member",
        channel: str = "general",
    ) -> None:
        if self.world is None:
            raise RuntimeError("harness not started")
        payload = self.world.slash_payload(
            name,
            options,
            persona=persona,
            channel=channel,
        )
        spawned_before = set(self._spawned)
        self.bot._connection.parse_interaction_create(payload)
        await self._settle(spawned_before)

    async def click(
        self,
        *,
        message_id: int,
        custom_id: str,
        component_type: int = 2,
        values: list[str] | None = None,
        persona: str = "member",
        channel: str = "general",
    ) -> None:
        if self.world is None:
            raise RuntimeError("harness not started")
        payload = self.world.component_payload(
            message_id=message_id,
            custom_id=custom_id,
            component_type=component_type,
            values=values,
            persona=persona,
            channel=channel,
        )
        spawned_before = set(self._spawned)
        self.bot._connection.parse_interaction_create(payload)
        await self._settle(spawned_before)

    # ---------------------------------------------------------------- output

    def take_calls(self) -> list[Any]:
        """Pop the outbound calls captured since the last take."""
        if self.http is None:
            raise RuntimeError("harness not started")
        calls = list(self.http.calls)
        self.http.calls.clear()
        return calls

    def take_events(self) -> list[dict[str, Any]]:
        events = list(self.events)
        self.events.clear()
        return events

    # ----------------------------------------------------------------- close

    async def close(self) -> None:
        if getattr(self, "_real_time", None) is not None:
            import time as _time

            _time.time = self._real_time  # type: ignore[assignment]
        for task in list(self._spawned):
            task.cancel()
        if self._spawned:
            await asyncio.gather(*self._spawned, return_exceptions=True)
        try:
            from utils.db import pool

            await pool.close()
        except Exception:  # noqa: BLE001 - close is best-effort
            pass
