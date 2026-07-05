"""Cog discovery, load/unload/reload primitives, and the interactive
:class:`_CogManagerView` (PR C).

Extracted from ``cogs/admin_cog.py`` to keep that file under the S4.6
800-LOC ceiling. The module owns:

* :data:`COGS_DIR` — absolute path to the cogs directory.
* Discovery helpers (:func:`_normalize`, :func:`_find_module`,
  :func:`_all_cog_modules`, :func:`_syntax_ok`).
* :data:`_PROTECTED_COGS` — core cogs that may not be unloaded from
  the panel UI (prefix ``!cog unload`` retains no protection).
* :func:`_do_load`, :func:`_do_unload`, :func:`_do_reload` — shared
  body for the ``!cog`` prefix command and the panel buttons.
* :class:`_CogManagerSelect`, :class:`_CogManagerView` — interactive
  panel surface.

``admin_cog.py`` imports the helpers and view from here.
"""

from __future__ import annotations

import ast
import logging
import os
import re
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from utils.ui_constants import INFO_COLOR, SUCCESS_COLOR
from views.base import HubView
from views.paginated_select import attach_windowed_select

if TYPE_CHECKING:
    from cogs.admin_cog import AdminCog, _AdminPanelView

# Absolute path to ``cogs/`` — the parent directory of ``cogs/admin/``.
COGS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _normalize(name: str) -> str:
    """Strip underscores/spaces, lowercase, remove trailing 'cog'."""
    return re.sub(r"[\s_]+", "", name.lower()).removesuffix("cog")


def _find_module(name: str) -> str | None:
    """Return the full module path (e.g. 'cogs.admin_cog') for a fuzzy cog name."""
    target = _normalize(name)
    for fname in sorted(os.listdir(COGS_DIR)):
        if fname.endswith("_cog.py") and not fname.startswith("__"):
            if _normalize(fname[:-3]) == target:
                return f"cogs.{fname[:-3]}"
    return None


def _all_cog_modules() -> list[str]:
    """Return module paths for every *_cog.py file."""
    return [
        f"cogs.{f[:-3]}"
        for f in sorted(os.listdir(COGS_DIR))
        if f.endswith("_cog.py") and not f.startswith("__")
    ]


def _syntax_ok(fname: str) -> bool:
    """Return True if the file parses without syntax errors."""
    try:
        with open(os.path.join(COGS_DIR, fname), encoding="utf-8") as fh:
            ast.parse(fh.read(), fname)
        return True
    except SyntaxError:
        return False


# Core cogs that must NOT be unloaded from the panel UI without a
# deliberate operator action. Unloading any of these can wedge the
# bot's safety / runtime surface (admin_cog itself is the obvious
# self-foot-gun; settings, help, logging, and cleanup are the
# bot's operator-facing minimum).
#
# Critical cogs may still be RELOADED from the panel (reversible) and
# the prefix ``!cog unload <name>`` command retains no protection — it
# is the operator's escape hatch when the panel won't open. Document
# the asymmetry in any operator-facing copy that grows around this.
_PROTECTED_COGS: frozenset[str] = frozenset(
    {
        "cogs.admin_cog",
        "cogs.cleanup_cog",
        "cogs.help_cog",
        "cogs.logging_cog",
        "cogs.settings_cog",
    },
)


logger = logging.getLogger("bot.cogs.admin.cog_manager")


