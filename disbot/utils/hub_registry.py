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
            ``key``. Two implicit contracts bite when you edit this:
            (1) **bidirectional roster rule** — every key here MUST set
            ``parent_hub=<key>`` in ``SUBSYSTEMS`` and vice versa, or
            ``services/help_catalogue.py`` reports ``roster_drift`` and
            ``test_every_hub_primary_children_match_parent_hub_filter``
            fails; (2) for the ``games`` hub specifically, adding a child
            subjects it to the **actionability contract**
            (``tests/unit/help/test_help_actionability_contract.py``) —
            its Help panel must expose a real action button (or be carried
            as an ``xfail`` target until it does).
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
# Every visible mother hub appears here, each with a real panel. After the
# help-menu regrouping (PR #1290) every subsystem is homed under one of these
# hubs, and the redundant "All Commands / Advanced" fallback was removed
# (PR #1294) — the hubs are the only category surface.
#
# Order in this tuple drives display order in Help.

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
        # fishing + creature homed here by the help-menu regrouping (PR #1290)
        # so the two newest minigames live in the Games section instead of only
        # the Advanced browser.
        primary_children=(
            "blackjack",
            "deathmatch",
            "rps_tournament",
            "mining",
            "counting",
            "chain",
            "fishing",
            "creature",
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
        # security homed here by the help-menu regrouping (PR #1290) — the
        # automated join-screening layer belongs in the Safety section.
        primary_children=(
            "automod",
            "image_moderation",
            "cleanup",
            "logging",
            "proof_channel",
            "security",
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
        # XP, Role, and Spotlight are the primary children
        # (parent_hub="community"; Spotlight registered via the Q-0025
        # scaffold lane). Counting, Chain (whose primary is Games) and
        # Leaderboard (whose primary is Economy) appear as cross-links —
        # CommunityHubView discovers both groups from registry (PR #4).
        # welcome + counters homed here by the help-menu regrouping (PR #1290);
        # both are administrator-tier so they stay operator-only in the
        # user-tier Community view (no clutter for normal members).
        primary_children=(
            "xp",
            "community_spotlight",
            "role",
            "welcome",
            "counters",
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
    # Server & Admin — the consolidated operator section (help-menu regrouping,
    # PR #1290). The four child-less admin hubs that used to crowd the Help index
    # (Admin, Settings, Diagnostics/Platform, Server Management) plus Channels,
    # AI Platform, and UX Lab are now ONE section: each is a primary child
    # (parent_hub="admin") reached from the Admin panel, so the admin-side index
    # drops from ~10 sections to a few clear ones. Their typed commands
    # (!settings, !platform, !servermanagement, !channelmenu, !ai, !uxlab) are
    # unchanged — only the Help section grouping changed.
    HubEntry(
        key="admin",
        display_name="Server & Admin",
        emoji="⚙️",
        purpose="Settings, diagnostics, server management, channels, AI, and ops.",
        entry_command="!adminmenu",
        primary_children=(
            "ux_lab",
            "channel",
            "server_management",
            "ai",
            "settings",
            "diagnostic",
        ),
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
    "HUBS",
    "HubEntry",
    "get_hub",
    "hubs_for_tier",
]
