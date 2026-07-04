"""Curated role packs for bulk role creation.

Pure data — no DB, no Discord I/O — so every surface reads one catalogue: the
standalone role-creation panel (:class:`views.roles.creation_panel.RoleCreatePanel`)
and the role-menu builder (:mod:`views.roles.role_menu_builder`) both offer a
**📦 Role Packs** flow that mirrors the shipped 🎨 Colours auto-create UX (pick a
category → multiselect predefined roles → the bot bulk-creates them through the
audited :class:`services.role_lifecycle_service.RoleLifecycleService`).

This is the *functional* sibling of the colour presets (``_COLOR_OPTIONS``) and
the gradient gallery (``role_menu_presentation.gradient_presets``): instead of
colours, a pack is a themed set of common server roles (game roles, staff roles,
pronouns, notification pings, regions, interests). Like ``ROLE_PRESETS`` they are
**creation conveniences only** — a starting point an operator picks instead of
typing each role by hand; they persist nothing until the operator actually
creates them, and they never touch automation, diagnostics, or any other surface.

Layer note: lives in ``utils/`` (may import stdlib + discord only) so any view
can import it without crossing a layer boundary. Extend freely — it is plain
data; keep each pack to ≤25 roles (Discord's select-option cap).
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "PackRole",
    "RolePack",
    "get_pack",
    "packs",
]


@dataclass(frozen=True)
class PackRole:
    """One predefined role in a pack — a name + appearance starting point.

    ``color`` is a hex string (e.g. ``"#3498db"``), matching ``RolePreset`` /
    ``_COLOR_OPTIONS`` so the same ``_parse_color`` helper applies. ``emoji`` is
    purely decorative — it labels the multiselect option; it is not applied to
    the created role (role icons need server boosts and are out of scope here).
    """

    name: str
    color: str = "#99aab5"  # Discord "greyple" — a neutral default
    hoist: bool = False
    emoji: str | None = None
    description: str = ""


@dataclass(frozen=True)
class RolePack:
    """A named category of predefined roles shown as one bulk-create choice."""

    key: str
    label: str  # picker text, e.g. "🎮 Gaming"
    description: str
    roles: tuple[PackRole, ...] = field(default_factory=tuple)


# Ordered so every picker renders the catalogue deterministically. Curated to be
# generic (not tied to one server's theme); colours drawn from a readable palette.
_PACKS: tuple[RolePack, ...] = (
    RolePack(
        "essentials",
        "⭐ Essentials",
        "Common server roles — a general starter set (the standard presets).",
        roles=(
            PackRole("Member", "#2ecc71", emoji="🙂", description="General member."),
            PackRole(
                "Verified",
                "#1abc9c",
                emoji="✅",
                description="Passed verification.",
            ),
            PackRole("Newcomer", "#95a5a6", emoji="🌱", description="Just joined."),
            PackRole("Active", "#3498db", emoji="⚡", description="Active member."),
            PackRole("Regular", "#9b59b6", emoji="🔆", description="Long-time member."),
            PackRole(
                "VIP",
                "#f1c40f",
                hoist=True,
                emoji="💎",
                description="Supporter / VIP — shown separately.",
            ),
            PackRole(
                "Supporter",
                "#e91e63",
                emoji="💖",
                description="Supports the server.",
            ),
            PackRole(
                "Content Creator",
                "#e67e22",
                emoji="🎥",
                description="Streams / makes content.",
            ),
            PackRole("DJ", "#1abc9c", emoji="🎧", description="Music DJ."),
            PackRole("Bot", "#5865f2", emoji="🤖", description="Bot account."),
            PackRole(
                "Helper",
                "#2ecc71",
                hoist=True,
                emoji="🤝",
                description="Community helper.",
            ),
            PackRole(
                "Event Host",
                "#9b59b6",
                hoist=True,
                emoji="🎉",
                description="Runs events.",
            ),
            PackRole(
                "Moderator",
                "#3498db",
                hoist=True,
                emoji="🛡️",
                description="Moderation team.",
            ),
            PackRole(
                "Admin",
                "#e74c3c",
                hoist=True,
                emoji="👑",
                description="Administrator.",
            ),
            PackRole(
                "Muted",
                "#607d8b",
                emoji="🔇",
                description="Restricted (used by moderation).",
            ),
        ),
    ),
    RolePack(
        "gaming",
        "🎮 Gaming",
        "Per-game roles members opt into for squads and pings.",
        roles=(
            PackRole("Valorant", "#fa4454", emoji="🎯"),
            PackRole("League of Legends", "#1e90ff", emoji="⚔️"),
            PackRole("Minecraft", "#5d8a3a", emoji="⛏️"),
            PackRole("Fortnite", "#7b2ff7", emoji="🛡️"),
            PackRole("CS2", "#f0a500", emoji="💣"),
            PackRole("Apex Legends", "#cd3333", emoji="🔺"),
            PackRole("Overwatch", "#f99e1a", emoji="🟠"),
            PackRole("Rocket League", "#1f8fff", emoji="🚗"),
            PackRole("Call of Duty", "#3b3b3b", emoji="🎖️"),
            PackRole("Among Us", "#c51111", emoji="🔪"),
            PackRole("Roblox", "#e2231a", emoji="🧱"),
            PackRole("Genshin Impact", "#4fc3f7", emoji="🌀"),
        ),
    ),
    RolePack(
        "staff",
        "🛡️ Staff / Moderation",
        "Hoisted team roles for server staff.",
        roles=(
            PackRole(
                "Admin",
                "#e74c3c",
                hoist=True,
                emoji="👑",
                description="Administrator.",
            ),
            PackRole(
                "Moderator",
                "#3498db",
                hoist=True,
                emoji="🛡️",
                description="Moderation team.",
            ),
            PackRole(
                "Trial Mod",
                "#5dade2",
                hoist=True,
                emoji="🔰",
                description="Moderator in training.",
            ),
            PackRole(
                "Helper",
                "#2ecc71",
                hoist=True,
                emoji="🤝",
                description="Community helper.",
            ),
            PackRole(
                "Event Manager",
                "#9b59b6",
                hoist=True,
                emoji="🎉",
                description="Runs events.",
            ),
            PackRole(
                "Bot Manager",
                "#1abc9c",
                hoist=True,
                emoji="🤖",
                description="Manages the bots.",
            ),
        ),
    ),
    RolePack(
        "pronouns",
        "🏷️ Pronouns",
        "Self-assignable pronoun roles.",
        roles=(
            PackRole("He/Him", "#3498db", emoji="💙"),
            PackRole("She/Her", "#e84393", emoji="💗"),
            PackRole("They/Them", "#2ecc71", emoji="💚"),
            PackRole("Any Pronouns", "#f1c40f", emoji="💛"),
            PackRole("Ask Pronouns", "#95a5a6", emoji="❔"),
        ),
    ),
    RolePack(
        "event_rsvp",
        "📣 Event RSVP",
        "Sign-up options for an event — pair with the 📣 Event RSVP menu template.",
        roles=(
            PackRole("Going", "#2ecc71", emoji="✅", description="Count me in."),
            PackRole("Maybe", "#f1c40f", emoji="🤔", description="Might make it."),
            PackRole(
                "Can't make it",
                "#e74c3c",
                emoji="❌",
                description="Not this time.",
            ),
        ),
    ),
    RolePack(
        "notifications",
        "🔔 Notifications",
        "Opt-in ping roles for announcements and events.",
        roles=(
            PackRole("Announcements", "#e67e22", emoji="📣"),
            PackRole("Events", "#9b59b6", emoji="📅"),
            PackRole("Giveaways", "#f1c40f", emoji="🎁"),
            PackRole("Updates", "#3498db", emoji="🆕"),
            PackRole("Polls", "#1abc9c", emoji="📊"),
            PackRole("Streams", "#9146ff", emoji="📺"),
        ),
    ),
    RolePack(
        "region",
        "🌍 Region",
        "Where members are based, for timezone-friendly grouping.",
        roles=(
            PackRole("North America", "#3498db", emoji="🌎"),
            PackRole("South America", "#2ecc71", emoji="🌎"),
            PackRole("Europe", "#9b59b6", emoji="🌍"),
            PackRole("Asia", "#e74c3c", emoji="🌏"),
            PackRole("Oceania", "#1abc9c", emoji="🌏"),
            PackRole("Africa", "#e67e22", emoji="🌍"),
        ),
    ),
    RolePack(
        "interests",
        "🎨 Interests",
        "Hobby and interest roles for finding like-minded members.",
        roles=(
            PackRole("Music", "#e74c3c", emoji="🎵"),
            PackRole("Movies", "#3498db", emoji="🎬"),
            PackRole("Art", "#9b59b6", emoji="🎨"),
            PackRole("Anime", "#e84393", emoji="🌸"),
            PackRole("Sports", "#2ecc71", emoji="⚽"),
            PackRole("Tech", "#1abc9c", emoji="💻"),
            PackRole("Books", "#d35400", emoji="📚"),
            PackRole("Cooking", "#f39c12", emoji="🍳"),
            PackRole("Photography", "#34495e", emoji="📷"),
        ),
    ),
    RolePack(
        "platforms",
        "🕹️ Platforms",
        "Which platform members play on.",
        roles=(
            PackRole("PC", "#5865f2", emoji="🖥️"),
            PackRole("PlayStation", "#003791", emoji="🎮"),
            PackRole("Xbox", "#107c10", emoji="🎮"),
            PackRole("Nintendo Switch", "#e60012", emoji="🎮"),
            PackRole("Mobile", "#f1c40f", emoji="📱"),
        ),
    ),
)

_PACK_BY_KEY: dict[str, RolePack] = {p.key: p for p in _PACKS}


def packs() -> tuple[RolePack, ...]:
    """Every role pack, in display order."""
    return _PACKS


def get_pack(key: str | None) -> RolePack | None:
    """Return the pack for ``key``, or ``None`` if unknown/absent."""
    if not key:
        return None
    return _PACK_BY_KEY.get(key)
