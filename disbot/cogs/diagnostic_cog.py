import discord
from discord.ext import commands
import psutil
import platform
import shutil
import asyncio
import datetime
import os  # Added for os.listdir usage

# Import DataManager from utils
from utils.data_manager import DataManager

class DiagnosticCog(commands.Cog):
    """
    DiagnosticCog provides advanced diagnostics and monitoring tools for the Discord bot.
    """
    def __init__(self, bot):
        self.bot = bot
        self.logger = DataManager.logger  # Utilize DataManager's logger

    # ==========================
    # Command Overview
    # ==========================

    @commands.command(name='list_commands_detailed', aliases=['listcmds'])
    @commands.has_permissions(administrator=True)
    async def list_commands_detailed(self, ctx):
        """
        List all registered commands with detailed information.
        Organized by cog for clarity.
        Usage: !list_commands_detailed
        """
        try:
            embed = discord.Embed(title="Detailed Command List", color=discord.Color.blue())
            commands_by_cog = {}
            for cog in self.bot.cogs:
                commands_by_cog[cog] = []
                for command in self.bot.cogs[cog].get_commands():
                    cmd_info = {
                        "Name": command.name,
                        "Description": command.help or "No description provided.",
                        "Cooldown": f"{command._buckets._cooldown.rate} uses per {command._buckets._cooldown.per} seconds" if command._buckets._cooldown else "No cooldown",
                        "Permissions": ", ".join([perm.replace('_', ' ').title() for perm in command._perms]) if command._perms else "Default",
                        "Aliases": ", ".join(command.aliases) if command.aliases else "None"
                    }
                    commands_by_cog[cog].append(cmd_info)

            for cog, commands in commands_by_cog.items():
                if commands:
                    field_value = ""
                    for cmd in commands:
                        field_value += f"**Name:** {cmd['Name']}\n" \
                                       f"**Description:** {cmd['Description']}\n" \
                                       f"**Cooldown:** {cmd['Cooldown']}\n" \
                                       f"**Permissions:** {cmd['Permissions']}\n" \
                                       f"**Aliases:** {cmd['Aliases']}\n\n"
                    embed.add_field(name=cog, value=field_value, inline=False)

            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: list_commands_detailed by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while listing commands.", delete_after=10)
            self.logger.error(f"Error in list_commands_detailed: {e}")

    @commands.command(name='find_command', aliases=['findcmd'])
    @commands.has_permissions(administrator=True)
    async def find_command(self, ctx, keyword: str):
        """
        Search for commands by keyword or partial match in their name or description.
        Usage: !find_command <keyword>
        """
        try:
            embed = discord.Embed(title=f"Search Results for '{keyword}'", color=discord.Color.green())
            found = False
            for cog in self.bot.cogs:
                for command in self.bot.cogs[cog].get_commands():
                    if keyword.lower() in command.name.lower() or (command.help and keyword.lower() in command.help.lower()):
                        found = True
                        embed.add_field(
                            name=command.name,
                            value=f"**Description:** {command.help or 'No description provided.'}\n" \
                                  f"**Cooldown:** {f'{command._buckets._cooldown.rate} uses per {command._buckets._cooldown.per} seconds' if command._buckets._cooldown else 'No cooldown'}\n" \
                                  f"**Permissions:** {', '.join([perm.replace('_', ' ').title() for perm in command._perms]) if command._perms else 'Default'}\n" \
                                  f"**Aliases:** {', '.join(command.aliases) if command.aliases else 'None'}\n" \
                                  f"**Cog:** {cog}",
                            inline=False
                        )
            if not found:
                embed.description = "No commands found matching the keyword."
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: find_command '{keyword}' by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while searching for commands.", delete_after=10)
            self.logger.error(f"Error in find_command: {e}")

    # ==========================
    # Data Integrity and Validation
    # ==========================

    @commands.command(name='validate_json_files', aliases=['validatejson'])
    @commands.has_permissions(administrator=True)
    async def validate_json_files(self, ctx):
        """
        Validate the structure and content of all JSON files the bot uses.
        Usage: !validate_json_files
        """
        try:
            embed = discord.Embed(title="JSON Files Validation Results", color=discord.Color.orange())
            json_files = DataManager.JSON_DIR
            discrepancies_found = False
            for filename in os.listdir(json_files):
                if filename.endswith('.json'):
                    data = DataManager.read_json(filename, read_only=True)
                    if data is None:
                        embed.add_field(name=filename, value="Failed to load or parse JSON.", inline=False)
                        discrepancies_found = True
                        continue
                    # Example validation: Check if data is a list or dict
                    if not isinstance(data, (list, dict)):
                        embed.add_field(name=filename, value="Invalid JSON structure. Expected list or dict.", inline=False)
                        discrepancies_found = True
                    else:
                        embed.add_field(name=filename, value="Valid JSON structure.", inline=False)
            if not discrepancies_found:
                embed.description = "All JSON files are valid and correctly formatted."
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: validate_json_files by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred during JSON files validation.", delete_after=10)
            self.logger.error(f"Error in validate_json_files: {e}")

    @commands.command(name='check_database', aliases=['checkdb'])
    @commands.has_permissions(administrator=True)
    async def check_database(self, ctx):
        """
        Verify that all registered tables exist in the database.
        Validate the schema of critical tables against expected structures.
        Usage: !check_database
        """
        try:
            expected_tables = list(DataManager._registered_tables.keys())
            existing_tables = DataManager.fetch_all("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {table['name'] for table in existing_tables}

            missing_tables = set(expected_tables) - existing_tables
            extra_tables = existing_tables - set(expected_tables)

            embed = discord.Embed(title="Database Schema Validation", color=discord.Color.purple())

            if missing_tables:
                embed.add_field(name="Missing Tables", value=", ".join(missing_tables), inline=False)
            else:
                embed.add_field(name="Missing Tables", value="None", inline=False)

            if extra_tables:
                embed.add_field(name="Extra Tables", value=", ".join(extra_tables), inline=False)
            else:
                embed.add_field(name="Extra Tables", value="None", inline=False)

            # Validate schema of critical tables
            discrepancies_found = False
            for table, create_stmt in DataManager._registered_tables.items():
                if table not in existing_tables:
                    continue  # Already reported as missing
                # Extract expected columns from CREATE statement
                expected_columns = self._extract_columns_from_create(create_stmt)
                # Fetch actual columns from DB
                actual_columns = DataManager.fetch_all(f"PRAGMA table_info({table});")
                actual_columns = {col['name']: col['type'].upper() for col in actual_columns}

                expected_columns_upper = {k: v.upper() for k, v in expected_columns.items()}

                missing_columns = set(expected_columns_upper.keys()) - set(actual_columns.keys())
                extra_columns = set(actual_columns.keys()) - set(expected_columns_upper.keys())
                type_mismatches = {k: (expected_columns_upper[k], actual_columns[k])
                                   for k in set(expected_columns_upper.keys()) & set(actual_columns.keys())
                                   if expected_columns_upper[k] != actual_columns[k]}

                if missing_columns or extra_columns or type_mismatches:
                    discrepancies_found = True
                    description = ""
                    if missing_columns:
                        description += f"**Missing Columns:** {', '.join(missing_columns)}\n"
                    if extra_columns:
                        description += f"**Extra Columns:** {', '.join(extra_columns)}\n"
                    if type_mismatches:
                        mismatches = ", ".join([f"{col} (Expected: {exp}, Found: {act})"
                                                for col, (exp, act) in type_mismatches.items()])
                        description += f"**Type Mismatches:** {mismatches}\n"
                    embed.add_field(name=f"Table: {table}", value=description, inline=False)

            if not discrepancies_found:
                embed.description = "All critical tables have the correct schema."

            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: check_database by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while checking the database.", delete_after=10)
            self.logger.error(f"Error in check_database: {e}")

    def _extract_columns_from_create(self, create_stmt):
        """
        Helper method to extract column names and types from a CREATE TABLE statement.
        """
        import re
        columns = {}
        pattern = r'\s*(\w+)\s+([\w\(\)]+)'
        matches = re.findall(pattern, create_stmt, re.IGNORECASE)
        for match in matches:
            col_name, col_type = match
            columns[col_name] = col_type
        return columns

    # ==========================
    # Health and Performance Monitoring
    # ==========================

    # Renamed 'bot_status' to 'diagnostic_bot_status' to avoid using reserved prefix
    @commands.command(name='diagnostic_bot_status', aliases=['diag_status'])
    @commands.has_permissions(administrator=True)
    async def diagnostic_bot_status(self, ctx):
        """
        Display bot's health and performance metrics.
        Usage: !diagnostic_bot_status
        """
        try:
            guild_count = len(self.bot.guilds)
            member_count = sum(guild.member_count for guild in self.bot.guilds)
            command_count = len(self.bot.commands)
            uptime_delta = datetime.datetime.utcnow() - self.bot.uptime
            uptime = str(uptime_delta).split('.')[0]  # Remove microseconds

            # CPU and Memory Usage
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent

            embed = discord.Embed(title="Bot Status", color=discord.Color.green())
            embed.add_field(name="Guilds Connected", value=str(guild_count), inline=True)
            embed.add_field(name="Total Members", value=str(member_count), inline=True)
            embed.add_field(name="Commands Loaded", value=str(command_count), inline=True)
            embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
            embed.add_field(name="Memory Usage", value=f"{memory_usage}%", inline=True)
            embed.add_field(name="Uptime", value=uptime, inline=True)
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: diagnostic_bot_status by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while fetching bot status.", delete_after=10)
            self.logger.error(f"Error in diagnostic_bot_status: {e}")

    @commands.command(name='latency', aliases=['ping'])
    @commands.has_permissions(administrator=True)
    async def latency(self, ctx):
        """
        Report the bot’s latency to Discord’s API.
        Usage: !latency
        """
        try:
            latency = self.bot.latency * 1000  # Convert to ms
            embed = discord.Embed(title="Bot Latency", color=discord.Color.blue())
            embed.add_field(name="Latency", value=f"{latency:.2f} ms", inline=True)
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: latency by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while fetching latency.", delete_after=10)
            self.logger.error(f"Error in latency: {e}")

    @commands.command(name='system_info', aliases=['sysinfo'])
    @commands.has_permissions(administrator=True)
    async def system_info(self, ctx):
        """
        Display system-level stats.
        Usage: !system_info
        """
        try:
            python_version = platform.python_version()
            os_info = f"{platform.system()} {platform.release()}"
            data_dir = DataManager.DATA_DIR
            total, used, free = shutil.disk_usage(data_dir)
            total_gb = total / (2**30)
            used_gb = used / (2**30)
            free_gb = free / (2**30)
            embed = discord.Embed(title="System Information", color=discord.Color.teal())
            embed.add_field(name="Python Version", value=python_version, inline=True)
            embed.add_field(name="Operating System", value=os_info, inline=True)
            embed.add_field(
                name=f"Disk Usage for {data_dir}",
                value=f"Total: {total_gb:.2f} GB\nUsed: {used_gb:.2f} GB\nFree: {free_gb:.2f} GB",
                inline=False
            )
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: system_info by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while fetching system information.", delete_after=10)
            self.logger.error(f"Error in system_info: {e}")

    # ==========================
    # Logging and Notifications
    # ==========================

    @commands.command(name='query_logs', aliases=['querylogs'])
    @commands.has_permissions(administrator=True)
    async def query_logs(self, ctx, event_type: str = None, limit: int = 10):
        """
        Query recent logs stored in the logs table.
        Usage: !query_logs [event_type] [limit=10]
        """
        try:
            if event_type:
                event_type = event_type.upper()
            logs = DataManager.query_logs(event_type=event_type, limit=limit)
            if not logs:
                await ctx.send("No logs found matching the criteria.", delete_after=10)
                return
            embed = discord.Embed(title="Queried Logs", color=discord.Color.dark_red())
            for log in logs:
                embed.add_field(
                    name=f"[{log['timestamp']}] {log['level']}",
                    value=log['message'],
                    inline=False
                )
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: query_logs event_type={event_type} limit={limit} by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while querying logs.", delete_after=10)
            self.logger.error(f"Error in query_logs: {e}")

    @commands.command(name='recent_errors', aliases=['errors'])
    @commands.has_permissions(administrator=True)
    async def recent_errors(self, ctx, limit: int = 10):
        """
        Retrieve the most recent ERROR logs for quick diagnostics.
        Usage: !recent_errors [limit=10]
        """
        try:
            logs = DataManager.query_logs(event_type="ERROR", limit=limit)
            if not logs:
                await ctx.send("No recent ERROR logs found.", delete_after=10)
                return
            embed = discord.Embed(title="Recent ERROR Logs", color=discord.Color.red())
            for log in logs:
                embed.add_field(
                    name=f"[{log['timestamp']}] {log['level']}",
                    value=log['message'],
                    inline=False
                )
            await ctx.send(embed=embed)
            self.logger.info(f"Executed command: recent_errors limit={limit} by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while retrieving recent errors.", delete_after=10)
            self.logger.error(f"Error in recent_errors: {e}")

    @commands.command(name='test_notification', aliases=['testnotify'])
    @commands.has_permissions(administrator=True)
    async def test_notification(self, ctx):
        """
        Send a test error notification to the configured webhook.
        Usage: !test_notification
        """
        try:
            DataManager.notify_error("This is a test error notification.")
            await ctx.send("Test error notification sent.", delete_after=10)
            self.logger.info(f"Executed command: test_notification by {ctx.author}")
        except Exception as e:
            await ctx.send("An error occurred while sending test notification.", delete_after=10)
            self.logger.error(f"Error in test_notification: {e}")

    # ==========================
    # Listeners
    # ==========================

    # Renamed 'cog_ready' to 'on_diagnostic_ready' to avoid using reserved prefix
    @commands.Cog.listener()
    async def on_diagnostic_ready(self):
        """
        Listener that triggers when the DiagnosticCog is ready.
        """
        print("Diagnostic Cog Ready")
        self.logger.info("Diagnostic Cog has been loaded and is ready.")

    # ==========================
    # Command Error Handling
    # ==========================

    @list_commands_detailed.error
    @find_command.error
    @validate_json_files.error
    @check_database.error
    @diagnostic_bot_status.error  # Updated method name
    @latency.error
    @system_info.error
    @query_logs.error
    @recent_errors.error
    @test_notification.error
    async def cog_command_error(self, ctx, error):
        """
        Local error handler for DiagnosticCog commands.
        """
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the necessary permissions to use this command.", delete_after=10)
        else:
            await ctx.send("An unexpected error occurred while executing the command.", delete_after=10)
            self.logger.error(f"Error in {ctx.command}: {error}")

# ==========================
# Cog Setup
# ==========================

async def setup(bot):
    await bot.add_cog(DiagnosticCog(bot))
