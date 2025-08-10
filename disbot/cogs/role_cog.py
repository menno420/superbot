import discord
from discord.ext import commands, tasks
from datetime import datetime
import logging

logger = logging.getLogger("bot")

class RoleCog(commands.Cog):
    """
    RoleCog automatically assigns roles based on time in the server
    and provides commands to check and manage role assignments.
    """

    def __init__(self, bot):
        self.bot = bot
        self.role_check.start()

    def cog_unload(self):
        self.role_check.cancel()

    @tasks.loop(hours=24)
    async def role_check(self):
        """Periodically checks and assigns roles."""
        await self.assign_roles()

    @role_check.before_loop
    async def before_role_check(self):
        await self.bot.wait_until_ready()

    async def assign_roles(self, ctx=None):
        """Assigns roles based on join time while keeping the highest role and removing outdated progression roles."""
        guild = self.bot.get_guild(1348216920993693716)  # Replace with your guild ID
        if not guild:
            logger.error("❌ Guild not found!")
            return

        role_mapping = {
            "Neu": 0,
            "Normal": 1,
            "Iron": 7,
            "Gold": 30,
            "Diamand": 365,
            "Netherite": 730,
            "Beacon": 1825,
        }

        progression_roles = list(role_mapping.keys())  # Ordered list of progression roles
        assigned_roles = 0
        admin_role = discord.utils.get(guild.roles, name="Admin")  # Exclude Admins

        for member in guild.members:
            if member.bot or (admin_role and admin_role in member.roles):
                if admin_role in member.roles:
                    logger.info(f"⏩ Skipping {member.display_name} (Admin role detected)")
                continue  # Skip bots and admins

            if not member.joined_at:
                logger.warning(f"⚠️ {member.display_name} has no join date, skipping...")
                continue

            # Convert to naive datetime for correct calculations
            join_date = member.joined_at.replace(tzinfo=None)
            days_in_server = (datetime.utcnow() - join_date).days

            # Determine the highest role the member qualifies for
            new_role = None
            for role_name, required_days in role_mapping.items():
                if days_in_server >= required_days:
                    new_role = role_name  # Member qualifies for this role

            role_to_add = discord.utils.get(guild.roles, name=new_role) if new_role else None

            # Check if the member already has a **higher** role
            current_highest_role = None
            for role in member.roles:
                if role.name in progression_roles:
                    if current_highest_role is None or progression_roles.index(role.name) > progression_roles.index(current_highest_role):
                        current_highest_role = role.name

            # Prevent assigning a lower role if they already have a higher one
            if current_highest_role and role_to_add and progression_roles.index(current_highest_role) > progression_roles.index(new_role):
                logger.info(f"⏩ Skipping {member.display_name} (Already has higher role: {current_highest_role})")
                continue  # Skip further processing for this member

            # Identify outdated progression roles to remove (ONLY from progression list, except the highest one)
            roles_to_remove = [
                role for role in member.roles
                if role.name in progression_roles and role != role_to_add and role.name != current_highest_role
            ]

            if roles_to_remove:
                try:
                    await member.remove_roles(*roles_to_remove)
                    logger.info(f"✅ Removed outdated roles from {member.display_name}: {[r.name for r in roles_to_remove]}")
                except discord.Forbidden:
                    logger.error(f"❌ Cannot remove roles from {member.display_name} (Missing permissions)")
                except discord.HTTPException as e:
                    logger.error(f"❌ Failed to remove roles from {member.display_name}: {e}")

            # Assign new role if necessary
            if role_to_add and role_to_add not in member.roles:
                try:
                    await member.add_roles(role_to_add)
                    assigned_roles += 1
                    logger.info(f"✅ Assigned {role_to_add.name} to {member.display_name}")

                except discord.Forbidden:
                    logger.error(f"❌ Cannot assign {role_to_add.name} to {member.display_name} (Missing permissions)")
                except discord.HTTPException as e:
                    logger.error(f"❌ Failed to assign {role_to_add.name} to {member.display_name}: {e}")

        if ctx:
            await ctx.send(f"✅ Assigned roles to {assigned_roles} members.")

    @commands.command(name="assignroles", help="Manually assigns roles based on member join time.")
    @commands.has_permissions(administrator=True)
    async def assign_roles_command(self, ctx):
        """Triggers role assignment manually with detailed error logging."""
        await ctx.send("🔄 Checking and assigning roles...")
        try:
            await self.assign_roles(ctx)
        except Exception as e:
            logger.error(f"❌ Error in assign_roles: {e}", exc_info=True)
            await ctx.send(f"⚠️ An error occurred: `{e}`")

    @commands.command(name="roles", help="Displays all roles in the server with member counts.")
    async def roles(self, ctx):
        """Lists roles and the number of members assigned to each."""
        logger.info(f"Bot can see {len(ctx.guild.members)} members.")

        roles = ctx.guild.roles
        roles_list = "\n".join([
            f"{role.name} - {sum(1 for member in ctx.guild.members if role in member.roles)} members"
            for role in roles if role != ctx.guild.default_role
        ])

        embed = discord.Embed(
            title=f"Roles in {ctx.guild.name}",
            description=roles_list or "No roles found.",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)

    @commands.command(name="debug_roles")
    async def debug_roles(self, ctx):
        """Prints all role names for verification."""
        roles = [role.name for role in ctx.guild.roles]
        await ctx.send(f"Available Roles: {', '.join(roles)}")

    @commands.command(name="refresh_members")
    async def refresh_members(self, ctx):
        """Forces the bot to fetch all members."""
        await ctx.guild.chunk()
        await ctx.send("✅ Fetched all members from the server.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Automatically assigns the 'Neu' role when a new member joins, unless they are an Admin or already have a higher role."""
        if member.bot:
            return  # Ignore bots

        guild = member.guild
        neu_role = discord.utils.get(guild.roles, name="Neu")
        admin_role = discord.utils.get(guild.roles, name="Admin")  # Exclude Admins

        if admin_role and admin_role in member.roles:
            logger.info(f"⏩ Skipping {member.display_name} (Admin role detected on join)")
            return

        if neu_role and not any(role.name in ["Normal", "Iron", "Gold", "Diamand", "Netherite", "Beacon"] for role in member.roles):
            try:
                await member.add_roles(neu_role)
                logger.info(f"✅ Assigned 'Neu' role to {member.display_name} upon joining.")
            except discord.Forbidden:
                logger.error(f"❌ Cannot assign 'Neu' role to {member.display_name} (Missing permissions)")
            except discord.HTTPException as e:
                logger.error(f"❌ Failed to assign 'Neu' role to {member.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(RoleCog(bot))