# 2026-07-02 Adversarial Review — Risks, Gaps, and Next Steps

## Verdict

**Ready after cleanup.** The strongest confirmed result from 2026-07-02 is that PR #1649 did merge after PR #1652 and materially completed the in-repo substrate-kit finalization lane. The design gate is still correctly present, Phase-2.5 cold-start A/B is still the next independent proof before Phase 3, and no evidence supports starting new-repo implementation yet. The main risk is not missing code; it is stale or overconfident documentation that now needs a reconciliation pass focused on one-fact-one-home cleanup.

## Top 10 findings

1. **Severity: important — S4 is stale after #1649.**
   - **Evidence:** S4 says #1649 was still “in flight” during the thirty-second reconciliation pass, and its Next section still points to the memory-retention/context-economy plan as an implementation-ready lane even though #1649 folded the kit-native context-economy engine into the substrate kit.
   - **Impact:** A new docs or memory agent could pick up already-subsumed work, duplicate it, or treat the wrong plan as the live source.
   - **Advised next action:** Run a small docs-drift cleanup that updates S4 after #1649, moves the retention plan to historical/subsumed status where appropriate, and points S4’s live next item at reconciliation/dashboard freshness instead of kit work.
   - **Agent-buildable or owner-gated:** Agent-buildable.

2. **Severity: important — the hub still has stale S3 wording.**
   - **Evidence:** `docs/current-state.md` still says the S3 next action is “finalize the memory substrate,” while the sector file correctly marks that lane done in #1649 and moves the remaining work to Phase-2.5 A/B plus owner-gated extraction/rebuild decisions.
   - **Impact:** The hub contradicts the per-sector source-of-current-state and can send the next session into completed work.
   - **Advised next action:** Update only the hub S3 row to mirror the S3 sector file: #1649 done; next objective Phase-2.5 cold-start A/B; owner gate remains Phase-2 design approval and extraction.
   - **Agent-buildable or owner-gated:** Agent-buildable.

3. **Severity: cleanup — test-count claims are internally inconsistent.**
   - **Evidence:** S3 claims “117→399 kit tests,” while the session log first says 399 and later says “117 → 407 tests”; local `python -m pytest tests/unit/substrate_kit -q` found **407 passed**.
   - **Impact:** The claim is directionally true but brittle; it erodes trust in the completion report and invites false regression accounting.
   - **Advised next action:** Standardize the claim to “117→407 tests locally in this repo after #1649; PR body/check output should be verified separately if needed.”
   - **Agent-buildable or owner-gated:** Agent-buildable.

4. **Severity: important — PR #1652 ran before #1649, so dashboard/current-state exports likely did not include the final substrate state.**
   - **Evidence:** Live GitHub API showed PR #1652 merged at 2026-07-02T16:39:51Z and PR #1649 merged later at 2026-07-02T17:30:46Z. S4’s pass record text also treated #1649 as in flight.
   - **Impact:** Any dashboard export, open-PR list, or current-state summary produced by #1652 is stale with respect to #1649.
   - **Advised next action:** Run a post-#1649 docs/dashboard freshness pass, not a broad replanning session.
   - **Agent-buildable or owner-gated:** Agent-buildable.

5. **Severity: important — “complete” is true for the in-repo kit, not for standalone extraction/publication.**
   - **Evidence:** The substrate-kit README says the package name is a placeholder and the published name is the owner’s call; `pyproject.toml` explicitly says not to publish to PyPI from here.
   - **Impact:** Agents may overread “shippable package” as permission to publish, rename, or extract the kit. That is still owner-gated.
   - **Advised next action:** In next docs cleanup, label substrate-kit as “in-repo shippable / extraction-ready,” not “externally shipped.”
   - **Agent-buildable or owner-gated:** Cleanup agent-buildable; extraction/publication owner-gated.

6. **Severity: important — Phase 3 remains blocked despite strong Phase 0/0.5 evidence.**
   - **Evidence:** The design spec says owner ratification of the design, backward-compat contract, and go/no-go is required before Phase 3; the strategy repeats that nothing below Phase 2 starts until owner approval and that Phase-2.5 gates Phase 3.
   - **Impact:** Starting new-repo K0 or Phase-3 implementation now would violate the active rebuild-gate discipline.
   - **Advised next action:** Do Phase-2.5 cold-start A/B and/or owner-facing approval package; do not create new-repo code.
   - **Agent-buildable or owner-gated:** Phase-2.5 is agent-buildable; approval is owner-gated.

