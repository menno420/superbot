"""Natural-language setup wedge — "describe your server, get a proposed plan".

The thin entry that folds an operator's free-form server description into the
existing setup-advisor pipeline (:mod:`services.setup_ai_advisor`). It reuses
that pipeline's structured output + subsystem-schema validation + deterministic
fallback wholesale: the description only adds *intent* signal to the prompt; it
can never extend the mutation surface, because every recommendation is still
re-validated against the live subsystem schema before it surfaces.

Graceful degradation mirrors the rest of the AI stack. With no OpenAI key
(CI / the default ``SETUP_ADVISOR_PROVIDER=deterministic``), :func:`build_advisor`
returns the deterministic name-matcher, which cannot reason about free text — so
the description is simply unused and the snapshot-only plan is returned. A bad
provider, missing key, or advisor error never raises into the caller.

Layering: ``services`` may import ``services`` / ``core`` / ``utils`` /
``governance``. This module imports only sibling services, so it stays clear of
the views/cogs layers (the command surface lives in ``cogs/setup``).
"""

from __future__ import annotations

from services.guild_snapshot import GuildSnapshot
from services.setup_ai_advisor import (
    OpenAISetupAdvisor,
    SetupAdvisor,
    build_advisor,
)
from services.setup_plan import SetupPlanDraft


async def suggest_from_description(
    snapshot: GuildSnapshot,
    description: str,
    *,
    advisor: SetupAdvisor | None = None,
    provider: str | None = None,
) -> SetupPlanDraft:
    """Produce a setup plan from a guild snapshot plus a free-form description.

    *advisor* is injectable for tests; otherwise the configured advisor is
    resolved via :func:`services.setup_ai_advisor.build_advisor`. When the
    resolved advisor is the OpenAI adapter and a non-empty description is
    given, the description is folded into the prompt
    (:meth:`OpenAISetupAdvisor.suggest_with_description`); otherwise the plain
    snapshot-only :meth:`~SetupAdvisor.suggest` runs — the deterministic
    fallback has no way to use free text, so the description is dropped rather
    than faked.

    Returns a :class:`SetupPlanDraft`; whether the description was actually
    used is observable via ``draft.source`` (``"openai"`` vs ``"deterministic"``).
    """
    text = (description or "").strip()
    resolved = advisor if advisor is not None else build_advisor(provider)
    if isinstance(resolved, OpenAISetupAdvisor) and text:
        return await resolved.suggest_with_description(snapshot, text)
    return await resolved.suggest(snapshot)


__all__ = ["suggest_from_description"]
