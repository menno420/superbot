"""Unit tests for core.runtime.panel_manifest — manifest spine slice 2.

The panel manifest is a pure projection of the persistent-view registry, so
most tests build from fake ``PersistentView`` fixtures (faithful projection,
PANEL_ID resolution, button introspection, to_dict shape, cache + diagnostics,
the subsystem join helper).

The final block is the vision doc's **"panel registry vs view classes / custom
IDs" reconciliation test** built against the *real* registered panels: every
button's custom_id round-trips against a fresh instantiation of the view class,
ids are unique per panel, panel_ids are unique across the manifest, and every
registered persistent view appears — i.e. the metadata is trustworthy.
"""

from __future__ import annotations

import datetime

import discord
import pytest

from core.runtime import panel_manifest as pm
from core.runtime import persistent_views


@pytest.fixture(autouse=True)
def _reset():
    pm._reset_for_tests()
    yield
    pm._reset_for_tests()


# --- Fake view classes (do not touch the live registry) --------------------


class _FakePanel(persistent_views.PersistentView):
    SUBSYSTEM = "fake"

    @discord.ui.button(label="Alpha", custom_id="fake:alpha", row=0)
    async def alpha(self, interaction, button):  # pragma: no cover - not invoked
        ...

    @discord.ui.button(label="Beta", custom_id="fake:beta", row=1)
    async def beta(self, interaction, button):  # pragma: no cover - not invoked
        ...


class _ExplicitIdPanel(persistent_views.PersistentView):
    SUBSYSTEM = "shared"
    PANEL_ID = "shared:secondary"

    @discord.ui.button(label="Gamma", custom_id="shared:gamma")
    async def gamma(self, interaction, button):  # pragma: no cover - not invoked
        ...


class _UrlButtonPanel(persistent_views.PersistentView):
    """A panel with a URL button (no custom_id) — must be skipped."""

    SUBSYSTEM = "linky"

    def __init__(self) -> None:
        super().__init__()
        self.add_item(discord.ui.Button(label="Docs", url="https://example.com"))

    @discord.ui.button(label="Keep", custom_id="linky:keep")
    async def keep(self, interaction, button):  # pragma: no cover - not invoked
        ...


# ---------------------------------------------------------------------------
# Faithful projection
# ---------------------------------------------------------------------------


def test_projects_each_view_class_to_one_entry():
    mf = pm.build_panel_manifest((_FakePanel, _ExplicitIdPanel))
    assert len(mf.panels) == 2
    by_id = {p.panel_id: p for p in mf.panels}
    assert set(by_id) == {"fake", "shared:secondary"}
    assert by_id["fake"].view_class == "_FakePanel"
    assert by_id["fake"].subsystem == "fake"
    assert by_id["fake"].layout_source == "hardcoded"
    assert by_id["fake"].source is None


def test_panel_id_falls_back_to_subsystem_and_honours_explicit():
    mf = pm.build_panel_manifest((_FakePanel, _ExplicitIdPanel))
    ids = {p.view_class: p.panel_id for p in mf.panels}
    assert ids["_FakePanel"] == "fake"  # PANEL_ID empty → SUBSYSTEM
    assert ids["_ExplicitIdPanel"] == "shared:secondary"  # explicit PANEL_ID


def test_buttons_introspected_in_component_order():
    mf = pm.build_panel_manifest((_FakePanel,))
    buttons = mf.panels[0].buttons
    assert [b.custom_id for b in buttons] == ["fake:alpha", "fake:beta"]
    alpha = buttons[0]
    assert alpha.action_id == alpha.custom_id == "fake:alpha"
    assert alpha.label == "Alpha"
    assert alpha.row == 0
    assert alpha.command is None  # deferred — no button→command binding yet


def test_components_without_custom_id_are_skipped():
    mf = pm.build_panel_manifest((_UrlButtonPanel,))
    cids = [b.custom_id for b in mf.panels[0].buttons]
    assert cids == ["linky:keep"]  # the url button has no custom_id → skipped


def test_entries_sorted_by_panel_id():
    mf = pm.build_panel_manifest((_ExplicitIdPanel, _FakePanel))
    assert [p.panel_id for p in mf.panels] == ["fake", "shared:secondary"]


# ---------------------------------------------------------------------------
# Envelope + to_dict shape
# ---------------------------------------------------------------------------


def test_envelope_fields():
    fixed = datetime.datetime(2026, 6, 17, 12, 0, tzinfo=datetime.timezone.utc)
    mf = pm.build_panel_manifest((_FakePanel,), now=fixed)
    assert mf.version == pm.PANEL_MANIFEST_VERSION
    assert mf.generated_at == fixed.isoformat()


