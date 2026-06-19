# Contributing to SuperBot

SuperBot is primarily built by **AI coding agents** working under a documented,
self-improving workflow — but the repository is public and human contributions are
welcome. This guide is the human-facing entry point; the agent workflow it bridges to is
the real source of truth.

## Start here (reading order)

1. **`docs/AGENT_ORIENTATION.md`** — the primary reading-order router ("what do I read for
   task X?").
2. **`docs/collaboration-model.md`** — how we work (the binding working model).
3. **`.claude/CLAUDE.md`** — the working agreement that governs every change.
4. The three binding contracts before any non-trivial change:
   - **`docs/architecture.md`** — layering and import boundaries.
   - **`docs/ownership.md`** — which service/pipeline owns each table, event, and write.
   - **`docs/runtime_contracts.md`** — lifecycle guarantees and failure modes.

`docs/current-state.md` is the living "what's true right now" ledger. **Source code and
merged PRs always win** over any document.

## Repository layout

| Path | What it is |
|---|---|
| `disbot/` | The Discord **bot runtime** (cogs, services, views, governance, control API). |
| `dashboard/` | A **separate** FastAPI developer-dashboard service. It never imports bot code. |
| `docs/` | The documentation surface — planning, ideas, contracts, subsystem folios. Planning lives here (and in the dashboard), **not** in GitHub issues, by design. |
| `scripts/` | Repo tooling (quality/architecture/docs checkers, data exporters). |
| `tests/` | The pytest suite (`tests/unit/...`). Dashboard tests live in `tests/unit/dashboard/`. |
| `architecture_rules/` | Machine-checked layer/consistency rules. |

## Local setup

CI runs **Python 3.10** — match it exactly, or formatters/mypy silently disagree.

```bash
bash scripts/setup_dev_env.sh          # or: pip install -r requirements.txt -r requirements-dev.txt
pip install -r dashboard/requirements.txt   # only if you touch dashboard/
```

## Before you open a PR

Both must pass:

```bash
python3.10 scripts/check_quality.py --full        # black + isort + ruff + mypy + pytest (CI mirror)
python3.10 scripts/check_architecture.py --mode strict
```

- Keep runtime (`disbot/`) PRs **small and focused**; larger end-to-end PRs are fine for
  docs/tooling.
- **Never** write directly to the database from a cog or view — go through the domain's
  `*_mutation.py` service and emit an audit action. See `docs/architecture.md`.
- Update the relevant docs/ledger when behavior or project state changes.
- **No secrets, tokens, or credentials** in code, tests, or fixtures.

CI (the **Code Quality** check) must be green before a PR can merge. `claude/*` PRs
auto-merge on green; human PRs merge after review.

## Open vs. owner-gated areas

Some areas are **owner-gated**: the production deploy, control-API **write** surfaces,
secret/credential management, and certain product/abuse decisions. Open questions and
pending decisions are tracked in `docs/owner/maintainer-question-router.md`. Documentation,
tests, tooling, and bug fixes are the easiest places to start.

## Security

Found a vulnerability? **Do not open a public issue** — follow `SECURITY.md`.

## License

By contributing, you agree that your contributions are licensed under the project's
**MIT License** (`LICENSE`).
