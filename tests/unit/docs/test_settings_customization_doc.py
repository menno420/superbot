"""Stale-doc guard for the Settings & Customization Manager S0 docs.

Tests three docs:

- ``docs/setup-platform/settings-customization-command-map.md``
- ``docs/setup-platform/settings-customization-roadmap.md``
- ``docs/setup-platform/resource-provisioning-overview.md``

Resilience model (mirrors ``tests/unit/docs/test_phase_2_readiness_doc.py``):
case-insensitive substring assertions tied to source-of-truth constants and
AST scans of schema files. **No runtime population of
``subsystem_schema._REGISTRY`` (or any other runtime registry) is required.**
Source-of-truth constants — ``SUBSYSTEMS``, ``INITIAL_EXTENSIONS``,
``SETUP_READINESS_BLOCKERS``, and ``settings_keys.__all__`` — are extracted
via AST parsing of their declaration files, so the test runs in any
environment without needing dotenv, discord.py, or any other bot runtime
dependency installed.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"
_DOCS = _REPO_ROOT / "docs"

_COMMAND_MAP = _DOCS / "setup-platform" / "settings-customization-command-map.md"
_ROADMAP = _DOCS / "setup-platform" / "settings-customization-roadmap.md"
_RPM_OVERVIEW = _DOCS / "setup-platform" / "resource-provisioning-overview.md"

_SUBSYSTEM_REGISTRY_SRC = _DISBOT / "utils" / "subsystem_registry.py"
_CONFIG_SRC = _DISBOT / "config.py"
_PLATFORM_CONSISTENCY_SRC = _DISBOT / "services" / "platform_consistency.py"
_SETUP_BLOCKERS_SRC = _DISBOT / "services" / "setup_blockers.py"
_SETTINGS_KEYS_INIT_SRC = _DISBOT / "utils" / "settings_keys" / "__init__.py"

# 24-field template labels (snake_case form). The doc may format them with
# any markdown markup as long as the snake_case token appears.
_FIELD_LABELS: tuple[str, ...] = (
    "cog_module",
    "subsystem",
    "current_commands",
    "current_command_groups",
    "current_command_panel_or_menu",
    "help_menu_discoverable",
    "dedicated_panel_command",
    "help_menu_direct_navigation_hook",
    "existing_settingspec_declarations",
    "existing_settings_keys",
    "existing_bindingspec_entries",
    "existing_resourcerequirement_entries",
    "current_access_policy_behavior",
    "hardcoded_or_env_only_behavior",
    "missing_customization_commands",
    "missing_settings_pages",
    "missing_menu_buttons_selects_modals",
    "setting_class_per_value",
    "target_settings_manager_page",
    "target_mutation_path",
    "target_help_or_menu_route",
    "provisionable_resources",
    "priority",
    "recommended_pr_phase",
)

# 12 numbered stages + 2 bridge milestones + S12 planning = 15 total.
_MILESTONES: tuple[str, ...] = (
    "S0",
    "S1",
    "S2",
    "S2.5",
    "S3",
    "S4",
    "S4.5",
    "S5",
    "S6",
    "S7",
    "S8",
    "S9",
    "S10",
    "S11",
    "S12",
)


# ---------------------------------------------------------------------------
# AST-based source-of-truth extractors. No imports — no runtime deps.
# ---------------------------------------------------------------------------


def _module_assignment(path: Path, name: str) -> ast.AST:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == name:
                    return node.value
        elif isinstance(node, ast.AnnAssign):
            tgt = node.target
            if isinstance(tgt, ast.Name) and tgt.id == name and node.value is not None:
                return node.value
    raise AssertionError(f"Source-of-truth assignment {name!r} not found in {path}")


def _subsystem_keys() -> tuple[str, ...]:
    """Statically extract SUBSYSTEMS keys from subsystem_registry.py."""
    value = _module_assignment(_SUBSYSTEM_REGISTRY_SRC, "SUBSYSTEMS")
    assert isinstance(value, ast.Dict), "SUBSYSTEMS must be a dict literal"
    names: list[str] = []
    for key in value.keys:
        assert isinstance(key, ast.Constant) and isinstance(
            key.value, str
        ), "SUBSYSTEMS keys must all be string literals"
        names.append(key.value)
    return tuple(names)


def _initial_extensions() -> tuple[str, ...]:
    """Statically extract INITIAL_EXTENSIONS entries from config.py."""
    value = _module_assignment(_CONFIG_SRC, "INITIAL_EXTENSIONS")
    assert isinstance(
        value, (ast.Tuple, ast.List)
    ), "INITIAL_EXTENSIONS must be a tuple/list literal"
    out: list[str] = []
    for elt in value.elts:
        assert isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        out.append(elt.value)
    return tuple(out)


def _setup_readiness_blockers() -> tuple[str, ...]:
    """Statically extract the canonical blocker IDs.

    PR-03: ``SETUP_READINESS_BLOCKERS`` is now derived from
    ``services.setup_blockers.BLOCKERS`` (a tuple of ``BlockerSpec``
    instances with literal ``id="..."`` arguments).  This helper
    parses the BlockerSpec(...) call expressions and pulls the ``id``
    keyword argument from each — keeping the doc-test fully static
    (no code execution).
    """
    tree = ast.parse(_SETUP_BLOCKERS_SRC.read_text(encoding="utf-8"))
    blockers_value: ast.AST | None = None
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            tgt = node.target
            if (
                isinstance(tgt, ast.Name)
                and tgt.id == "BLOCKERS"
                and node.value is not None
            ):
                blockers_value = node.value
                break
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "BLOCKERS":
                    blockers_value = node.value
                    break
            if blockers_value is not None:
                break
    assert isinstance(
        blockers_value, (ast.Tuple, ast.List)
    ), "setup_blockers.BLOCKERS must be a tuple/list literal of BlockerSpec(...) calls"
    out: list[str] = []
    for elt in blockers_value.elts:
        assert isinstance(
            elt, ast.Call
        ), "BLOCKERS entries must be BlockerSpec(...) calls"
        # id may be passed positionally or as a keyword; canonical form
        # in setup_blockers.py is keyword.
        spec_id: str | None = None
        for kw in elt.keywords:
            if kw.arg == "id" and isinstance(kw.value, ast.Constant):
                spec_id = kw.value.value
                break
        if spec_id is None and elt.args:
            first = elt.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                spec_id = first.value
        assert spec_id is not None, f"BlockerSpec call missing id: {ast.dump(elt)}"
        out.append(spec_id)
    return tuple(out)


def _settings_keys_exposed() -> tuple[str, ...]:
    """Statically extract __all__ from utils/settings_keys/__init__.py."""
    value = _module_assignment(_SETTINGS_KEYS_INIT_SRC, "__all__")
    assert isinstance(
        value, (ast.Tuple, ast.List)
    ), "__all__ must be a tuple/list literal"
    out: list[str] = []
    for elt in value.elts:
        assert isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        out.append(elt.value)
    return tuple(out)


def _schema_files() -> list[Path]:
    """Statically locate schema source files. No imports, no execution."""
    paths: list[Path] = []
    paths.extend(_DISBOT.glob("cogs/**/schemas.py"))
    paths.extend(_DISBOT.glob("services/*_schemas.py"))
    return sorted(paths)


def _extract_call_name_arg(source: str, call_name: str) -> list[str]:
    """AST-scan source for ``call_name(name="...", ...)`` literals and
    return each ``name`` keyword argument value. No code execution."""
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        matched = False
        if isinstance(fn, ast.Name) and fn.id == call_name:
            matched = True
        elif isinstance(fn, ast.Attribute) and fn.attr == call_name:
            matched = True
        if not matched:
            continue
        for kw in node.keywords:
            if (
                kw.arg == "name"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ):
                names.append(kw.value.value)
    return names


def _schema_has_call(source: str, call_name: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id == call_name:
            return True
        if isinstance(fn, ast.Attribute) and fn.attr == call_name:
            return True
    return False


def _subsystem_for_schema_path(path: Path) -> str | None:
    """Infer subsystem name from a schema source path."""
    if path.parent.parent.name == "cogs":
        return path.parent.name
    if path.parent.name == "services" and path.name.endswith("_schemas.py"):
        return path.name.removesuffix("_schemas.py")
    return None


def _section_for(text: str, subsystem: str) -> str:
    """Return the slice of ``text`` between ``### <subsystem>`` and the
    next ``### `` heading (or end of doc)."""
    header = f"### {subsystem}"
    idx = text.find(header)
    if idx < 0:
        return ""
    next_idx = text.find("\n### ", idx + len(header))
    return text[idx:] if next_idx < 0 else text[idx:next_idx]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def command_map_text() -> str:
    return _COMMAND_MAP.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def roadmap_text() -> str:
    return _ROADMAP.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def rpm_overview_text() -> str:
    return _RPM_OVERVIEW.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Files exist
