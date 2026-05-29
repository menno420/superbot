"""Offline AI evals harness (capability tests + OpenAI/Claude scorecard).

The machinery is unit-tested in CI with a fake provider (no API). The real run
is opt-in via ``scripts/run_evals.py`` (needs ``RUN_EVALS=1`` + API keys). See
``tests/evals/README.md``.
"""
