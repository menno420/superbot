"""Top-level test configuration.

Sets required environment variables before any disbot imports happen,
then validates and freezes the subsystem registry once per session.
All test subdirectories inherit this setup automatically.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Must be set before importing config.py, which validates at import time.
os.environ.setdefault("DISCORD_BOT_TOKEN_PRODUCTION", "TEST_TOKEN_PLACEHOLDER")

_DISBOT = Path(__file__).parent / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


@pytest.fixture(scope="session", autouse=True)
def validated_registry():
    """Validate and deep-freeze the real subsystem registry once per session."""
    from utils.subsystem_registry import validate_registry

    validate_registry()