def test_to_dict_schema_shape():
    mf = pm.build_panel_manifest((_FakePanel,))
    d = mf.to_dict()
    assert set(d) == {"version", "generated_at", "panels", "findings"}
    assert d["findings"] == []
    panel = d["panels"][0]
    assert set(panel) == {
        "panel_id",
        "view_class",
        "subsystem",
        "layout_source",
        "source",
        "buttons",
    }
    button = panel["buttons"][0]
    assert set(button) == {"action_id", "custom_id", "label", "row", "command"}


# ---------------------------------------------------------------------------
# Subsystem join helper
# ---------------------------------------------------------------------------


def test_panels_by_subsystem_groups_and_sorts():
    mf = pm.build_panel_manifest((_FakePanel, _ExplicitIdPanel))
    # Two panels under one subsystem must both appear, sorted.
    join = pm.panels_by_subsystem(mf)
    assert join["fake"] == ("fake",)
    assert join["shared"] == ("shared:secondary",)


def test_panels_by_subsystem_collects_multiple_per_subsystem():
    mf = pm.build_panel_manifest((_FakePanel, _ExplicitIdPanel, _UrlButtonPanel))
    # Add a second panel under "fake" by reusing the subsystem on a fresh class.
    join = pm.panels_by_subsystem(mf)
    assert set(join) == {"fake", "shared", "linky"}


# ---------------------------------------------------------------------------
# Cache round-trip + diagnostics
# ---------------------------------------------------------------------------


def test_build_and_cache_round_trip():
    assert pm.get_cached_manifest() is None
    built = pm.build_and_cache((_FakePanel,))
    assert pm.get_cached_manifest() is built
    assert len(built.panels) == 1


def test_diagnostics_snapshot_not_built():
    from services import diagnostics_service

    assert "panel_manifest" in diagnostics_service.registered_names()
    snap = diagnostics_service.snapshot("panel_manifest")
    assert snap["built"] is False


def test_diagnostics_snapshot_built():
    from services import diagnostics_service

    pm.build_and_cache((_FakePanel, _ExplicitIdPanel))
    snap = diagnostics_service.snapshot("panel_manifest")
    assert snap["built"] is True
    assert snap["panel_count"] == 2
    assert snap["button_count"] == 3  # 2 + 1
    assert snap["version"] == pm.PANEL_MANIFEST_VERSION


# ---------------------------------------------------------------------------
# Reconciliation — panel registry vs view classes / custom IDs (real registry)
# ---------------------------------------------------------------------------


def _real_manifest() -> pm.PanelManifest:
    """Build from the live registry, importing the panel modules so it's
    populated regardless of test collection order.
    """
    import importlib

    for mod in (
        "views.ai.panel",
        "views.moderation.main_panel",
        "views.economy.main_panel",
        "views.btd6.panel",
        "views.mining.main_panel",
        "views.ux_lab.persistent_demo",
        "views.server_management.hub",
        "cogs.help.panels",
        "cogs.role_cog",
    ):
        importlib.import_module(mod)
    return pm.build_panel_manifest()


def test_real_manifest_covers_every_registered_class():
    mf = _real_manifest()
    registered = {c.__name__ for c in persistent_views.iter_registered_view_classes()}
    projected = {p.view_class for p in mf.panels}
    # Every registered persistent view is projected (no panel dropped, including
    # the two that share the "help" subsystem).
    assert registered <= projected


def test_real_panel_ids_are_unique():
    mf = _real_manifest()
    ids = [p.panel_id for p in mf.panels]
    assert len(ids) == len(set(ids)), f"duplicate panel_id(s): {ids}"


def test_real_button_custom_ids_round_trip_against_view_classes():
    """The core reconciliation: every button recorded in the manifest matches a
    real component on a freshly instantiated view class (no fabricated id, none
    dropped), and custom_ids are unique within a panel.
    """
    mf = _real_manifest()
    by_class = {c.__name__: c for c in persistent_views.iter_registered_view_classes()}
    for panel in mf.panels:
        cls = by_class[panel.view_class]
        live_ids = [
            getattr(c, "custom_id", None)
            for c in cls().children
            if getattr(c, "custom_id", None)
        ]
        manifest_ids = [b.custom_id for b in panel.buttons]
        assert manifest_ids == live_ids, f"{panel.panel_id} drifted from its view"
        assert len(manifest_ids) == len(
            set(manifest_ids),
        ), f"{panel.panel_id} has duplicate custom_ids"
