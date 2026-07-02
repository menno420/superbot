"""Deterministic gateway-payload factories — the harness's fake Discord world.

Guilds, members, channels, messages, and interactions are fed to the REAL
``ConnectionState`` as synthetic gateway payloads (what the websocket would
deliver), so every object the bot touches is a genuine discord.py model —
converters, permission resolution, cooldown buckets, and the view store all
behave exactly as in production.

Determinism: ids come from one monotonic allocator, timestamps from one
logical clock that advances a fixed step per event. Two identical runs
produce byte-identical observations.
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

__all__ = ["Clock", "World", "DEFAULT_PERSONAS"]

_EPOCH = _dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=_dt.timezone.utc)
_DISCORD_EPOCH_MS = 1_420_070_400_000


class Clock:
    """Logical clock + deterministic snowflake mint.

    discord.py derives ``Message.created_at`` (and therefore command-cooldown
    buckets) from the SNOWFLAKE, not from the payload timestamp — so the
    clock must be encoded in every id we mint. ``advance()`` moves logical
    time one fixed step per driven event; ``snowflake()`` mints a unique id
    carrying the current logical time.
    """

    def __init__(self) -> None:
        self._now = _EPOCH
        self._seq = 0

    @property
    def now(self) -> _dt.datetime:
        return self._now

    def advance(self, seconds: float = 30.0) -> _dt.datetime:
        self._now += _dt.timedelta(seconds=seconds)
        return self._now

    def isoformat(self) -> str:
        return self._now.isoformat()

    def snowflake(self) -> int:
        ms = int(self._now.timestamp() * 1000) - _DISCORD_EPOCH_MS
        self._seq += 1
        return (ms << 22) | (self._seq & 0x3FFFFF)

    # FakeHTTP compatibility: it asks its id source to `allocate()`.
    def allocate(self) -> int:
        return self.snowflake()

    def set_case_base(self, case_id: str) -> None:
        """Give a case a POSITION-INDEPENDENT logical timeline.

        Absolute logical time leaks into goldens (epoch-int columns like
        ``xp.last_xp`` stamp the pinned ``time.time``), so if the clock only
        ever advanced, a case's golden would depend on where in the run it
        executed — a full-corpus capture and an ``--only`` capture of the
        same case would disagree (observed). Deriving each case's start
        from a hash of its id makes every case's timeline a pure function
        of the case itself. Collision odds over the 10-year second-space
        for a ~500-case corpus are ~4e-4; the seq counter is never reset,
        so snowflake uniqueness holds regardless.
        """
        import hashlib

        digest = hashlib.sha1(case_id.encode(), usedforsecurity=False).digest()
        offset = int.from_bytes(digest[:8], "big") % (10 * 365 * 86_400)
        self._now = _EPOCH + _dt.timedelta(seconds=offset)


# Fixed 18-digit ids: discord.py's mention regexes require 15–20 digit
# snowflakes — shorter ids silently fail MemberConverter (verified).
_GUILD_ID = 700_000_000_000_000_001

#: Personas every case can rely on. Authority comes from Discord permissions
#: (admin) — platform-owner identity is a config concern the boot layer pins.
DEFAULT_PERSONAS = {
    "admin": {"id": 900_000_000_000_000_101, "name": "AdminActor", "admin": True},
    "member": {"id": 900_000_000_000_000_102, "name": "MemberActor", "admin": False},
    "second_member": {
        "id": 900_000_000_000_000_103,
        "name": "OtherActor",
        "admin": False,
    },
}

_ADMIN_ROLE_ID = 800_000_000_000_000_201
_EVERYONE_PERMS = "412317240384"  # standard member permset (read/send/react/embed…)
_ADMIN_PERMS = "8"  # ADMINISTRATOR


class World:
    """Builds and feeds the synthetic Discord world into a real bot state."""

    BOT_USER_ID = 500_000_000_000_000_001

    def __init__(self, bot: Any, *, guild_id: int = _GUILD_ID) -> None:
        self.bot = bot
        self.state = bot._connection
        self.clock = Clock()
        self.ids = self.clock  # id mint == clock (snowflakes carry time)
        self.guild_id = guild_id
        self.channels: dict[str, int] = {}
        self.bot_user_payload = {
            "id": str(self.BOT_USER_ID),
            "username": "GalaxyBotParity",
            "discriminator": "0000",
            "global_name": "GalaxyBotParity",
            "avatar": None,
            "bot": True,
        }

    # ------------------------------------------------------------- payloads

    def _member_payload(self, persona: dict[str, Any]) -> dict[str, Any]:
        roles = [str(_ADMIN_ROLE_ID)] if persona.get("admin") else []
        return {
            "user": {
                "id": str(persona["id"]),
                "username": persona["name"],
                "discriminator": "0000",
                "global_name": persona["name"],
                "avatar": None,
                "bot": False,
            },
            "nick": None,
            "roles": roles,
            "joined_at": _EPOCH.isoformat(),
            "deaf": False,
            "mute": False,
            "flags": 0,
        }

    def _channel_payload(self, name: str, cid: int) -> dict[str, Any]:
        return {
            "id": str(cid),
            "type": 0,  # text
            "guild_id": str(self.guild_id),
            "name": name,
            "position": len(self.channels),
            "permission_overwrites": [],
            "nsfw": False,
            "parent_id": None,
            "topic": None,
            "rate_limit_per_user": 0,
        }

    def _guild_payload(self, personas: dict[str, dict[str, Any]]) -> dict[str, Any]:
        channel_names = ["general", "commands", "mod-log", "audit-log"]
        channels = []
        for name in channel_names:
            cid = self.ids.allocate()
            self.channels[name] = cid
            channels.append(self._channel_payload(name, cid))
        members = [self._member_payload(p) for p in personas.values()]
        # The bot itself must be a member so guild.me resolves.
        members.append(
            {
                "user": dict(self.bot_user_payload),
                "nick": None,
                "roles": [str(_ADMIN_ROLE_ID)],
                "joined_at": _EPOCH.isoformat(),
                "deaf": False,
                "mute": False,
                "flags": 0,
            },
        )
        return {
            "id": str(self.guild_id),
            "name": "Parity Test Guild",
            "icon": None,
            "splash": None,
            "discovery_splash": None,
            "owner_id": str(DEFAULT_PERSONAS["admin"]["id"]),
            "afk_channel_id": None,
            "afk_timeout": 300,
            "verification_level": 0,
            "default_message_notifications": 0,
            "explicit_content_filter": 0,
            "roles": [
                {
                    "id": str(self.guild_id),  # @everyone shares the guild id
                    "name": "@everyone",
                    "color": 0,
                    "hoist": False,
                    "position": 0,
                    "permissions": _EVERYONE_PERMS,
                    "managed": False,
                    "mentionable": False,
                },
                {
                    "id": str(_ADMIN_ROLE_ID),
                    "name": "Admin",
                    "color": 0,
                    "hoist": False,
                    "position": 1,
                    "permissions": _ADMIN_PERMS,
                    "managed": False,
                    "mentionable": False,
                },
            ],
            "emojis": [],
            "features": [],
            "mfa_level": 0,
            "application_id": None,
            "system_channel_id": None,
            "system_channel_flags": 0,
            "rules_channel_id": None,
            "max_members": 1000,
            "vanity_url_code": None,
            "description": None,
            "banner": None,
            "premium_tier": 0,
            "premium_subscription_count": 0,
            "preferred_locale": "en-US",
            "public_updates_channel_id": None,
            "nsfw_level": 0,
            "premium_progress_bar_enabled": False,
            "stickers": [],
            "stage_instances": [],
            "guild_scheduled_events": [],
            "member_count": len(members),
            "large": False,
            "unavailable": False,
            "voice_states": [],
            "members": members,
            "channels": channels,
            "threads": [],
            "presences": [],
        }

    # -------------------------------------------------------------- feeding

    def install(self, personas: dict[str, dict[str, Any]] | None = None) -> None:
        """Feed READY + GUILD_CREATE through the real parser."""
        personas = personas or DEFAULT_PERSONAS
        state = self.state
        state.parse_ready(
            {
                "v": 10,
                "user": dict(self.bot_user_payload),
                "guilds": [],
                "session_id": "parity-session",
                "resume_gateway_url": "wss://parity.invalid",
                "shard": [0, 1],
                "application": {"id": str(self.BOT_USER_ID), "flags": 0},
            },
        )
        state.parse_guild_create(self._guild_payload(personas))

    # ------------------------------------------------------------- messages

    def message_payload(
        self,
        content: str,
        *,
        persona: str = "member",
        channel: str = "general",
        mentions: tuple[int, ...] = (),
    ) -> dict[str, Any]:
        member = DEFAULT_PERSONAS[persona]
        ts = self.clock.advance().isoformat()
        mention_users = []
        for uid in mentions:
            p = next(
                (x for x in DEFAULT_PERSONAS.values() if x["id"] == uid),
                {"id": uid, "name": f"user{uid}"},
            )
            mention_users.append(
                {
                    "id": str(uid),
                    "username": p["name"],
                    "discriminator": "0000",
                    "global_name": p["name"],
                    "avatar": None,
                    "bot": False,
                    "member": self._member_payload(p),
                },
            )
        return {
            "id": str(self.ids.allocate()),
            "channel_id": str(self.channels[channel]),
            "guild_id": str(self.guild_id),
            "author": {
                "id": str(member["id"]),
                "username": member["name"],
                "discriminator": "0000",
                "global_name": member["name"],
                "avatar": None,
                "bot": False,
            },
            "member": {
                k: v for k, v in self._member_payload(member).items() if k != "user"
            },
            "content": content,
            "timestamp": ts,
            "edited_timestamp": None,
            "tts": False,
            "mention_everyone": False,
            "mentions": mention_users,
            "mention_roles": [],
            "attachments": [],
            "embeds": [],
            "pinned": False,
            "type": 0,
        }

    # ---------------------------------------------------------- interactions

    def slash_payload(
        self,
        name: str,
        options: list[dict[str, Any]] | None = None,
        *,
        persona: str = "member",
        channel: str = "general",
        command_id: int | None = None,
    ) -> dict[str, Any]:
        member = DEFAULT_PERSONAS[persona]
        self.clock.advance()
        return {
            "id": str(self.ids.allocate()),
            "application_id": str(self.BOT_USER_ID),
            "type": 2,
            "data": {
                "id": str(command_id or self.ids.allocate()),
                "name": name,
                "type": 1,
                "options": options or [],
                "resolved": {},
            },
            "guild_id": str(self.guild_id),
            "channel_id": str(self.channels[channel]),
            "channel": self._channel_payload(channel, self.channels[channel]),
            "member": self._member_payload(member),
            "token": f"parity-token-{self.ids.allocate()}",
            "version": 1,
            "locale": "en-US",
            "guild_locale": "en-US",
            "app_permissions": "562949953421311",
            "attachment_size_limit": 26214400,
            "entitlements": [],
            "authorizing_integration_owners": {},
            "context": 0,
        }

    def component_payload(
        self,
        *,
        message_id: int,
        custom_id: str,
        component_type: int = 2,
        values: list[str] | None = None,
        persona: str = "member",
        channel: str = "general",
    ) -> dict[str, Any]:
        member = DEFAULT_PERSONAS[persona]
        self.clock.advance()
        data: dict[str, Any] = {
            "custom_id": custom_id,
            "component_type": component_type,
        }
        if values is not None:
            data["values"] = values
        return {
            "id": str(self.ids.allocate()),
            "application_id": str(self.BOT_USER_ID),
            "type": 3,
            "data": data,
            "guild_id": str(self.guild_id),
            "channel_id": str(self.channels[channel]),
            "channel": self._channel_payload(channel, self.channels[channel]),
            "member": self._member_payload(member),
            "message": {
                "id": str(message_id),
                "channel_id": str(self.channels[channel]),
                "author": dict(self.bot_user_payload),
                "content": "",
                "timestamp": self.clock.isoformat(),
                "edited_timestamp": None,
                "tts": False,
                "mention_everyone": False,
                "mentions": [],
                "mention_roles": [],
                "attachments": [],
                "embeds": [],
                "pinned": False,
                "type": 0,
            },
            "token": f"parity-token-{self.ids.allocate()}",
            "version": 1,
            "locale": "en-US",
            "guild_locale": "en-US",
            "app_permissions": "562949953421311",
            "attachment_size_limit": 26214400,
            "entitlements": [],
            "authorizing_integration_owners": {},
            "context": 0,
        }
