"""Central hub presentation registry (S3).

Hub display metadata MUST NOT be scattered inside ``help_cog.py`` —
that would couple Help rendering to subsystem-specific knowledge and
make new hubs (S7–S10) painful to land. Instead, every visible mother
hub registers a single :class:`HubEntry` here. Help and (later) slash
front doors both read from this single source.

Presentation only. The registry describes Help/category display.
It is NOT a second router and must not own business logic:

* No DB writes.
* No governance resolution. ``minimum_tier`` is metadata — Help
  is responsible for applying it via ``governance_service``.
* No command dispatch. ``entry_command`` is metadata; the actual
  ``!`` command lives in the host cog.

Cross-references:

* :mod:`utils.subsystem_registry` — canonical SUBSYSTEMS metadata
  (with ``parent_hub`` / ``hub_group`` for child discovery).
* :mod:`docs.building-roadmap.mother-hub-map` — the design
  doctrine this registry implements (§ "Central hub presentation
  registry").
"""

from __future__ import annotations

from dataclasses import dataclass

# Sentinel hub key for the permanent tier-grouped subsystem browser.
# Selecting this category in the Help dropdown opens the paginated
# all-commands view (the pre-S3 Help layout, now demoted to a
# secondary navigation path).
ALL_COMMANDS_KEY = "all_commands"


@dataclass(frozen=True)
class HubEntry:
    """One mother-hub entry in the Help category index.

    Fields:
        key: stable internal id (e.g. ``"games"``). Doubles as the
            registry key. For hubs with a ``parent_hub``-backed child
            list, this must equal the ``parent_hub`` value used in
            ``SUBSYSTEMS``.
        display_name: user-facing name (e.g. ``"Games"``).
        emoji: single emoji for the dropdown / embed.
        purpose: 1-line description shown under the category heading.
        entry_command: typed ``!`` command (e.g. ``"!games"``). The
            doctrine forbids panel-only hubs.
        slash_command: future ``/`` command, ``None`` until S11.
        primary_children: subsystem keys whose ``parent_hub`` equals
            ``key``. Empty for hubs that don't use child discovery
            (Admin, Settings, Platform).
        cross_link_children: subsystem keys cross-listed via UI
            buttons (no metadata change). Empty for the v1 hubs.
        minimum_tier: lowest governance tier that may see this hub.
            ``"user"`` shows to everyone; ``"administrator"`` hides
            from non-admins. Help applies the filter.
        settings_path: settings hub subsystem key (or ``None``).
        panel_available: ``True`` when the hub has a real panel that
            ``build_help_menu_view`` can return. ``False`` hides the
            hub from Help — the visibility rule.
    """

    key: str
    display_name: str
    emoji: str
    purpose: str
    entry_command: str
    slash_command: str | None = None
    primary_children: tuple[str, ...] = ()
    cross_link_children: tuple[str, ...] = ()
    minimum_tier: str = "user"
    settings_path: str | None = None
    panel_available: bool = True


# ---------------------------------------------------------------------------
# Canonical hub list (S3 v1 — existing-hub-only rollout)
# ---------------------------------------------------------------------------
#
# Only hubs whose panels exist today appear here. Economy, Moderation/
# Safety, Community, and Utility hubs are added by S7–S10 PRs once their
# panels land. Until then, their child subsystems remain reachable via
# the All Commands / Advanced fallback.
#
# Order in this tuple drives display order in Help. The All Commands
# fallback always sorts last (Help appends it after the iteration).

