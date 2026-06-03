"""Pure deterministic embed builder for BTD6 answers.

Renders the **code-grounded** facts the faithfulness verifier already validated
the reply against into a compact embed, stamped with the served game version.
The model's (verified, redacted) prose becomes the description; the digits and
names in the data block come from the grounding facts, not the model — so the
formatter is a defense *separate* from the verifier (acceptance criterion c).

Returns ``None`` when there is nothing deterministic to anchor, so the stage
falls through to the plain-text path for conversational BTD6 replies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import discord

from utils.btd6 import grounding_format

# The grounding prepends an internal provenance tag ("[btd6_tower] …") that is
# not meant for users; strip it before display.
_SOURCE_TAG_RE = re.compile(r"^\[btd6_[a-z0-9_]*\]\s*")

_MAX_FACT_LINES = 10
_MAX_FIELD_CHARS = 1000
_MAX_DESC_CHARS = 3500


@dataclass(frozen=True)
class BTD6RenderContext:
    """Deterministic render payload threaded via ``FeatureFactsResult``."""

    facts: tuple[str, ...]
    game_version: str


def _clean_fact(line: str) -> str:
    return grounding_format.sanitise(_SOURCE_TAG_RE.sub("", line or ""), cap=200)


def build_answer_embed(reply_text: str, ctx: BTD6RenderContext) -> discord.Embed | None:
    """Build the verified-data embed, or ``None`` when there is nothing to show."""
    cleaned = [c for c in (_clean_fact(fact) for fact in ctx.facts) if c]
    if not cleaned:
        return None

    description = grounding_format.sanitise(reply_text, cap=_MAX_DESC_CHARS)
    embed = discord.Embed(description=description or None)

    shown = cleaned[:_MAX_FACT_LINES]
    block = "\n".join(f"• {line}" for line in shown)
    if len(block) > _MAX_FIELD_CHARS:
        block = block[: _MAX_FIELD_CHARS - 1].rstrip() + "…"

    label = "Verified data"
    if len(cleaned) > len(shown):
        label = f"Verified data (showing {len(shown)} of {len(cleaned)})"
    embed.add_field(name=label, value=block, inline=False)

    version = ctx.game_version or "the current version"
    embed.set_footer(text=f"BTD6 {version} · grounded data")
    return embed


__all__ = ["BTD6RenderContext", "build_answer_embed"]
