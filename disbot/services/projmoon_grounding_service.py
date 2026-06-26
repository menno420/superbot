"""Project Moon (Limbus) answer-faithfulness verifier.

The projmoon analogue of :func:`services.btd6_grounding_service.validate_btd6_reply`:
a ``PROJMOON_ANSWER`` reply must not state distinctive Limbus proper names absent
from the grounded payload (the facts injected by
:mod:`services.projmoon_context_service`). The natural-language stage calls
:func:`validate_projmoon_reply` after the model answers; an unsupported name
triggers a single regenerate-with-constraint, then the deterministic refusal floor.

This realises **Slice A follow-up (b)** of the Project Moon knowledge-domain plan
(``docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md``, Q-0192) — the
prose-faithfulness *validation* guard the plan's §6 calls "the hardest correctness
risk". PR #1467 (Slice A item 2) injected grounded facts but deliberately deferred
this verify step; this module closes that gap.

Design notes:

* **Names-only.** Limbus *exact numbers* aren't ingested yet (Slice A item 1 — the
  StaticData dump), so there is no numeric grounding here, unlike the BTD6 path. The
  committed fixtures are structural/lore prose; the realistic confabulation a guard
  can catch is **misattributing a known Sinner / E.G.O grade**, not inventing a
  numeric stat.
* **Common-word discipline.** Only the *distinctive* proper names are indexed: the
  12 Sinners and the four non-ambiguous E.G.O grade letters. The Sins (``Wrath`` …),
  damage types (``Slash`` …) and statuses (``Burn`` …) are ordinary English words,
  so — exactly like BTD6's bloon colours / generic tower words — they are **not**
  single-token matched (a reply that says "this deals slash damage" must never be
  refused for the word "slash"). This mirrors
  :func:`services.btd6_grounding_service._name_index`.
* **Reuses** the domain-agnostic, stdlib-only :mod:`utils.btd6.name_guard` matchers
  and the shared :class:`services.btd6_grounding_service.GroundingResult` dataclass —
  so when the shared ``KnowledgeDomain`` seam (Slice B) lands, this module and the
  BTD6 grounding service fold onto one renderer with no contract change.

Layering: ``services`` may import ``utils`` and sibling services; this module imports
only :mod:`services.projmoon_data_service`, :mod:`services.btd6_grounding_service`
(for the shared result type), :mod:`core.runtime.ai.contracts`, and ``utils`` —
never cogs / views.
"""

from __future__ import annotations

import logging
import threading

from core.runtime.ai.contracts import PolicyDenialReason
from services import projmoon_data_service
from services.btd6_grounding_service import GroundingResult
from utils.btd6 import name_guard

logger = logging.getLogger("bot.services.projmoon_grounding")

# E.G.O grade canonicals that are distinctive Hebrew-letter tokens safe to match
# whole-word. "HE" is excluded — it is the ordinary English pronoun (the same
# ambiguous-bare-token curation ``projmoon_context_service`` applies); it grounds
# only via its multi-word "he grade" alias.
_AMBIGUOUS_EGO_CANONICALS: frozenset[str] = frozenset({"he"})

_index_lock = threading.Lock()
_NAME_INDEX: name_guard.NameMatchers | None = None