# ---------------------------------------------------------------------------


def test_command_map_file_exists():
    assert _COMMAND_MAP.is_file(), f"Missing doc: {_COMMAND_MAP}"


def test_roadmap_file_exists():
    assert _ROADMAP.is_file(), f"Missing doc: {_ROADMAP}"


def test_rpm_overview_file_exists():
    assert _RPM_OVERVIEW.is_file(), f"Missing doc: {_RPM_OVERVIEW}"


# ---------------------------------------------------------------------------
# Command-map doc — per-subsystem coverage
# ---------------------------------------------------------------------------


def test_every_subsystem_has_section(command_map_text: str):
    """Every SUBSYSTEMS key must have a `### <subsystem>` section."""
    missing = [
        name for name in _subsystem_keys() if f"### {name}" not in command_map_text
    ]
    assert (
        not missing
    ), "Command-map doc missing per-subsystem sections for: " + ", ".join(missing)


def test_every_loaded_cog_referenced(command_map_text: str):
    """Every cog module in INITIAL_EXTENSIONS must be referenced by base name."""
    missing: list[str] = []
    for ext in _initial_extensions():
        base = ext.rsplit(".", 1)[-1]
        if base not in command_map_text:
            missing.append(base)
    assert not missing, "Command-map doc missing cog references: " + ", ".join(missing)


