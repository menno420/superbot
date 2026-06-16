# Surface `check_docs` soft signals in the SessionStart banner

> **Status:** `ideas` — captured 2026-06-16 (Q-0089 session idea, from the architecture-atlas
> thread: the count-guard #964 + the atlas #960). Not a plan; not approved. Source + merged PRs win.
> **Touches executable config** (the SessionStart hook) → needs owner sign-off to wire (Q-0106).

## The gap

This repo keeps adding **read-only / soft signals that only help if someone runs them by hand**:

- `check_docs` soft ratchets: the top-level-pile budget, `Recently shipped` budget, and now the
  **inventory-count drift guard** (#964) — all *warn, never fail CI*.
- The architecture **atlas** (#960): its body is generated **on demand, not committed** (Q-0151a).
- `scripts/atlas.py --check`, `extension_crosswalk.py --check`, `dispatch_menu.py`, … — runnable,
  not CI-wired (ask-first).

A soft signal's whole value is the *nudge*, and a nudge nobody sees does nothing. Today the
SessionStart banner surfaces **arch / recon / ledger** state — but not the `check_docs` soft warnings.
So a binding doc can grow a stale inventory count (exactly the drift the #964 guard exists to catch)
and the warning sits unseen until someone happens to run `check_docs`.

## The idea

Add **one line** to the SessionStart banner (`scripts/claude_session_start.sh`) summarising the soft
signals, e.g.:

```
Docs   : soft — top-level 19/19 · recently-shipped 20/20 · inventory-count flags: 0
```

Backed by a cheap `check_docs --soft-summary` mode (a new flag that prints just the ratchet counts +
`len(inventory_count_flags())`, no full run). The banner already shows `Recon`/`Ledger`, so this fits
the existing shape — it makes the soft ratchets *proactively visible* instead of discovered by luck.

## Why I believe in it

Two PRs this session (#960 atlas body-not-committed, #964 soft count-guard) independently chose
"correct but invisible-unless-run." That's a *systemic* pattern, not a one-off — the repo's instinct
to avoid false-positive **hard** gates is right, but it has produced a pile of **soft** signals with
no surfacing channel. One banner line closes the loop for the whole class at once, and it's the
cheapest possible intervention (no new gate, no CI cost, no FP risk).

## Mechanics / caveats

- `scripts/claude_session_start.sh` is **executable config** — per Q-0106 an agent proposes, the owner
  wires it. This capture is the proposal; the `--soft-summary` mode in `check_docs.py` (ordinary
  tooling) can be built first and the hook line added on owner approval.
- Keep it to **counts**, not the full flag list, so the banner stays scannable (the detail is one
  `python3.10 scripts/check_docs.py` away).
- Pairs with the prior `mirror-test coverage by review-unit` idea (same "surface a latent signal" theme).
