"""Tests for scripts/check_audit_seam.py — the audit-seam coverage guard (CI-setup arc, item #5).

Covers the pure ``analyze()`` logic on injected synthetic sources (no disk, no live bot):

* it BITES on the #1728 bug shapes (bug #5 unaudited ``channel.edit``; bug #6 an unaudited write to
  an *auditable-class* db domain) — the Q-0120 "does the gate actually block?" meta-test;
* it stays quiet on the correct shapes (audited write+emit wrapper, delegated audit via a callee,
  a game write to a non-auditable domain, the ``self.add_item`` name collision, a message re-render);
* the allowlist suppresses a triaged finding;
* the small AST helpers (``_db_imports`` / ``_discord_mutation`` / ``build_db_write_helpers``) behave.

Plus a ground-truth check that the REAL tree is clean (every finding triaged/allowlisted) — so a new
unaudited mutation reddens this test, which is the whole point of shipping it warn-first.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SPEC = importlib.util.spec_from_file_location(
    "check_audit_seam",
    _REPO_ROOT / "scripts" / "check_audit_seam.py",
)
assert _SPEC and _SPEC.loader
cas = importlib.util.module_from_spec(_SPEC)
# Register before exec: the module's frozen dataclasses resolve string annotations against
# sys.modules at class-creation time (a `from __future__ import annotations` + importlib quirk).
sys.modules["check_audit_seam"] = cas
_SPEC.loader.exec_module(cas)


# ---------------------------------------------------------------------------
# Shared synthetic sources (a tiny world: a db layer, the audit primitive, wrappers)
# ---------------------------------------------------------------------------

# A utils/db module: set_* write (raw SQL), get_* read, and a thin wrapper.
_DB = '''
async def set_wordfilter_strict(gid, s):
    await pool.execute("UPDATE wordfilter SET strict=$1 WHERE gid=$2", s, gid)
async def get_wordfilter_strict(gid):
    return await pool.fetchval("SELECT strict FROM wordfilter WHERE gid=$1", gid)
async def set_counting_state(gid, n):
    await pool.execute("UPDATE counting SET n=$1 WHERE gid=$2", n, gid)
async def delete_for_guild(gid):
    await delete_by_ids(gid)          # wrapper -> writer via fixpoint
async def delete_by_ids(gid):
    await pool.execute("DELETE FROM wordfilter WHERE gid=$1", gid)
'''

# The audit primitive lives here.
_AUDIT = "async def emit_audit_action(**kw):\n    ...\n"

# An audited service wrapper: writes set_wordfilter_strict AND emits, in one body. This is what makes
# the wordfilter domain *auditable-class*.
_WRAPPER = '''
from utils import db
from services.audit_events import emit_audit_action
async def set_wordfilter_strict(gid, s, *, actor_id):
    await db.set_wordfilter_strict(gid, s)
    await emit_audit_action(mutation_id="x", subsystem="cleanup")
'''


def _analyze(extra: dict[str, str], exceptions: dict | None = None) -> set[tuple[str, str]]:
    """Analyze the shared world + ``extra`` sources; return the flagged (file, qualname) set."""
    sources = {
        "disbot/utils/db/wordfilter.py": _DB,
        "disbot/services/audit_events.py": _AUDIT,
        "disbot/services/prohibited_words_service.py": _WRAPPER,
        **extra,
    }
    return {(f.file, f.qualname) for f in cas.analyze(sources, exceptions or {})}


# ---------------------------------------------------------------------------
# The gate BITES (Q-0120 meta-test) — bug #5 and bug #6 shapes are flagged
# ---------------------------------------------------------------------------


def test_bug6_unaudited_write_to_auditable_domain_is_flagged():
    """A cog writing db.set_wordfilter_strict directly (no audit), when an audited wrapper for that
    same helper exists → the bug #6 bypass. MUST flag."""
    cog = (
        "from utils import db\n"
        "class CleanupCog:\n"
        "    async def toggle(self, gid, s):\n"
        "        await db.set_wordfilter_strict(gid, s)\n"
    )
    flagged = _analyze({"disbot/cogs/cleanup_cog.py": cog})
    assert ("disbot/cogs/cleanup_cog.py", "CleanupCog.toggle") in flagged


def test_bug5_unaudited_channel_edit_is_flagged():
    """A service calling channel.edit(slowmode_delay=...) with no audit — the raid-lockdown bypass
    (bug #5). MUST flag."""
    svc = (
        "class SecurityService:\n"
        "    async def apply_lockdown(self, channel):\n"
        '        await channel.edit(slowmode_delay=30, reason="raid")\n'
    )
    flagged = _analyze({"disbot/services/security_service.py": svc})
    assert ("disbot/services/security_service.py", "SecurityService.apply_lockdown") in flagged


