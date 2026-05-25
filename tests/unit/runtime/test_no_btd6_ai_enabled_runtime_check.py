"""M5 pin — BTD6_AI_ENABLED is retired from runtime.

After M5, AI Platform policy + task policy are the gates for BTD6
augmentation; the legacy ``BTD6_AI_ENABLED`` env var must not
appear in any production code path. Mentions in tests are allowed
(legacy regression coverage) and prose mentions in docs / comments
are stripped before the scan.
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DISBOT = _REPO / "disbot"


_FORBIDDEN = re.compile(r"\bBTD6_AI_ENABLED\b")
_LEGACY_OK = {"AI_BTD6_VIA_ROUTER"}


def _strip_comments_and_strings(source: str) -> str:
    """Remove ``# ...`` end-of-line comments and triple-quoted blocks.

    Keeps the rest of the source intact for the regex scan.
    """
    out: list[str] = []
    in_block = False
    block_delim = ""
    for line in source.splitlines():
        if in_block:
            if block_delim in line:
                # Block ends on this line.
                in_block = False
                line = line.split(block_delim, 1)[1]
            else:
                continue
        for delim in ('"""', "'''"):
            if delim in line:
                pre, _, rest = line.partition(delim)
                if delim in rest:
                    # Single-line docstring.
                    out.append(pre)
                    line = rest.split(delim, 1)[1]
                else:
                    out.append(pre)
                    in_block = True
                    block_delim = delim
                    line = ""
                    break
        if "#" in line:
            line = line.split("#", 1)[0]
        out.append(line)
    return "\n".join(out)


def test_no_production_module_reads_btd6_ai_enabled_env():
    offenders: list[str] = []
    for path in _DISBOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        cleaned = _strip_comments_and_strings(source)
        if _FORBIDDEN.search(cleaned):
            offenders.append(str(path.relative_to(_REPO)))
    assert not offenders, (
        "Production code references BTD6_AI_ENABLED — the env var "
        "was retired in M5. Gate on AI Platform task policy + "
        "ai_natural_language_policy instead. "
        f"Offenders: {offenders}"
    )


def test_ai_btd6_via_router_flag_is_also_retired():
    """The short-lived M2 → M5 flag is removed in M5."""
    cog = (_DISBOT / "cogs" / "btd6_cog.py").read_text(encoding="utf-8")
    cleaned = _strip_comments_and_strings(cog)
    assert "AI_BTD6_VIA_ROUTER" not in cleaned, (
        "btd6_cog still reads AI_BTD6_VIA_ROUTER — delete the env "
        "var branch in cog_load and always leave the legacy stage "
        "unregistered."
    )
