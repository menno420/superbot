import discord
from discord.ext import commands
from discord import ButtonStyle
import os
import aiosqlite

from config import Config
from helpers.embed_helper import create_embed, error_embed
from utils.admin import reload_json_files
from utils.data_manager import DatabaseManager


class DebugCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="debug", description="Show debug UI with categories.")
    async def debug(self, ctx: commands.Context):
        """Opens the Debug Menu with various categories."""
        view = DebugMenuView(bot=self.bot, user=ctx.author)
        embed = create_embed("🛠️ Debug Menu", "Choose a category to explore:")
        await ctx.send(embed=embed, view=view)


class DebugMenuView(discord.ui.View):
    """Main menu with debug categories."""
    def __init__(self, bot, user, timeout=90):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user

        self.add_item(DebugButton("Commands", "commands", ButtonStyle.primary))
        self.add_item(DebugButton("Cogs", "cogs", ButtonStyle.primary))
        self.add_item(DebugButton("JSON", "json", ButtonStyle.primary))
        self.add_item(DebugButton("DB", "db", ButtonStyle.primary))
        self.add_item(DebugButton("Paths", "paths", ButtonStyle.secondary))
        self.add_item(DebugButton("Helpers", "helpers", ButtonStyle.secondary))
        self.add_item(DebugButton("Utils", "utils", ButtonStyle.secondary))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id


class DebugButton(discord.ui.Button):
    """
    Navigates to the DebugActionView for the chosen category.
    """
    def __init__(self, label: str, category: str, style: ButtonStyle):
        super().__init__(label=label, style=style)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        view = DebugActionView(
            category=self.category,
            bot=interaction.client,
            user=interaction.user
        )
        embed = create_embed(f"🔍 Debug - {self.category.capitalize()}", "Choose an action:")
        await interaction.response.edit_message(embed=embed, view=view)


class DebugActionView(discord.ui.View):
    """
    Submenu for each category, showing 'Show', 'Test', and 'Back'.
    """
    def __init__(self, category: str, bot, user, timeout=90):
        super().__init__(timeout=timeout)
        self.category = category
        self.bot = bot
        self.user = user

        self.add_item(ActionButton("Show", self.handle_show, ButtonStyle.secondary))
        self.add_item(ActionButton("Test", self.handle_test, ButtonStyle.secondary))
        self.add_item(BackToMenuButton(bot, user))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    async def handle_show(self, interaction: discord.Interaction):
        """Show relevant data for the category."""
        try:
            if self.category == "commands":
                cmds = [cmd.name for cmd in self.bot.commands]
                embed = create_embed("Available Commands", "\n".join(cmds) or "No commands found.")
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "cogs":
                cogs = list(self.bot.cogs.keys())
                embed = create_embed("Loaded Cogs", "\n".join(cogs) or "No cogs loaded.")
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "json":
                paths = [
                    f"Item Stats: {Config.ITEM_STATS_FILE}",
                    f"Item Aliases: {Config.ITEM_ALIASES_FILE}",
                    f"Recipes: {Config.RECIPES_FILE}"
                ]
                embed = create_embed("JSON Files", "\n".join(paths))
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "db":
                # The "Show" action for DB: show the database file path and table list.
                db_path = Config.DB_FILE
                async with aiosqlite.connect(db_path) as db:
                    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    rows = await cursor.fetchall()
                    tables = [r[0] for r in rows]
                content = (
                    f"**Database File:** `{db_path}`\n"
                    f"**Tables:** {', '.join(tables) if tables else 'None'}"
                )
                embed = create_embed("DB Show", content)
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category in ("paths", "helpers", "utils"):
                file_list = gather_files(self.category)
                import_map = build_import_map(file_list)
                pager = FilePagerView(
                    category=self.category,
                    user=self.user,
                    bot=self.bot,
                    files=file_list,
                    parent_view=self,
                    import_map=import_map
                )
                await interaction.response.edit_message(embed=pager.get_embed(), view=pager)

        except Exception as e:
            embed = error_embed(f"Error during SHOW: {e}")
            await interaction.response.edit_message(embed=embed, view=self)

    async def handle_test(self, interaction: discord.Interaction):
        """Run a simple test for the DB category or others."""
        try:
            if self.category == "commands":
                embed = create_embed("Commands Test", f"Total commands: {len(self.bot.commands)}")
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "cogs":
                embed = create_embed("Cogs Test", f"Total loaded cogs: {len(self.bot.cogs)}")
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "json":
                data = reload_json_files()
                embed = create_embed("JSON Test", f"Keys: {', '.join(data.keys())}")
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category == "db":
                # The "Test" action for DB now also checks inventory registration.
                db_path = Config.DB_FILE
                async with aiosqlite.connect(db_path) as db:
                    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    rows = await cursor.fetchall()
                    tables = [r[0] for r in rows]
                # Call a function from your data manager that tests read/write/inventory registration.
                # This function should return a status message, e.g. which files (cogs) correctly access the inventory.
                inventory_status = await DatabaseManager.check_inventory_registration()
                info = await DatabaseManager.get_bot_info()
                content = (
                    f"**Database File:** `{db_path}`\n"
                    f"**Tables:** {', '.join(tables) if tables else 'None'}\n\n"
                    f"**Inventory Registration:** {inventory_status}\n"
                    f"**Bot Info:** {info}"
                )
                embed = create_embed("DB Test", content)
                await interaction.response.edit_message(embed=embed, view=self)

            elif self.category in ("paths", "helpers", "utils"):
                files = gather_files(self.category)
                embed = create_embed("File Test", f"Total .py files: {len(files)}")
                await interaction.response.edit_message(embed=embed, view=self)

        except Exception as e:
            embed = error_embed(f"Error during TEST: {e}")
            await interaction.response.edit_message(embed=embed, view=self)


