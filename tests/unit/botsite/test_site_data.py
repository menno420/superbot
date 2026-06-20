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


# --- shape ----------------------------------------------------------------


def test_emits_every_top_level_family(proto):
    assert set(proto) == {"icons", "areas", "commands", "games", "changelog", "status"}
    assert proto["areas"] and proto["commands"] and proto["games"]


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
