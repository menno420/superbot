from __future__ import annotations

import logging
from datetime import datetime

import discord
from discord.ext import commands, tasks
from utils import db
from utils.helpers import CogMenuView, normalize_name

logger = logging.getLogger("bot")

# Default time-based thresholds seeded into the DB when a guild has none.
_DEFAULT_THRESHOLDS: list[tuple[str, int]] = [
    ("Neu", 0),
    ("Normal", 1),
    ("Iron", 7),
    ("Gold", 30),
    ("Diamand", 365),
    ("Netherite", 730),
    ("Beacon", 1825),
]

SKIP_ROLES = {"Admin"}  # role names that are never auto-assigned / removed

_ROLE_MENU_COMMANDS: list[tuple[str, str, str]] = [
    ("rolemenu", "!rolemenu", "Show this role command menu."),
    ("roles", "!roles", "List all server roles with member counts."),
    ("assignroles", "!assignroles", "Manually run time-based role assignment."),
    (
        "createrole",
        "!createrole <name> [color] [hoist]",
        "Create a new role with optional hex color.",
    ),
    ("deleterole", "!deleterole <@role>", "Delete a role from the server."),
    ("rolecreator", "!rolecreator", "Open the interactive role creator UI."),
    ("rolesettings", "!rolesettings", "Manage time-based role thresholds (admin UI)."),
    (
        "setrole",
        "!setrole <days> <role name>",
        "Add/update a time-based role threshold.",
    ),
    ("unsetrole", "!unsetrole <role name>", "Remove a role from auto-assignment."),
    (
        "reactroles",
        "!reactroles <msg_id> <emoji> <@role>",
        "Attach a reaction→role mapping to a message.",
    ),
    (
        "removereactrole",
        "!removereactrole <msg_id> <emoji>",
        "Remove a reaction role binding.",
    ),
    (
        "listreactroles",
        "!listreactroles",
        "List all active reaction roles in this server.",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_defaults(guild_id: int) -> None:
    """Seed default thresholds for a guild that has none yet."""
    existing = await db.get_role_thresholds(guild_id)
    if not existing:
        for name, days in _DEFAULT_THRESHOLDS:
            await db.set_role_threshold(guild_id, name, days)


def _parse_color(value: str) -> discord.Color:
    """Parse a hex string like '#ff0000' or 'ff0000' into a discord.Color."""
    value = value.strip().lstrip("#")
    return discord.Color(int(value, 16))


def _find_role_normalized(guild: discord.Guild, name: str) -> discord.Role | None:
    """Case-insensitive, space-insensitive role lookup."""
    key = normalize_name(name)
    return discord.utils.find(lambda r: normalize_name(r.name) == key, guild.roles)


_COLOR_OPTIONS = [
    ("Red", "#e74c3c"),
    ("Blue", "#3498db"),
    ("Green", "#2ecc71"),
    ("Yellow", "#f1c40f"),
    ("Purple", "#9b59b6"),
    ("Orange", "#e67e22"),
    ("White", "#ffffff"),
    ("Black", "#000000"),
]


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class RoleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.role_check.start()

    def cog_unload(self):
        self.role_check.cancel()

    # ------------------------------------------------------------------ loop

    @tasks.loop(hours=24)
    async def role_check(self):
        for guild in self.bot.guilds:
            await self._assign_roles(guild)

    @role_check.before_loop
    async def before_role_check(self):
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ core role assignment

    async def _assign_roles(
        self, guild: discord.Guild, ctx: commands.Context = None
    ) -> int:
        """Assign time-based roles to all members. Returns count of assignments made."""
        await _ensure_defaults(guild.id)
        thresholds = await db.get_role_thresholds(guild.id)
        if not thresholds:
            return 0

        # Build ordered mapping: role_name -> days_required
        role_map = {row["role_name"]: row["days_required"] for row in thresholds}
        progression = sorted(role_map, key=lambda r: role_map[r])

        admin_role = _find_role_normalized(guild, "Admin")
        assigned = 0

        for member in guild.members:
            if member.bot:
                continue
            if admin_role and admin_role in member.roles:
                continue
            if not member.joined_at:
                continue

            days = (datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days

            # Find the highest qualifying role
            target_name = None
            for name in progression:
                if days >= role_map[name]:
                    target_name = name

            target_role = (
                _find_role_normalized(guild, target_name) if target_name else None
            )

            # Current highest progression role this member holds
            current_highest: str | None = None
            for role in member.roles:
                matched = next(
                    (
                        n
                        for n in role_map
                        if normalize_name(n) == normalize_name(role.name)
                    ),
                    None,
                )
                if matched:
                    if current_highest is None or progression.index(
                        matched
                    ) > progression.index(current_highest):
                        current_highest = matched

            # Don't downgrade
            if (
                current_highest
                and target_name
                and progression.index(current_highest) > progression.index(target_name)
            ):
                continue

            # Remove outdated progression roles (keep target only)
            to_remove = [
                r
                for r in member.roles
                if any(normalize_name(r.name) == normalize_name(n) for n in role_map)
                and r != target_role
            ]
            if to_remove:
                try:
                    await member.remove_roles(*to_remove)
                except (discord.Forbidden, discord.HTTPException):
                    pass

            if target_role and target_role not in member.roles:
                try:
                    await member.add_roles(target_role)
                    assigned += 1
                    logger.info(
                        "Assigned %s to %s", target_role.name, member.display_name
                    )
                except (discord.Forbidden, discord.HTTPException):
                    pass

        if ctx:
            await ctx.send(f"✅ Role check complete — {assigned} assignment(s) made.")
        return assigned

    # ------------------------------------------------------------------ commands

    @commands.command(name="rolemenu")
    async def rolemenu(self, ctx: commands.Context):
        """Show a quick-reference menu for all role commands."""
        view = CogMenuView(ctx, "🎭 Role Commands", _ROLE_MENU_COMMANDS)
        msg = await ctx.send(embed=view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="assignroles")
    @commands.has_permissions(administrator=True)
    async def assign_roles_cmd(self, ctx: commands.Context):
        """Manually run the time-based role assignment for all members."""
        await ctx.send("🔄 Running role assignment…")
        await self._assign_roles(ctx.guild, ctx)

    @commands.command(name="roles")
    async def roles(self, ctx: commands.Context):
        """List all server roles with member counts."""
        lines = [
            f"**{role.name}** — {sum(1 for m in ctx.guild.members if role in m.roles)} members"
            for role in reversed(ctx.guild.roles)
            if role != ctx.guild.default_role
        ]
        embed = discord.Embed(
            title=f"Roles in {ctx.guild.name}",
            description="\n".join(lines) or "No roles found.",
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="debugroles")
    @commands.has_permissions(administrator=True)
    async def debug_roles(self, ctx: commands.Context):
        """Print all role names for verification."""
        names = [r.name for r in ctx.guild.roles]
        await ctx.send(f"Roles: {', '.join(names)}")

    @commands.command(name="refreshmembers")
    @commands.has_permissions(administrator=True)
    async def refresh_members(self, ctx: commands.Context):
        """Force-fetch all members from Discord."""
        await ctx.guild.chunk()
        await ctx.send("✅ Member list refreshed.")

    # ------------------------------------------------------------------ role creation commands

    @commands.command(name="createrole")
    @commands.has_permissions(manage_roles=True)
    async def createrole(
        self, ctx: commands.Context, name: str, color: str = "000000", hoist: str = "no"
    ):
        """Create a new role.  Usage: !createrole <name> [hex_color] [hoist yes/no]"""
        try:
            col = _parse_color(color)
        except (ValueError, OverflowError):
            await ctx.send(
                "❌ Invalid color — use a hex code like `#3498db`.", delete_after=10
            )
            return
        do_hoist = hoist.lower() in ("yes", "true", "1", "y")
        try:
            role = await ctx.guild.create_role(name=name, color=col, hoist=do_hoist)
            await ctx.send(
                f"✅ Created role **{role.name}** (color `{color}`, hoist={do_hoist})."
            )
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to create roles.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command(name="deleterole")
    @commands.has_permissions(manage_roles=True)
    async def deleterole(self, ctx: commands.Context, *, role: discord.Role):
        """Delete a role by name or mention."""
        if role >= ctx.guild.me.top_role:
            await ctx.send("❌ That role is higher than or equal to my top role.")
            return
        name = role.name
        try:
            await role.delete()
            await ctx.send(f"🗑️ Deleted role **{name}**.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to delete that role.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Failed: {e}")

    @commands.command(name="rolecreator")
    @commands.has_permissions(manage_roles=True)
    async def rolecreator(self, ctx: commands.Context):
        """Open the interactive role creator."""
        view = RoleCreatorView(ctx)
        embed = discord.Embed(
            title="🎨 Role Creator",
            description="Click **Create Role** to open the creation form.",
            color=discord.Color.blurple(),
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    @commands.command(name="rolesettings")
    @commands.has_permissions(administrator=True)
    async def rolesettings(self, ctx: commands.Context):
        """Open the time-based role threshold manager."""
        await _ensure_defaults(ctx.guild.id)
        view = RoleSettingsView(ctx)
        msg = await ctx.send(embed=await view.build_embed(), view=view)
        view.message = msg

    @commands.command(name="setrole")
    @commands.has_permissions(administrator=True)
    async def setrole(self, ctx: commands.Context, days: int, *, role_name: str):
        """Add or update a time-based role threshold.  Usage: !setrole <days> <role name>"""
        if days < 0:
            await ctx.send("Days must be 0 or greater.", delete_after=5)
            return
        normalized = normalize_name(role_name)
        # Store the original Discord role name (case-preserved) if the role exists
        discord_role = _find_role_normalized(ctx.guild, role_name)
        store_name = discord_role.name if discord_role else role_name
        await db.set_role_threshold(ctx.guild.id, store_name, days)
        await ctx.send(
            f"✅ Role **{store_name}** will be assigned after **{days}** day(s)."
        )

    @commands.command(name="unsetrole")
    @commands.has_permissions(administrator=True)
    async def unsetrole(self, ctx: commands.Context, *, role_name: str):
        """Remove a role from the time-based assignment system."""
        # Try exact match first, then normalized match against stored thresholds
        thresholds = await db.get_role_thresholds(ctx.guild.id)
        key = normalize_name(role_name)
        match = next(
            (
                r["role_name"]
                for r in thresholds
                if normalize_name(r["role_name"]) == key
            ),
            role_name,
        )
        await db.remove_role_threshold(ctx.guild.id, match)
        await ctx.send(f"✅ Removed **{match}** from the auto-assignment system.")

    # ------------------------------------------------------------------ Reaction Role System (DB-backed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        role_id = await db.get_reaction_role(
            payload.guild_id, payload.message_id, str(payload.emoji)
        )
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Reaction role")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        if not member or member.bot:
            return
        role_id = await db.get_reaction_role(
            payload.guild_id, payload.message_id, str(payload.emoji)
        )
        if role_id:
            role = guild.get_role(role_id)
            if role:
                try:
                    await member.remove_roles(role, reason="Reaction role removed")
                except discord.Forbidden:
                    pass

    @commands.command(name="reactroles", aliases=["reaktionsrollen"])
    @commands.has_permissions(manage_roles=True)
    async def setup_reaction_roles(
        self, ctx, message_id: int, emoji: str, role: discord.Role
    ):
        """Attach a reaction role to a message. Usage: !reactroles <message_id> <emoji> <@role>"""
        try:
            message = await ctx.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("❌ Message not found in this channel.", delete_after=8)
            return
        except discord.Forbidden:
            await ctx.send("❌ I can't read that message.", delete_after=8)
            return

        await db.add_reaction_role(ctx.guild.id, message_id, emoji, role.id)
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(
                "⚠️ Role saved, but I couldn't add the reaction (invalid emoji?)."
            )
            return
        await ctx.send(
            f"✅ Reaction role set: reacting with {emoji} on that message will assign **{role.name}**.",
            delete_after=15,
        )

    @commands.command(name="removereactrole")
    @commands.has_permissions(manage_roles=True)
    async def remove_reaction_role(self, ctx, message_id: int, emoji: str):
        """Remove a reaction role binding. Usage: !removereactrole <message_id> <emoji>"""
        await db.remove_reaction_role(ctx.guild.id, message_id, emoji)
        await ctx.send(
            f"✅ Reaction role for {emoji} on that message removed.", delete_after=10
        )

    @commands.command(name="listreactroles")
    @commands.has_permissions(manage_roles=True)
    async def list_reaction_roles(self, ctx):
        """List all active reaction roles in this server."""
        rows = await db.get_all_reaction_roles(ctx.guild.id)
        if not rows:
            await ctx.send("No reaction roles configured.", delete_after=8)
            return
        lines = []
        for r in rows:
            role = ctx.guild.get_role(r["role_id"])
            role_str = role.mention if role else f"<deleted role {r['role_id']}>"
            lines.append(f"Message `{r['message_id']}` · {r['emoji']} → {role_str}")
        embed = discord.Embed(
            title="⚙️ Reaction Roles",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)

    # ------------------------------------------------------------------ on_member_join

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        await _ensure_defaults(member.guild.id)
        thresholds = await db.get_role_thresholds(member.guild.id)
        zero_day = next(
            (r["role_name"] for r in thresholds if r["days_required"] == 0), None
        )
        if not zero_day:
            return
        role = _find_role_normalized(member.guild, zero_day)
        if role:
            try:
                await member.add_roles(role)
                logger.info(
                    "Assigned '%s' to %s on join.", zero_day, member.display_name
                )
            except (discord.Forbidden, discord.HTTPException):
                pass


# ---------------------------------------------------------------------------
# Role Creator UI
# ---------------------------------------------------------------------------


class RoleCreatorView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This panel isn't for you.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="Create Role", style=discord.ButtonStyle.green)
    async def create_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_RoleCreateModal(self.ctx))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _RoleCreateModal(discord.ui.Modal, title="Create Role"):  # type: ignore[call-arg]
    name = discord.ui.TextInput(label="Role name", max_length=100)
    color = discord.ui.TextInput(
        label="Color (hex, e.g. #3498db)",
        placeholder="#000000",
        required=False,
        max_length=7,
    )
    hoist = discord.ui.TextInput(
        label="Show separately in member list? (yes/no)",
        placeholder="no",
        required=False,
        max_length=3,
    )
    mentionable = discord.ui.TextInput(
        label="Mentionable by everyone? (yes/no)",
        placeholder="no",
        required=False,
        max_length=3,
    )

    def __init__(self, ctx: commands.Context):
        super().__init__()
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction):
        col = discord.Color.default()
        if self.color.value.strip():
            try:
                col = _parse_color(self.color.value)
            except (ValueError, OverflowError):
                await interaction.response.send_message(
                    "❌ Invalid color — use hex like `#3498db`.", ephemeral=True
                )
                return

        do_hoist = self.hoist.value.strip().lower() in ("yes", "y", "true", "1")
        do_mention = self.mentionable.value.strip().lower() in ("yes", "y", "true", "1")

        try:
            role = await interaction.guild.create_role(
                name=self.name.value,
                color=col,
                hoist=do_hoist,
                mentionable=do_mention,
            )
            await interaction.response.send_message(
                f"✅ Created role **{role.name}**.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don't have permission to create roles.", ephemeral=True
            )
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed: {e}", ephemeral=True)


# ---------------------------------------------------------------------------
# Role Settings UI (time thresholds)
# ---------------------------------------------------------------------------


class RoleSettingsView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.message: discord.Message | None = None

    async def build_embed(self) -> discord.Embed:
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        embed = discord.Embed(
            title="⏱️ Time-Based Role Thresholds",
            color=discord.Color.blurple(),
        )
        if thresholds:
            lines = [
                f"**{r['role_name']}** — {r['days_required']} day(s)"
                for r in thresholds
            ]
            embed.description = "\n".join(lines)
        else:
            embed.description = "No thresholds configured."
        embed.set_footer(text="Add / Edit / Remove thresholds using the buttons below.")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "This panel isn't for you.", ephemeral=True
            )
            return False
        return True

    async def _refresh(self, interaction: discord.Interaction):
        await interaction.message.edit(embed=await self.build_embed(), view=self)

    @discord.ui.button(label="Add / Edit", style=discord.ButtonStyle.green, row=0)
    async def add_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(_ThresholdAddModal(self))

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red, row=0)
    async def remove_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        thresholds = await db.get_role_thresholds(self.ctx.guild.id)
        if not thresholds:
            await interaction.response.send_message(
                "No thresholds to remove.", ephemeral=True
            )
            return
        view = _RemoveThresholdView(self, thresholds)
        await interaction.response.send_message(
            "Select a role threshold to remove:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Reset to Defaults", style=discord.ButtonStyle.grey, row=0)
    async def reset_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        for name, days in _DEFAULT_THRESHOLDS:
            await db.set_role_threshold(self.ctx.guild.id, name, days)
        await interaction.response.defer()
        await self._refresh(interaction)

    @discord.ui.button(
        label="Run Assignment Now", style=discord.ButtonStyle.blurple, row=1
    )
    async def run_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cog: RoleCog = interaction.client.get_cog("RoleCog")
        if cog:
            count = await cog._assign_roles(interaction.guild)
            await interaction.followup.send(
                f"✅ Assignment complete — {count} role(s) assigned.", ephemeral=True
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass


class _ThresholdAddModal(discord.ui.Modal, title="Add / Edit Threshold"):  # type: ignore[call-arg]
    role_name = discord.ui.TextInput(
        label="Role name (must exist in server)", max_length=100
    )
    days = discord.ui.TextInput(
        label="Days in server required", placeholder="0", max_length=5
    )

    def __init__(self, parent: RoleSettingsView):
        super().__init__()
        self.parent = parent

    async def on_submit(self, interaction: discord.Interaction):
        try:
            d = int(self.days.value)
            if d < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(
                "Days must be a non-negative integer.", ephemeral=True
            )
            return
        # Store with Discord's original casing if the role exists
        discord_role = _find_role_normalized(
            interaction.guild, self.role_name.value.strip()
        )
        store_name = discord_role.name if discord_role else self.role_name.value.strip()
        await db.set_role_threshold(interaction.guild.id, store_name, d)
        await interaction.response.defer()
        await self.parent._refresh(interaction)


class _RemoveSelect(discord.ui.Select):
    def __init__(self, parent: RoleSettingsView, thresholds: list[dict]):
        self.parent = parent
        options = [
            discord.SelectOption(
                label=r["role_name"],
                value=r["role_name"],
                description=f"{r['days_required']} day(s)",
            )
            for r in thresholds
        ][:25]
        super().__init__(placeholder="Choose a threshold to remove…", options=options)

    async def callback(self, interaction: discord.Interaction):
        await db.remove_role_threshold(interaction.guild.id, self.values[0])
        await interaction.response.send_message(
            f"✅ Removed **{self.values[0]}** from auto-assignment.", ephemeral=True
        )
        await self.parent._refresh(interaction)


class _RemoveThresholdView(discord.ui.View):
    def __init__(self, parent: RoleSettingsView, thresholds: list[dict]):
        super().__init__(timeout=60)
        self.add_item(_RemoveSelect(parent, thresholds))


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleCog(bot))
    logger.info("RoleCog loaded.")
