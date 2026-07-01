"""Tests for the Paragon calculator view, modals, and panel wiring.

Structural tests (no live Discord) — they exercise view construction, the
5-input modal limit, T5 select limits, embed formatting, and command/panel
registration.
"""

from __future__ import annotations

from types import SimpleNamespace

import discord
from discord.ext import commands

from services.paragon_service import ParagonRequirementResult, ParagonResult
from utils.btd6 import paragon_math as pm
from views.btd6.panel import BTD6PanelView
from views.btd6.paragon_modals import ParagonForwardModal, ParagonTargetModal
from views.btd6.paragon_view import (
    ParagonCalculatorView,
    ParagonRequirementsView,
    build_calculator_embed,
    build_error_embed,
    build_requirement_embed,
    build_result_embed,
)

_AUTHOR = SimpleNamespace(id=123)


def _selects(view: discord.ui.View) -> list[discord.ui.Select]:
    return [c for c in view.children if isinstance(c, discord.ui.Select)]


def _buttons(view: discord.ui.View) -> list[discord.ui.Button]:
    return [c for c in view.children if isinstance(c, discord.ui.Button)]


# --- view construction -------------------------------------------------------


def test_calculator_view_has_four_selects_and_five_buttons():
    view = ParagonCalculatorView(_AUTHOR)
    assert len(_selects(view)) == 4
    # Calculate, Requirements, 📊 Stats, ↩ BTD6, and the web-calculator link.
    assert len(_buttons(view)) == 5
    assert any("Stats" in (b.label or "") for b in _buttons(view))


def test_calculator_view_has_web_calculator_link_button():
    view = ParagonCalculatorView(_AUTHOR)
    link_buttons = [
        b for b in _buttons(view) if b.style is discord.ButtonStyle.link
    ]
    assert len(link_buttons) == 1
    assert link_buttons[0].url == "https://paragon-calc.vercel.app/"


def test_calculator_view_panel_reference_survives_init():
    # Regression: discord.ui.Item.__init__ resets self._parent — the view must
    # use a non-colliding back-reference so selects can read live state.
    view = ParagonCalculatorView(_AUTHOR)
    for select in _selects(view):
        assert select._panel is view


def _tier5_select(view: ParagonCalculatorView) -> discord.ui.Select:
    return next(s for s in _selects(view) if s.placeholder == "Extra T5s…")


def test_tier5_select_disabled_for_solo_non_dart():
    view = ParagonCalculatorView(
        _AUTHOR, paragon_id="nautic_siege_core", player_count=1,
    )
    assert _tier5_select(view).disabled is True


def test_tier5_select_offers_zero_to_nine_in_coop():
    view = ParagonCalculatorView(
        _AUTHOR, paragon_id="nautic_siege_core", player_count=4,
    )
    select = _tier5_select(view)
    assert select.disabled is False
    assert [o.value for o in select.options] == [str(n) for n in range(10)]


def test_tier5_count_clamped_to_mode_limit_on_build():
    # Solo Dart allows only 1 extra T5; an out-of-range default is clamped.
    view = ParagonCalculatorView(
        _AUTHOR, paragon_id="apex_plasma_master", player_count=1, tier5_count=5,
    )
    assert view.tier5_count == 1


def test_requirements_view_has_strategy_select_and_three_buttons():
    view = ParagonRequirementsView(
        _AUTHOR, paragon_id="apex_plasma_master", player_count=1, difficulty="medium",
    )
    selects = _selects(view)
    assert len(selects) == 1
    assert {o.value for o in selects[0].options} == {s.value for s in pm.SolveStrategy}
    # Enter target, ↩ Calculator, and the web-calculator link button.
    assert len(_buttons(view)) == 3
    link_buttons = [b for b in _buttons(view) if b.style is discord.ButtonStyle.link]
    assert [b.url for b in link_buttons] == ["https://paragon-calc.vercel.app/"]


# --- modals (Discord limits) -------------------------------------------------


def test_forward_modal_has_exactly_five_text_inputs():
    view = ParagonCalculatorView(_AUTHOR)
    modal = ParagonForwardModal(view)
    text_inputs = [c for c in modal.children if isinstance(c, discord.ui.TextInput)]
    assert len(text_inputs) == 5  # Discord's hard cap


