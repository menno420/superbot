"""Capture + replay engines.

``capture_case`` runs one :class:`GoldenCase` against the booted harness and
returns its golden document. ``replay_case`` runs the same case and diffs the
fresh document against a stored golden — the red-until-parity primitive (and,
run against this repo, the current-bot regression net).
"""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from typing import Any

from parity.harness.boot import Harness
from parity.harness.capture import Normalizer
from parity.harness.cases import GoldenCase, Step
from parity.harness.dbsnap import diff_snapshots, reset_database, snapshot
from parity.harness.world import DEFAULT_PERSONAS

__all__ = ["capture_case", "replay_case", "golden_path", "apply_isolation_resets"]

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS_VERSION = 1


def golden_path(root: Path, case: GoldenCase) -> Path:
    return root / case.subsystem / f"{case.id.replace('.', '_')}.json"


def apply_isolation_resets() -> None:
    """Reset the bot's module-level singletons between cases.

    Reuses the suite's canonical registry (``tests/_isolation.py``) so the
    harness and the test suite share one definition of "process-global state".
    """
    iso_path = _REPO_ROOT / "tests" / "_isolation.py"
    spec = importlib.util.spec_from_file_location("parity_isolation", iso_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load isolation registry from {iso_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply_global_resets()


def _flatten_components(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for row in components:
        flat.extend(row.get("components", []))
    return flat


async def _drive(
    harness: Harness,
    step: Step,
    minted: list[int],
    minted_components: dict[int, list[dict[str, Any]]],
) -> str | None:
    """Drive one step; returns the resolved custom_id for click steps."""
    mentions = tuple(DEFAULT_PERSONAS[m]["id"] for m in step.mentions)
    if step.kind == "command":
        content = step.content
        if "__CHANNEL_" in content and harness.world is not None:
            for name, cid in harness.world.channels.items():
                content = content.replace(f"__CHANNEL_{name.upper()}__", f"<#{cid}>")
        await harness.send_command(
            content,
            persona=step.persona,
            channel=step.channel,
            mentions=mentions,
        )
        return None
    if step.kind == "slash":
        await harness.invoke_slash(
            step.name,
            list(step.options),
            persona=step.persona,
            channel=step.channel,
        )
        return None
    if step.kind == "click":
        index = step.target_message - 1
        if index < 0 or index >= len(minted):
            raise ValueError(
                f"step targets <msg:{step.target_message}> but only "
                f"{len(minted)} bot messages were minted",
            )
        message_id = minted[index]
        custom_id = step.custom_id
        component_type = step.component_type
        if not custom_id and step.component_index >= 0:
            flat = _flatten_components(minted_components.get(message_id, []))
            if step.component_index >= len(flat):
                raise ValueError(
                    f"component_index {step.component_index} out of range "
                    f"({len(flat)} components on <msg:{step.target_message}>)",
                )
            component = flat[step.component_index]
            custom_id = component.get("custom_id", "")
            component_type = component.get("type", component_type)
        await harness.click(
            message_id=message_id,
            custom_id=custom_id,
            component_type=component_type,
            values=list(step.values) if step.values is not None else None,
            persona=step.persona,
            channel=step.channel,
        )
        return custom_id
    raise ValueError(f"unknown step kind {step.kind!r}")  # pragma: no cover


async def capture_case(harness: Harness, case: GoldenCase) -> dict[str, Any]:
    from utils.db import pool

    if harness.world is None or harness.http is None:
        raise RuntimeError("harness not started")
    random.seed(case.seed)
    harness.world.clock.set_case_base(case.id)
    apply_isolation_resets()
    await reset_database(pool)
    for statement in case.fixture_sql:
        await pool.execute(statement)
    before = await snapshot(pool)

    normalizer = Normalizer(harness.world)
    minted: list[int] = []
    minted_components: dict[int, list[dict[str, Any]]] = {}
    steps_out: list[dict[str, Any]] = []
    harness.take_calls()
    harness.take_events()

    harness.http.gaps.clear()
    for step in case.steps:
        resolved_custom_id = await _drive(harness, step, minted, minted_components)
        if harness.http.gaps:
            gaps = sorted(set(harness.http.gaps))
            harness.http.gaps.clear()
            raise RuntimeError(
                f"capture integrity: fake-HTTP gap(s) hit during {case.id}: "
                f"{gaps} — the golden would record harness artifacts as "
                "behavior. Extend parity/harness/fake_http.py.",
            )
        raw_calls = harness.take_calls()
        for call in raw_calls:
            rid = getattr(call, "response_id", None)
            if rid is not None:
                minted.append(rid)
                components = (call.payload or {}).get("components")
                if components:
                    minted_components[rid] = components
        events = harness.take_events()
        # Cross-listener fan-out order is asyncio-scheduler noise, not a
        # behavioral contract (the bus is publish-accepted, no ordering
        # guarantee across independent subscribers) — sort stably by event
        # name so same-name sequences keep their real order.
        events.sort(key=lambda e: e["event"])
        input_doc = _describe_step(step)
        if resolved_custom_id:
            input_doc["custom_id"] = normalizer.normalize(resolved_custom_id)
        step_doc: dict[str, Any] = {
            "input": input_doc,
            "calls": normalizer.calls(raw_calls),
        }
        if events:
            step_doc["events"] = normalizer.events(events)
        steps_out.append(step_doc)

    after = await snapshot(pool)
    delta = normalizer.db_delta(diff_snapshots(before, after))

    return {
        "harness_version": HARNESS_VERSION,
        "case_id": case.id,
        "subsystem": case.subsystem,
        "seed": case.seed,
        "notes": case.notes,
        "steps": steps_out,
        "db_delta": delta,
    }


def _describe_step(step: Step) -> dict[str, Any]:
    doc: dict[str, Any] = {"kind": step.kind, "persona": step.persona}
    if step.kind == "command":
        doc["content"] = step.content
    elif step.kind == "slash":
        doc["name"] = step.name
        if step.options:
            doc["options"] = list(step.options)
    elif step.kind == "click":
        doc["custom_id"] = step.custom_id
        doc["target_message"] = step.target_message
    if step.channel != "general":
        doc["channel"] = step.channel
    return doc


def _diff_docs(expected: Any, actual: Any, path: str = "$") -> list[str]:
    """Minimal structural diff — every mismatch line is actionable."""
    if type(expected) is not type(actual):
        return [f"{path}: type {type(expected).__name__} != {type(actual).__name__}"]
    if isinstance(expected, dict):
        problems = []
        for key in sorted(set(expected) | set(actual)):
            if key not in expected:
                problems.append(f"{path}.{key}: unexpected (new behavior)")
            elif key not in actual:
                problems.append(f"{path}.{key}: missing (behavior gone)")
            else:
                problems.extend(_diff_docs(expected[key], actual[key], f"{path}.{key}"))
        return problems
    if isinstance(expected, list):
        problems = []
        if len(expected) != len(actual):
            problems.append(f"{path}: length {len(expected)} != {len(actual)}")
        for i, (e, a) in enumerate(zip(expected, actual, strict=False)):
            problems.extend(_diff_docs(e, a, f"{path}[{i}]"))
        return problems
    if expected != actual:
        return [
            f"{path}: {json.dumps(expected, default=str)[:120]} != {json.dumps(actual, default=str)[:120]}",
        ]
    return []


async def replay_case(
    harness: Harness,
    case: GoldenCase,
    goldens_root: Path,
) -> tuple[bool, list[str]]:
    """Re-run a case and diff against its stored golden. True = parity."""
    path = golden_path(goldens_root, case)
    if not path.exists():
        return False, [f"golden missing: {path}"]
    expected = json.loads(path.read_text())
    actual = await capture_case(harness, case)
    problems = _diff_docs(expected, actual)
    return (not problems), problems
