"""Put ``substrate-kit/src`` on sys.path so the engine imports as ``engine.*``.

The kit lives in its own top-level tree; during the in-repo proving phase its
tests run from here (superbot's collected ``tests/``). On extraction these move
into ``substrate-kit/tests/`` and this path insert is dropped.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3] / "substrate-kit" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
