# Minimal Foundation Plan

## Inventory

- `superbot-start/helpers/config.py`: dataclass-based settings loader using `dotenv`. Provides inspiration for the new Pydantic settings module.
- `superbot-start/helpers/logging.py`: simple logger initializer returning a named logger. Suitable to reuse with minimal changes.
- `superbot-start/helpers/errors.py`: helper to log unexpected exceptions. Will be reused as-is.
- `superbot-start/helpers/loader.py`: utility to discover and load extensions. Will inform the new cog loader.
- No current implementations for `config.py`, `core/services/{logging_service.py, db.py, errors.py}`, or `loaders/cogs.py` under `superbot/src`—these will be introduced.

## Plan

- **Reuse unchanged**
  - Exception reporting helper (`errors.py`).
  - Basic logger initialization (`logging_service.py`).

- **Extend**
  - New `config.py` built on Pydantic v2 with robust `.env` discovery, ID parsing, directory creation, and predefined `PRELOAD_COGS` list.
  - Cog loader in `loaders/cogs.py` that skips already loaded extensions and logs tracebacks on failure.

- **Add**
  - `main.py` that disables built-in help, initializes services, loads cogs, and syncs slash commands on startup.
  - Feature cogs: `features/help/help_cog.py` and `features/admin/admin_core.py` implementing enhanced help and admin functionality.
  - Minimal database service (`db.py`) using SQLite with optional migrations.
