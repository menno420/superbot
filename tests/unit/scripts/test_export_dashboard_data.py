"""Tests for ``scripts/export_dashboard_data.py`` — the dashboard data exporter.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules, which are
not a package) so the test does not depend on ``sys.path`` layout. The exporter is
pure stdlib, so this runs in CI with no extra dependencies.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "export_dashboard_data.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("export_dashboard_data_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SAMPLE_REGISTRY = '''
from utils.ui_constants import ADMIN_COLOR

SUBSYSTEMS: dict[str, dict] = {
    "admin": {
        "display_name": "Administration",
        "description": "Cog management",
        "emoji": "X",
        "color": ADMIN_COLOR.value,
        "category": "admin",
        "visibility_tier": "administrator",
        "tags": ["admin", "cogs"],
        "entry_points": ["adminmenu"],
        "capabilities": ["admin.cog.load"],
    },
}
'''

SAMPLE_BUGS = """# Bug book

## BUG-0014 — `!coglist` infinite loop — FIXED

- **Symptom (owner-reported):** typing `!coglist`
  spammed the channel endlessly until restart.
- **Root cause:** something.

## BUG-0010 — something still broken — OPEN

- **Symptom:** it breaks.
"""


def test_parse_catalogue_extracts_literals_and_skips_color(mod):
    entries = mod.parse_catalogue(SAMPLE_REGISTRY)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["key"] == "admin"
    assert entry["display_name"] == "Administration"
    assert entry["tags"] == ["admin", "cogs"]
    assert entry["entry_points"] == ["adminmenu"]
    # The non-literal ``color`` field is skipped, not crashed on.
    assert "color" not in entry


def test_parse_catalogue_handles_source_without_registry(mod):
    assert mod.parse_catalogue("x = 1\n") == []


def test_parse_bugs_extracts_id_title_status_summary(mod):
    bugs = mod.parse_bugs(SAMPLE_BUGS)
    assert [b["id"] for b in bugs] == ["BUG-0014", "BUG-0010"]
    assert bugs[0]["status"] == "FIXED"
    assert bugs[1]["status"] == "OPEN"
    assert "infinite loop" in bugs[0]["title"]
    # Multi-line symptom is joined.
    assert "spammed the channel endlessly" in bugs[0]["summary"]


def test_parse_ideas_reads_title_status_date(mod, tmp_path):
    ideas_dir = tmp_path / "ideas"
    ideas_dir.mkdir()
    (ideas_dir / "README.md").write_text("# index\n", encoding="utf-8")
    (ideas_dir / "cool-thing-2026-06-16.md").write_text(
        "# Cool thing\n\n> **Status:** `ideas`\n\nThis is the idea body.\n",
        encoding="utf-8",
    )
    ideas = mod.parse_ideas(ideas_dir)
    assert len(ideas) == 1
    assert ideas[0]["title"] == "Cool thing"
    assert ideas[0]["date"] == "2026-06-16"
    assert ideas[0]["summary"] == "This is the idea body."


def test_build_data_against_real_repo_is_well_formed(mod):
    data = mod.build_data()
    assert set(data) >= {"meta", "catalogue", "ideas", "bugs", "updates", "env_usage"}
    assert data["meta"]["counts"]["functions"] == len(data["catalogue"])
    assert len(data["catalogue"]) >= 10
    keys = {e["key"] for e in data["catalogue"]}
    assert "admin" in keys
    for entry in data["catalogue"]:
        assert isinstance(entry["key"], str)


def test_build_data_includes_build_meta(mod):
    # The /status "deployed build" banner reads meta.build; in the real git repo
    # it resolves, and a non-repo path degrades to {} rather than raising.
    data = mod.build_data()
    build = data["meta"]["build"]
    assert isinstance(build, dict)
    if build:  # present when run inside the git checkout (always, in CI)
        assert set(build) == {"commit", "subject", "committed_at", "branch"}
        assert all(isinstance(v, str) and v for v in build.values())
    # A path with no git history must not crash the export.
    assert mod._git_meta(mod.Path("/nonexistent-not-a-repo")) == {}


def test_build_data_includes_env_usage_section(mod):
    data = mod.build_data()
    env_usage = data["env_usage"]
    assert data["meta"]["counts"]["env_vars"] == len(env_usage)
    assert len(env_usage) >= 20
    names = {r["name"] for r in env_usage}
    assert "DATABASE_URL" in names
    # The section is the scanner's shape (names + locations only, no values).
    for record in env_usage:
        assert set(record) == {"name", "required", "usage_count", "layers", "usages"}


def test_build_data_includes_cogs_section(mod):
    data = mod.build_data()
    cogs = data["cogs"]
    assert data["meta"]["counts"]["cogs"] == sum(1 for c in cogs if c.get("is_cog"))
    assert data["meta"]["counts"]["commands"] == sum(len(c["commands"]) for c in cogs)
    assert len(cogs) >= 20
    assert "EconomyCog" in {c["cog"] for c in cogs}
    for cog in cogs:
        for cmd in cog["commands"]:
            assert set(cmd) >= {"name", "type", "button_backed", "aliases"}
            assert cmd["type"] in {"prefix", "slash", "both"}


# ---------------------------------------------------------------------------
# S1 — bot changelog parser (docs/bot-changelog.md → site.json.bot_changelog)
# ---------------------------------------------------------------------------

SAMPLE_CHANGELOG = """# Bot changelog

