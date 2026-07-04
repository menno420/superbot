"""Golden behavioral harness (Phase 0.5) — black-box capture of the current bot.

Command-in → embed/DB-out golden fixtures, captured from the REAL bot
(``disbot/``) driven in-process through the real discord.py state machine with
a fake HTTP boundary. The current bot is the oracle: this package observes it
verbatim and never changes its behavior.

Integrity rule (design spec §6): these goldens are the acceptance oracle for
the future rebuild. The new repo consumes them **read-only**; golden updates
are explicit, reviewed PRs to THIS repo — neither bot rewrites its own oracle.

Layout:
    parity/harness/   the driver (fake HTTP + gateway payloads + boot + capture)
    parity/cases/     the golden case corpus (typed Python, like tests/evals)
    parity/goldens/   captured fixtures (JSON, deterministic, reviewable)
    parity/run.py     CLI — capture / check / coverage
"""
