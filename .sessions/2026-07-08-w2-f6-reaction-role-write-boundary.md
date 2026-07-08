# 2026-07-08 — W2-F6: reaction-role write-boundary invariant suite

> **Status:** `complete`

**Intent:** tests-only PR adding `tests/unit/invariants/test_reaction_role_write_boundary.py` — an AST write-boundary suite (mirroring `test_chain_write_boundary.py`) fencing the 5 reaction-role-overhaul tables (`role_menus`, `role_menu_options`, `reaction_role_message_modes`, `role_grants`, `role_menu_pickup_stats`) to the audited seams `reaction_role_service.py` / `role_grants_service.py`. Evidence + intent: `docs/analysis/server-management-audit-2026-07-08.md` finding F6. PR #1850.

## What happened

- Added `tests/unit/invariants/test_reaction_role_write_boundary.py` (2 tests): the negative
  fence (scan ALL of `disbot/` for direct write-primitive calls outside the allowlist) and the
  positive seam check (services exist + `emit_audit_action`). Pattern: chain suite's full-disbot
  scan + allowed-files set, plus mining suite's DB-receiver tier for colliding names (the service
  re-exports `create_menu`/`delete_menu`/… under the same names; `grant`/`remove`/
  `delete_for_guild` collide across 10+ domains). Added bare-`Name`-call detection for the
  unique names (the `guild_lifecycle` from-import style), a gap in the chain model.
- Allowlist: the two services, `utils/db/role_menus.py` / `role_grants.py` / `roles.py`
  (owners), and `guild_lifecycle.py` (INV-I teardown carve-out, per the audit's proposed fix).
- **Invariant HOLDS — zero violations, no known-violation entry needed.** Ground-truth-verified
  the scanner (Q-0120 instinct): it detects 16 real write calls inside the allowlisted files,
  so the green outside them is a true green, not a blind scanner.
- Gates: `check_architecture --mode strict` exit 0; `check_quality.py --full` green
  (14238 passed / 49 skipped / 2 xfailed, my 2 tests included).
- Scope note: the legacy `reaction_roles` table (audit F6 also names `add_reaction_role`/
  `remove_reaction_role`) was NOT fenced — the dispatch scoped exactly the 5 overhaul tables.
  Follow-up candidate: extend the suite (or `test_no_direct_role_mutations.py`) to the legacy
  table's two writers.

## 💡 Session idea

**Meta-ratchet invariant: every write-bearing `utils/db/` module must have a boundary fence.**
F6's root cause was "shipped the audited seam without the ratchet step the older seams got" —
i.e. the ratchet itself is unenforced. A meta-test in `tests/unit/invariants/` could scan
`disbot/utils/db/*.py` for functions executing INSERT/UPDATE/DELETE and assert each such module
is referenced by at least one invariant test file (or sits on a documented starter allowlist,
burned down over time). That converts "remember to add the fence" into a failing test the next
time a new mutation surface ships — "enforce, don't exhort" (Q-0132) applied one level up.
Dedup-grepped `docs/ideas/` + roadmap: no existing write-boundary meta-invariant idea. Recorded
here only (not as a `docs/ideas/` file) — lane W1-B owns `docs/ideas/` right now; next groomer
can lift it into the index.

## ⟲ Previous-session review

Previous session (`2026-07-08-repo-settings-ledger-phase1.md`) did something genuinely
resourceful — no video tooling, so it installed `imageio-ffmpeg` and read a screen recording as
extracted frames, and it filed the Q-0105 provenance/kill-switch header correctly. What it left
softer: the ledger rows it could not verify from the recording are marked "confirm-per-repo"
with no owning mechanism — a flag that relies on someone remembering. Concrete workflow
improvement: unverified ledger rows should carry a machine-greppable token (e.g.
`UNCONFIRMED-ROW`) so a checker or the reconciliation routine can count them and nag until
burn-down, instead of the flag living only in prose.

## Docs audit (Q-0104)

- `check_current_state_ledger.py --strict`: exit 0 — 14 merged PRs newer than reconciliation
  marker #1830 reported as **benign newest-merge lag** (informational; the next reconciliation
  pass records them). No drift older than the marker.
- `check_docs.py --strict`: exit 0, all checks passed.
- No docs edits made (docs/ claimed by sibling lanes W2-A1 / W1-B); nothing from this session
  needs a docs home beyond this card — the audit doc already carries F6, and the test file is
  self-documenting.

## ⚑ Self-initiated

None — dispatched work (Wave-2 lane F6 from the 2026-07-08 server-management audit). The one
in-lane judgment call: bare-Name-call detection added on top of the sibling pattern (strictly
stronger fence, zero false positives verified against the full tree).
