"""P1-3 invariant — every declared scalar setting has a runtime consumer.

The settings production-readiness map names this as the missing "stays
fixed" layer (§Required #3 / §Bugs "Declaration-to-runtime-consumer parity
is manually verified, not invariant-backed"): a setting can be *declared*
(rendered in the settings UI, editable, audited) yet read by **nothing** at
runtime — a silent no-op the operator can toggle with zero effect.  Today's
parity was verified by hand; without an invariant the next editable-no-op
setting ships unnoticed.  This test makes the check machine-enforced.

**The contract:** every ``SettingSpec`` declared in a subsystem schema
(``cogs/*/schemas.py``) must be consumed by at least one runtime reader.
A setting is considered *consumed* when production code under ``disbot/``
does any of:

1. **Typed read by name** — ``resolve_value`` / ``resolve_setting`` called
   with this setting's ``(subsystem, name)`` as string-literal arguments
   (the modern path, e.g. ``resolve_value(g, "welcome", "enabled", ...)``).
2. **Batch / dynamic read** — ``resolve_batch(g, subsystem)`` (reads every
   setting in the subsystem) **or** a ``resolve_value``/``resolve_setting``
   call whose *name* argument is non-literal (a loop variable, e.g. the AI
   config projection's ``resolve_setting(g, "ai", legacy_key)`` over a key
   list).  Both consume the **whole subsystem** — we cannot statically
   prove which names are read, so we conservatively treat all of that
   subsystem's settings as consumed (fail-safe toward "consumed", never a
   false dead-setting alarm).
3. **Key-constant / raw-key reference** — the setting's
   ``utils.settings_keys`` constant (or its raw key string) appears anywhere
   in production code *other than* the ``settings_key=`` argument of its own
   declaration.  This covers the legacy ``db.get_setting(g, KEY, ...)`` path
   **and** the binding/governance lane, where a pointer setting's key is
   consumed as a ``legacy_key=`` field in ``binding_backfill`` /
   ``config_arbitration`` rather than through a ``resolve_*`` call.

A setting matched by none of these has no reader → it is a declared no-op
and the test fails, naming it.  If a setting is *intentionally* declared
ahead of its consumer (a staged rollout), add it to ``_DECLARED_NO_OP_OK``
with a comment and a tracking reference — an explicit, reviewed waiver, not
a silent gap.

Pure AST + the schema registry: no database, CI-runnable on every PR.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"
_SETTINGS_KEYS_DIR = _DISBOT / "utils" / "settings_keys"
_SCHEMAS_GLOB = "cogs/*/schemas.py"

# Functions that read a setting by an explicit ``(subsystem, name)`` pair.
_RESOLVE_NAMED = {"resolve_value", "resolve_setting"}
# Functions that read every setting in a subsystem at once.
_RESOLVE_BATCH = {"resolve_batch"}
# Module-level aliases commonly used for the subsystem-name argument.
_SUBSYSTEM_VARS = {"SUBSYSTEM", "_SUBSYSTEM", "SUBSYSTEM_NAME"}

# Settings deliberately declared before their runtime consumer exists (a
# staged rollout). Each entry needs a comment + tracking reference; this is
# a reviewed waiver, never a dumping ground. Empty today — every declared
# setting has a reader.
_DECLARED_NO_OP_OK: frozenset[str] = frozenset()


def _string_const(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _declared_settings() -> dict[tuple[str, str], str]:
    """``{(subsystem, name): settings_key}`` for every declared SettingSpec."""
    from core.runtime.subsystem_schema import all_schemas

    for schema_path in sorted((_DISBOT / "cogs").glob("*/schemas.py")):
        module = f"cogs.{schema_path.parent.name}.schemas"
        register = getattr(importlib.import_module(module), "register_schemas", None)
        if register is not None:
            register()  # idempotent — re-registers the same subsystem

    declared: dict[tuple[str, str], str] = {}
    for subsystem, schema in all_schemas().items():
        for spec in schema.settings:
            if spec.settings_key:
                declared[(subsystem, spec.name)] = spec.settings_key
    return declared


def _key_constant_index() -> dict[str, str]:
    """``{CONSTANT_NAME: key_value}`` for every ``utils.settings_keys`` const."""
    index: dict[str, str] = {}
    for path in _SETTINGS_KEYS_DIR.glob("*.py"):
        if path.name == "__init__.py":
            continue
        for node in ast.parse(path.read_text()).body:
            if not (
                isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    index[target.id] = node.value.value
    return index


def _scan_consumption(
    name_to_value: dict[str, str],
    all_key_values: set[str],
) -> tuple[set[tuple[str, str]], set[str], set[str]]:
    """Walk every production file once, collecting what is consumed.

    Returns ``(named_pairs, whole_subsystems, key_values)``:
    * ``named_pairs`` — ``(subsystem, name)`` read by an explicit literal
      ``resolve_value``/``resolve_setting`` call.
    * ``whole_subsystems`` — subsystems read via ``resolve_batch`` or a
      dynamic-name ``resolve_*`` call (the whole subsystem is consumed).
    * ``key_values`` — settings-key values referenced anywhere outside their
      own ``settings_key=`` declaration argument.
    """
    named_pairs: set[tuple[str, str]] = set()
    whole_subsystems: set[str] = set()
    key_values: set[str] = set()

    for path in sorted(_DISBOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if _SETTINGS_KEYS_DIR in path.resolve().parents:
            continue  # the key definitions themselves are not consumers
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover — defensive
            continue

        subsystem_const = _module_subsystem_const(tree)

        def _subsystem_arg(node: ast.AST) -> str | None:
            literal = _string_const(node)
            if literal is not None:
                return literal
            if isinstance(node, ast.Name) and node.id in _SUBSYSTEM_VARS:
                return subsystem_const
            return None

        # The one non-consumer reference of a key constant is the
        # ``settings_key=`` argument of its own SettingSpec — exclude it.
        decl_arg_nodes = {
            id(kw.value)
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _call_name(n) == "SettingSpec"
            for kw in n.keywords
            if kw.arg == "settings_key"
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = _call_name(node)
                args = node.args
                if fn in _RESOLVE_NAMED and len(args) >= 3:
                    sub = _subsystem_arg(args[1])
                    name = _string_const(args[2])
                    if sub and name:
                        named_pairs.add((sub, name))
                    elif sub and name is None:
                        whole_subsystems.add(sub)  # dynamic name
                elif fn in _RESOLVE_BATCH and len(args) >= 2:
                    sub = _subsystem_arg(args[1])
                    if sub:
                        whole_subsystems.add(sub)

            if id(node) in decl_arg_nodes:
                continue
            ref = None
            if isinstance(node, ast.Name):
                ref = name_to_value.get(node.id)
            elif isinstance(node, ast.Attribute):
                ref = name_to_value.get(node.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                ref = node.value if node.value in all_key_values else None
            if ref in all_key_values:
                key_values.add(ref)

    return named_pairs, whole_subsystems, key_values


def _scan_literal_reads() -> list[tuple[str, str, str]]:
    """``(subsystem, name, "file:line")`` for every ``resolve_value`` /
    ``resolve_setting`` call with a string-literal ``(subsystem, name)`` pair.

    The subsystem may be a literal or a module-level ``SUBSYSTEM`` alias;
    the name must be a literal (dynamic-name reads carry nothing to check).
    """
    reads: list[tuple[str, str, str]] = []
    for path in sorted(_DISBOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover — defensive
            continue
        subsystem_const = _module_subsystem_const(tree)
        rel = path.relative_to(_REPO_ROOT)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and _call_name(node) in _RESOLVE_NAMED):
                continue
            if len(node.args) < 3:
                continue
            sub_arg, name_arg = node.args[1], node.args[2]
            subsystem = _string_const(sub_arg)
            if (
                subsystem is None
                and isinstance(sub_arg, ast.Name)
                and sub_arg.id in _SUBSYSTEM_VARS
            ):
                subsystem = subsystem_const
            name = _string_const(name_arg)
            if subsystem and name:
                reads.append((subsystem, name, f"{rel}:{node.lineno}"))
    return reads


def _module_subsystem_const(tree: ast.Module) -> str | None:
    for node in tree.body:
        if not (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in _SUBSYSTEM_VARS:
                return node.value.value
    return None


def test_every_declared_setting_has_a_runtime_consumer():
    """No declared scalar setting is a silent runtime no-op."""
    declared = _declared_settings()
    assert declared, "no settings declared — schema registration is broken"

    name_to_value = _key_constant_index()
    all_key_values = set(declared.values())
    named_pairs, whole_subsystems, key_values = _scan_consumption(
        name_to_value,
        all_key_values,
    )

    dead: list[str] = []
    for (subsystem, name), key in sorted(declared.items()):
        label = f"{subsystem}.{name}"
        if label in _DECLARED_NO_OP_OK:
            continue
        consumed = (
            (subsystem, name) in named_pairs
            or subsystem in whole_subsystems
            or key in key_values
        )
        if not consumed:
            dead.append(f"{label} (key={key!r})")

    assert not dead, (
        "P1-3 parity violation: declared setting(s) with NO runtime "
        "consumer — an operator can edit them and nothing reads the value "
        "(a silent no-op). Wire a reader (resolve_value / resolve_setting / "
        "resolve_batch, or db.get_setting via the key constant), or — if the "
        "declaration is intentionally ahead of its consumer — add it to "
        "_DECLARED_NO_OP_OK with a tracking reference:\n"
        + "\n".join(f"  {d}" for d in dead)
    )


def test_every_literal_setting_read_targets_a_declared_setting():
    """The reverse direction — no read of an *undeclared* setting.

    The forward parity above proves every declaration has a reader. The
    mirror gap is just as silent: a typo'd or stale literal read —
    ``resolve_value(g, "welcom", "enabld", default)`` — resolves to the
    *fallback* forever (the misspelled key is never written, so it always
    misses), an invisible always-default bug no other test catches. This
    asserts every ``resolve_value``/``resolve_setting`` call with a literal
    ``(subsystem, name)`` pair targets a setting that actually exists in the
    schema registry, turning the settings lane's parity into a true
    bijection (declared ⇔ consumed). Dynamic-name and ``resolve_batch``
    reads carry no literal name to check and are out of scope.
    """
    declared_pairs = set(_declared_settings())
    literal_reads = _scan_literal_reads()

    stray = sorted(
        {
            f"({sub!r}, {name!r}) at {loc}"
            for sub, name, loc in literal_reads
            if (sub, name) not in declared_pairs
        }
    )
    assert not stray, (
        "P1-3 reverse-parity violation: a resolve_value/resolve_setting "
        "call reads a (subsystem, name) that is NOT a declared SettingSpec "
        "— it silently resolves to the fallback every time (a typo'd or "
        "stale key). Fix the literal, or declare the setting:\n"
        + "\n".join(f"  {s}" for s in stray)
    )
