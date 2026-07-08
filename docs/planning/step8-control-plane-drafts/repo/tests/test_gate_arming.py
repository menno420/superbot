"""The prove-can-fail harness for the six required gates (runs under code-quality's
pytest from day 0 -- which also makes code-quality's pytest leg real from birth).

Each test builds a sandbox repo (the born-with control-plane files + a synthetic state),
runs a gate runner with GATE_ROOT pointed at it, and asserts the exit code. This is the
mechanical proof that every gate (a) passes on the day-0 skeleton for the RIGHT reason
and (b) actually goes red in the partial/violating states it claims to block.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
BORN_WITH = [
    "gates/escape-hatch-baseline.json",
    "gates/schema-growth-ledger.yml",
    "gates/architecture-rules.yml",
    "parity/parity.yml",
    "parity/goldens-source.lock",
    "docs/compat-contract.md",
]


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    for rel in BORN_WITH:
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, dest)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git = ["git", "-C", str(tmp_path)]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "day0"],
        check=True,
    )
    return tmp_path


def gate(sandbox: Path, runner: str, base: str = "") -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "GATE_ROOT": str(sandbox), "GATE_BASE_SHA": base}
    return subprocess.run(
        [sys.executable, str(REPO / "tools" / "gates" / runner)],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
    )


def head_sha(sandbox: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(sandbox), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def commit(sandbox: Path, msg: str) -> str:
    git = ["git", "-C", str(sandbox)]
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", msg],
        check=True,
    )
    return head_sha(sandbox)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")


STUB_EXIT0 = "import sys\nsys.exit(0)\n"

ECONOMY_PENDING = (
    "  economy:\n"
    "    status: pending\n"
    "    depth:\n"
    "      declared: {events: null, tables: null, settings: null}\n"
    "      covered: {events: 0, tables: 0, settings: 0}\n"
    "      exempt: []"
)


def arm_manifest_state(
    root: Path, snapshot: dict, report: dict, baseline: dict, ledger_fields: list
) -> None:
    """Write a consistent ARMED manifest-validate state (stub S3 toolchain whose
    compiler regenerates the committed artifacts byte-identically)."""
    (root / "sb" / "spec").mkdir(parents=True, exist_ok=True)
    (root / "sb" / "spec" / "grammar.py").write_text("X = 1\n")
    tools = root / "tools"
    tools.mkdir(exist_ok=True)
    (tools / "manifest_compile.py").write_text(
        "import json, pathlib\n"
        f"SNAP = {snapshot!r}\n"
        f"REPORT = {report!r}\n"
        "pathlib.Path('manifest.snapshot.json').write_text("
        "json.dumps(SNAP, indent=1, sort_keys=True) + '\\n')\n"
        "pathlib.Path('escape_hatch_report.json').write_text("
        "json.dumps(REPORT, indent=1, sort_keys=True) + '\\n')\n"
    )
    (tools / "check_namespace.py").write_text(STUB_EXIT0)
    (tools / "manifest_validators.py").write_text(STUB_EXIT0)
    write_json(root / "manifest.snapshot.json", snapshot)
    write_json(root / "escape_hatch_report.json", report)
    write_json(root / "gates" / "escape-hatch-baseline.json", baseline)
    # JSON is valid YAML -- keeps the stub ledger writable without a yaml dep here.
    (root / "gates" / "schema-growth-ledger.yml").write_text(
        json.dumps({"schema_version": 1, "fields": ledger_fields}, indent=1) + "\n"
    )


SNAP0 = {
    "schema_field_inventory": ["Spec.f"],
    "declared_surfaces": {},
    "arrangement": {},
}
REPORT0 = {"repo_total": 1, "per_subsystem": {"economy": 1}}
BASELINE0 = {
    "schema_version": 1,
    "repo_total": 1,
    "per_subsystem": {"economy": 1},
    "ledger": [],
}
LEDGER0 = [{"field": "Spec.f", "status": "frozen_baseline"}]


@pytest.fixture()
def armed_manifest_sandbox(sandbox: Path) -> tuple[Path, str]:
    arm_manifest_state(sandbox, SNAP0, REPORT0, BASELINE0, LEDGER0)
    return sandbox, commit(sandbox, "armed base")


# --- manifest-validate -----------------------------------------------------------------


def test_manifest_validate_passes_pre_kernel(sandbox):
    r = gate(sandbox, "run_manifest_validate.py")
    assert r.returncode == 0, r.stderr
    assert "pre-kernel" in r.stdout


def test_manifest_validate_fails_partial_state(sandbox):
    (sandbox / "sb" / "spec").mkdir(parents=True)
    (sandbox / "sb" / "spec" / "grammar.py").write_text("X = 1\n")
    r = gate(sandbox, "run_manifest_validate.py")
    assert r.returncode == 1
    assert "partial" in r.stderr


def test_manifest_validate_fails_nonvirgin_baseline_pre_kernel(sandbox):
    base = sandbox / "gates" / "escape-hatch-baseline.json"
    doc = json.loads(base.read_text())
    doc["repo_total"] = 3
    base.write_text(json.dumps(doc))
    r = gate(sandbox, "run_manifest_validate.py")
    assert r.returncode == 1


# --- architecture ----------------------------------------------------------------------


def test_architecture_passes_pre_kernel(sandbox):
    r = gate(sandbox, "run_architecture.py")
    assert r.returncode == 0, r.stderr


def test_architecture_fails_sb_without_full_checker(sandbox):
    (sandbox / "sb").mkdir()
    (sandbox / "sb" / "clean.py").write_text("X = 1\n")
    r = gate(sandbox, "run_architecture.py")
    assert r.returncode == 1
    assert "check_architecture.py" in r.stderr


def test_architecture_fails_lazy_import_inline(sandbox):
    (sandbox / "sb").mkdir()
    (sandbox / "sb" / "lazy.py").write_text(
        "def f():\n    import json\n    return json\n"
    )
    r = gate(sandbox, "run_architecture.py")
    assert r.returncode == 1
    assert "lazy-import" in r.stderr


# --- sim-gate --------------------------------------------------------------------------


def test_sim_gate_passes_pre_manifest(sandbox):
    r = gate(sandbox, "run_sim_gate.py", base=head_sha(sandbox))
    assert r.returncode == 0
    assert "arrangement surface empty" in r.stdout


def test_sim_gate_fails_naked_arrangement_change(sandbox):
    base = head_sha(sandbox)
    (sandbox / "manifest.snapshot.json").write_text(
        json.dumps({"arrangement": {"panel:economy.home": {"row": 1}}})
    )
    r = gate(sandbox, "run_sim_gate.py", base=base)
    assert r.returncode == 1
    assert "provenance" in r.stderr


def test_sim_gate_passes_exempt_overlay(sandbox):
    base = head_sha(sandbox)
    (sandbox / "manifest.snapshot.json").write_text(
        json.dumps({"arrangement": {"panel:economy.home": {"row": 1}}})
    )
    overlay = sandbox / "sb" / "manifest" / "layout"
    overlay.mkdir(parents=True)
    (overlay / "economy.lock.json").write_text(
        json.dumps(
            {"provenance": {"panel:economy.home": {"Exempt": "below threshold"}}}
        )
    )
    r = gate(sandbox, "run_sim_gate.py", base=base)
    assert r.returncode == 0, r.stderr


# --- golden-parity ---------------------------------------------------------------------


def test_golden_parity_passes_day0_all_pending(sandbox):
    r = gate(sandbox, "run_golden_parity.py")
    assert r.returncode == 0, r.stderr
    assert "pending" in r.stdout


def test_golden_parity_fails_flip_without_denominators(sandbox):
    f = sandbox / "parity" / "parity.yml"
    f.write_text(
        f.read_text().replace(
            "  economy:\n    status: pending", "  economy:\n    status: ported", 1
        )
    )
    r = gate(sandbox, "run_golden_parity.py", base=head_sha(sandbox))
    assert r.returncode == 1
    assert "denominator" in r.stderr


def test_golden_parity_one_way_door(sandbox):
    f = sandbox / "parity" / "parity.yml"
    git = ["git", "-C", str(sandbox)]
    f.write_text(
        f.read_text().replace(
            "  economy:\n    status: pending\n    depth:\n      declared: {events: null, tables: null, settings: null}",
            "  economy:\n    status: ported\n    depth:\n      declared: {events: 0, tables: 0, settings: 0}",
            1,
        )
    )
    subprocess.run([*git, "add", "-A"], check=True)
    subprocess.run(
        [*git, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "flip"],
        check=True,
    )
    base = head_sha(sandbox)
    f.write_text(
        f.read_text().replace(
            "  economy:\n    status: ported", "  economy:\n    status: pending", 1
        )
    )
    r = gate(sandbox, "run_golden_parity.py", base=base)
    assert r.returncode == 1
    assert "one-way" in r.stderr


# --- golden-parity: B-2 key-set arming (deletion cannot disarm) -------------------------


def test_golden_parity_fails_deleted_subsystem_row(sandbox):
    base = head_sha(sandbox)
    f = sandbox / "parity" / "parity.yml"
    assert ECONOMY_PENDING in f.read_text()
    f.write_text(f.read_text().replace(ECONOMY_PENDING + "\n", "", 1))
    r = gate(sandbox, "run_golden_parity.py", base=base)
    assert r.returncode == 1
    assert "economy" in r.stderr and "frozen" in r.stderr


def test_golden_parity_fails_emptied_subsystems_map(sandbox):
    f = sandbox / "parity" / "parity.yml"
    f.write_text(
        "schema_version: 1\n"
        "subsystems: {}\n"
        "kernel_governance:\n"
        "  status: pending\n"
        "  depth:\n"
        "    declared: {events: null, tables: null, settings: null}\n"
        "    covered: {events: 0, tables: 0, settings: 0}\n"
        "    exempt: []\n"
    )
    r = gate(sandbox, "run_golden_parity.py")
    assert r.returncode == 1
    assert "frozen expected set" in r.stderr


# --- golden-parity: M-1 declared is never self-graded ------------------------------------


def test_golden_parity_fails_declared_mismatch_vs_snapshot(sandbox):
    write_json(
        sandbox / "manifest.snapshot.json",
        {
            "declared_surfaces": {
                "economy": {"events": ["e1", "e2"], "tables": [], "settings": []}
            }
        },
    )
    f = sandbox / "parity" / "parity.yml"
    f.write_text(
        f.read_text().replace(
            "  economy:\n    status: pending\n    depth:\n      declared: {events: null, tables: null, settings: null}",
            "  economy:\n    status: pending\n    depth:\n      declared: {events: 5, tables: null, settings: null}",
            1,
        )
    )
    r = gate(sandbox, "run_golden_parity.py")
    assert r.returncode == 1
    assert "denominator-setter" in r.stderr


def test_golden_parity_passes_declared_matching_snapshot(sandbox):
    write_json(
        sandbox / "manifest.snapshot.json",
        {
            "declared_surfaces": {
                "economy": {"events": ["e1", "e2"], "tables": [], "settings": []}
            }
        },
    )
    f = sandbox / "parity" / "parity.yml"
    f.write_text(
        f.read_text().replace(
            "  economy:\n    status: pending\n    depth:\n      declared: {events: null, tables: null, settings: null}",
            "  economy:\n    status: pending\n    depth:\n      declared: {events: 2, tables: 0, settings: 0}",
            1,
        )
    )
    r = gate(sandbox, "run_golden_parity.py")
    assert r.returncode == 0, r.stderr


# --- golden-parity: m-7 exempt-row hygiene -----------------------------------------------


def test_golden_parity_fails_duplicate_exempt_rows(sandbox):
    f = sandbox / "parity" / "parity.yml"
    f.write_text(
        f.read_text().replace(
            ECONOMY_PENDING,
            ECONOMY_PENDING[: -len("      exempt: []")]
            + "      exempt:\n"
            + "        - {surface: 'event:x', reason: 'owner-exempt: dup'}\n"
            + "        - {surface: 'event:x', reason: 'owner-exempt: dup'}",
            1,
        )
    )
    r = gate(sandbox, "run_golden_parity.py")
    assert r.returncode == 1
    assert "duplicate exempt" in r.stderr


# --- manifest-validate: M-2 A-19 ledger-on-rise ------------------------------------------


def test_manifest_validate_fails_baseline_rise_without_ledger_entry(
    armed_manifest_sandbox,
):
    root, base = armed_manifest_sandbox
    arm_manifest_state(
        root,
        SNAP0,
        {"repo_total": 2, "per_subsystem": {"economy": 2}},
        {
            "schema_version": 1,
            "repo_total": 2,
            "per_subsystem": {"economy": 2},
            "ledger": [],
        },
        LEDGER0,
    )
    commit(root, "bump baseline, no ledger entry")
    r = gate(root, "run_manifest_validate.py", base=base)
    assert r.returncode == 1
    assert "ledger" in r.stderr and "economy" in r.stderr


def test_manifest_validate_passes_baseline_rise_with_ledger_entry(
    armed_manifest_sandbox,
):
    root, base = armed_manifest_sandbox
    arm_manifest_state(
        root,
        SNAP0,
        {"repo_total": 2, "per_subsystem": {"economy": 2}},
        {
            "schema_version": 1,
            "repo_total": 2,
            "per_subsystem": {"economy": 2},
            "ledger": [
                {
                    "subsystem": "economy",
                    "grew": "tier-3 count 1 -> 2",
                    "why": "new ui module pending tier-2 refactor",
                    "rejected_tier2_alternative": "registered ref would strand the panel",
                }
            ],
        },
        LEDGER0,
    )
    commit(root, "bump baseline with ledger entry")
    r = gate(root, "run_manifest_validate.py", base=base)
    assert r.returncode == 0, r.stderr


# --- manifest-validate: M-3 frozen_baseline is S3-only -----------------------------------


def test_manifest_validate_fails_new_frozen_baseline_post_freeze(
    armed_manifest_sandbox,
):
    root, base = armed_manifest_sandbox
    snap = dict(SNAP0, schema_field_inventory=["Spec.f", "Spec.g"])
    arm_manifest_state(
        root,
        snap,
        REPORT0,
        BASELINE0,
        LEDGER0 + [{"field": "Spec.g", "status": "frozen_baseline"}],
    )
    commit(root, "sneak a frozen_baseline entry post-freeze")
    r = gate(root, "run_manifest_validate.py", base=base)
    assert r.returncode == 1
    assert "frozen_baseline" in r.stderr


def test_manifest_validate_passes_new_ledgered_field_post_freeze(
    armed_manifest_sandbox,
):
    root, base = armed_manifest_sandbox
    snap = dict(SNAP0, schema_field_inventory=["Spec.f", "Spec.g"])
    arm_manifest_state(
        root,
        snap,
        REPORT0,
        BASELINE0,
        LEDGER0
        + [
            {
                "field": "Spec.g",
                "status": "ledgered",
                "consumers": ["sb/manifest/economy.py", "sb/manifest/farm.py"],
                "rejected_tier3_alternative": "tier-3 module would evade the layer table",
            }
        ],
    )
    commit(root, "legitimate ledgered growth")
    r = gate(root, "run_manifest_validate.py", base=base)
    assert r.returncode == 0, r.stderr


# --- sim-gate: M-4 the authoritative checker cannot silently vanish ----------------------


def test_sim_gate_fails_checker_deleted(sandbox):
    (sandbox / "manifest.snapshot.json").write_text(json.dumps({"arrangement": {}}))
    (sandbox / "tools").mkdir()
    (sandbox / "tools" / "check_sim_gate.py").write_text(STUB_EXIT0)
    base = commit(sandbox, "checker lands")
    (sandbox / "tools" / "check_sim_gate.py").unlink()
    r = gate(sandbox, "run_sim_gate.py", base=base)
    assert r.returncode == 1
    assert "deleted" in r.stderr


def test_sim_gate_delegates_to_present_checker(sandbox):
    (sandbox / "manifest.snapshot.json").write_text(json.dumps({"arrangement": {}}))
    (sandbox / "tools").mkdir()
    (sandbox / "tools" / "check_sim_gate.py").write_text(STUB_EXIT0)
    base = commit(sandbox, "checker lands")
    r = gate(sandbox, "run_sim_gate.py", base=base)
    assert r.returncode == 0, r.stderr
    assert "check_sim_gate green" in r.stdout


# --- check_compat_frozen ---------------------------------------------------------------


def test_compat_passes_pre_kernel(sandbox):
    r = gate(sandbox, "run_check_compat_frozen.py")
    assert r.returncode == 0, r.stderr
    assert "pre-kernel" in r.stdout


def test_compat_fails_snapshot_without_reservations(sandbox):
    (sandbox / "manifest.snapshot.json").write_text(json.dumps({"compat_export": {}}))
    r = gate(sandbox, "run_check_compat_frozen.py")
    assert r.returncode == 1
    assert "unpinned" in r.stderr
