"""Tests for utils.role_menu_presentation — theme + template catalogues (§4.6 b/c)."""

from __future__ import annotations

import discord

from services.reaction_role_service import VALID_STYLES
from utils import role_menu_presentation as presentation


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
        assert tpl.title and tpl.description


def test_get_template_lookup():
    assert presentation.get_template(None) is None
    assert presentation.get_template("bogus") is None
    verify = presentation.get_template("verify")
    assert verify is not None
    assert verify.style == "button"
