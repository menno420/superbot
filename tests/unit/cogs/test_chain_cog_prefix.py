"""Chain cog must show the bot's real prefix (``!``) in usage text.

Regression (audit §9.9): ``chain_cog`` hard-coded ``?chain`` in 9 usage
strings and command docstrings while the bot prefix is ``!``
(``config.PREFIX`` default), so every chain help/usage line told users to
type a command that does not work. The convention across the codebase is
a hard-coded ``!`` (``!platform``, ``!setup``, …); this pins chain to it.
"""

from __future__ import annotations

from pathlib import Path

_CHAIN_COG = Path(__file__).resolve().parents[3] / "disbot" / "cogs" / "chain_cog.py"


def test_chain_cog_uses_bang_prefix_not_question_mark():
    src = _CHAIN_COG.read_text(encoding="utf-8")
    assert "?chain" not in src, "chain_cog must not show the wrong '?' prefix"
    assert "!chain" in src, "chain_cog usage strings should reference !chain"
