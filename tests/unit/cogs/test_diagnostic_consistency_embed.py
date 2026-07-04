"""Tests for cogs.diagnostic._platform_embeds.build_consistency_embed."""

from __future__ import annotations

import datetime

import discord
import pytest

from cogs.diagnostic._platform_embeds import (
    _EMBED_SOFT_CAP,
    _FIELD_HARD_CAP,
    _INFORMATIONAL_PREFIX,
    build_consistency_embed,
)
from services.platform_consistency import (
    ConsistencyReport,
    SectionResult,
    SectionStatus,
)


def _section(
    name: str,
    status: SectionStatus,
    *,
    summary: str = "summary",
    details: tuple[str, ...] = (),
    informational: bool = False,
) -> SectionResult:
    return SectionResult(
        name=name,
        status=status,
        summary=summary,
        details=details,
        informational=informational,
    )


def _report(*sections: SectionResult) -> ConsistencyReport:
    return ConsistencyReport(
        sections=sections,
        generated_at=datetime.datetime(2026, 5, 18, 17, 30, tzinfo=datetime.timezone.utc),
    )


# ---------------------------------------------------------------------------
# Color mapping
# ---------------------------------------------------------------------------


def test_build_embed_color_red_when_any_fatal():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section("b", SectionStatus.FATAL),
        ),
    )
    assert embed.color == discord.Color.red()
    assert "FATAL" in embed.title


def test_build_embed_color_gold_when_warning():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section("b", SectionStatus.WARNING),
        ),
    )
    assert embed.color == discord.Color.gold()
    assert "WARNING" in embed.title


def test_build_embed_color_green_when_clean():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section("b", SectionStatus.CLEAN),
        ),
    )
    assert embed.color == discord.Color.green()
    assert "CLEAN" in embed.title


def test_build_embed_color_grey_when_all_skipped():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.SKIPPED),
            _section("b", SectionStatus.SKIPPED),
        ),
    )
    assert embed.color == discord.Color.light_grey()
    assert "SKIPPED" in embed.title


# ---------------------------------------------------------------------------
# Bounded size
# ---------------------------------------------------------------------------


def test_build_embed_bounded_under_6000_chars():
    """Stress: 10 sections each with 4KB of details should not exceed
    Discord's 6000-char embed limit."""
    big = "x" * 4000
    sections = tuple(
        _section(
            f"section-{i}",
            SectionStatus.WARNING,
            summary="s" * 200,
            details=tuple([big] * 4),
        )
        for i in range(10)
    )
    embed = build_consistency_embed(_report(*sections))
    # The Discord SDK exposes __len__ for Embed; use that as the source of truth.
    assert len(embed) < 6000


def test_build_embed_truncates_field_with_marker():
    big = "y" * 5000
    embed = build_consistency_embed(
        _report(
            _section(
                "big",
                SectionStatus.WARNING,
                summary="overview",
                details=(big,),
            ),
        ),
    )
    # The field value cap (≤1000) leaves a truncation marker on long
    # fields.
    overflow_fields = [
        f for f in embed.fields if f.value and len(f.value) > 1024
    ]
    assert not overflow_fields
    long_fields = [f for f in embed.fields if f.value and "…" in f.value]
    assert long_fields, "Expected at least one truncated field with the … marker"


def test_build_embed_field_cap_at_24():
    sections = tuple(
        _section(f"s{i}", SectionStatus.CLEAN, summary="ok")
        for i in range(50)
    )
    embed = build_consistency_embed(_report(*sections))
    assert len(embed.fields) <= _FIELD_HARD_CAP + 1  # +1 for optional `… truncated`


# ---------------------------------------------------------------------------
# Informational section labelling (clarification #4)
# ---------------------------------------------------------------------------


