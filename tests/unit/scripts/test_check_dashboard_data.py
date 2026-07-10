"""Tests for ``scripts/check_dashboard_data.py`` — the dashboard export guard.

Loaded via ``importlib`` (the repo convention for ``scripts/`` modules). Pure
stdlib, so it runs in CI with no extra dependencies — including the live guard
that validates the freshly-built export.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_dashboard_data.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("check_dashboard_data_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# cog -> subsystem resolution
# ---------------------------------------------------------------------------


def test_cog_subsystem_resolution_flags_unregistered_real_cog(mod):
    data = {
        "catalogue": [{"key": "economy"}],
        "cogs": [
            {"cog": "EconomyCog", "is_cog": True, "subsystem": "economy", "file": "a"},
            {"cog": "MysteryCog", "is_cog": True, "subsystem": "mystery", "file": "b"},
        ],
    }
    issues = mod.check_cog_subsystem_resolution(data)
    assert [i.code for i in issues] == ["cog_subsystem_unresolved"]
    assert "MysteryCog" in issues[0].message
    assert issues[0].severity == "error"


def test_cog_subsystem_resolution_allows_allowlist_and_modules(mod):
    data = {
        "catalogue": [{"key": "economy"}],
        # HermesCog is allow-listed (no own registry entry); the module is is_cog=False.
        "cogs": [
            {"cog": "HermesCog", "is_cog": True, "subsystem": "hermes", "file": "h"},
            {"cog": "(bot1.py)", "is_cog": False, "subsystem": "", "file": "b"},
        ],
    }
    assert mod.check_cog_subsystem_resolution(data) == []


# ---------------------------------------------------------------------------
# count integrity
# ---------------------------------------------------------------------------


def _count_consistent_data():
    return {
        "meta": {
            "counts": {
                "cogs": 1,
                "commands": 2,
                "synonyms": 1,
                "ideas": 0,
                "bugs": 0,
                "env_vars": 0,
                "setting_domains": 0,
                "setting_keys": 0,
                "visible_subsystems": 1,
            },
        },
        "cogs": [{"is_cog": True, "commands": [{}, {}]}],
        "synonyms": [{"synonyms": ["a"]}],
        "ideas": [],
        "bugs": [],
        "env_usage": [],
        "settings": [],
        "access": {"total_visible": 1},
    }


def test_count_integrity_passes_when_consistent(mod):
    assert mod.check_count_integrity(_count_consistent_data()) == []


def test_count_integrity_flags_mismatch_and_missing(mod):
    data = _count_consistent_data()
    data["meta"]["counts"]["commands"] = 99  # wrong
    del data["meta"]["counts"]["synonyms"]  # missing
    issues = mod.check_count_integrity(data)
    codes = {i.code for i in issues}
    assert "count_mismatch" in codes
    assert "count_missing" in codes
    mismatch = next(i for i in issues if i.code == "count_mismatch")
    assert mismatch.severity == "error"


# ---------------------------------------------------------------------------
# required fields
# ---------------------------------------------------------------------------


def test_required_fields_flags_each_class(mod):
    data = {
        "cogs": [
            {
                "cog": "X",
                "file": "",  # missing file
                "commands": [
                    {"name": "ok", "type": "prefix"},
                    {"name": "", "type": "weird"},  # missing name + bad type
                ],
            },
        ],
        "catalogue": [{"key": ""}],  # missing key
    }
    codes = {i.code for i in mod.check_required_fields(data)}
    assert codes == {
        "cog_missing_file",
        "command_missing_name",
        "command_bad_type",
        "catalogue_missing_key",
    }


# ---------------------------------------------------------------------------
# live guard — the in-CI value: a freshly-built export must be clean
# ---------------------------------------------------------------------------


def test_live_export_has_no_integrity_errors(mod):
    data = mod._build_fresh()
    errors = [i for i in mod.validate(data) if i.severity == "error"]
    assert errors == [], f"dashboard export has integrity errors: {errors}"


def test_main_fresh_exits_zero(mod):
    assert mod.main(["--fresh"]) == 0


# ---------------------------------------------------------------------------
# structural-drift reporter (--drift)
# ---------------------------------------------------------------------------


def _drift_payload(env_names, setting_keys, command_names):
    """Minimal payload carrying just the surfaces the drift report inspects."""
    return {
        "cogs": [
            {
                "cog": "X",
                "is_cog": True,
                "commands": [{"name": n} for n in command_names],
            },
        ],
        "env_usage": [{"name": n} for n in env_names],
        "settings": [{"domain": "d", "keys": [{"key": k} for k in setting_keys]}],
        "catalogue": [{"key": "economy"}],
        "synonyms": [{"canonical": "ban"}],
    }


def test_structural_drift_clean_when_identical(mod):
    payload = _drift_payload(["A_TOKEN"], ["k1"], ["ping"])
    assert mod.check_structural_drift(payload, payload) == []


def test_structural_drift_reports_added_and_removed(mod):
    committed = _drift_payload(["A_TOKEN"], ["k1"], ["ping"])
    # Fresh build gained an env var + a setting key + a command, and a stale
    # env var that no longer exists in source was dropped.
    fresh = _drift_payload(["B_TOKEN"], ["k1", "k2"], ["ping", "pong"])
    issues = mod.check_structural_drift(committed, fresh)
    # Every drift finding is a non-blocking warning, never an error.
    assert issues, "expected drift findings"
    assert all(i.severity == "warning" for i in issues)
    codes = {i.code for i in issues}
    assert "structural_drift_added" in codes  # B_TOKEN / k2 / pong are new
    assert "structural_drift_removed" in codes  # A_TOKEN was dropped
    # The added env var is named in a message so the report is actionable.
    assert any("B_TOKEN" in i.message for i in issues)


def test_drift_findings_are_only_warnings_against_live(mod):
    # The whole point: drift between the committed file and a fresh build must
    # never produce an error (it would gate CI on every parallel-session churn).
    committed = mod._build_fresh()  # stand-in committed payload
    issues = mod.check_structural_drift(committed, mod._build_fresh())
    assert all(i.severity == "warning" for i in issues)


def test_main_drift_exits_zero(mod):
    # --drift reports warnings but never fails the run.
    assert mod.main(["--drift"]) == 0


# ---------------------------------------------------------------------------
# site.json subset guard (--site) — the redaction whitelist (plan §5 / §2.2)
# ---------------------------------------------------------------------------


def test_site_subset_clean_when_whitelisted(mod):
    clean = {
        "meta": {},
        "counts": {"commands": 1, "features": 0, "games": 0},
        "catalogue": [],
        "commands": [{"name": "ping"}],
        "bot_changelog": [],
    }
    assert mod.check_site_subset(clean) == []


def test_site_subset_fails_closed_on_unwhitelisted_key(mod):
    # The leak class: a non-public family appearing at the top level is an ERROR.
    forged = {
        "meta": {},
        "counts": {},
        "catalogue": [],
        "commands": [],
        "bot_changelog": [],
        "env_usage": ["SECRET_TOKEN"],  # must never reach the public site
    }
    issues = mod.check_site_subset(forged)
    assert [i.code for i in issues] == ["site_key_not_whitelisted"]
    assert issues[0].severity == "error"
    assert "env_usage" in issues[0].message


def test_site_subset_flags_count_mismatch(mod):
    forged = {
        "meta": {},
        "counts": {"commands": 99},  # wrong
        "catalogue": [],
        "commands": [{"name": "ping"}],
        "bot_changelog": [],
    }
    issues = mod.check_site_subset(forged)
    assert any(i.code == "site_count_mismatch" and i.severity == "error" for i in issues)


def test_site_subset_fails_closed_on_unwhitelisted_command_field(mod):
    # The S1.1 per-command leak class: a command field outside SITE_COMMAND_FIELDS is
    # an ERROR (it could be a per-guild value or a dev-only datum sneaking onto the
    # public command surface).
    forged = {
        "meta": {},
        "counts": {"commands": 1, "features": 0, "games": 0},
        "catalogue": [],
        "commands": [{"name": "ping", "guild_override_value": "leak"}],
        "bot_changelog": [],
    }
    issues = mod.check_site_subset(forged)
    assert any(
        i.code == "site_field_not_whitelisted" and i.severity == "error"
        for i in issues
    )
    field_issue = next(i for i in issues if i.code == "site_field_not_whitelisted")
    assert "guild_override_value" in field_issue.message
    assert "commands" in field_issue.message


def test_site_subset_fails_closed_on_unwhitelisted_catalogue_field(mod):
    # The within-family leak class beyond commands: a NEW field on an already-allowed
    # family (catalogue) must fail closed, not ride the family whitelist silently.
    forged = {
        "meta": {},
        "counts": {"commands": 0, "features": 1, "games": 0},
        "catalogue": [
            {"key": "fishing", "display_name": "Fishing", "internal_owner_id": 42},
        ],
        "commands": [],
        "bot_changelog": [],
    }
    issues = mod.check_site_subset(forged)
    field_issue = next(
        (
            i
            for i in issues
            if i.code == "site_field_not_whitelisted" and "catalogue" in i.message
        ),
        None,
    )
    assert field_issue is not None and field_issue.severity == "error"
    assert "internal_owner_id" in field_issue.message


def test_site_subset_fails_closed_on_unwhitelisted_nested_meta_build_field(mod):
    # Nested dicts are pinned per level: a stray field inside meta.build (build
    # provenance) must also fail closed.
    forged = {
        "meta": {"generated_at": "", "build": {"commit": "abc", "secret_token": "x"}},
        "counts": {},
        "catalogue": [],
        "commands": [],
        "bot_changelog": [],
    }
    issues = mod.check_site_subset(forged)
    field_issue = next(
        (
            i
            for i in issues
            if i.code == "site_field_not_whitelisted" and "meta.build" in i.message
        ),
        None,
    )
    assert field_issue is not None and field_issue.severity == "error"
    assert "secret_token" in field_issue.message


def test_site_subset_fails_closed_on_unwhitelisted_changelog_field(mod):
    forged = {
        "meta": {},
        "counts": {},
        "catalogue": [],
        "commands": [],
        "bot_changelog": [{"date": "2026-06-21", "title": "x", "raw_session_id": "z"}],
    }
    issues = mod.check_site_subset(forged)
    assert any(
        i.code == "site_field_not_whitelisted"
        and "bot_changelog" in i.message
        and "raw_session_id" in i.message
        for i in issues
    )


def test_site_subset_enriched_command_fields_pass(mod):
    # The full S1.1-enriched command shape must pass the per-command whitelist.
    enriched = {
        "meta": {},
        "counts": {"commands": 1, "features": 0, "games": 0},
        "catalogue": [],
        "commands": [
            {
                "name": "ping",
                "aliases": [],
                "category": "utility",
                "cooldown": None,
                "permissions": "user",
                "usage": "Ping the bot.",
                "description": "Report the bot's WebSocket latency.",
                "use_cases": None,
                "examples": ["!ping"],
                "status": "finished",
                "linked_ideas": [],
                "notes": None,
            },
        ],
        "bot_changelog": [],
    }
    assert mod.check_site_subset(enriched) == []


def test_live_site_subset_is_clean(mod):
    # The freshly-built subset must pass its own whitelist + count guard.
    fresh = mod._export_module().build_site_subset(mod._build_fresh())
    errors = [i for i in mod.check_site_subset(fresh) if i.severity == "error"]
    assert errors == [], f"fresh site.json subset has errors: {errors}"


def test_committed_site_json_passes_guard(mod):
    # The committed botsite/data/site.json must pass the guard as shipped.
    errors = [i for i in mod.check_site_subset() if i.severity == "error"]
    assert errors == [], f"committed site.json has errors: {errors}"


def test_main_site_exits_zero(mod):
    assert mod.main(["--site"]) == 0


# ---------------------------------------------------------------------------
# console feed shape contract (botsite/data/console_data_contract.json)
# ---------------------------------------------------------------------------


def _codes(issues):
    return [i.code for i in issues]


@pytest.fixture(scope="module")
def committed_console(mod):
    import json

    return json.loads(
        (mod.REPO_ROOT / "botsite" / "data" / "console.json").read_text(
            encoding="utf-8",
        ),
    )


def _clone(payload):
    import json

    return json.loads(json.dumps(payload))


def test_committed_console_json_passes_contract(mod):
    # THE cross-repo guard: the committed console.json (consumed by superbot's
    # botsite console AND the websites repo's dashboard /console over raw
    # GitHub) must match the committed, versioned contract as shipped.
    errors = [i for i in mod.check_console_subset() if i.severity == "error"]
    assert errors == [], f"committed console.json breaks its contract: {errors}"


def test_fresh_console_subset_passes_contract(mod):
    export = mod._export_module()
    fresh = export.build_console_subset(mod._build_fresh())
    errors = [i for i in mod.check_console_subset(fresh) if i.severity == "error"]
    assert errors == [], f"fresh console subset breaks the contract: {errors}"


def test_console_contract_matches_producer_constants(mod):
    # The contract file is the cross-repo source of truth; the producer constants
    # must match it exactly (changing one without the other = CI-red drift).
    contract = mod.load_console_contract()
    export = mod._export_module()
    assert contract["version"] == export.CONSOLE_SCHEMA_VERSION
    assert set(contract["top_level"]) == set(export.CONSOLE_TOPLEVEL_KEYS)
    assert set(contract["session"]) == set(export.CONSOLE_SESSION_FIELDS)
    assert set(contract["telemetry"]) == set(export.CONSOLE_TELEMETRY_FIELDS)
    assert set(contract["telemetry_outcome"]) == set(export.TELEMETRY_OUTCOME_FIELDS)


def test_console_fails_closed_on_uncontracted_family(mod, committed_console):
    bad = _clone(committed_console)
    bad["secret_family"] = []
    assert "console_key_not_in_contract" in _codes(mod.check_console_subset(bad))


def test_console_fails_closed_on_missing_family(mod, committed_console):
    # The consumer-blanking class (BUG-0022): a dropped family is an ERROR, not
    # a silent shrink — the websites dashboard renders this feed.
    bad = {k: v for k, v in _clone(committed_console).items() if k != "telemetry"}
    assert "console_family_missing" in _codes(mod.check_console_subset(bad))


def test_console_fails_closed_on_schema_version_mismatch(mod, committed_console):
    bad = _clone(committed_console)
    bad["meta"]["schema_version"] = 999
    assert "console_schema_version_mismatch" in _codes(mod.check_console_subset(bad))


def test_console_fails_closed_on_uncontracted_session_field(mod, committed_console):
    bad = _clone(committed_console)
    bad["sessions"][0]["guild_id"] = 123  # the per-guild-leak class
    assert "console_field_not_in_contract" in _codes(mod.check_console_subset(bad))


def test_console_fails_closed_on_dropped_guaranteed_field(mod, committed_console):
    bad = _clone(committed_console)
    del bad["sessions"][0]["title"]
    assert "console_field_missing" in _codes(mod.check_console_subset(bad))


def test_console_fails_closed_on_uncontracted_telemetry_outcome_field(
    mod,
    committed_console,
):
    bad = _clone(committed_console)
    assert bad["telemetry"], "committed telemetry feed unexpectedly empty"
    bad["telemetry"][0]["outcome"]["surprise"] = True
    assert "console_field_not_in_contract" in _codes(mod.check_console_subset(bad))


def test_console_contract_producer_drift_is_flagged(mod, committed_console, tmp_path):
    import json

    contract = mod.load_console_contract()
    contract["session"] = list(contract["session"]) + ["not_a_real_field"]
    drifted = tmp_path / "console_data_contract.json"
    drifted.write_text(json.dumps(contract), encoding="utf-8")
    codes = _codes(
        mod.check_console_subset(
            _clone(committed_console),
            contract_path=drifted,
        ),
    )
    assert "console_contract_producer_drift" in codes


def test_console_unreadable_contract_is_an_error(mod, committed_console, tmp_path):
    missing = tmp_path / "nope.json"
    codes = _codes(
        mod.check_console_subset(_clone(committed_console), contract_path=missing),
    )
    assert codes == ["console_contract_unreadable"]


def test_main_console_exits_zero(mod):
    assert mod.main(["--console"]) == 0

# ---------------------------------------------------------------------------
# dashboard feed shape contract (dashboard/data/dashboard_data_contract.json)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed_dashboard(mod):
    import json

    return json.loads(
        (mod.REPO_ROOT / "dashboard" / "data" / "dashboard.json").read_text(
            encoding="utf-8",
        ),
    )


def test_committed_dashboard_json_passes_contract(mod):
    # THE cross-repo guard: the committed dashboard.json (the websites repo's
    # dashboard renders ~12 pages off it over raw GitHub) must match the
    # committed, versioned contract's contracted families as shipped.
    errors = [i for i in mod.check_dashboard_contract() if i.severity == "error"]
    assert errors == [], f"committed dashboard.json breaks its contract: {errors}"


def test_fresh_dashboard_passes_contract(mod):
    fresh = mod._build_fresh()
    errors = [
        i for i in mod.check_dashboard_contract(fresh) if i.severity == "error"
    ]
    assert errors == [], f"fresh dashboard payload breaks the contract: {errors}"


def test_dashboard_contract_matches_producer_constants(mod):
    # The contract file is the cross-repo source of truth; the producer constants
    # must match it exactly (changing one without the other = CI-red drift).
    contract = mod.load_dashboard_contract()
    export = mod._export_module()
    assert contract["version"] == export.DASHBOARD_SCHEMA_VERSION
    assert set(contract["contracted_families"]) == set(
        export.DASHBOARD_CONTRACTED_FAMILIES
    )
    assert set(contract["meta"]) == set(export.DASHBOARD_META_FIELDS)
    assert set(contract["bug"]) == set(export.DASHBOARD_BUG_FIELDS)


def test_dashboard_slice_allows_uncontracted_family(mod, committed_dashboard):
    # SLICE semantics (vs the console's total whitelist): a top-level family the
    # contract has not adopted yet is NOT a finding — growth is family-by-family.
    ok = _clone(committed_dashboard)
    ok["future_family"] = []
    errors = [i for i in mod.check_dashboard_contract(ok) if i.severity == "error"]
    assert errors == []


def test_dashboard_fails_closed_on_missing_contracted_family(
    mod,
    committed_dashboard,
):
    # The consumer-blanking class (BUG-0022): a dropped CONTRACTED family is an
    # ERROR, not a silent shrink — websites' bugs page renders this family.
    bad = {k: v for k, v in _clone(committed_dashboard).items() if k != "bugs"}
    assert "dashboard_family_missing" in _codes(mod.check_dashboard_contract(bad))


def test_dashboard_fails_closed_on_schema_version_mismatch(
    mod,
    committed_dashboard,
):
    bad = _clone(committed_dashboard)
    bad["meta"]["schema_version"] = 999
    assert "dashboard_schema_version_mismatch" in _codes(
        mod.check_dashboard_contract(bad),
    )


def test_dashboard_fails_closed_on_uncontracted_meta_field(
    mod,
    committed_dashboard,
):
    bad = _clone(committed_dashboard)
    bad["meta"]["surprise"] = True
    assert "dashboard_field_not_in_contract" in _codes(
        mod.check_dashboard_contract(bad),
    )


def test_dashboard_fails_closed_on_uncontracted_bug_field(mod, committed_dashboard):
    bad = _clone(committed_dashboard)
    assert bad["bugs"], "committed bugs family unexpectedly empty"
    bad["bugs"][0]["reporter_id"] = 123  # the per-user-leak class
    assert "dashboard_field_not_in_contract" in _codes(
        mod.check_dashboard_contract(bad),
    )


def test_dashboard_fails_closed_on_dropped_guaranteed_bug_field(
    mod,
    committed_dashboard,
):
    bad = _clone(committed_dashboard)
    del bad["bugs"][0]["summary"]
    assert "dashboard_field_missing" in _codes(mod.check_dashboard_contract(bad))


def test_dashboard_contract_producer_drift_is_flagged(
    mod,
    committed_dashboard,
    tmp_path,
):
    import json

    contract = mod.load_dashboard_contract()
    contract["bug"] = list(contract["bug"]) + ["not_a_real_field"]
    drifted = tmp_path / "dashboard_data_contract.json"
    drifted.write_text(json.dumps(contract), encoding="utf-8")
    codes = _codes(
        mod.check_dashboard_contract(
            _clone(committed_dashboard),
            contract_path=drifted,
        ),
    )
    assert "dashboard_contract_producer_drift" in codes


def test_dashboard_unreadable_contract_is_an_error(
    mod,
    committed_dashboard,
    tmp_path,
):
    missing = tmp_path / "nope.json"
    codes = _codes(
        mod.check_dashboard_contract(
            _clone(committed_dashboard),
            contract_path=missing,
        ),
    )
    assert codes == ["dashboard_contract_unreadable"]


def test_dashboard_absent_data_file_is_clean(mod, tmp_path):
    # Generated artifact: absence is a freshness concern, not a contract error.
    assert mod.check_dashboard_contract(data_path=tmp_path / "gone.json") == []


def test_main_dashboard_contract_exits_zero(mod):
    assert mod.main(["--dashboard-contract"]) == 0
