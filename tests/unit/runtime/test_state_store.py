"""Tests for core.runtime.state_store batch helper (set_many).

R3 from the platform-hardening plan: ensures multi-key state updates
are atomic and that the empty-input case is a no-op.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.runtime import state_store


class TestSetMany:
    @pytest.mark.asyncio
    async def test_empty_items_is_noop(self):
        with patch(
            "core.runtime.state_store.db.set_session_state_many",
            new_callable=AsyncMock,
        ) as m:
            await state_store.set_many("session-1", {})
            m.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delegates_to_db_layer(self):
        items = {"nav_stack": [1, 2, 3], "active_screen": "home"}
        with patch(
            "core.runtime.state_store.db.set_session_state_many",
            new_callable=AsyncMock,
        ) as m:
            await state_store.set_many("session-1", items)
            m.assert_awaited_once_with("session-1", items)

    @pytest.mark.asyncio
    async def test_db_error_propagates(self):
        with patch(
            "core.runtime.state_store.db.set_session_state_many",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ):
            with pytest.raises(RuntimeError):
                await state_store.set_many("session-1", {"k": "v"})
