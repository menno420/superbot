# 2026-06-19 — router_status.py: a question-router digest tool

> **Status:** `complete`

## Arc

Continuation grooming-ender after the website-split planning chain merged (#1100 plan · #1102 Q-0179).
Executes the idea I captured in #1102's card (Q-0089): a small stdlib tool that digests the
6,500-line / 184-block maintainer question router — the recurring per-session friction of finding the
next free `Q-NNNN` and scanning for what's still OPEN (hit by hand twice this session).

## Shipped (PR #1103)

- `scripts/router_status.py` — pure stdlib, read-only (never writes the router), Q-0105 disposable:
  - `--next` → the next free Q-number, **exact** (header parse): `Q-0180` today.
  - default digest → counts + next number + the **OPEN owner-decision queue** (2 today: Q-0137 partial ·
    Q-0179), classified by each block's leading `> **MARKER**` convention.
  - `--open` / `--unclassified` / `--json` for the detail.
- `tests/unit/scripts/test_router_status.py` — parse / classify / next-number + a real-router smoke test
  (6 tests, green). Carries the Q-0105 provenance/reliability header.
- Verified against the live router; `check_quality.py --check-only` green (CI mirror).

## Context delta

- **Honest classifier limit, surfaced by the tool itself:** 116 of 184 blocks are UNCLASSIFIED — almost
  all the *older* blocks (≈Q-0001…Q-0130) predate the `> **MARKER**` leading-status convention the newer
  blocks use. The tool buckets them as UNCLASSIFIED rather than guessing (it does **not** fight the
  evidence — Q-0120), and the default digest *summarises* that bucket instead of dumping 116 lines. The
  two outputs that matter — next number (exact) and the OPEN queue (both genuinely-open blocks found) —
  are reliable. This gap is the seed of this session's idea below.
- **Gotcha worth recording:** loading a script by path via `importlib` that defines a `@dataclass` needs
  the module registered in `sys.modules` *before* `exec_module`, or the dataclass decorator raises
  `'NoneType' has no attribute '__dict__'` (it looks its module up by name). The existing
  `export_dashboard_data._load_sibling` pattern doesn't hit this only because its siblings define no
  dataclasses. Test loader does `sys.modules[spec.name] = module` before exec.
- **CI-scope reminder confirmed:** ruff flagged `S101`/`PT018` on the *test* file — but CI excludes
  `tests/` from black/isort/ruff, so those are not real CI failures; I did not chase them (the documented
  "don't reformat tests to chase a formatter-over-tests red" rule).

## ⟲ Previous-session review (Q-0102)

**#1102 (route Q-0179) — correct and tight:** it caught the one genuine owner-intent fork the plan left
unrouted and put it in the router with a clear recommendation. More importantly, the **self-audit loop
worked**: #1100's card flagged "the plan surfaced the fork but didn't route it," and #1102 *was* that
correction — each session reviewing its predecessor and closing the gap is exactly the Q-0102 mechanism
doing its job. **What it (and every prior session) did the slow way:** it found the next Q-number and
scanned for open blocks by hand-grepping a 6,500-line file — the friction this session's tool removes.
**System improvement:** the `/route-idea` and `/session-close` disciplines should *use* `router_status.py`
now that it exists (dogfood it — `--next` for the append number, `--open` for the close-out "what does the
owner still owe a decision?" check), turning a manual grep into one command.

## 💡 Session idea (Q-0089)

**One-time backfill of leading status markers on the ~116 older router blocks.** Building the digest
revealed that the older blocks (≈Q-0001…Q-0130) lack the `> **<STATUS>**` leading-status line that newer
blocks use, so no tool — `router_status.py`, a future website "open decisions" surface, or a reconciliation
check — can classify them. Idea: a careful one-pass normalization that prepends each old block a leading
`> **<STATUS>**` line inferred from its body (most are decided/historical; a human confirms the handful
that are ambiguous), making the **whole** router machine-classifiable. Distinct from prior ideas (born-red
outlines / the digest tool itself); motivated directly by this tool's own UNCLASSIFIED output. Sizeable
(116 blocks) → an idea file / its own session, not a drive-by. Believe in it — the digest is only as good
as the convention's coverage.

## 📊 Doc audit (Q-0104)

- New files are `scripts/` + `tests/` (code, not docs) — `check_docs --strict` unaffected/green; no new
  doc needs a reachability link.
- Tool is self-documenting (module docstring + `--help`); the README/AGENT_ORIENTATION need no entry for a
  disposable Q-0105 convenience script (it advertises its own deletion criteria).
- Ledger: only benign newest-merge lag (#1095–#1102, all newer than the #1094 marker → the #1110
  reconciliation pass's job; a manual session does not run it, Q-0124). Not this session's drift.

## 📤 Run report

- **Did:** executed the captured Q-0089 idea — shipped `scripts/router_status.py`, a stdlib digest of the
  question router (next free Q-number + the OPEN owner-decision queue). · **Outcome:** shipped.
- **Shipped:** #1103 — `scripts/router_status.py` + test + active-work entry.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** `none` (disposable Q-0105 tooling; no owner gate). The standing OPEN
  owner decision remains **Q-0179** (control-panel placement) — now also discoverable via
  `python3.10 scripts/router_status.py --open`.
- **⚑ Owner manual steps:** `none`.
- **⚑ Self-initiated:** yes — grooming-ender executing a captured idea, agent-initiated in an unattended
  continuation (Q-0129 welcomes workflow-improving self-initiative). Contained read-only tooling.
- **↪ Next:** the website-split **ultracode build run** is still the substantive next step (gated on
  Q-0179 / its default). The router-marker backfill (above) is a fresh groomable idea.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1103, auto-merge on green) |
| New tool | `scripts/router_status.py` (stdlib, read-only, Q-0105) |
| Tests added | 6 (all green) |
| Router blocks the tool parses | 184 (next free: Q-0180; OPEN: 2) |
| CI-red rounds | 1 (born-red gate by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (backfill old router status markers) |