async def _emit_cog_audit(
    module: str,
    mutation_type: str,
    actor_id: int | None,
) -> None:
    """Best-effort audit for a cog load/unload/reload (a runtime mutation).

    These are process/runtime mutations with no DB write and no owning
    ``*_mutation`` service, so — like ``proof_channel_cog._emit_prize_audit`` —
    the cog-layer emit is the correct seam. Audit is best-effort: a bus/emit
    failure never blocks the operation.
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    from services.audit_events import emit_audit_action

    try:
        await emit_audit_action(
            mutation_id=str(uuid4()),
            subsystem="admin",
            mutation_type=mutation_type,
            target=f"cog:{module}",
            scope="global",
            guild_id=None,
            prev_value=None,
            new_value=module,
            actor_id=actor_id,
            actor_type="admin",
            occurred_at=datetime.now(tz=timezone.utc),
        )
    except Exception:  # noqa: BLE001 — audit is best-effort; never block the op
        logger.exception("cog audit emit failed for %s (%s)", mutation_type, module)


async def _emit_admin_runtime_audit(
    mutation_type: str,
    target: str,
    prev_value: str | None,
    new_value: str | None,
    actor_id: int | None,
) -> None:
    """Best-effort audit for a high-privilege admin runtime mutation.

    Restart and log-level changes are process/runtime mutations with no DB
    write and no owning ``*_mutation`` service, so — like
    ``proof_channel_cog._emit_prize_audit`` — the cog-layer emit is the right
    seam. Audit is best-effort: a bus/emit failure never blocks the action.
    """
    from datetime import datetime, timezone
    from uuid import uuid4

    from services.audit_events import emit_audit_action

    try:
        await emit_audit_action(
            mutation_id=str(uuid4()),
            subsystem="admin",
            mutation_type=mutation_type,
            target=target,
            scope="global",
            guild_id=None,
            prev_value=prev_value,
            new_value=new_value,
            actor_id=actor_id,
            actor_type="admin",
            occurred_at=datetime.now(tz=timezone.utc),
        )
    except Exception:  # noqa: BLE001 — audit is best-effort; never block the op
        logger.exception(
            "admin runtime audit emit failed for %s (%s)",
            mutation_type,
            target,
        )


async def _do_load(
    bot: commands.Bot,
    module: str,
    *,
    actor_id: int | None = None,
) -> str:
    """Load ``module``; return an operator-readable status string."""
    try:
        await bot.load_extension(module)
        await _emit_cog_audit(module, "cog_load", actor_id)
        return f"✅ `{module}` loaded."
    except Exception as exc:  # noqa: BLE001 — operator-facing surface
        return f"⚠️ Error loading `{module}`: {exc}"


async def _do_unload(
    bot: commands.Bot,
    module: str,
    *,
    actor_id: int | None = None,
) -> str:
    """Unload ``module``; return an operator-readable status string."""
    try:
        await bot.unload_extension(module)
        await _emit_cog_audit(module, "cog_unload", actor_id)
        return f"🔴 `{module}` unloaded."
    except Exception as exc:  # noqa: BLE001 — operator-facing surface
        return f"⚠️ Error unloading `{module}`: {exc}"


async def _do_reload(
    bot: commands.Bot,
    module: str,
    *,
    actor_id: int | None = None,
) -> str:
    """Reload ``module``; return an operator-readable status string."""
    try:
        await bot.reload_extension(module)
        await _emit_cog_audit(module, "cog_reload", actor_id)
        return f"🔄 `{module}` reloaded."
    except Exception as exc:  # noqa: BLE001 — operator-facing surface
        return f"⚠️ Error reloading `{module}`: {exc}"


# ---------------------------------------------------------------------------
# Interactive Cog Manager (PR C)
# ---------------------------------------------------------------------------


def _build_cog_options(loaded: set[str]) -> list[discord.SelectOption]:
    """Build a :class:`discord.SelectOption` per ``*_cog.py`` under ``COGS_DIR``.

    One option per discovered cog — *not* front-truncated to Discord's 25-option
    cap. The :class:`_CogManagerView` windows the full list with
    :func:`views.paginated_select.attach_windowed_select` so every cog stays
    reachable even when there are more than 25 (there are currently ~46; the old
    ``options[:25]`` silently dropped every cog sorting past the 25th — the #1040
    select-option-truncation class, in the cog layer this time).

    Status glyphs in each label reflect load/syntax state at panel-render time.
    """
    options: list[discord.SelectOption] = []
    for fname in sorted(os.listdir(COGS_DIR)):
        if not fname.endswith("_cog.py") or fname.startswith("__"):
            continue
        short = fname[:-3]
        module = f"cogs.{short}"
        load_glyph = "✅" if module in loaded else "❌"
        syntax_glyph = "🟢" if _syntax_ok(fname) else "🔴"
        protected_glyph = "🛡" if module in _PROTECTED_COGS else ""
        label = f"{load_glyph}{syntax_glyph}{protected_glyph} {short}"[:100]
        options.append(
            discord.SelectOption(
                label=label,
                value=module,
                description=(
                    "Protected core cog — panel unload denied"
                    if module in _PROTECTED_COGS
                    else None
                ),
            ),
        )
    return options


class _CogManagerView(HubView):
    """Owner-driven Load / Unload / Reload panel.

    PR C replaces the previous read-only embed under "Cog List" with
    an interactive surface. Mutations are owner-gated:

    * Non-owners see the same status surface but the action buttons
      ephemerally deny.
    * Owners can load any cog, reload any cog (including protected
      core cogs — reload is reversible), and unload any non-protected
      cog.
    * Unloading a protected core cog from the panel is refused; the
      ephemeral surfaces the prefix-command escape hatch.

    Load / Unload / Reload paths share their bodies with the
    ``!cog`` prefix command via the module-level :func:`_do_load` /
    :func:`_do_unload` / :func:`_do_reload` helpers.
    """

    def __init__(
        self,
        cog: AdminCog,
        author: discord.Member | discord.User,
    ) -> None:
        super().__init__(author)
        self.cog = cog
        self.selected_module: str | None = None
        self.last_status: str | None = None
        self._add_components()

    def _add_components(self) -> None:
        loaded = set(self.cog.bot.extensions.keys())
        # Windowed select (◀/▶ paging) instead of a front-truncated
        # ``options[:25]`` — so all ~46 cogs stay selectable. select_row=0
        # and nav_row=3 leave row 1 (Load/Unload/Reload), row 2 (Refresh),
        # and row 4 (the opener's Back button) clear.
        attach_windowed_select(
            self,
            _build_cog_options(loaded),
            self._on_cog_selected,
            placeholder="Choose a cog…",
            select_row=0,
            nav_row=3,
        )

        load = discord.ui.Button(  # type: ignore[var-annotated]
            label="Load",
            style=discord.ButtonStyle.green,
            row=1,
            custom_id="admin:cogmgr:load",
        )
        load.callback = self._on_load  # type: ignore[method-assign]
        self.add_item(load)

        unload = discord.ui.Button(  # type: ignore[var-annotated]
            label="Unload",
            style=discord.ButtonStyle.danger,
            row=1,
            custom_id="admin:cogmgr:unload",
        )
        unload.callback = self._on_unload  # type: ignore[method-assign]
        self.add_item(unload)

        reload_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="Reload",
            style=discord.ButtonStyle.blurple,
            row=1,
            custom_id="admin:cogmgr:reload",
        )
        reload_btn.callback = self._on_reload  # type: ignore[method-assign]
        self.add_item(reload_btn)

        refresh = discord.ui.Button(  # type: ignore[var-annotated]
            label="🔄 Refresh",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id="admin:cogmgr:refresh",
        )
        refresh.callback = self._on_refresh  # type: ignore[method-assign]
        self.add_item(refresh)

    async def _on_cog_selected(
        self,
        interaction: discord.Interaction,
        values: list[str],
    ) -> None:
        """Windowed-select callback — stash the chosen cog and re-render.

        ``values`` is the windowed select's cleaned value list (the empty-state
        sentinel is already filtered out by the window), so an empty list means
        no real cog was picked.
        """
        if not values:
            await interaction.response.send_message(
                "No cogs available.",
                ephemeral=True,
            )
            return
        self.selected_module = values[0]
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    def build_embed(self) -> discord.Embed:
        loaded = set(self.cog.bot.extensions.keys())
        lines = []
        for fname in sorted(os.listdir(COGS_DIR)):
            if not fname.endswith("_cog.py") or fname.startswith("__"):
                continue
            module = f"cogs.{fname[:-3]}"
            load_icon = "✅" if module in loaded else "❌"
            syntax_icon = "🟢" if _syntax_ok(fname) else "🔴"
            protected_icon = " 🛡" if module in _PROTECTED_COGS else ""
            marker = "  ← selected" if module == self.selected_module else ""
            lines.append(
                f"{load_icon} {syntax_icon}  `{fname[:-3]}`{protected_icon}{marker}",
            )

        description_parts = [
            "**Pick a cog from the dropdown, then Load / Unload / Reload.**",
            "",
            "\n".join(lines) or "_No cogs found._",
            "",
            (
                "✅ Loaded  ❌ Unloaded  🟢 OK  🔴 Syntax error  🛡 "
                "Protected (panel unload denied — use `!cog unload <name>`)"
            ),
        ]
        if self.last_status:
            description_parts.append("")
            description_parts.append(self.last_status)
        embed = discord.Embed(
            title="📋 Cog Manager",
            description="\n".join(description_parts),
            color=INFO_COLOR,
        )
        if self.selected_module:
            embed.set_footer(text=f"Selected: {self.selected_module}")
        else:
            embed.set_footer(text="No cog selected.")
        return embed

    async def _require_owner_or_deny(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if not await interaction.client.is_owner(interaction.user):  # type: ignore[attr-defined]
            await interaction.response.send_message(
                "Owner only.",
                ephemeral=True,
            )
            return False
        return True

    async def _require_selection_or_deny(
        self,
        interaction: discord.Interaction,
    ) -> bool:
        if self.selected_module is None:
            await interaction.response.send_message(
                "Pick a cog from the dropdown first.",
                ephemeral=True,
            )
            return False
        return True

    async def _on_load(self, interaction: discord.Interaction) -> None:
        if not await self._require_owner_or_deny(interaction):
            return
        if not await self._require_selection_or_deny(interaction):
            return
        assert self.selected_module is not None  # noqa: S101 — guarded above
        self.last_status = await _do_load(
            self.cog.bot,
            self.selected_module,
            actor_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def _on_unload(self, interaction: discord.Interaction) -> None:
        if not await self._require_owner_or_deny(interaction):
            return
        if not await self._require_selection_or_deny(interaction):
            return
        assert self.selected_module is not None  # noqa: S101 — guarded above
        if self.selected_module in _PROTECTED_COGS:
            short = self.selected_module.split(".")[-1]
            await interaction.response.send_message(
                f"`{self.selected_module}` is a protected core cog. "
                f"Use `!cog unload {short}` from a terminal if you really "
                "need to (risk of bot lockup).",
                ephemeral=True,
            )
            return
        self.last_status = await _do_unload(
            self.cog.bot,
            self.selected_module,
            actor_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def _on_reload(self, interaction: discord.Interaction) -> None:
        if not await self._require_owner_or_deny(interaction):
            return
        if not await self._require_selection_or_deny(interaction):
            return
        assert self.selected_module is not None  # noqa: S101 — guarded above
        # Reload is allowed even for protected core cogs — it is
        # reversible and is the operator's hot-path for picking up a
        # code change without restarting the process.
        self.last_status = await _do_reload(
            self.cog.bot,
            self.selected_module,
            actor_id=interaction.user.id,
        )
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def _on_refresh(self, interaction: discord.Interaction) -> None:
        # Refresh is open to any admin who reached the panel — it
        # only re-reads load state, no mutation.
        self.last_status = None
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )


class _LogLevelModal(discord.ui.Modal, title="Set Log Level"):  # type: ignore[call-arg]
    level = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)",
        placeholder="INFO",
        max_length=10,
    )

    def __init__(self, panel: _AdminPanelView):
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        level_int = getattr(logging, self.level.value.upper(), None)
        if not isinstance(level_int, int):
            await interaction.response.send_message(
                f"❌ Unknown level `{self.level.value.upper()}`. "
                "Choose from: DEBUG, INFO, WARNING, ERROR, CRITICAL",
                ephemeral=True,
            )
            return
        old_level = logging.getLevelName(logging.getLogger().level)
        logging.getLogger().setLevel(level_int)
        embed = discord.Embed(
            title="📝 Log Level Updated",
            description=f"Log level set to `{self.level.value.upper()}`.",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="Click ↩ Overview to return.")
        await interaction.response.edit_message(embed=embed, view=self.panel)
        await _emit_admin_runtime_audit(
            "set_log_level",
            "logging:root",
            old_level,
            self.level.value.upper(),
            getattr(interaction.user, "id", None),
        )


__all__ = [
    "COGS_DIR",
    "_CogManagerView",
    "_LogLevelModal",
    "_PROTECTED_COGS",
    "_all_cog_modules",
    "_do_load",
    "_do_reload",
    "_do_unload",
    "_emit_admin_runtime_audit",
    "_find_module",
    "_normalize",
    "_syntax_ok",
]
