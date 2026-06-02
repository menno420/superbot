"""Pin slash/prefix parity for the whole BTD6 command surface.

Every prefix command must have a slash twin (and vice versa) across the
mother cog + sibling cogs, except the documented ``SLASH_ONLY`` /
``PREFIX_ONLY`` allowlists. Twins must share at least one ``build_*`` /
``safe_*`` backbone call so the two forms can't drift apart.

Runtime-introspection based (the ``test_btd6_ops_command_parity`` pattern):
the surface now spans four cog modules, so instead of AST-scanning a single
file we instantiate the *registered* BTD6 cog classes and walk their command
trees. The shared-backbone check reads each command callback's source via
``inspect.getsource`` so it covers exactly the registered set, wherever a
command physically lives.
"""

from __future__ import annotations

import ast
import inspect
import textwrap
from unittest.mock import MagicMock

import pytest
from discord import app_commands
from discord.ext import commands

from cogs.btd6_cog import BTD6Cog
from cogs.btd6_events_cog import BTD6EventsCog
from cogs.btd6_reference_cog import BTD6ReferenceCog
from cogs.btd6_strategy_cog import BTD6StrategyCog

# The cogs that together form the BTD6 command surface. The ops cog has its
# own parity test (test_btd6_ops_command_parity.py) and is excluded here.
_COG_CLASSES = (BTD6Cog, BTD6ReferenceCog, BTD6EventsCog, BTD6StrategyCog)

# ``submit`` triggers a Discord modal (slash-only); its prefix form is a
# redirect string that intentionally shares no builder, so it is exempt from
# both the prefix-twin requirement and the backbone check.
SLASH_ONLY = frozenset({"submit"})

# ``ctteam`` — admin utility to paste a CT bracket id / group URL. Prefix is
# the natural surface for pasting a long URL, and it is a low-traffic config
# command, so it intentionally has no slash twin.
PREFIX_ONLY: frozenset[str] = frozenset({"ctteam"})

# Prefix group parents (``!btd6`` / ``!btd6ref`` / …) are not leaves.
_GROUP_PARENTS = frozenset({"btd6", "btd6ref", "btd6events", "btd6strat"})


def _collect() -> tuple[dict[str, object], dict[str, object]]:
    """Aggregate prefix + slash leaf commands across all BTD6 cogs."""
    prefix: dict[str, object] = {}
    slash: dict[str, object] = {}
    for cls in _COG_CLASSES:
        cog = cls(bot=MagicMock())
        for cmd in cog.walk_commands():
            if isinstance(cmd, commands.Group):
                continue
            prefix[cmd.name] = cmd
        for cmd in cog.walk_app_commands():
            if isinstance(cmd, app_commands.Command):
                slash[cmd.name] = cmd
    return prefix, slash


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


def test_every_slash_has_a_prefix_twin() -> None:
    prefix, slash = _collect()
    missing = {n for n in slash if n not in SLASH_ONLY and n not in prefix}
    assert not missing, (
        f"Slash commands without a prefix twin: {sorted(missing)}. "
        f"Add them to SLASH_ONLY if intentionally slash-only."
    )


def test_every_prefix_has_a_slash_twin() -> None:
    prefix, slash = _collect()
    missing = {
        n
        for n in prefix
        if n not in PREFIX_ONLY and n not in _GROUP_PARENTS and n not in slash
    }
    assert not missing, (
        f"Prefix commands without a slash twin: {sorted(missing)}. "
        f"Add them to PREFIX_ONLY if intentionally prefix-only."
    )


# ---------------------------------------------------------------------------
# Shared backbone
# ---------------------------------------------------------------------------

# Names that count as "shared backbone" — at least one must appear in BOTH the
# prefix and slash forms of a twin. ``build_*`` covers the entire
# ``_builders`` / ``_embeds`` / ``strategy_browse`` API; ``reply_ephemeral``
# is the shared ephemeral slash backbone.
_SHARED_BACKBONE_PREFIXES = ("build_",)
_SHARED_BACKBONE_NAMES = frozenset(
    {
        "_response_to_embed",
        "answer_question",
        "reply_ephemeral",
        "response_to_embed",
        "safe_defer",
        "safe_edit",
        "safe_followup",
    },
)


def _called_names(cmd: object) -> set[str]:
    """Names of all functions called in a command callback's *body*.

    Decorators are excluded (walk only the function body) so the check sees
    real call sites, not the ``@group.command(...)`` registration.
    """
    src = textwrap.dedent(inspect.getsource(cmd.callback))  # type: ignore[attr-defined]
    func_node = ast.parse(src).body[0]
    names: set[str] = set()
    for stmt in getattr(func_node, "body", []):
        for node in ast.walk(stmt):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _backbone_calls(names: set[str]) -> set[str]:
    return {
        n
        for n in names
        if n in _SHARED_BACKBONE_NAMES
        or any(n.startswith(p) for p in _SHARED_BACKBONE_PREFIXES)
    }


_PREFIX_MAP, _SLASH_MAP = _collect()
_TWINS = sorted(n for n in _SLASH_MAP if n not in SLASH_ONLY and n in _PREFIX_MAP)


@pytest.mark.parametrize("cmd", _TWINS)
def test_twins_share_a_backbone_call(cmd: str) -> None:
    prefix, slash = _collect()
    prefix_calls = _backbone_calls(_called_names(prefix[cmd]))
    slash_calls = _backbone_calls(_called_names(slash[cmd]))
    common = prefix_calls & slash_calls
    assert common, (
        f"Twins for {cmd!r} share no backbone call. "
        f"Prefix calls backbone: {sorted(prefix_calls)}; "
        f"slash calls backbone: {sorted(slash_calls)}. "
        f"Both forms should route through a shared build_* / reply_ephemeral "
        f"/ safe_* helper to prevent drift."
    )
