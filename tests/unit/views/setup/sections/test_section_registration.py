"""Pins the production section set registered at import time.

If a contributor adds a new section, they update this test alongside the
hub layout it pins.  If they reorder existing sections, the ordering
assertion catches it.
"""

from __future__ import annotations

import discord

import views.setup.sections  # noqa: F401 — import side-effect: registration
from services.setup_sections import REGISTRY


def test_all_production_sections_are_registered():
    slugs = {section.slug for section in REGISTRY.all()}
    expected = {"server_scan", "readiness", "suggestions", "identity", "final_review"}
    assert expected <= slugs, (
        f"missing expected production section slugs: {expected - slugs}"
    )


def test_section_render_order_is_stable():
    """Production layout: server_scan → readiness → suggestions → identity → final_review."""
    layout = [
        section.slug
        for section in REGISTRY.all()
        if section.slug
        in {"server_scan", "readiness", "suggestions", "identity", "final_review"}
    ]
    assert layout == [
        "server_scan",
        "readiness",
        "suggestions",
        "identity",
        "final_review",
    ], (
        "production section ordering must remain stable; reorder requires "
        "an intentional update of this test"
    )


def test_server_scan_section_uses_primary_button():
    section = REGISTRY.get("server_scan")
    assert section is not None
    assert section.style == discord.ButtonStyle.primary


def test_readiness_section_uses_primary_button():
    section = REGISTRY.get("readiness")
    assert section is not None
    assert section.style == discord.ButtonStyle.primary


def test_suggestions_section_uses_success_button():
    section = REGISTRY.get("suggestions")
    assert section is not None
    assert section.style == discord.ButtonStyle.success


def test_final_review_section_uses_secondary_button():
    section = REGISTRY.get("final_review")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_identity_section_uses_secondary_button():
    section = REGISTRY.get("identity")
    assert section is not None
    assert section.style == discord.ButtonStyle.secondary


def test_every_section_label_fits_discord_button():
    for section in REGISTRY.all():
        assert 1 <= len(section.label) <= 80, (
            f"{section.slug!r} label out of Discord button-label range: "
            f"{section.label!r}"
        )
