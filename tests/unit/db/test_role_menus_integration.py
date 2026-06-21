"""Real-Postgres integration for the PR 2 additions to utils.db.role_menus.

PR 1's ``test_role_menus.py`` covers the base CRUD; this file exercises only the
two helpers PR 2 adds — ``replace_options`` (transactional full-list replace, the
builder's create/edit path) and ``list_posted_menus`` (the boot re-attach query).

CI safety: no shared Postgres fixture and CI runs no Postgres service, so the
module-local ``postgres_pool`` fixture ``pytest.skip()``s when ``DATABASE_URL`` is
unset (CI) or the DB is unreachable. Isolation: rows live under a reserved test
``guild_id`` swept on entry + exit.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
import pytest_asyncio

from utils.db import pool
from utils.db import role_menus as menus

_TEST_GUILD = 9_000_000_000_000_000_078


async def _sweep() -> None:
    await pool.execute("DELETE FROM role_menus WHERE guild_id=$1", (_TEST_GUILD,))


@pytest_asyncio.fixture
async def postgres_pool():
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL unset — real-Postgres integration test skipped (CI)")
    try:
        await pool.init()
    except (OSError, asyncpg.PostgresError) as exc:
        pytest.skip(f"Postgres unreachable ({type(exc).__name__}) — skipped")
    await _sweep()
    try:
        yield pool
    finally:
        await _sweep()
        await pool.close()


async def _new_menu() -> int:
    return await menus.create_menu(
        _TEST_GUILD,
        123,
        title="A",
        description=None,
    )


@pytest.mark.asyncio
async def test_replace_options_sets_ordered_list(postgres_pool):
    menu_id = await _new_menu()
    await menus.replace_options(menu_id, [(10, None, "Gamer"), (20, "🎨", "Artist")])
    opts = await menus.get_options(menu_id)
    assert [o["role_id"] for o in opts] == [10, 20]  # position order preserved
    assert opts[1]["emoji"] == "🎨"


@pytest.mark.asyncio
async def test_replace_options_replaces_and_dedupes(postgres_pool):
    menu_id = await _new_menu()
    await menus.replace_options(menu_id, [(10, None, None), (20, None, None)])
    # Replace with a new set that also contains a duplicate role id.
    await menus.replace_options(menu_id, [(30, None, None), (30, None, None)])
    opts = await menus.get_options(menu_id)
    assert [o["role_id"] for o in opts] == [30]  # replaced + deduped


@pytest.mark.asyncio
async def test_list_posted_menus_only_after_message_set(postgres_pool):
    menu_id = await _new_menu()
    posted_ids = {m["menu_id"] for m in await menus.list_posted_menus()}
    assert menu_id not in posted_ids  # not posted yet

    await menus.set_menu_message(menu_id, 7777)
    posted_ids = {m["menu_id"] for m in await menus.list_posted_menus()}
    assert menu_id in posted_ids
