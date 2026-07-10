# Fleet doctrine enforcement audit — adversarial review (2026-07-10)

> **Status:** `audit`
>
> Scope: public `menno420/fleet-manager` and `menno420/superbot`, read-only evidence gathered from fresh public clones on 2026-07-10. Required reading checked: `fleet-manager/docs/gen2-blueprint.md`, `fleet-manager/docs/playbook.md`, `superbot/docs/eap/eap-program-review-2026-07-10.md` §5, and `superbot/docs/planning/projects-eap-evaluation-log.md`.

## Executive findings, ranked by severity

1. **Wake/routine doctrine was already falsified and only partially corrected.** The superbot EAP log records an owner screen recording at 2026-07-10 ~11:01Z proving the earlier “routine creation is walled on both sides” belief false: some Project sessions can create in-Project routines, but run observability remains broken. `fleet-manager/docs/gen2-blueprint.md` now says the cadence is “agent-executable” and `fleet-manager/docs/capabilities.md` records the correction, while `fleet-manager/docs/planning/gen2-launch-record-2026-07-10.md` still contains stale “PLATFORM GAP / walled on BOTH sides” wording. Evidence: superbot `docs/planning/projects-eap-evaluation-log.md` lines 295-311; fleet-manager `docs/gen2-blueprint.md` wake rider; fleet-manager `docs/capabilities.md` routine section; fleet-manager `docs/planning/gen2-launch-record-2026-07-10.md` lines 83-97.
2. **Merge-authority doctrine is internally inconsistent with the machinery.** The blueprint says gen-2 lanes “ALWAYS” land their own PRs, no PR waits for review, and post-merge review is the rule. The playbook also states classifier R12 blocks self-merge without review and permits only auto-merge arming while checks are pending; R21 admits REST merge-on-green is primary on born-red/no-CI repos. I found no in-repo gate that prevents draft PRs, enforces auto-merge-at-creation, requires review-queue entries for “needs second eyes,” or drains that queue. Evidence: fleet-manager `docs/gen2-blueprint.md` §1/§2; `docs/playbook.md` R5/R12/R21; `docs/ideas/review-queue-drainer-2026-07-10.md` lines 16-18.
3. **Most binding seed-state rules are prose-only.** The only fleet-manager CI gate is `substrate-gate`, which runs `bootstrap.py check --strict` and a control-only status shortcut. That covers substrate/session/status hygiene; it does not enforce CI-tier assignment, ready-vs-draft, merge authority, environment-spec testing, claims seeding, heartbeat timing, walking skeleton timing, routines, or model/time card fields. Evidence: fleet-manager `.github/workflows/substrate-gate.yml`.
4. **The record already contains several “claimed solved by doctrine” classes recurring as evidence.** Same-inbox/order races are documented in R19; mid-flight scope evaporated in fleet-manager PR #8; superbot's EAP log says claim/file overlap checking only reads a local claims dir; superbot's grand review says do-not-automerge gen-1 carve-outs were still merged by ratification. These are not hypothetical risks. Evidence: fleet-manager `docs/playbook.md` R19/R20; superbot `docs/planning/projects-eap-evaluation-log.md` line 143; superbot `docs/eap/gen1-grand-review-2026-07-09.md` lines 104-105.

## Enforcement inventory by rule

Legend: **Machinery** means an actual checker, CI gate, template, or generated file exists in the audited trees and plausibly catches at least some violations. **Prose-only** means I found only instructions, ledgers, or manual practices. **Partial** means machinery exists but does not catch the rule as written.

### Blueprint seed-state checklist and deltas

