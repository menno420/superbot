"""BTD6 boundary regression pins (PR-A).

These tests lock in invariants the AI Platform + BTD6 polish series
relies on:

* No BTD6 module installs an ``on_message`` listener — natural-
  language eligibility is owned by the central AI Platform stage.
* No BTD6 module imports or calls the AI Platform write helpers in
  :mod:`utils.db.ai`.
* Every BTD6 prefix command has a slash twin (parity test).
* The BTD6 status / panel embeds no longer carry the stale
  "Module 4 / deterministic-only / AI augmentation off /
  No provider, no network, no AI" copy.
"""

from __future__ import annotations

import ast
from pathlib import Path

import discord
import pytest

from cogs.btd6_cog import BTD6Cog, build_status_embed
from views.btd6.panel import build_btd6_panel_embed


_DISBOT_ROOT = Path(__file__).resolve().parents[3] / "disbot"

# Module paths owned by BTD6.
_BTD6_PATHS = [
    _DISBOT_ROOT / "cogs" / "btd6_cog.py",
    _DISBOT_ROOT / "cogs" / "btd6",
    _DISBOT_ROOT / "views" / "btd6",
    _DISBOT_ROOT / "services",  # filtered below
]


def _btd6_python_files() -> list[Path]:
    """All Python files owned by BTD6 (cog + views + btd6_* services)."""
    paths: list[Path] = []
    for root in _BTD6_PATHS:
        if root.is_file():
            paths.append(root)
            continue
        if not root.is_dir():
            continue
        for p in root.rglob("*.py"):
            # ``services/`` only contains btd6_* files.
            if root.name == "services" and not p.name.startswith("btd6_"):
                continue
            paths.append(p)
    return paths


# ---------------------------------------------------------------------------
# Retired passive stage regression
# ---------------------------------------------------------------------------


def test_no_btd6_module_installs_on_message_listener():
    """``@commands.Cog.listener('on_message')`` is forbidden in BTD6.

    The retired passive stage stays retired; the central AI Platform
    stage is the only natural-language entry point.
    """
    offenders: list[str] = []
    for path in _btd6_python_files():
        src = path.read_text()
        tree = ast.parse(src, filename=str(path))
        for node in ast.walk(tree):
            # Look for any decorator literal "on_message" — this catches
            # both ``@commands.Cog.listener(name='on_message')`` and
            # ``@bot.event`` style ``async def on_message`` definitions.
            if (
                isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
                and node.name == "on_message"
            ):
                offenders.append(f"{path.relative_to(_DISBOT_ROOT)}::{node.name}")
            for dec in getattr(node, "decorator_list", []):
                src_seg = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if "on_message" in src_seg:
                    offenders.append(
                        f"{path.relative_to(_DISBOT_ROOT)}::{getattr(node, 'name', '?')}",
                    )
    assert offenders == [], (
        "BTD6 modules must not register on_message listeners; "
        f"offenders: {offenders}"
    )


# ---------------------------------------------------------------------------
# BTD6 must not import AI Platform write helpers
# ---------------------------------------------------------------------------


_FORBIDDEN_AI_DB_SYMBOLS = {
    "upsert_channel_policy",
    "upsert_category_policy",
    "upsert_role_policy",
    "upsert_instruction_profile",
    "upsert_guild_policy",
}


def test_no_btd6_module_imports_ai_db_write_helpers():
    offenders: list[str] = []
    for path in _btd6_python_files():
        src = path.read_text()
        # Substring-grep is sufficient: these are the actual function
        # names exported by ``utils/db/ai.py``. Anything legitimately
        # mentioning them in a docstring would also be a concern.
        for symbol in _FORBIDDEN_AI_DB_SYMBOLS:
            if symbol in src:
                offenders.append(f"{path.relative_to(_DISBOT_ROOT)}::{symbol}")
    assert offenders == [], (
        "BTD6 modules must not import or reference AI Platform write "
        f"helpers; offenders: {offenders}"
    )


# ---------------------------------------------------------------------------
# Prefix / slash parity
# ---------------------------------------------------------------------------


def _expected_parity_names() -> set[str]:
    """Names that must exist on BOTH the prefix and slash surfaces."""
    return {
        "status",
        "diagnostics",
        "ask",
        "tower",
        "hero",
        "round",
        "test-intent",
        "why-no-response",
        "sources",
        "strategies",
        "pending",
    }


def test_btd6_prefix_and_slash_commands_have_parity():
    cog = BTD6Cog(bot=type("Bot", (), {})())

    prefix_names: set[str] = set()
    for cmd in cog.walk_commands():
        # Only consider commands inside the btd6 group.
        if getattr(cmd, "parent", None) is not None and cmd.parent.name == "btd6":
            prefix_names.add(cmd.name)

    # The slash group lives on the cog as a class attribute.
    slash_group = cog.btd6_app_group
    slash_names = {c.name for c in slash_group.commands}

    expected = _expected_parity_names()
    missing_prefix = expected - prefix_names
    missing_slash = expected - slash_names
    assert not missing_prefix, f"Missing prefix commands: {missing_prefix}"
    assert not missing_slash, f"Missing slash commands: {missing_slash}"


# ---------------------------------------------------------------------------
# Truthful copy
# ---------------------------------------------------------------------------


_STALE_STRINGS = (
    "Module 4",
    "deterministic-only",
    "AI augmentation off",
    "No provider, no network, no AI",
)


def test_status_embed_has_no_stale_strings():
    embed = build_status_embed()
    blob = (embed.title or "") + " " + (embed.description or "")
    for stale in _STALE_STRINGS:
        assert stale not in blob, f"Stale string {stale!r} in status embed"


def test_panel_embed_has_no_stale_strings():
    embed = build_btd6_panel_embed()
    blob = (embed.title or "") + " " + (embed.description or "")
    for stale in _STALE_STRINGS:
        assert stale not in blob, f"Stale string {stale!r} in panel embed"


# ---------------------------------------------------------------------------
# Embed builders return valid embeds with the new audit fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_why_no_response_builder_surfaces_audit_fields(monkeypatch):
    """The PR-A embed extension surfaces the five new audit fields:
    ``policy_snapshot_hash``, ``instruction_profile_ids``, ``route``,
    ``provider``, ``model`` — plus the existing reason_code.
    """
    from cogs.btd6._builders import build_why_no_response_payload
    from services import ai_decision_audit_service

    async def _query(_guild_id, **_kw):
        return [
            {
                "task": "btd6.answer",
                "decision": "denied",
                "reason_code": "below_min_level",
                "route": "btd6.answer",
                "channel_id": 1,
                "user_id": 9,
                "policy_snapshot_hash": "deadbeef",
                "instruction_profile_ids": [11, 22],
                "provider": "anthropic",
                "model": "claude-haiku",
            },
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _query)
    payload = await build_why_no_response_payload(42, limit=5)
    assert isinstance(payload, discord.Embed)
    blob = "\n".join(f"{f.name}\n{f.value}" for f in payload.fields)
    assert "below_min_level" in blob
    assert "deadbeef" in blob
    assert "11" in blob and "22" in blob
    assert "anthropic" in blob
    assert "claude-haiku" in blob
