# Hostile audit: checking the checkers (2026-07-10)

> **Status:** `audit` — external (Codex/GPT-5.6-Sol) factual re-verification, independently spot-checked 2026-07-10 (see addendum).

Scope: read-only re-verification of factual claims in:

- `docs/eap/gen1-grand-review-2026-07-09.md`
- `docs/eap/fleet-overnight-review-2026-07-10.md`

Method: live GitHub REST API calls against `menno420/*`, plus fresh shallow clones of sibling repos into `/tmp/audit-repos` for file/test/workflow inspection. I did **not** treat the target documents' own citations as proof.

Bias: I sampled high-blast-radius claims: fleet-wide counts, PR terminal states, timing windows, cross-repo “zero” assertions, test counts, CI coverage, and stale-state findings.

## Summary verdict

- **Confirmed:** 12 / 15
- **Refuted:** 2 / 15
- **Unverifiable from primary public evidence:** 1 / 15

The third correction candidate is real: the overnight review says `superbot-next` had “~20 PRs up the testing ladder” overnight, but live PR data for the stated 00:00–06:15Z window shows only **2 merged PRs** in `superbot-next` (#98 and #99), neither of which is a testing-ladder implementation PR. The fleet-wide “116 PRs” number is nevertheless exactly reproducible, so the error appears to be a per-repo narrative drift, not a fleet-count drift.

## Claims sampled

### 1. Fleet-wide overnight merge count: “116 PRs merged fleet-wide 00:00–06:15Z”

**Verdict: CONFIRMED.**

Evidence from live REST API (`GET /repos/menno420/{repo}/pulls?state=closed`) counted PRs with `merged_at` in `[2026-07-10T00:00:00Z, 2026-07-10T06:15:00Z]` across all 13 public repos:

| Repo | Count |
|---|---:|
| codetool-lab-fable5 | 0 |
| codetool-lab-opus4.8 | 0 |
| codetool-lab-sonnet5 | 0 |
| fleet-manager | 3 |
| gba-homebrew | 18 |
| pokemon-mod-lab | 7 |
| substrate-kit | 35 |
| superbot | 13 |
| superbot-games | 6 |
| superbot-next | 2 |
| trading-strategy | 18 |
| venture-lab | 8 |
| websites | 6 |
| **Total** | **116** |

Evidence links: [`menno420` public repo list](https://api.github.com/users/menno420/repos?per_page=100), representative API endpoint for closed PRs: [`substrate-kit` pulls](https://api.github.com/repos/menno420/substrate-kit/pulls?state=closed&per_page=100).

### 2. Public account repo census: the overnight review covers “all 13 repos”

**Verdict: CONFIRMED.**

Live `GET /users/menno420/repos?per_page=100` returned exactly 13 public repos: `codetool-lab-fable5`, `codetool-lab-opus4.8`, `codetool-lab-sonnet5`, `fleet-manager`, `gba-homebrew`, `pokemon-mod-lab`, `substrate-kit`, `superbot`, `superbot-games`, `superbot-next`, `trading-strategy`, `venture-lab`, `websites`.

Evidence: <https://api.github.com/users/menno420/repos?per_page=100>.

### 3. Overnight review headline: “zero open PRs”

**Verdict: REFUTED as a durable/public claim; possibly true only at the review snapshot.**

A live open-PR sweep across the same 13 repos found open PRs after the review was written:

| Repo | Live open PRs found during this audit |
|---|---:|
| fleet-manager | 1 |
| superbot | 5 |
| superbot-next | 1 |
| all other public repos | 0 |

Evidence endpoints: [`superbot` open pulls](https://api.github.com/repos/menno420/superbot/pulls?state=open&per_page=100), [`superbot-next` open pulls](https://api.github.com/repos/menno420/superbot-next/pulls?state=open&per_page=100), [`fleet-manager` open pulls](https://api.github.com/repos/menno420/fleet-manager/pulls?state=open&per_page=100).

Caveat: the target sentence is a time-sensitive review snapshot. Public REST data can prove it is no longer true; it cannot, by itself, prove whether the statement was true at the exact review minute unless one reconstructs event history from timelines.

### 4. `superbot-next`: “~20 PRs up the testing ladder (bands 3–5)” overnight

**Verdict: REFUTED.**

For the same overnight interval used by the fleet claim (`2026-07-10T00:00:00Z` through `2026-07-10T06:15:00Z`), live GitHub shows only two merged `superbot-next` PRs:

- #98, merged `2026-07-10T00:57:42Z`, title: `status: band-5 heartbeat + step-7 replay evidence — live-drive is the next lane (gen-2 night prep)`.
- #99, merged `2026-07-10T01:10:01Z`, title: `ideas: seed overnight backlog — port-the-small-four + reaction-adapter seam`.

Those are status/ideas PRs, not “~20 PRs up the testing ladder.” This is the strongest correction candidate found.

Evidence: [`superbot-next` closed pulls](https://api.github.com/repos/menno420/superbot-next/pulls?state=closed&per_page=100).

### 5. `substrate-kit`: “~35 PRs, releases v1.4→v1.7.0” overnight

**Verdict: CONFIRMED on PR count; release-range wording is plausible from tags/releases but not exhaustively audited.**

Live PR data counted **35** `substrate-kit` PRs merged in the 00:00–06:15Z window. GitHub releases/tags expose release artifacts in the named range, including v1.4.x/v1.5.x/v1.6.x/v1.7.0 era entries.

Evidence: [`substrate-kit` closed pulls](https://api.github.com/repos/menno420/substrate-kit/pulls?state=closed&per_page=100), [`substrate-kit` releases](https://api.github.com/repos/menno420/substrate-kit/releases?per_page=100), [`substrate-kit` tags](https://api.github.com/repos/menno420/substrate-kit/tags?per_page=100).

### 6. `fleet-manager`: “18 PRs incl. gen-2 blueprint→binding…” in the per-repo table

**Verdict: REFUTED if read as the night-of-review window; CONFIRMED only if read as broader gen-1/project history.**

Live 00:00–06:15Z count is **3** merged PRs in `fleet-manager`: #15, #16, #17. Therefore the overnight-table phrasing overstates the overnight PR volume if its “18 PRs” is meant to be within the review night.

However, the repo had at least 18 PR numbers by then, so this may be a sloppy cumulative-lane phrase rather than a fabricated count.

Evidence: [`fleet-manager` closed pulls](https://api.github.com/repos/menno420/fleet-manager/pulls?state=closed&per_page=100).

### 7. `superbot-games`: “73+48 tests pass locally”

**Verdict: CONFIRMED.**

Fresh clone test collection:

- `python3 -m pytest tests --collect-only -q` returned `73 tests collected`.
- `python3 -m pytest games/exploration/tests --collect-only -q` returned `48 tests collected`.
- Combined collection returned `121 tests collected`.

Evidence: repository source in fresh clone from <https://github.com/menno420/superbot-games>; test directories `tests/` and `games/exploration/tests/`.

### 8. `superbot-games`: “CI coverage overstated… workflow runs only tests/ (mining 73); exploration’s 48 tests … outside CI”

**Verdict: CONFIRMED.**

Fresh clone of `superbot-games` shows `.github/workflows/substrate-gate.yml` has a test step:

```yaml
python3 -m pytest tests/ -q
```

That command includes the 73 mining tests but excludes `games/exploration/tests/`, whose 48 tests are collected separately. This supports the overnight review finding.

Evidence: <https://github.com/menno420/superbot-games/blob/main/.github/workflows/substrate-gate.yml>.

### 9. Gen-1 sweep: `superbot` #1910 merged at 23:18:36Z

**Verdict: CONFIRMED.**

Live PR API for `menno420/superbot#1910` reports `state=closed`, `merged_at=2026-07-09T23:18:36Z`, title `docs(eap): gen-1 wrap-up email draft v2 (2026-07-09)`.

Evidence: <https://api.github.com/repos/menno420/superbot/pulls/1910> and UI <https://github.com/menno420/superbot/pull/1910>.

### 10. Gen-1 sweep: `superbot-next` #95 merged at 23:52:01Z

**Verdict: CONFIRMED.**

Live PR API for `menno420/superbot-next#95` reports `state=closed`, `merged_at=2026-07-09T23:52:01Z`, title beginning `fix: band-5 replay/live seams…`.

Evidence: <https://api.github.com/repos/menno420/superbot-next/pulls/95> and UI <https://github.com/menno420/superbot-next/pull/95>.

### 11. Gen-1 sweep: `superbot-next` #97 merged “~23:47Z”

**Verdict: CONFIRMED within rounding.**

Live PR API reports `merged_at=2026-07-09T23:45:49Z` for #97. That is within about 1 minute 11 seconds of “~23:47Z.”

Evidence: <https://api.github.com/repos/menno420/superbot-next/pulls/97> and UI <https://github.com/menno420/superbot-next/pull/97>.

### 12. Gen-1 sweep: `superbot-games` #5/#11/#14 all merged with the named squash SHAs

**Verdict: CONFIRMED.**

Live API reported:

- #5 merged `2026-07-10T00:00:58Z`, `merge_commit_sha=1eea13a69c26f15cd1e6b83b59382938491a7d19`.
- #11 merged `2026-07-10T00:03:02Z`, `merge_commit_sha=b285df6efe17e76a715a206e795bc2330264d5d0`.
- #14 merged `2026-07-10T00:04:39Z`, `merge_commit_sha=4c9f8899450dd4892f06c465dd15adf7c0db14aa`.

Evidence: <https://api.github.com/repos/menno420/superbot-games/pulls/5>, <https://api.github.com/repos/menno420/superbot-games/pulls/11>, <https://api.github.com/repos/menno420/superbot-games/pulls/14>.

### 13. Gen-1 sweep: `substrate-kit` #49 and #26 were merged/ratified

**Verdict: CONFIRMED.**

Live API reported:

- #49 merged `2026-07-10T00:07:46Z`, `merge_commit_sha=6d6046bf3b37b6d8ff35e23586270c932bfef2ee`.
- #26 merged `2026-07-10T00:12:35Z`, `merge_commit_sha=706190f885a89ce18791d2a57fd1c1911ecca771`.

Evidence: <https://api.github.com/repos/menno420/substrate-kit/pulls/49>, <https://api.github.com/repos/menno420/substrate-kit/pulls/26>.

### 14. Gen-1 sweep: `fleet-manager` #12/#13 self-merged at 23:40:31Z / 23:37:03Z

**Verdict: CONFIRMED.**

Live API reported:

- #12 merged `2026-07-09T23:40:31Z`, `merge_commit_sha=d913cbde611c94bf3c21c3322bcf32e4236d4722`.
- #13 merged `2026-07-09T23:37:03Z`, `merge_commit_sha=45cc1f0a1113ab7a8f8492b2c1e6e71b3db84893`.

Evidence: <https://api.github.com/repos/menno420/fleet-manager/pulls/12>, <https://api.github.com/repos/menno420/fleet-manager/pulls/13>.

### 15. Wind-down audit / README claim: “21/21 spot-checked incidents verified … zero fabrication found”

**Verdict: UNVERIFIABLE from concise public primary evidence in this pass.**

I can verify that the audit document exists in `superbot` history and that PR #1913 merged it, but the claim is a compound assertion over 21 incident-level checks. The target documents and README do not expose a machine-readable manifest of the exact 21 sampled incident IDs plus their expected primary evidence in a way that can be re-run without relying on the audit's own internal citations. Re-verifying it properly would require reconstructing each incident from the wind-down audit's narrative and independently opening each PR/commit/CI record.

Evidence for the document/PR existence only: <https://api.github.com/repos/menno420/superbot/pulls/1913>, <https://github.com/menno420/superbot/blob/main/docs/eap/fleet-winddown-audit-2026-07-09.md>.

## Pattern notes

1. **Fleet-wide arithmetic is stronger than per-repo prose.** The 116-merge census reproduced exactly, but the overnight one-liner for `superbot-next` drifted badly.
2. **Snapshot “zero” claims rot immediately.** “Zero open PRs” is unsafe unless timestamped and tied to an API transcript; the live state already differs.
3. **CI/test claims need command-level specificity.** `superbot-games` is the good example: `73+48` is real, and the CI gap is also real because the workflow names only `tests/`.
4. **Cumulative-vs-window language is a recurring ambiguity.** `fleet-manager` “18 PRs” is defensible as cumulative repo history, but false as the same overnight window used by the paragraph around it.

## Recommended corrections

1. In `fleet-overnight-review-2026-07-10.md`, replace the `superbot-next` one-liner’s “~20 PRs up the testing ladder” with a narrower statement such as: “2 overnight PRs (#98/#99) landed status/backlog prep after the prior evening's band-5 work.”
2. Timestamp or qualify the “zero open PRs” headline, or change it to “zero open PRs at review snapshot” and include the snapshot time plus API query transcript.
3. Clarify whether `fleet-manager` “18 PRs” is cumulative project output or overnight output; if overnight, correct it to 3 for 00:00–06:15Z.

---

## Independent verification addendum (Claude, 2026-07-10)

Five of the fifteen claims were re-verified by a second, independent method
(local git history in superbot; fresh clones + pytest for superbot-games;
GitHub API for superbot-next). **All five reproduced exactly:**

| Claim | This audit said | Independent re-check | Verdict |
|---|---|---|---|
| 1 (superbot overnight count) | 13 | 13 distinct PRs on first-parent `main`, 00:00–06:15Z | exact |
| 4 (superbot-next window) | only #98, #99 | #98 merged 00:57:42Z, #99 merged 01:10:01Z; titles verbatim; #95/#97 merged pre-midnight | exact |
| 7 (superbot-games tests) | 73 + 48 | `pytest --collect-only`: 73 and 48 | exact |
| 8 (CI gap) | workflow runs only `tests/` | `substrate-gate.yml:62` = `python3 -m pytest tests/ -q`; the step comment itself says the gate ran zero tests before it | exact |
| 9 (#1910 merge time) | 23:18:36Z | `git log`: 2026-07-09T23:18:36Z | exact |

Corroboration: fleet-manager's own `docs/planning/gen2-launch-record-2026-07-10.md`
§5.1 independently corrected "~80 fleet PRs" to the same **116** this audit
reproduced.

**One verdict-precision note:** claim 3 ("zero open PRs") is labeled REFUTED,
but the audit's own caveat concedes the statement may have been true at the
review snapshot and only provably differs *later*. For a time-indexed snapshot
claim, the accurate verdict under this audit's own definitions is
**UNVERIFIABLE as written** (with the fix it already recommends: timestamp +
API transcript). The refutation stands only against the *durable/unqualified*
reading.

The three recommended corrections at the end of this audit are endorsed; the
`superbot-next` "~20 PRs up the testing ladder" correction (claim 4) is the
load-bearing one and should be applied to
`docs/eap/fleet-overnight-review-2026-07-10.md`.
