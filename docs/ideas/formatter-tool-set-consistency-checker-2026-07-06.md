# Idea — `check_tool_pins` should also assert the formatter tool *set* (not just versions)

> **Status:** `ideas` — surfaced doing the ruff migration (A3, 2026-07-06). A small extension to the
> existing `scripts/check_tool_pins.py` guard. Sector S5.

## The gap it closes

`check_tool_pins.py` verifies that each tool's **version** agrees across the three pin surfaces
(`code-quality.yml`, `requirements-dev.txt`, `.pre-commit-config.yaml`). It does **not** verify that the
**set of tools** is the same — so a *partial* formatter swap (add/remove a tool in some surfaces but not
all) sails through.

That partial-swap risk is real: the ruff migration had to remove black + isort from **8+** surfaces in
lockstep — the design named "five" (`code-quality.yml`, `requirements-dev.txt`, `.pre-commit-config.yaml`,
`check_quality.py`, `claude_post_edit.py`) but the actual set also included `claude_stop_check.py` (Stop
hook), `check_routine_permission_surface.py`, `setup_dev_env.sh`, and two guard tests. Miss one and you
get exactly the "passes locally, fails in CI" (or the reverse) drift `check_tool_pins` exists to prevent —
e.g. a leftover `black` hook in `.pre-commit-config.yaml` reformats with black and fights ruff every commit.

## The precise signal

Extend `check_tool_pins` (or a sibling): assert the **tool set is identical** across the pin surfaces, not
just the versions of tools that happen to appear in all of them. Today `_TOOLS` is the *expected* set and
the checker only flags a version mismatch or a tool that's expected-but-missing; a tool present in *one*
surface and absent from `_TOOLS` (a half-added tool) is invisible. Concretely: parse the tool set from each
surface and flag any tool that appears in some surfaces but not others, in **both** directions.

Cheap follow-on found the same session: **`.pre-commit-config.yaml` is not run by any workflow** — CI only
reads its *pins* (via `check_tool_pins`), never executes `pre-commit run`. So a structurally-broken
pre-commit config (a hook that no longer exists) is caught by nobody. A `pre-commit validate-config` (or a
tiny "every hook id resolves" check) would close that, or — if pre-commit is purely a local convenience —
document that explicitly so nobody assumes CI runs it.

## Why it's worth having

The whole `check_tool_pins` guard exists because formatter drift is a recurring, expensive pain
(#1074/#1315/#1556). Version-drift is guarded; tool-set-drift (a partial migration) is the same failure
class on a different axis, and this session is exactly when it could have bitten. Small, mechanical, low-FP.
