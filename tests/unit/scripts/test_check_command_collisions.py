"""Tests for scripts/check_command_collisions.py — the static duplicate-command guard.

Guards the #1541/#1544 outage class: two cogs claiming one top-level command
name/alias crash the ``discord.ext.commands`` registry at boot
(``CommandRegistrationError`` → cog load failure → STRICT identity abort →
crash-loop). The pure AST core (``extract_declarations`` / ``find_collisions``)
is tested on inline fixtures; ``collect_all`` + ``main`` are exercised against
both a staged tmp tree and the real ``disbot/cogs/`` tree (the live-tree test
doubles as the standing "0 collisions post-#1544" regression).
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "scripts" / "check_command_collisions.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_command_collisions_ut",
        _SCRIPT,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass introspects the owning module via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load()


def _extract(mod, source: str):
    return mod.extract_declarations(textwrap.dedent(source), "cogs/fixture.py")


# ---------------------------------------------------------------------------
# extract_declarations — token discovery
# ---------------------------------------------------------------------------


def test_name_kwarg_and_aliases(mod):
    decls = _extract(
        mod,
        '''
        class KarmaCog(commands.Cog):
            @commands.command(name="thanks", aliases=["rep", "thank"])
            async def _thanks(self, ctx):
                ...
        ''',
    )
    tokens = {(d.token, d.kind) for d in decls}
    assert tokens == {("thanks", "name"), ("rep", "alias"), ("thank", "alias")}
    assert all(d.namespace == mod.PREFIX for d in decls)
    assert all(d.cog == "KarmaCog" for d in decls)


def test_function_name_fallback_when_name_absent(mod):
    decls = _extract(
        mod,
        """
        class MiningCog(commands.Cog):
            @commands.command()
            async def mine(self, ctx):
                ...
        """,
    )
    assert [(d.token, d.kind, d.cog) for d in decls] == [("mine", "name", "MiningCog")]


def test_dynamic_name_is_skipped_not_fabricated(mod):
    # name=SOME_VAR is unresolvable — falling back to the function name would
    # fabricate a token, so the declaration must be dropped entirely.
    decls = _extract(
        mod,
        """
        class Cog(commands.Cog):
            @commands.command(name=COMMAND_NAME)
            async def helper(self, ctx):
                ...
        """,
    )
    assert decls == []


def test_group_decorator_is_prefix_namespace(mod):
    decls = _extract(
        mod,
        '''
        class OpsCog(commands.Cog):
            @commands.group(name="btd6ops", invoke_without_command=True)
            async def ops(self, ctx):
                ...
        ''',
    )
    assert [(d.token, d.namespace, d.kind) for d in decls] == [("btd6ops", mod.PREFIX, "group")]


def test_subcommands_are_excluded(mod):
    # @somegroup.command() registers under the parent group, not top-level.
    decls = _extract(
        mod,
        '''
        class OpsCog(commands.Cog):
            @commands.group(name="ops")
            async def ops(self, ctx):
                ...

            @ops.command(name="seed-data")
            async def ops_seed(self, ctx):
                ...
        ''',
    )
    assert [d.token for d in decls] == ["ops"]


def test_app_command_is_slash_namespace(mod):
    decls = _extract(
        mod,
        '''
        class CountersCog(commands.Cog):
            @app_commands.command(name="counters", description="x")
            async def counters_slash(self, interaction):
                ...
        ''',
    )
    assert [(d.token, d.namespace) for d in decls] == [("counters", mod.SLASH)]


def test_app_commands_group_assignment_is_collected(mod):
    decls = _extract(
        mod,
        '''
        btd6_app = app_commands.Group(name="btd6", description="x")
        ''',
    )
    assert [(d.token, d.namespace, d.kind, d.cog) for d in decls] == [
        ("btd6", mod.SLASH, "group", "<module>")
    ]


def test_hybrid_command_claims_both_namespaces(mod):
    # A hybrid command registers one prefix command AND one app command;
    # its aliases exist on the prefix side only.
    decls = _extract(
        mod,
        '''
        class C(commands.Cog):
            @commands.hybrid_command(name="ping", aliases=["p"])
            async def ping(self, ctx):
                ...
        ''',
    )
    assert {(d.token, d.namespace, d.kind) for d in decls} == {
        ("ping", mod.PREFIX, "name"),
        ("ping", mod.SLASH, "name"),
        ("p", mod.PREFIX, "alias"),
    }


def test_hybrid_group_claims_both_namespaces(mod):
    decls = _extract(
        mod,
        '''
        class C(commands.Cog):
            @commands.hybrid_group(name="ops")
            async def ops(self, ctx):
                ...
        ''',
    )
    assert {(d.token, d.namespace, d.kind) for d in decls} == {
        ("ops", mod.PREFIX, "group"),
        ("ops", mod.SLASH, "group"),
    }


def test_alias_tuple_form(mod):
    decls = _extract(
        mod,
        '''
        class C(commands.Cog):
            @commands.command(name="counttop", aliases=("ct", "counting_top"))
            async def top(self, ctx):
                ...
        ''',
    )
    assert {d.token for d in decls} == {"counttop", "ct", "counting_top"}


def test_unrelated_decorators_ignored(mod):
    decls = _extract(
        mod,
        """
        class C(commands.Cog):
            @commands.has_permissions(administrator=True)
            @app_commands.guild_only()
            @staticmethod
            def helper():
                ...
        """,
    )
    assert decls == []


# ---------------------------------------------------------------------------
# find_collisions — the registry rule
# ---------------------------------------------------------------------------


def _decl(mod, token, namespace, kind="name", cog="C", file="a.py", line=1):
    return mod.CommandDecl(token, namespace, kind, cog, file, line)


def test_cross_cog_name_collision_detected(mod):
    # The literal #1541 shape: two cogs, one token.
    decls = [
        _decl(mod, "give", mod.PREFIX, cog="MiningCog", file="mining_cog.py", line=10),
        _decl(mod, "give", mod.PREFIX, cog="EconomyCog", file="economy_cog.py", line=20),
    ]
    collisions = mod.find_collisions(decls)
    assert set(collisions) == {(mod.PREFIX, "give")}
    assert len(collisions[(mod.PREFIX, "give")]) == 2


def test_alias_vs_name_collision_detected(mod):
    # An alias claims the registry slot just like a primary name does.
    decls = [
        _decl(mod, "pay", mod.PREFIX, kind="name", file="economy_cog.py", line=5),
        _decl(mod, "pay", mod.PREFIX, kind="alias", file="karma_cog.py", line=9),
    ]
    assert set(mod.find_collisions(decls)) == {(mod.PREFIX, "pay")}


def test_same_cog_duplicate_detected(mod):
    # Two same-name commands in ONE cog crash the boot registry just as hard.
    decls = [
        _decl(mod, "x", mod.PREFIX, file="a.py", line=1),
        _decl(mod, "x", mod.PREFIX, file="a.py", line=50),
    ]
    assert set(mod.find_collisions(decls)) == {(mod.PREFIX, "x")}


def test_prefix_and_slash_namespaces_do_not_collide(mod):
    # Mirrors the real tree: !btd6 (prefix group) + /btd6 (slash group) coexist.
    decls = [
        _decl(mod, "btd6", mod.PREFIX, file="a.py", line=1),
        _decl(mod, "btd6", mod.SLASH, file="a.py", line=2),
    ]
    assert mod.find_collisions(decls) == {}


def test_no_collision_on_unique_tokens(mod):
    decls = [
        _decl(mod, "a", mod.PREFIX, line=1),
        _decl(mod, "b", mod.PREFIX, line=2),
    ]
    assert mod.find_collisions(decls) == {}


# ---------------------------------------------------------------------------
# collect_all + main — end to end on a staged tree and on the real tree
# ---------------------------------------------------------------------------


def _stage(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "cogs"
    root.mkdir()
    for name, src in files.items():
        (root / name).write_text(textwrap.dedent(src), encoding="utf-8")
    return root


def test_main_exit_1_and_sites_on_staged_collision(mod, tmp_path, capsys, monkeypatch):
    root = _stage(
        tmp_path,
        {
            "mining_cog.py": '''
                class MiningCog(commands.Cog):
                    @commands.command(name="give")
                    async def admin_give(self, ctx):
                        ...
                ''',
            "economy_cog.py": '''
                class EconomyCog(commands.Cog):
                    @commands.command(name="give", aliases=["pay"])
                    async def give(self, ctx):
                        ...
                ''',
        },
    )
    monkeypatch.setattr(mod, "COGS_ROOT", root)
    assert mod.main([]) == 1
    out = capsys.readouterr().out
    assert "'give'" in out
    # dedented fixtures open with a blank line → the decorator sits on line 3
    assert "mining_cog.py:3" in out
    assert "economy_cog.py:3" in out


def test_main_exit_0_on_clean_staged_tree(mod, tmp_path, capsys, monkeypatch):
    root = _stage(
        tmp_path,
        {
            "a_cog.py": '''
                class ACog(commands.Cog):
                    @commands.command(name="alpha")
                    async def alpha(self, ctx):
                        ...
                ''',
        },
    )
    monkeypatch.setattr(mod, "COGS_ROOT", root)
    assert mod.main([]) == 0
    assert "0 collisions" in capsys.readouterr().out


def test_list_mode_exits_0_even_with_collisions(mod, tmp_path, capsys, monkeypatch):
    root = _stage(
        tmp_path,
        {
            "a_cog.py": '''
                class A(commands.Cog):
                    @commands.command(name="dup")
                    async def one(self, ctx):
                        ...

                    @commands.command(name="dup")
                    async def two(self, ctx):
                        ...
                ''',
        },
    )
    monkeypatch.setattr(mod, "COGS_ROOT", root)
    assert mod.main(["--list"]) == 0
    assert "token claims" in capsys.readouterr().out


def test_live_tree_has_zero_collisions(mod):
    """Standing regression: the real cog tree stays collision-free (post-#1544).

    If this ever fails, a PR introduced the #1541 outage class — fix the
    collision, do not relax the test.
    """
    decls = mod.collect_all()
    assert len(decls) > 300  # census sanity: the surface is large and real
    assert mod.find_collisions(decls) == {}
