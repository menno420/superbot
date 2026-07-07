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


SAMPLE_REGISTRY = """
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
"""

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
        # `branch` is deliberately excluded — transient generator-host junk + a conflict source
        # (the #1261 root cause). See _git_meta.
        assert set(build) == {"commit", "subject", "committed_at"}
        assert all(isinstance(v, str) and v for v in build.values())
    # A path with no git history must not crash the export.
    assert mod._git_meta(mod.Path("/nonexistent-not-a-repo")) == {}


def test_generated_at_is_deterministic_not_wall_clock(mod, monkeypatch):
    # `generated_at` must be the latest-commit time, NOT wall-clock — so two regenerations at the
    # same commit are byte-identical. A wall-clock value churned a refresh PR every run and
    # guaranteed a merge conflict whenever two branches regenerated the file (#1261 root cause).
    #
    # HERMETIC (BUG-0024): pin `_git_meta` instead of letting `build_data` shell out to real `git`.
    # The production `_git_meta` runs git with `timeout=5, check=True`; under `pytest -n auto` load
    # those calls can time out, returning {} so `generated_at` falls back to wall-clock — which made
    # this assertion flaky (the BUG-0021 real-clock class). Pinning the commit context exercises the
    # determinism logic deterministically (the git-absent fallback is covered by the test below).
    fixed_build = {
        "commit": "abc1234",
        "subject": "pinned commit for a hermetic test",
        "committed_at": "2026-06-22T00:00:00Z",
    }
    monkeypatch.setattr(mod, "_git_meta", lambda repo_root: dict(fixed_build))
    first = mod.build_data()["meta"]
    second = mod.build_data()["meta"]
    assert (
        first["generated_at"] == second["generated_at"]
    ), "generated_at changed between runs at the same commit (not deterministic)"
    # generated_at anchors to the commit's committed_at — never wall-clock when a build is present.
    assert first["generated_at"] == fixed_build["committed_at"]
    assert second["build"] == fixed_build


def test_generated_at_falls_back_to_wall_clock_when_git_unavailable(mod, monkeypatch):
    # When git is unavailable (`_git_meta` -> {}), `build` is empty and `generated_at` degrades to a
    # wall-clock ISO timestamp rather than crashing. Guards the intentional fallback branch.
    monkeypatch.setattr(mod, "_git_meta", lambda repo_root: {})
    meta = mod.build_data()["meta"]
    assert meta["build"] == {}
    # An ISO-8601 "...Z" wall-clock string (parses, ends in Z).
    assert meta["generated_at"].endswith("Z")
    import datetime as _dt

    _dt.datetime.fromisoformat(meta["generated_at"].replace("Z", "+00:00"))



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


def test_site_field_contract_covers_every_public_family(mod):
    # The within-family redaction contract must pin a field set for every top-level
    # public family (so no family escapes the leaf-level guard), plus the nested
    # meta.build dict. A new family added to SITE_TOPLEVEL_KEYS without a contract
    # entry trips this — the field guard would silently skip it otherwise.
    paths = set(mod.SITE_FIELD_CONTRACT)
    assert set(mod.SITE_TOPLEVEL_KEYS) <= paths
    assert "meta.build" in paths


def test_site_field_contract_matches_the_live_build(mod):
    # The pinned contract must be a *superset* of what the producer actually emits —
    # i.e. the producer never emits a field the contract hasn't vetted as public. This
    # is the test that forces a conscious contract bump before a new field can ship.
    subset = mod.build_site_subset(mod.build_data())

    def leaves(value):
        records = value if isinstance(value, list) else [value]
        return {k for r in records if isinstance(r, dict) for k in r}

    assert leaves(subset["meta"]) <= set(mod.SITE_META_FIELDS)
    assert leaves(subset["meta"]["build"]) <= set(mod.SITE_META_BUILD_FIELDS)
    assert leaves(subset["counts"]) <= set(mod.SITE_COUNTS_FIELDS)
    assert leaves(subset["catalogue"]) <= set(mod.SITE_CATALOGUE_FIELDS)
    assert leaves(subset["commands"]) <= set(mod.SITE_COMMAND_FIELDS)
    assert leaves(subset["bot_changelog"]) <= set(mod.SITE_CHANGELOG_FIELDS)


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
    assert (
        desc
        == "Open the access explorer for the invoker. It is read-only and ephemeral."
    )
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
        {
            "file": "mining-roadmap-2026-06-16.md",
            "title": "Mining roadmap",
            "status": "ideas",
        },
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