def test_raw_sql_write_outside_utils_db_is_flagged():
    """A service running a raw INSERT/UPDATE/DELETE itself (not via utils.db) with no audit."""
    svc = (
        "class Svc:\n"
        "    async def wipe(self, conn, gid):\n"
        '        await conn.execute("DELETE FROM roles WHERE gid=$1", gid)\n'
    )
    flagged = _analyze({"disbot/services/svc.py": svc})
    assert ("disbot/services/svc.py", "Svc.wipe") in flagged


def test_member_ban_is_flagged():
    svc = (
        "class Mod:\n"
        "    async def do_ban(self, member):\n"
        '        await member.ban(reason="spam")\n'
    )
    flagged = _analyze({"disbot/services/mod.py": svc})
    assert ("disbot/services/mod.py", "Mod.do_ban") in flagged


# ---------------------------------------------------------------------------
# The gate stays QUIET on correct / non-auditable shapes
# ---------------------------------------------------------------------------


def test_audited_wrapper_is_clean():
    """The write+emit wrapper itself is not flagged (it audits in-body)."""
    flagged = _analyze({})
    assert ("disbot/services/prohibited_words_service.py", "set_wordfilter_strict") not in flagged


def test_game_write_to_non_auditable_domain_is_clean():
    """A db write whose domain has NO audited wrapper anywhere (counting/economy/games) is NOT a
    finding — the ~42% false-positive class the calibration warned about is scoped out."""
    cog = (
        "from utils import db\n"
        "class CountingCog:\n"
        "    async def save(self, gid, n):\n"
        "        await db.set_counting_state(gid, n)\n"
    )
    flagged = _analyze({"disbot/cogs/counting_cog.py": cog})
    assert ("disbot/cogs/counting_cog.py", "CountingCog.save") not in flagged


def test_delegated_audit_via_callee_is_clean():
    """A function that writes directly but delegates the emit to a callee is audit-reachable."""
    svc = (
        "from utils import db\n"
        "async def add_delegated_admin(gid, uid, *, actor_id):\n"
        "    await db.set_wordfilter_strict(gid, True)\n"
        "    await _emit(gid)\n"
        "async def _emit(gid):\n"
        "    from services.audit_events import emit_audit_action\n"
        '    await emit_audit_action(mutation_id="x", subsystem="setup")\n'
    )
    flagged = _analyze({"disbot/services/setup_session.py": svc})
    assert ("disbot/services/setup_session.py", "add_delegated_admin") not in flagged


def test_routing_through_audited_service_is_clean():
    """A cog that calls the audited service wrapper (not the db helper directly) is clean — it reaches
    emit_audit_action transitively through the wrapper."""
    cog = (
        "from services import prohibited_words_service as pw\n"
        "class CleanupCog:\n"
        "    async def toggle(self, gid, s):\n"
        "        await pw.set_wordfilter_strict(gid, s, actor_id=1)\n"
    )
    flagged = _analyze({"disbot/cogs/cleanup_cog.py": cog})
    assert ("disbot/cogs/cleanup_cog.py", "CleanupCog.toggle") not in flagged


def test_self_add_item_collision_is_clean():
    """`discord.ui.View.add_item` shares a name with the inventory db helper — a `self.add_item`
    call must NOT be read as a db write (its receiver is `self`, not a db alias)."""
    db_with_add = _DB + (
        "async def add_item(uid, item):\n"
        '    await pool.execute("INSERT INTO inventory VALUES ($1,$2)", uid, item)\n'
    )
    view = (
        "from utils import db\n"
        "class MyView:\n"
        "    def build(self):\n"
        "        self.add_item(SomeButton())\n"
    )
    sources = {
        "disbot/utils/db/wordfilter.py": db_with_add,
        "disbot/services/audit_events.py": _AUDIT,
        "disbot/views/my_view.py": view,
    }
    flagged = {(f.file, f.qualname) for f in cas.analyze(sources, {})}
    assert ("disbot/views/my_view.py", "MyView.build") not in flagged


def test_message_edit_embed_is_clean():
    """`X.edit(embed=...)` writes only message fields → a re-render, not a state mutation."""
    view = (
        "class Panel:\n"
        "    async def refresh(self):\n"
        "        await self.some_var.edit(embed=self.embed, view=self)\n"
    )
    flagged = _analyze({"disbot/views/panel.py": view})
    assert ("disbot/views/panel.py", "Panel.refresh") not in flagged


def test_message_receiver_delete_is_clean():
    """`parent_message.delete()` — a `*_message` receiver is a message op, not a channel delete."""
    view = (
        "class Panel:\n"
        "    async def close(self):\n"
        "        await self.parent_message.delete()\n"
    )
    flagged = _analyze({"disbot/views/panel.py": view})
    assert ("disbot/views/panel.py", "Panel.close") not in flagged


