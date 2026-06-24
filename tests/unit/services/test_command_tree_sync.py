"""Tests for the diff-gated startup command-tree auto-sync.

Pins: env kill-switch parsing; that local/remote path extraction reach the same
qualified paths from the two different object models (so the diff is meaningful);
and that ``auto_sync_if_changed`` syncs ONLY on a real diff and is non-fatal on
every failure path.
"""

from __future__ import annotations

from types import SimpleNamespace

import discord
import pytest

from services import command_tree_sync as cts

_SUB = discord.AppCommandOptionType.subcommand
_GROUP = discord.AppCommandOptionType.subcommand_group
_STR = discord.AppCommandOptionType.string


# ---------------------------------------------------------------------------
# env_enabled — kill-switch
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw", ["1", "true", "yes", "on", "TRUE", "anything", "", None])
def test_env_enabled_default_on(raw):
    assert cts.env_enabled(raw) is True


@pytest.mark.parametrize("raw", ["0", "false", "no", "off", " OFF ", "False"])
def test_env_enabled_explicit_off(raw):
    assert cts.env_enabled(raw) is False


# ---------------------------------------------------------------------------
# path extraction — local (real unified tree) and remote (fetched model)
# ---------------------------------------------------------------------------


def test_local_paths_walk_the_real_unified_tree():
    from cogs.btd6 import _unified

    paths = cts._local_paths([_unified.btd6_app])
    assert "btd6" in paths
    assert "btd6 income" in paths  # flat lookup
    assert "btd6 strat" in paths  # nested subgroup
    assert "btd6 strat browse" in paths  # nested leaf
    assert "btd6 ops seed-data" in paths


def test_local_paths_treats_a_plain_command_as_a_leaf():
    cmd = SimpleNamespace(name="help")
    assert cts._local_paths([cmd]) == {"help"}


def _remote(name, options=None):
    return SimpleNamespace(name=name, options=options or [])


def _opt(name, type_, options=None):
    return SimpleNamespace(name=name, type=type_, options=options or [])


def test_remote_paths_recurse_through_subcommand_groups_and_skip_params():
    btd6 = _remote(
        "btd6",
        options=[
            _opt("income", _SUB, options=[_opt("start_round", _STR)]),  # param skipped
            _opt(
                "strat",
                _GROUP,
                options=[_opt("browse", _SUB)],
            ),
        ],
    )
    paths = cts._remote_paths([btd6])
    assert paths == {"btd6", "btd6 income", "btd6 strat", "btd6 strat browse"}
    assert "btd6 income start_round" not in paths  # a parameter is not a path


def test_local_and_remote_paths_match_for_an_equivalent_tree():
    # _local_paths uses isinstance(app_commands.Group), so build the local side
    # from a real Group; the remote side from the fetched-AppCommand model. Both
    # must reach the same qualified paths for the diff to be meaningful.
    from discord import app_commands

    grp = app_commands.Group(name="x", description="d")

    @grp.command(name="a", description="d")
    async def _a(interaction):  # pragma: no cover - registration only
        pass

    @grp.command(name="b", description="d")
    async def _b(interaction):  # pragma: no cover - registration only
        pass

    local = cts._local_paths([grp])
    remote = cts._remote_paths(
        [_remote("x", options=[_opt("a", _SUB), _opt("b", _SUB)])],
    )
    assert local == remote == {"x", "x a", "x b"}


# ---------------------------------------------------------------------------
# auto_sync_if_changed — the gate
# ---------------------------------------------------------------------------


class _Tree:
    def __init__(self, *, local, remote, sync_result=None, fetch_exc=None, sync_exc=None):
        self._local = local
        self._remote = remote
        self._sync_result = sync_result if sync_result is not None else []
        self._fetch_exc = fetch_exc
        self._sync_exc = sync_exc
        self.sync_calls = 0
        self.fetch_calls = 0

    def get_commands(self):
        return self._local

    async def fetch_commands(self):
        self.fetch_calls += 1
        if self._fetch_exc:
            raise self._fetch_exc
        return self._remote

    async def sync(self):
        self.sync_calls += 1
        if self._sync_exc:
            raise self._sync_exc
        return self._sync_result


def _bot(tree):
    return SimpleNamespace(tree=tree)


@pytest.mark.asyncio
async def test_disabled_does_nothing():
    tree = _Tree(local=[_remote("help")], remote=[])
    out = await cts.auto_sync_if_changed(_bot(tree), enabled=False)
    assert out.synced is False and out.reason == "disabled"
    assert tree.fetch_calls == 0 and tree.sync_calls == 0


@pytest.mark.asyncio
async def test_unchanged_tree_does_not_sync():
    tree = _Tree(local=[SimpleNamespace(name="help")], remote=[_remote("help")])
    out = await cts.auto_sync_if_changed(_bot(tree), enabled=True)
    assert out.synced is False and out.reason == "unchanged"
    assert tree.fetch_calls == 1 and tree.sync_calls == 0


@pytest.mark.asyncio
async def test_changed_tree_syncs_and_reports_diff():
    # local has /new that Discord lacks; Discord has /old that's gone locally.
    tree = _Tree(
        local=[SimpleNamespace(name="help"), SimpleNamespace(name="new")],
        remote=[_remote("help"), _remote("old")],
        sync_result=[SimpleNamespace(name="help"), SimpleNamespace(name="new")],
    )
    out = await cts.auto_sync_if_changed(_bot(tree), enabled=True)
    assert out.synced is True and out.reason == "synced"
    assert tree.sync_calls == 1
    assert out.added == ("new",)
    assert out.removed == ("old",)


@pytest.mark.asyncio
async def test_fetch_failure_is_non_fatal():
    tree = _Tree(local=[], remote=[], fetch_exc=discord.HTTPException(
        response=SimpleNamespace(status=503, reason="x"), message="boom"))
    out = await cts.auto_sync_if_changed(_bot(tree), enabled=True)
    assert out.synced is False and out.reason == "fetch_failed"
    assert tree.sync_calls == 0


@pytest.mark.asyncio
async def test_sync_failure_is_non_fatal():
    tree = _Tree(
        local=[SimpleNamespace(name="new")],
        remote=[],
        sync_exc=discord.HTTPException(
            response=SimpleNamespace(status=429, reason="rate"), message="rate limited"
        ),
    )
    out = await cts.auto_sync_if_changed(_bot(tree), enabled=True)
    assert out.synced is False and out.reason == "sync_failed"
    assert tree.sync_calls == 1
    assert out.added == ("new",)
