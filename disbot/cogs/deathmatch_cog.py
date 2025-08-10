# cogs/deathmatch_cog.py

import discord
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import asyncio
import json
import os
import random

LEADERBOARD_FILE = os.path.join("data", "leaderboard.json")

class Deathmatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Active duels: {(user1_id, user2_id): Duel}
        self.active_duels = {}
        # Load or initialize leaderboard
        self.leaderboard = self.load_leaderboard()

    def load_leaderboard(self):
        # Ensure the 'data/' directory exists
        os.makedirs(os.path.dirname(LEADERBOARD_FILE), exist_ok=True)
        
        if not os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump({}, f)
            return {}
        with open(LEADERBOARD_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted JSON file
                return {}

    def save_leaderboard(self):
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(self.leaderboard, f, indent=4)

    class Duel:
        def __init__(self, player1, player2):
            self.player1 = player1
            self.player2 = player2
            self.player1_hp = 100
            self.player2_hp = 100
            self.turn = player1  # Player1 starts
            self.is_over = False
            self.defense = {player1.id: False, player2.id: False}  # Defense status

        def attack(self, attacker_id, defender_id):
            base_damage = 15
            critical_hit_chance = 0.1  # 10% chance
            if random.random() < critical_hit_chance:
                damage = base_damage * 2
                critical = True
            else:
                damage = base_damage
                critical = False

            # Check if defender is defending
            if self.defense.get(defender_id, False):
                damage = int(damage / 2)
                self.defense[defender_id] = False  # Reset defense

            # Apply damage
            if defender_id == self.player1.id:
                self.player1_hp -= damage
            else:
                self.player2_hp -= damage

            return damage, critical

        def defend(self, player_id):
            self.defense[player_id] = True

    @commands.command(name='dm_challenge', aliases=['deathmatch', 'challenge'])
    @cooldown(1, 30, BucketType.user)  # 1 use per 30 seconds per user
    async def challenge(self, ctx, opponent: discord.Member):
        """Challenge another user to a deathmatch duel."""
        if opponent == ctx.author:
            await ctx.send("You cannot challenge yourself!")
            return

        if opponent.bot:
            await ctx.send("You cannot challenge a bot!")
            return

        duel_key = tuple(sorted([ctx.author.id, opponent.id]))
        if duel_key in self.active_duels:
            await ctx.send("A duel between you and the opponent is already in progress.")
            return

        # Prevent challenging users who are already in another duel
        for existing_duel in self.active_duels.keys():
            if ctx.author.id in existing_duel or opponent.id in existing_duel:
                await ctx.send("Either you or the opponent is already in a duel.")
                return

        # Send a challenge message with reactions
        embed = discord.Embed(
            title="Deathmatch Challenge",
            description=f"{ctx.author.mention} has challenged {opponent.mention} to a duel!\n\nReact with ✅ to accept or ❌ to decline.",
            color=discord.Color.red(),
            timestamp=ctx.message.created_at
        )
        embed.set_footer(text="You have 30 seconds to respond.")
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")

        def check(reaction, user):
            return (
                user == opponent and 
                str(reaction.emoji) in ["✅", "❌"] and 
                reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send(f"{opponent.mention} did not respond in time. Challenge canceled.")
            await message.delete()
            return

        if str(reaction.emoji) == "✅":
            await ctx.send(f"{opponent.mention} accepted the duel! Let the battle begin!")
            # Initialize and start the duel
            duel = self.Duel(ctx.author, opponent)
            self.active_duels[duel_key] = duel
            await self.start_duel(ctx, duel)
        else:
            await ctx.send(f"{opponent.mention} declined the duel.")
            await message.delete()

    @commands.command(name='dm_leaderboard', aliases=['dm_lb', 'board'])
    async def leaderboard_cmd(self, ctx):
        """Display the Deathmatch leaderboard."""
        if not self.leaderboard:
            await ctx.send("No battles have been recorded yet.")
            return

        sorted_lb = sorted(self.leaderboard.items(), key=lambda x: x[1]['wins'], reverse=True)
        embed = discord.Embed(
            title="Deathmatch Leaderboard",
            description="Top players by wins",
            color=discord.Color.gold(),
            timestamp=ctx.message.created_at
        )
        for idx, (user_id, stats) in enumerate(sorted_lb, start=1):
            user = self.bot.get_user(int(user_id))
            if user:
                embed.add_field(
                    name=f"{idx}. {user.name}",
                    value=f"Wins: {stats['wins']} | Losses: {stats['losses']}",
                    inline=False
                )
        await ctx.send(embed=embed)

    async def start_duel(self, ctx, duel):
        """Manage the duel flow."""
        embed = discord.Embed(
            title="Deathmatch Started!",
            description=f"{duel.player1.mention} vs {duel.player2.mention}\n\nBoth players have **100 HP**.\nIt's {duel.turn.mention}'s turn!",
            color=discord.Color.dark_red(),
            timestamp=ctx.message.created_at
        )
        duel_message = await ctx.send(embed=embed)

        while not duel.is_over:
            current_player = duel.turn
            opponent = duel.player2 if current_player == duel.player1 else duel.player1

            # Update duel status
            embed = discord.Embed(
                title="Deathmatch In Progress",
                description=(
                    f"{duel.player1.mention}: **{duel.player1_hp} HP**\n"
                    f"{duel.player2.mention}: **{duel.player2_hp} HP**\n\n"
                    f"It's {current_player.mention}'s turn!\n\n"
                    f"Choose your action: `attack` or `defend`."
                ),
                color=discord.Color.dark_red(),
                timestamp=ctx.message.created_at
            )
            await duel_message.edit(embed=embed)

            def check(m):
                return (
                    m.author == current_player and 
                    m.channel == ctx.channel and 
                    m.content.lower() in ['attack', 'defend']
                )

            try:
                await ctx.send(f"{current_player.mention}, choose your action (`attack` or `defend`):")
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send(f"{current_player.mention} took too long to respond. {opponent.mention} wins by default!")
                self.update_leaderboard(winner=opponent.id, loser=current_player.id)
                duel.is_over = True
                del self.active_duels[tuple(sorted([duel.player1.id, duel.player2.id]))]
                return

            action = msg.content.lower()
            if action == 'attack':
                damage, critical = duel.attack(current_player.id, opponent.id)
                attack_msg = f"{current_player.mention} attacks {opponent.mention} for **{damage} damage**!"
                if critical:
                    attack_msg += " **Critical Hit!**"
                await ctx.send(attack_msg)
            elif action == 'defend':
                duel.defend(current_player.id)
                await ctx.send(f"{current_player.mention} is defending against the next attack!")

            # Check for win condition
            if duel.player1_hp <= 0:
                await ctx.send(f"{duel.player1.mention} has been defeated! {duel.player2.mention} wins!")
                self.update_leaderboard(winner=duel.player2.id, loser=duel.player1.id)
                duel.is_over = True
            elif duel.player2_hp <= 0:
                await ctx.send(f"{duel.player2.mention} has been defeated! {duel.player1.mention} wins!")
                self.update_leaderboard(winner=duel.player1.id, loser=duel.player2.id)
                duel.is_over = True
            else:
                # Switch turn
                duel.turn = opponent

        # Final duel status
        embed = discord.Embed(
            title="Deathmatch Ended",
            description=(
                f"{duel.player1.mention}: **{max(duel.player1_hp, 0)} HP**\n"
                f"{duel.player2.mention}: **{max(duel.player2_hp, 0)} HP**"
            ),
            color=discord.Color.green() if duel.player1_hp > duel.player2_hp else discord.Color.red(),
            timestamp=ctx.message.created_at
        )
        await duel_message.edit(embed=embed)
        self.save_leaderboard()

    def update_leaderboard(self, winner_id, loser_id):
        """Update the leaderboard with the duel results."""
        if str(winner_id) not in self.leaderboard:
            self.leaderboard[str(winner_id)] = {"wins": 0, "losses": 0}
        if str(loser_id) not in self.leaderboard:
            self.leaderboard[str(loser_id)] = {"wins": 0, "losses": 0}

        self.leaderboard[str(winner_id)]['wins'] += 1
        self.leaderboard[str(loser_id)]['losses'] += 1

    @challenge.error
    async def challenge_error(self, ctx, error):
        """Handle errors for the challenge command."""
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"You're on cooldown! Please try again in {int(error.retry_after)} seconds.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Couldn't find the user. Please mention a valid member.")
        else:
            await ctx.send("An error occurred while processing the command.")
            raise error  # Re-raise the error for debugging purposes

    @commands.command(name='dm_help', aliases=['deathmatch_help'])
    async def dm_help(self, ctx):
        """Display help information for Deathmatch commands."""
        embed = discord.Embed(
            title="Deathmatch Help",
            description=(
                "**Commands:**\n"
                "`!deathmatch @User` - Challenge a user to a duel.\n"
                "`!board` - View the top duelists.\n\n"
                "**During a Duel:**\n"
                "`attack` - Perform an attack on your opponent.\n"
                "`defend` - Defend against your opponent's next attack."
            ),
            color=discord.Color.blue(),
            timestamp=ctx.message.created_at
        )
        await ctx.send(embed=embed)

# Asynchronous setup function for discord.py v2.x
async def setup(bot):
    await bot.add_cog(Deathmatch(bot))
