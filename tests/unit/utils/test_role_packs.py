"""The curated role-pack catalogue (utils.role_packs) is well-formed."""

from __future__ import annotations

import pytest

from utils import role_packs
from views.roles._helpers import _parse_color


def test_packs_nonempty_with_unique_keys():
    packs = role_packs.packs()
    assert packs, "the catalogue must offer at least one pack"
    keys = [p.key for p in packs]
    assert len(keys) == len(set(keys)), "pack keys must be unique"


def test_each_pack_has_roles_within_select_limit():
    for pack in role_packs.packs():
        assert pack.roles, f"pack {pack.key!r} has no roles"
        # Discord's select-option cap (a single multiselect page).
        assert len(pack.roles) <= 25, f"pack {pack.key!r} exceeds 25 roles"
        names = [r.name for r in pack.roles]
        assert len(names) == len(set(names)), f"pack {pack.key!r} has duplicate names"


def test_every_pack_role_colour_parses():
    for pack in role_packs.packs():
        for role in pack.roles:
            # A bad hex would raise — the bulk-create flow relies on this.
            assert _parse_color(role.color) is not None


def test_get_pack_resolves_and_handles_unknown():
    first = role_packs.packs()[0]
    assert role_packs.get_pack(first.key) is first
    assert role_packs.get_pack("does-not-exist") is None
    assert role_packs.get_pack(None) is None


@pytest.mark.parametrize("key", ["essentials", "gaming", "staff", "pronouns"])
def test_expected_core_packs_present(key: str):
    assert role_packs.get_pack(key) is not None


def test_event_rsvp_pack_offers_the_signup_options():
    """The one-tap RSVP role set that pairs with the Event RSVP menu template."""
    pack = role_packs.get_pack("event_rsvp")
    assert pack is not None
    names = {r.name for r in pack.roles}
    assert names == {"Going", "Maybe", "Can't make it"}


def test_role_presets_are_derived_from_the_essentials_pack():
    """The single-create dropdown (`ROLE_PRESETS`) and the multi-select Essentials
    pack share one data source, so they never drift apart.
    """
    from views.roles._helpers import ROLE_PRESETS

    essentials = role_packs.get_pack("essentials")
    assert essentials is not None
    assert [p.name for p in ROLE_PRESETS] == [r.name for r in essentials.roles]
    # Enlarged well past the original six-name starter set.
    assert len(ROLE_PRESETS) >= 10
