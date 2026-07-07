"""Contract tests for the SPA data generator (botsite/site_data.py).

These are **stdlib-only** (no FastAPI / no web deps), so unlike the rest of
``tests/unit/botsite`` they run in CI. They guard the Claude-Design data contract
(``DATA_CONTRACT.md``): the generated ``window.SBDATA`` must keep every key, every
cross-reference must resolve (or SPA pages 404), and the data must be derived from
the real ``site.json`` rather than hand-written sample content.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SITE_DATA = _REPO / "botsite" / "site_data.py"
_SITE_JSON = _REPO / "botsite" / "data" / "site.json"
_APP_CSS = _REPO / "botsite" / "site" / "app.css"
_DATA_JS = _REPO / "botsite" / "site" / "data.js"

_PALETTE = {
    "var(--g)",
    "var(--g-bright)",
    "var(--sky)",
    "var(--amber)",
    "var(--pink)",
    "var(--indigo)",
}
_EXPORT_LINE = "window.SBDATA = { ICONS, AREAS, COMMANDS, GAMES, CHANGELOG, STATUS, byCommand, byArea, byGame, commandsInArea };"


def _load_module():
    spec = importlib.util.spec_from_file_location("botsite_site_data_ut", _SITE_DATA)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_module()


@pytest.fixture(scope="module")
def site():
    return json.loads(_SITE_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def proto(mod, site):
    return mod.build_prototype_data(site)


# --- /site-data.json contract guard (the React-SPA seam) -------------------
# These run in the main code-quality CI (stdlib-only), unlike the FastAPI-gated
# test_app.py — so producer-side drift in the React data seam fails loudly here.

_ADD_URL = "https://discord.com/oauth2/authorize?client_id=1403818430758654132"


@pytest.fixture(scope="module")
def payload(mod, site):
    return mod.build_site_data_payload(site, _ADD_URL)


def test_site_data_payload_conforms_to_contract(mod, payload):
    # The real payload (built from the committed site.json) satisfies the canonical
    # contract — the same file the React adapter's vitest test checks against.
    problems = mod.validate_site_data_payload(payload)
    assert problems == [], f"contract violations: {problems}"


def test_site_data_payload_carries_real_data_and_install_url(payload):
    assert payload["addUrl"] == _ADD_URL
    assert "discord.com/oauth2/authorize" in payload["addUrl"]
    names = {c["name"] for c in payload["commands"]}
    assert "blackjack" in names
    # Honest posture: only catalogue counts, never server/user totals.
    assert set(payload["counts"]) <= {"commands", "features", "games"}


def test_validator_flags_a_missing_top_level_key(mod, payload):
    broken = {k: v for k, v in payload.items() if k != "areas"}
    problems = mod.validate_site_data_payload(broken)
    assert any("missing top-level key" in p and "areas" in p for p in problems)


def test_validator_flags_an_unexpected_top_level_key(mod, payload):
    broken = {**payload, "secretTotals": 9001}
    problems = mod.validate_site_data_payload(broken)
    assert any("unexpected top-level key" in p and "secretTotals" in p for p in problems)


def test_validator_flags_a_missing_entry_subkey(mod, payload):
    broken = {**payload, "commands": [{"area": "games"}]}  # no "name"
    problems = mod.validate_site_data_payload(broken)
    assert any("commands[0] missing key" in p and "name" in p for p in problems)


def test_contract_file_is_the_single_source_loaded_by_the_validator(mod):
    contract = mod.load_site_data_contract()
    assert set(contract["top_level"]) == {
        "addUrl",
        "build",
        "counts",
        "areas",
        "commands",
        "games",
        "changelog",
        "status",
    }


# --- shape ----------------------------------------------------------------


def test_emits_every_top_level_family(proto):
    assert set(proto) == {
        "icons",
        "areas",
        "commands",
        "games",
        "changelog",
        "status",
        "features",
        "build",
        "counts",
        "add_url",
    }
    assert proto["areas"] and proto["commands"] and proto["games"]
    assert proto["features"]
    assert "discord.com/oauth2/authorize" in proto["add_url"]


def test_command_fields_match_contract(proto):
    for c in proto["commands"]:
        assert set(c) == {
            "name",
            "area",
            "status",
            "summary",
            "description",
            "usage",
            "aliases",
            "permissions",
            "cooldown",
            "examples",
            "planned",
        }
        assert c["status"] in ("finished", "in-progress")
        assert c["cooldown"] is None or isinstance(c["cooldown"], str)
        # arrays that can be empty must be present as lists, never None.
        assert isinstance(c["aliases"], list)
        assert isinstance(c["examples"], list)
        assert isinstance(c["planned"], list)
        for p in c["planned"]:
            assert set(p) == {"status", "title"}


def test_command_names_are_unique(proto):
    names = [c["name"] for c in proto["commands"]]
    assert len(names) == len(
        set(names),
    ), "duplicate command names break #/command/<name>"


# --- cross-reference rules (must hold or pages 404) -----------------------


def test_every_command_area_resolves(proto):
    area_ids = {a["id"] for a in proto["areas"]}
    for c in proto["commands"]:
        assert c["area"] in area_ids, f"{c['name']} → unknown area {c['area']}"


def test_every_game_command_resolves(proto):
    names = {c["name"] for c in proto["commands"]}
    for g in proto["games"]:
        assert g["command"] in names, f"game {g['id']} → unknown command {g['command']}"


# --- v2 additive families (FEATURES / BUILD / COUNTS) ----------------------


def test_feature_fields_and_area_cross_refs(proto):
    area_ids = {a["id"] for a in proto["areas"]}
    for f in proto["features"]:
        assert set(f) == {
            "key",
            "name",
            "emoji",
            "area",
            "description",
            "tags",
            "is_game",
        }
        assert f["key"] and f["name"]
        assert f["area"] in area_ids, f"feature {f['key']} → unknown area {f['area']}"
        assert isinstance(f["tags"], list)
        assert isinstance(f["is_game"], bool)


def test_features_are_the_full_catalogue(proto, site):
    keys = [f["key"] for f in proto["features"]]
    assert len(keys) == len(set(keys)), "duplicate feature keys break #/feature/<key>"
    assert len(keys) == len([c for c in site["catalogue"] if c.get("key")])
    game_keys = {f["key"] for f in proto["features"] if f["is_game"]}
    assert {g["id"] for g in proto["games"]} == game_keys


def test_build_and_counts_carry_real_provenance(proto, site):
    assert proto["build"]["commit"] == site["meta"]["build"]["commit"]
    assert set(proto["counts"]) <= {"commands", "features", "games"}
    assert proto["counts"].get("commands")


def test_all_icons_exist(mod, proto):
    for a in proto["areas"]:
        assert a["icon"] in mod.ICONS
    for g in proto["games"]:
        assert g["icon"] in mod.ICONS


def test_all_colors_are_real_css_vars(proto):
    css = _APP_CSS.read_text(encoding="utf-8")
    for item in (*proto["areas"], *proto["games"]):
        assert item["color"] in _PALETTE
        # The var must actually be defined in the theme (handoff rule 4).
        assert item["color"][4:-1] + ":" in css or item["color"][4:-1] in css


def test_status_enums(proto):
    s = proto["status"]
    assert s["overall"] == "operational"
    for sys in s["systems"]:
        assert sys["state"] in ("operational", "degraded", "maintenance", "outage")
        assert len(sys["history"]) == 60


def test_changelog_change_types(proto):
    for entry in proto["changelog"]:
        assert set(entry) == {"version", "date", "build", "title", "changes"}
        for ch in entry["changes"]:
            assert ch["type"] in ("added", "improved", "fixed", "removed")


# --- derived-from-real-data + render --------------------------------------


def test_derived_from_real_site_json_not_sample(proto, site):
    # The generator must reflect the actual bot, not the handoff's sample content.
    names = {c["name"] for c in proto["commands"]}
    assert "blackjack" in names
    # Deduped command count == unique names in site.json.
    assert len(proto["commands"]) == len({c["name"] for c in site["commands"]})


def test_render_data_js_keeps_export_line_and_is_loadable(mod, proto):
    js = mod.render_data_js(proto)
    assert _EXPORT_LINE in js
    # The lookup helpers + mkHistory the contract says to keep are present.
    for token in (
        "const byCommand",
        "const byArea",
        "const byGame",
        "const commandsInArea",
        "function mkHistory",
        # v2 additive families ride behind the frozen v1 export line.
        "const byFeature",
        "const featuresInArea",
        "Object.assign(window.SBDATA, { FEATURES, BUILD, COUNTS",
    ):
        assert token in js
    assert "GENERATED FROM botsite/data/site.json" in js


def test_committed_data_js_is_in_sync_with_site_json(mod, site):
    # The committed fallback must match what the generator produces now — i.e. it was
    # regenerated after the last site.json change. Re-run `python3.10 -m
    # botsite.site_data` (or scripts/export_dashboard_data.py) if this fails.
    expected = mod.render_from_site(site)
    actual = _DATA_JS.read_text(encoding="utf-8")
    assert actual == expected, "botsite/site/data.js is stale — regenerate it"
