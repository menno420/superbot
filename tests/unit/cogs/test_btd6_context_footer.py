"""Coverage for ``utils/btd6/context_footer.py``.

The helper must preserve existing footer text, preserve icon_url,
and be idempotent. Tests pin each of those rules.
"""

from __future__ import annotations

import discord
import pytest

from utils.btd6.context_footer import append_context_footer


def test_empty_footer_gets_ctx_only() -> None:
    embed = discord.Embed(title="x")
    append_context_footer(embed, "btd6_hub:main")
    assert embed.footer.text == "ctx=btd6_hub:main"


def test_existing_footer_preserved_and_appended() -> None:
    embed = discord.Embed(title="x")
    embed.set_footer(text="Sources: BTD6 data v1.0")
    append_context_footer(embed, "btd6_tower:dart_monkey")
    assert embed.footer.text == "Sources: BTD6 data v1.0 • ctx=btd6_tower:dart_monkey"


def test_existing_command_hint_footer_preserved() -> None:
    embed = discord.Embed(title="x")
    embed.set_footer(text="!btd6 ask <q> · !btd6 tower <n>")
    append_context_footer(embed, "btd6_hub:main")
    assert "!btd6 ask <q> · !btd6 tower <n>" in (embed.footer.text or "")
    assert "ctx=btd6_hub:main" in (embed.footer.text or "")


def test_idempotent_same_context_id() -> None:
    embed = discord.Embed(title="x")
    embed.set_footer(text="Sources: x")
    append_context_footer(embed, "btd6_tower:dart_monkey")
    first_text = embed.footer.text
    append_context_footer(embed, "btd6_tower:dart_monkey")
    assert embed.footer.text == first_text  # no double-append


def test_different_context_id_replaces_marker() -> None:
    """Re-rendering an embed with a fresh context_id replaces, not appends."""
    embed = discord.Embed(title="x")
    embed.set_footer(text="Sources: x")
    append_context_footer(embed, "btd6_tower:dart_monkey")
    append_context_footer(embed, "btd6_tower:bomb_shooter")
    assert (embed.footer.text or "").count("ctx=") == 1
    assert "btd6_tower:bomb_shooter" in (embed.footer.text or "")
    assert "btd6_tower:dart_monkey" not in (embed.footer.text or "")


def test_icon_url_preserved() -> None:
    embed = discord.Embed(title="x")
    embed.set_footer(text="src", icon_url="https://example.com/icon.png")
    append_context_footer(embed, "btd6_hub:main")
    assert embed.footer.icon_url == "https://example.com/icon.png"
    assert "ctx=btd6_hub:main" in (embed.footer.text or "")


def test_empty_context_id_raises() -> None:
    embed = discord.Embed(title="x")
    with pytest.raises(ValueError, match="empty"):
        append_context_footer(embed, "")


def test_returns_same_embed() -> None:
    embed = discord.Embed(title="x")
    result = append_context_footer(embed, "btd6_hub:main")
    assert result is embed
