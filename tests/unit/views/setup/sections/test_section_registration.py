"""Pins the production section set registered at import time.

If a contributor adds a new section, they update this test alongside the
hub layout it pins.  If they reorder existing sections, the ordering
assertion catches it.

PR 3a (2026-06-25) retired the dead/legacy sections — ``purpose``,
``identity``, ``btd6``, ``ai_setup``, ``readiness``, ``diagnostics``,
``suggestions`` (deleted modules) and the ``server_scan`` button (module
kept as a cache seam) — whose function moved into the Essential Setup
spine.  The ``_RETIRED_SLUGS`` assertion keeps them gone.
"""

from __future__ import annotations

import discord

import views.setup.sections  # noqa: F401 — import side-effect: registration
from services.setup_sections import REGISTRY

_PRODUCTION_SLUGS = {
    "preset_select",
    "channels",
    "cleanup",
    "moderation",
    "roles",
    "role_templates",
    "logging_presets",
    "cog_routing",
    "final_review",
    "ticket",
}

# Sections retired from the wizard flow by PR 3a — their function now lives
# in the Essential Setup spine (step 0 + "Check my setup").
_RETIRED_SLUGS = {
    "purpose",
    "identity",
    "btd6",
    "ai_setup",
    "server_scan",
    "readiness",
    "diagnostics",
    "suggestions",
}


def test_all_production_sections_are_registered():
    slugs = {section.slug for section in REGISTRY.all()}
    assert (
        _PRODUCTION_SLUGS <= slugs
    ), f"missing expected production section slugs: {_PRODUCTION_SLUGS - slugs}"


def test_retired_sections_are_not_registered():
    """PR 3a: the dead/legacy sections no longer render in the wizard."""
    slugs = {section.slug for section in REGISTRY.all()}
    still_present = _RETIRED_SLUGS & slugs
    assert not still_present, (
        f"retired setup sections re-registered: {still_present}. "
        "Their function moved into Essential Setup (step 0 / Check my setup)."
    )


def test_section_render_order_is_stable():
    """Production layout after PR 3a's retirements."""
    layout = [
        section.slug
        for section in REGISTRY.all()
        if section.slug in _PRODUCTION_SLUGS
    ]
    assert layout == [
        "preset_select",
        "channels",
        "logging_presets",
        "roles",
        "role_templates",
        "cleanup",
        "moderation",
        "cog_routing",
        "ticket",
        "final_review",
    ], (
        "production section ordering must remain stable; reorder requires "
        "an intentional update of this test"
    )


def test_preset_select_section_uses_success_button():
    section = REGISTRY.get("preset_select")
    assert section is not None
    assert section.style == discord.ButtonStyle.success


def test_channels_section_uses_secondary_button():
    section = REGISTRY.get("channels")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_cleanup_section_uses_secondary_button():
    section = REGISTRY.get("cleanup")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_cleanup_section_is_advanced_only():
    """PR 3a: cleanup demoted out of the standard depth."""
    section = REGISTRY.get("cleanup")
    assert section is not None
    assert section.depths == frozenset({"advanced"})


def test_cog_routing_section_uses_secondary_button():
    section = REGISTRY.get("cog_routing")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_final_review_section_uses_secondary_button():
    section = REGISTRY.get("final_review")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_every_section_label_fits_discord_button():
    for section in REGISTRY.all():
        assert 1 <= len(section.label) <= 80, (
            f"{section.slug!r} label out of Discord button-label range: "
            f"{section.label!r}"
        )
