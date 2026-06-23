"""AI-assisted setup advisor — Phase 9f / Track 5 PR 13.

Defines the :class:`SetupAdvisor` Protocol that both deterministic
and AI advisors implement, an OpenAI implementation, and a
factory :func:`build_advisor` that picks an implementation based on
the ``SETUP_ADVISOR_PROVIDER`` environment variable (default:
``deterministic`` — so CI and dev environments never reach out to
an external API by accident).

Provider contract
-----------------
Any advisor must:

* Take a :class:`GuildSnapshot` as its only input.
* Return a :class:`SetupPlanDraft` describing recommendations.
* Never mutate DB state, never call ``guild.create_*``, never
  invent a subsystem or binding name.

Output validation
-----------------
Every advisor's recommendations are re-validated against
:func:`subsystem_schema.all_schemas` before they ever surface in the
UI. An AI model that hallucinates a subsystem like ``"vibes"`` or a
binding kind like ``"emoji"`` simply has its proposal dropped with a
reason; it cannot extend the bot's mutation surface.

Structured output
-----------------
The OpenAI implementation uses strict JSON Schema response format
(``response_format={"type": "json_schema", "json_schema": {...,
"strict": true}}``) so the SDK validates shape on the wire. We
then re-validate the parsed objects against our local schema
catalogue. Both layers run; CI does not have an OPENAI_API_KEY so
the path is exercised through mock objects.

Gateway migration (Module 1, AI/BTD6 plan)
------------------------------------------
The OpenAI provider call no longer happens in this module. It is
routed through :class:`core.runtime.ai.gateway.AIGateway` so:

* The ``openai`` SDK import lives only in
  :mod:`core.runtime.ai.providers.openai_provider`.
* Redaction, timeout, metrics, and failure handling are uniform
  across every AI consumer.
* The advisor's public API is unchanged: ``OpenAISetupAdvisor``
  still accepts an injected ``client`` for tests, and
  ``build_advisor`` still resolves the provider via
  ``SETUP_ADVISOR_PROVIDER``. When a test injects a ``client``, the
  advisor wraps it in an ``OpenAIProvider`` and feeds the gateway,
  so the legacy injection contract continues to work end-to-end.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from core.runtime.ai.contracts import (
    AIRequest,
    AIRequestContext,
    AIResponseMode,
    AIScope,
    AITask,
)
from core.runtime.ai.providers import OpenAIProvider
from services import ai_gateway as _ai_gateway_service
from services.guild_snapshot import GuildSnapshot
from services.setup_plan import (
    CONFIDENCES,
    DeterministicAdvisor,
    SetupPlanDraft,
    SetupRecommendation,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.services.setup_ai_advisor")

DETERMINISTIC = "deterministic"
OPENAI = "openai"
ANTHROPIC = "anthropic"

KNOWN_PROVIDERS: frozenset[str] = frozenset({DETERMINISTIC, OPENAI, ANTHROPIC})

# JSON schema posted alongside ``response_format`` so the SDK guards
# the shape we then re-validate locally.
_RECOMMENDATION_JSON_SCHEMA: dict[str, Any] = {
    "name": "SetupPlanDraft",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "subsystem": {"type": "string"},
                        "binding_name": {"type": "string"},
                        "target_kind": {"type": "string"},
                        "target_id": {"type": "integer"},
                        "target_name": {"type": "string"},
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "reason": {"type": "string"},
                    },
                    "required": [
                        "subsystem",
                        "binding_name",
                        "target_kind",
                        "target_id",
                        "target_name",
                        "confidence",
                        "reason",
                    ],
                },
            },
        },
        "required": ["recommendations"],
    },
    "strict": True,
}


@runtime_checkable
class SetupAdvisor(Protocol):
    """The single interface deterministic + AI advisors implement."""

    async def suggest(self, snapshot: GuildSnapshot) -> SetupPlanDraft: ...


# ---------------------------------------------------------------------------
# OpenAI advisor
# ---------------------------------------------------------------------------


_SYSTEM_PROMPT = (
    "You are a Discord-server setup assistant. The user will send you a "
    "metadata snapshot of a guild and ask which channels/categories/roles "
    "should be bound to which bot subsystems. Reply ONLY with the strict "
    "JSON schema provided. Never invent a subsystem name, binding name, or "
    "target kind that does not appear in the snapshot's settings_snapshot "
    "or bindings_snapshot. If you are unsure, return fewer recommendations "
    "rather than guessing."
)

# Appended to the system prompt when the operator supplies a free-form
# description of their server (the natural-language setup wedge). The
# description adds *intent* the channel names alone can't convey, but it must
# never widen the mutation surface — every recommendation is still re-validated
# against the subsystem schema, so an off-schema suggestion is dropped.
_DESCRIPTION_DIRECTIVE = (
    " The operator has ALSO described, in their own words, what their server is "
    "for and how it is organised (field `operator_description`). Use that intent "
    "to choose better bindings — it can disambiguate a channel whose name is not "
    "self-explanatory. You still must NEVER invent a subsystem, binding, or "
    "target kind that is absent from the snapshot."
)


class OpenAISetupAdvisor:
    """OpenAI structured-output adapter.

    The adapter is a thin wrapper around the AI gateway. The
    ``client`` constructor argument is preserved for test injection:
    when set, the advisor builds a one-off :class:`OpenAIProvider`
    bound to the injected client and feeds it to the gateway via
    ``provider_override`` — every other test path stays identical.
    Without an injected client, the advisor uses the gateway's
    default OpenAI provider.
    """

    def __init__(
        self,
        *,
        client: Any = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._client = client
        self._model = model or os.getenv("SETUP_ADVISOR_OPENAI_MODEL", "gpt-4o-mini")
        self._api_key = api_key
        if client is None and not (api_key or os.getenv("OPENAI_API_KEY", "")):
            # Preserve the legacy constructor contract: build_advisor()
            # only reaches this branch when api_key is present, and
            # tests always inject either ``client`` or ``api_key``.
            # Raising here keeps backwards compatibility with code that
            # introspected the failure mode.
            raise RuntimeError(
                "OPENAI_API_KEY is not set; cannot build OpenAISetupAdvisor.",
            )

    async def suggest(self, snapshot: GuildSnapshot) -> SetupPlanDraft:
        return await self._run(snapshot, description=None)

    async def suggest_with_description(
        self,
        snapshot: GuildSnapshot,
        description: str,
    ) -> SetupPlanDraft:
        """Like :meth:`suggest`, but folds the operator's free-form
        description of the server into the prompt — the natural-language
        setup wedge. Consumed by
        :mod:`services.setup_natural_language_advisor`. The description only
        adds intent signal; recommendations are still re-validated against the
        subsystem schema, so it can never widen the mutation surface.
        """
        return await self._run(snapshot, description=description)

    async def _run(
        self,
        snapshot: GuildSnapshot,
        *,
        description: str | None,
    ) -> SetupPlanDraft:
        provider_override = None
        if self._client is not None:
            provider_override = OpenAIProvider(client=self._client)

        system_prompt = _SYSTEM_PROMPT
        payload = _snapshot_to_prompt(snapshot)
        if description:
            system_prompt = _SYSTEM_PROMPT + _DESCRIPTION_DIRECTIVE
            payload = {**payload, "operator_description": description}

        request = AIRequest(
            context=AIRequestContext(
                task=AITask.SETUP_SUGGEST,
                scope=AIScope.ADMIN,
                guild_id=snapshot.guild_id,
                source="setup_ai_advisor",
            ),
            system_prompt=system_prompt,
            payload=payload,
            mode=AIResponseMode.JSON,
            response_schema=_RECOMMENDATION_JSON_SCHEMA,
            # Multi-recommendation plans can be large; give the structured
            # response generous headroom now that the OpenAI adapter honours
            # this cap (previously it was silently ignored).
            max_output_tokens=4096,
        )

        gateway = _ai_gateway_service.get_default_gateway()
        response = await gateway.execute(
            request,
            provider_override=provider_override,
        )

        if response.degraded:
            reason = response.fallback_reason or "openai: degraded response"
            if "invalid_json" in reason:
                return SetupPlanDraft(
                    recommendations=(),
                    dropped=(f"openai: invalid JSON ({reason})",),
                    source=OPENAI,
                )
            if "empty response" in reason or "no choices" in reason:
                return SetupPlanDraft(
                    recommendations=(),
                    dropped=("openai: empty response",),
                    source=OPENAI,
                )
            return SetupPlanDraft(
                recommendations=(),
                dropped=(f"openai: {reason}",),
                source=OPENAI,
            )

        if response.data is None:
            return SetupPlanDraft(
                recommendations=(),
                dropped=("openai: empty response",),
                source=OPENAI,
            )

        return _validate_ai_payload(response.data)


def _snapshot_to_prompt(snapshot: GuildSnapshot) -> dict[str, Any]:
    """Compact serialisation for the LLM prompt.

    Drops the readiness_findings details — the model only needs
    structure, not the per-finding messages — and renames fields to
    plain ``snake_case`` (already the case for dataclass fields).
    """
    return {
        "guild_id": snapshot.guild_id,
        "guild_name": snapshot.guild_name,
        "channels": [
            {
                "id": ch.id,
                "name": ch.name,
                "type": ch.type,
                "topic": ch.topic,
                "parent_category": ch.parent_category,
                "bot_can_send": ch.bot_can_send,
            }
            for ch in snapshot.channels
        ],
        "categories": [{"id": cat.id, "name": cat.name} for cat in snapshot.categories],
        "roles": [
            {"id": r.id, "name": r.name, "bot_can_manage": r.bot_can_manage}
            for r in snapshot.roles
        ],
        "settings_snapshot": snapshot.settings_snapshot,
        "bindings_snapshot": snapshot.bindings_snapshot,
    }


def _validate_ai_payload(parsed: Any) -> SetupPlanDraft:
    """Re-validate a parsed AI payload against the local schema.

    Steps:

    * The top-level object must carry a ``recommendations`` list.
    * Each item must carry every required field of
      :class:`SetupRecommendation`.
    * ``confidence`` must be one of ``high`` / ``medium`` / ``low``.
    * The (subsystem, binding_name, target_kind) tuple must match
      a real :class:`BindingSpec` in
      ``subsystem_schema.all_schemas()``. Anything else is dropped
      with a reason.
    """
    if not isinstance(parsed, dict):
        return SetupPlanDraft(
            recommendations=(),
            dropped=(f"openai: top-level type {type(parsed).__name__}",),
            source=OPENAI,
        )

    recommendations_raw = parsed.get("recommendations")
    if not isinstance(recommendations_raw, list):
        return SetupPlanDraft(
            recommendations=(),
            dropped=("openai: missing recommendations[]",),
            source=OPENAI,
        )

    survivors: list[SetupRecommendation] = []
    dropped: list[str] = []
    for index, item in enumerate(recommendations_raw):
        if not isinstance(item, dict):
            dropped.append(f"openai: item[{index}] not a dict")
            continue
        confidence = item.get("confidence")
        if confidence not in CONFIDENCES:
            dropped.append(
                f"openai: item[{index}] bad confidence {confidence!r}",
            )
            continue
        try:
            rec = SetupRecommendation(
                subsystem=item["subsystem"],
                binding_name=item["binding_name"],
                target_kind=item["target_kind"],
                target_id=int(item["target_id"]),
                target_name=item["target_name"],
                confidence=confidence,
                reason=item["reason"],
                source=OPENAI,
            )
        except (KeyError, TypeError, ValueError) as exc:
            dropped.append(f"openai: item[{index}] {type(exc).__name__}: {exc}")
            continue

        reason = _validate_against_schema(rec)
        if reason is not None:
            dropped.append(f"openai: {rec.subsystem}.{rec.binding_name}: {reason}")
            continue
        survivors.append(rec)

    return SetupPlanDraft(
        recommendations=tuple(survivors),
        dropped=tuple(dropped),
        source=OPENAI,
    )


def _validate_against_schema(rec: SetupRecommendation) -> str | None:
    """Mirror of :func:`services.setup_plan._validate_against_schema`."""
    try:
        from core.runtime.subsystem_schema import all_schemas
    except Exception:
        logger.exception(
            "setup_ai_advisor: subsystem_schema unavailable; "
            "dropping every AI recommendation.",
        )
        return "subsystem_schema unavailable"
    schemas = all_schemas() or {}
    schema = schemas.get(rec.subsystem)
    if schema is None:
        return f"subsystem {rec.subsystem!r} not registered"
    for spec in schema.bindings:
        if spec.name == rec.binding_name:
            if spec.kind.value != rec.target_kind:
                return (
                    f"binding {rec.subsystem}.{rec.binding_name} has kind "
                    f"{spec.kind.value}, AI proposed {rec.target_kind}"
                )
            return None
    return f"binding {rec.subsystem}.{rec.binding_name} not declared"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def build_advisor(
    provider: str | None = None,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> SetupAdvisor:
    """Pick and instantiate the right advisor.

    Resolution:

    1. Explicit ``provider`` argument (used by tests).
    2. ``SETUP_ADVISOR_PROVIDER`` environment variable.
    3. Default: ``deterministic``.

    Whenever the requested provider is unavailable (missing API
    key, missing SDK), we silently fall back to the deterministic
    advisor and log a warning. CI never has an ``OPENAI_API_KEY``
    so the fallback path is the default for the test suite — no
    external requests are made.
    """
    chosen = (provider or os.getenv("SETUP_ADVISOR_PROVIDER", DETERMINISTIC)).lower()
    if chosen not in KNOWN_PROVIDERS:
        logger.warning(
            "setup_ai_advisor: unknown SETUP_ADVISOR_PROVIDER=%r; "
            "falling back to deterministic.",
            chosen,
        )
        return DeterministicAdvisor()

    if chosen == DETERMINISTIC:
        return DeterministicAdvisor()

    if chosen == OPENAI:
        api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning(
                "setup_ai_advisor: OPENAI_API_KEY not set; "
                "falling back to deterministic.",
            )
            return DeterministicAdvisor()
        try:
            return OpenAISetupAdvisor(api_key=api_key, model=model)
        except Exception:
            logger.exception(
                "setup_ai_advisor: OpenAISetupAdvisor construction failed; "
                "falling back to deterministic.",
            )
            return DeterministicAdvisor()

    if chosen == ANTHROPIC:
        # Reserved — the adapter ships in a follow-up. Until then
        # we want operators who flip the env var to get a clear
        # log line, not silent breakage.
        logger.warning(
            "setup_ai_advisor: ANTHROPIC adapter is not implemented yet; "
            "falling back to deterministic.",
        )
        return DeterministicAdvisor()

    return DeterministicAdvisor()


__all__ = [
    "ANTHROPIC",
    "DETERMINISTIC",
    "KNOWN_PROVIDERS",
    "OPENAI",
    "OpenAISetupAdvisor",
    "SetupAdvisor",
    "build_advisor",
]
