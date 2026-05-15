from __future__ import annotations

import discord


class PermissionDenied(Exception):
    def __init__(self, capability: str) -> None:
        self.capability = capability
        super().__init__(f"Missing capability: {capability}")


class PermissionService:
    """Capability-based permission checks.

    Currently a thin wrapper over Discord guild permissions.
    Future evolution: role-based overrides from guild_settings,
    per-guild capability maps, premium tiers.

    All new permission checks use permission_service.check() instead of
    inline guild_permissions.* checks.
    """

    CAPABILITY_MAP: dict[str, str] = {
        "moderation.warn": "manage_roles",
        "moderation.timeout": "moderate_members",
        "moderation.kick": "kick_members",
        "moderation.ban": "ban_members",
        "roles.manage": "manage_roles",
        "channels.manage": "manage_channels",
        "admin.cogs": "administrator",
        "admin.settings": "administrator",
        "economy.manage": "administrator",
        "xp.manage": "administrator",
        "games.tournament": "manage_guild",
    }

    async def has(self, member: discord.Member, capability: str) -> bool:
        discord_perm = self.CAPABILITY_MAP.get(capability)
        if not discord_perm:
            return member.guild_permissions.administrator
        return getattr(member.guild_permissions, discord_perm, False)

    async def check(self, member: discord.Member, capability: str) -> None:
        if not await self.has(member, capability):
            raise PermissionDenied(capability)


permission_service = PermissionService()