HUBS: tuple[HubEntry, ...] = (
    HubEntry(
        key="games",
        display_name="Games",
        emoji="🎮",
        purpose="Game flows and tournaments.",
        entry_command="!games",
        # M1: BTD6 promoted to its own top-level hub. Removed from
        # Games' primary_children; subsystem_registry drops btd6's
        # parent_hub="games" / hub_group="activities" in the same PR.
        # No Games cross-link by accepted decision.
        primary_children=(
            "blackjack",
            "deathmatch",
            "rps_tournament",
            "mining",
            "counting",
            "chain",
        ),
        minimum_tier="user",
    ),
    HubEntry(
        key="btd6",
        display_name="BTD6 Assistant",
        emoji="🐵",
        purpose=(
            "Bloons Tower Defense 6 assistant — lookups, strategy "
            "guidance, and round breakdowns."
        ),
        entry_command="!btd6",
        primary_children=(),
        minimum_tier="user",
    ),
    HubEntry(
        key="economy",
        display_name="Economy",
        emoji="💰",
        purpose="Currency, items, work, shop, and standings.",
        entry_command="!economymenu",
        # PR #3 promotes Inventory and Leaderboard to parent_hub of
        # "economy" (their primary placement). Mining stays under
        # Games — Economy declares it as a cross-link so the Economy
        # hub view can surface it without changing Mining's metadata.
        primary_children=(
            "inventory",
            "leaderboard",
        ),
        cross_link_children=("mining",),
        minimum_tier="user",
    ),
    HubEntry(
        key="moderation",
        display_name="Moderation & Safety",
        emoji="🛡️",
        purpose="Warnings, timeouts, bans, cleanup, audit logs.",
        entry_command="!modmenu",
        # PR #3 promotes Cleanup, Logging, and Proof Channel to
        # parent_hub of "moderation" so they hide from the Help Home
        # top-level overview and surface under this hub instead.
        primary_children=(
            "cleanup",
            "logging",
            "proof_channel",
        ),
        cross_link_children=(),
        minimum_tier="moderator",
    ),
    HubEntry(
        key="community",
        display_name="Community",
        emoji="🌱",
        purpose="Progression, roles, and community activities.",
        entry_command="!community",
        # XP and Role are the primary children (parent_hub="community"
        # since PR #3). Counting, Chain (whose primary is Games) and
        # Leaderboard (whose primary is Economy) appear as cross-links —
        # CommunityHubView discovers both groups from registry (PR #4).
        primary_children=(
            "xp",
            "role",
        ),
        cross_link_children=(
            "counting",
            "chain",
            "leaderboard",
        ),
        minimum_tier="user",
    ),
    HubEntry(
        key="utility",
        display_name="Utility",
        emoji="🧰",
        purpose="Info, tools, and discovery commands.",
        entry_command="!utilitymenu",
        # PR #3 promotes General to parent_hub of "utility". Help
        # itself stays top-level — it IS the Help surface so it never
        # surfaces under any hub. PR #420 adds the 🍃 420 easter-egg
        # subsystem here too.
        primary_children=("general", "four_twenty"),
        cross_link_children=(),
        minimum_tier="user",
    ),
    HubEntry(
        key="admin",
        display_name="Admin / Operations",
        emoji="⚙️",
        purpose="Cog management, role/channel admin, runtime ops.",
        entry_command="!adminmenu",
        minimum_tier="administrator",
    ),
    HubEntry(
        key="settings",
        display_name="Settings / Configuration",
        emoji="🔧",
        purpose="Configure all subsystems via mutation pipelines.",
        entry_command="!settings",
        minimum_tier="administrator",
    ),
    HubEntry(
        key="diagnostic",
        display_name="Platform / Diagnostics",
        emoji="🩺",
        purpose="Platform identity, feature flags, runtime health.",
        entry_command="!platform",
        minimum_tier="administrator",
    ),
    HubEntry(
        # key is the snake_case subsystem key (Q-0026), matching
        # SUBSYSTEMS["server_management"]; entry_command keeps the
        # ``!servermanagement`` command name.
        key="server_management",
        display_name="Server Management",
        emoji="🧭",
        purpose="Moderation, channels, roles, cleanup, and setup in one place.",
        entry_command="!servermanagement",
        minimum_tier="administrator",
    ),
)


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


def get_hub(key: str) -> HubEntry | None:
    """Return the :class:`HubEntry` for ``key``, or ``None``."""
    for hub in HUBS:
        if hub.key == key:
            return hub
    return None


def hubs_for_tier(member_tier: str) -> list[HubEntry]:
    """Return hubs visible to ``member_tier`` in registry order.

    Uses :func:`governance.permission_tiers.tier_at_or_above` so the
    tier comparison stays consistent with the rest of the bot.

    Hubs with ``panel_available=False`` are filtered out — the
    visibility rule from the mother-hub map.

    Unknown or legacy tier strings (e.g. an old ``"everyone"`` left in
    a fixture) are treated as the lowest tier ``"user"`` so Help never
    crashes on stale data. The decision is logged at WARNING via the
    governance module for visibility.
    """
    # Local import: governance lives outside utils to keep the
    # import graph layered. Function-local keeps this module
    # cheap to import at startup.
    from governance.permission_tiers import tier_at_or_above

    visible: list[HubEntry] = []
    for hub in HUBS:
        if not hub.panel_available:
            continue
        try:
            allowed = tier_at_or_above(member_tier, hub.minimum_tier)
        except ValueError:
            # Defensive: unknown tier string → only user-tier hubs.
            allowed = tier_at_or_above("user", hub.minimum_tier)
        if allowed:
            visible.append(hub)
    return visible


__all__ = [
    "ALL_COMMANDS_KEY",
    "HUBS",
    "HubEntry",
    "get_hub",
    "hubs_for_tier",
]