| Doctrine item | Classification | Evidence and gap |
|---|---:|---|
| Substrate-kit adopted and `check --strict` green at repo birth | **Partial machinery** | Fleet-manager has `.github/workflows/substrate-gate.yml` invoking `python3 bootstrap.py check --strict`; this catches engaged substrate hygiene after the workflow exists, not “at repo birth” across new repos. |
| CI + required checks aligned; no legacy/skipped required contexts; CI tier assigned | **Prose-only / external settings** | I found CI YAML, but required-check settings live in GitHub branch rulesets outside the repo. Fleet-manager owner-queue still asks humans to change substrate-kit rulesets, proving this is not repo-enforced. |
| Conventions file day 0: READY never draft | **Partial template only** | Superbot has `.github/PULL_REQUEST_TEMPLATE.md` and fleet-manager templates mention READY; no checker/API policy rejects draft PRs. |
| Conventions file: lane always lands own PRs; landing path by repo shape | **Prose-only / platform-classifier dependent** | R12 says direct self-merge is classifier-blocked, R21 says REST merge-on-green is primary in two shapes; no repo checker enforces the selected path. |
| No PR waits for review; needs-second-review ledger and/or Codex mention | **Prose-only** | `docs/review-queue.md` exists, but `docs/ideas/review-queue-drainer-2026-07-10.md` says no lane/routine/order owns draining it. |
| Forward-only git; repo conventions override harness defaults | **Prose-only** | No hook/CI rule found that rejects force-push, rewrite, or harness-default deviations. |
| `control/` files, capability manifest, `PLATFORM-LIMITS.md`, retro questions planted day 0 | **Partial machinery** | Fleet-manager contains `control/`, `docs/capabilities.md`, and substrate files. I found no `PLATFORM-LIMITS.md` in fleet-manager, and no birth-time checker for the complete file set. |
| `claims/` dir seeded and shared surfaces pre-resolved | **Prose-only in fleet-manager; partial in superbot only** | Superbot has `scripts/check_stale_claims.py` and `scripts/check_lane_overlap.py`, but the EAP log notes overlap scans local claims only; fleet-manager has no comparable checker. |
| Environment spec from `environments/SPEC-TEMPLATE.md`; setup script tested, shape-agnostic, `exit 0` | **Prose-only / template** | Fleet-manager has the template and archetype scripts. I found no CI job that executes every environment script or verifies `exit 0`. |
| Heartbeat-before-work: first act is status/WIP commit | **Partial machinery** | `substrate-gate` requires a session log for non-control diffs and has a control status gate, but it cannot prove the first act occurred before work or within a time budget. |
| Walking skeleton through full merge path in first 20 minutes | **Prose-only** | No timestamp checker ties branch/PR/CI/merge proof to the first 20 minutes. |
| Model + time line on every session card from card #1 | **Partial machinery in superbot; unclear in fleet-manager** | Superbot `check_session_gate.py` gates session-card readiness and telemetry append, but fleet-manager's `substrate-gate` delegates to substrate `bootstrap.py`; I did not verify a model+time-field checker in the fleet-manager tree. |
| Boot-time capability audit before impossible claims | **Prose-only** | `docs/capabilities.md` exists, but no checker proves it was read before a wall/impossibility claim. |
| Every mission names done-when and between-orders standing default | **Prose-only** | No parser found for order text completeness. |
| Control fast lane for cheap heartbeats | **Machinery** | Fleet-manager `substrate-gate` has a `control/**`-only fast lane and status-only gate. |
| Inbox `status: new` semantics baked into control README | **Template/prose only** | `control/README.md` documents ritual/semantics; no checker prevents re-execution based on `status: new`. |
| Wake cadence by lane class; routines self-arm | **Prose-only and partly falsified** | The cadence is a table and a capability claim; the EAP log falsifies the earlier wall claim and leaves observability gaps. No repo evidence proves routines are armed or firing. |
| CI-tier standard, fast-full Tier 1, nightly matrix, Tier 0 substrate hold | **Prose-only / simulation-backed** | `tools/sim/ci_tier_sim.py` supports the recommendation, but no generator/checker enforces tier labels, job shape, wall-time, or nightly matrix in born repos. |

### Playbook R1-R21

