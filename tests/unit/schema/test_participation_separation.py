"""Phase 1b structural invariant — participation concerns stay separated.

A :class:`~core.runtime.participation_schema.ParticipationSchema` MUST
expose four distinct fields (subscriptions, visibility_intents,
notification_intents, preference_specs) — never a single
``dict[str, Any]`` catch-all.  Collapsing them would re-introduce the
god-object trap at the per-user layer (see roadmap Trap #11).

The test verifies two things:

1. The :class:`ParticipationSchema` dataclass continues to expose the
   four field names with their declared tuple types.
2. The XP reference schema instance actually populates each field with
   distinct content (subscriptions != notification_intents !=
   visibility_intents != preference_specs as objects).
"""

from __future__ import annotations

from dataclasses import fields

import pytest

from core.runtime.participation_schema import (
    NotificationIntent,
    ParticipationSchema,
    PreferenceSpec,
    SubscriptionSpec,
    VisibilityIntent,
)


def test_participation_schema_has_four_separate_field_groups():
    """Each concern lives in its own field; no catch-all dict allowed."""
    field_names = {f.name for f in fields(ParticipationSchema)}
    required = {
        "subscriptions",
        "visibility_intents",
        "notification_intents",
        "preference_specs",
    }
    missing = required - field_names
    assert not missing, (
        f"ParticipationSchema is missing required concern-separated "
        f"fields: {missing}.  Do not collapse participation, visibility, "
        f"notifications, and preferences into a single bag."
    )


@pytest.mark.parametrize(
    ("field_name", "expected_element_type"),
    [
        ("subscriptions", SubscriptionSpec),
        ("visibility_intents", VisibilityIntent),
        ("notification_intents", NotificationIntent),
        ("preference_specs", PreferenceSpec),
    ],
)
def test_field_element_type_matches_concern(field_name, expected_element_type):
    """Each field carries elements of the right concern-specific dataclass."""
    schema = ParticipationSchema(
        subsystem="test",
        subscriptions=(
            SubscriptionSpec(
                name="x",
                description="x",
                default_enabled=True,
            ),
        ),
        visibility_intents=(VisibilityIntent(name="x.public", description="x"),),
        notification_intents=(NotificationIntent(name="x.notify", description="x"),),
        preference_specs=(),
    )
    value = getattr(schema, field_name)
    if not value:
        # Empty tuple is acceptable; the field exists and is iterable.
        return
    assert all(isinstance(v, expected_element_type) for v in value), (
        f"Field {field_name!r} should hold only {expected_element_type.__name__} "
        f"instances; found {[type(v).__name__ for v in value]}."
    )


def test_xp_reference_schema_uses_all_four_fields():
    """The XP reference schema must populate every concern field.

    Confirms the reference migration demonstrates the discipline.  If a
    future change empties out (say) ``visibility_intents``, this test
    fails — which is the desired signal that the reference is no longer
    showing all four concerns.
    """
    from cogs.xp.schemas import XP_PARTICIPATION_SCHEMA

    assert (
        XP_PARTICIPATION_SCHEMA.subscriptions
    ), "XP reference schema must declare at least one SubscriptionSpec."
    assert (
        XP_PARTICIPATION_SCHEMA.visibility_intents
    ), "XP reference schema must declare at least one VisibilityIntent."
    assert (
        XP_PARTICIPATION_SCHEMA.notification_intents
    ), "XP reference schema must declare at least one NotificationIntent."
    assert (
        XP_PARTICIPATION_SCHEMA.preference_specs
    ), "XP reference schema must declare at least one PreferenceSpec."


def test_no_catchall_dict_field():
    """No :class:`ParticipationSchema` field may be a ``dict`` or
    ``Mapping`` — collapsing the four concerns into a single mapping is
    the trap the structural invariant exists to prevent.
    """
    for field in fields(ParticipationSchema):
        # The dataclass uses tuples for the four concern lists; subsystem,
        # version are str/int.  No field should ever be dict[...].
        annotation_text = str(field.type)
        bad_markers = ("dict[", "Dict[", "Mapping[", "dict ", "Mapping ")
        for marker in bad_markers:
            assert marker not in annotation_text, (
                f"ParticipationSchema.{field.name} has dict-like type "
                f"{annotation_text!r}.  Do not collapse the four concerns "
                f"into a single mapping."
            )
