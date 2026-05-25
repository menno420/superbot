"""AI Behavior preset orchestration (PR-B).

A thin service on top of the existing instruction / policy mutation
chokepoints. Presets live as seeded ``ai_instruction_profile`` rows
(migration 044) with ``is_preset = TRUE`` and ``guild_id IS NULL``;
this service reads them through :mod:`utils.db.ai`, and binds a
preset's id into a scope's policy through
:mod:`services.ai_policy_mutation`. No new write path is introduced.

Each preset implies a channel-mode (always_reply / mention_only /
disabled) — that mapping lives in :data:`_PRESET_CATALOG` so the
service can return it to the UI without a second DB lookup. The
catalog keys must match the seed rows in migration 044; the service
asserts this on first call.

Scopes supported by :func:`apply_preset`:

* ``channel``  — binds the preset id into ``ai_channel_policy``
* ``category`` — binds the preset id into ``ai_category_policy``

The guild scope is intentionally out of scope: ``set_guild_policy``
takes a holistic snapshot of every guild-policy field, so an
operator who wants to point the guild baseline at a preset uses the
existing guild-scope modal. PR-C-pre's ``UNCHANGED`` sentinel will
unlock a future ``apply_preset_to_guild`` helper if needed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from services import ai_policy_mutation
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_behavior_profile")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class BehaviorPresetError(Exception):
    pass


class UnknownBehaviorPresetError(BehaviorPresetError):
    pass


class InvalidBehaviorPresetScopeError(BehaviorPresetError):
    pass


# ---------------------------------------------------------------------------
# Catalog metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BehaviorPresetCatalogEntry:
    """In-process metadata for a built-in preset.

    The DB row provides the id, name, and body; this dataclass adds
    the recommended channel/category mode and a short headline used
    by the UI.
    """

    key: str
    headline: str
    recommended_mode: Literal["always_reply", "mention_only", "disabled"]


_PRESET_CATALOG: dict[str, BehaviorPresetCatalogEntry] = {
    "disabled": BehaviorPresetCatalogEntry(
        key="disabled",
        headline="No AI replies in this scope",
        recommended_mode="disabled",
    ),
    "mention_only_helper": BehaviorPresetCatalogEntry(
        key="mention_only_helper",
        headline="Concise replies when mentioned",
        recommended_mode="mention_only",
    ),
    "helpful_channel": BehaviorPresetCatalogEntry(
        key="helpful_channel",
        headline="Full natural-language behavior",
        recommended_mode="always_reply",
    ),
    "btd6_focused": BehaviorPresetCatalogEntry(
        key="btd6_focused",
        headline="BTD6 grounding prioritised",
        recommended_mode="always_reply",
    ),
    "quiet_btd6_focused": BehaviorPresetCatalogEntry(
        key="quiet_btd6_focused",
        headline="BTD6 grounding, mention-only",
        recommended_mode="mention_only",
    ),
    "staff_diagnostics": BehaviorPresetCatalogEntry(
        key="staff_diagnostics",
        headline="Operator diagnostics, mention-only",
        recommended_mode="mention_only",
    ),
    "support_triage": BehaviorPresetCatalogEntry(
        key="support_triage",
        headline="Neutral support triage",
        recommended_mode="mention_only",
    ),
}


PRESET_KEYS: frozenset[str] = frozenset(_PRESET_CATALOG.keys())


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BehaviorPresetSummary:
    """UI-friendly summary of one preset row + its catalog metadata."""

    preset_id: int
    key: str
    headline: str
    recommended_mode: str
    body: str


@dataclass(frozen=True)
class BehaviorApplyResult:
    """Returned by :func:`apply_preset` so the UI can render confirmation."""

    scope: str
    target_id: int
    preset_id: int
    preset_key: str
    recommended_mode: str
    policy_mutation_id: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_SUPPORTED_SCOPES: frozenset[str] = frozenset({"channel", "category"})


async def list_presets() -> list[BehaviorPresetSummary]:
    """Return every seeded preset, joined with its catalog metadata."""
    rows = await ai_db.list_preset_profiles()
    out: list[BehaviorPresetSummary] = []
    for row in rows:
        meta = _PRESET_CATALOG.get(row["name"])
        if meta is None:
            # A DB row we don't recognise — surface it with a fallback
            # entry rather than dropping it, so a stale catalog never
            # silently hides presets from operators.
            meta = BehaviorPresetCatalogEntry(
                key=row["name"],
                headline=f"(uncatalogued preset {row['name']!r})",
                recommended_mode="mention_only",
            )
        out.append(
            BehaviorPresetSummary(
                preset_id=int(row["id"]),
                key=row["name"],
                headline=meta.headline,
                recommended_mode=meta.recommended_mode,
                body=row["body"],
            ),
        )
    return out


async def describe_preset(preset_id: int) -> BehaviorPresetSummary | None:
    """Return one preset by id, or ``None`` if it does not exist /
    is not flagged ``is_preset``.
    """
    row = await ai_db.get_instruction_profile(preset_id)
    if row is None or not row.get("is_preset"):
        return None
    meta = _PRESET_CATALOG.get(row["name"]) or BehaviorPresetCatalogEntry(
        key=row["name"],
        headline=f"(uncatalogued preset {row['name']!r})",
        recommended_mode="mention_only",
    )
    return BehaviorPresetSummary(
        preset_id=int(row["id"]),
        key=row["name"],
        headline=meta.headline,
        recommended_mode=meta.recommended_mode,
        body=row["body"],
    )


async def apply_preset(
    *,
    guild_id: int,
    scope: str,
    target_id: int,
    preset_id: int,
    actor: Any,
) -> BehaviorApplyResult:
    """Bind a preset id into the matching policy scope.

    ``scope`` must be one of :data:`_SUPPORTED_SCOPES`. The preset's
    recommended mode and the preset id are written; other optional
    columns (``min_level``, ``cooldown_seconds``) are passed as
    :data:`ai_policy_mutation.UNCHANGED` so any existing per-scope
    overrides are preserved across preset applies.
    """
    if scope not in _SUPPORTED_SCOPES:
        raise InvalidBehaviorPresetScopeError(
            f"scope must be one of {sorted(_SUPPORTED_SCOPES)}, got {scope!r}",
        )

    summary = await describe_preset(preset_id)
    if summary is None:
        raise UnknownBehaviorPresetError(
            f"preset_id={preset_id} not found or not flagged is_preset=True",
        )

    if scope == "channel":
        result = await ai_policy_mutation.set_channel_policy(
            guild_id,
            target_id,
            mode=summary.recommended_mode,
            min_level=ai_policy_mutation.UNCHANGED,
            cooldown_seconds=ai_policy_mutation.UNCHANGED,
            instruction_profile_id=preset_id,
            actor=actor,
        )
    else:  # scope == "category"
        result = await ai_policy_mutation.set_category_policy(
            guild_id,
            target_id,
            mode=summary.recommended_mode,
            min_level=ai_policy_mutation.UNCHANGED,
            cooldown_seconds=ai_policy_mutation.UNCHANGED,
            instruction_profile_id=preset_id,
            actor=actor,
        )

    return BehaviorApplyResult(
        scope=scope,
        target_id=target_id,
        preset_id=preset_id,
        preset_key=summary.key,
        recommended_mode=summary.recommended_mode,
        policy_mutation_id=result.mutation_id,
    )


__all__ = [
    "BehaviorApplyResult",
    "BehaviorPresetCatalogEntry",
    "BehaviorPresetError",
    "BehaviorPresetSummary",
    "InvalidBehaviorPresetScopeError",
    "PRESET_KEYS",
    "UnknownBehaviorPresetError",
    "apply_preset",
    "describe_preset",
    "list_presets",
]
