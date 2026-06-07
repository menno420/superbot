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

# Warn escalation — the discipline ladder applied at the warn seam.  The
# defaults reproduce today's behaviour exactly: at the third warning the
# member is auto-timed-out for ten minutes, then their warnings reset.
DEFAULT_WARN_THRESHOLD = 3
DEFAULT_WARN_TIMEOUT_MINUTES = 10
DEFAULT_WARN_ESCALATION_ACTION = "timeout"
# The terminal action taken when the warning count reaches the threshold.
# ``"none"`` disables auto-escalation (the count still accrues + audits).
WARN_ESCALATION_ACTIONS: tuple[str, ...] = ("timeout", "kick", "ban", "none")

# Post-action cleanup — after a kick/ban, optionally sweep the moderated
# member's recent messages in the channel where the action was taken.  The
# default ``"none"`` keeps today's behaviour exactly; the sweep itself is
# *requested* from the cleanup subsystem (services.history_cleanup), so
# moderation never re-implements deletion mechanics.
DEFAULT_POST_ACTION_CLEANUP = "none"
# Which actions trigger the sweep: ``"kick"`` / ``"ban"`` / ``"both"`` /
# ``"none"`` (disabled).
POST_ACTION_CLEANUP_ACTIONS: tuple[str, ...] = ("none", "kick", "ban", "both")
DEFAULT_POST_ACTION_CLEANUP_LIMIT = 100
# How many recent messages the sweep scans in the channel.  Bounded tighter
# than the manual ``!cleanuphistory`` ceiling because this runs automatically.
MIN_POST_ACTION_CLEANUP_LIMIT = 1
MAX_POST_ACTION_CLEANUP_LIMIT = 500

# Optional PUBLIC moderation log — an operator-opt-in channel that announces
# selected actions WITHOUT naming the acting moderator.  Default OFF (no channel
# + ``"none"``).  ``public_log_channel`` is a channel-id string ("" = off);
# ``public_log_actions`` selects which actions are announced.
DEFAULT_PUBLIC_LOG_CHANNEL = ""
DEFAULT_PUBLIC_LOG_ACTIONS = "none"
# ``none`` = off · ``bans`` = ban only · ``removals`` = kick + ban ·
# ``all`` = warn + timeout + kick + ban.  unban / clearwarnings / system
# auto-deletes / the post-action sweep are never publicised.
PUBLIC_LOG_ACTIONS: tuple[str, ...] = ("none", "bans", "removals", "all")
_PUBLIC_LOG_ACTION_SETS: dict[str, frozenset[str]] = {
    "none": frozenset(),
    "bans": frozenset({"ban"}),
    "removals": frozenset({"kick", "ban"}),
    "all": frozenset({"warn", "timeout", "kick", "ban"}),
}

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
    warn_threshold: int = DEFAULT_WARN_THRESHOLD
    warn_timeout_minutes: int = DEFAULT_WARN_TIMEOUT_MINUTES
    warn_escalation_action: str = DEFAULT_WARN_ESCALATION_ACTION
    post_action_cleanup: str = DEFAULT_POST_ACTION_CLEANUP
    post_action_cleanup_limit: int = DEFAULT_POST_ACTION_CLEANUP_LIMIT
    public_log_channel: str = DEFAULT_PUBLIC_LOG_CHANNEL
    public_log_actions: str = DEFAULT_PUBLIC_LOG_ACTIONS

    @property
    def effective_post_action_cleanup_limit(self) -> int:
        """Scan limit for the post-action sweep, clamped to the safe window."""
        return max(
            MIN_POST_ACTION_CLEANUP_LIMIT,
            min(MAX_POST_ACTION_CLEANUP_LIMIT, self.post_action_cleanup_limit),
        )

    @property
    def public_log_channel_id(self) -> int:
        """The configured public-log channel id, or ``0`` when unset/malformed."""
        raw = (self.public_log_channel or "").strip()
        return int(raw) if raw.isdigit() else 0

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


@dataclass(frozen=True)
class EscalationDecision:
    """The terminal action a warning count triggers (pure, no I/O).

    ``action`` is one of ``"timeout"`` / ``"kick"`` / ``"ban"``;
    ``timeout_minutes`` is only meaningful for the timeout action (0
    otherwise).  :func:`evaluate_escalation` returns ``None`` when no
    escalation is due.
    """

    action: str
    timeout_minutes: int = 0


