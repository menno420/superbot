"""Pure role-menu toggle/reconcile logic — no Discord, no DB.

The server-side enforcement for the modern role menus (reaction-roles overhaul
PR 2). Kept Discord-free so the mode rules (``normal`` / ``unique`` / ``verify``
+ the ``max_roles`` cap) are unit-testable in isolation; the view layer turns the
``RoleDelta`` decision into ``member.add_roles`` / ``remove_roles`` calls.

Modes mirror Carl-bot's (plan §2) but enforced server-side on a stateless click,
so there is no stale-reaction problem:

* ``normal`` — picking adds, un-picking removes (the default).
* ``unique`` — at most one role from the menu; a new pick clears the siblings.
* ``verify`` — add-only; the menu never removes a role it granted.

``max_roles`` (Carl's ``rr limit``, ``0`` = unlimited) caps how many roles a
member may simultaneously hold from one menu.
"""

from __future__ import annotations

from dataclasses import dataclass

NORMAL = "normal"
UNIQUE = "unique"
VERIFY = "verify"
MODES = (NORMAL, UNIQUE, VERIFY)


@dataclass(frozen=True)
class RoleDelta:
    """The roles to add / remove for one menu interaction.

    ``rejected`` carries a human reason when a pick was refused (cap reached);
    it is advisory — ``to_add`` / ``to_remove`` are already the safe set to apply.
    """

    to_add: tuple[int, ...]
    to_remove: tuple[int, ...]
    rejected: str | None = None


def reconcile_select(
    *,
    member_role_ids: set[int],
    menu_role_ids: list[int],
    picked_role_ids: set[int],
    mode: str,
    max_roles: int,
) -> RoleDelta:
    """Compute the add/remove delta for a *dropdown* submission.

    The dropdown is a "set my roles from this menu" surface: the member submits
    the exact set they want from ``menu_role_ids``. Menu roles they did not pick
    are removed (``verify`` never removes). ``unique`` and ``max_roles`` cap the
    picked set, keeping the first picks in menu order.
    """
    menu_set = set(menu_role_ids)
    picked = {r for r in picked_role_ids if r in menu_set}

    cap = 1 if mode == UNIQUE else max_roles
    rejected: str | None = None
    if cap and len(picked) > cap:
        kept = [r for r in menu_role_ids if r in picked][:cap]
        picked = set(kept)
        noun = "role" if cap == 1 else "roles"
        rejected = f"You can pick at most {cap} {noun} from this menu."

    to_add = [r for r in menu_role_ids if r in picked and r not in member_role_ids]
    if mode == VERIFY:
        to_remove: list[int] = []  # add-only
    else:
        to_remove = [
            r for r in menu_role_ids if r not in picked and r in member_role_ids
        ]
    return RoleDelta(tuple(to_add), tuple(to_remove), rejected)


def toggle_button(
    *,
    member_role_ids: set[int],
    menu_role_ids: list[int],
    clicked_role_id: int,
    mode: str,
    max_roles: int,
) -> RoleDelta:
    """Compute the delta for a single *button* click (toggle one role)."""
    if clicked_role_id in member_role_ids:
        if mode == VERIFY:
            return RoleDelta(
                (),
                (),
                "This menu only grants roles — it can't remove them.",
            )
        return RoleDelta((), (clicked_role_id,))

    # Adding the role.
    to_remove: list[int] = []
    if mode == UNIQUE:
        to_remove = [
            r for r in menu_role_ids if r != clicked_role_id and r in member_role_ids
        ]
    elif max_roles:
        held = [r for r in menu_role_ids if r in member_role_ids]
        if len(held) >= max_roles:
            noun = "role" if max_roles == 1 else "roles"
            return RoleDelta(
                (),
                (),
                f"You already hold the maximum of {max_roles} {noun} from this menu.",
            )
    return RoleDelta((clicked_role_id,), tuple(to_remove))


__all__ = [
    "MODES",
    "NORMAL",
    "UNIQUE",
    "VERIFY",
    "RoleDelta",
    "reconcile_select",
    "toggle_button",
]
