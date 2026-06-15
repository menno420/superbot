"""titles — pure earn-check + catalogue model (mining Slice F)."""

from __future__ import annotations

from utils.mining import skills, titles


def _ctx(*, mining=0, combat=0, fortune=0, crafting=0, max_depth=0, level=0):
    alloc = {
        skills.MINING: mining,
        skills.COMBAT: combat,
        skills.FORTUNE: fortune,
        skills.CRAFTING: crafting,
    }
    return titles.TitleContext(
        skills={b: p for b, p in alloc.items() if p > 0},
        max_depth=max_depth,
        level=level,
    )


def test_fresh_player_earns_nothing():
    assert titles.earned_titles(_ctx()) == ()


def test_unique_ids_and_lookup_round_trips():
    ids = [t.id for t in titles.ALL_TITLES]
    assert len(ids) == len(set(ids))  # ids are unique
    for t in titles.ALL_TITLES:
        assert titles.get_title(t.id) is t
    assert titles.get_title("not_a_title") is None
    assert titles.get_title(None) is None


def test_mastery_title_needs_the_branch_at_cap():
    cap = skills.PER_BRANCH_CAP
    assert not titles.is_earned("the_deep", _ctx(mining=cap - 1))
    assert titles.is_earned("the_deep", _ctx(mining=cap))
    # the mining-mastery title doesn't fire on a different branch maxed.
    assert not titles.is_earned("the_deep", _ctx(combat=cap))


def test_each_branch_maps_to_its_own_mastery_title():
    cap = skills.PER_BRANCH_CAP
    assert titles.is_earned("ironclad", _ctx(combat=cap))
    assert titles.is_earned("the_lucky", _ctx(fortune=cap))
    assert titles.is_earned("master_smith", _ctx(crafting=cap))


def test_depth_milestones_are_thresholds():
    assert not titles.is_earned("spelunker", _ctx(max_depth=0))
    assert titles.is_earned("spelunker", _ctx(max_depth=1))
    assert titles.is_earned("deepdelver", _ctx(max_depth=2))
    assert titles.is_earned("coreborn", _ctx(max_depth=3))
    # a deeper world (future P6 grid) still satisfies the shallower milestones.
    deep = _ctx(max_depth=9)
    assert titles.is_earned("spelunker", deep)
    assert titles.is_earned("coreborn", deep)


def test_level_milestones_are_thresholds():
    assert not titles.is_earned("veteran", _ctx(level=9))
    assert titles.is_earned("veteran", _ctx(level=10))
    assert titles.is_earned("legend", _ctx(level=25))


def test_earned_titles_preserves_catalogue_order():
    cap = skills.PER_BRANCH_CAP
    ctx = _ctx(mining=cap, max_depth=3, level=25)
    earned_ids = [t.id for t in titles.earned_titles(ctx)]
    catalogue_ids = [t.id for t in titles.ALL_TITLES]
    # earned is a subsequence of the catalogue order.
    assert earned_ids == [i for i in catalogue_ids if i in set(earned_ids)]
    assert "the_deep" in earned_ids and "coreborn" in earned_ids


def test_display_includes_emoji_and_label():
    t = titles.get_title("coreborn")
    assert titles.display(t) == f"{t.emoji} {t.label}"
