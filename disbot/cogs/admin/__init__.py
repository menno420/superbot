"""Admin cog helpers — extracted per the F-3 decomposition convention.

This subpackage holds support modules for ``cogs/admin_cog.py``:

* :mod:`cogs.admin.cog_manager` — discovery helpers, load/unload/reload
  primitives, the ``_PROTECTED_COGS`` constant, and the interactive
  :class:`_CogManagerView`. Kept out of ``admin_cog.py`` to stay under
  the S4.6 cog-size invariant.

``admin_cog.py`` remains the Discord-facing surface (the cog
registers commands and panel views from here); helpers live here.
"""
