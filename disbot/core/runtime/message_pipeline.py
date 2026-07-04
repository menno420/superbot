"""Message-pipeline orchestrator — §3.2 of the foundational plan.

Provides a single platform-level ``on_message`` that dispatches to
registered :class:`MessageStage` handlers in defined order, with
error isolation, latency metrics, and a routing hook for auto-mod
stages to emit through ``moderation_service``.

The previous architecture had five concurrent ``on_message``
listeners (counting, chain, cleanup, xp, rps_tournament) racing on
every message: XP could award before CleanupCog deleted, ChainCog
could delete a message CountingCog was mid-validating.  The
pipeline fixes that by running stages sequentially in ``order`` and
honouring ``short_circuit`` on early termination.

Stage contract (Protocol)
-------------------------

::

    class MessageStage(Protocol):
        name: str       # stable identifier (used as the metric label)
        order: int      # smaller order runs first; ties run in
                        # registration order

        async def process(
            self, ctx: MessagePipelineContext,
        ) -> StageResult: ...

Stages should be pure-Python objects (a dataclass or hand-rolled
class).  The orchestrator never instantiates them — register an
already-constructed instance via :func:`register`.

Canonical stage-order table
---------------------------

**This is the single source of truth for stage ordering.**  Stages run
in ascending ``order``; the value lives next to each stage class as a
``*_STAGE_ORDER`` constant.  Tiers are spaced so new stages slot in
without renumbering, and every value is distinct so ordering never
depends on cog load order (enforced by
``tests/unit/runtime/test_message_pipeline.py::
test_registered_stage_orders_are_distinct``).

==========  =====  =========================================  ============
order       tier   stage (constant)                           short-circuits?
==========  =====  =========================================  ============
5           auto-mod   automod    (``AUTOMOD_STAGE_ORDER``)    on delete
10          auto-mod   cleanup    (``CLEANUP_STAGE_ORDER``)    on delete
15          auto-mod   counting   (``COUNTING_STAGE_ORDER``)   on delete
20          auto-mod   chain      (``CHAIN_STAGE_ORDER``)      on delete
25          auto-mod   image_mod  (``IMAGE_MOD_STAGE_ORDER``)  on delete
30          rewards    xp         (``XP_STAGE_ORDER``)         no
40          rewards    rps        (``RPS_STAGE_ORDER``)        no
50          passive    four_twenty(``FOUR_TWENTY_STAGE_ORDER``) no
55          passive    ai_correction(``AI_CORRECTION_STAGE_ORDER``) no
70          conv.      ai_nl      (``ai…STAGE_ORDER``)         on bot mention
80          conv.      btd6       (``btd6…STAGE_ORDER``)       on handle
==========  =====  =========================================  ============

Tier rationale:

* **auto-mod (10–20)** — may delete the message; cleanup runs first so a
  banned word is gone before counting/chain validate it.
* **rewards (30–40)** — award/capture; must run after auto-mod so a
  deleted message is never rewarded.
* **passive (50–69)** — observe-only side effects (e.g. the 🍃 egg).
  Must precede any short-circuiting conversational stage so a message
  the AI consumes still gets passive treatment.
* **conversational (70+)** — may *handle* the message and short-circuit
  (AI reply, BTD6 assistant).

Built-in pre-filter
-------------------

The orchestrator drops two categories of messages before any stage
runs:

  - ``message.author.bot`` is True (bot-emitted messages)
  - ``message.guild`` is ``None`` (DMs)

Stages can therefore assume a guild-bound, non-bot author.

Error isolation
---------------

An exception raised by ``stage.process`` is logged with the stage
name + message id and the pipeline continues to the next stage.  A
stage cannot crash the platform listener.

Latency metrics
---------------

``message_pipeline_stage_seconds{stage=...}`` (Prometheus Histogram)
records per-stage ``process`` time including any I/O the stage did.
The metric is emitted in a ``finally`` clause so exceptions still
contribute a measurement.

Moderation routing
------------------

When a stage returns ``StageResult(moderation_action=...)`` the
orchestrator awaits :func:`_route_moderation_action`, which routes
the descriptor to ``moderation_service.auto_delete``.  The stage may
already have deleted the message itself — ``auto_delete`` catches
the resulting ``NotFound`` and still records the rule trigger so the
audit row exists either way.

If a stage prefers the imperative form (call ``moderation_service``
directly inside ``process``), that also works — see CleanupStage for
an example.  Both paths land in the same ``mod_logs`` row + emit the
same ``EVT_MOD_ACTION``.

Public surface
--------------

::

    register(stage)         — add a stage (deduplicates by name)
    unregister(name)        — remove a stage by name
    clear()                 — test-only: drop all stages
    stages_snapshot()       — defensive copy of current stages
    setup(bot)              — install the platform listener (idempotent)
    dispatch(bot, message)  — orchestrator (exposed for unit tests)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import discord
from discord.ext import commands

from core.runtime import lifecycle
from services import metrics

logger = logging.getLogger("bot.runtime.message_pipeline")


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModerationActionDescriptor:
    """Describes an auto-mod action for unified audit.

    The originating stage has already performed the action (e.g.
    deleted the message); the descriptor tells the orchestrator to
    log + emit it through ``moderation_service``.

    Plumbing only in this PR — no current consumer.  Future auto-mod
    stage migrations (counting / chain / cleanup) will return a
    populated descriptor and the routing hook will dispatch it.
    """

    action: str  # e.g. "auto_delete:counting"
    target_id: int  # message author id
    reason: str  # human-readable
    rule: str = ""  # optional machine-readable rule id


@dataclass
class MessagePipelineContext:
    """Per-message context threaded through every stage.

    ``metadata`` is mutable scratch — stages can stash derived state
    (parsed command context, expensive lookups) under stable keys
    so downstream stages avoid re-computation.
    """

    bot: commands.Bot
    message: discord.Message
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """Stage return value.

    Fields:
        deleted: stage deleted the message.  Advisory — set
                 ``short_circuit=True`` if downstream stages should
                 skip.  (We keep them separate so a stage can delete
                 *and* let downstream observability stages still run
                 if appropriate.)
        short_circuit: stop the pipeline; no downstream stages run.
        moderation_action: when non-None, the orchestrator routes
                 this descriptor through ``moderation_service`` for
                 unified audit.  Currently a no-op hook (see plan
                 §3.2 — wired up by future auto-mod migrations).
    """

    deleted: bool = False
    short_circuit: bool = False
    moderation_action: ModerationActionDescriptor | None = None


@runtime_checkable
class MessageStage(Protocol):
    """Protocol every stage must satisfy.

    A stage's ``name`` is its stable identifier — used as the
    Prometheus label and as the dedup key for :func:`register`.
    """

    name: str
    order: int

    async def process(self, ctx: MessagePipelineContext) -> StageResult: ...


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_STAGES: list[MessageStage] = []


def register(stage: MessageStage) -> None:
    """Register a stage; deduplicates by name.

    A subsequent ``register`` with the same ``name`` replaces the
    earlier entry — this makes cog reload safe (the old stage is
    dropped and the new instance takes its place).  Stages are
    re-sorted by ``order`` on every registration so :func:`dispatch`
    can iterate in run order without re-sorting per message.
    """
    global _STAGES
    _STAGES = [s for s in _STAGES if s.name != stage.name]
    _STAGES.append(stage)
    _STAGES.sort(key=lambda s: s.order)
    logger.debug("Registered stage %r (order=%d)", stage.name, stage.order)


def unregister(name: str) -> None:
    """Remove a stage by name.  No-op if not registered."""
    global _STAGES
    _STAGES = [s for s in _STAGES if s.name != name]


def clear() -> None:
    """Test-only: drop all registered stages."""
    global _STAGES
    _STAGES = []


def stages_snapshot() -> list[MessageStage]:
    """Return a defensive copy of the current stages in run order."""
    return list(_STAGES)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def dispatch(bot: commands.Bot, message: discord.Message) -> None:
    """Run every registered stage for one message, in order.

    See module docstring for the pre-filter rules, error-isolation
    semantics, and moderation-routing hook.
    """
    # Deploy-handoff double-fire guard (LP-4).  main() releases the runtime
    # lock BEFORE bot.close() drains, so the incoming replica connects while
    # this instance is still draining.  Discord delivers MESSAGE_CREATE to
    # BOTH gateway connections during the overlap; running the stages here
    # would double-apply every additive side effect (db.add_xp is additive
    # with no per-message idempotency → double XP; same class for counting /
    # chain / rps / four_twenty / btd6).  A draining instance runs no stages
    # — the incoming replica owns ongoing traffic.  This does not regress the
    # LP-4 fast lock release; it only stops the OUTGOING instance from acting
    # during the handoff overlap.
    if lifecycle.is_shutting_down():
        return
    if message.author.bot:
        return
    if message.guild is None:
        return

    ctx = MessagePipelineContext(bot=bot, message=message)
    for stage in _STAGES:
        t0 = time.perf_counter()
        result: StageResult | None = None
        try:
            result = await stage.process(ctx)
        except Exception:
            logger.exception(
                "message pipeline stage %r raised on message %s",
                stage.name,
                message.id,
            )
        finally:
            metrics.message_pipeline_stage_seconds.labels(
                stage=stage.name,
            ).observe(time.perf_counter() - t0)

        if result is None:
            # Stage raised — error already logged.  Continue to next.
            continue

        if result.moderation_action is not None:
            await _route_moderation_action(message, result.moderation_action)

        if result.short_circuit:
            return


async def _route_moderation_action(
    message: discord.Message,
    action: ModerationActionDescriptor,
) -> None:
    """Route an auto-mod descriptor to ``moderation_service``.

    The originating stage typically already deleted the message;
    ``moderation_service.auto_delete`` catches the resulting
    ``NotFound`` and still records the rule trigger so the audit
    row exists either way.

    Currently only ``"auto_delete:..."`` actions are recognised.
    Future descriptor types (e.g. ``"auto_timeout:..."``) extend
    this dispatch with the matching ``moderation_service`` call.
    """
    from services import moderation_service

    if action.action.startswith("auto_delete"):
        await moderation_service.auto_delete(
            message,
            reason=action.reason,
            rule=action.rule or action.action,
        )
        return

    logger.warning(
        "ModerationActionDescriptor with unrecognised action=%r reached "
        "_route_moderation_action — extend the dispatch when adding new "
        "descriptor types.  target=%d reason=%r message=%d",
        action.action,
        action.target_id,
        action.reason,
        message.id,
    )


# ---------------------------------------------------------------------------
# Wire-up
# ---------------------------------------------------------------------------

_PLATFORM_LISTENER_INSTALLED = False


def setup(bot: commands.Bot) -> None:
    """Install the platform-level ``on_message`` listener.  Idempotent.

    Call once during bot startup, before ``bot.start()``.  Subsequent
    calls are no-ops — discord.py's ``bot.listen`` would otherwise
    register duplicate handlers on hot-reload.
    """
    global _PLATFORM_LISTENER_INSTALLED
    if _PLATFORM_LISTENER_INSTALLED:
        logger.debug("message_pipeline.setup() called again — skipping.")
        return
    _PLATFORM_LISTENER_INSTALLED = True

    @bot.listen("on_message")
    async def _platform_on_message(message: discord.Message) -> None:
        await dispatch(bot, message)

    logger.info("message_pipeline platform listener installed.")
