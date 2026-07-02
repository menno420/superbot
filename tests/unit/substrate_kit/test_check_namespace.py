"""Tests for the AST namespace / shadowing guard (Lane B6).

Covers in-module shadowing, cross-package public collisions (with the
__init__ re-export exemption), reserved-name violations, syntax-error
handling, and the dogfood check: the kit's own engine tree must be
collision-free when treated as ONE namespace (the dist concatenation rule).
"""

import ast
from pathlib import Path

from engine.checks.check_namespace import check_namespace

_ENGINE_SRC = Path(__file__).resolve().parents[3] / "substrate-kit" / "src" / "engine"


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# (1) In-module shadowing
# ---------------------------------------------------------------------------


def test_same_name_twice_in_one_module_fires(tmp_path):
    _write(
        tmp_path / "pkg" / "mod.py",
        "def helper():\n    return 1\n\n\ndef helper():\n    return 2\n",
    )
    findings = check_namespace([tmp_path])
    assert len(findings) == 1
    f = findings[0]
    assert f.kind == "namespace" and f.path == "pkg/mod.py"
    assert "`helper`" in f.message and "shadows" in f.message


def test_class_shadowing_a_def_fires(tmp_path):
    _write(tmp_path / "m.py", "def thing():\n    pass\n\n\nclass thing:\n    pass\n")
    findings = check_namespace([tmp_path])
    assert len(findings) == 1 and "`thing`" in findings[0].message


def test_distinct_names_do_not_fire(tmp_path):
    _write(tmp_path / "m.py", "def a():\n    pass\n\n\ndef b():\n    pass\n")
    assert check_namespace([tmp_path]) == []


def test_nested_defs_are_not_top_level(tmp_path):
    # A method named like a module function is fine — only top level counts.
    _write(
        tmp_path / "m.py",
        "def run():\n    pass\n\n\nclass Cog:\n    def run(self):\n        pass\n",
    )
    assert check_namespace([tmp_path]) == []


# ---------------------------------------------------------------------------
# (2) Cross-module public collision within one package
# ---------------------------------------------------------------------------


def test_public_name_in_two_modules_of_one_package_fires(tmp_path):
    _write(tmp_path / "pkg" / "a.py", "def build():\n    pass\n")
    _write(tmp_path / "pkg" / "b.py", "def build():\n    pass\n")
    findings = check_namespace([tmp_path])
    assert len(findings) == 1
    assert findings[0].kind == "namespace"
    assert "`build`" in findings[0].message
    assert "pkg/a.py" in findings[0].message and "pkg/b.py" in findings[0].message


def test_init_reexport_def_is_exempt(tmp_path):
    _write(tmp_path / "pkg" / "__init__.py", "def build():\n    pass\n")
    _write(tmp_path / "pkg" / "a.py", "def build():\n    pass\n")
    assert check_namespace([tmp_path]) == []


def test_private_names_do_not_collide_across_modules(tmp_path):
    _write(tmp_path / "pkg" / "a.py", "def _helper():\n    pass\n")
    _write(tmp_path / "pkg" / "b.py", "def _helper():\n    pass\n")
    assert check_namespace([tmp_path]) == []


def test_same_name_in_different_packages_is_fine(tmp_path):
    _write(tmp_path / "one" / "a.py", "def build():\n    pass\n")
    _write(tmp_path / "two" / "b.py", "def build():\n    pass\n")
    assert check_namespace([tmp_path]) == []


# ---------------------------------------------------------------------------
# (3) Reserved names
# ---------------------------------------------------------------------------


def test_reserved_name_outside_canonical_module_fires(tmp_path):
    _write(tmp_path / "lib" / "state.py", "class Backend:\n    pass\n")
    _write(tmp_path / "other.py", "class Backend:\n    pass\n")
    findings = check_namespace(
        [tmp_path],
        reserved={"Backend": "lib/state.py"},
    )
    assert len(findings) == 1
    f = findings[0]
    assert f.path == "other.py" and f.kind == "namespace"
    assert "reserved name `Backend`" in f.message and "lib/state.py" in f.message


def test_reserved_name_in_canonical_module_is_clean(tmp_path):
    _write(tmp_path / "lib" / "state.py", "class Backend:\n    pass\n")
    assert check_namespace([tmp_path], reserved={"Backend": "lib/state.py"}) == []


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------


def test_syntax_error_becomes_parse_finding_not_exception(tmp_path):
    _write(tmp_path / "broken.py", "def oops(:\n")
    _write(tmp_path / "fine.py", "def ok():\n    pass\n")
    findings = check_namespace([tmp_path])
    assert len(findings) == 1
    assert findings[0].kind == "namespace-parse"
    assert findings[0].path == "broken.py"


def test_missing_root_and_single_file_root(tmp_path):
    assert check_namespace([tmp_path / "nope"]) == []
    single = tmp_path / "solo.py"
    _write(single, "def a():\n    pass\n\n\ndef a():\n    pass\n")
    findings = check_namespace([single])
    assert len(findings) == 1 and findings[0].path == "solo.py"


# ---------------------------------------------------------------------------
# Dogfood — the engine tree as ONE namespace (dist concatenation rule)
# ---------------------------------------------------------------------------


def test_engine_tree_has_no_cross_module_top_level_collisions():
    """dist/bootstrap.py concatenates every engine module into one namespace,
    so a top-level def/class name defined in two different modules would
    silently shadow across files. Assert the whole tree is collision-free.
    """
    owners: dict[str, str] = {}
    collisions: list[str] = []
    for py in sorted(_ENGINE_SRC.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        rel = py.relative_to(_ENGINE_SRC).as_posix()
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                first = owners.setdefault(node.name, rel)
                if first != rel:
                    collisions.append(f"{node.name}: {first} and {rel}")
    assert collisions == [], "\n".join(collisions)


def test_engine_tree_has_no_cross_module_constant_collisions():
    """The dist concatenation rule, extended to module-level constants.

    A duplicate top-level NAME (def, class, or constant) across two engine
    modules silently takes the last module's value in the single-file dist —
    the def/class half is covered above; this covers simple assignments.
    """
    import ast as ast_mod

    engine_root = Path(__file__).resolve().parents[3] / "substrate-kit/src/engine"
    owners: dict[str, str] = {}
    collisions: list[str] = []
    for py in sorted(engine_root.rglob("*.py")):
        if py.name == "__init__.py":
            continue
        tree = ast_mod.parse(py.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in tree.body:
            if isinstance(node, ast_mod.Assign):
                names |= {
                    t.id for t in node.targets if isinstance(t, ast_mod.Name)
                }
            elif isinstance(node, ast_mod.AnnAssign) and isinstance(
                node.target,
                ast_mod.Name,
            ):
                names.add(node.target.id)
        for name in names:
            if name.startswith("__"):
                continue
            if name in owners and owners[name] != py.name:
                collisions.append(f"{name}: {owners[name]} vs {py.name}")
            owners.setdefault(name, py.name)
    assert not collisions, f"constant collisions break the dist: {collisions}"
