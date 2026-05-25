"""Ninja Kiwi /odyssey parser skeleton (M3B).

Real implementation lands once the response format is captured —
see docs/AGENT_ORIENTATION.md and the refined-direction plan's
M3B open question. Until then the skeleton's parse() raises
raises `ParserNotImplemented` so the M3B
fetch loop cannot silently write empty fact rows.
"""

from __future__ import annotations

from services import btd6_source_parser
from services.parsers._skeleton import NinjaKiwiParserSkeleton

Parser = NinjaKiwiParserSkeleton(source_key="nk_btd6_odyssey")
btd6_source_parser.register(Parser)
