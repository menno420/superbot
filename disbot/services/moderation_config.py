"""Moderation policy — the config read model applied at the mutation seam.

PR10 (server-management) makes moderation **first-class configurable**.
Rather than scatter ``resolve_value`` reads across the cog and the seven
modals (the call-site-guard anti-pattern PR1 fixed for the audit fan-out),
the behaviour policy is loaded **once inside**
:mod:`services.moderation_service` so every current and future caller — the
prefix commands, the panel modals, and the eventual Server-Management hub —
gets identical behaviour.  This module owns:

* the canonical **default constants** (one source of truth shared by the
  :class:`SettingSpec` declarations in ``cogs/moderation/schemas.py`` and
  by :func:`load_policy`'s fallbacks);
* :class:`ModerationPolicy`, the frozen read model;
* :func:`load_policy`, which composes the typed values via
  :func:`services.settings_resolution.resolve_value`;
* :func:`render_dm_message`, the **pure** (no Discord I/O) renderer for the
  optional notify-the-member DM.

The settings themselves are stored as ordinary scalar guild settings (the
legacy KV table); there is **no new migration** — the keys live in
:mod:`utils.settings_keys.moderation` and are operator-editable through the
existing ``!settings`` widget dispatcher.

Cycle discipline (mirrors :mod:`services.settings_resolution`): the only
cross-package import (``settings_resolution``) is function-local; top-level
imports are stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

SUBSYSTEM = "moderation"

# ---------------------------------------------------------------------------
# Canonical defaults — the single source of truth.
#
# ``cogs/moderation/schemas.py`` imports these for its SettingSpec
# ``default=`` values and validator bounds; :func:`load_policy` uses them as
# the ``resolve_value`` fallback.  A spec default and a policy default can
# therefore never silently drift (pinned by the schema test).
# ---------------------------------------------------------------------------

DEFAULT_DM_ON_ACTION = False
DEFAULT_DM_TEMPLATE = ""
DEFAULT_REQUIRE_REASON = False
DEFAULT_BAN_DELETE_MESSAGE_DAYS = 0
# Discord caps a member timeout at 28 days; the default ceiling is that hard
# maximum, so an unconfigured guild keeps today's behaviour exactly.
DEFAULT_MAX_TIMEOUT_MINUTES = 28 * 24 * 60  # 40320

# Validator bounds (also enforced defensively at the service seam).
MIN_BAN_DELETE_MESSAGE_DAYS = 0
MAX_BAN_DELETE_MESSAGE_DAYS = 7
MIN_TIMEOUT_MINUTES = 1
MAX_TIMEOUT_MINUTES = DEFAULT_MAX_TIMEOUT_MINUTES

_SECONDS_PER_DAY = 24 * 60 * 60

# The placeholder reason every moderation surface substitutes for an empty
# input.  Treated as "no reason" when rendering a member DM so the notice
# does not read "Reason: No reason provided".
_PLACEHOLDER_REASON = "no reason provided"

# Per-action presentation for the built-in DM body.
_DM_ACTION_TEXT: dict[str, tuple[str, str]] = {
    "warn": ("⚠️", "warned"),
    "timeout": ("⏳", "timed out"),
    "kick": ("👢", "kicked"),
    "ban": ("🚫", "banned"),
}


@dataclass(frozen=True)
class ModerationPolicy:
    """Resolved moderation behaviour for one guild.

    Field defaults are the canonical constants above, so
    ``ModerationPolicy()`` is the behaviour-preserving baseline an
    unconfigured guild (or a test) gets.
    """

    dm_on_action: bool = DEFAULT_DM_ON_ACTION
    dm_template: str = DEFAULT_DM_TEMPLATE
    require_reason: bool = DEFAULT_REQUIRE_REASON
    ban_delete_message_days: int = DEFAULT_BAN_DELETE_MESSAGE_DAYS
    max_timeout_minutes: int = DEFAULT_MAX_TIMEOUT_MINUTES

    @property
    def ban_delete_message_seconds(self) -> int:
        """``ban_delete_message_days`` as the seconds Discord's API expects.

        Clamped defensively to Discord's accepted 0–7 day window so a
        malformed stored value can never raise at the ``guild.ban`` call.
        """
        days = max(
            MIN_BAN_DELETE_MESSAGE_DAYS,
            min(MAX_BAN_DELETE_MESSAGE_DAYS, self.ban_delete_message_days),
        )
        return days * _SECONDS_PER_DAY

    @property
    def effective_max_timeout_minutes(self) -> int:
        """The timeout ceiling, clamped to Discord's 1..28-day window."""
        return max(
            MIN_TIMEOUT_MINUTES,
            min(MAX_TIMEOUT_MINUTES, self.max_timeout_minutes),
        )


