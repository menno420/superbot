"""``!platform flags`` embed splits operator flags from internal gates (PR2).

``build_flags_embed`` resolves every declared flag for the (here global)
context. With ``feature_flag.primary`` OFF by default the evaluator
short-circuits to declared defaults before touching the DB, so this test
runs offline.
"""

from __future__ import annotations

import pytest

from cogs.diagnostic._platform_embeds import build_flags_embed


@pytest.mark.asyncio
async def test_flags_embed_splits_operator_and_internal():
    embed = await build_flags_embed(None)
    fields = {f.name: f.value for f in embed.fields}

    assert "Operator flags" in fields
    assert "Internal / platform gates" in fields

    operator = fields["Operator flags"]
    internal = fields["Internal / platform gates"]

    # The two operator-facing flags land in the operator section…
    assert "settings.manager_cog.enabled" in operator
    assert "youtube.context.enabled" in operator
    # …and carry their plain-language label.
    assert "Settings menu" in operator

    # …while the migration / kill-switch gates land in the internal section.
    assert "bindings.primary" in internal
    assert "feature_flag.primary" in internal

    # Operator flags do not leak into the internal section.
    assert "settings.manager_cog.enabled" not in internal
    # The internal section is clearly marked as not-user-facing.
    assert "not user-facing" in internal.lower()