def _name_index() -> name_guard.NameMatchers:
    """Memoized Limbus proper-name matchers built from the committed fixtures.

    Discipline (mirrors :func:`btd6_grounding_service._name_index`):

    * **Sinners** — distinctive proper names; feed every canonical + alias to
      :func:`name_guard.build_matchers`, which keeps single-word forms at the
      router's length thresholds (so "Faust"/"Gregor" match whole-word while the
      generic short aliases "don"/"ish"/"sang" are filtered out) and multi-word
      forms ("Don Quixote", "Yi Sang") as substring phrases.
    * **E.G.O grades** — the four non-ambiguous letters (ZAYIN/TETH/WAW/ALEPH) as
      single tokens, plus the "<grade> grade" aliases as multi-word phrases.
    * **Sins / damage types / statuses** — ordinary English words, **skipped**
      entirely (single-token matching them would false-positive on normal prose).

    Never raises: a fixture-load fault yields an empty index so the guard passes
    (fail-open on a *load* error — see :func:`validate_projmoon_reply`).
    """
    global _NAME_INDEX
    if _NAME_INDEX is not None:
        return _NAME_INDEX
    with _index_lock:
        if _NAME_INDEX is not None:
            return _NAME_INDEX

        canonicals: set[str] = set()
        aliases: set[str] = set()
        try:
            for entry in projmoon_data_service.get_entries("sinner"):
                canonicals.add(entry.canonical)
                aliases.update(entry.aliases)
            for entry in projmoon_data_service.get_entries("ego_grade"):
                if entry.canonical.casefold() not in _AMBIGUOUS_EGO_CANONICALS:
                    canonicals.add(entry.canonical)
                # The "<x> grade" aliases are distinctive multi-word phrases.
                aliases.update(alias for alias in entry.aliases if " " in alias)
        except Exception:
            logger.warning(
                "projmoon_grounding: fixtures unavailable; using empty name index",
                exc_info=True,
            )
            return name_guard.NameMatchers(multi=frozenset(), single=frozenset())

        index = name_guard.build_matchers(canonicals, aliases)
        _NAME_INDEX = index
        return index


def _reset_for_tests() -> None:
    """Clear the memoized name index (call alongside ``projmoon_data_service.reset_cache``)."""
    global _NAME_INDEX
    with _index_lock:
        _NAME_INDEX = None


def validate_projmoon_reply(
    answer_text: str,
    *,
    facts: tuple[str, ...] = (),
) -> GroundingResult:
    """Verify a model-authored Limbus reply against the grounded payload.

    Trusted haystack = the injected grounding ``facts``. A reply is grounded when
    every indexed Limbus proper name it states is present in the haystack. Names
    only — Limbus exact numbers aren't grounded yet.

    On a real unsupported-name finding the result is *not grounded* so the caller
    floors to the refusal (fail closed on a genuine miss). On an internal verifier
    error the result is *grounded* (fail open): a verifier bug must not turn a
    legitimate, lower-stakes Limbus answer into a refusal — unlike the BTD6 numeric
    path, projmoon faithfulness is additive hardening, not a hard safety floor.
    """
    try:
        matchers = _name_index()
        haystack = " ".join(facts)

        allowed_names = name_guard.names_present(haystack, matchers)
        answer_names = name_guard.names_present(answer_text, matchers)
        offending_names = tuple(sorted(answer_names - allowed_names))

        if not offending_names:
            return GroundingResult(
                grounded=True,
                reason_code=PolicyDenialReason.NONE.value,
                used_fact_keys=(),
            )
        return GroundingResult(
            grounded=False,
            reason_code=PolicyDenialReason.GROUNDING_FAILED.value,
            used_fact_keys=(),
            notes=("entity_name_unsupported",),
            offending_names=offending_names,
        )
    except Exception:
        logger.warning(
            "projmoon_grounding: validate_projmoon_reply raised; failing open",
            exc_info=True,
        )
        return GroundingResult(
            grounded=True,
            reason_code=PolicyDenialReason.NONE.value,
            used_fact_keys=(),
            notes=("verifier_error",),
        )


def build_grounding_constraint(verdict: GroundingResult) -> str:
    """A do-not-state constraint appended to the system prompt on the retry."""
    detail = (
        "names not in the data: " + ", ".join(verdict.offending_names)
        if verdict.offending_names
        else "unsupported Limbus claims"
    )
    return (
        "GROUNDING CORRECTION: your previous reply contained "
        f"{detail}. Do NOT state these. Use only Project Moon (Limbus) names "
        "present in the provided data. If the data does not support an answer, "
        "say you don't have that information."
    )


def no_data_refusal() -> str:
    """Deterministic Project Moon refusal — never model prose.

    The single source for the floor string so every projmoon grounding refusal
    reads the same. Never raises.
    """
    return (
        "I don't have verified Project Moon (Limbus) details to answer that "
        "confidently. I won't state Sinner or E.G.O facts I can't ground in my "
        "data — try asking about a specific Sinner (e.g. Faust, Don Quixote) or "
        "one of the E.G.O grades."
    )


__all__ = [
    "build_grounding_constraint",
    "no_data_refusal",
    "validate_projmoon_reply",
]