def test_subsystem_tags_reads_header_only(mod):
    # A real tag in the front-matter blockquote is read; a `**Subsystem:**` *example*
    # below the first `## ` / in a code fence is NOT (the proposal that documents the tag
    # would otherwise self-tag every subsystem it names).
    tagged = (
        "# Title\n\n> **Status:** `ideas`\n> **Subsystem:** economy, mining\n\n"
        "## Body\n\n> **Subsystem:** welcome  <- an example, must be ignored\n"
        "```markdown\n> **Subsystem:** admin\n```\n"
    )
    assert mod._subsystem_tags(tagged) == ["economy", "mining"]
    # `none` / `-` sentinel → [] ("tagged, links to nothing").
    assert mod._subsystem_tags("# T\n\n> **Subsystem:** none\n\n## B\n") == []
    # `**Area:**` is an accepted alias.
    assert mod._subsystem_tags("# T\n\n> **Area:** rps_tournament\n\n## B\n") == [
        "rps_tournament",
    ]
    # Absent tag → None (caller falls back to the slug heuristic).
    assert mod._subsystem_tags("# T\n\n> **Status:** `ideas`\n\n## B\n") is None


def test_subsystem_open_work_prefers_explicit_tag(mod):
    catalogue = [{"key": "chain"}, {"key": "economy"}]
    ideas = [
        # Slug says "chain" but the explicit `none` tag wins → links to nothing (the
        # executor-self-chaining false-positive this mechanism exists to kill).
        {
            "file": "executor-chain-trigger.md",
            "title": "Executor self-chaining",
            "status": "ideas",
            "subsystems": [],
        },
        # Explicit tag links to `economy` even though the slug has no economy token.
        {
            "file": "shop-revamp-2026-06-19.md",
            "title": "Shop revamp",
            "status": "ideas",
            "subsystems": ["economy"],
        },
        # An unknown tag key matches no real subsystem (fail-safe).
        {
            "file": "misc-2026-06-19.md",
            "title": "Misc",
            "status": "ideas",
            "subsystems": ["not_a_real_subsystem"],
        },
    ]
    work = mod._subsystem_open_work(ideas, bugs=[], catalogue=catalogue)
    assert "chain" not in work  # the none-tagged idea linked nothing
    assert work["economy"]["ideas"] == [{"title": "Shop revamp", "status": "ideas"}]


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
    assert any(
        c["description"] for c in cmds
    ), "expected some commands to have a description"
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


# Command fields derived from docs/ideas/ + the bug book — both churn far more
# often than site.json is regenerated, so they are excluded from the *hard*
# equality below (their structural identity is covered warn-only by
# check_generated_artifacts_fresh.py instead — BUG-0018 root-fix, recommendation (a)).
_VOLATILE_COMMAND_FIELDS = ("linked_ideas", "status")


def _stable_commands(commands: list[dict]) -> list[dict]:
    """A command list with the high-churn idea/bug-derived fields stripped."""
    return [
        {k: v for k, v in cmd.items() if k not in _VOLATILE_COMMAND_FIELDS}
        for cmd in commands
    ]


def test_committed_site_json_matches_a_fresh_build(mod):
    # The committed botsite/data/site.json must be regenerable-identical (modulo
    # the volatile meta) to a fresh subset — the freshness guarantee S1 registers.
    import json

    committed = json.loads(mod.SITE_OUTPUT_FILE.read_text(encoding="utf-8"))
    fresh = mod.build_site_subset(mod.build_data())
    # Compare the stable families; meta carries the volatile build SHA/timestamp.
    for family in ("counts", "catalogue", "bot_changelog"):
        assert committed[family] == fresh[family], f"{family} drifted — re-export"
    # commands: pin only the stable fields. linked_ideas/status are idea-derived
    # (BUG-0018) — re-exporting on every idea-doc PR is the trap this avoids; the
    # freshness umbrella covers their identity warn-only.
    assert _stable_commands(committed["commands"]) == _stable_commands(
        fresh["commands"],
    ), "commands drifted (stable fields) — re-export"