| Rule | Classification | Evidence and gap |
|---|---:|---|
| R1 Fetch before read | **Prose-only** | No wrapper/checker prevents stale local reads. |
| R2 Verify against repos | **Prose-only** | Normative audit rule; no machine can know whether a reviewer trusted a report. |
| R3 Match merge event to right PR | **Prose-only** | No release/announcement checker found. |
| R4 Worker prompts include no background timers + final report | **Partial template** | Fleet-manager `templates/worker-preamble.md` can carry the wording; no lint ensures every dispatch uses it. |
| R5 Arm auto-merge at creation where checks can pend | **Prose-only / external API behavior** | No PR metadata gate verifies arming time; R21 narrows scope. |
| R6 READY never draft | **Partial template only** | Templates say it; no draft-rejection machinery. |
| R7 One writer per repo sequential | **Prose-only** | No global lock/queue prevents two workers writing the same repo. |
| R8 REST merge-on-green fallback for GraphQL quota | **Prose-only** | Operational advice; no checker. |
| R9 One writer per file; appends only on inboxes; per-lane files | **Partial in superbot, prose in fleet-manager** | Superbot has overlap/concurrency scripts; fleet-manager has no equivalent fleet-wide lock and R19 documents actual races. |
| R10 First-declared + claim-filed wins | **Prose-only** | Arbitration policy only; no enforced claim lease. |
| R11 Orders carry done-when; owner asks carry click-level instructions and stay valid | **Prose-only** | No schema/linter for inbox or owner-queue items. |
| R12 Direct self-merge without review blocked; pending auto-merge allowed | **Platform machinery, not repo machinery** | This relies on the external classifier/GitHub behavior named in the rule. The repo cannot enforce it. |
| R13 Empty-repo bootstrap via Contents API | **Prose-only** | Recipe only. |
| R14 Superbot docs reachability + valid badge tokens | **Machinery in superbot** | `scripts/check_docs.py --strict` implements badge/link/reachability/freshness rules and is covered by tests. |
| R15 Env setup scripts defensive (`exit 0`) | **Prose-only / templates** | No CI execution/lint of all env scripts found. |
| R16 One deduplicated owner queue in `docs/owner-queue.md` | **Prose-only** | File exists; no scanner detects scattered asks in chat/docs. |
| R17 Owner-action gate with exact-wall evidence and WHAT/WHERE/HOW/WHY/UNBLOCKS | **Prose-only** | No structured schema/checker for ⚑ items. |
| R18 Read/update capability manifest before impossibility claims | **Prose-only** | File exists; no enforcement of read-before-claim. |
| R19 Serialize same-inbox appends; re-read before merge | **Prose-only** | The rule itself cites repeated collisions; no lock/checker found in fleet-manager. |
| R20 Mid-flight scope addition requires ack or re-dispatch | **Prose-only** | Based on PR #8 failure; no PR-comment ack gate. |
| R21 REST merge-on-green primary on born-red/no-CI; arm-at-creation elsewhere | **Prose-only / platform behavior** | External wall documented; no repo mechanism chooses or validates landing path. |

## Claims already falsified or contradicted by the record

| Severity | Claim or doctrine | Falsifying/contradictory evidence |
|---:|---|---|
| Critical | “Routine creation is walled on both sides.” | Superbot EAP log 2026-07-10 ~11:01Z says owner recording proves some Project sessions can self-arm routines; fleet-manager capabilities now says Projects CAN create routines. Stale launch record still says “PLATFORM GAP / walled on BOTH sides.” |
| Critical | “Gen-2 lanes always land their own PRs” as an unconditional rule. | R12 says direct self-merge is classifier-blocked; R21 says auto-merge arming is impossible in born-red/no-CI shapes and REST merge-on-green is primary. The doctrine is really “use one of several externally permitted paths,” not unconditional self-landing machinery. |
| High | “Needs-second-eyes post-merge review is safe if logged.” | The review queue has no owner: fleet-manager idea `review-queue-drainer-2026-07-10.md` explicitly says no lane, routine, or order owns draining it. A logged concern can silently rot. |
| High | “One-writer/inbox serialization prevents order races.” | R19 records substrate-kit ORDER 008/009 and ORDER 005 races that cost PRs; I found no lock machinery in fleet-manager. |
| High | “Mid-flight comments/scopes are deliverable to running sessions.” | R20 records fleet-manager PR #8 merged after a Task-4 PR comment went unread and evaporated. |
| Medium | “Claims/overlap machinery prevents shared-surface races.” | Superbot EAP log says `check_lane_overlap.py` reads only local claims, leaving cross-repo overlap under-covered. |
| Medium | “READY-never-draft is handled by templates.” | Templates are present, but no repo gate rejects draft PRs; the grand review lists superbot-games PR #5 and #11 as draft/stacked work needing manual recovery. |
| Medium | “Owner-queue wake-routine asks are owner-only.” | The EAP log and fleet-manager capabilities correction say at least some routine creation can be self-armed; prior owner-click queue items were partially invalid. |

