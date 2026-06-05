"""Phase 1d — Formal :class:`GovernanceScope` enum.

The governance runtime historically referred to scopes as bare strings
(``"guild"``, ``"category"``, ``"channel"``, ``"thread"``) — see
:data:`governance.writes._VALID_VISIBILITY_SCOPE_TYPES` /
:data:`governance.writes._VALID_CLEANUP_SCOPE_TYPES`.  Phase 1d formalizes the
taxonomy as a typed enum so:

* Phase 4.5's :class:`access_control_service` can statically reason
  about scope hierarchies.
* Phase 7's wizard renders scope pickers from the enum rather than a
  hand-curated list.
* Future scopes (``USER`` for delegations, ``ROLE`` for role-tier
  bindings) can be added once, in one place.

The existing string-keyed code paths in :mod:`governance.writes` and
:mod:`governance.resolver` continue to work — :class:`GovernanceScope`
exposes ``.value`` strings matching the legacy form, and helper
functions convert in both directions.

This module is import-cheap: only enum + helpers, no I/O or runtime
side effects.
"""

from __future__ import annotations

from enum import Enum


class GovernanceScope(Enum):
    """Typed governance scope taxonomy.

    Order matters for the implicit hierarchy used by
    :func:`governance.resolver.resolve_visibility`: narrower scopes
    override broader scopes.  The enum value strings match the
    historical governance scope strings so existing DB rows and
    cached values continue to work.

    Members:

    GUILD:
        Whole-guild scope — broadest.
    CATEGORY:
        Discord category (a group of channels).
    CHANNEL:
        Individual text/voice channel.
    THREAD:
        Thread under a channel; narrowest channel-level scope.
    ROLE:
        Role-scoped override (Phase 4.5; previously unused).
    USER:
        User-scoped override (Phase 4.5 delegations).
    """

    GUILD = "guild"
    CATEGORY = "category"
    CHANNEL = "channel"
    THREAD = "thread"
    ROLE = "role"
    USER = "user"


# The historical string set, exposed for back-compat consumers that
# index by string rather than enum.
LEGACY_SCOPE_TYPES: frozenset[str] = frozenset(s.value for s in GovernanceScope)


def from_string(value: str) -> GovernanceScope:
    """Parse a legacy scope string into a :class:`GovernanceScope`.

    Raises ``ValueError`` on unknown input.  Use sparingly — prefer the
    enum at API boundaries and reach for this only when adapting
    legacy storage.
    """
    try:
        return GovernanceScope(value)
    except ValueError:
        valid = ", ".join(sorted(s.value for s in GovernanceScope))
        raise ValueError(
            f"unknown governance scope {value!r}; valid: {valid}",
        ) from None


__all__ = ["LEGACY_SCOPE_TYPES", "GovernanceScope", "from_string"]
