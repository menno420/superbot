"""Economy subsystem internals.

Submodules host the shared constants and helper functions extracted
from cogs/economy_cog.py during D5 so that views (under
``views/economy/``) and the cog itself depend on a common location
instead of importing through each other.

Submodules:
    _helpers — JOBS, SHOP_ITEMS, daily-tier tables, cooldown constants,
               and the pure helper functions (_pick_daily, _job_pay,
               _available_jobs, _shop_embed, _build_economy_embed).
"""