def test_build_embed_informational_section_labelled():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section(
                "Setup readiness",
                SectionStatus.WARNING,
                summary="3 roadmap blocker(s)",
                details=("blocker_a", "blocker_b"),
                informational=True,
            ),
        ),
    )
    # Find the Setup readiness field; its value must contain the
    # informational marker so operators don't read it as runtime failure.
    setup_field = next(
        (f for f in embed.fields if "Setup readiness" in (f.name or "")),
        None,
    )
    assert setup_field is not None
    # The marker prefix lives at the start of the rendered value.
    assert _INFORMATIONAL_PREFIX.strip() in (setup_field.value or "")


def test_build_embed_footer_separates_informational_from_runtime_warnings():
    """Footer must count informational and runtime warnings separately."""
    embed = build_consistency_embed(
        _report(
            _section("runtime-a", SectionStatus.WARNING),
            _section("runtime-b", SectionStatus.WARNING),
            _section(
                "Setup readiness",
                SectionStatus.WARNING,
                informational=True,
            ),
        ),
    )
    assert embed.footer is not None
    footer_text = embed.footer.text or ""
    assert "2 runtime warning" in footer_text
    assert "1 informational" in footer_text


def test_build_embed_informational_warning_does_not_force_fatal_title():
    """If only the Setup readiness section is WARNING, the overall
    status (and embed title) must remain CLEAN."""
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section(
                "Setup readiness",
                SectionStatus.WARNING,
                informational=True,
            ),
        ),
    )
    assert "CLEAN" in embed.title


# ---------------------------------------------------------------------------
# Description content
# ---------------------------------------------------------------------------


def test_build_embed_description_includes_counts_and_timestamp():
    embed = build_consistency_embed(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section("b", SectionStatus.WARNING),
            _section("c", SectionStatus.FATAL),
            _section("d", SectionStatus.SKIPPED),
        ),
    )
    desc = embed.description or ""
    assert "1 clean" in desc
    assert "1 warning" in desc
    assert "1 fatal" in desc
    assert "1 skipped" in desc
    assert "2026-05-18" in desc


# ---------------------------------------------------------------------------
# Embed soft cap constant sanity
# ---------------------------------------------------------------------------


def test_soft_cap_under_discord_hard_limit():
    """Soft cap must leave headroom under Discord's 6000-char hard limit."""
    assert _EMBED_SOFT_CAP < 6000


# ---------------------------------------------------------------------------
# Pagination — build_consistency_pages (diagnostic cert punch #2)
# ---------------------------------------------------------------------------


from cogs.diagnostic._platform_embeds import build_consistency_pages  # noqa: E402


def _big_section(name: str, status: SectionStatus) -> SectionResult:
    """A section large enough that ~5 of them fill one page near the soft cap."""
    return SectionResult(
        name=name,
        status=status,
        summary="X" * 600,
        details=("d" * 120, "e" * 120, "f" * 120),
        suggested_actions=("a" * 120, "b" * 120),
    )


def test_pages_single_when_report_fits_one_embed():
    pages = build_consistency_pages(
        _report(
            _section("a", SectionStatus.CLEAN),
            _section("b", SectionStatus.WARNING),
        ),
    )
    assert len(pages) == 1
    # Single page carries no "Page i/N" prefix.
    assert not (pages[0].footer.text or "").startswith("Page ")


def test_pages_split_keep_every_section_no_drop():
    sections = [_big_section(f"s{i}", SectionStatus.WARNING) for i in range(30)]
    pages = build_consistency_pages(_report(*sections))
    assert len(pages) > 1
    # No section is dropped: total fields across pages == section count.
    total_fields = sum(len(p.fields) for p in pages)
    assert total_fields == 30
    # Each page footer is labelled Page i/N and every page is under the hard limit.
    n = len(pages)
    for i, page in enumerate(pages, start=1):
        assert (page.footer.text or "").startswith(f"Page {i}/{n}")
        assert len(page.fields) <= _FIELD_HARD_CAP
        size = len(page.title or "") + len(page.description or "")
        size += len(page.footer.text or "")
        size += sum(len(f.name or "") + len(f.value or "") for f in page.fields)
        assert size < 6000


def test_pages_empty_report_returns_one_summary_page():
    pages = build_consistency_pages(_report())
    assert len(pages) == 1
    assert pages[0].fields == []