## 2026-06-19 — New game: Blackjack (feature)

You can now play Blackjack against the bot.

## 2026-06-10 — Faster help menu (improvement)

The help menu opens faster now.

## 2026-05-01 — Untagged entry

No kind tag here.
"""


def test_parse_bot_changelog_extracts_date_title_kind_summary(mod):
    entries = mod.parse_bot_changelog(SAMPLE_CHANGELOG)
    assert [e["date"] for e in entries] == ["2026-06-19", "2026-06-10", "2026-05-01"]
    assert entries[0]["title"] == "New game: Blackjack"
    assert entries[0]["kind"] == "feature"
    assert "Blackjack against the bot" in entries[0]["summary"]
    assert entries[1]["kind"] == "improvement"
    # An entry with no kind tag → kind == "" (never fabricated), title intact.
    assert entries[2]["kind"] == ""
    assert entries[2]["title"] == "Untagged entry"


def test_parse_bot_changelog_empty_source(mod):
    assert mod.parse_bot_changelog("# Bot changelog\n\nNo entries yet.\n") == []


def test_build_data_includes_bot_changelog(mod):
    data = mod.build_data()
    assert "bot_changelog" in data
    assert data["meta"]["counts"]["bot_changelog"] == len(data["bot_changelog"])
    for entry in data["bot_changelog"]:
        assert set(entry) == {"date", "title", "kind", "summary"}
        assert entry["kind"] in {"", "feature", "fix", "improvement"}


# ---------------------------------------------------------------------------
# S1 — the public site.json subset (redaction by construction, plan §2.2 / §5)
# ---------------------------------------------------------------------------


def test_site_subset_toplevel_keys_are_exactly_the_whitelist(mod):
    subset = mod.build_site_subset(mod.build_data())
    # The hard guarantee: nothing but the whitelisted families, ever.
    assert set(subset) == set(mod.SITE_TOPLEVEL_KEYS)
    assert set(subset) == {"meta", "counts", "catalogue", "commands", "bot_changelog"}


def test_site_subset_omits_every_dev_only_family(mod):
    subset = mod.build_site_subset(mod.build_data())
    for forbidden in (
        "env_usage",
        "settings",
        "access",
        "reviews",
        "ideas",
        "bugs",
        "cogs",
        "synonyms",
    ):
        assert forbidden not in subset, f"{forbidden} leaked into site.json"


def test_site_subset_meta_carries_build_only_no_private_counts(mod):
    meta = mod.build_site_subset(mod.build_data())["meta"]
    # Only build provenance + the generation stamp — never the dashboard's full
    # meta.counts (which include server-revealing internals like env_vars).
    assert set(meta) <= {"generated_at", "build"}
    assert "counts" not in meta


def test_site_subset_counts_are_catalogue_only(mod):
    counts = mod.build_site_subset(mod.build_data())["counts"]
    # Catalogue totals ONLY — never server/user totals (plan §5 / layout note).
    assert set(counts) == {"commands", "features", "games"}
    for forbidden in ("guilds", "servers", "users", "members", "env_vars"):
        assert forbidden not in counts


def test_site_subset_commands_carry_no_per_guild_value(mod):
    subset = mod.build_site_subset(mod.build_data())
    assert subset["commands"], "expected a non-empty command reference"
    for cmd in subset["commands"]:
        assert set(cmd) == set(mod.SITE_COMMAND_FIELDS)
        assert set(cmd) == {
            "name",
            "aliases",
            "category",
            "cooldown",
            "permissions",
            "usage",
            # S1.1 enrichment fields (the interactive browser):
            "description",
            "use_cases",
            "examples",
            "status",
            "linked_ideas",
            "notes",
        }
        # cooldown is reserved (not statically resolvable) — None, never fabricated.
        assert cmd["cooldown"] is None


# ---------------------------------------------------------------------------
# S1.1 — per-command enrichment (description / examples / status / linked_ideas)
# ---------------------------------------------------------------------------


def test_command_description_first_paragraph_and_sphinx_strip(mod):
    doc = (
        "Open the access explorer for the invoker.\n"
        "It is read-only and ephemeral.\n\n"
        "PR E1 — implementation note that must NOT appear in the first paragraph.\n"
    )
    desc = mod._command_description(doc)
    assert desc == "Open the access explorer for the invoker. It is read-only and ephemeral."
    # Sphinx cross-reference roles are reduced to their human label.
    assert mod._command_description("Open :class:`AccessExplorerView` now.") == (
        "Open AccessExplorerView now."
    )
    # A docstring-less command yields None — never invented prose.
    assert mod._command_description("") is None
    assert mod._command_description("   \n  ") is None


def test_command_examples_only_backticked_bang_invocations(mod):
    doc = (
        "Sell raw resources for coins (e.g. `!sell diamond 5`).\n"
        "Also `!sellall` works. A bare !notanexample in prose is ignored.\n"
        "Duplicate `!sell diamond 5` is de-duplicated.\n"
    )
    examples = mod._command_examples(doc)
    assert examples == ["!sell diamond 5", "!sellall"]
    # No docstring → no fabricated examples.
    assert mod._command_examples("") == []


def test_subsystem_open_work_links_ideas_title_and_status_only(mod):
    catalogue = [{"key": "mining"}, {"key": "welcome"}, {"key": "admin"}]
    ideas = [
        {"file": "mining-roadmap-2026-06-16.md", "title": "Mining roadmap", "status": "ideas"},
        # historical/closed ideas must NOT count as open work.
        {"file": "old-mining-thing.md", "title": "Old mining", "status": "historical"},
        {"file": "welcome-feeds.md", "title": "Welcome feeds", "status": "planned"},
    ]
    bugs = [{"id": "BUG-1", "title": "admin panel crash", "status": "OPEN"}]
    work = mod._subsystem_open_work(ideas, bugs, catalogue)
    # mining: one OPEN idea linked (the historical one excluded), in-progress.
    assert work["mining"]["in_progress"] is True
    assert work["mining"]["ideas"] == [{"title": "Mining roadmap", "status": "ideas"}]
    # welcome: linked via a 'planned' idea.
    assert work["welcome"]["in_progress"] is True
    # admin: no idea, but an OPEN bug → in-progress with empty linked-ideas list.
    assert work["admin"]["in_progress"] is True
    assert work["admin"]["ideas"] == []
    # A subsystem with no open work is absent from the map.
    assert "general" not in work
    # Redaction: linked ideas carry ONLY title + status — never the raw body/file.
    for entry in work.values():
        for idea in entry["ideas"]:
            assert set(idea) == {"title", "status"}


def test_subsystem_open_work_ignores_closed_bug(mod):
    catalogue = [{"key": "counting"}]
    work = mod._subsystem_open_work(
        ideas=[],
        bugs=[{"id": "BUG-1", "title": "counting bug", "status": "FIXED"}],
        catalogue=catalogue,
    )
    assert work == {}  # a FIXED bug is not open work


def test_site_subset_command_enrichment_shapes_are_honest(mod):
    subset = mod.build_site_subset(mod.build_data())
    cmds = subset["commands"]
    assert cmds
    for cmd in cmds:
        # use_cases / notes are reserved null (no honest static source); never faked.
        assert cmd["use_cases"] is None
        assert cmd["notes"] is None
        # status is one of the two honest maturity tokens.
        assert cmd["status"] in {
            mod.COMMAND_STATUS_FINISHED,
            mod.COMMAND_STATUS_IN_PROGRESS,
        }
        # examples + linked_ideas are always lists.
        assert isinstance(cmd["examples"], list)
        assert isinstance(cmd["linked_ideas"], list)
        # every example is a backticked-style bang invocation lifted verbatim.
        assert all(e.startswith("!") for e in cmd["examples"])
        # description is either None or a non-empty string.
        assert cmd["description"] is None or (
            isinstance(cmd["description"], str) and cmd["description"]
        )
        # linked ideas carry title + status only (redaction).
        for idea in cmd["linked_ideas"]:
            assert set(idea) == {"title", "status"}
    # The real repo has at least some enrichment (proves the wiring is live, not inert).
    assert any(c["examples"] for c in cmds), "expected some commands to expose examples"
    assert any(c["description"] for c in cmds), "expected some commands to have a description"
    assert any(
        c["status"] == mod.COMMAND_STATUS_IN_PROGRESS for c in cmds
    ), "expected some commands flagged in-progress by linked open work"


def test_build_site_subset_degrades_without_repo_docstrings(mod, tmp_path):
    # With a repo_root that has no disbot/ tree, the docstring map is empty — the
    # subset still builds, every command just has no description/examples.
    subset = mod.build_site_subset(mod.build_data(), repo_root=tmp_path)
    for cmd in subset["commands"]:
        assert cmd["description"] is None
        assert cmd["examples"] == []
    # The subset is still structurally valid (top-level keys intact).
    assert set(subset) == set(mod.SITE_TOPLEVEL_KEYS)


def test_site_subset_catalogue_is_metadata_only(mod):
    subset = mod.build_site_subset(mod.build_data())
    assert subset["catalogue"], "expected a non-empty catalogue"
    for entry in subset["catalogue"]:
        # Public metadata only — internal wiring fields must not be present.
        for forbidden in ("capabilities", "entry_points", "visibility_mode"):
            assert forbidden not in entry
        assert "badges" in entry
        assert isinstance(entry["is_game"], bool)


def test_site_subset_counts_match_lengths(mod):
    subset = mod.build_site_subset(mod.build_data())
    assert subset["counts"]["commands"] == len(subset["commands"])
    assert subset["counts"]["features"] == len(subset["catalogue"])
    assert subset["counts"]["games"] == sum(
        1 for e in subset["catalogue"] if e.get("is_game")
    )


def test_build_site_subset_raises_if_a_disallowed_key_is_added(mod):
    # The producer's own defensive guard: a future edit that adds an un-whitelisted
    # key must fail in the producer, not silently ship. We simulate by monkeypatching
    # SITE_TOPLEVEL_KEYS to a stricter set so the real subset trips it.
    original = mod.SITE_TOPLEVEL_KEYS
    try:
        mod.SITE_TOPLEVEL_KEYS = frozenset({"meta"})  # type: ignore[misc]
        with pytest.raises(ValueError, match="disallowed top-level keys"):
            mod.build_site_subset(mod.build_data())
    finally:
        mod.SITE_TOPLEVEL_KEYS = original  # type: ignore[misc]


def test_committed_site_json_matches_a_fresh_build(mod):
    # The committed botsite/data/site.json must be regenerable-identical (modulo
    # the volatile meta) to a fresh subset — the freshness guarantee S1 registers.
    import json

    committed = json.loads(mod.SITE_OUTPUT_FILE.read_text(encoding="utf-8"))
    fresh = mod.build_site_subset(mod.build_data())
    # Compare the stable families; meta carries the volatile build SHA/timestamp.
    for family in ("counts", "catalogue", "commands", "bot_changelog"):
        assert committed[family] == fresh[family], f"{family} drifted — re-export"


def test_cli_targets_site_writes_only_site_json(mod, tmp_path):
    dash = tmp_path / "dashboard.json"
    site = tmp_path / "site.json"
    rc = mod.main(
        [
            "--targets",
            "site",
            "--output",
            str(dash),
            "--site-output",
            str(site),
        ],
    )
    assert rc == 0
    assert site.exists()
    assert not dash.exists()  # --targets site must not write the dashboard payload


def test_cli_targets_both_writes_both(mod, tmp_path):
    dash = tmp_path / "dashboard.json"
    site = tmp_path / "site.json"
    rc = mod.main(["--output", str(dash), "--site-output", str(site)])
    assert rc == 0
    assert dash.exists() and site.exists()
    import json

    site_data = json.loads(site.read_text(encoding="utf-8"))
    assert set(site_data) == set(mod.SITE_TOPLEVEL_KEYS)
