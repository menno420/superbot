"""Tests for utils.role_menu_presentation — theme + template catalogues (§4.6 b/c)."""

from __future__ import annotations

import discord

from services.reaction_role_service import VALID_MODES, VALID_STYLES
from utils import role_menu_presentation as presentation
from utils import role_menu_render


def test_themes_are_non_empty_and_unique():
    themes = presentation.themes()
    assert themes
    keys = [t.key for t in themes]
    assert len(keys) == len(set(keys))  # no duplicate keys
    for theme in themes:
        assert isinstance(theme.color, discord.Color)
        assert theme.label


def test_get_theme_falls_back_to_default():
    assert presentation.get_theme(None).key == presentation.DEFAULT_THEME_KEY
    assert presentation.get_theme("bogus").key == presentation.DEFAULT_THEME_KEY
    assert presentation.get_theme("neon").key == "neon"


def test_theme_color_is_default_safe():
    assert isinstance(presentation.theme_color(None), discord.Color)
    assert presentation.theme_color("neon") == presentation.get_theme("neon").color


def test_templates_reference_valid_themes_and_styles():
    templates = presentation.templates()
    assert templates
    theme_keys = {t.key for t in presentation.themes()}
    for tpl in templates:
        assert tpl.theme in theme_keys, f"{tpl.key} → unknown theme {tpl.theme!r}"
        assert tpl.style in VALID_STYLES, f"{tpl.key} → bad style {tpl.style!r}"
        assert tpl.mode in VALID_MODES, f"{tpl.key} → bad mode {tpl.mode!r}"
        assert tpl.title and tpl.description


def test_event_rsvp_template_is_a_counted_unique_button_poll():
    """The RSVP starter pre-picks the multi-option live-poll config in one tap."""
    rsvp = presentation.get_template("event_rsvp")
    assert rsvp is not None
    assert rsvp.style == "button"  # one button per option (Going / Maybe / …)
    assert rsvp.mode == "unique"  # pick exactly one answer
    assert rsvp.show_counts is True  # the live headcount is on by default


def test_plain_templates_default_to_no_counter():
    """Counts stay opt-in — only the RSVP starter turns them on."""
    assert presentation.get_template("game_roles").show_counts is False
    assert presentation.get_template("colour_roles").mode == "unique"


def test_card_templates_are_non_empty_unique_and_renderable():
    cards = presentation.card_templates()
    assert cards
    keys = [c.key for c in cards]
    assert len(keys) == len(set(keys))  # no duplicate keys
    for card in cards:
        assert card.label
        # Every catalogue entry must map to a style the renderer can draw — a
        # mismatch would silently render nothing in production.
        assert (
            card.style in role_menu_render.KNOWN_STYLES
        ), f"{card.key} → unknown render style {card.style!r}"


def test_get_card_template_none_and_unknown_return_none():
    assert presentation.get_card_template(None) is None
    assert presentation.get_card_template("") is None
    assert presentation.get_card_template("bogus") is None
    first = presentation.card_templates()[0]
    assert presentation.get_card_template(first.key) is first


def test_get_template_lookup():
    assert presentation.get_template(None) is None
    assert presentation.get_template("bogus") is None
    verify = presentation.get_template("verify")
    assert verify is not None
    assert verify.style == "button"


def test_gradient_presets_are_non_empty_unique_and_valid_colours():
    presets = presentation.gradient_presets()
    assert presets
    keys = [p.key for p in presets]
    assert len(keys) == len(set(keys))  # no duplicate keys
    for preset in presets:
        assert preset.label and preset.name
        # primary/secondary must convert to a discord.Color (valid 0xRRGGBB int).
        assert isinstance(discord.Color(preset.primary), discord.Color)
        assert isinstance(discord.Color(preset.secondary), discord.Color)
        assert 0 <= preset.primary <= 0xFFFFFF
        assert 0 <= preset.secondary <= 0xFFFFFF
