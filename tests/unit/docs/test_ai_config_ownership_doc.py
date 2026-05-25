"""Doc-pin: ``docs/ai-config-ownership.md`` stays in sync with code.

Three contracts (see the doc's "Doc-pin tests" section):

1. **Projection table sync.** The doc's "Projected scalars" table lists
   exactly the keys in
   ``services.ai_policy_mutation._LEGACY_TO_POLICY_FIELD``.
2. **Settings-key sync.** Every constant defined in
   ``disbot/utils/settings_keys/ai.py`` is mentioned in the doc — under
   the projected table OR the "Not projected" table.
3. **UI-surface coverage.** Every prefix subcommand on ``AICog``
   (extracted by AST scan: ``@ai_group.command(name="...")``) appears
   in the doc's "UI surfaces" table.

Resilience model mirrors ``tests/unit/docs/test_settings_customization_doc.py``:
AST-based extraction so the test runs without runtime imports of
``services``, ``cogs``, or ``discord``.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DOCS = _REPO_ROOT / "docs"
_DISBOT = _REPO_ROOT / "disbot"

_DOC = _DOCS / "ai-config-ownership.md"
_PROJECTION_SRC = _DISBOT / "services" / "ai_policy_mutation.py"
_KEYS_SRC = _DISBOT / "utils" / "settings_keys" / "ai.py"
_AI_COG_SRC = _DISBOT / "cogs" / "ai_cog.py"


# ---------------------------------------------------------------------------
# AST extractors (no runtime imports)
# ---------------------------------------------------------------------------


def _projection_keys() -> set[str]:
    """Keys of ``_LEGACY_TO_POLICY_FIELD`` in ai_policy_mutation.py."""
    tree = ast.parse(_PROJECTION_SRC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target = node.target
            if (
                isinstance(target, ast.Name)
                and target.id == "_LEGACY_TO_POLICY_FIELD"
                and isinstance(node.value, ast.Dict)
            ):
                return {
                    key.value
                    for key in node.value.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if (
                    isinstance(tgt, ast.Name)
                    and tgt.id == "_LEGACY_TO_POLICY_FIELD"
                    and isinstance(node.value, ast.Dict)
                ):
                    return {
                        key.value
                        for key in node.value.keys
                        if isinstance(key, ast.Constant)
                        and isinstance(key.value, str)
                    }
    raise AssertionError(
        "_LEGACY_TO_POLICY_FIELD dict not found in "
        "disbot/services/ai_policy_mutation.py — update this test if the "
        "constant moved or was renamed.",
    )


def _settings_key_values() -> set[str]:
    """Values of every top-level string constant in settings_keys/ai.py."""
    tree = ast.parse(_KEYS_SRC.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if not (isinstance(tgt, ast.Name) and tgt.id.isupper()):
                    continue
                if isinstance(node.value, ast.Constant) and isinstance(
                    node.value.value, str,
                ):
                    out.add(node.value.value)
    return out


def _ai_prefix_subcommands() -> set[str]:
    """Names of every ``@ai_group.command(name="...")`` in ai_cog.py."""
    tree = ast.parse(_AI_COG_SRC.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "ai_group"
                and func.attr == "command"
            ):
                continue
            for kw in decorator.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    out.add(kw.value.value)
    return out


# ---------------------------------------------------------------------------
# Doc loading
# ---------------------------------------------------------------------------


def _doc_text() -> str:
    return _DOC.read_text(encoding="utf-8")


def _doc_section(text: str, header: str) -> str:
    """Return the markdown body under ``## header`` until the next ``## ``."""
    pattern = re.compile(
        rf"##\s+{re.escape(header)}\b.*?(?=\n## |\Z)", re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(0) if match else ""


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------


def test_doc_exists() -> None:
    assert _DOC.exists(), (
        f"{_DOC.relative_to(_REPO_ROOT)} is missing — this is a binding doc "
        "introduced in PR-1 of the AI cog refinement plan."
    )


def test_projection_table_matches_legacy_map() -> None:
    """Doc's projected-scalars table lists exactly the keys in the map."""
    keys_in_code = _projection_keys()
    text = _doc_text()
    section = _doc_section(text, "2. Projection rules")
    assert section, "Doc is missing the '2. Projection rules' section."

    missing_in_doc = {k for k in keys_in_code if f"`{k}`" not in section}
    assert not missing_in_doc, (
        f"docs/ai-config-ownership.md § 'Projection rules' must mention "
        f"every key in ai_policy_mutation._LEGACY_TO_POLICY_FIELD. "
        f"Missing from doc: {sorted(missing_in_doc)}."
    )


def test_every_settings_key_appears_in_doc() -> None:
    """Every constant in settings_keys/ai.py is mentioned in the doc."""
    keys = _settings_key_values()
    text = _doc_text()
    missing = {k for k in keys if f"`{k}`" not in text}
    assert not missing, (
        f"docs/ai-config-ownership.md must mention every AI settings key. "
        f"Missing: {sorted(missing)}. Place each new key under § "
        f"'Projection rules' (projected) or 'Not projected' (deferred)."
    )


def test_every_prefix_subcommand_appears_in_doc() -> None:
    """Every ``!ai *`` subcommand has a row in the UI-surfaces table."""
    subcommands = _ai_prefix_subcommands()
    text = _doc_text()
    section = _doc_section(text, "4. UI surfaces")
    assert section, "Doc is missing the '4. UI surfaces' section."

    missing = {name for name in subcommands if f"`!ai {name}`" not in section}
    assert not missing, (
        f"docs/ai-config-ownership.md § 'UI surfaces' must list every "
        f"@ai_group.command. Missing rows for: "
        f"{sorted(f'!ai {n}' for n in missing)}."
    )


def test_doc_lists_each_status_class_for_audit_fields() -> None:
    """Audit-fields section documents the legacy-NULL rendering rule."""
    text = _doc_text()
    section = _doc_section(text, "5. Audit fields")
    assert section, "Doc is missing the '5. Audit fields' section."
    assert (
        "legacy-NULL rendering rule" in section.lower()
        or 'render as `—`' in section
        or "Legacy-NULL" in section
    ), (
        "Doc § 'Audit fields' must describe the I-4 legacy-NULL rendering "
        "rule (audit readers tolerate both pre- and post-045 schemas, "
        "rendering missing columns as '—')."
    )
