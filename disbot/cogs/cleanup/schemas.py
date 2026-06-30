"""Cleanup SubsystemSchema (Settings Phase 2).

Cleanup's real configuration is **domain config**, not scalar settings:
prohibited-word policy + cleanup behavior live in the governance
``cleanup_policies`` tables (written only by
:class:`~governance.writes.GovernanceMutationPipeline`) and are operated
through the dedicated cleanup panel.  This schema declares that
destination as a :class:`~core.runtime.subsystem_schema.DomainPanelSpec`
so the Settings hub discovers cleanup as a *domain configuration group*
through the real declaration mechanism instead of the retired Phase 1
``DOMAIN_CONFIG_SUBSYSTEMS`` curated table (settings audit §10.2 step 4;
consolidated plan Batch 4).

It **also** declares the one genuine *scalar* cleanup behaviour — the
``!cleanuphistory`` spam-duplicate detection window — as a
:class:`~core.runtime.subsystem_schema.SettingSpec` with a
``numeric_presets`` config-input widget (completion-cert punch #4).  This
is an operational knob, not policy, so it is a legacy-KV scalar setting
(no migration) rather than a governance ``cleanup_policies`` row, mirroring
automod's ``spam_window_seconds``.  The default + bounds below are the
single source of truth shared with the consumer in ``cogs.cleanup_cog``
(pinned by ``test_cleanup_schemas``), so a spec default and the runtime
fallback can never silently drift.
"""

from __future__ import annotations

from core.runtime.subsystem_schema import (
    DomainPanelSpec,
    SettingSpec,
    SubsystemSchema,
)
from utils.settings_keys import CLEANUP_SPAM_WINDOW_SECONDS

# Spam-duplicate detection window (seconds) for the ``!cleanuphistory`` spam
# sweep.  Default is the historical hardcoded constant so every existing guild
# behaves byte-identically; bounds keep the window sane (1s..5min).
DEFAULT_SPAM_WINDOW_SECONDS = 15
MIN_SPAM_WINDOW_SECONDS = 1
MAX_SPAM_WINDOW_SECONDS = 300

# Edit authority borrows the cleanup *policy* configure capability: the spam
# window is cleanup behaviour, configured by the same staff who set cleanup
# policy.  (``cleanup.settings.configure`` is not a registered capability;
# ``cleanup.policy.configure`` is — see ``utils.subsystem_registry``.)
_CLEANUP_CAPABILITY = "cleanup.policy.configure"


def _validate_spam_window(value: object) -> None:
    # ``isinstance(True, int)`` is True, so guard the bool type explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"expected int, got {value!r}")
    if not (MIN_SPAM_WINDOW_SECONDS <= value <= MAX_SPAM_WINDOW_SECONDS):
        raise ValueError(
            f"must be between {MIN_SPAM_WINDOW_SECONDS} and {MAX_SPAM_WINDOW_SECONDS}",
        )


CLEANUP_SETTINGS: tuple[SettingSpec, ...] = (
    SettingSpec(
        name="spam_window_seconds",
        value_type=int,
        default=DEFAULT_SPAM_WINDOW_SECONDS,
        settings_key=CLEANUP_SPAM_WINDOW_SECONDS,
        capability_required=_CLEANUP_CAPABILITY,
        hint=(
            "Window (seconds) the `!cleanuphistory` spam sweep treats two "
            "near-identical messages from one author as duplicates."
        ),
        validator=_validate_spam_window,
        input_hint="numeric_presets",
        presets=(10, 15, 30),
    ),
)


CLEANUP_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="cleanup",
    settings=CLEANUP_SETTINGS,
    domain_panels=(
        DomainPanelSpec(
            name="Cleanup policies",
            description=(
                "Prohibited words and message-cleanup behavior — configured "
                "in the dedicated cleanup panel (governance-audited); the "
                "Settings group routes there."
            ),
            capability_required="cleanup.settings.configure",
        ),
    ),
    version=1,
)


def register_schemas() -> None:
    """Register the cleanup subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(CLEANUP_CONFIG_SCHEMA)


__all__ = [
    "CLEANUP_CONFIG_SCHEMA",
    "CLEANUP_SETTINGS",
    "DEFAULT_SPAM_WINDOW_SECONDS",
    "MAX_SPAM_WINDOW_SECONDS",
    "MIN_SPAM_WINDOW_SECONDS",
    "register_schemas",
]
