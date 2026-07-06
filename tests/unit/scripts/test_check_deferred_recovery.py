"""Tests for scripts/check_deferred_recovery.py — the deferred-action restart-recovery guard (item #5).

Covers the pure ``analyze()`` on injected synthetic sources:

* it BITES on the bug shape (a spawned task that sleeps then mutates Discord state, in a module with no
  persisted deadline + no boot reconcile) — the Q-0120 gate-bites meta-test;
* it stays quiet on the recoverable shape (persist + reconcile), on infra loops / game re-renders /
  non-spawned inline mutations, and on an allowlisted timer;
* a ground-truth check that the real tree is clean (the one finding — security's ADR-002 timer — is
  triaged + allowlisted), so a NEW deferred lock without recovery reddens this test.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "check_deferred_recovery",
    _REPO_ROOT / "scripts" / "check_deferred_recovery.py",
)
assert _SPEC and _SPEC.loader
cdr = importlib.util.module_from_spec(_SPEC)
sys.modules["check_deferred_recovery"] = cdr  # register before exec (dataclass string-annotation quirk)
_SPEC.loader.exec_module(cdr)


def _flags(src: str, exceptions: dict | None = None) -> set[tuple[str, str]]:
    return {
        (f.file, f.spawn_target)
        for f in cdr.analyze({"disbot/cogs/x.py": src}, exceptions or {})
    }


_BUG = (
    "import asyncio\n"
    "from disbot.runtime import tasks\n"
    "class ProofCog:\n"
    "    def schedule(self, channel):\n"
    "        async def _auto_unlock():\n"
    "            await asyncio.sleep(3600)\n"
    "            await channel.set_permissions(role, view_channel=False)\n"
    "        tasks.spawn('unlock', _auto_unlock())\n"
)


def test_bug_shape_is_flagged():
    assert ("disbot/cogs/x.py", "_auto_unlock") in _flags(_BUG)


def test_recoverable_shape_is_clean():
    """Same timer, but the module persists a deadline (upsert_lock) and reconciles on_ready."""
    fixed = (
        "import asyncio\n"
        "from disbot.runtime import tasks\n"
        "from utils.db import proof_channel_locks\n"
        "class ProofCog:\n"
        "    async def on_ready(self):\n"
        "        await self._reconcile_locks()\n"
        "    async def _reconcile_locks(self): ...\n"
        "    async def _persist_timed_lock(self, gid, deadline):\n"
        "        await proof_channel_locks.upsert_lock(gid, deadline)\n"
        "    def schedule(self, channel):\n"
        "        async def _auto_unlock():\n"
        "            await asyncio.sleep(3600)\n"
        "            await channel.set_permissions(role, view_channel=False)\n"
        "        tasks.spawn('unlock', _auto_unlock())\n"
    )
    assert _flags(fixed) == set()


def test_infra_loop_without_state_mutation_is_clean():
    infra = (
        "import asyncio\n"
        "from disbot.runtime import tasks\n"
        "class Gc:\n"
        "    def start(self):\n"
        "        async def _run_gc_loop():\n"
        "            while True:\n"
        "                await asyncio.sleep(60)\n"
        "                await self._delete_stale()\n"
        "        tasks.spawn('gc', _run_gc_loop())\n"
    )
    assert _flags(infra) == set()


def test_game_message_rerender_is_clean():
    game = (
        "import asyncio\n"
        "from disbot.runtime import tasks\n"
        "class Poker:\n"
        "    def start(self, msg):\n"
        "        async def _turn_timeout():\n"
        "            await asyncio.sleep(30)\n"
        "            await msg.edit(embed=self.render())\n"
        "        tasks.spawn('t', _turn_timeout())\n"
    )
    assert _flags(game) == set()


def test_inline_not_spawned_is_clean():
    """A sleep+mutation awaited inline (not fire-and-forget) is not the deferred-recovery risk."""
    inline = (
        "import asyncio\n"
        "class Svc:\n"
        "    async def do(self, channel):\n"
        "        await asyncio.sleep(30)\n"
        "        await channel.set_permissions(r, view_channel=False)\n"
    )
    assert _flags(inline) == set()


def test_name_based_state_effect_is_flagged():
    """A mutation routed through a lifecycle/service call (e.g. _lift_lockdown) is still a state effect."""
    namebased = (
        "import asyncio\n"
        "from disbot.runtime import tasks\n"
        "class Sec:\n"
        "    def start(self, gid, channel):\n"
        "        async def _hold_then_lift():\n"
        "            await asyncio.sleep(300)\n"
        "            await _lift_lockdown(gid, channel)\n"
        "        tasks.spawn('lock', _hold_then_lift())\n"
    )
    assert ("disbot/cogs/x.py", "_hold_then_lift") in _flags(namebased)


def test_allowlist_suppresses():
    exc = {"exceptions": [{"file": "disbot/cogs/x.py", "reason": "intentional"}]}
    assert _flags(_BUG, exceptions=exc) == set()


def test_allowlist_spawn_target_scoped():
    exc = {
        "exceptions": [
            {"file": "disbot/cogs/x.py", "spawn_target": "_other", "reason": "x"},
        ],
    }
    # The allowlist targets a different spawn_target → the real one is still flagged.
    assert ("disbot/cogs/x.py", "_auto_unlock") in _flags(_BUG, exceptions=exc)


def test_has_recovery_helper():
    assert cdr._has_recovery("upsert_lock(...)\nasync def on_ready(): await reconcile()") is True
    assert cdr._has_recovery("just some code with no persistence") is False
    # persist without reconcile → not recovered
    assert cdr._has_recovery("upsert_lock(...)") is False


def test_real_tree_is_clean():
    """The committed tree + allowlist must be 0 findings, so a NEW deferred lock without recovery reddens.

    If this fails: either a deferred one-shot Discord-state mutation was added without a persisted
    deadline + boot reconcile (add them — the proof_channel_cog #1728 pattern), or a new
    intentionally-process-local timer needs an allowlist entry with a reason.
    """
    findings = cdr.run_check()
    assert findings == [], "\n".join(f.display() for f in findings)