def test_channel_edit_name_is_flagged_not_a_message_edit():
    """`channel.edit(name=...)` is a state mutation (name is not a message kwarg)."""
    svc = (
        "class Svc:\n"
        "    async def rename(self, channel):\n"
        '        await channel.edit(name="x", reason="y")\n'
    )
    flagged = _analyze({"disbot/services/svc.py": svc})
    assert ("disbot/services/svc.py", "Svc.rename") in flagged


def test_utils_db_layer_is_never_flagged():
    """The utils/db raw-write primitive layer writes raw SQL by design — never a finding."""
    # _DB itself has raw writes; confirm none of its functions are flagged.
    flagged = _analyze({})
    assert not any(f.startswith("disbot/utils/db/") for f, _ in flagged)


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def test_allowlist_whole_file_suppresses():
    cog = (
        "from utils import db\n"
        "class CleanupCog:\n"
        "    async def toggle(self, gid, s):\n"
        "        await db.set_wordfilter_strict(gid, s)\n"
    )
    exc = {"exceptions": [{"file": "disbot/cogs/cleanup_cog.py", "reason": "test"}]}
    flagged = _analyze({"disbot/cogs/cleanup_cog.py": cog}, exceptions=exc)
    assert ("disbot/cogs/cleanup_cog.py", "CleanupCog.toggle") not in flagged


def test_allowlist_function_scoped_suppresses_only_that_function():
    cog = (
        "from utils import db\n"
        "class CleanupCog:\n"
        "    async def toggle(self, gid, s):\n"
        "        await db.set_wordfilter_strict(gid, s)\n"
        "    async def toggle2(self, gid, s):\n"
        "        await db.set_wordfilter_strict(gid, s)\n"
    )
    exc = {
        "exceptions": [
            {
                "file": "disbot/cogs/cleanup_cog.py",
                "function": "CleanupCog.toggle",
                "reason": "test",
            },
        ],
    }
    flagged = _analyze({"disbot/cogs/cleanup_cog.py": cog}, exceptions=exc)
    assert ("disbot/cogs/cleanup_cog.py", "CleanupCog.toggle") not in flagged
    assert ("disbot/cogs/cleanup_cog.py", "CleanupCog.toggle2") in flagged


# ---------------------------------------------------------------------------
# Unit-level helpers
# ---------------------------------------------------------------------------


def test_build_db_write_helpers_distinguishes_reads_and_wraps():
    helpers = cas.build_db_write_helpers({"disbot/utils/db/wordfilter.py": _DB})
    assert "set_wordfilter_strict" in helpers  # raw write
    assert "set_counting_state" in helpers  # raw write
    assert "delete_by_ids" in helpers  # raw write
    assert "delete_for_guild" in helpers  # wrapper -> writer via fixpoint
    assert "get_wordfilter_strict" not in helpers  # a read


def test_db_imports_recognizes_the_common_styles():
    import ast

    tree = ast.parse(
        "from utils import db\n"
        "from utils.db import roles\n"
        "from utils.db.settings import set_setting, get_setting\n"
        "import utils.db.games as games_db\n",
    )
    dbi = cas._db_imports(tree)
    assert "db" in dbi.aliases  # from utils import db
    assert "roles" in dbi.aliases  # from utils.db import roles (submodule)
    assert "games_db" in dbi.aliases  # import ... as
    assert "set_setting" in dbi.bare  # from utils.db.settings import ...
    assert "get_setting" in dbi.bare


def test_discord_mutation_detection():
    import ast

    def mut(expr: str):
        return cas._discord_mutation(ast.parse(expr, mode="eval").body)

    assert mut("member.ban(reason='x')") == "ban"
    assert mut("channel.edit(name='x')") == "edit"
    assert mut("member.add_roles(role)") == "add_roles"
    assert mut("self.message.edit(embed=e)") is None  # message re-render
    assert mut("m.edit(embed=e, view=v)") is None  # message-kwargs only
    assert mut("obj.set_state(1)") is None  # not a mutation attr


# ---------------------------------------------------------------------------
# Ground truth — the real tree is clean (every finding triaged/allowlisted)
# ---------------------------------------------------------------------------


def test_real_tree_is_clean():
    """The committed tree + allowlist must be 0 findings, so a NEW unaudited mutation reddens this.

    If this fails, either a real audit-seam bypass was introduced (route it through the audited
    *_mutation / lifecycle seam), or a new legitimately-non-auditable write needs an allowlist entry
    with a reason in architecture_rules/audit_seam_exceptions.yml.
    """
    findings = cas.run_check()
    assert findings == [], "\n".join(f.display() for f in findings)
