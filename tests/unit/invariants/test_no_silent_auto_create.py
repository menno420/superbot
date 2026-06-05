"""S4.5 invariant — no silent Discord-resource creation outside the pipeline.

The Settings Manager roadmap (S4.5) introduces
:class:`services.resource_provisioning.ResourceProvisioningPipeline`
as the canonical creator/binder of Discord resources for subsystem
use.  Resource creation now has a single owner; new code MUST route
through the pipeline.

This test scans every ``disbot/**/*.py`` for direct
``guild.create_*`` calls (``create_text_channel`` /
``create_voice_channel`` / ``create_category`` /
``create_category_channel`` / ``create_role``) and ``*.create_thread``
calls.  Each call must originate from one of:

  * The pipeline's helper layer (:mod:`core.runtime.guild_resources`
    and the older :mod:`utils.channels`) — pure infrastructure with
    no policy logic.  The pipeline composes these helpers.
  * The :class:`core.resources.mutation.ResourceMutationPipeline`
    stub from Phase 2a (raises NotImplementedError; superseded by
    the new pipeline but kept on the allowlist until a future
    cleanup PR removes it).
  * Explicitly grandfathered legacy paths — cogs and views that
    today create resources directly.  Each entry is a per-subsystem
    S10 migration candidate.

Stronger than ``test_no_direct_settings_keys_writes.py``: this scan
catches **every** Discord-resource-creating call shape, not just
calls through one named primitive.  A new caller wanting to create
a channel/role/category outside the pipeline must either:

  * Route through ``ResourceProvisioningPipeline.provision(...)``
    (preferred); or
  * Add itself to ``_ALLOWED_PATHS`` with a comment explaining why
    the bypass is correct (e.g. it is a UI CRUD command that the
    pipeline will later compose).

The accompanying test pins the pipeline service itself to NOT
contain any ``guild.create_*`` call directly — it must go through
the ``ensure_*`` helpers in ``guild_resources``.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DISBOT = _REPO_ROOT / "disbot"

# Discord-API methods that create resources we care about.
_FORBIDDEN_CREATE_METHODS: frozenset[str] = frozenset(
    {
        "create_text_channel",
        "create_voice_channel",
        "create_category",
        "create_category_channel",
        "create_role",
        "create_thread",
        # ``create_stage_channel``, ``create_forum``, etc. are not in
        # scope for v1; future PRs adding stages/forums must extend
        # this set and update the allowlist.
    },
)

# Files ALLOWED to call any of the forbidden create methods directly.
# Adding to this list weakens the invariant; do not extend without
# pairing the entry with a comment naming the future migration PR.
_ALLOWED_PATHS = {
    # Pipeline's helper layer — pure infrastructure, called by the
    # pipeline.  The real safety boundary is the pipeline's 11-step
    # contract, not these helpers.
    _DISBOT / "core" / "runtime" / "guild_resources.py",
    _DISBOT / "utils" / "channels.py",
    # Phase 2a stub — raises NotImplementedError; superseded by S4.5.
    # Future cleanup PR may remove this file.
    _DISBOT / "core" / "resources" / "mutation.py",
    # Audited manual-role creator (server-management PR5).  The role-domain
    # sibling of the provisioning pipeline: it owns operator-driven role
    # create/edit/delete with manageability checks + audit + event, so it is
    # the one sanctioned guild.create_role caller for *manual* roles (subsystem
    # role provisioning still goes through ResourceProvisioningPipeline).
    _DISBOT / "services" / "role_lifecycle_service.py",
    # Grandfathered legacy paths — UI CRUD and admin commands.
    # Each migrates to ResourceProvisioningPipeline in a per-subsystem
    # S10 sub-PR.  (role_cog / views/roles/creation_panel were removed from
    # this list once their create_role calls routed through
    # RoleLifecycleService in PR5.)
    _DISBOT / "views" / "channels" / "create_panel.py",
    _DISBOT / "cogs" / "channel_cog.py",
    _DISBOT / "cogs" / "counting_cog.py",  # auto-create counting channel
    _DISBOT / "cogs" / "economy_cog.py",  # auto-create economy log channel
}


def _iter_production_py_files() -> list[Path]:
    return [p for p in _DISBOT.rglob("*.py") if "__pycache__" not in p.parts]


def _create_call_targets(tree: ast.AST) -> list[str]:
    """Return ``"<receiver>.<method>"`` for any forbidden create call."""
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in _FORBIDDEN_CREATE_METHODS:
            continue
        rcv = node.func.value
        parts: list[str] = []
        while isinstance(rcv, ast.Attribute):
            parts.append(rcv.attr)
            rcv = rcv.value
        if isinstance(rcv, ast.Name):
            parts.append(rcv.id)
        receiver = ".".join(reversed(parts)) if parts else "<expr>"
        found.append(f"{receiver}.{node.func.attr}")
    return found


def test_no_direct_create_calls_outside_allowlist():
    """No production file outside the allowlist may call
    ``guild.create_*`` (or any of the forbidden methods) directly.
    """
    violations: list[tuple[str, list[str]]] = []
    for path in _iter_production_py_files():
        if path in _ALLOWED_PATHS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        offenders = _create_call_targets(tree)
        if offenders:
            violations.append((str(path.relative_to(_REPO_ROOT)), offenders))
    assert not violations, (
        "S4.5 invariant violation: direct guild.create_* (or *.create_thread) "
        "outside the ResourceProvisioningPipeline allowlist.\n"
        "Route new resource creation through "
        "services.resource_provisioning.ResourceProvisioningPipeline.provision(...) "
        "or extend the allowlist with a justification.\n\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )


def test_allowlist_entries_exist():
    """Every allowlisted file must still exist on disk."""
    missing = [str(p.relative_to(_REPO_ROOT)) for p in _ALLOWED_PATHS if not p.exists()]
    assert (
        not missing
    ), "S4.5 allowlist references files that no longer exist:\n" + "\n".join(
        f"  {p}" for p in missing
    )


def test_pipeline_does_not_call_create_directly():
    """The pipeline service itself must NOT contain raw ``guild.create_*``
    calls — every resource creation must compose the ``ensure_*``
    helpers in :mod:`core.runtime.guild_resources`.

    This is the architectural boundary the directive demanded:
    ``ensure_*`` are policy-free infrastructure, the pipeline owns the
    policy (preview, permission, confirmation, audit, binding, event).
    """
    pipeline_path = _DISBOT / "services" / "resource_provisioning.py"
    tree = ast.parse(pipeline_path.read_text())
    offenders = _create_call_targets(tree)
    assert not offenders, (
        "services.resource_provisioning must not call guild.create_* "
        "directly — compose the ensure_* helpers in "
        "core.runtime.guild_resources instead.  Offenders:\n  " + "\n  ".join(offenders)
    )


def test_create_method_set_is_documented():
    """Sanity: the set of methods we forbid must be non-empty and lower-cased.

    Catches a future drive-by edit that empties the set or types one
    method name wrong.
    """
    assert _FORBIDDEN_CREATE_METHODS, "the forbidden-method set must be non-empty"
    for m in _FORBIDDEN_CREATE_METHODS:
        assert m.startswith(
            "create_"
        ), f"method name does not start with create_: {m!r}"
        assert m == m.lower(), f"method name is not lowercase: {m!r}"