class ActionButton(discord.ui.Button):
    """Generic button that calls a function from DebugActionView."""
    def __init__(self, label: str, callback_func, style: ButtonStyle = ButtonStyle.secondary):
        super().__init__(label=label, style=style)
        self._callback_func = callback_func

    async def callback(self, interaction: discord.Interaction):
        await self._callback_func(interaction)


class BackToMenuButton(discord.ui.Button):
    """Return to the main Debug Menu."""
    def __init__(self, bot, user):
        super().__init__(label="Back", style=ButtonStyle.danger)
        self.bot = bot
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        view = DebugMenuView(self.bot, self.user)
        embed = create_embed("🛠️ Debug Menu", "Choose a category to explore:")
        await interaction.response.edit_message(embed=embed, view=view)


def gather_files(category: str):
    """
    Collect .py files (limit ~300) depending on the category:
      - 'paths': cogs + helpers + utils
      - 'helpers': only helpers/
      - 'utils': only utils/
    """
    all_paths = []
    limit = 300

    if category == "paths":
        subfolders = ["cogs", "helpers", "utils"]
        for sub in subfolders:
            folder = os.path.join(Config.BASE_DIR, sub)
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".py"):
                        all_paths.append(os.path.abspath(os.path.join(root, file)))
                        if len(all_paths) >= limit:
                            break
                if len(all_paths) >= limit:
                    break

    elif category == "helpers":
        folder = Config.HELPERS_DIR
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.endswith(".py"):
                    all_paths.append(os.path.abspath(os.path.join(folder, f)))

    elif category == "utils":
        folder = Config.UTILS_DIR
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.endswith(".py"):
                    all_paths.append(os.path.abspath(os.path.join(folder, f)))

    return sorted(all_paths)


def build_import_map(files: list[str]) -> dict[str, set[str]]:
    """
    For each file, parse lines beginning with 'import' or 'from' and store the referenced modules.
    """
    import_map = {f: set() for f in files}

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("import "):
                        parts = line.split()
                        if len(parts) >= 2:
                            import_map[path].add(parts[1])
                    elif line.startswith("from "):
                        parts = line.split()
                        if len(parts) > 1:
                            import_map[path].add(parts[1])
        except Exception:
            continue

    return import_map


