"""AI tool-orchestration policy resolver (Phase 3).

Returns the resolved :class:`OrchestrationDecision` — which toolsets are
offered, the tool-choice mode, and the loop budget — for one request, by
picking the most-specific orchestration profile across the channel / category /
guild scopes and mapping it through :mod:`services.ai_orchestration_presets`.

Pure resolver: no writes, no I/O beyond the policy-table reads it caches, no
gateway calls. The natural-language stage feeds the decision into
``ai_tools.build_registry`` (toolset narrowing) and onto the ``AIRequest``
(``tool_choice`` / ``tool_budget``).

Precedence (most-specific profile wins; a profile is atomic, so there is no
field-level inheritance the way the reply policy has):

    channel orchestration_profile
        → category orchestration_profile
        → guild orchestration_profile
        → system compatible default (today's behaviour)

Rules:

* A ``NULL`` profile at a scope means "no opinion" — fall through to the next
  layer.
* An all-``NULL`` guild resolves to ``ai_orchestration_presets.DEFAULT_PROFILE_KEY``
  (``enabled_toolsets=None`` + automatic choice + hop-bounded budget), i.e. the
  byte-for-byte historical behaviour.
* A persisted key whose preset no longer exists degrades to the default (never
  raises) — the resolver is on the live request path.
* This resolver governs *how* tools are offered, never *whether* the bot replies
  (that is :mod:`services.ai_natural_language_policy`). The two are independent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from core.runtime.ai.contracts import AIToolBudget, AIToolChoice
from services import ai_orchestration_presets as presets
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_orchestration_policy")


# ---------------------------------------------------------------------------
# Inputs / outputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OrchestrationContext:
    """Minimal context the resolver needs to pick a profile."""

    guild_id: int
    channel_id: int
    category_id: int | None = None


@dataclass(frozen=True)
class OrchestrationDecision:
    """The resolved orchestration policy for one request.

    ``enabled_toolsets`` / ``disabled_tools`` feed ``ai_tools.build_registry``
    (they can only *narrow* the scope-allowed set). ``tool_choice`` /
    ``tool_budget`` go straight onto the :class:`AIRequest`. ``profile_key`` and
    ``source`` name the winning preset and the scope that selected it.

    ``source_trace`` is populated only when :func:`resolve` is called with
    ``dry_run=True`` so the admin preview can show "why" without re-implementing
    the resolver. Live decisions leave it empty.
    """

    profile_key: str
    source: str  # "channel" | "category" | "guild" | "default"
    enabled_toolsets: tuple[str, ...] | None
    disabled_tools: tuple[str, ...]
    tool_choice: AIToolChoice
    tool_budget: AIToolBudget
    workflow: str
    answer_contract: str
    source_trace: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Cached read of the per-guild profile bundle (generation-keyed, like the
# natural-language resolver)
# ---------------------------------------------------------------------------


_CACHE: dict[int, tuple[int, dict[str, Any]]] = {}


def invalidate(guild_id: int) -> None:
    """Drop the cached bundle for ``guild_id`` (called by the mutation seam)."""
    _CACHE.pop(guild_id, None)


def _reset_for_tests() -> None:
    _CACHE.clear()


_EMPTY_BUNDLE: dict[str, Any] = {"guild_profile": None, "channel": {}, "category": {}}


async def _load_bundle(guild_id: int) -> dict[str, Any]:
    """Load (with cache) the three policy tables' orchestration columns.

    DB-fault-tolerant: this runs on the live reply path, so a failed policy
    read must never break the reply — it degrades to "no profile set" (the
    compatible default), exactly the historical behaviour. The same fallback
    keeps the resolver callable from unit tests with no database initialised.
    """
    try:
        policy = await ai_db.get_guild_policy(guild_id)
    except Exception as exc:  # noqa: BLE001 — never break the reply on a read fault
        logger.debug("ai_orchestration_policy: guild read failed (%s)", exc)
        return dict(_EMPTY_BUNDLE)
    generation = (policy or {}).get("generation", 0)

    cached = _CACHE.get(guild_id)
    if cached is not None and cached[0] == generation and policy is not None:
        return cached[1]

    try:
        channel = await ai_db.list_channel_policies(guild_id)
        category = await ai_db.list_category_policies(guild_id)
    except Exception as exc:  # noqa: BLE001 — see above
        logger.debug("ai_orchestration_policy: scoped read failed (%s)", exc)
        return dict(_EMPTY_BUNDLE)

    bundle = {
        "guild_profile": (policy or {}).get("orchestration_profile"),
        "channel": {
            row["channel_id"]: row.get("orchestration_profile") for row in channel
        },
        "category": {
            row["category_id"]: row.get("orchestration_profile") for row in category
        },
    }
    if policy is not None:
        _CACHE[guild_id] = (generation, bundle)
    return bundle


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


async def resolve(
    ctx: OrchestrationContext,
    *,
    dry_run: bool = False,
) -> OrchestrationDecision:
    """Resolve the orchestration profile for ``ctx``.

    Pure read with no side effects, so a dry-run is safe from an admin preview
    UI. ``dry_run=True`` additionally records the precedence trace.
    """
    trace: list[str] | None = [] if dry_run else None
    bundle = await _load_bundle(ctx.guild_id)

    key, source = _select_key(ctx, bundle, trace)
    return _decision_for_key(key, source, trace)


def _select_key(
    ctx: OrchestrationContext,
    bundle: dict[str, Any],
    trace: list[str] | None,
) -> tuple[str, str]:
    """Pick the most-specific non-NULL profile key + its source scope."""
    chan_key = bundle["channel"].get(ctx.channel_id)
    if chan_key:
        if trace is not None:
            trace.append(f"channel_profile: {chan_key} (channel {ctx.channel_id})")
        return chan_key, "channel"
    if trace is not None and ctx.channel_id:
        trace.append(f"channel_profile: none for {ctx.channel_id} (inherit)")

    if ctx.category_id is not None:
        cat_key = bundle["category"].get(ctx.category_id)
        if cat_key:
            if trace is not None:
                trace.append(
                    f"category_profile: {cat_key} (category {ctx.category_id})",
                )
            return cat_key, "category"
        if trace is not None:
            trace.append(f"category_profile: none for {ctx.category_id} (inherit)")

    guild_key = bundle.get("guild_profile")
    if guild_key:
        if trace is not None:
            trace.append(f"guild_profile: {guild_key}")
        return guild_key, "guild"

    if trace is not None:
        trace.append(
            f"default: no scope set a profile → {presets.DEFAULT_PROFILE_KEY} "
            "(today's behaviour)",
        )
    return presets.DEFAULT_PROFILE_KEY, "default"


def _decision_for_key(
    key: str,
    source: str,
    trace: list[str] | None,
) -> OrchestrationDecision:
    """Map a (possibly stale) profile key onto a resolved decision."""
    profile = presets.get(key)
    if profile is None:
        # A key persisted by an older build whose preset was removed: never
        # raise on the live path — degrade to the compatible default.
        profile = presets.default()
        if trace is not None:
            trace.append(
                f"unknown_profile: {key!r} not a built-in preset → "
                f"{profile.key} (default)",
            )
        source = "default"
        key = profile.key

    if trace is not None:
        toolsets = (
            "all"
            if profile.enabled_toolsets is None
            else (",".join(profile.enabled_toolsets) or "none")
        )
        trace.append(
            f"resolved: profile={key} source={source} "
            f"toolsets={toolsets} tool_choice={profile.tool_choice.mode.value} "
            f"budget(hops={profile.tool_budget.max_hops},"
            f"calls={profile.tool_budget.max_calls})",
        )

    return OrchestrationDecision(
        profile_key=key,
        source=source,
        enabled_toolsets=profile.enabled_toolsets,
        disabled_tools=profile.disabled_tools,
        tool_choice=profile.tool_choice,
        tool_budget=profile.tool_budget,
        workflow=profile.workflow,
        answer_contract=profile.answer_contract,
        source_trace=tuple(trace or ()),
    )


__all__ = [
    "OrchestrationContext",
    "OrchestrationDecision",
    "invalidate",
    "resolve",
]