def test_target_modal_has_one_text_input():
    view = ParagonRequirementsView(
        _AUTHOR, paragon_id="apex_plasma_master", player_count=1, difficulty="medium",
    )
    modal = ParagonTargetModal(view)
    text_inputs = [c for c in modal.children if isinstance(c, discord.ui.TextInput)]
    assert len(text_inputs) == 1


# --- embeds ------------------------------------------------------------------


def _make_result(*, estimated: bool = False) -> ParagonResult:
    breakdown = pm.compute_breakdown(
        pm.ParagonInputs(
            tower="apex_plasma_master", pops=8_000_000, cash_spent=150_000,
        ),
        150_000,
    )
    return ParagonResult(
        paragon_id="apex_plasma_master",
        paragon_name="Apex Plasma Master",
        tower="Dart Monkey",
        base_price=150_000,
        difficulty="medium",
        game_mode="solo",
        breakdown=breakdown,
        warnings=(),
        estimated=estimated,
        source="local_formula" if estimated else "live_api",
        base_price_source="local_table" if estimated else "api",
        api_version=None if estimated else "1.1",
    )


def test_result_embed_shows_degree_and_breakdown():
    embed = build_result_embed(_make_result())
    assert "Degree" in (embed.title or "")
    breakdown_field = next(f for f in embed.fields if f.name == "Power breakdown")
    assert "Pops" in breakdown_field.value


def test_result_embed_flags_local_estimate():
    embed = build_result_embed(_make_result(estimated=True))
    assert "estimate" in (embed.description or "").lower()


def test_requirement_embed_lists_recommended_build():
    paragon = pm.resolve_paragon("apex_plasma_master")
    solution = pm.solve_requirements(
        paragon, 90, pm.SolveStrategy.LEAST_CASH, player_count=1,
    )
    req = ParagonRequirementResult(
        solution=solution,
        paragon_id=paragon.paragon_id,
        paragon_name=paragon.name,
        tower=paragon.tower,
        verified=True,
        estimated=False,
        confirmed_degree=solution.breakdown.degree,
    )
    embed = build_requirement_embed(req)
    assert "Degree 90" in (embed.title or "")
    build_field = next(f for f in embed.fields if f.name == "Recommended sacrifices")
    assert "Geraldo totems" in build_field.value


def test_calculator_embed_reflects_state():
    view = ParagonCalculatorView(
        _AUTHOR, paragon_id="root_of_all_nature", player_count=4,
    )
    embed = build_calculator_embed(view)
    assert "Root of all Nature" in (embed.description or "")
    assert "coop" in (embed.description or "")


def test_calculator_embed_carries_web_link_and_author_credit():
    view = ParagonCalculatorView(_AUTHOR)
    embed = build_calculator_embed(view)
    credit = next(f for f in embed.fields if "credit" in f.name.lower())
    assert "https://paragon-calc.vercel.app/" in credit.value
    assert "notausgang0341" in credit.value


def test_result_embed_carries_web_link_and_author_credit():
    embed = build_result_embed(_make_result())
    credit = next(f for f in embed.fields if "credit" in f.name.lower())
    assert "https://paragon-calc.vercel.app/" in credit.value
    assert "notausgang0341" in credit.value


def test_error_embed_surfaces_valid_towers():
    from services.paragon_service import ParagonUnknownTowerError

    embed = build_error_embed(
        ParagonUnknownTowerError("no", valid_towers=("Dart Monkey (Dart Monkey)",)),
    )
    assert "Dart Monkey" in (embed.description or "")


# --- panel + command wiring --------------------------------------------------


def test_paragon_reachable_from_panel_units_subpanel():
    # Layout B (2026-07-01): the Paragon calculator moved from a top-level panel
    # button into the 🗼 Units sub-panel. Assert the panel exposes the Units
    # category button AND that the Units sub-panel wires the paragon calculator.
    ids = [getattr(c, "custom_id", None) for c in BTD6PanelView().children]
    assert "btd6:units" in ids
    from views.btd6.hub_panels import _CATEGORIES, _open_paragon

    units_handlers = [entry[3] for entry in _CATEGORIES["units"][3]]
    assert _open_paragon in units_handlers


def test_cog_registers_paragon_command():
    from cogs.paragon_cog import ParagonCog

    assert isinstance(ParagonCog.paragon, commands.Command)
    assert ParagonCog.paragon.name == "paragon"