def path_to_module(file_path: str):
    """
    Convert a file path to a module string, e.g.:
       /home/user/bot/cogs/admin.py -> cogs.admin
    """
    try:
        rel = os.path.relpath(file_path, Config.BASE_DIR)
        parts = rel.split(os.sep)
        parts[-1] = parts[-1].replace(".py", "")
        return ".".join(parts)
    except Exception:
        return file_path  # fallback to raw path


class FilePagerView(discord.ui.View):
    """
    Paged display of .py files, with:
      - Search across file paths and import references
      - Dependencies listing (A -> B)
      - Back button
    """
    def __init__(
        self,
        category: str,
        user,
        bot,
        files: list[str],
        parent_view,
        import_map: dict[str, set[str]],
        page=0,
        search_query: str = None,
    ):
        super().__init__(timeout=90)
        self.category = category
        self.user = user
        self.bot = bot
        self.parent_view = parent_view

        self.original_files = files
        self.import_map = import_map
        self.filtered_files = files
        self.page = page
        self.per_page = 20
        self.search_query = search_query

        # Precompute lowercase cache for paths and import references.
        self.lower_cache = {
            f: (f.lower(), {imp.lower() for imp in import_map.get(f, set())})
            for f in files
        }

        self.add_pagination_buttons()
        self.add_item(SearchButton(self))
        if search_query:
            self.add_item(ClearFilterButton(self))
        self.add_item(DependenciesButton(self))
        self.add_item(BackToCategoryButton(self.parent_view))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user.id

    def add_pagination_buttons(self):
        if self.total_pages() > 1:
            if self.page > 0:
                self.add_item(PrevPageButton(self))
            if self.page < self.total_pages() - 1:
                self.add_item(NextPageButton(self))

    def total_pages(self):
        return max((len(self.filtered_files) - 1) // self.per_page + 1, 1)

    def get_embed(self):
        start = self.page * self.per_page
        end = min(start + self.per_page, len(self.filtered_files))
        subset = self.filtered_files[start:end]

        desc = "\n".join(subset) if subset else "No files found."
        base = f"{self.category.capitalize()} Files"
        title = f"{base} (Page {self.page + 1}/{self.total_pages()}, {len(self.filtered_files)} total)"
        if self.search_query:
            title = f"{base} - Search: '{self.search_query}' (Page {self.page + 1}/{self.total_pages()})"
        return create_embed(title, desc)


class PrevPageButton(discord.ui.Button):
    def __init__(self, pager_view: FilePagerView):
        super().__init__(label="Previous", style=ButtonStyle.secondary)
        self.pager_view = pager_view

    async def callback(self, interaction: discord.Interaction):
        self.pager_view.page -= 1
        new_view = FilePagerView(
            category=self.pager_view.category,
            user=self.pager_view.user,
            bot=self.pager_view.bot,
            files=self.pager_view.original_files,
            parent_view=self.pager_view.parent_view,
            import_map=self.pager_view.import_map,
            page=self.pager_view.page,
            search_query=self.pager_view.search_query
        )
        new_view.filtered_files = self.pager_view.filtered_files
        await interaction.response.edit_message(embed=new_view.get_embed(), view=new_view)


class NextPageButton(discord.ui.Button):
    def __init__(self, pager_view: FilePagerView):
        super().__init__(label="Next", style=ButtonStyle.secondary)
        self.pager_view = pager_view

    async def callback(self, interaction: discord.Interaction):
        self.pager_view.page += 1
        new_view = FilePagerView(
            category=self.pager_view.category,
            user=self.pager_view.user,
            bot=self.pager_view.bot,
            files=self.pager_view.original_files,
            parent_view=self.pager_view.parent_view,
            import_map=self.pager_view.import_map,
            page=self.pager_view.page,
            search_query=self.pager_view.search_query
        )
        new_view.filtered_files = self.pager_view.filtered_files
        await interaction.response.edit_message(embed=new_view.get_embed(), view=new_view)


class SearchButton(discord.ui.Button):
    """Opens a modal to filter the file list by path and references."""
    def __init__(self, pager_view: FilePagerView):
        super().__init__(label="Search", style=ButtonStyle.success)
        self.pager_view = pager_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(SearchModal(self.pager_view))


class ClearFilterButton(discord.ui.Button):
    """Resets the file filter back to the original list."""
    def __init__(self, pager_view: FilePagerView):
        super().__init__(label="Clear Filter", style=ButtonStyle.secondary)
        self.pager_view = pager_view

    async def callback(self, interaction: discord.Interaction):
        new_view = FilePagerView(
            category=self.pager_view.category,
            user=self.pager_view.user,
            bot=self.pager_view.bot,
            files=self.pager_view.original_files,
            parent_view=self.pager_view.parent_view,
            import_map=self.pager_view.import_map,
            page=0
        )
        await interaction.response.edit_message(embed=new_view.get_embed(), view=new_view)


class SearchModal(discord.ui.Modal, title="File Search"):
    search_input = discord.ui.TextInput(
        label="Search query (path or references)",
        placeholder="e.g. 'data_manager' or 'inventory'",
        required=False,
        max_length=100
    )

    def __init__(self, pager_view: FilePagerView):
        super().__init__()
        self.pager_view = pager_view

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value.strip().lower()
        files = self.pager_view.original_files
        lower_cache = self.pager_view.lower_cache

        filtered = files if not query else [
            f for f in files
            if query in lower_cache[f][0] or any(query in imp for imp in lower_cache[f][1])
        ]

        new_view = FilePagerView(
            category=self.pager_view.category,
            user=self.pager_view.user,
            bot=self.pager_view.bot,
            files=files,
            parent_view=self.pager_view.parent_view,
            import_map=self.pager_view.import_map,
            page=0,
            search_query=query if query else None
        )
        new_view.filtered_files = filtered
        await interaction.response.edit_message(embed=new_view.get_embed(), view=new_view)


class DependenciesButton(discord.ui.Button):
    """
    Displays one-way import references among the filtered files:
    If file A imports file B, it shows "A -> B" (if B is in the filtered list).
    When a search query is active, only dependency pairs where the query appears
    in either file's name are shown. Each dependency is shown only once.
    """
    def __init__(self, pager_view: FilePagerView):
        super().__init__(label="Dependencies", style=ButtonStyle.primary)
        self.pager_view = pager_view

    async def callback(self, interaction: discord.Interaction):
        file_list = self.pager_view.filtered_files
        import_map = self.pager_view.import_map
        unique_deps = set()
        query = self.pager_view.search_query  # May be None

        for fileA in file_list:
            modA = path_to_module(fileA)
            for fileB in file_list:
                if fileB != fileA:
                    modB = path_to_module(fileB)
                    if modB in import_map[fileA]:
                        dep_str = f"{os.path.basename(fileA)} -> {os.path.basename(fileB)}"
                        if query:
                            if query in os.path.basename(fileA).lower() or query in os.path.basename(fileB).lower():
                                unique_deps.add(dep_str)
                        else:
                            unique_deps.add(dep_str)
        embed = create_embed("Dependencies", "\n".join(sorted(unique_deps)) if unique_deps else "No cross-references found.")
        await interaction.response.edit_message(embed=embed, view=self.pager_view)


class BackToCategoryButton(discord.ui.Button):
    """Returns from the file pager view back to the category action view."""
    def __init__(self, parent_view: DebugActionView):
        super().__init__(label="Back", style=ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        embed = create_embed(f"🔍 Debug - {self.parent_view.category.capitalize()}", "Choose an action:")
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


async def setup(bot):
    await bot.add_cog(DebugCog(bot))
