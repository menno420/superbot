"""Absence-claim contradiction guard — BTD6 faithfulness Layer B (first slice).

The faithfulness verifier (``services.btd6_grounding_service.validate_btd6_reply``)
catches ungrounded **positives**: a name or number the reply states that the
grounded payload does not contain. It does **not** catch a false **negative** — a
reply can fluently, confidently assert *"<tower> has no paragon"* when the
committed data (and the grounded facts in front of the model that very turn) say
it does. A fluent false "no" is worse than a refusal: it looks authoritative and
the user believes it. The canonical repro is the design doc's Update 2 — *"Monkey
Buccaneer does not have a paragon"* (it has Navarch of the Seas, and the grounding
emitted that fact). See ``docs/btd6/btd6-absence-claim-guard-design.md`` §1.

This is the **grounded-contradiction** slice of Layer B (design §4.2 step 3): it
rejects an absence claim **only when the grounded haystack affirms the very thing
the reply denies**. By construction it can never block a *true* negative — a true
"X has no paragon" has no contradicting positive in the grounding, so nothing
fires. The harder §4.3 half (downgrading a "no" about a subject that never
*resolved*, where Layer A shrinks the trigger) needs the live false-positive-rate
check and stays a follow-up.

Seeded with the **paragon-existence** attribute (the documented repro). The
:data:`_ATTRIBUTES` table is the extension point: add a clean existence-attribute
with (a) a regex that reads the subject the grounding *affirms* has it and (b) the
sentence patterns that *deny* it — then live-verify before trusting it.

UNVERIFIED convenience guard (Q-0105, 2026-06-27): the deny patterns are
deliberately tight (negation adjacent to the attribute word) to keep false floors
near-zero, and a contradicted claim only costs one regeneration before the
deterministic refusal. If it proves noisy across sessions, narrow the patterns or
delete this guard rather than working around it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Sentence splitter — good enough for model prose (split after . ? ! + space).
_SENTENCE_SPLIT = re.compile(r"(?<=[.?!])\s+")


@dataclass(frozen=True)
class _ExistenceAttribute:
    """One binary "does <subject> have <attribute>?" fact the gate can check."""

    name: str
    # Reads, from the grounded haystack, the subject(s) the data AFFIRMS have this
    # attribute. Group 1 = the subject's proper name (e.g. "Monkey Buccaneer").
    affirm_re: re.Pattern[str]
    # A sentence matching any of these (case-insensitively) DENIES the attribute.
    deny_res: tuple[re.Pattern[str], ...]
    # Words that turn a "no <attr>" into a non-absence ("no SECOND paragon"); a
    # sentence containing one is skipped even if a deny pattern matched.
    exclude_qualifiers: frozenset[str]


# Apostrophe class covers the straight ' and the curly ' a model may emit.
_APOS = r"['’]"

_PARAGON = _ExistenceAttribute(
    name="paragon",
    # Both grounded paragon lines affirm the owning tower: the headline form
    # (Monkey Buccaneer ... Paragon is Navarch) and the descriptive form
    # (Navarch ... the Monkey Buccaneer Paragon, fusing ...).
    affirm_re=re.compile(
        r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+)*)" + _APOS + r"s Paragon\b",
    ),
    deny_res=(
        # "no paragon", "no monkey buccaneer paragon" (<=2 words between)
        re.compile(r"\bno\s+(?:\w+\s+){0,2}paragon\b"),
        # "does not have a paragon", "doesn't have a paragon"
        re.compile(
            r"\b(?:does\s+not|doesn" + _APOS + r"?t|do\s+not|don" + _APOS + r"?t)"
            r"\s+have\s+(?:a\s+|an\s+|any\s+)?(?:\w+\s+){0,2}paragon\b",
        ),
        # "lacks a paragon", "lack a paragon"
        re.compile(r"\blacks?\s+(?:a\s+|an\s+|any\s+)?(?:\w+\s+){0,2}paragon\b"),
        # "without a paragon"
        re.compile(r"\bwithout\s+(?:a\s+|an\s+|any\s+)?(?:\w+\s+){0,2}paragon\b"),
        # "paragon does not exist / doesn't exist / is not available"
        re.compile(
            r"\bparagon\b(?:\s+\w+){0,3}\s+(?:does\s+not|doesn" + _APOS + r"?t)"
            r"\s+exist\b",
        ),
        re.compile(
            r"\bparagon\b(?:\s+\w+){0,3}\s+(?:is\s+not|isn" + _APOS + r"?t)"
            r"\s+available\b",
        ),
    ),
    exclude_qualifiers=frozenset({"second", "another", "additional", "other", "more"}),
)

_ATTRIBUTES: tuple[_ExistenceAttribute, ...] = (_PARAGON,)


def contradicted_absence_claims(answer_text: str, haystack: str) -> tuple[str, ...]:
    """Return the reply sentences that deny an attribute the grounding affirms.

    ``answer_text`` is the model's draft reply; ``haystack`` is the joined
    grounded payload (auto-grounding facts ∪ approved tool results) — the same
    haystack the positive faithfulness check uses. The result is empty unless the
    reply makes a grounding-**contradicted** absence claim (so a true "no", or any
    absence about a subject the grounding never affirmed, returns nothing).
    """
    if not answer_text or not haystack:
        return ()

    offending: list[str] = []
    sentences = _SENTENCE_SPLIT.split(answer_text)
    for attr in _ATTRIBUTES:
        affirmed = {m.group(1).lower() for m in attr.affirm_re.finditer(haystack)}
        if not affirmed:
            continue
        for sentence in sentences:
            low = sentence.lower()
            if not any(pat.search(low) for pat in attr.deny_res):
                continue
            if any(q in low for q in attr.exclude_qualifiers):
                continue
            if any(subject in low for subject in affirmed):
                offending.append(sentence.strip())

    # Preserve order, drop duplicates.
    return tuple(dict.fromkeys(offending))


__all__ = ["contradicted_absence_claims"]
