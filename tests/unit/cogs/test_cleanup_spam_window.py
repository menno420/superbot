"""The `!cleanuphistory` spam-window is resolved per-guild (cert punch #4).

Pins that ``cogs.cleanup_cog._resolve_spam_window`` reads the
``cleanup_spam_window_seconds`` scalar via the canonical settings resolver and
falls back to the declared default (15s) when unset or malformed — so an
existing guild's sweep behaves byte-identically to the old hardcoded constant.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime import subsystem_schema as schema_mod


@pytest.fixture(autouse=True)
def _isolated_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    from cogs.cleanup.schemas import register_schemas

    register_schemas()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)


async def test_resolves_a_set_per_guild_value(monkeypatch):
    import utils.guild_config_accessors as accessors
    from cogs.cleanup_cog import _resolve_spam_window

    monkeypatch.setattr(accessors, "get_setting_value", AsyncMock(return_value="30"))
    assert await _resolve_spam_window(42) == 30


async def test_falls_back_to_default_when_unset(monkeypatch):
    import utils.guild_config_accessors as accessors
    from cogs.cleanup.schemas import DEFAULT_SPAM_WINDOW_SECONDS
    from cogs.cleanup_cog import _resolve_spam_window

    monkeypatch.setattr(accessors, "get_setting_value", AsyncMock(return_value=""))
    assert await _resolve_spam_window(42) == DEFAULT_SPAM_WINDOW_SECONDS


async def test_falls_back_to_default_on_malformed_value(monkeypatch):
    import utils.guild_config_accessors as accessors
    from cogs.cleanup.schemas import DEFAULT_SPAM_WINDOW_SECONDS
    from cogs.cleanup_cog import _resolve_spam_window

    # A non-int KV row must not raise — the resolver coerces, fails, defaults.
    monkeypatch.setattr(accessors, "get_setting_value", AsyncMock(return_value="abc"))
    assert await _resolve_spam_window(42) == DEFAULT_SPAM_WINDOW_SECONDS


async def test_out_of_range_value_falls_back_to_default(monkeypatch):
    """A stored value outside the validator bounds falls back, never crashes."""
    import utils.guild_config_accessors as accessors
    from cogs.cleanup.schemas import DEFAULT_SPAM_WINDOW_SECONDS
    from cogs.cleanup_cog import _resolve_spam_window

    monkeypatch.setattr(accessors, "get_setting_value", AsyncMock(return_value="99999"))
    assert await _resolve_spam_window(42) == DEFAULT_SPAM_WINDOW_SECONDS
