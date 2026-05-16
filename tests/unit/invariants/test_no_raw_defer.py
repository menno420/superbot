"""INV-L enforcement — no raw ``interaction.response.defer(`` outside helpers.

Discord interaction tokens expire 3 seconds after the user clicks.
Every handler that defers must go through
``core.runtime.interaction_helpers.safe_defer`` so the recoverable
failure modes (token expired, HTTP error) are swallowed and logged
at WARNING rather than raising mid-handler.

P2 PR-10 introduces this gate after the rollout completes
(PRs 9 and 10).  It catches the regression where a new view or
cog callback uses the raw discord.py API and re-opens the
"Interaction Failed" UX bug that motivated the helper.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Only the helpers module itself is allowed to call defer raw —
# that IS the safe wrapper.
_ALLOWED_PATHS = {
    _DISBOT / "core" / "runtime" / "interaction_helpers.py",
}

_RAW_DEFER_RE = re.compile(r"\binteraction\.response\.defer\s*\(")


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def test_no_raw_interaction_defer_outside_helpers():
    violations: list[str] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        src = path.read_text()
        for line_no, line in enumerate(src.splitlines(), start=1):
            if _RAW_DEFER_RE.search(line):
                violations.append(
                    f"{path.relative_to(_REPO_ROOT)}:{line_no}: {line.strip()}",
                )
    assert not violations, (
        "INV-L violation: raw interaction.response.defer( outside "
        "core/runtime/interaction_helpers.py.\n"
        "Use `await safe_defer(interaction, ...)` instead — it swallows "
        "token-expiry / HTTP errors and returns False so the caller can "
        "bail cleanly.\n" + "\n".join(violations)
    )
