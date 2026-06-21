"""Parse a free-text emoji string into individual emotes.

The reaction-role **Add** panel lets an operator bind *several* emotes to one
message in a single step, each emote getting its own role (owner direction,
2026-06-21). To do that we have to turn what the operator typed — ``"🎮"`` or
``"💀 ❤️ 😘"`` or even ``"💀❤️😘"`` jammed together — into a clean ordered list
of distinct emotes.

Pure stdlib (``re`` only) so it can live in ``utils/`` and be imported by any
view without crossing a layer boundary; covered by
``tests/unit/utils/test_emoji_tokens.py``.

The hard part is splitting *adjacent* unicode emoji with no separators. We do it
conservatively: a token is only split into clusters when those clusters
reconstruct the token **exactly** (``"".join(parts) == token``). If they don't —
a ZWJ family emoji we don't fully model, an arbitrary word — the token is kept
whole rather than risk silently dropping or corrupting characters. ZWJ
sequences, variation selectors (``U+FE0F``), skin-tone modifiers and keycap
combiners are kept attached to their base, so a multi-codepoint emoji stays one
emote.
"""

from __future__ import annotations

import re

# Discord custom emoji: <:name:id> or <a:name:id> (animated). Matched first and
# kept whole — they never contain whitespace, so they survive the split cleanly.
_CUSTOM_EMOJI = re.compile(r"<a?:[A-Za-z0-9_]{2,32}:\d{15,25}>")

# Codepoint ranges that cover the vast majority of standalone unicode emoji.
# Deliberately broad — correctness is guaranteed by the exact-reconstruction
# guard in :func:`_split_run`, not by the range being perfectly tight. Written as
# explicit escapes (the chars are otherwise invisible/ambiguous in source).
_PICTO = (
    "\U0001f000-\U0001faff"  # emoticons, symbols & pictographs, transport,
    #                          supplemental, extended-A, mahjong/dominoes/cards
    "←-⇿"  # arrows
    "⌀-⏿"  # technical (watch / hourglass / keyboard …)
    "■-◿"  # geometric shapes
    "☀-➿"  # misc symbols + dingbats
    "⬀-⯿"  # misc symbols & arrows
    "⤴⤵〰〽㊗㊙"  # stray symbols Discord renders as emoji
)
# Modifiers that attach to a preceding base: VS15/VS16 variation selectors,
# Fitzpatrick skin tones, and the keycap combining enclosing mark.
_MOD = "︎️\U0001f3fb-\U0001f3ff⃣"
_ZWJ = "‍"
# One emote grapheme: a base, its modifiers, and any ZWJ-joined continuations.
_CLUSTER = re.compile(
    f"[{_PICTO}][{_MOD}]*(?:{_ZWJ}[{_PICTO}][{_MOD}]*)*",
)


def _split_run(token: str) -> list[str]:
    """Split a whitespace-free run into emoji clusters, or keep it whole.

    Only splits when the clusters reconstruct the token exactly — otherwise the
    token is returned unchanged so we never drop or mangle what the operator
    typed (a non-emoji word, or an emoji sequence we don't fully model).
    """
    clusters = _CLUSTER.findall(token)
    if clusters and "".join(clusters) == token:
        return clusters
    return [token]


def parse_emotes(raw: str) -> list[str]:
    """Return the ordered, de-duplicated list of emotes in ``raw``.

    Handles single emotes, whitespace-separated emotes, adjacent emotes with no
    separator, and Discord custom ``<:name:id>`` emoji. Order is preserved and
    duplicates are dropped (binding the same emote twice in one add is a no-op).
    """
    if not raw or not raw.strip():
        return []

    emotes: list[str] = []

    # Pull out custom emoji first (they carry digits/colons the unicode splitter
    # would mishandle), preserving their position via re.split.
    parts = _CUSTOM_EMOJI.split(raw)
    customs = _CUSTOM_EMOJI.findall(raw)
    for i, part in enumerate(parts):
        for token in part.split():
            emotes.extend(_split_run(token))
        if i < len(customs):
            emotes.append(customs[i])

    # De-dupe while preserving first-seen order.
    seen: set[str] = set()
    ordered: list[str] = []
    for emote in emotes:
        if emote and emote not in seen:
            seen.add(emote)
            ordered.append(emote)
    return ordered


__all__ = ["parse_emotes"]
