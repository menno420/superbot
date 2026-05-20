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
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

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


class OpenAISetupAdvisor:
    """OpenAI structured-output adapter.

    Construction is lazy: the SDK + API key are resolved on first
    use so a session that never invokes the advisor never pulls in
    the dependency.
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

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # noqa: BLE001 — import boundary
            raise RuntimeError(
                "openai package not installed; install ``openai>=1.40.0`` or "
                "set SETUP_ADVISOR_PROVIDER=deterministic.",
            ) from exc
        api_key = self._api_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set; cannot build OpenAISetupAdvisor.",
            )
        self._client = AsyncOpenAI(api_key=api_key)
        return self._client

    async def suggest(self, snapshot: GuildSnapshot) -> SetupPlanDraft:
        client = self._ensure_client()
        user_payload = json.dumps(_snapshot_to_prompt(snapshot), default=str)
        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_payload},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": _RECOMMENDATION_JSON_SCHEMA,
                },
            )
        except Exception as exc:  # noqa: BLE001 — network boundary
            logger.exception(
                "OpenAISetupAdvisor.suggest: chat.completions.create failed; "
                "falling back to empty draft.",
            )
            return SetupPlanDraft(
                recommendations=(),
                dropped=(f"openai: {type(exc).__name__}: {exc}",),
                source=OPENAI,
            )

        raw = _extract_response_text(response)
        if raw is None:
            return SetupPlanDraft(
                recommendations=(),
                dropped=("openai: empty response",),
                source=OPENAI,
            )

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            return SetupPlanDraft(
                recommendations=(),
                dropped=(f"openai: invalid JSON ({exc})",),
                source=OPENAI,
            )

        return _validate_ai_payload(parsed)


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


def _extract_response_text(response: Any) -> str | None:
    """Pull the assistant message text out of an OpenAI ChatCompletion."""
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if not content:
        return None
    return content


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
