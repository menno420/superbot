"""Counting subsystem internals.

Submodules host the parsing/game-logic primitives extracted from the
formerly monolithic cogs/counting_cog.py during D3:

    _constants  — number-word sets, mappings, compiled regex
    parsing     — message → integer pipeline (parse_message and helpers)
    game_logic  — calculate_expected_count, is_prime, sequence helpers

The cog file itself (cogs/counting_cog.py) hosts only Discord plumbing:
commands, listener, lifecycle, and admin helpers.  All business logic
lives in this package and can be tested without instantiating a cog.
"""