def test_cli_targets_site_writes_only_site_json(mod, tmp_path):
    dash = tmp_path / "dashboard.json"
    site = tmp_path / "site.json"
    data_js = tmp_path / "data.js"
    console = tmp_path / "console.json"
    rc = mod.main(
        [
            "--targets",
            "site",
            "--output",
            str(dash),
            "--site-output",
            str(site),
            "--data-js-output",
            str(data_js),
            "--console-output",
            str(console),
        ],
    )
    assert rc == 0
    assert site.exists()
    assert (
        data_js.exists()
    )  # the SPA layer is written alongside, to the redirected path
    assert not dash.exists()  # --targets site must not write the dashboard payload
    assert not console.exists()  # --targets site must not write the console feed


def test_cli_targets_both_writes_all_three(mod, tmp_path):
    dash = tmp_path / "dashboard.json"
    site = tmp_path / "site.json"
    data_js = tmp_path / "data.js"
    console = tmp_path / "console.json"
    rc = mod.main(
        [
            "--output",
            str(dash),
            "--site-output",
            str(site),
            "--data-js-output",
            str(data_js),
            "--console-output",
            str(console),
        ],
    )
    assert rc == 0
    assert dash.exists() and site.exists() and console.exists()
    import json

    site_data = json.loads(site.read_text(encoding="utf-8"))
    assert set(site_data) == set(mod.SITE_TOPLEVEL_KEYS)
    console_data = json.loads(console.read_text(encoding="utf-8"))
    assert set(console_data) == set(mod.CONSOLE_TOPLEVEL_KEYS)


# --- the program-console feed (console.json) --------------------------------


def test_console_subset_whitelist_and_shapes(mod):
    subset = mod.build_console_subset(mod.build_data())
    # Redaction by construction: exactly the whitelisted families, nothing else.
    assert set(subset) == set(mod.CONSOLE_TOPLEVEL_KEYS)
    # The dev-only value families physically cannot appear.
    assert not ({"env_usage", "settings", "access", "reviews", "cogs"} & set(subset))
    for entry in subset["sessions"]:
        assert set(entry) == set(mod.CONSOLE_SESSION_FIELDS)
    assert {"total", "by_status"} <= set(subset["ideas"])
    assert {"total", "by_status", "open"} <= set(subset["bugs"])
    for bug in subset["bugs"]["open"]:
        # Titles + ids only — never full bug bodies on the console feed.
        assert set(bug) == {"id", "title", "status"}
    assert len(subset["bugs"]["open"]) <= 10


def test_cli_targets_console_writes_only_console(mod, tmp_path):
    dash = tmp_path / "dashboard.json"
    site = tmp_path / "site.json"
    console = tmp_path / "console.json"
    rc = mod.main(
        [
            "--targets",
            "console",
            "--output",
            str(dash),
            "--site-output",
            str(site),
            "--data-js-output",
            str(tmp_path / "data.js"),
            "--console-output",
            str(console),
        ],
    )
    assert rc == 0
    assert console.exists()
    assert not dash.exists() and not site.exists()


def test_cli_does_not_clobber_tracked_data_js_when_redirected(mod, tmp_path):
    """BUG-0022 guard: driving ``main()`` with redirected outputs must NOT touch the
    real tracked ``botsite/site/data.js`` — the live-HEAD build sha would desync it
    from the committed site.json and redden botsite-tests for an unrelated commit.
    """
    tracked = mod.DATA_JS_OUTPUT_FILE
    before = tracked.read_text(encoding="utf-8") if tracked.exists() else None
    rc = mod.main(
        [
            "--targets",
            "site",
            "--output",
            str(tmp_path / "dashboard.json"),
            "--site-output",
            str(tmp_path / "site.json"),
            "--data-js-output",
            str(tmp_path / "data.js"),
        ],
    )
    assert rc == 0
    after = tracked.read_text(encoding="utf-8") if tracked.exists() else None
    assert (
        after == before
    ), "main() with redirected outputs must not rewrite the tracked data.js"
