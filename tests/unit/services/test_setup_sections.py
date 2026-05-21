"""Tests for the `SetupSection` registry foundation.

These pin the contracts the setup-wizard hub relies on:

* slugs and labels are validated up front (no Discord errors at render
  time);
* sections register once — duplicate slugs raise rather than silently
  shadow;
* `all()` returns sections sorted by `(order, slug)` so the hub layout
  is deterministic across processes;
* `unregister` is a safe test escape hatch.

The tests use a private registry instance so the production registrations
in `views.setup.sections` are not perturbed.
"""

from __future__ import annotations

from typing import Any

import discord
import pytest

from services.setup_sections import (
    REGISTRY,
    SetupSection,
    SetupSectionRegistry,
)


async def _noop(_interaction: Any, _hub: Any) -> None:
    return None


def _section(
    slug: str = "demo",
    *,
    label: str = "Demo section",
    order: int = 50,
    style: discord.ButtonStyle = discord.ButtonStyle.primary,
    step: str | None = None,
) -> SetupSection:
    return SetupSection(
        slug=slug,
        label=label,
        style=style,
        run=_noop,
        order=order,
        step=step,
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def test_register_rejects_empty_slug():
    reg = SetupSectionRegistry()
    with pytest.raises(ValueError, match="non-empty"):
        reg.register(_section(slug=""))


def test_register_rejects_non_alphanumeric_slug():
    reg = SetupSectionRegistry()
    with pytest.raises(ValueError, match="alphanumeric/underscore"):
        reg.register(_section(slug="not-a-slug"))


def test_register_rejects_empty_label():
    reg = SetupSectionRegistry()
    with pytest.raises(ValueError, match="label"):
        reg.register(_section(label=""))


def test_register_rejects_label_over_discord_limit():
    reg = SetupSectionRegistry()
    too_long = "x" * 81
    with pytest.raises(ValueError, match="80 chars"):
        reg.register(_section(label=too_long))


def test_register_rejects_non_callable_run():
    reg = SetupSectionRegistry()
    bad = SetupSection(
        slug="demo",
        label="Demo",
        style=discord.ButtonStyle.primary,
        run="not a function",  # type: ignore[arg-type]
    )
    with pytest.raises(ValueError, match="callable"):
        reg.register(bad)


def test_register_rejects_duplicate_slug():
    reg = SetupSectionRegistry()
    reg.register(_section(slug="demo"))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(_section(slug="demo", label="Other"))


# ---------------------------------------------------------------------------
# Lookups + ordering
# ---------------------------------------------------------------------------


def test_get_returns_registered_section():
    reg = SetupSectionRegistry()
    section = _section(slug="demo")
    reg.register(section)
    assert reg.get("demo") is section


def test_get_returns_none_for_unknown_slug():
    reg = SetupSectionRegistry()
    assert reg.get("never_registered") is None


def test_contains_matches_registered_slug():
    reg = SetupSectionRegistry()
    reg.register(_section(slug="demo"))
    assert "demo" in reg
    assert "missing" not in reg
    assert 42 not in reg  # type: ignore[operator]


def test_len_counts_registered_sections():
    reg = SetupSectionRegistry()
    assert len(reg) == 0
    reg.register(_section(slug="a"))
    reg.register(_section(slug="b"))
    assert len(reg) == 2


def test_all_sorted_by_order_then_slug():
    reg = SetupSectionRegistry()
    reg.register(_section(slug="z", order=10))
    reg.register(_section(slug="a", order=10))
    reg.register(_section(slug="m", order=5))
    slugs = [s.slug for s in reg.all()]
    assert slugs == ["m", "a", "z"], "lower order first; ties broken by slug"


# ---------------------------------------------------------------------------
# unregister
# ---------------------------------------------------------------------------


def test_unregister_removes_registered_section():
    reg = SetupSectionRegistry()
    reg.register(_section(slug="demo"))
    reg.unregister("demo")
    assert reg.get("demo") is None


def test_unregister_unknown_slug_is_noop():
    reg = SetupSectionRegistry()
    reg.unregister("never_registered")  # must not raise


# ---------------------------------------------------------------------------
# session_step
# ---------------------------------------------------------------------------


def test_session_step_defaults_to_slug():
    section = _section(slug="demo")
    assert section.session_step == "demo"


def test_session_step_uses_explicit_step_override():
    section = _section(slug="demo", step="custom_step")
    assert section.session_step == "custom_step"


# ---------------------------------------------------------------------------
# Module-level REGISTRY
# ---------------------------------------------------------------------------


def test_module_registry_is_a_setup_section_registry():
    assert isinstance(REGISTRY, SetupSectionRegistry)


# ---------------------------------------------------------------------------
# for_depth filtering
# ---------------------------------------------------------------------------


def test_for_depth_returns_only_matching_sections():
    registry = SetupSectionRegistry()
    quick_only = _section("quick_only", order=10)
    quick_only_with_depth = SetupSection(
        slug=quick_only.slug,
        label=quick_only.label,
        style=quick_only.style,
        run=quick_only.run,
        order=quick_only.order,
        depths=frozenset({"quick"}),
    )
    standard_only = SetupSection(
        slug="standard_only",
        label="Standard Only",
        style=discord.ButtonStyle.secondary,
        run=_noop,
        order=20,
        depths=frozenset({"standard"}),
    )
    universal = SetupSection(
        slug="universal",
        label="Universal",
        style=discord.ButtonStyle.secondary,
        run=_noop,
        order=30,
        depths=frozenset({"quick", "standard", "advanced"}),
    )
    registry.register(quick_only_with_depth)
    registry.register(standard_only)
    registry.register(universal)

    quick = {s.slug for s in registry.for_depth("quick")}
    standard = {s.slug for s in registry.for_depth("standard")}
    advanced = {s.slug for s in registry.for_depth("advanced")}

    assert quick == {"quick_only", "universal"}
    assert standard == {"standard_only", "universal"}
    assert advanced == {"universal"}


def test_for_depth_none_returns_every_section():
    """``None`` is the legacy / pre-picker fallback — show everything."""
    registry = SetupSectionRegistry()
    registry.register(
        SetupSection(
            slug="advanced_only",
            label="Advanced Only",
            style=discord.ButtonStyle.secondary,
            run=_noop,
            order=10,
            depths=frozenset({"advanced"}),
        ),
    )
    sections = registry.for_depth(None)
    assert len(sections) == 1


def test_for_depth_is_sorted_consistently_with_all():
    registry = SetupSectionRegistry()
    registry.register(
        SetupSection(
            slug="z_section",
            label="Z",
            style=discord.ButtonStyle.secondary,
            run=_noop,
            order=10,
            depths=frozenset({"standard"}),
        ),
    )
    registry.register(
        SetupSection(
            slug="a_section",
            label="A",
            style=discord.ButtonStyle.secondary,
            run=_noop,
            order=10,
            depths=frozenset({"standard"}),
        ),
    )
    sections = registry.for_depth("standard")
    # Order-then-slug means a_section first.
    assert [s.slug for s in sections] == ["a_section", "z_section"]
