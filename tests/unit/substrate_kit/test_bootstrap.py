"""Tests for the bootstrap builder + the generated single-file artifact."""

import re
import subprocess
import sys
from pathlib import Path

import build_bootstrap

_KIT = Path(__file__).resolve().parents[3] / "substrate-kit"
_DIST = _KIT / "dist" / "bootstrap.py"


def _manifest_keys(content: str) -> list[str]:
    return re.findall(r"^\s*'(engine/[^']+)':", content, re.MULTILINE)


def test_build_is_deterministic():
    assert build_bootstrap.build() == build_bootstrap.build()


def test_committed_bootstrap_is_current():
    # The committed dist/bootstrap.py must equal a fresh build — i.e. nobody
    # edited src/ and forgot to regenerate. Regenerate: python3 src/build_bootstrap.py
    assert _DIST.read_text(encoding="utf-8") == build_bootstrap.build()


def test_no_self_embedding_recursion():
    keys = _manifest_keys(build_bootstrap.build())
    assert keys  # the manifest is non-empty
    assert all(k.startswith("engine/") for k in keys)  # never embeds dist/


def test_generated_file_compiles():
    compile(build_bootstrap.build(), "bootstrap.py", "exec")


def test_no_leftover_placeholder_tokens():
    content = build_bootstrap.build()
    assert "$PLACEHOLDER" not in content
    assert "$SLOT" not in content


def test_split_imports_drops_multiline_intra_package():
    # A parenthesized multi-line `from engine...` import must be dropped WHOLE —
    # its continuation lines must not leak into the body (that IndentationError'd
    # the generated bootstrap when cli.py imported the skills layer).
    src = (
        "from __future__ import annotations\n"
        "import os\n"
        "from engine.skills.skills import (\n"
        "    SKILLS,\n"
        "    skill_document,\n"
        ")\n"
        "x = 1\n"
    )
    future, imports, body = build_bootstrap._split_imports(src)
    assert future == ["from __future__ import annotations"]
    assert imports == ["import os"]
    assert body == ["x = 1"]


def test_single_file_simulate_via_subprocess(tmp_path):
    boot = tmp_path / "bootstrap.py"
    boot.write_text(build_bootstrap.build(), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(boot), "--simulate", "3"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    # proves the interview engine is embedded and reaches steady in the single file
    assert "graduated=True" in result.stdout


def test_split_imports_ignores_import_like_docstring_lines():
    """A docstring line starting with 'from ' must never be hoisted as an import.

    Regression: contextpack.py's module docstring contained a sentence starting
    'from the index, ...' which the line-based splitter moved into the import
    block, producing a SyntaxError in the generated bootstrap.
    """
    source = (
        '"""Module doc.\n'
        "from the index, never hand-edit them.\n"
        "import-looking prose line.\n"
        '"""\n'
        "from engine.lib.config import Config\n"
        "import json\n"
        "VALUE = 1\n"
    )
    future, imports, body = build_bootstrap._split_imports(source)
    assert imports == ["import json"]
    assert not future
    assert "from the index, never hand-edit them." in body
    assert "import-looking prose line." in body


def test_no_aliased_intra_package_imports_in_engine():
    """`from engine... import X as Y` breaks the generated single file.

    The builder drops intra-package import lines whole, so an alias bound by
    one never exists in the concatenated namespace (a `check` NameError in the
    dist was the live failure). Enforce alias-free engine imports.
    """
    engine_root = Path(build_bootstrap.ENGINE_ROOT)
    offenders = []
    for path in sorted(engine_root.rglob("*.py")):
        in_import = False
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if line.startswith(("from engine", "import engine")):
                in_import = not (")" in line or "(" not in line)
                if " as " in line:
                    offenders.append(f"{path.name}:{lineno}")
                continue
            if in_import:
                if " as " in stripped:
                    offenders.append(f"{path.name}:{lineno}")
                if ")" in line:
                    in_import = False
    assert not offenders, f"aliased intra-package imports break the dist: {offenders}"
