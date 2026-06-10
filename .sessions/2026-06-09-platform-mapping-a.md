# Platform mapping A — user surface

> **Status:** `completed` — 2026-06-09 · mapping-only session at HEAD `560e35198c46e5d624344b73e94d17dd16d77dcd`.

## Outcome

- Produced `docs/planning/platform-mapping-a-user-surface.md` for the 17 user-facing subsystems and the five split BTD6 cog command surfaces.
- Added the binding standard from live PR #641 because it was absent in the checkout, and converted Agent A's pre-allocated output path to a reachable markdown link.
- Live GitHub API verification: #638 open; #639 merged; #640, #641, and #642 open.
- No runtime, test, registry, roadmap, current-state, folio, or router files changed.

## Verification

- Unqualified `python3.10` was unavailable through the installed pyenv shim. Context maps used Python 3.12.13; required checks were retried with `PYENV_VERSION=3.10.20` to select the installed Python 3.10.20 runtime.
- Ran `python scripts/context_map.py <path>` for 163 scoped cog/view/service files using Python 3.12.13; all 163 completed with zero failures.
- Required docs and quality checks recorded below after completion.

## Context-delta

### Needed-not-pointed

- The binding standard was not in the checkout; it had to be discovered and downloaded from live PR #641.
- Live PR #641 and queued #640/#642 were relevant to interpreting the mapping campaign state even though the prompt named only expected #638/#639.
- The exact source command count required an AST decorator enumeration; no existing single inventory supplied the scoped 22-cog count.

### Pointed-not-needed

- The settings centralization audit and setup-platform command map were useful only for boundary confirmation; Agent A did not need to re-derive their architecture.
- The mother-hub prior art was not needed beyond checking placement because source registries and actual views won.

### Discovered-by-hand

- #639 had merged at `2026-06-09T23:55:54Z`, contrary to the standard's provisional/open expectation.
- BTD6 panel footer copy advertises paths under `!btd6` while implementations live under split `!btd6ref`/`!btd6events` groups.
- Economy's `setlogchannel` is a cross-boundary platform-binding-shaped surface.

## Check results

- `PYENV_VERSION=3.10.20 python3.10 scripts/check_docs.py --strict` — failed only because both new campaign documents are unreachable until the still-open standard PR #641's read-path integration is present; fixing that would require a forbidden fourth touched file.
- Initial unqualified `python scripts/check_quality.py --full` failed because its subprocesses invoke the unavailable default `python3.10` shim.
- `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` — final result recorded after completion.
- Final `PYENV_VERSION=3.10.20 python3.10 scripts/check_quality.py --full` — black/isort/ruff/mypy passed; check_docs failed on the two campaign-doc orphans caused by absent/open #641 read-path integration; pytest could not collect because the selected Python 3.10 environment lacks runtime dependencies (`discord`, `asyncpg`, etc.).
