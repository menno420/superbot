"""Guards for the bot-owner (platform-owner) override completeness (Q-0212).

#1573 added ``config.is_platform_owner`` and wired it into the governance /
service / setup / canonical-view seams — but a **truncated grep** missed two whole
gate classes (the ``views/ai/policy`` ``interaction_check``s and the
``@has_permissions(administrator=True)`` command decorators), so the owner was
still denied ("it still does not work").  These source guards make that
miss-class fail CI: every admin gate must route through an owner-aware helper, so
a new raw gate can never silently re-lock the owner out.

Two guards + a behavioural check of the new decorator helper.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

import config

_REPO = pathlib.Path(__file__).resolve().parents[3]
_DISBOT = _REPO / "disbot"
_VIEWS = _DISBOT / "views"
_COGS = _DISBOT / "cogs"


def _py_files(root: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def test_no_raw_admin_in_view_interaction_check() -> None:
    """A view ``interaction_check`` must authorise via the owner-aware
    ``views.base.interaction_is_admin`` / ``member_is_admin`` helpers, never a raw
    ``...guild_permissions.administrator`` read.

    That raw read is exactly what re-locked the bot owner out of the AI policy /
    routing panels (the #1573 miss → #1577 fix).  ``views/base.py`` (the canonical
    helpers) is exempt.
    """
    offenders: list[str] = []
    for path in _py_files(_VIEWS):
        if path.name == "base.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - defensive
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "interaction_check"
            ):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute) and sub.attr == "administrator":
                        offenders.append(
                            f"  {path.relative_to(_REPO)}:{sub.lineno}"
                            " (interaction_check reads .administrator directly)"
                        )
    assert not offenders, (
        "View interaction_check(s) gate on a raw administrator permission instead "
        "of the owner-aware views.base.interaction_is_admin / member_is_admin "
        "helpers (Q-0212) — the bot owner would be denied. Route them through the "
        "helper:\n" + "\n".join(sorted(offenders))
    )


def test_no_raw_has_permissions_decorator() -> None:
    """No cog command may gate on a raw ``has_permissions(...)`` decorator — for
    **any** permission, not just administrator.

    Use ``@perms_or_owner(**perms)`` / ``@app_perms_or_owner(**perms)`` (or the
    ``@admin_or_owner()`` wrappers) from :mod:`core.runtime.permission_checks` so
    the platform owner can do everything with the bot (Q-0212, "do everything as
    owner"); the plain decorator denies the owner.  Catches every spelling
    (``commands.has_permissions``, ``app_commands.checks.has_permissions``,
    ``commands.has_guild_permissions``, bare ``has_permissions``) at the
    decorator line.
    """
    offenders: list[str] = []
    for path in _py_files(_COGS):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("@") and (
                "has_permissions(" in stripped or "has_guild_permissions(" in stripped
            ):
                offenders.append(f"  {path.relative_to(_REPO)}:{i}: {stripped}")
    assert not offenders, (
        "Raw has_permissions(...) command decorator(s) found — replace with "
        "@perms_or_owner(**perms) / @app_perms_or_owner(**perms) (or "
        "@admin_or_owner()) from core.runtime.permission_checks so the platform "
        "owner passes (Q-0212):\n" + "\n".join(offenders)
    )


_ROLE_VIEWS = _VIEWS / "roles"


def test_role_surface_gates_are_owner_aware() -> None:
    """The role surfaces (the panel the owner reported being locked out of —
    role menus / creation / hub) must not read an interacting user's
    ``guild_permissions.<perm>`` directly; they route through
    ``member_has_perms_or_owner`` / ``member_is_admin`` so the platform owner is
    never denied (Q-0212).  ``me.guild_permissions`` (the bot's own capability) is
    allowed.
    """
    offenders: list[str] = []
    for path in _py_files(_ROLE_VIEWS):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "guild_permissions" not in line:
                continue
            # The bot's own capability check is fine; only user gates are banned.
            if "me.guild_permissions" in line or "guild.me" in line:
                continue
            offenders.append(f"  {path.relative_to(_REPO)}:{i}: {line.strip()}")
    assert not offenders, (
        "Role-surface view reads an interacting user's guild_permissions directly "
        "— route through member_has_perms_or_owner / member_is_admin so the "
        "platform owner is not denied (Q-0212):\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# Behaviour of the new decorator helper (core.runtime.permission_checks)
# ---------------------------------------------------------------------------

_OWNER_ID = 555_000_111


@pytest.fixture()
def _owner(monkeypatch: pytest.MonkeyPatch) -> int:
    monkeypatch.setattr(config, "BOT_OWNER_USER_ID", _OWNER_ID)
    return _OWNER_ID


class _Perms:
    def __init__(self, **perms: bool) -> None:
        # Any unset permission reads False (mirrors discord.Permissions defaults).
        self._perms = perms

    def __getattr__(self, name: str) -> bool:
        return self._perms.get(name, False)


class _User:
    def __init__(self, uid: int, **perms: bool) -> None:
        self.id = uid
        self.guild_permissions = _Perms(**perms)


def test_member_has_perms_or_owner_grants_owner_any_permission(_owner: int) -> None:
    from core.runtime.permission_checks import member_has_perms_or_owner

    # Platform owner passes every specific-permission gate without holding it.
    assert member_has_perms_or_owner(_User(_OWNER_ID), manage_roles=True) is True
    assert member_has_perms_or_owner(_User(_OWNER_ID), manage_guild=True) is True
    # A member holding the named permission passes (unchanged behaviour)…
    assert (
        member_has_perms_or_owner(_User(42, manage_roles=True), manage_roles=True)
        is True
    )
    # …and one lacking it is denied.
    assert member_has_perms_or_owner(_User(42), manage_roles=True) is False


def test_member_has_admin_or_owner_grants_owner(_owner: int) -> None:
    from core.runtime.permission_checks import member_has_admin_or_owner

    # Platform owner without Discord admin → allowed.
    assert member_has_admin_or_owner(_User(_OWNER_ID, administrator=False)) is True
    # Plain administrator → allowed (unchanged behaviour).
    assert member_has_admin_or_owner(_User(42, administrator=True)) is True
    # Non-owner non-admin → denied.
    assert member_has_admin_or_owner(_User(42, administrator=False)) is False