def evaluate_escalation(
    count: int,
    policy: ModerationPolicy,
) -> EscalationDecision | None:
    """Decide whether *count* warnings escalate under *policy* (pure).

    Returns ``None`` below the threshold, when escalation is disabled
    (``warn_escalation_action == "none"``), or for an unrecognised stored
    action (fail-safe: never perform an unintended kick/ban).  Otherwise the
    decision names the configured terminal action; only ``"timeout"`` carries
    a duration.
    """
    action = policy.warn_escalation_action
    if action not in ("timeout", "kick", "ban"):
        return None
    if count < policy.warn_threshold:
        return None
    minutes = policy.warn_timeout_minutes if action == "timeout" else 0
    return EscalationDecision(action=action, timeout_minutes=minutes)


def cleanup_applies_to(action: str, policy: ModerationPolicy) -> bool:
    """Whether *policy* enables a post-action message sweep for *action* (pure).

    ``post_action_cleanup`` is one of ``"none"`` (default) / ``"kick"`` /
    ``"ban"`` / ``"both"``.  Fail-safe: any unrecognised stored value disables
    the sweep, so a malformed setting can never trigger an unintended deletion.
    """
    setting = policy.post_action_cleanup
    if setting == "kick":
        return action == "kick"
    if setting == "ban":
        return action == "ban"
    if setting == "both":
        return action in ("kick", "ban")
    return False


def public_log_includes(action: str, policy: ModerationPolicy) -> bool:
    """Whether *action* should be announced on the public log under *policy* (pure).

    Considers only the action selector (``public_log_actions``) — the caller
    (``services.server_logging``) still checks that a channel is configured and
    resolvable.  Fail-safe: an unrecognised selector announces nothing.  Only
    the disciplinary actions warn / timeout / kick / ban are ever eligible;
    unban, clearwarnings, the post-action sweep, and system auto-deletes never
    surface publicly.
    """
    return action in _PUBLIC_LOG_ACTION_SETS.get(policy.public_log_actions, frozenset())


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
    warn_threshold = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "warn_threshold",
        DEFAULT_WARN_THRESHOLD,
    )
    warn_timeout_minutes = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "warn_timeout_minutes",
        DEFAULT_WARN_TIMEOUT_MINUTES,
    )
    warn_escalation_action = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "warn_escalation_action",
        DEFAULT_WARN_ESCALATION_ACTION,
    )
    post_action_cleanup = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "post_action_cleanup",
        DEFAULT_POST_ACTION_CLEANUP,
    )
    post_action_cleanup_limit = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "post_action_cleanup_limit",
        DEFAULT_POST_ACTION_CLEANUP_LIMIT,
    )
    public_log_channel = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "public_log_channel",
        DEFAULT_PUBLIC_LOG_CHANNEL,
    )
    public_log_actions = await resolve_value(
        guild_id,
        SUBSYSTEM,
        "public_log_actions",
        DEFAULT_PUBLIC_LOG_ACTIONS,
    )
    return ModerationPolicy(
        dm_on_action=bool(dm_on_action),
        dm_template=str(dm_template),
        require_reason=bool(require_reason),
        ban_delete_message_days=int(ban_delete_message_days),
        max_timeout_minutes=int(max_timeout_minutes),
        warn_threshold=int(warn_threshold),
        warn_timeout_minutes=int(warn_timeout_minutes),
        warn_escalation_action=str(warn_escalation_action),
        post_action_cleanup=str(post_action_cleanup),
        post_action_cleanup_limit=int(post_action_cleanup_limit),
        public_log_channel=str(public_log_channel),
        public_log_actions=str(public_log_actions),
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
    "DEFAULT_POST_ACTION_CLEANUP",
    "DEFAULT_POST_ACTION_CLEANUP_LIMIT",
    "DEFAULT_PUBLIC_LOG_ACTIONS",
    "DEFAULT_PUBLIC_LOG_CHANNEL",
    "DEFAULT_REQUIRE_REASON",
    "DEFAULT_WARN_ESCALATION_ACTION",
    "DEFAULT_WARN_THRESHOLD",
    "DEFAULT_WARN_TIMEOUT_MINUTES",
    "MAX_BAN_DELETE_MESSAGE_DAYS",
    "MAX_POST_ACTION_CLEANUP_LIMIT",
    "MAX_TIMEOUT_MINUTES",
    "MIN_BAN_DELETE_MESSAGE_DAYS",
    "MIN_POST_ACTION_CLEANUP_LIMIT",
    "MIN_TIMEOUT_MINUTES",
    "POST_ACTION_CLEANUP_ACTIONS",
    "PUBLIC_LOG_ACTIONS",
    "WARN_ESCALATION_ACTIONS",
    "EscalationDecision",
    "ModerationPolicy",
    "SUBSYSTEM",
    "cleanup_applies_to",
    "evaluate_escalation",
    "has_reason",
    "load_policy",
    "public_log_includes",
    "render_dm_message",
]