def test_all_24_field_labels_present(command_map_text: str):
    lowered = command_map_text.lower()
    missing = [label for label in _FIELD_LABELS if label not in lowered]
    assert (
        not missing
    ), "Command-map doc missing 24-field-template labels: " + ", ".join(missing)


def test_setup_readiness_blockers_referenced(command_map_text: str):
    """Every entry of SETUP_READINESS_BLOCKERS must appear in the doc, in
    humanised form (snake_case → space-separated) or as the raw tag."""
    lowered = command_map_text.lower()
    missing: list[str] = []
    for blocker in _setup_readiness_blockers():
        humanised = blocker.replace("_", " ")
        if humanised not in lowered and blocker not in lowered:
            missing.append(blocker)
    assert (
        not missing
    ), "Doc / SETUP_READINESS_BLOCKERS sync gap — add these to the doc: " + ", ".join(
        missing
    )


def test_existing_settings_keys_constants_referenced(command_map_text: str):
    """Every public constant exposed by ``utils.settings_keys`` must be
    referenced somewhere in the command-map doc."""
    exposed = _settings_keys_exposed()
    missing = [c for c in exposed if c not in command_map_text]
    assert not missing, "Command-map doc missing settings-keys constants: " + ", ".join(
        missing
    )


# ---------------------------------------------------------------------------
# Command-map doc — schema-declared specs surface
# ---------------------------------------------------------------------------


def test_schema_settingspec_names_appear(command_map_text: str):
    """Every ``SettingSpec(name="...")`` literal in disbot schemas must
    appear in the doc."""
    missing: list[str] = []
    for path in _schema_files():
        source = path.read_text(encoding="utf-8")
        for name in _extract_call_name_arg(source, "SettingSpec"):
            if name not in command_map_text:
                missing.append(f"{name} (from {path.name})")
    assert not missing, "Command-map doc missing SettingSpec names: " + ", ".join(
        missing
    )


def test_schema_bindingspec_names_appear(command_map_text: str):
    """Every ``BindingSpec(name="...")`` literal in disbot schemas must
    appear in the doc."""
    missing: list[str] = []
    for path in _schema_files():
        source = path.read_text(encoding="utf-8")
        for name in _extract_call_name_arg(source, "BindingSpec"):
            if name not in command_map_text:
                missing.append(f"{name} (from {path.name})")
    assert not missing, "Command-map doc missing BindingSpec names: " + ", ".join(
        missing
    )


def test_schema_resource_requirements_have_provisioning_section(
    command_map_text: str,
):
    """Every schema declaring at least one ``ResourceRequirement(...)`` must
    correspond to a section whose ``provisionable_resources`` field is not
    'none'."""
    gaps: list[str] = []
    for path in _schema_files():
        source = path.read_text(encoding="utf-8")
        if not _schema_has_call(source, "ResourceRequirement"):
            continue
        subsystem = _subsystem_for_schema_path(path)
        if subsystem is None:
            continue
        section = _section_for(command_map_text, subsystem)
        if not section:
            gaps.append(f"{subsystem}: section missing")
            continue
        prov_line = next(
            (
                ln
                for ln in section.splitlines()
                if "provisionable_resources" in ln.lower()
            ),
            None,
        )
        if prov_line is None:
            gaps.append(f"{subsystem}: provisionable_resources field missing")
            continue
        stripped = prov_line.lower().rstrip(" .")
        if stripped.endswith(": none") or stripped.endswith("none**"):
            gaps.append(
                f"{subsystem}: schema declares ResourceRequirement but "
                f"provisionable_resources says 'none'"
            )
    assert not gaps, "Provisioning subsection gaps: " + "; ".join(gaps)


