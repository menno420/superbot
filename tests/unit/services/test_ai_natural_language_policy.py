"""M2 — Resolver precedence tests for ``ai_natural_language_policy``.

Stubs the four DB read primitives in ``utils.db.ai`` so the resolver
exercises the layered precedence rule without a real database.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import PolicyDenialReason  # noqa: E402
from services import ai_natural_language_policy as policy  # noqa: E402
from services.ai_natural_language_policy import MessageContext  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_ai_db(monkeypatch):
    state: dict[str, Any] = {
        "policy": None,
        "channel": {},
        "category": {},
        "role": {},
    }

    async def _get_guild_policy(guild_id: int):
        return state["policy"]

    async def _list_channel_policies(guild_id: int):
        return [
            dict(row, channel_id=cid)
            for cid, row in state["channel"].items()
        ]

    async def _list_category_policies(guild_id: int):
        return [
            dict(row, category_id=cid)
            for cid, row in state["category"].items()
        ]

    async def _list_role_policies(guild_id: int):
        return [
            dict(row, role_id=rid)
            for rid, row in state["role"].items()
        ]

    monkeypatch.setattr(ai_db, "get_guild_policy", _get_guild_policy)
    monkeypatch.setattr(ai_db, "list_channel_policies", _list_channel_policies)
    monkeypatch.setattr(ai_db, "list_category_policies", _list_category_policies)
    monkeypatch.setattr(ai_db, "list_role_policies", _list_role_policies)

    policy._reset_for_tests()
    yield state
    policy._reset_for_tests()


def _msg(**overrides) -> MessageContext:
    base = dict(
        guild_id=1,
        channel_id=10,
        category_id=100,
        user_id=999,
        user_level=5,
        user_role_ids=(),
        is_mention=False,
        is_fresh_user=False,
    )
    base.update(overrides)
    return MessageContext(**base)


def _enabled_policy(**overrides) -> dict[str, Any]:
    base = dict(
        guild_id=1,
        enabled=True,
        natural_language_enabled=True,
        default_provider="deterministic",
        default_model="",
        minimum_level_default=2,
        cooldown_seconds=30,
        fresh_user_mention_allowance=1,
        guild_instruction_profile_id=None,
        generation=1,
    )
    base.update(overrides)
    return base


async def test_unconfigured_guild_denies(_stub_ai_db):
    """No ai_guild_policy row → deny by default with the right reason."""
    decision = await policy.resolve(_msg())
    assert not decision.allowed
    assert decision.reason_code is PolicyDenialReason.GUILD_NOT_CONFIGURED


async def test_ai_disabled_blocks_everything(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(enabled=False)
    decision = await policy.resolve(_msg())
    assert not decision.allowed
    assert decision.reason_code is PolicyDenialReason.AI_GLOBALLY_DISABLED


async def test_nl_disabled_blocks_everything(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(natural_language_enabled=False)
    decision = await policy.resolve(_msg())
    assert decision.reason_code is PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD


async def test_happy_path_allows(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    decision = await policy.resolve(_msg(user_level=5))
    assert decision.allowed is True
    assert decision.reason_code is PolicyDenialReason.NONE


async def test_below_minimum_level_denies(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(minimum_level_default=10)
    decision = await policy.resolve(_msg(user_level=3))
    assert decision.reason_code is PolicyDenialReason.BELOW_MIN_LEVEL


async def test_channel_disabled_overrides_role_allow(_stub_ai_db):
    """Channel mode='disabled' wins even when an allowed role lowers the level."""
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["channel"] = {
        10: {"mode": "disabled", "min_level": None,
             "cooldown_seconds": None, "instruction_profile_id": None},
    }
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": 0,
             "bypass_cooldown": False},
    }
    decision = await policy.resolve(_msg(user_role_ids=(77,)))
    assert decision.reason_code is PolicyDenialReason.CHANNEL_DISABLED


async def test_category_disabled_overrides_role_allow(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {
        100: {"mode": "disabled", "min_level": None,
              "cooldown_seconds": None, "instruction_profile_id": None},
    }
    decision = await policy.resolve(_msg())
    assert decision.reason_code is PolicyDenialReason.CATEGORY_DISABLED


async def test_role_deny_beats_allow(_stub_ai_db):
    """Explicit role 'deny' wins over another role's 'allow'."""
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": 0, "bypass_cooldown": False},
        88: {"decision": "deny",  "min_level_override": None, "bypass_cooldown": False},
    }
    decision = await policy.resolve(_msg(user_role_ids=(77, 88)))
    assert decision.reason_code is PolicyDenialReason.ROLE_DENIED


