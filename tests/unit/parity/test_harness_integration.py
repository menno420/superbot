"""Full-boot capture round-trip — opt-in (heavy: boots the real bot).

Gated behind ``PARITY_INTEGRATION=1`` AND a reachable ``DATABASE_URL``:
importing ``bot1`` installs process-global handlers and the harness
truncates the database per case, so this must never run implicitly inside
the normal suite. The CLI (`python3.10 -m parity.run`) is the primary
runnable; this test exists so `pytest` can prove the round-trip on demand:

    PARITY_INTEGRATION=1 python3.10 -m pytest \
        tests/unit/parity/test_harness_integration.py -v
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytestmark = pytest.mark.skipif(
    os.environ.get("PARITY_INTEGRATION") != "1" or not os.environ.get("DATABASE_URL"),
    reason="opt-in: PARITY_INTEGRATION=1 + DATABASE_URL (boots the real bot, "
    "truncates the database)",
)


async def test_capture_then_replay_is_deterministic():
    from parity.cases import CURATED_CASES
    from parity.harness.boot import Harness
    from parity.harness.runner import capture_case

    harness = await Harness.start()
    try:
        case = next(c for c in CURATED_CASES if c.id == "karma.thanks_grant")
        first = await capture_case(harness, case)
        second = await capture_case(harness, case)
        assert first == second
        # the golden observed the real seam end-to-end
        step_events = [e["event"] for e in first["steps"][0].get("events", [])]
        assert "karma.granted" in step_events
        assert "karma" in first["db_delta"]
    finally:
        await harness.close()
