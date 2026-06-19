<!--
Provenance: Q-0177 (2026-06-19). Keep PRs focused. Agent sessions follow
.claude/CLAUDE.md (born-red session card + enders); this template is mainly for
human contributors. The body set by an agent via the API overrides this template.
-->

## Summary

<!-- What does this change, and why? -->

## Linked issue / plan

<!-- "Closes #NN", or link the docs/planning or docs/ideas entry this implements. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] Tooling / CI
- [ ] Breaking change

## Checks

- [ ] `python3.10 scripts/check_quality.py --full` passes (black + isort + ruff + mypy + pytest)
- [ ] `python3.10 scripts/check_architecture.py --mode strict` passes (exit 0)
- [ ] Docs / ledger updated if behavior or project state changed
- [ ] No secrets, tokens, or credentials added

<!-- CI's "Code Quality" check must be green to merge. claude/* PRs auto-merge on green. -->
