import discord
from discord.ext import commands
from utils.data_manager import DatabaseManager
from helpers.embed_helper import create_embed, success_embed, error_embed
from helpers.button_helper import create_button_view

TABLES = [
    "users",
    "user_progress",
    "inventory",
    "equipped_items",
    "items",
    "item_aliases",
    "bot_info",
    "exploration_data"
]

# Modal for updating a cell with a chosen column.
class UpdateColumnModal(discord.ui.Modal, title="Update Table Cell"):
    # These values will be set by the UI.
    table_name: str = None
    column: str = None

    condition = discord.ui.TextInput(label="Condition (WHERE clause)", placeholder="e.g. id = 1", required=True)
    new_value = discord.ui.TextInput(label="New Value", placeholder="e.g. 1.0.6 or 'new text'", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Build the query using the table and column from the view.
        query = f"UPDATE {self.table_name} SET {self.column} = ? WHERE {self.condition.value}"
        try:
            await DatabaseManager.execute_query(query, (self.new_value.value,))
            await interaction.response.send_message(success_embed(f"Successfully updated {self.column} in {self.table_name}."), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(error_embed(f"Update failed: {e}"), ephemeral=True)

# View for selecting a column from a table.
class ColumnSelectView(discord.ui.View):
    def __init__(self, table: str):
        super().__init__(timeout=60)
        self.table = table
        self.columns = []  # Will be loaded asynchronously.
        # We'll add a "Back" button at the end.
        self.add_item(discord.ui.Button(label="Back", style=discord.ButtonStyle.secondary, custom_id="back_to_tables"))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)

    async def load_columns(self):
        self.columns = await DatabaseManager.get_table_columns(self.table)
        for col in self.columns:
            # Create a button for each column.
            button = discord.ui.Button(label=col, style=discord.ButtonStyle.primary)
            button.callback = self.make_column_callback(col)
            self.add_item(button)

    def make_column_callback(self, column: str):
        async def callback(interaction: discord.Interaction):
            modal = UpdateColumnModal()
            modal.table_name = self.table
            modal.column = column
            await interaction.response.send_modal(modal)
        return callback

# View for selecting a table.
class TableSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for table in TABLES:
            button = discord.ui.Button(label=table, style=discord.ButtonStyle.primary)
            button.callback = self.make_table_callback(table)
            self.add_item(button)

    def make_table_callback(self, table: str):
        async def callback(interaction: discord.Interaction):
            # Create a new view for column selection.
            view = ColumnSelectView(table)
            await view.load_columns()
            embed = create_embed(title=f"Table: {table}", description="Select a column to update:", color=discord.Color.blue())
            await interaction.response.edit_message(embed=embed, view=view)
        return callback

class DataAdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="dbadmin", description="Data Admin: View and edit the SQLite database. (Owner only)")
    @commands.is_owner()
    async def dbadmin(self, ctx: commands.Context):
        embed = create_embed(
            title="Database Administration",
            description="Select a table to view/edit:",
            color=discord.Color.blue()
        )
        view = TableSelectView()
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="viewtable", description="View the first few rows of a table. (Owner only)")
    @commands.is_owner()
    async def viewtable(self, ctx: commands.Context, table: str, limit: int = 10):
        query = f"SELECT * FROM {table} LIMIT ?"
        try:
            rows = await DatabaseManager.execute_query(query, (limit,), fetch_all=True)
            if not rows:
                await ctx.send(embed=error_embed(f"No data found in table '{table}'"))
                return
            content = "\n".join(str(row) for row in rows)
            embed = create_embed(title=f"Table: {table}", description=content, color=discord.Color.green())
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=error_embed(f"Failed to view table '{table}': {e}"))

    @commands.hybrid_command(name="dbquery", description="Run a custom SELECT query. (Owner only)")
    @commands.is_owner()
    async def dbquery(self, ctx: commands.Context):
        modal = DBQueryModal()
        await ctx.send_modal(modal)

# Modal for custom SELECT queries.
class DBQueryModal(discord.ui.Modal, title="Run Custom SELECT Query"):
    query = discord.ui.TextInput(label="SQL Query", placeholder="e.g. SELECT * FROM users LIMIT 5", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not self.query.value.strip().lower().startswith("select"):
                await interaction.response.send_message(error_embed("Only SELECT queries are allowed."), ephemeral=True)
                return
            rows = await DatabaseManager.execute_query(self.query.value, fetch_all=True)
            content = "\n".join(str(row) for row in rows) if rows else "No results."
            embed = create_embed(title="Query Results", description=content, color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(error_embed(f"Query failed: {e}"), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(DataAdminCog(bot))