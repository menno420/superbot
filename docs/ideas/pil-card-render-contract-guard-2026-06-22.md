# Idea: a shared `bytes | None` lazy-PIL contract guard for the card-render family

> **Status:** `ideas` — capture only, **not** a plan and **not** approval for
> implementation. Source code and the binding contracts win over this file.
> **Subsystem:** none (cross-cutting test/tooling).

**Captured:** 2026-06-22 · **Source:** the reaction-roles PR 6 session (PIL banner
cards, #1279) — generated as the Q-0089 session idea. · **Lane:** small / decided — implementable.

## The problem it solves

Several `disbot/utils/*_render.py` modules render PIL image cards under the **same
contract**: a **lazy `from PIL import …`** inside the function, a **`bytes | None`
return** (`None` when Pillow is unavailable so the caller degrades to embed-only),
and **no network**. Today the family includes at least:

- `utils.welcome_render.render_welcome_card`
- `utils.mining_render` card builders
- `utils.character_render` (gear paper-doll)
- `utils.role_menu_render.render_role_menu_card` (new in PR 6)

Each module has its *own* `test_*_render.py::…_returns_none_without_pillow`, but
**nothing pins the contract cross-cutting**. A future card renderer could forget the
`try/except ImportError → None` guard and instead let the `ImportError` propagate —
which would crash whatever boot/runtime path renders a card on a Pillow-less
environment (the sandbox runs degraded, exactly where this bites). The per-module
tests don't catch a *new* renderer that never added one.

## Sketch

A single `tests/unit/utils/test_card_render_contract.py` invariant that:

1. discovers the public card-render entrypoints (either an explicit registry list,
   or by scanning `utils/*_render.py` for `def render_*_card`-shaped functions whose
   params all have defaults),
2. forces the `PIL` import to fail (the `builtins.__import__` monkeypatch the
   existing `…_returns_none_without_pillow` tests already use),
3. asserts each returns `None` rather than raising.

Locks the whole family to the contract for ~15–25 lines. **Caveat to resolve at
build time:** the renderers have different signatures — some need sample args (a
member name, a gear set). The clean version is a small **explicit registry** of
`(callable, sample_kwargs)` tuples the renderers opt into, rather than reflection
that has to guess valid inputs; that also documents the family in one place.

## Why it's worth having

- It's a **safety guard for a contract the codebase already depends on** but only
  enforces per-module — the gap is precisely a *new* renderer, which is when a guard
  matters most.
- Cheap, fully offline, read-only test tooling (Q-0105 — never gated).
- Reversible / disposable: delete it if it proves noisy.

→ relates `utils/welcome_render.py` · `utils/role_menu_render.py` ·
[reaction-roles overhaul plan §4.6d](../planning/reaction-roles-overhaul-plan-2026-06-21.md).
