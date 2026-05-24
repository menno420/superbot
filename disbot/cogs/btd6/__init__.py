"""BTD6 cog package — domain helpers and the passive message stage.

Module 6 of the AI/BTD6 plan introduces ``BTD6AssistantMessageStage``
here. The cog entry point (``disbot/cogs/btd6_cog.py``) registers
the stage with ``core.runtime.message_pipeline`` in ``cog_load`` and
unregisters it in ``cog_unload``. No ``on_message`` listener is
ever installed — the platform pipeline is the only entry point for
message handling.
"""

from __future__ import annotations

__all__: list[str] = []
