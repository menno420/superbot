"""Game-mode arithmetic for the counting game.

Pure functions, no Discord or DB dependencies — testable in isolation.
"""

from __future__ import annotations

import math


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
        expected = current_count + channel_data.get("step", 1)
        while expected in channel_data.get("skip_numbers", []):
            expected += channel_data.get("step", 1)
        return expected
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
