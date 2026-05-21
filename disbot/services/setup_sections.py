"""Setup-wizard section registry.

The setup hub (`disbot/views/setup/hub.py`) historically hardcoded each
button + callback.  New sections required editing `hub.py`, which created
merge friction and made it impossible to deliver section work in isolated
PRs.  This module replaces that pattern with a small registry: a section
module declares a `SetupSection`, registers it at import time, and the hub
iterates the registry to render its buttons.

The registry is intentionally narrow:

* immutable section descriptions — once registered, a section's slug,
  label, style, and run callback do not change at runtime;
* deterministic ordering — sections are sorted by `(order, slug)` so the
  hub renders the same layout across processes;
* no IO — the registry stores plain Python objects, never touches the DB
  or Discord;
* test escape hatch — `unregister(slug)` lets tests register/clean up
  fixture sections without colliding with the production registrations.

The hub still owns authorization (owner-gate), error logging, and
`setup_session.mark_in_progress` calls.  Sections only own their own
domain logic and the SetupOperation batches they produce.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import discord

    from views.setup.hub import SetupHubView

RunCallback = Callable[["discord.Interaction", "SetupHubView"], Awaitable[None]]


@dataclass(frozen=True)
class SetupSection:
    """Declarative description of one button in the setup wizard hub.

    Attributes:
        slug: Stable identifier; used as the `setup_session.current_step`
            marker, as the button's `custom_id` suffix, and as the
            registry key.  Lowercase letters / digits / underscores only.
        label: Discord button label shown to the operator.  Limited to
            80 characters to match Discord's `Button.label` limit.
        style: Discord `ButtonStyle` for the button.
        run: Async callback invoked after the hub's owner-gate passes.
            Receives the interaction and the parent hub view so it can
            edit the same message, open follow-up views, or read shared
            state on the hub.
        emoji: Optional emoji shown alongside `label`.
        order: Sort key for hub layout; lower numbers render first.
            Production sections use multiples of 10 so contributors can
            slot new sections between existing ones without renumbering.
        step: Optional override for the `setup_session.current_step`
            marker written when the section is invoked.  Defaults to
            `slug`.
        op_kinds: SetupOperation kind strings this section can stage
            (e.g. ``frozenset({"bind_channel"})`` for `channels`).
            Used by `services.setup_progress.compute_section_status`
            to decide which draft rows belong to this section.  Empty
            for read-only sections (`server_scan`, `readiness`,
            `final_review`).
        description_if_skipped: Operator-facing one-liner that explains
            what happens if this section is skipped.  Rendered on the
            section card (PR 3) and surfaced by the hub embed.  Empty
            string means "no special skip impact documented yet".
        depths: Wizard depths in which this section appears.  The hub
            filters its button layout by the session's depth choice.
            Default is all three depths so unmigrated sections remain
            visible everywhere; sections opt into a narrower scope
            (e.g. quick-only or advanced-only) at registration.
    """

    slug: str
    label: str
    style: Any  # discord.ButtonStyle — Any to avoid import at module load
    run: RunCallback
    emoji: str | None = None
    order: int = 100
    step: str | None = None
    op_kinds: frozenset[str] = frozenset()
    description_if_skipped: str = ""
    depths: frozenset[str] = frozenset({"quick", "standard", "advanced"})

    @property
    def session_step(self) -> str:
        return self.step or self.slug


class SetupSectionRegistry:
    """Ordered registry of `SetupSection` instances.

    Sections register at module import time via the module-level
    `REGISTRY` instance.  Discovery happens implicitly when the
    `views.setup.sections` package is imported by `hub.py`.
    """

    _SLUG_MAX_LEN = 64
    _LABEL_MAX_LEN = 80

    def __init__(self) -> None:
        self._sections: dict[str, SetupSection] = {}

    def register(self, section: SetupSection) -> None:
        """Register `section`.  Raises `ValueError` on validation failure."""
        self._validate(section)
        if section.slug in self._sections:
            raise ValueError(
                f"SetupSection slug {section.slug!r} is already registered",
            )
        self._sections[section.slug] = section

    def unregister(self, slug: str) -> None:
        """Remove `slug` if present.  No-op if absent.  Test escape hatch."""
        self._sections.pop(slug, None)

    def get(self, slug: str) -> SetupSection | None:
        return self._sections.get(slug)

    def all(self) -> list[SetupSection]:
        """Return registered sections, sorted by `(order, slug)`."""
        return sorted(
            self._sections.values(),
            key=lambda s: (s.order, s.slug),
        )

    def for_depth(self, depth: str | None) -> list[SetupSection]:
        """Return registered sections that participate in ``depth``.

        ``depth`` ∈ ``{"quick", "standard", "advanced"}``.  Passing
        ``None`` (no choice persisted yet) returns every section so
        the hub still works in legacy / pre-picker code paths.
        Sorted by ``(order, slug)`` to match :meth:`all`.
        """
        if depth is None:
            return self.all()
        return [s for s in self.all() if depth in s.depths]

    def __contains__(self, slug: object) -> bool:
        return isinstance(slug, str) and slug in self._sections

    def __len__(self) -> int:
        return len(self._sections)

    @classmethod
    def _validate(cls, section: SetupSection) -> None:
        slug = section.slug
        if not isinstance(slug, str) or not slug:
            raise ValueError("SetupSection.slug must be a non-empty string")
        if len(slug) > cls._SLUG_MAX_LEN:
            raise ValueError(
                f"SetupSection.slug exceeds {cls._SLUG_MAX_LEN} chars: {slug!r}",
            )
        if not all(c.isalnum() or c == "_" for c in slug):
            raise ValueError(
                f"SetupSection.slug must be alphanumeric/underscore: {slug!r}",
            )
        if not section.label:
            raise ValueError("SetupSection.label must be non-empty")
        if len(section.label) > cls._LABEL_MAX_LEN:
            raise ValueError(
                f"SetupSection.label exceeds {cls._LABEL_MAX_LEN} chars: "
                f"{section.label!r}",
            )
        if not callable(section.run):
            raise ValueError("SetupSection.run must be callable")


REGISTRY = SetupSectionRegistry()
"""Process-wide registry of setup-wizard sections.

`hub.py` reads this to render the wizard layout.  Production section
modules register their sections at import time.  Tests can use
`REGISTRY.unregister(slug)` to clean up fixture sections.
"""


__all__ = [
    "REGISTRY",
    "RunCallback",
    "SetupSection",
    "SetupSectionRegistry",
]
