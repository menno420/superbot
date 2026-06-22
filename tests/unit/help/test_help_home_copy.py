"""Help Home embed copy tests.

After the routing-consistency PR, every hub row uses the same two-line
shape — purpose + typed entry command — with no ``Includes:`` line and
no internal metadata terms.
"""

from __future__ import annotations

from cogs.help_cog import build_categories_overview_embed


def test_no_includes_line_in_any_row():
    embed = build_categories_overview_embed(member_tier="owner")
    for field in embed.fields:
        assert (
            "Includes:" not in field.value
        ), f"row {field.name!r} contains an Includes: line"


def test_no_internal_metadata_terms():
    embed = build_categories_overview_embed(member_tier="owner")
    body = "\n".join(f.value for f in embed.fields)
    for term in ("primary_children", "cross_link_children", "parent_hub"):
        assert term not in body, f"internal term {term!r} leaked into Help Home"


def test_each_hub_row_has_uniform_two_line_shape():
    r"""Each hub row contains a one-line purpose followed by a
    ``→ \`!command\``` line. Pin the shape, not the exact wording.
    """
    embed = build_categories_overview_embed(member_tier="owner")
    for field in embed.fields:
        if "Advanced" in field.name:
            continue
        assert "→" in field.value, f"row {field.name!r} missing → entry line"
        lines = field.value.split("\n")
        assert len(lines) >= 2, f"row {field.name!r} has fewer than 2 lines"


def test_advanced_row_is_present_for_every_tier():
    for tier in ("user", "moderator", "administrator", "owner"):
        embed = build_categories_overview_embed(member_tier=tier)
        names = [f.name for f in embed.fields]
        assert any(
            "Advanced" in n for n in names
        ), f"Advanced row missing at tier={tier}"


def test_admin_tier_sees_all_hubs():
    embed = build_categories_overview_embed(member_tier="administrator")
    names = [f.name for f in embed.fields]
    # Help-menu regrouping (PR #1290): the seven top-level sections. Settings /
    # Platform / Server Management are now Server & Admin children, not hubs.
    for label in (
        "Games",
        "BTD6",
        "Economy",
        "Moderation",
        "Community",
        "Utility",
        "Server & Admin",
    ):
        assert any(label in n for n in names), f"hub {label} missing for admin"


def test_user_tier_hides_admin_only_hubs():
    embed = build_categories_overview_embed(member_tier="user")
    names = [f.name for f in embed.fields]
    for label in ("Admin", "Settings", "Platform"):
        assert not any(
            label in n for n in names
        ), f"admin-only hub {label} leaked into user-tier Help Home"