def test_bindings_route_through_declared_pipelines(command_map_text: str):
    """For every cog section listing a BindingSpec via schema, the section's
    ``target_mutation_path`` field must mention ``BindingMutationPipeline``
    or ``ResourceProvisioningPipeline`` (or both)."""
    gaps: list[str] = []
    schema_binding_subsystems: set[str] = set()
    for path in _schema_files():
        source = path.read_text(encoding="utf-8")
        if not _schema_has_call(source, "BindingSpec"):
            continue
        subsystem = _subsystem_for_schema_path(path)
        if subsystem is not None:
            schema_binding_subsystems.add(subsystem)

    for subsystem in sorted(schema_binding_subsystems):
        section = _section_for(command_map_text, subsystem)
        if not section:
            gaps.append(f"{subsystem}: section missing")
            continue
        section_lc = section.lower()
        if "target_mutation_path" not in section_lc:
            gaps.append(f"{subsystem}: target_mutation_path field missing")
            continue
        if (
            "bindingmutationpipeline" not in section_lc
            and "resourceprovisioningpipeline" not in section_lc
        ):
            gaps.append(
                f"{subsystem}: has BindingSpec but target_mutation_path "
                f"mentions neither BindingMutationPipeline nor "
                f"ResourceProvisioningPipeline"
            )
    assert not gaps, "Binding pipeline routing gaps: " + "; ".join(gaps)


# ---------------------------------------------------------------------------
# Roadmap doc — milestones, lanes, pipelines
# ---------------------------------------------------------------------------


def test_roadmap_lists_all_15_milestones(roadmap_text: str):
    missing = [m for m in _MILESTONES if m not in roadmap_text]
    assert not missing, "Roadmap doc missing milestone codes: " + ", ".join(missing)


def test_roadmap_names_all_pipelines(roadmap_text: str):
    expected = (
        "BindingMutationPipeline",
        "GovernanceMutationPipeline",
        "ParticipationMutationPipeline",
        "RolloutMutationPipeline",
        "SettingsMutationPipeline",
        "ResourceProvisioningPipeline",
    )
    missing = [p for p in expected if p not in roadmap_text]
    assert not missing, "Roadmap doc missing pipeline names: " + ", ".join(missing)


def test_roadmap_names_three_lanes(roadmap_text: str):
    lowered = roadmap_text.lower()
    expected_terms = ("settings lane", "binding lane", "resource provisioning lane")
    missing = [t for t in expected_terms if t not in lowered]
    assert not missing, "Roadmap doc missing lane labels: " + ", ".join(missing)


def test_roadmap_describes_15_milestones_count(roadmap_text: str):
    """The roadmap text must explain that there are 15 milestones (12 numbered
    plus 2 bridge milestones plus S12 planning) — not 12, not 14."""
    lowered = roadmap_text.lower()
    assert "15 roadmap milestones" in lowered or "15-milestone" in lowered, (
        "Roadmap doc must describe the milestone count as 15 "
        "(12 numbered stages plus two bridge milestones plus S12 planning)."
    )


# ---------------------------------------------------------------------------
# RPM overview doc — 11-step contract, hard rules, presets
# ---------------------------------------------------------------------------


def test_rpm_overview_lists_eleven_steps(rpm_overview_text: str):
    """All 11 contract steps must appear as numbered list items."""
    for n in range(1, 12):
        token = f"{n}. "
        assert (
            token in rpm_overview_text
        ), f"RPM overview missing 11-step contract item {n}."


def test_rpm_overview_no_silent_auto_create(rpm_overview_text: str):
    lowered = rpm_overview_text.lower()
    assert (
        "silent auto-create" in lowered
    ), "RPM overview must explicitly state the no-silent-auto-create rule."


def test_rpm_overview_reserves_logging_routes_future(rpm_overview_text: str):
    lowered = rpm_overview_text.lower()
    assert (
        "logging_routes" in lowered
    ), "RPM overview must reserve the future logging_routes table."
    assert (
        "not in v1 scope" in lowered
    ), "RPM overview must mark logging_routes as not in v1 scope."


def test_rpm_overview_lists_standard_channel_presets(rpm_overview_text: str):
    expected = (
        "mod-logs",
        "cleanup-logs",
        "log-channel-debug",
        "log-channel-info",
        "log-channel-warning",
        "log-channel-error",
        "log-channel-critical",
    )
    missing = [p for p in expected if p not in rpm_overview_text]
    assert not missing, "RPM overview missing channel-name presets: " + ", ".join(
        missing
    )


def test_rpm_overview_names_binding_mutation_pipeline(rpm_overview_text: str):
    """The overview must make clear that RPM delegates to BindingMutationPipeline
    at step 8, never writes subsystem_bindings directly."""
    assert (
        "BindingMutationPipeline" in rpm_overview_text
    ), "RPM overview must name BindingMutationPipeline as the delegated writer."
    lowered = rpm_overview_text.lower()
    assert "subsystem_bindings" in lowered, (
        "RPM overview must reference subsystem_bindings as the table it does "
        "NOT write directly."
    )