7. **Severity: cleanup — PR/session metadata disagree on #1649 commit/test counts.**
   - **Evidence:** Live API reported #1649 had 13 commits, while the session summary says “8 substantive commits.” The same session log contains both 399 and 407 test-count claims.
   - **Impact:** Not a product blocker, but the evidence package should not force readers to reconcile avoidable arithmetic drift.
   - **Advised next action:** If the session log is intended as archival truth, append a correction note rather than rewriting history; prefer PR/live source for commit counts.
   - **Agent-buildable or owner-gated:** Agent-buildable.

8. **Severity: important — scratch proof exists in logs and tests, but independent cold-start A/B does not.**
   - **Evidence:** The session log records bare-dir single-file proof, real-dir proof, and pip venv install; tests cover bootstrap freshness/simulation and adopt behavior. However S3 and strategy still mark cold-start substrate-on/off A/B as remaining and gating Phase 3.
   - **Impact:** The kit’s mechanics are proven, but its claimed productivity/quality benefit for fresh agents is not yet proven.
   - **Advised next action:** Run Phase-2.5 first: same small throwaway task, same acceptance rubric, substrate on vs off, record time-to-orientation, mistakes, questions, doc drift, and quality results.
   - **Agent-buildable or owner-gated:** Agent-buildable, unless owner wants to define the A/B target.

9. **Severity: cleanup — quality checks were not fully rerun in this review environment.**
   - **Evidence:** `python3 scripts/check_quality.py --full` failed here because `python3.10` was not active in pyenv, while substrate-kit pytest, bootstrap simulate, scratch adopt/check, and reconcile marker passed.
   - **Impact:** This review cannot independently confirm full-repo quality after #1649; it can only cite session/PR claims plus partial local checks.
   - **Advised next action:** Rerun full quality in the project’s expected Python 3.10 environment before using this report as the final go/no-go evidence.
   - **Agent-buildable or owner-gated:** Agent-buildable/environment-gated.

10. **Severity: future — open PR list is mostly dependency noise, but it should not be ignored before rebuild work consumes CI attention.**
    - **Evidence:** Live open PR query after #1649 showed dependabot PRs still open; #1509 was also mentioned by S4 as owner-left during the prior pass.
    - **Impact:** Dependency PRs can obscure relevant open work and consume review/CI bandwidth during rebuild preparation.
    - **Advised next action:** Separate “dependabot cleanup” from rebuild-critical work; do not let it block Phase-2.5 unless CI becomes noisy.
    - **Agent-buildable or owner-gated:** Mostly agent-buildable; any owner-left PR remains owner-gated.

## Gate status table

| Gate | Status | Evidence | Next action | Owner required? |
|---|---|---|---|---|
| Phase-2 design approval | **Blocked on owner** | Design spec explicitly awaits owner ratification before Phase 3. | Prepare owner-facing approval packet; do not implement Phase 3. | yes |
| Phase-2.5 cold-start A/B | **Next agent-buildable proof** | Strategy says cold-start proof gates Phase 3; S3 keeps it as remaining work after #1649. | Run substrate-on/off A/B in a throwaway repo. | no, unless owner wants to choose target |
| substrate-kit standalone extraction | **Owner-gated** | README and pyproject mark name/publication as owner decision and no PyPI publish. | Draft extraction plan only; do not publish/extract externally. | yes |
| new-repo K0 start | **Blocked** | K0 is Phase 3 and Phase 3 is owner-gated. | Wait for owner approval and Phase-2.5 evidence. | yes |
| Phase-3 implementation | **Blocked** | Strategy: nothing below Phase 2 starts until owner gate; Phase-2.5 gates Phase 3. | Do not start. | yes |
| cutover | **Blocked/future** | Strategy says cutover is owner-verified after shadow-run, data migration, and rollback window. | No action except preserving goldens/rollback evidence. | yes |
| production freeze | **Blocked/future** | Strategy says goldens must be captured before old repo freeze. | Do not freeze production bot yet. | yes |
| dashboard/current-state freshness | **Stale after #1649** | #1652 merged before #1649; S4 says #1649 was in flight. | Post-#1649 current-state/dashboard docs cleanup. | no |