async def test_allowed_role_min_level_lowering_takes_most_permissive(_stub_ai_db):
    """Among allowed roles the smallest min_level_override wins."""
    _stub_ai_db["policy"] = _enabled_policy(minimum_level_default=10)
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": 5, "bypass_cooldown": False},
        88: {"decision": "allow", "min_level_override": 2, "bypass_cooldown": False},
    }
    decision = await policy.resolve(
        _msg(user_role_ids=(77, 88), user_level=3),
    )
    assert decision.allowed is True
    assert decision.effective_min_level == 2


async def test_mention_only_channel_requires_mention(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["channel"] = {
        10: {"mode": "mention_only", "min_level": None,
             "cooldown_seconds": None, "instruction_profile_id": None},
    }
    decision_no_mention = await policy.resolve(_msg(is_mention=False))
    decision_mention = await policy.resolve(_msg(is_mention=True))
    assert decision_no_mention.reason_code is PolicyDenialReason.NO_MENTION_REQUIRED
    assert decision_mention.allowed is True


async def test_fresh_user_mention_allowance_lets_first_reply_through(_stub_ai_db):
    """A fresh user @-mentioning the bot once gets past the level gate."""
    _stub_ai_db["policy"] = _enabled_policy(
        minimum_level_default=5,
        fresh_user_mention_allowance=1,
    )
    decision = await policy.resolve(
        _msg(user_level=0, is_mention=True, is_fresh_user=True),
    )
    assert decision.allowed is True


async def test_bypass_cooldown_role_zeroes_effective_cooldown(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(cooldown_seconds=120)
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": None, "bypass_cooldown": True},
    }
    decision = await policy.resolve(_msg(user_role_ids=(77,)))
    assert decision.allowed is True
    assert decision.effective_cooldown == 0


async def test_generation_bump_invalidates_resolver_cache(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(generation=1)
    first = await policy.resolve(_msg())
    assert first.allowed is True
    # Flip enabled to false and bump generation; next resolve must
    # see the change without explicit invalidate().
    _stub_ai_db["policy"] = _enabled_policy(enabled=False, generation=2)
    second = await policy.resolve(_msg())
    assert second.reason_code is PolicyDenialReason.AI_GLOBALLY_DISABLED


# ---------------------------------------------------------------------------
# Most-specific-wins inheritance (PR 1 — resolver refactor)
# ---------------------------------------------------------------------------


def _chan(mode: str, **overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "mode": mode,
        "min_level": None,
        "cooldown_seconds": None,
        "instruction_profile_id": None,
    }
    base.update(overrides)
    return base


def _cat(mode: str, **overrides) -> dict[str, Any]:
    base: dict[str, Any] = {
        "mode": mode,
        "min_level": None,
        "cooldown_seconds": None,
        "instruction_profile_id": None,
    }
    base.update(overrides)
    return base


async def test_guild_enabled_false_cannot_be_bypassed_by_channel_always_reply(
    _stub_ai_db,
):
    """``enabled=false`` is the only hard kill — scoped overrides cannot resurrect AI."""
    _stub_ai_db["policy"] = _enabled_policy(enabled=False)
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is False
    assert decision.reason_code is PolicyDenialReason.AI_GLOBALLY_DISABLED


async def test_guild_nl_disabled_with_channel_always_reply_allows(_stub_ai_db):
    """The bug case: guild NL baseline says disabled, channel says always_reply → allow."""
    _stub_ai_db["policy"] = _enabled_policy(natural_language_enabled=False)
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is True
    assert decision.reason_code is PolicyDenialReason.NONE
    assert decision.effective_mode == "always_reply"
    assert decision.effective_source == "channel"


async def test_guild_nl_disabled_with_channel_inherit_still_denies(_stub_ai_db):
    """The inverse: no scoped override → guild baseline disabled applies, source=guild."""
    _stub_ai_db["policy"] = _enabled_policy(natural_language_enabled=False)
    decision = await policy.resolve(_msg())
    assert decision.allowed is False
    assert decision.reason_code is PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD


async def test_channel_always_reply_overrides_category_disabled(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("disabled")}
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is True
    assert decision.effective_source == "channel"
    assert decision.effective_mode == "always_reply"


async def test_channel_disabled_beats_category_always_reply(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("always_reply")}
    _stub_ai_db["channel"] = {10: _chan("disabled")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is False
    assert decision.reason_code is PolicyDenialReason.CHANNEL_DISABLED


async def test_channel_mention_only_beats_category_always_reply(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("always_reply")}
    _stub_ai_db["channel"] = {10: _chan("mention_only")}
    decision_no = await policy.resolve(_msg(is_mention=False))
    decision_yes = await policy.resolve(_msg(is_mention=True))
    assert decision_no.reason_code is PolicyDenialReason.NO_MENTION_REQUIRED
    assert decision_yes.allowed is True


async def test_channel_always_reply_beats_category_mention_only(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("mention_only")}
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    decision = await policy.resolve(_msg(is_mention=False))
    assert decision.allowed is True
    assert decision.effective_source == "channel"


async def test_category_always_reply_when_channel_inherits(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy(natural_language_enabled=False)
    _stub_ai_db["category"] = {100: _cat("always_reply")}
    _stub_ai_db["channel"] = {10: _chan("inherit")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is True
    assert decision.effective_source == "category"
    assert decision.effective_mode == "always_reply"


async def test_category_mention_only_requires_mention_when_channel_inherits(
    _stub_ai_db,
):
    """Closes the gap: today's resolver ignores ``mention_only`` at the category scope."""
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("mention_only")}
    # No channel row → channel inherits.
    decision_no = await policy.resolve(_msg(is_mention=False))
    decision_yes = await policy.resolve(_msg(is_mention=True))
    assert decision_no.reason_code is PolicyDenialReason.NO_MENTION_REQUIRED
    assert decision_no.effective_source == "category"
    assert decision_yes.allowed is True


async def test_category_disabled_applies_when_channel_inherits(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("disabled")}
    _stub_ai_db["channel"] = {10: _chan("inherit")}
    decision = await policy.resolve(_msg())
    assert decision.reason_code is PolicyDenialReason.CATEGORY_DISABLED
    assert decision.effective_source == "category"


async def test_channel_inherit_falls_through_to_category(_stub_ai_db):
    """An explicit ``inherit`` row is treated identically to a missing row."""
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["category"] = {100: _cat("always_reply")}
    _stub_ai_db["channel"] = {10: _chan("inherit")}
    decision = await policy.resolve(_msg())
    assert decision.allowed is True
    assert decision.effective_source == "category"


async def test_role_allow_can_lower_min_level_under_always_reply(_stub_ai_db):
    """Role most-permissive override still applies after most-specific-wins."""
    _stub_ai_db["policy"] = _enabled_policy(minimum_level_default=10)
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": 1, "bypass_cooldown": False},
    }
    decision = await policy.resolve(
        _msg(user_role_ids=(77,), user_level=2),
    )
    assert decision.allowed is True
    assert decision.effective_min_level == 1


async def test_role_cannot_bypass_disabled_effective_mode(_stub_ai_db):
    """A permissive role does not resurrect a ``disabled`` effective mode."""
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["channel"] = {10: _chan("disabled")}
    _stub_ai_db["role"] = {
        77: {"decision": "allow", "min_level_override": 0, "bypass_cooldown": True},
    }
    decision = await policy.resolve(_msg(user_role_ids=(77,)))
    assert decision.allowed is False
    assert decision.reason_code is PolicyDenialReason.CHANNEL_DISABLED


async def test_role_deny_still_denies_after_always_reply_mode(_stub_ai_db):
    _stub_ai_db["policy"] = _enabled_policy()
    _stub_ai_db["channel"] = {10: _chan("always_reply")}
    _stub_ai_db["role"] = {
        88: {"decision": "deny", "min_level_override": None, "bypass_cooldown": False},
    }
    decision = await policy.resolve(_msg(user_role_ids=(88,)))
    assert decision.reason_code is PolicyDenialReason.ROLE_DENIED


async def test_effective_fields_empty_on_early_returns(_stub_ai_db):
    """Early returns (no row, global kill) leave effective_mode/source empty."""
    decision_unconf = await policy.resolve(_msg())
    assert decision_unconf.effective_mode == ""
    assert decision_unconf.effective_source == ""

    _stub_ai_db["policy"] = _enabled_policy(enabled=False)
    decision_off = await policy.resolve(_msg())
    assert decision_off.effective_mode == ""
    assert decision_off.effective_source == ""


async def test_channel_inherit_carries_param_overrides(_stub_ai_db):
    """Value inheritance: a row with mode=inherit can still set min_level/cooldown."""
    _stub_ai_db["policy"] = _enabled_policy(
        minimum_level_default=10, cooldown_seconds=60,
    )
    _stub_ai_db["channel"] = {
        10: _chan("inherit", min_level=2, cooldown_seconds=5),
    }
    decision = await policy.resolve(_msg(user_level=3))
    assert decision.allowed is True
    assert decision.effective_min_level == 2
    assert decision.effective_cooldown == 5
