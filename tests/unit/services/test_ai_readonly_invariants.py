"""Pin: AI snapshot + readiness services never mutate state.

Both ``services.ai_config_projection_service`` and
``services.ai_readiness_service`` are read orchestration layers. They
must compose existing services / repositories without calling any of
the documented mutation seams or side-effect entry points.

This test enforces the invariant by AST scan — no runtime imports of
the modules under test, so it runs without DB / Discord setup. The
forbidden-name list mirrors the rules in
``docs/ai-config-ownership.md`` § "Non-mutating invariant".
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

_SUBJECT_FILES: tuple[Path, ...] = (
    _DISBOT / "services" / "ai_config_projection_service.py",
    _DISBOT / "services" / "ai_readiness_service.py",
)

# Forbidden module-qualified mutation patterns. Each entry is
# ``(module_name, attribute)`` — matched against ``module.attribute(...)``
# call expressions. Module name is the immediate identifier on the left
# of the dot, mirroring this codebase's "from services import x; x.foo()"
# convention. Reference: docs/ai-config-ownership.md § "Non-mutating
# invariant (I-2)".
_FORBIDDEN_CALLS: frozenset[tuple[str, str]] = frozenset(
    {
        # AI policy writes
        ("ai_policy_mutation", "set_guild_policy"),
        ("ai_policy_mutation", "set_channel_policy"),
        ("ai_policy_mutation", "set_category_policy"),
        ("ai_policy_mutation", "set_role_policy"),
        ("ai_policy_mutation", "project_from_legacy_settings"),
        ("ai_db", "upsert_guild_policy"),
        ("ai_db", "upsert_channel_policy"),
        ("ai_db", "upsert_category_policy"),
        ("ai_db", "upsert_role_policy"),
        ("ai_db", "bump_generation"),
        ("ai_db", "delete_channel_policy"),
        ("ai_db", "upsert_instruction_profile"),
        ("ai_db", "delete_instruction_profile"),
        ("ai_db", "record_decision"),
        ("ai_db", "delete_for_guild"),
        # Instruction profile writes
        ("ai_instruction_mutation", "upsert_profile"),
        # Resolver-cache invalidation
        ("ai_natural_language_policy", "invalidate"),
        # Audit writes
        ("ai_decision_audit_service", "record"),
        # Memory mutation
        ("ai_conversation_service", "append"),
        ("ai_conversation_service", "forget_guild"),
        ("ai_conversation_service", "forget_channel"),
        # Gateway / provider call
        ("ai_gateway", "execute"),
        # Apply-side behavior preset
        ("ai_behavior_profile_service", "apply_preset"),
        ("ai_behavior_profile_service", "apply_preset_to_guild"),
    },
)


def _walk_qualified_calls(tree: ast.AST) -> list[tuple[str, str]]:
    """Return every ``(module, attribute)`` call expression in ``tree``.

    Only matches ``module.attribute(...)`` where ``module`` is a bare
    ``Name`` — that is the dominant pattern after ``from services import
    x``. Calls like ``some_local_list.append(...)`` are intentionally
    NOT captured here; ``some_local_list`` may match a forbidden
    attribute name (``append``) but it is not the mutation surface
    we are guarding.
    """
    pairs: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            pairs.append((func.value.id, func.attr))
    return pairs


@pytest.mark.parametrize("subject", _SUBJECT_FILES, ids=lambda p: p.name)
def test_no_forbidden_mutation_calls(subject: Path) -> None:
    """The subject must not invoke any of :data:`_FORBIDDEN_CALLS`."""
    source = subject.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = set(_walk_qualified_calls(tree))
    offenders = called & _FORBIDDEN_CALLS
    assert not offenders, (
        f"{subject.name} invokes forbidden mutation calls: "
        f"{sorted(offenders)}. The snapshot / readiness layer is read "
        "orchestration only — see docs/ai-config-ownership.md § "
        "'Non-mutating invariant (I-2)'."
    )


def test_subject_files_exist() -> None:
    """Tripwire: the AST scan is meaningless if the files have moved."""
    for subject in _SUBJECT_FILES:
        assert subject.exists(), (
            f"Expected subject file {subject.relative_to(_REPO_ROOT)} not found. "
            "Update tests/unit/services/test_ai_readonly_invariants.py if the "
            "module moved."
        )
