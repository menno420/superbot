"""Game-mode arithmetic for the counting game.

Pure functions, no Discord or DB dependencies — testable in isolation.
"""

from __future__ import annotations

import math
import random


def calculate_expected_count(
    channel_data: dict,
    current_count: int,
    mode: str,
) -> int | None:
    """Return the next expected count for *channel_data* under *mode*.

    Falls back to ``current_count + step`` for the default ``normal``,
    ``multiples``, and ``prime`` modes.  ``custom`` mode returns
    ``None`` once the configured sequence is exhausted.
    """
    if mode == "reverse":
        return current_count - channel_data.get("step", 1)
    if mode == "skip":
        # "skip N": the count climbs by N each step, anchored at 1 —
        # 1, 1+N, 1+2N, …  (e.g. ``!start_match skip 5`` → 1, 6, 11, 16).
        # N is stored as ``step``; the first valid number is always 1.
        step = channel_data.get("step", 1)
        if current_count < 1:
            return 1
        return current_count + step
    if mode == "random":
        # Use the pre-rolled value so it doesn't change between calls.
        return channel_data.get("next_expected", current_count + 1)
    if mode == "fibonacci":
        a, b = 0, 1
        for _ in range(channel_data.get("sequence_index", 0) + 1):
            a, b = b, a + b
        return a
    if mode == "squares":
        index = channel_data.get("sequence_index", 0) + 1
        return index**2
    if mode == "cubes":
        index = channel_data.get("sequence_index", 0) + 1
        return index**3
    if mode == "factorials":
        index = channel_data.get("sequence_index", 0) + 1
        return math.factorial(index)
    if mode == "custom":
        sequence = channel_data.get("custom_sequence", [])
        index = channel_data.get("sequence_index", 0)
        return sequence[index] if index < len(sequence) else None
    # normal, multiples, prime — simple step increment.
    return current_count + channel_data.get("step", 1)


def is_prime(number: int) -> bool:
    """Check whether *number* is prime (positive integers only)."""
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False
    return all(number % i != 0 for i in range(3, int(number**0.5) + 1, 2))


# ---------------------------------------------------------------------------
# Random mode — "guess the secret number in a shrinking range"
# ---------------------------------------------------------------------------
# The bot rolls a secret target above the current count and announces a wide
# window that contains it.  Each wrong guess halves the window toward the
# target (never below a width of 10); a correct guess advances the count and
# rolls a fresh target + window.  The target sits at a random (non-centred)
# position inside the window so it can't be solved by always guessing the
# midpoint.
_RANDOM_MIN_GAP = 10  # smallest announced range width
_RANDOM_MIN_JUMP = 10  # target is at least this far above the current count
_RANDOM_MAX_JUMP = 60  # ...and at most this far
_RANDOM_MIN_INIT_GAP = 30  # initial window is wide and randomly sized
_RANDOM_MAX_INIT_GAP = 180


def _random_window(target: int, width: int, *, floor: int) -> tuple[int, int]:
    """A window of ``max(width, 10)`` containing *target* at a random
    position, with the low bound never below *floor*.
    """
    width = max(_RANDOM_MIN_GAP, width)
    lo_min = max(floor, target - width)
    lo = random.randint(lo_min, target) if lo_min < target else target
    hi = lo + width
    if hi < target:  # safety — keep the target strictly inside the window
        hi = target
    return lo, hi


def start_random_round(current_count: int) -> tuple[int, int, int]:
    """Roll a fresh secret target above *current_count* plus its initial
    (wide, randomly sized) window.  Returns ``(target, range_lo, range_hi)``.
    """
    target = current_count + random.randint(_RANDOM_MIN_JUMP, _RANDOM_MAX_JUMP)
    width = random.randint(_RANDOM_MIN_INIT_GAP, _RANDOM_MAX_INIT_GAP)
    lo, hi = _random_window(target, width, floor=current_count + 1)
    return target, lo, hi


def narrow_random_range(
    range_lo: int,
    range_hi: int,
    target: int,
) -> tuple[int, int]:
    """Halve the announced window toward *target* after a wrong guess,
    never below a width of 10.  Returns the new ``(range_lo, range_hi)``.
    """
    width = max(_RANDOM_MIN_GAP, (range_hi - range_lo) // 2)
    return _random_window(target, width, floor=0)
