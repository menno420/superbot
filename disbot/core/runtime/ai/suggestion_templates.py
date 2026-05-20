"""Suggestion templates for future AI-assisted SuperBot services.

Inert scaffold: not imported by production runtime yet.

Templates describe what each AI task may suggest and which deterministic
service should own any eventual state change.  They are intentionally
small so future UI panels can render consistent previews.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.runtime.ai.contracts import AISuggestionKind, AITask

OperationOwner = Literal[
    "read_only",
    "settings_mutation",
    "binding_mutation",
    "resource_provisioning",
    "setup_operations",
    "moderation_review",
]


@dataclass(frozen=True)
class SuggestionTemplate:
    """Declarative template for one AI suggestion family."""

    task: AITask
    kind: AISuggestionKind
    owner: OperationOwner
    title: str
    description: str
    confirmation_required: bool = True
    default_enabled: bool = False


TEMPLATES: tuple[SuggestionTemplate, ...] = (
    SuggestionTemplate(
        task=AITask.SETUP_SUGGEST,
        kind=AISuggestionKind.BINDING_CHANGE,
        owner="setup_operations",
        title="Setup binding recommendation",
        description="Suggests a channel or role binding for a registered subsystem.",
    ),
    SuggestionTemplate(
        task=AITask.SETUP_SUGGEST,
        kind=AISuggestionKind.RESOURCE_PROVISION,
        owner="setup_operations",
        title="Setup resource recommendation",
        description="Suggests a missing channel, role, or category for setup review.",
    ),
    SuggestionTemplate(
        task=AITask.PLATFORM_EXPLAIN_STATUS,
        kind=AISuggestionKind.DIAGNOSTIC_NEXT_STEP,
        owner="read_only",
        title="Platform status explanation",
        description="Explains diagnostics output and suggests the next command to inspect.",
        confirmation_required=False,
    ),
    SuggestionTemplate(
        task=AITask.LOGS_TRIAGE,
        kind=AISuggestionKind.DIAGNOSTIC_NEXT_STEP,
        owner="read_only",
        title="Log triage finding",
        description="Groups recent runtime signals into an operator-facing incident summary.",
        confirmation_required=False,
    ),
    SuggestionTemplate(
        task=AITask.SETTINGS_PROPOSE,
        kind=AISuggestionKind.SETTING_CHANGE,
        owner="settings_mutation",
        title="Settings change proposal",
        description="Suggests a scalar setting change that must pass SettingsMutationPipeline.",
    ),
    SuggestionTemplate(
        task=AITask.HELP_ANSWER,
        kind=AISuggestionKind.HELP_NAVIGATION,
        owner="read_only",
        title="Help navigation answer",
        description="Suggests the most relevant command panel or help surface.",
        confirmation_required=False,
        default_enabled=True,
    ),
    SuggestionTemplate(
        task=AITask.MODERATION_ASSIST,
        kind=AISuggestionKind.MODERATION_REVIEW,
        owner="moderation_review",
        title="Moderation review suggestion",
        description="Classifies a moderation situation for human review only.",
    ),
)


def templates_for_task(task: AITask) -> tuple[SuggestionTemplate, ...]:
    """Return templates matching `task`."""

    return tuple(template for template in TEMPLATES if template.task == task)


__all__ = ["OperationOwner", "SuggestionTemplate", "TEMPLATES", "templates_for_task"]
