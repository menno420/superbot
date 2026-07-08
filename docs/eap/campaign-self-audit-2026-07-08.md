# Campaign self-audit — coordinator memory vs. git ground truth (2026-07-08)

> **Status:** `audit` — labeled EAP probe (Claude Code Projects evaluation, second mandate).
> **What this is:** the Waves 1–3 coordination campaign (PRs #1844 · #1845 · #1846 · #1850 ·
> #1851 · #1854 · #1855; scratch #1857) was run by a Project coordinator dispatching worker
> sessions. Before any verification, the coordinator wrote down its recollection of the whole
> campaign **from in-context conversation history only** (same day, no context compression, no
> repo search). This document grades that snapshot against git. **Git wins every disagreement;
> discrepancies are the findings.** Wins and misses are both logged; observed and inferred are
> kept separate. Friction items are banked in
> [`docs/planning/projects-eap-evaluation-log.md`](../planning/projects-eap-evaluation-log.md)
> (§6 below points at them).
> **Audited by:** a worker session (this PR), with no access to the coordinator's conversation —
> only the snapshot text and the repo.

## Provenance and method

- The snapshot was recorded **before** verification and is graded as-is — nothing in it was
  silently corrected.
- Ground truth used: `git log` / merge commits on `origin/main`; PR metadata + per-PR commit
  lists via the GitHub API (needed for the three squash-merged PRs whose branch commits are not
  reachable from `main`); check-run records for #1857; the merged artifacts themselves
  (`docs/analysis/server-management-audit-2026-07-08.md`, `scripts/check_supersede_integrity.py`,
  `tests/`, `.github/workflows/code-quality.yml`, session cards in `.sessions/`,
  `git log --full-history -- docs/owner/claims/`).
- Merged campaign branches are absent from `origin` because the repo setting **"Automatically
  delete head branches" is On** (`docs/operations/repo-settings-state.md:37`) — server-side
  deletion on merge, not agent action. The one surviving branch is
  `claude/scratch-fastpath-proof-2026-07-08` (head of the closed, never-merged #1857).

## 1. Roster graded against git

Every discrete, checkable claim in the snapshot was verified. Summary first, then the diff.

| Lane | Snapshot claim (compressed) | Verdict |
|---|---|---|
| W1-A (#1844) | claim `claude__audit-server-management-2026-07-08.md`, audit-only; shipped `docs/analysis/server-management-audit-2026-07-08.md`, 6 LOW / 0 RISKY | **All confirmed** — including the odd double-underscore claim filename, verbatim (commit `a0e4ae1`). Report has F1–F6, all LOW, 0 RISKY (§Counts) |
| W1-B (#1846) | claim `claude-wave1-lane-b-supersede-checker.md`; shipped `scripts/check_supersede_integrity.py` warn-first w/ Q-0105 header, soft-check wired into `check_docs.py`, **16 unit tests**, idea re-badged IMPLEMENTED; #1843 drift fix then dedup/yield after #1848 | **Confirmed except the test count: the shipped file has 15 test functions, not 16** (see Contradictions). Everything else verbatim-true, including the yield story (#1848 merged 11:40:29Z; B's dedup commit `0dc13f6` 11:46) |
| W1-C (#1845) | branch `claude/grooming-wave1-usage-limit-plan`, grooming-only; idea → `docs/planning/usage-limit-aware-routines-plan-2026-07-08.md` (2-PR) + roadmap S5; NEW idea `claim-remote-visibility-scan-2026-07-08.md`; also fixed #1843 drift | **All confirmed** (PR body, commits `5aaa9bd`/`43831a7`, plan doc, roadmap S5, idea file) |
| W2-A1 (#1851) | ownership role row → all 7 tables w/ both service writers; ChannelLifecycleService `:46` vs `:87` fixed; payload row 4→9 values; server_logging v1→v2; folio `:118-119`; nuance: `reaction_role_message_modes` primitives in `utils/db/roles.py` not `role_menus.py` | **All confirmed** — `docs/ownership.md:71` lists exactly 7 tables with `reaction_role_service` + `role_grants_service`; the nuance is in the session card (`:46`) and matches source (`grep -rl reaction_role_message_modes disbot/utils/db/` → `roles.py` only) |
| W2-A2 (#1850) | `tests/unit/invariants/test_reaction_role_write_boundary.py`, 2 tests (AST scan + positive seam); HOLDS 5/5 tables; 16 real writes allowlisted; legacy `reaction_roles` pair (`add`/`remove_reaction_role`) NOT fenced, flagged | **All confirmed** (file has exactly 2 tests; card records "16 real write calls inside the allowlisted files" and the legacy-pair scope note verbatim) |
| W2-B (#1854) | item1 → tracked note on idea file (trigger ~5 clean sessions); item2 → NEW idea `live-tree-test-culprit-attribution-2026-07-08.md`; item3 answered inline in `ci-what-runs-where.md` §2b, verdict "green-by-skip"; item4 → tracked note w/ trigger | **All confirmed** (idea file §Follow-ups carries both A and D notes with the stated triggers; §2b carries the dated green-by-skip answer: 12s run 11:06:56→11:07:08Z on `faaa29f`, fast path skipped pytest incl. the live-tree homing test) |
| W3 (#1855) | `check_plan_homing.py --strict` as always-run named step in required `code-quality` before Python setup; proof-red via scratch draft #1857 (induced unhomed plan, 12s fast path, red, closed w/o merge); proof-green live tree 81/81 | **All confirmed** — step "Plan-homing gate (check_plan_homing)" at `code-quality.yml:96`, `Set up Python` at `:166`; #1857: draft ✓, `do-not-automerge` ✓, 2 files / +7 ✓, `code-quality` conclusion **failure** in **12s** (13:00:20→13:00:32Z) ✓, closed 13:01:00Z unmerged ✓; 81/81 recorded in both the W3 and #1854 cards |
| Terminal states | 7/7 campaign PRs merged; #1857 closed-by-design | **Confirmed** (merged_at on all seven; #1857 `merged: false`) |

### Contradictions (git wins)

1. **"16 unit tests" for the supersede checker → the shipped file has 15.**
   `tests/unit/scripts/test_check_supersede_integrity.py` contains exactly 15 `def test_`
   functions (lines 50–314), unchanged since its only commit `58a2e24`. Notably, the **worker's
   own session card and PR#1846 body also say 16** — the error originated in the Wave-1-B
   worker's self-report, and the coordinator relayed it faithfully. So this is a *report-vs-git*
   drift the coordinator inherited, not a memory corruption — but under the probe's rule (git
   wins) the snapshot claim is wrong.

That is the only roster claim git contradicted. Two more record-level discrepancies surfaced
that the snapshot did **not** make (i.e., they are misses of the record, not of the coordinator
— logged for completeness):

- **W3's session card says the scratch branch was "deleted"; it was not** —
  `claude/scratch-fastpath-proof-2026-07-08` still exists on origin (the deletion attempt hit
  the documented credential-layer 403; see the eval log's clear-path entry). The coordinator
  snapshot correctly said only "closed w/o merge" and did **not** repeat the card's deletion
  claim — a small win for the memory over the written record.
- **The coordinator-side "~25-min" merge-latency figure understates the tail** — see §5
  (scheduling/reliability) and friction entry (c): git shows ready→merged latencies up to
  ~2h28m for the campaign's late queue.

### Unverifiable-from-repo (not contradicted, not confirmable)

- The W1-A subsystem-choice rationale specifics (#1789 automod, #1602 permission-gate, "largest
  folio-covered subsystem") — see §4.
- All coordinator-side observations (sidebar states, timer chains, token blowout) — see §5;
  marked reported-not-independently-verifiable there.

### Precision / recall read

Counting discrete checkable assertions in the snapshot (roster + causality + memory-depth):
**53 verifiable against the repo record → 52 confirmed, 1 contradicted ≈ 0.98 precision.**
A further ~4 assertions are conversation-side and unverifiable from the repo (excluded from the
denominator, listed above). **Recall at the campaign-event level is effectively 1.0**: all 7
sessions, all 8 PRs (incl. the scratch), every branch name, both claim filenames it attempted
(one with its idiosyncratic double underscore), every shipped artifact path, and every finding
count were present — nothing material missing. What the snapshot did *not* contain is
meta-level: the squash-vs-merge-commit split (three PRs squash-merged, four merge-committed),
the one post-flip substantive commit on #1846, and the true merge-latency tail. Fair summary:
**same-day in-context recall was near-verbatim on facts it was told, and its one error was an
inherited reporting error, not a confabulation.**

## 2. Causality chain verified

Each link checked against merged artifact contents (diffs/docs), not dispatch notes:

| Link | Evidence in the merged record | Verdict |
|---|---|---|
| #1844 (F1–F5) → #1851 | #1851's PR body enumerates F1–F5 by number against `docs/analysis/server-management-audit-2026-07-08.md`; each fix is present in `docs/ownership.md` / the folio; the A1 card records per-finding Q-0120 re-verification | **Supported** |
| #1844 (F6) → #1850 | #1850's PR body cites audit finding F6 verbatim ("shipped the audited seam without the ratchet step"); the test file fences exactly the 5 tables F6 names | **Supported** |
| #1846 (follow-ons) → #1854 | #1854's card routes exactly four items and names PR #1846 as their source; items A/D land as §Follow-ups notes on the very idea file #1846 implemented | **Supported** |
| #1854 (item-3 archaeology) → #1855 | #1855's card and the workflow comment (`code-quality.yml:94`) both cite "the PR #1854 archaeology"; the gate closes precisely the §2b green-by-skip gap #1854 documented | **Supported** |

No unsupported links. The chain also demonstrates a full unprompted friction→guard loop in git:
#1846 card-flag → #1854 idea/archaeology → #1855 enforcing CI gate (relevant to §5 proactivity).

## 3. Per-session workflow compliance

Commit-sequence evidence. For the three squash-merged PRs (#1845, #1850, #1851) branch commits
are not reachable from `main` (and branches are auto-deleted), so ordering is attested by the
**PR API commit list** — file-level stats for those first commits are API-level evidence, marked
(api). "Forward-only" is graded as *no force-push evidence*: a clean forward history cannot
prove a force-push never happened, so absence is stated as observed-history-consistent, and
"unverifiable" is said where that is the honest ceiling.

| Session (PR) | Claim in 1st commit | Born-red 1st / flip last | Forward-only | Enders (💡 / ⟲ / Q-0104) |
|---|---|---|---|---|
| W1-A (#1844) | ✓ `a0e4ae1` adds card + claim (2 files) | ✓ open 11:21; flip + claim-delete in `7a19338` 11:36 — last non-merge commit (later commits are main-merge churn) | merge commits only; no force evidence (unverifiable beyond that) | ✓ / ✓ / ✓ |
| W1-B (#1846) | ✓ `562672b` card + claim | ⚠ **deviation**: flip `1ba08da` 11:44, then one substantive commit **after** the flip — `0dc13f6` 11:46 (dedup of the #1843 homing row after #1848's merge-in). Reactive to a parallel lane, docs-only, but it is a post-flip content change on a green-gated PR | merge commits only; no force evidence | ✓ / ✓ / ✓ |
| W1-C (#1845) | ✓ (api) `5aaa9bd` "born-red card + claim" | ✓ flip + claim-delete inside the final work commit `43831a7` (combined, but last) | (api) 3 commits, incl. one main-merge; no force evidence; branch commits unverifiable locally | ✓ / ✓ / ✓ (+ run report + telemetry) |
| W2-A1 (#1851) | ✓ (api) `15e5a37` | ✓ open 11:50:36; work `793217c`; flip as separate deliberate final commit `8451d8d` | (api) no force evidence | ✓ / ✓ / ✓ |
| W2-A2 (#1850) | ✓ (api) `c8dfb74` | ✓ flip + claim-delete inside final work commit `a634948`; later commits are pr-auto-update main-merges | (api) no force evidence | ✓ / ✓ / ✓ |
| W2-B (#1854) | ✓ `0fb52d7` card + claim | ✓ two-commit session; flip in close commit `61d9ce4` | merge commit only; no force evidence | ✓ / ✓ / ✓ |
| W3 (#1855) | ✓ `f528851` card + claim | ✓ open 12:37; work `cd2723b`; flip + claim-drop `5d6ff60` last | merge commits only; no force evidence. Scratch-branch deletion was *attempted* post-close and failed (403) — the deletion intent targeted a scratch ref, not history rewrite; the branch survives | ✓ / ✓ / ✓ (💡 card-only by declared campaign scope) |
| Terminal claims state | — | — | — | `docs/owner/claims/` on main contains no campaign claim files (all deleted at close; net-zero per PR) ✓ |

Compliance read: **7/7 claim-first, 7/7 born-red-first, 7/7 enders complete; 6/7 clean
flip-as-last; 1 post-flip commit (#1846) as the single deviation.** Forward-only: consistent
everywhere the record can show it; strict proof of no-force-push is unverifiable by nature.

## 4. Memory-depth probe

All three depth answers were given **from conversation context, without repo search** (stated in
the snapshot's provenance note and taken at face value — the grader cannot verify what the
coordinator did or didn't search; what is gradable is whether the answers match the record).

1. **"Why server-management for W1-A"** (largest folio-covered subsystem with recent churn —
   #1594/#1618/#1619 server-logging, #1789 automod, #1602 permission-gate): **partially
   verifiable.** #1594/#1618/#1619 are in the audit report (F4, `:128`) and the session card.
   #1789, #1602, and the "largest folio-covered" framing appear **nowhere in the merged record**
   (audit doc, card, PR body) — that rationale lived in the dispatch conversation. Not
   contradicted; unverifiable from the repo. Verdict: consistent where checkable.
2. **"W1-B follow-ons deliberately not acted on = the 4 items"**: **verified.** The #1846 card
   explicitly defers follow-ons to Wave-2 grooming, and #1854's dispatched list is exactly the
   four items the snapshot names, with matching dispositions.
3. **"W1-C's new-idea observation = claims blind window"**: **verified in detail.** The #1845
   card's anti-collision record has the ≈11:15 UTC zero-visible-claims observation; the idea file
   names `check_lane_overlap.py`'s local-only read (`scripts/check_lane_overlap.py:47`), the
   `--remote` `origin/claude/*` scan, and the re-scan-after-own-claim-push protocol line — all
   four specifics the snapshot recalled.

**What this does and doesn't demonstrate.** All answers came from a **same-day, pre-compression**
context: this is a test of *conversation retention and fidelity under load* (many sessions, many
PRs, hours of traffic), and on that test the performance was near-verbatim — down to a
double-underscored filename and a 12-second CI run time. It is **not** a test of durable Project
memory: nothing here shows the coordinator could reproduce this roster tomorrow, after context
compression, or in a fresh session from Project-level memory alone. The one inherited error
(15-vs-16) also shows the ceiling: the coordinator remembers **what it was told**, and cannot
exceed the accuracy of its workers' reports without doing exactly what this probe did — go to
git. A follow-up probe worth running: the same questions after a compression event or in a
successor session.

## 5. EAP axis scores (this campaign only)

Weights: **pass / partial / fail**, one concrete example each. Coordinator-side items are marked
**(reported)** = from the snapshot, not independently verifiable from the repo.

| Axis | Score | Evidence from this campaign |
|---|---|---|
| **Use-case fit** | **partial** | Verified: the fan-out worked — three lanes opened within 60s of each other (11:21–11:22Z first commits), zero duplicated work, one collision resolved by a deterministic yield (#1846 → #1848's row). Against it: the ~4096-byte spawn-brief cap, no direct coordinator→session channel, no coordinator shell (reported; consistent with prior eval-log entries), and the claims blind window at simultaneous start (verified — friction (a)) |
| **Coordinator judgment** | **pass** | Verified: 0 risky actions across 7 PRs — zero `disbot/` runtime changes anywhere in the campaign; file-territory partitions were disjoint by design (docs-only vs tests-only lanes, recorded per-card in anti-collision notes); the W1-B yield-precedence call was correct and cheap. Dispatch scoping was clean enough that workers' cards repeatedly cite "sibling lane owns docs/" |
| **Reliability / completion** | **pass** | Verified: 7/7 campaign PRs merged; #1857 closed-by-design after serving its proof; all 7 sessions reached Q-0103 terminal state with claims deleted. The two background-child resumes (friction (e)) cost time, not completion (reported) |
| **Memory** | **pass** (with the stated limitation) | This probe: ≈0.98 precision / ~1.0 event-level recall from context alone, same-day, pre-compression — near-verbatim on filenames, counts, and timings; one inherited (not confabulated) error. Durable/post-compression memory untested — do not generalize this score beyond same-day retention |
| **Proactivity** | **pass** | Verified in git: W3 (#1855) was self-derived under Q-0194 from #1854's finding without an owner prompt — the full flag→idea→enforcing-CI-gate loop shipped within ~3.5h of the flag, and the gate ground-truth-proofed itself both directions (#1857 red, 81/81 green) |
| **Scheduling** | **fail** | Reported: `send_later` absent at the coordinator (matches the 2026-07-07 eval-log entry — verified call rejection then); two sleeping-timer worker chains died silently; the 09:00 roll-up arrived ~3h late. Repo-side corroboration is the *workaround shape itself* (sleeping-worker chains documented in the eval log). Nothing in this campaign showed a working scheduled wake |
| **Sidebar states** | **fail (thin)** | Reported, single observation: `list_project_activity` showed long-terminal sessions as status "active" at 10:06Z. Not repo-verifiable, n=1 — but it is the axis's only data point this campaign, and it points the same direction as the born-red/auto-merge workaround entry already in the eval log (session lifecycle state isn't a server-honored signal) |

Honesty notes: **scheduling** and **sidebar states** scores rest mostly on coordinator-side
reports; they are consistent with independently-verified prior entries in the eval log but were
not re-probed by this audit. **Memory**'s pass is explicitly scoped to same-day pre-compression
retention (§4).

## 6. Friction bank

The five campaign friction items — (a) claims blind window, (b) `list_pull_requests` token
blowout, (c) CI-churn merge latency (with git-verified numbers: ~22–30 min typical, ~2h10m–2h28m
tail on #1844/#1846/#1854/#1855), (d) bash GitHub-API proxy 403 forcing MCP-only CI polling,
(e) background children not waking their parent worker — are appended in the standard entry
shape to [`docs/planning/projects-eap-evaluation-log.md`](../planning/projects-eap-evaluation-log.md)
(entries dated 2026-07-08, this PR).

## Verdict in one paragraph

The coordinator's same-day memory of a 7-PR, 3-wave campaign was **almost exactly right**: one
false detail in fifty-three, and that one inherited from a worker's own miscount rather than
invented. The campaign record itself is in strong workflow compliance (one post-flip commit and
one wrong "branch deleted" line are the only blemishes git shows). The genuinely weak axes are
the platform's, not the campaign's: scheduling primitives and session-state signals. The most
useful follow-ups this probe suggests: re-run the memory questions post-compression; and treat
worker self-reported counts as unverified until a checker or the auditor recounts them (the
15-vs-16 class — small here, but the same class at runtime-code scale is how false confidence
compounds).
