"""Tests for the reaction-role Add message-picker helpers (owner direction).

Covers the pure helpers behind the picker — the select label/description for a
recent message, the panel-message exclusion, and the history fetch (including its
graceful degrade when history can't be read). The interaction wiring
(`_AddSourceView` / `_NewMessageModal`) is a thin shell over these + the existing
`_BindEmotesView`, which has its own tests.
"""

from __future__ import annotations

from types import SimpleNamespace

import discord
import pytest

from views.roles import reaction_panel as rp


def _msg(mid, author="Menno", content="hi", embeds=(), attachments=()):
    return SimpleNamespace(
        id=mid,
        author=SimpleNamespace(display_name=author),
        content=content,
        embeds=list(embeds),
        attachments=list(attachments),
    )


class _FakeChannel:
    """Minimal channel with an async ``history`` matching discord.py's shape."""

    def __init__(self, messages, *, exc=None):
        self._messages = messages
        self._exc = exc

    def history(self, *, limit):
        messages = list(self._messages)[:limit]
        exc = self._exc

        async def _gen():
            if exc is not None:
                raise exc
            for message in messages:
                yield message

        return _gen()


def test_message_label_variants():
    assert rp._message_label(_msg(1, "Menno", "Hello   world")) == "Menno: Hello world"
    assert rp._message_label(_msg(2, "Bot", "", embeds=[object()])) == "Bot: [embed]"
    assert (
        rp._message_label(_msg(3, "Bot", "", attachments=[object()]))
        == "Bot: [attachment]"
    )
    assert rp._message_label(_msg(4, "Bot", "")) == "Bot: [no text]"


def test_message_desc():
    assert rp._message_desc(_msg(77)) == "id 77"


def test_panel_message_id():
    assert rp._panel_message_id(SimpleNamespace(message=None)) is None
    assert rp._panel_message_id(SimpleNamespace(message=SimpleNamespace(id=9))) == 9


@pytest.mark.asyncio
async def test_recent_messages_excludes_panel_and_preserves_order():
    channel = _FakeChannel([_msg(10), _msg(20), _msg(30)])
    out = await rp._recent_messages(channel, exclude_id=20, limit=10)
    assert [m.id for m in out] == [10, 30]


@pytest.mark.asyncio
async def test_recent_messages_degrades_to_empty_when_history_forbidden():
    forbidden = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "no")
    channel = _FakeChannel([_msg(10)], exc=forbidden)
    out = await rp._recent_messages(channel, exclude_id=None, limit=10)
    assert out == []