## Ten riskiest prose-only rules and cheapest enforcement proposals

1. **R19 inbox serialization / one inbox writer** — silent double-execution corrupts fleet orders. *Cheapest enforcement:* add a `control/inbox.lock` lease file with owner+expires fields and a CI checker that rejects inbox edits without a valid lease and a “read HEAD at” timestamp.
2. **Merge-authority/R21 landing-path selection** — a wrong path parks or prematurely merges work. *Cheapest enforcement:* add a PR close checklist bot/check script that reads PR state via GitHub API and fails if the PR is draft, unarmed when armable, or lacks a documented REST merge-on-green reason.
3. **Review-queue post-merge drain** — “merge anyway” becomes “never review.” *Cheapest enforcement:* scheduled CI issue/comment that fails or opens an issue when `docs/review-queue.md` has non-empty entries older than N hours without a linked resolution.
4. **Wake cadence / routine armed and observable** — idle lanes miss orders indefinitely. *Cheapest enforcement:* commit a `docs/routines.json` manifest and a daily checker comparing expected cadence to last heartbeat/status timestamps, with explicit “unobservable” failures.
5. **R7/R9 one writer per repo/file** — parallel writes create conflicts and duplicated work. *Cheapest enforcement:* require every active order to add a claim file under `claims/<repo>/<path>.json`; CI rejects overlapping non-expired claims.
6. **R11 done-when and owner ask completeness** — ambiguous orders waste sessions and owner attention. *Cheapest enforcement:* lint `control/inbox.md` and `docs/owner-queue.md` for required headings/fields (`DONE-WHEN`, `WHAT`, `WHERE`, `HOW`, `WHY`, `UNBLOCKS`, `valid-until: until-acted`).
7. **R17 owner-action gate proof** — false owner-only asks spend the owner. *Cheapest enforcement:* require every ⚑ item to include `attempted-by`, `wall-verbatim`, and `fallback-tried` fields; a markdown checker blocks missing evidence.
8. **Environment script defensive setup** — broken setup kills sessions with no report. *Cheapest enforcement:* CI matrix executes every `environments/archetype-*.sh` and `templates/setup-universal.sh` in dry-run mode and asserts exit 0.
9. **Walking skeleton in first 20 minutes** — broken merge path discovered after real work. *Cheapest enforcement:* seed-lane generator writes `docs/launch-proof.md`; CI requires timestamps for branch/PR/check/merge proof before accepting domain files in a new repo.
10. **Capability manifest read-before-impossible** — false “walls” route work to owner or stop progress. *Cheapest enforcement:* define an “impossibility claim” block format and lint any `owner-queue`/status item containing “cannot/walled/impossible” for a `capability-ref:` and `exact-error:` field.

## Verification limits

- I did not inspect private repos or private Project UI state; routine run history and branch-protection rulesets are not fully verifiable from public tree contents.
- I treated public PR numbers and commit names cited inside the audited docs as record pointers, but did not re-query every GitHub PR timeline. Where a mechanism was alleged, I looked for a corresponding file/checker/workflow/template in the public trees before classifying it as machinery.
- “Platform machinery” such as the self-merge classifier and GitHub auto-merge behavior is real only to the extent the cited records report it; it is not controlled by either repo.