## Stale or conflicting docs

- `docs/current-state.md`: S3 row still points at finalizing the memory substrate as the next action; source/merged #1649 and `docs/current-state/S3-ai-memory.md` say that is done and Phase-2.5 A/B is next.
- `docs/current-state/S3-ai-memory.md`: test-count claim says 117→399, but the final session summary and local test run show 407 substrate-kit tests.
- `docs/current-state/S4-docs.md`: the thirty-second pass records #1649 as in flight and the Next section still points at memory-retention/context-economy implementation work that #1649 largely subsumed.
- `.sessions/2026-07-02-ultracode-memory-substrate-finalize.md`: contains both 399 and 407 test-count claims and says “8 substantive commits,” while live PR metadata shows 13 commits.
- `docs/planning/fresh-rebuild-strategy-2026-07-02.md`: still describes Phase 0 as buildable future work in its phase list, while later docs/S3 say #1649 completed the substrate finalization. Keep this as historical plan text or add a small status overlay.
- `docs/planning/memory-retention-and-context-economy-plan-2026-07-02.md`: remains valuable as design provenance, but its kit-native context-economy engine portion is no longer the live implementation queue after #1649.

## Forgotten-work candidates

- **Post-#1649 reconciliation/dashboard export:** likely missed because #1652 merged before #1649. Classification: docs freshness.
- **Cold-start A/B rubric:** mechanics are ready, but the A/B protocol/metrics must be written before running agents. Classification: verification design.
- **Owner approval package:** design exists, but owner-facing “approve these exact clauses / reject these exact risks” packaging may not. Classification: owner-gated decision support.
- **Substrate-kit extraction plan:** package exists in-repo, but external repo/name/PyPI rights remain unchosen. Classification: owner-gated distribution.
- **Full quality rerun in Python 3.10 environment:** this review could not run it locally. Classification: environment verification.
- **Live CI/check rollup archival:** API metadata was inspected for PR state/commits/files, but check conclusions were not archived into this report because `gh` was unavailable and status API detail was not fully fetched. Classification: verification evidence.
- **Placeholder/TODO sweep beyond substrate-kit:** not completed in this review. Classification: repo hygiene.
- **Dashboard export drift after #1649:** likely stale; not regenerated. Classification: generated-doc freshness.

## Verification checklist

Expected evidence for the next verifier:

```bash
# PR/live-state verification
python - <<'PY'
import json, urllib.request
for n in (1649, 1652, 1639):
    p=json.load(urllib.request.urlopen(f'https://api.github.com/repos/menno420/superbot/pulls/{n}'))
    print(n, p['state'], p['merged_at'], p['head']['sha'], p['merge_commit_sha'])
PY
```
Expected: #1639, #1652, and #1649 are closed/merged; #1652 merged before #1649; #1649 head `33dcc92fc97bdd26d88495e5374f4bcda8426bdd`, merge commit `87997562484a1cb65052c84a970f84cd5e7fd510`.

```bash
python -m pytest tests/unit/substrate_kit -q
```
Expected: 407 passed in the current repo state.

```bash
python3 substrate-kit/dist/bootstrap.py --simulate 3
```
Expected: simulate OK; guided mode reaches steady/graduated.

```bash
tmp=$(mktemp -d) && cp substrate-kit/dist/bootstrap.py "$tmp/bootstrap.py" && (cd "$tmp" && python3 bootstrap.py adopt && python3 bootstrap.py check --strict)
```
Expected: adopt plants the doc/session/index artifacts, stages hooks/skills/agents under `.substrate/`, and `check --strict` passes.

```bash
python3 scripts/check_reconcile_marker.py
```
Expected: marker internally consistent.

```bash
python3 scripts/check_quality.py --full
```
Expected: full quality green in an environment where `python3.10` is active; this review saw an environment failure because pyenv did not expose `python3.10` on PATH.

```bash
rg -n "from disbot|import disbot|disbot/" substrate-kit tests/unit/substrate_kit
```
Expected: no substrate-kit code imports `disbot`; prose references may exist only in planning docs, not kit runtime.