async def load_policy(guild_id: int) -> ModerationPolicy:
    """Load the effective :class:`ModerationPolicy` for ``guild_id``.

    Each field resolves through :func:`services.settings_resolution.resolve_value`
    so coercion, validation, and provenance stay centralised; a missing or
    malformed stored value transparently falls back to the canonical
    default.
    """
    from services.settings_resolution import resolve_value

    dm_on_action = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "dm_on_action",
        DEFAULT_DM_ON_ACTION,
    )
    dm_template = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "dm_template",
        DEFAULT_DM_TEMPLATE,
    )
    require_reason = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "require_reason",
        DEFAULT_REQUIRE_REASON,
    )
    ban_delete_message_days = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "ban_delete_message_days",
        DEFAULT_BAN_DELETE_MESSAGE_DAYS,
    )
    max_timeout_minutes = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "max_timeout_minutes",
        DEFAULT_MAX_TIMEOUT_MINUTES,
    )
    return ModerationPolicy(
        dm_on_action=bool(dm_on_action),
        dm_template=str(dm_template),
        require_reason=bool(require_reason),
        ban_delete_message_days=int(ban_delete_message_days),
        max_timeout_minutes=int(max_timeout_minutes),
    )


def _clean_reason(reason: str | None) -> str:
    """Return a display reason, or ``""`` for empty / placeholder input."""
    text = (reason or "").strip()
    if not text or text.lower() == _PLACEHOLDER_REASON:
        return ""
    return text


def has_reason(reason: str | None) -> bool:
    """True if *reason* is a real operator-supplied reason.

    Empty, whitespace-only, and the ``"No reason provided"`` placeholder all
    count as **no** reason — this is the single placeholder-aware check the
    ``require_reason`` enforcement (at the ``moderation_service`` seam) and the
    DM renderer share, so "has a reason" means the same thing everywhere.
    """
    return _clean_reason(reason) != ""


def render_dm_message(
    *,
    action: str,
    guild_name: str,
    reason: str | None,
    target_name: str = "",
    template: str = "",
) -> str:
    """Render the member-facing DM body for ``action`` (pure, no I/O).

    When ``template`` is non-empty the operator's custom text is used with
    ``{guild}`` / ``{action}`` / ``{reason}`` / ``{user}`` substituted (plain
    token replacement — never ``str.format``, so a stray brace or attribute
    expression in operator input can't raise or leak). Otherwise a built-in
    per-action notice is rendered, omitting the reason line when none was
    given.
    """
    emoji, verb = _DM_ACTION_TEXT.get(action, ("🔔", action))
    clean_reason = _clean_reason(reason)

    custom = template.strip()
    if custom:
        return (
            custom.replace("{guild}", guild_name)
            .replace("{action}", verb)
            .replace("{reason}", clean_reason or "—")
            .replace("{user}", target_name or "you")
        )

    lines = [f"{emoji} You have been **{verb}** in **{guild_name}**."]
    if clean_reason:
        lines.append(f"**Reason:** {clean_reason}")
    return "\n".join(lines)


__all__ = [
    "DEFAULT_BAN_DELETE_MESSAGE_DAYS",
    "DEFAULT_DM_ON_ACTION",
    "DEFAULT_DM_TEMPLATE",
    "DEFAULT_MAX_TIMEOUT_MINUTES",
    "DEFAULT_REQUIRE_REASON",
    "MAX_BAN_DELETE_MESSAGE_DAYS",
    "MAX_TIMEOUT_MINUTES",
    "MIN_BAN_DELETE_MESSAGE_DAYS",
    "MIN_TIMEOUT_MINUTES",
    "ModerationPolicy",
    "SUBSYSTEM",
    "has_reason",
    "load_policy",
    "render_dm_message",
]
