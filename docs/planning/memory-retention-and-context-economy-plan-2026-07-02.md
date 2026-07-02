# Memory retention & context economy — the deletion policy, hard limits, and the retention simulator (2026-07-02)

> **Status:** `plan` — owner-directed design session (in-chat brainstorm, 2026-07-02; PR #1643 is the
> provenance). **Extends** [`orientation-cost-reduction-plan-2026-06-30.md`](orientation-cost-reduction-plan-2026-06-30.md)
> (which stays authoritative for the boot-path compression it covers) and supplies the concrete design
> for the fresh-rebuild strategy's §5.2 "substrate's own context budget" gap
> ([`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md)). Method:
> [`simulation-driven-design-2026-07-02.md`](simulation-driven-design-2026-07-02.md) applied to the
> memory system itself — the simulator is **built and run**: `tools/sim/retention_policy_sim.py`.
> Every number below is a 2026-07-02 measurement or a sim output labeled as such.
> **Owner decisions recorded (Q-0214, same day, live):** delete+tombstones posture confirmed ·
> owner inbox = the website `/updates` feed (export must read harvest tables) · shrink duty =
> checker+routine (no per-session ritual; supersedes orientation-plan Workstream D) · rebuilt-repo
> ledger depth = verdict + short why.

## 0. TL;DR

The memory system **archives but never deletes**, and its own session-ender rules (Q-0089 idea,
Q-0102 review, per-session log) mandate growth with no mandated shrink — so the corpus grows
**linearly by construction** (~12–20k words/day of session logs alone). Today 55% of the 1.6M-word
markdown corpus is terminal content, ~70% of grep file-hits land in it, and the boot surface is 26k
words. The policy below keeps every live guarantee, converts terminal content to **git-backed
provenance behind tombstones/stubs**, and caps the living files — enforced by a checker with an
auto-fix actuator, not by exhortation. Sim-verified: **~70% lower expected context cost per session
vs. keep-everything, with zero modeled retrieval loss**, and the corpus becomes **bounded** instead
of linear.

| Class | Terminal state | Policy (sim-selected) | Mechanism |
|---|---|---|---|
| Binding docs, contracts, guidebook rules | never | **never touched** (hard constraint) | — |
| `.sessions/` logs | at birth | **DELETE, harvest-gated** at max(2 bands, 14 days): a log is deletable only when its slug appears in a **committed pass-record harvest table** (per-file evidence, never mere age); the full run-report (⚑ decisions · ⚑ manual steps · 💡 · 📊 telemetry · reflection counts) lands in the pass record first; one grep-visible index line per pruned log (per-band sharded); logs cited from **any tracked file** are held | `check_retention.py --fix`, single-writer (claims lock) |
| Historical plans (`docs/planning/`) | on `historical` rebadge | **ARCHIVE-with-stub after 2 bands** (Q-0210 pattern); DELETE only after 8 bands with zero inbound refs | reconciliation pass step |
| Idea files (implemented) | on grooming | **DELETE after 4 bands**, one-line tombstone in the ideas README index | `check_retention.py --fix` |
| Idea files (rejected) | on grooming | **KEEP body** (tiny class) — under Q-0172 any agent may build without approval, so the rejection rationale must stay grep-findable | — |
| Router decided Q-blocks | on decision | **ARCHIVE with pointer stubs — never delete** (~5,422 working-tree Q-refs must keep resolving) | orientation plan B1–B3 |
| Ledger tails (`current-state.md` narrative, roadmap history, `current-state-archive.md`) | rolling | **compress to per-band one-liners past 2 bands**; archives get windows too | recon pass + trim actuators |
| `.session-journal.md` | living | **stop-growth word cap at ~8,500** (today 8,349); shrinking below that has no lawful overflow target while CLAUDE.md promotion is owner-gated | `check_retention.py` gauge |
| `.session-journal-archive.md` | frozen (zero reads since 2026-06-08) | **deletion DEFERRED** — CLAUDE.md L136 cites it and is owner-gated; rider on the orientation plan's owner-reviewed CLAUDE.md pass | orientation plan A |
| Claims | at close | already delete-at-close — **the precedent, unchanged** | `check_stale_claims` (exists) |

## 1. Origin & goal

Owner-directed brainstorm (2026-07-02): the keep-everything-forever default is quietly costing
context — every new agent wades through completed plans, stale session entries, and long-decided
questions before reaching live work. Shift to **aggressive deletion (not just archival) + hardcoded
limits that cap the corpus**, with the numbers found **empirically by a simulator** rather than
guessed — the same sim-driven method the repo now applies to the bot, turned on the memory system
itself. The result must fold into the finalised AI-memory substrate-kit (which reserves
"memory-integrity/quarantine + a context budget") and apply to this repo now.

## 2. Measured evidence (2026-07-02, verified against the repo per Q-0120)

**Corpus composition** (git ls-files + status-badge scan; commands in §Appendix):

- Repo-wide markdown: **1,489 tracked files / ~1.67M words**; `.sessions/` (541k) + `docs/` (1.03M)
  are 97% of it.
- **Terminal content: 876 files / 924k words = 55% of all words** (badges historical/audit +
  `.sessions/` + archives). Live: 413 files / 710k words; 47 files carry no badge.
- `.sessions/`: **736 files / 541k words in 27 days** (2026-06-06 → 07-02); median log 724 words;
  created at 10–60/day (mean ~27, last-7-days ~16, peak 52 on 2026-06-22). **No retention deletion
  has ever occurred** — history's one deliberate log deletion was the owner-directed wrong-claim
  removal (#1278), a precedent *for* this policy, not against it.
- `docs/planning/`: 189 files / 397k words — 71 `historical` (199k words) vs 57 `plan`; the index
  README still says "~85 files" (it was true on 2026-06-19).
- `docs/ideas/`: 172 files / 130k words (145 active-badged); the ideas README index alone is
  **13,093 words**.
- Question router: **67,839 words / 7,913 lines / 218 Q-blocks** — the largest md file in the repo
  by 2.3×; its Q-0210 archive is a 26-line stub with 0 blocks moved.
- Boot surface (unconditional always-read: CLAUDE.md 5,169 + collaboration-model 2,336 +
  current-state 6,555 + journal 8,349 + AGENT_ORIENTATION 3,292 + `.claude/rules/` 548): **26,249
  words**, before any task-specific reading.

**Read/reference behavior** (measured, not assumed):

- **Grep noise:** over 20 representative working-term greps, **69.6% of file-hits land in terminal
  docs**. Discovery — not the boot route — is where terminal mass taxes every session.
- **Session logs are write-once:** only **5.3%** (39/736) are ever cited from outside `.sessions/`
  — and reading those contexts, they are provenance anchors in router Q-blocks ("decision recorded
  in session X"), not later reads. Cross-references *inside* `.sessions/` never span time: **in
  date terms, zero references ever reach a log 2+ days old** (86 same-day + 11 next-day, all
  parallel-session coordination + the Q-0102 review). The consumers that matter are structural and
  *young*: the next session's review, the band's reconciliation pass, the owner's ⚑ audit trail.
- **Historical plans: 96% (68/71) are cited by live docs — but that number is index plumbing.**
  The plan index lists every plan by construction; roadmap.md (26 citing entries), the router (14),
  and current-state.md (12) carry "shipped #N (plan-link)" history lines — provenance decoration,
  not load-bearing instruction. The honest afterlife rate: **3/41 historical plans (7.3%) were
  ever cited by a session log after their historical-badge date** (4 citing sessions out of 735 =
  0.54%), vs. 8.3% of sessions citing plans while active. **Deletability cascades:** compress the
  ledger tails first, and most plan bodies lose their last inbound reference. One hard catch: **3
  plans are cited from code** (e.g. `disbot/views/ux_lab/home.py:66` renders its design-plan path
  as runtime UI text; `scripts/new_subsystem.py` docstring) — the reference gate must scan code,
  not just docs.
- **The journal archive is a dead file:** `.session-journal-archive.md` has been frozen since
  2026-06-08 (it holds only pre-`.sessions/`-migration history), and **zero of 736 session logs
  have ever recorded reading, grepping, or citing it**. The reconciliation-pass snapshots (32
  files, the largest terminal class in `docs/planning/`) are read only by their immediate
  successor pass (25/31) — never by a session 2+ days later.
- Both soft ratchets that exist (top-level docs 20/20, recently-shipped 20/20) sit **exactly at
  their caps** today — the growth pressure is constant.

**Enforcement history** (what the repo has already proven about itself):

- The only CI-hard docs gates are `check_docs --strict`'s badge/link/pinned/reachable checks — and
  **reachability explicitly exempts `historical`/`archive` badges**, so terminal content
  accumulates unlinked and invisible to every checker.
- Advisory budgets do not hold: AGENT_ORIENTATION.md states its own ~250-line cap and sits at 484
  (~2×, unenforced); the ▶ Next-action callout hit a ~40KB wall *before* its 6KB gauge shipped;
  **Q-0210's router archive was decided 2026-06-28 and has been skipped by every reconciliation
  pass since** (130→131 unclassified blocks; the archive is still a stub). The orientation plan
  itself concedes "permission-to-prune alone hasn't been sufficient."
- What *does* hold: **advisory + actuator + cadence/fix-on-sight** — not blocking. The precise
  split (the adversarial round corrected this plan's own first draft here): stale-claims surfacing
  is **warn-only by explicit owner decision** (Q-0206, `continue-on-error` in `code-quality.yml` —
  it never blocks a merge), yet the loop works: it surfaced a merged branch's leftover claim during
  this very session and the passing session deleted it. `trim_recently_shipped.py` (dry-run
  default, idempotent, recon-invoked) keeps its ratchet at 20 the same way. The repo has **zero
  hard global-state gates** — its one hard-and-holding gate, the session gate, is **diff-scoped**
  (engages only on what the PR itself adds). The lesson is not "make caps block"; it is "give
  every gauge an actuator and a cadence, and reserve hard CI for defects the diff itself
  introduces."

## 3. The retention principle — reference topology decides, not sentiment

A doc's afterlife is determined by two mechanical facts: **is it on a reading route**, and **does
live content reference it**. That yields three tiers:

1. **Live** (binding docs, active plans, living ledgers, the guidebook): on a route or cited as
   authority → stays in-tree, **budgeted** (caps + gauges). Never touched by retention. This is the
   hard constraint, by construction: the policy only ever sees terminal-state docs.
2. **Referenced-terminal** (decided Q-blocks — 5,422 plain-text `Q-NNNN` refs across the working
   tree (the recorded 9,084/9,690 figures counted `.git` objects — scope caveat verified
   2026-07-02); historical plans while still cited; anything a live doc *or code file* links):
   **archive in-tree with a pointer stub** (exactly Q-0210's mechanism). The archive is a *reference target*, not reading
   material — off every route, grep-resolvable forever. The proof-case for why the router class
   never graduates to deletion: **Q-0035 is cited by zero docs anywhere, yet two sessions genuinely
   invoked it 13 days after it was decided** — router blocks have real, unpredictable afterlife
   that filename-citation analysis cannot see, so the router keeps Q-0210's
   archive-with-stub-forever semantics.
3. **Unreferenced-terminal** (95% of session logs; plan bodies after the ledger-tail cascade;
   groomed idea files; aged journal-archive entries): **DELETE**, leaving the cheapest
   discoverability artifact that still works — a one-line tombstone in the owning index for docs
   that get cited by name (plans, ideas), a single dated banner for classes that don't (session
   logs).

### The git-history question (the owner's §2) — where "git already preserves it" holds, and where it breaks

**It holds almost everywhere, with one addition.** Every deleted file remains one
`git show <sha>:<path>` away, PR history keeps the review trail, and this repo merges (never
squashes branches away), so tree states persist. For content whose future access pattern is *rare,
deliberate, forensic* — "why did we do X in June?" — git + a pointer is strictly better than
in-tree retention: the rare reader pays one hop; every other session stops paying rent. The claims
lane has run exactly this way for weeks with zero recorded misses.

**Where it breaks — and what each break costs:**

1. **Grep is the retrieval system.** Agents discover by grepping the working tree; nobody greps
   git history speculatively. A deleted file without a pointer is not "archived," it is
   *undiscoverable*. → **Tombstones/banners are mandatory**: title + date + last path + one-line
   what-it-was. That converts "lost" into "one extra hop," at ~20 words instead of ~2,700.
2. **Plain-text reference integrity.** ~5,422 working-tree `Q-NNNN` references resolve by grep into
   the router;
   filenames are cited in prose — **and in code**: 3 historical plans are cited from `disbot/` and
   `scripts/` (one as runtime UI text). Deleting a referenced body dangles them. → the
   **inbound-reference check is the deletion gate** (mechanical, not judgment): `check_docs`' CI
   link gate already hard-fails dangling relative links in docs; a new plain-text pass covers
   Q-numbers and filename mentions **across the whole tree (docs + `disbot/` + `scripts/` +
   `tools/` + `.github/`)**. Referenced content archives with a stub instead (tier 2).
3. **Non-git consumers.** The dashboard export (`scripts/export_dashboard_data.py`) and any website
   surface read the working tree; the substrate-kit export ships the tree. → windows must respect
   the *slowest structural consumer* — concretely, nothing is pruned before the reconciliation pass
   that reads it has run and committed its harvest table (full run-report lines into the pass record).
4. **Squash/rewrite risk is a policy invariant, not a footnote:** the git-provenance argument is
   valid *because* history is append-only here. The rule ships with that stated assumption.

Deletion is safe **exactly when** discoverability is preserved by a cheaper artifact and no live
reference dangles — both checkable by machine. That is what makes it safe *unattended*.

## 4. The policy, per class

§0's table is normative. Details and edge cases:

- **Session logs.** The window is **max(2 bands, 14 days)** — the band term is the sim knee; the
  day floor covers the two human/machine consumers the sim doesn't model (measured owner action-lag
  runs ~19 days on control-plane items, and `scripts/export_dashboard_data.py` feeds the owner's
  website `/updates` from the newest ~60 raw logs) — at ~2–3k words/session over the sim-optimal
  window, the stated price of the owner-inbox floor, retunable by one constant once the pass-record
  inbox proves itself. And **deletion is harvest-gated, never age-gated** (the panel's central
  amendment): `--fix` may delete log X only if X's slug appears in a **committed pass-record
  harvest table** — per-file machine evidence, not a hand-advanced marker; a skipped pass
  self-blocks exactly the unharvested files. The Q-0210 skip record (a decided mandatory step
  unexecuted across 3+ passes) is why neither age nor a promised step can be the trigger. The
  harvest takes the **full run-report**:
  ⚑ Self-initiated, ⚑ Owner decisions needed, ⚑ Owner manual steps, 💡 ideas, status/PR line, the 📊
  telemetry footer (5 numbers), and the band's aggregate reflection counts ("needed but not pointed
  to" / "pointed to but didn't need" — 142/115 today, the system's route-quality telemetry). The
  pass record becomes the owner's durable audit surface; drill-down to a raw log = its index line →
  git. Each pruned log leaves **one grep-visible index line** (slug · title · PR#) in a pruned-log
  index under `.sessions/` — grep-shaped consumers (the Hermes dispatch skill greps `.sessions/` for
  slice names to decide shipped-vs-not) hit the line instead of silent-empty; that skill's text is
  updated in the same PR. **Owner inbox is the website feed (Q-0214.2):** `export_dashboard_data.py`
  gains a harvest-table source alongside raw logs in PR 2, so the `/updates` feed survives pruning
  by construction. Logs cited from **any tracked file** (the router cites 30 in backtick
  prose as canonical `Home:` lines — live-badge scoping would miss them) are held automatically.
- **Historical plans.** On rebadge: index row moves to Historical (existing convention). After 2
  bands: body moves to `docs/planning/archive/`, and a **one-line stub file stays at the old path**
  — required, not optional: inbound relative links must keep resolving (`check_docs` link gate;
  the docs/archive README already records that moving historical docs breaks links, which is why
  in-place rebadging won — the stub gets both: links resolve *and* the 2,700-word body leaves the
  grep surface). After 8 bands with zero inbound refs (post ledger-compression cascade): delete
  body, tombstone row stays in the index Historical section. `reference`-badged companions
  (sim-pinned numbers etc.) are **live**, not terminal — untouched.
- **Reconciliation pass records.** Keep the newest 2 (the working set); older ones compress to
  their summary header + the harvested run-report lines (they are the audit trail), then archive.
- **Ideas.** Implemented ideas: tombstone line in the README index (which already exists as the
  lifecycle ledger) + delete after 4 bands — the content shipped; the body is redundant with the
  plan/PR record. **Rejected ideas keep their bodies**: under Q-0172 any agent may promote an idea
  to implementation without approval, and the Q-0089 dedup surface is a grep of `docs/ideas/` — a
  one-line tombstone is too weak to stop re-building something the owner declined; the class is
  tiny (a handful of files). The 13k-word README itself gets a word budget — it is a living index,
  not a second archive.
- **Ledger tails.** Compress current-state.md's marked historical-narrative block (lines ~29–194) +
  roadmap history sections to per-band one-liners, under two hard rules from the adversarial round:
  (1) **migrate-then-compress** — the narrative is *not* purely historical (verified: the Q-0036
  denial-copy gate, the V-16 ⛔ PNG-pack block, and "#702 still never owner-played" live only there,
  absent from § Gates) — every still-live gate/blocked/never-verified item moves to § Gates or its
  sector file *before* its band collapses; (2) **compressed one-liners keep PR numbers and plan
  filenames verbatim** (they are how "which plan shipped #884" resolves by grep). The overflow
  archive (current-state-archive.md, 29k words) gets the same treatment past its window.
- **Router.** Unchanged from Q-0210/orientation-plan: decided blocks archive with pointer stubs,
  never delete, never renumber. This plan adds only the *enforcement*: the router-archive step
  becomes part of the retention checker's report, so skipping it a fourth time turns red instead
  of silent.
- **Journal + archive.** Guidebook keeps its "correct-in-place, keep lean" contract with a real
  gauge — a **stop-growth cap at ~8,500 words** (today 8,349). Not a shrink target: 94 rule bullets
  live there and their only promotion outlet (CLAUDE.md) is owner-gated, so forcing a cut would
  evict candidate rules with no lawful home. The archive is **frozen pre-migration history with
  zero recorded reads since 2026-06-08** — the eventual move is deleting the file, but CLAUDE.md
  L136 cites it and CLAUDE.md is owner-gated, so the deletion is a **rider on the orientation
  plan's owner-reviewed CLAUDE.md pass** (one pointer line changes in the same breath), not a PR-2
  action. It costs 6k words of nothing-on-any-route in the meantime.
- **Generated packs** (`docs/agent/generated/`): build artifacts, regenerated, exempt (already
  marked NOT SOURCE OF TRUTH).
- **Unbadged files** (47 today): the retention checker refuses to classify them and *reports* them
  — badge-or-triage becomes part of the prune step, so the unbadged class shrinks to zero instead
  of hiding from policy.

## 5. Hard limits & enforcement — caps that trigger prunes, not nags

The repo's own history splits cleanly: **advisory = ignored** (AGENT_ORIENTATION 2× its cap;
Q-0210 skipped 3+ passes), **checker+actuator = held** (recently-shipped ratchet; stale-claims).
So every cap below ships **with its actuator** or it doesn't ship (Q-0194 friction→guard, applied
to retention itself). Two enforcement tiers by prune type:

**The enforcement polarity (the panel's central inversion — matches the owner's recorded
posture):** corpus-*state* caps are **never PR-blocking** — they warn-print in PR CI forever, the
proven ratchet pattern, per the owner's own Q-0206 choice (offered blocking and picking warn-only
for stale claims four days before this plan) and the repo's total absence of hard global-state
gates. **Hard CI red is reserved for diff-scoped defects the PR itself introduces** — this PR
deletes a file that still has inbound references elsewhere in the tree; this PR introduces a
dangling reference — the session-gate precedent (engage-when-present, never ambushes an unrelated
PR). Cap breaches escalate by **opening work, not blocking work**: a push-to-main check auto-opens
a `retention`-labeled routine issue (body emitted by `check_retention --issue-body`, label-scoped
dedupe, the `reconciliation-trigger.yml` pattern) that the routine answers.

**Tier M — mechanical prunes** (rule fully determines the action):
session-log prune, journal word gauge, recently-shipped trim (exists), router live-size gauge,
unbadged-file report.
→ `scripts/check_retention.py` (new): reports every class vs. its cap (warn census in PR CI);
`--fix` performs the mechanical prunes (dry-run default, house posture like
`trim_recently_shipped.py`). Two hard rules on the actuator itself: **deletion eligibility is
per-file machine evidence, not a trusted marker** — `--fix` may delete log X only if X's slug
appears in a *committed* reconciliation-pass record's harvest table (a skipped harvest
self-blocks exactly the unharvested files — no global freeze, no hand-advanced line to drift);
and **pruning is single-writer** — `--fix` requires holding a retention claim file
(`docs/owner/claims/`, the existing lock), in practice recon-routine-owned, with per-band sharded
prune-index files (`.sessions/pruned/band-NNNN.md`) instead of any shared append-point (the
claims sim measured shared-append at ~98% merge-conflict vs 0% per-file).

**Tier J — judgment prunes** (need reading: plan archival/deletion, ledger-tail compression,
pass-record compression):
→ bound to the **every-30-PR reconciliation pass** as a numbered step in its saved prompt
(`docs/operations/autonomous-routines.md`) — but the *enforcement* is not the prompt (Q-0210 is
already a numbered mandatory step there, with a self-exempting clause, skipped by every pass
since it was decided): it is the **retention-debt escalation** above (debt past threshold →
labeled routine issue → a session whose entire job is the prune) plus the per-file evidence rule,
which makes "skipped the step" mean "nothing new becomes deletable" rather than "debt silently
grows invisible". PR-3 also adds a retention row to the control-plane table so a dead
ROUTINE_PAT (the trigger's documented single point of failure) is live-verified instead of
silently freezing the loop.

**Safety rails (all tiers):** prunes land as dedicated docs-only commits (one `git revert`
restores everything); the inbound-reference gate blocks any delete with a dangling ref — hold
scope is a reference from **any tracked file, live or terminal, docs or code** (the router cites
session logs in backtick prose; historical audits cite them too; live-badge scoping would miss
both), with sanctioned reference removal happening only through the compression steps;
`check_docs`' link gate is CI-hard already and the plain-text Q/filename pass joins it — running
**census-only for at least one band** (its hold-set spot-verified against the router's 30
backtick `.sessions/` citations) before the first `--fix` deletion; deletions are recorded as
tombstones/index-lines at prune time (grep-discoverable); irreversible-by-policy content (binding
docs, owner-guidance, ADRs, `reference` badges, rejected ideas, the router) is **out of the
pruner's jurisdiction entirely** — allowlist of prunable classes, not a blocklist of protected
ones.

**The caps** (sim-derived starting values; each is a named constant in `check_retention.py` with
this plan cited; owner can retune any of them by number):

| Cap | Value | Basis |
|---|---|---|
| `.sessions/` retention | max(2 bands, 14 days) **AND slug in a committed harvest table** | sim knee: 1–2 bands; day floor = owner-lag + dashboard feed; per-file evidence, not age, is the trigger |
| plan archive window | 2 bands after `historical` | afterlife citations cluster near completion (halflife ~3 bands) |
| plan delete window | 8 bands + zero refs | conservative 4× the citation halflife |
| idea delete window | 4 bands after terminal | grooming pass cadence |
| journal gauge | stop-growth at ~8,500 words | shrink-to-4k would save ~4.3k words/boot but has no lawful overflow target (CLAUDE.md promotion is owner-gated) — owner's call if he wants the deeper cut |
| router live gauge | orientation plan B2's budget (set by B0's result) | deferred to that plan |
| active plans (`plan` badge) | soft gauge at 40 (57 today) | forces finish-or-park pressure; census prints the number |
| self-declared per-doc caps | read from each doc's own header (e.g. AGENT_ORIENTATION's ~250 lines) | absorbs [`orientation-doc-linecap-guard`](../ideas/orientation-doc-linecap-guard-2026-06-30.md); warn-first → graduate |
| top-level docs, recently-shipped | 20 / 20 (exist) | unchanged |

## 6. The simulator — design, results, and how to re-run

`tools/sim/retention_policy_sim.py` (stdlib, deterministic, seeded; the four sim-driven-design
guardrails in its docstring). Model: corpus classes grow at measured birth rates; agents pay
boot + discovery (grep/ls noise from in-tree terminal stock, measured profile) + back-reference
costs by disposition (in-tree read / tombstone→git hop / bare-delete re-derivation) + a small
stale-encounter tail; policies prune on band cadence under the reference gate. Objective:
**expected words/session**, hard constraint retrieval-miss ≈ 0, secondary objective (owner's "lean
by construction") = smallest tree at horizon among policies within 5% of the best primary.

**Results (2026-07-02 calibration, 20-band horizon):**

| Policy | words/session | vs. status quo | tree @ horizon | miss/band |
|---|---|---|---|---|
| status quo (keep everything) | 92,066 | — | 2,694k (unbounded, linear) | 0 |
| archive-everything @2 bands | 31,041 | −66% | 2,694k (unbounded) | 0 |
| delete-bare @1 band (no tombstones) | 29,964 | −67% | 806k | **0.119 — infeasible** |
| **winner: sess=delete (harvest-gated) · plan=archive@2b · ideas=delete@4b · ledger-compress · journal-capped** | **~27,300** | **−70%** | **1,648k (bounded)** | **0.000** |

What the sim actually teaches (more durable than the point numbers):

1. **The knee is early.** Session-log windows beyond ~2 bands buy nothing — back-reference demand
   decays with ~3-band halflife and the cited 5% are reference-held anyway.
2. **Archive vs. delete is a ~0.4% read-cost difference — with the sign favoring ARCHIVE.** Stated
   plainly (the adversarial round caught the draft soft-pedaling this): the sim's primary objective
   ranks session-log archive at 27,161 w/s vs delete at 27,267 at every window; **deletion wins only
   on the secondary objective** (tree size 1,648k vs 2,607k words at horizon, bounded vs unbounded).
   So DELETE-for-logs is the owner's stated lean-by-construction goal applied as a tiebreak, **not a
   sim discovery** — the sim's finding is that the read-cost objective genuinely does not
   distinguish them, i.e. the choice is safe to make on principle. The sim-optimal
   archive-everything variant remains on the table at one config change if the owner prefers
   maximal reversibility over boundedness.
3. **Plans ≠ session logs.** Real afterlife demand + 96% citation-lock makes archive-with-stub the
   right mode for plans (and for the router — Q-0210 had this right).
4. **Bare deletion is the one genuinely dangerous mode** (miss-rate 0.119/band) — tombstones are
   what make aggressive deletion safe, at ~20 words each.
5. **Boot dominates the residual** (~24.7k of 27.3k). Retention fixes discovery + growth;
   the **orientation plan fixes boot** — compose them for the full win (~4× total).
6. **Sensitivity:** the near-tie group ("prune terminal content within 1–2 bands + compress ledger
   tails") is rank-stable under ×⅓/×3 sweeps of the assumption-grade constants — back-ref rates,
   stale rate, session velocity, **and the archive-side/discovery weights the first sweep omitted**
   (archive pollution, grep-hit rate, maintenance) — worst case (+3× velocity) costs +2.1k w/s;
   the policy self-stabilizes because prunes scale with input. The archive-vs-delete ~0.4% gap
   sits inside the sweep noise, which is precisely why it is a values call, not a measurement.

Honest limits: the w/s figures are model estimates, not telemetry (the `context-cost-telemetry`
idea is the upgrade path); the sim models **agent** costs only — owner-review lag, website, and
dashboard surfaces are handled structurally (harvest-gating, pass records) rather than modeled,
so call it **sim-informed** where humans are involved. The *structure* of the result (early knee,
archive≈delete on read-cost, plans≠logs, tombstones-or-nothing, boot dominance) is what to trust,
and it survived the sweeps. Re-run: `python3.10 tools/sim/retention_policy_sim.py` (≈seconds);
recalibrate constants per §Appendix when velocity or composition shifts.

## 7. Failure modes & the adversarial evidence

**The strongest counter-evidence in the repo, addressed head-on.** On 2026-06-30 a 37-agent audit
(~2.7M tokens) of the 111 in-place historical docs found only **7 (6%) safe to delete**; 14 initial
delete votes were **refuted** — broken inbound links, sole-source facts — and 45 "need condensing"
([`superbot-fresh-rebuild-vision-2026-06-30.md`](../ideas/superbot-fresh-rebuild-vision-2026-06-30.md)
§4: "even deliberately hunting for dead weight, 94% of what looked deletable wasn't, once checked").
That audit refutes *naive* deletion — and specifies this policy's gates: its two refutation classes
are exactly what the mechanics make impossible (**broken links** → the reference gate blocks the
delete; **sole-source facts** → the harvest step moves them to durable homes *before* the window
opens), its "45 need condensing" is the tail-compression workstream, and its population (historical
plans/audits) is the class this policy *archives*, not deletes. The class it did not cover —
session logs — is where the measured afterlife is near-zero. The audit's 7 confirmed-delete files
(still awaiting the maintainer's go-ahead) become PR 2's first deletions under the new gates.

**The incident record splits the failure modes cleanly** (30+ incidents swept from
journal/sessions/router, 2026-07-02):

- *Bloat failures are pointer-prose failures*: the stamp wall Hermes acted on (named an
  already-shipped slice, 2026-06-15 — and the wall had been archived once and **regrew**); the
  40.5KB ▶ callout ("a pointer that's allowed to grow unboundedly becomes a liar", band-990); stale
  plan-status headers and folio lines misleading sessions mid-task (3 recorded); the router
  physically exceeding the Read tool's size limit (Q-0210's own session read it in slices); the
  orientation tax making Sonnet "compact on arrival" — owner-recorded as costing "an entire weekly
  bucket every week". **Deferral is the meta-failure: "a cleanup always one session away is never
  done"** (band-#1200's deferred prune never happened; the wall grew another pass) — which is why
  every cap here ships with its actuator.
- *Missing-context failures are invisibility failures, not deletion failures*: every duplicate-work
  incident (#677/#678, #1221, #804, the ultracode B4 collision) traces to claim/PR visibility gaps;
  every re-derivation traces to knowledge parked in non-read homes (session logs, code comments).
  **No incident in the repo's history traces to a deleted doc** — in 27 days only 8 non-claim docs
  were ever deleted (1 owner-directed wrong-claim removal #1278, plus supersessions/renames), and
  the two that left dangling refs caused zero recorded problems.
- *The owner has already directed deletion where it matters most*: PR #1278 — "completely remove
  wrong/fixed claims from the repo — not annotate them 'was wrong, now fixed' — so a future session
  never reads about a problem that no longer exists." Retention-by-default is not a standing owner
  preference; provenance-by-default is.

**The adversarial panel (2026-07-02, this session).** Three lenses attacked the draft —
over-deletion red team, archive-everything steelman, enforcement critic. All three returned
**adopt-with-amendments**; every blocking/serious objection is folded into §4/§5/§6 above. The
seven that changed the policy: **(1)** harvest-gated deletion upgraded to **per-file committed
evidence** (a slug in a pass-record harvest table — mandatory recon steps demonstrably skip
(Q-0210, 0-for-3+), so neither age nor a promised step nor a hand-advanced marker can gate
destruction); **(2)** the **enforcement polarity inversion** — corpus-state caps warn forever
(the owner's own Q-0206 posture; this plan's first draft even mischaracterized the stale-claims
step as blocking — it is `continue-on-error`), hard CI red only for diff-scoped defects the PR
introduces; **(3)** per-log grep-visible index lines, per-band sharded (the Hermes dispatch skill
greps `.sessions/` for shipped-slice detection — silent-empty would read as "not shipped" →
duplicate work; a shared index would re-import the measured 98%-conflict append-point); **(4)**
hold-scope = any tracked file (the router's 30 backtick `Home:` citations of session logs are
invisible to live-badge scoping); **(5)** rejected ideas keep their bodies (Q-0172 lets any agent
build without approval — the rejection rationale is the dedup surface); **(6)** a **14-day floor**
on the log window (owner action-lag measured ~19 days; the website `/updates` feed reads the
newest ~60 raw logs); **(7)** the sim-honesty restatement in §6.2 (archive wins the primary by
~0.4%; deletion is the owner's boundedness tiebreak) plus a **shadow band + `do-not-automerge` on
the first executing prune** — the first mass deletion in repo history must not land on the
docs-only fast path reviewed by nobody. Notably, even the archive-everything steelman conceded
the absolute: the owner has already directed removal-not-annotation for wrong content (#1278),
and both soft ratchets sit pinned at their caps.

Standing risks and their mitigations:

- **A wrongly-deleted doc**: bounded by the triple filter (terminal badge + past window + zero
  inbound refs) and restorable by one revert of a docs-only commit. Worst realistic case is the hop
  cost, not loss.
- **Owner's audit trail**: full run-report harvesting (⚑ decisions, ⚑ manual steps, 💡, 📊) into pass records happens *before* a band's
  logs become prunable; pass records persist (compressed, never bare-deleted). The owner reviews a
  30-PR band summary rather than 30 raw logs — strictly less to wade through.
- **Parallel-session races**: prunes are recon-pass-owned (Tier J) or single-writer under the
  retention claim lock with per-band sharded indexes (Tier M); the claims lane already exercises
  concurrent delete safely at a measured 0% conflict rate.
- **Actuator bugs**: dry-run default, Q-0105 unverified header with graduate-or-delete, and the
  checker (not the actuator) is what CI trusts.
- **Unattended safety**: every mechanism above is deterministic and reviewable in the PR diff;
  nothing deletes in a hook or at merge time.

## 8. What this plan does NOT change

Router canon (no renumbering, no moving canonical text — Q-0210), binding docs and CLAUDE.md
(owner-gated; the one rule-change this plan wants — the standing shrink ritual — goes to the
router as a DISCUSS block per orientation-plan Workstream D, drafted by the implementing session
under the next free Q-number), the orientation plan's workstreams (still authoritative for
CLAUDE.md/router/AGENT_ORIENTATION compression), and the safety brakes (irreversible/external
work still asks first).

## 9. Implementation plan (the ultracode handoff — 3 PRs)

**PR 1 — the checker + the mechanical lane (foundation).**
`scripts/check_retention.py`: class census (badge scan), per-cap gauges, retention-debt count,
plain-text reference pass (Q-numbers + filename mentions, scanned across docs **and** `disbot/` /
`scripts/` / `tools/` / `.github/` — code cites plans), `--fix` for Tier-M prunes (session-log
window; dry-run default). Wire soft census into `code-quality` next to `check_docs`. Harvest step
added to the reconciliation routine prompt (full run-report → committed harvest table in the
pass record). Unit tests over a fixture tree.
*No deletions of real content in this PR.*

**PR 2 — the first real prune (the cascade, top-down; shadow-first).**
Prerequisites: PR 1's reference pass has run census-only for ≥1 band, its hold-set spot-verified
against the router's backtick `.sessions/` citations; **one shadow band** — PR 2 first commits the
would-delete report (file list + per-file ref-scan evidence) and the next reconciliation pass
spot-verifies a sample against ground truth (the same Q-0105 graduation the cap flip gets).
**The first executing prune PR carries the `do-not-automerge` label (Q-0114)** so the owner sees
history's first mass deletion before it lands — every later prune rides normal auto-merge. Then
in order: **migrate** still-live gate/blocked items out of the ledger narrative → ledger-tail
compression (current-state narrative block → per-band one-liners keeping PR#s/filenames verbatim;
roadmap history sections; current-state-archive entries past window) → re-run reference pass →
archive newly-unreferenced historical plans (body → `docs/planning/archive/`, one-line stub file
stays at the old path) → **execute the 2026-06-30 audit's 7 confirmed-delete files** (owner
reviews them with this plan) → first session-log prune (only slugs present in committed harvest
tables; per-band sharded index lines written; the Hermes dispatch-skill grep text updated in the
same commit; run under the retention claim lock). Each step its own commit,
`check_docs --strict` green throughout. Update plan-index convention text ("never deleted" →
tiered rule, citing this plan + PR #1643 as owner-reviewed provenance) and `.sessions/README.md`
banner.

**PR 3 — the escalation loop + kit export.**
Graduate the **diff-scoped** hard gates (deletes-referenced-file / introduces-dangling-ref) once
proven; wire the retention-debt threshold to the routine-issue trigger (`retention` label,
label-scoped dedupe, `--issue-body`, the routine registered in `autonomous-routines.md`, a
retention row in `check_loop_health`'s control-plane table so a dead ROUTINE_PAT is
live-verified); record that orientation-plan Workstream D is settled by Q-0214.3 (shrink = checker+routine, no
per-session ritual — no DISCUSS block needed); port the checker +
policy table into the substrate-kit as the **context-economy engine** (kit's §5.2 slot: budget +
retention + tombstone semantics as a portable capability, config-driven classes so any repo it's
planted in defines its own table).

Prerequisite ordering with the orientation plan: none — they are independent lanes (this plan
never touches CLAUDE.md/router bodies); but the *full* win needs both, and B0–B3 should run soon
regardless (three passes overdue).

## 10. Where it lands in the substrate-kit

The kit reserves "memory-integrity/quarantine + a context budget" (fresh-rebuild §5.2). This plan
is the context-budget half made concrete: a **context-economy engine** = (a) the class/badge
taxonomy + reading-route declaration, (b) the budget gauges + retention windows as config, (c) the
checker + actuator pair, (d) the tombstone/stub semantics, (e) the simulator itself (re-runnable
per repo to *find* that repo's numbers — the kit ships the search, not our constants). The
rebuilt repo starts with this engine on day one (its design spec already commits to the 7,000-word
orientation budget + provenance-separated ledger; this engine is what keeps it true).

## Appendix — re-calibration commands

- Corpus/badge census: `git ls-files '*.md'` + first-12-lines `> **Status:**` scan (the checker
  automates this; the sim's `--calibrate` prints the recipe).
- Grep-noise profile: run the 20-term grep set (sim docstring) and split file-hits by class.
- Velocity: `git log --diff-filter=A --format='%ad' --date=short -- .sessions/` bucketed per day;
  `git log --merges --since='14 days ago'` for band wall-clock.
- Back-reference rates: filename-mention grep of `.sessions/` names from outside `.sessions/`;
  historical-plan filename grep across live docs (excluding index/archives).
- Boot surface: `wc -w` over CLAUDE.md, collaboration-model, current-state, journal,
  AGENT_ORIENTATION, `.claude/rules/*`.
