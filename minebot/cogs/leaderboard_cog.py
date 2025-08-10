import discord
from discord.ext import commands
import aiosqlite
import json
import logging
from config import Config

class LeaderboardCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Create the leaderboard table on startup
        self.bot.loop.create_task(self.create_leaderboard_table())

    async def create_leaderboard_table(self):
        """Creates the 'leaderboard' table if it doesn't exist."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard (
                        user_id TEXT PRIMARY KEY,
                        total_items INTEGER,
                        last_updated TEXT,
                        total_sessions INTEGER
                    )
                """)
                await db.commit()
                logging.info("Leaderboard table created/verified.")
        except Exception as e:
            logging.error(f"Error creating leaderboard table: {e}")

    async def get_inventory(self, user_id):
        """Fetches a user's inventory from the database."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("SELECT data FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        # Use json.loads instead of eval for safety.
                        return json.loads(row[0])
                    else:
                        return {}
        except Exception as e:
            logging.error(f"Error fetching inventory for user {user_id}: {e}")
            return {}

    async def get_total_items(self, user_id):
        """Calculates the total number of items a user has collected."""
        inventory = await self.get_inventory(user_id)
        return sum(inventory.values())

    async def get_most_collected_item(self, user_id):
        """Finds the player's most collected resource."""
        inventory = await self.get_inventory(user_id)
        if not inventory:
            return "None", 0
        return max(inventory.items(), key=lambda x: x[1])

    async def get_efficiency(self, user_id):
        """Calculates mining efficiency (items per session)."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("SELECT total_items, total_sessions FROM leaderboard WHERE user_id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
            if not row or row[1] == 0:
                return 0  # No sessions recorded
            total_items, total_sessions = row
            return round(total_items / total_sessions, 2)
        except Exception as e:
            logging.error(f"Error calculating efficiency for user {user_id}: {e}")
            return 0

    async def update_leaderboard(self, user_id):
        """Updates the leaderboard with the user's total items."""
        try:
            total_items = await self.get_total_items(user_id)
            async with aiosqlite.connect(Config.DB_FILE) as db:
                await db.execute("""
                    INSERT INTO leaderboard (user_id, total_items, last_updated, total_sessions)
                    VALUES (?, ?, datetime('now'), COALESCE((SELECT total_sessions FROM leaderboard WHERE user_id = ?), 0) + 1)
                    ON CONFLICT(user_id) DO UPDATE SET total_items = ?, last_updated = datetime('now'), total_sessions = total_sessions + 1
                """, (user_id, total_items, user_id, total_items))
                await db.commit()
            logging.info(f"Leaderboard updated for user {user_id}.")
        except Exception as e:
            logging.error(f"Error updating leaderboard for user {user_id}: {e}")

    @commands.command()
    async def stats(self, ctx, member: discord.Member = None):
        """Shows detailed player mining stats."""
        try:
            user_id = str(member.id if member else ctx.author.id)
            inventory = await self.get_inventory(user_id)
            total_items = sum(inventory.values())
            most_collected, most_collected_amt = await self.get_most_collected_item(user_id)
            efficiency = await self.get_efficiency(user_id)

            inventory_text = "\n".join([f"**{item}**: {count}" for item, count in inventory.items()]) if inventory else "No items collected yet."

            embed = discord.Embed(
                title=f"📊 {(member.display_name if member else ctx.author.display_name)}'s Stats",
                color=discord.Color.purple()
            )
            embed.add_field(name="Total Items Collected", value=f"{total_items} items", inline=False)
            embed.add_field(name="Most Collected Resource", value=f"**{most_collected}** ({most_collected_amt}x)", inline=False)
            embed.add_field(name="Mining Efficiency", value=f"{efficiency} items/session", inline=False)
            embed.add_field(name="Inventory Breakdown", value=inventory_text, inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"Error in stats command: {e}"
            logging.error(error_msg)
            await ctx.send(error_msg)

    @commands.command()
    async def topresource(self, ctx):
        """Finds the most collected resource among all players."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("SELECT data FROM inventory") as cursor:
                    all_inventories = await cursor.fetchall()

            total_counts = {}
            for row in all_inventories:
                inv = json.loads(row[0])
                for item, count in inv.items():
                    total_counts[item] = total_counts.get(item, 0) + count

            if not total_counts:
                return await ctx.send("No data available.")

            top_resource, top_amount = max(total_counts.items(), key=lambda x: x[1])
            embed = discord.Embed(
                title="🌟 Most Collected Resource",
                description=f"**{top_resource}** ({top_amount}x collected by all players)",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            error_msg = f"Error in topresource command: {e}"
            logging.error(error_msg)
            await ctx.send(error_msg)

    @commands.command()
    async def leaderboard(self, ctx):
        """Displays the leaderboard of all players sorted by total items collected."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("""
                    SELECT user_id, total_items, total_sessions, last_updated
                    FROM leaderboard
                    ORDER BY total_items DESC
                """) as cursor:
                    rows = await cursor.fetchall()

            if not rows:
                return await ctx.send("No leaderboard data available.")

            leaderboard_entries = []
            for index, (user_id, total_items, total_sessions, last_updated) in enumerate(rows, start=1):
                user = self.bot.get_user(int(user_id))
                username = user.display_name if user else f"User ID {user_id}"
                efficiency = round(total_items / total_sessions, 2) if total_sessions > 0 else 0
                leaderboard_entries.append(f"**{index}. {username}** - {total_items} items, {total_sessions} sessions, {efficiency} items/session")

            description = "\n".join(leaderboard_entries)
            embed = discord.Embed(
                title="🏆 Leaderboard",
                description=description,
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error displaying leaderboard: {e}")
            await ctx.send(f"Error displaying leaderboard: {e}")

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        """Shows your ranking on the leaderboard."""
        try:
            target = member or ctx.author
            user_id = str(target.id)
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("""
                    SELECT user_id, total_items, total_sessions
                    FROM leaderboard
                    ORDER BY total_items DESC
                """) as cursor:
                    rows = await cursor.fetchall()

            if not rows:
                return await ctx.send("No leaderboard data available.")

            rank = None
            leaderboard_list = []
            for i, (uid, total_items, total_sessions) in enumerate(rows, start=1):
                efficiency = round(total_items / total_sessions, 2) if total_sessions > 0 else 0
                leaderboard_list.append((uid, total_items, total_sessions, efficiency))
                if uid == user_id:
                    rank = i
                    user_total_items = total_items
                    user_sessions = total_sessions
                    user_efficiency = efficiency

            if rank is None:
                return await ctx.send("You are not on the leaderboard yet. Try collecting some items!")

            embed = discord.Embed(
                title=f"🏅 {target.display_name}'s Ranking",
                color=discord.Color.blue()
            )
            embed.add_field(name="Rank", value=f"#{rank}", inline=True)
            embed.add_field(name="Total Items", value=f"{user_total_items}", inline=True)
            embed.add_field(name="Sessions", value=f"{user_sessions}", inline=True)
            embed.add_field(name="Efficiency", value=f"{user_efficiency} items/session", inline=True)

            # Optionally, include the top 3 players as context.
            top_entries = leaderboard_list[:3]
            top_text = ""
            for i, (uid, t_items, t_sessions, eff) in enumerate(top_entries, start=1):
                user = self.bot.get_user(int(uid))
                name = user.display_name if user else f"User {uid}"
                top_text += f"**{i}. {name}** - {t_items} items\n"
            embed.add_field(name="Top Players", value=top_text, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error in rank command: {e}")
            await ctx.send(f"Error in rank command: {e}")

    @commands.command()
    async def resourceinfo(self, ctx):
        """Provides detailed information about each resource collected by players."""
        try:
            async with aiosqlite.connect(Config.DB_FILE) as db:
                async with db.execute("SELECT data FROM inventory") as cursor:
                    all_inventories = await cursor.fetchall()

            if not all_inventories:
                return await ctx.send("No inventory data available.")

            resource_totals = {}
            resource_players = {}
            for row in all_inventories:
                inv = json.loads(row[0])
                for resource, count in inv.items():
                    resource_totals[resource] = resource_totals.get(resource, 0) + count
                    resource_players[resource] = resource_players.get(resource, 0) + 1

            info_lines = []
            for resource in resource_totals:
                total = resource_totals[resource]
                players = resource_players[resource]
                average = total / players if players > 0 else 0
                info_lines.append(f"**{resource}**: Total: {total}, Players: {players}, Avg: {average:.2f}")
            info_text = "\n".join(info_lines)
            embed = discord.Embed(
                title="📋 Resource Information",
                description=info_text,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"Error in resourceinfo command: {e}")
            await ctx.send(f"Error in resourceinfo command: {e}")

async def setup(bot):
    await bot.add_cog(LeaderboardCog(bot))