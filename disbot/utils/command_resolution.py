"""Fuzzy command resolution — typo / near-miss correction.

When a user mistypes a prefix command (``!serverstas`` instead of
``!serverstats``), the bot's ``CommandNotFound`` handler consults this
module to decide whether to **auto-run** the intended command, merely
**suggest** it ("did you mean …?"), or stay silent.

Design contract (see the PR that introduced this module):

* **Capitals are NOT handled here.**  ``commands.Bot(case_insensitive=True)``
  resolves case variants at the source, so anything reaching this module
  is a genuinely unknown token.
* **Auto-run is gated twice.**  A command is eligible for silent
  auto-correction only if it is *lexically isolated* (no other command or
  alias is a close match — :func:`derive_auto_correct_set`) **and** not in
  :data:`DESTRUCTIVE_COMMANDS`.  Isolation alone is not enough: a mistaken
  ``!ban`` is irreversible even when "ban" is far from every other token.
* **Ambiguous matches always suggest.**  If a second *different* command
  scores within :data:`_AMBIGUITY_DELTA` of the best match, we never
  auto-run — the user might have meant either.

This module is pure (stdlib :mod:`difflib` only) so it respects the
``utils/ → stdlib + discord`` layer rule and is trivially unit-testable.
The live command/alias inventory is built by the caller (the composition
root) and passed in as a ``token -> canonical-command`` mapping.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from enum import Enum

# Commands that must never be auto-executed from a guessed token,
# regardless of lexical isolation: a mistaken invocation is destructive,
# irreversible, or otherwise high-impact.  These always fall through to a
# suggestion.  Keep this list conservative — when in doubt, add the name.
DESTRUCTIVE_COMMANDS: frozenset[str] = frozenset(
    {
        "ban",
        "unban",
        "kick",
        "clear",
        "purge",
        "timeout",
        "untimeout",
        "warn",
        "createrole",
        "deleterole",
        "assignroles",
        "givexp",
        "resetxp",
        "restart",
        "cleanuphistory",
        "word",
    },
)

# Minimum SequenceMatcher ratio for a token to be considered a candidate.
# Matches the in-repo precedent in cogs/counting/parsing.py.
_DEFAULT_CUTOFF = 0.8

# Auto-run is reserved for names long enough that a fuzzy match is
# meaningful.  Short names ("bj", "rps", "21") are inherently
# collision-prone and stay suggestion-only.
_MIN_AUTO_LEN = 4

# A runner-up that scores within this margin of the best match — and maps
# to a *different* command — makes the match ambiguous (suggest, never
# auto-run).
_AMBIGUITY_DELTA = 0.08


class Outcome(Enum):
    """What the error handler should do with a near-miss token."""

    AUTO = "auto"  # re-dispatch the corrected command silently (with a note)
    SUGGEST = "suggest"  # show "did you mean …?"
    NONE = "none"  # no close match; fall through to generic not-found


@dataclass(frozen=True)
class Resolution:
    outcome: Outcome
    command: str | None = None


def _ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def derive_auto_correct_set(
    token_to_command: dict[str, str],
    *,
    destructive: frozenset[str] = DESTRUCTIVE_COMMANDS,
    cutoff: float = _DEFAULT_CUTOFF,
    min_len: int = _MIN_AUTO_LEN,
) -> frozenset[str]:
    """Derive the set of canonical commands eligible for silent auto-run.

    A canonical command qualifies iff:

    * it is at least *min_len* characters long,
    * it is not in *destructive*, and
    * it is *lexically isolated* — no token that resolves to a **different**
      command is a close match (``cutoff``).

    *token_to_command* maps every known token (command names AND aliases AND
    synonyms) to its canonical command name.  Comparing against aliases of
    *other* commands — not just their primary names — is deliberate: it is
    how we catch "this typo could plausibly be a different command".
    """
    canonical_names = set(token_to_command.values())
    eligible: set[str] = set()
    for name in canonical_names:
        if len(name) < min_len or name in destructive:
            continue
        others = [tok for tok, owner in token_to_command.items() if owner != name]
        if not difflib.get_close_matches(name, others, n=1, cutoff=cutoff):
            eligible.add(name)
    return frozenset(eligible)


def classify(
    raw: str,
    token_to_command: dict[str, str],
    auto_set: frozenset[str],
    *,
    cutoff: float = _DEFAULT_CUTOFF,
    ambiguity_delta: float = _AMBIGUITY_DELTA,
) -> Resolution:
    """Classify an unknown command token into AUTO / SUGGEST / NONE.

    *auto_set* is the output of :func:`derive_auto_correct_set` for the same
    *token_to_command* mapping.
    """
    token = raw.lower().strip()
    if not token:
        return Resolution(Outcome.NONE)

    # Exact known token (a synonym or alias that simply isn't a live command
    # name): high confidence, route purely on auto-set membership.
    if token in token_to_command:
        cmd = token_to_command[token]
        return Resolution(Outcome.AUTO if cmd in auto_set else Outcome.SUGGEST, cmd)

    scored = sorted(
        (
            (_ratio(token, candidate), candidate)
            for candidate in token_to_command
            if _ratio(token, candidate) >= cutoff
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not scored:
        return Resolution(Outcome.NONE)

    best_score, best_token = scored[0]
    best_cmd = token_to_command[best_token]

    # Ambiguity guard: a near-tied runner-up pointing at a *different*
    # command means we cannot safely guess — suggest instead.
    for score, other_token in scored[1:]:
        if (
            token_to_command[other_token] != best_cmd
            and (best_score - score) <= ambiguity_delta
        ):
            return Resolution(Outcome.SUGGEST, best_cmd)

    return Resolution(
        Outcome.AUTO if best_cmd in auto_set else Outcome.SUGGEST,
        best_cmd,
    )
