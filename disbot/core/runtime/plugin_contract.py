"""Plugin isolation protocol for SuperBot.

All official cogs should implement PluginContract. Future third-party plugins
are validated against this interface at load time before their capabilities
are granted by the governance admin.

Usage:
    class MyCog(commands.Cog, PluginContract):
        plugin_id = "my_cog"
        required_capabilities = ["economy.use"]
        provided_subsystems = ["economy"]

        async def setup(self, bot: commands.Bot) -> None:
            await bot.add_cog(self)

        async def teardown(self) -> None:
            pass
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from discord.ext import commands


@runtime_checkable
class PluginContract(Protocol):
    """Interface every SuperBot plugin must satisfy.

    Validated by _load_cogs() at startup. Plugins whose required_capabilities
    are not governance-granted will be rejected before loading.
    """

    plugin_id: str
    required_capabilities: list[str]
    provided_subsystems: list[str]

    async def plugin_setup(self, bot: commands.Bot) -> None:
        """Called once after the plugin is loaded. Default: no-op."""
        ...

    async def plugin_teardown(self) -> None:
        """Called once before the plugin is unloaded. Default: no-op."""
        ...


def validate_plugin(cog_instance: object) -> list[str]:
    """Return a list of validation errors for a cog instance.

    An empty list means the cog satisfies the PluginContract.
    This is a soft-validation used for warnings — cogs are not rejected
    unless they explicitly fail a required capability check.
    """
    errors: list[str] = []
    for attr in ("plugin_id", "required_capabilities", "provided_subsystems"):
        if not hasattr(cog_instance, attr):
            errors.append(f"Missing PluginContract attribute: {attr!r}")
    return errors
