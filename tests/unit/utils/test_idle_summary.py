"""Pure idle-summary tests — duration formatting + the "while you were away" blurb."""

from __future__ import annotations

import pytest

from utils import idle_summary


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "now"),
        (-5, "now"),
        (45, "45s"),
        (65, "1m 05s"),
        (125, "2m 05s"),
        (3600, "1h 00m"),
        (3780, "1h 03m"),
    ],
)
def test_format_duration(seconds, expected):
    assert idle_summary.format_duration(seconds) == expected


def test_summary_none_when_nothing_gained():
    assert (
        idle_summary.summarize_idle_gain(
            0,
            10_000,
            noun_singular="egg",
            noun_plural="eggs",
        )
        is None
    )
    assert (
        idle_summary.summarize_idle_gain(
            -3,
            10_000,
            noun_singular="egg",
            noun_plural="eggs",
        )
        is None
    )


def test_summary_pluralizes_and_formats_elapsed():
    one = idle_summary.summarize_idle_gain(
        1,
        45,
        noun_singular="egg",
        noun_plural="eggs",
    )
    assert one is not None
    assert "**1** egg." in one
    assert "45s" in one

    many = idle_summary.summarize_idle_gain(
        17,
        8040,  # 2h 14m
        noun_singular="egg",
        noun_plural="eggs",
    )
    assert many is not None
    assert "**17** eggs." in many
    assert "2h 14m" in many


def test_summary_appends_capped_note_only_when_capped():
    note = "The coop is full — collect!"
    capped = idle_summary.summarize_idle_gain(
        20,
        99_999,
        noun_singular="egg",
        noun_plural="eggs",
        capped=True,
        capped_note=note,
    )
    assert capped is not None and note in capped

    not_capped = idle_summary.summarize_idle_gain(
        5,
        600,
        noun_singular="egg",
        noun_plural="eggs",
        capped=False,
        capped_note=note,
    )
    assert not_capped is not None and note not in not_capped

    # Capped but no note supplied → no suffix, no crash.
    no_note = idle_summary.summarize_idle_gain(
        20,
        99_999,
        noun_singular="egg",
        noun_plural="eggs",
        capped=True,
    )
    assert no_note is not None and no_note.endswith("eggs.")