```bash
rg -n "117→399|117 → \*\*399|117 → \*\*407|#1649 memory-substrate in flight|Memory retention & context economy" docs/current-state.md docs/current-state/S3-ai-memory.md docs/current-state/S4-docs.md .sessions/2026-07-02-*.md
```
Expected: identifies stale claims to normalize.

## Recommended next prompt

```text
You are Codex in menno420/superbot. Review only the post-#1649 docs/current-state drift; do not touch runtime code. Read docs/current-state.md, docs/current-state/S3-ai-memory.md, docs/current-state/S4-docs.md, docs/planning/rebuild-ultracode-handoff-2026-07-02.md, .sessions/2026-07-02-ultracode-memory-substrate-finalize.md, and live PR metadata for #1649/#1652. Update the current-state hub and S4 so they reflect that #1649 merged after #1652, substrate-kit finalization is done in-repo, Phase-2.5 cold-start A/B is the next agent-buildable proof, extraction/publication and Phase-3 remain owner-gated, and memory-retention/context-economy implementation work is marked subsumed/historical where #1649 covers it. Normalize the substrate-kit test-count claim to the current local pytest count or phrase it as “117→400+” if you do not rerun tests. Run docs/checker and reconcile-marker checks plus substrate-kit pytest if feasible. Produce a small docs-only PR.
```

## Evidence appendix

### PRs inspected

- PR #1639 — merged 2026-07-02T14:15:11Z; head `487e464f1a27eae790062a3403026e9ae037bff4`; merge commit `43a7ea7247a9b0129a1cf969f8e59b4ca6f3e834`; files included `parity/**`, rebuild strategy/design/linchpin docs, S3/current-state updates.
- PR #1652 — merged 2026-07-02T16:39:51Z; head `b56b31dbd570549556af6a903bf18f653a454806`; merge commit `d9995903bbd3e84bb5a445a72eb5f1600a45f600`; docs/dashboard reconciliation pass.
- PR #1649 — merged 2026-07-02T17:30:46Z; head `33dcc92fc97bdd26d88495e5374f4bcda8426bdd`; merge commit `87997562484a1cb65052c84a970f84cd5e7fd510`; 30 files and 13 commits by API; substrate-kit finalization.

### Files inspected

- `docs/current-state.md`
- `docs/current-state/S3-ai-memory.md`
- `docs/current-state/S4-docs.md`
- `docs/planning/rebuild-ultracode-handoff-2026-07-02.md`
- `docs/planning/rebuild-design-spec-2026-07-02.md`
- `docs/planning/fresh-rebuild-strategy-2026-07-02.md`
- `docs/planning/rebuild-linchpin-validation-2026-07-02.md`
- `docs/planning/memory-retention-and-context-economy-plan-2026-07-02.md`
- `substrate-kit/README.md`
- `substrate-kit/pyproject.toml`
- `substrate-kit/src/**`
- `substrate-kit/dist/bootstrap.py`
- `tests/unit/substrate_kit/**`
- `.sessions/2026-07-02-*.md`

### Commands run

```bash
find .. -name AGENTS.md -print
sed -n '1,220p' docs/current-state.md
sed -n '1,220p' docs/current-state/S3-ai-memory.md
sed -n '1,220p' docs/current-state/S4-docs.md
python - <<'PY'
import urllib.request,json
# GitHub PR metadata/files/commits/open PRs
PY
find substrate-kit/src tests/unit/substrate_kit -type f | sort
python -m pytest tests/unit/substrate_kit -q
rg -n "disbot|TODO|PLACEHOLDER|Phase-2.5|cold-start|owner|117|399|407|scratch|one-step|stdlib-only|single-file" substrate-kit tests/unit/substrate_kit .sessions/2026-07-02-ultracode-memory-substrate-finalize.md docs/current-state/S3-ai-memory.md docs/current-state/S4-docs.md docs/planning/*.md
python3 substrate-kit/dist/bootstrap.py --simulate 3
tmp=$(mktemp -d) && cp substrate-kit/dist/bootstrap.py "$tmp/bootstrap.py" && (cd "$tmp" && python3 bootstrap.py adopt && python3 bootstrap.py check --strict)
python3 scripts/check_reconcile_marker.py
python3 scripts/check_quality.py --full
```
