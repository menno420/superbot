# Foundational-mechanics ultracode outputs — adversarial review (2026-07-03)

> **Status:** `audit` — read-through review of the two foundational-mechanics ultracode lanes.
> Reviewed Prompt A's merged runtime/logic report, the required planning docs, and the current source
> behind a sample of high-impact claims. Prompt B's expected final report was not present locally at
> review time, and PR #1691 appeared to still be an in-progress session-card PR rather than a landed
> presentation/verification report.
>
> **Read-only review note:** this document records review findings only. It does not approve an
> implementation, does not add new rebuild requirements by itself, and does not supersede source or
> owner rulings. Source wins over this document under Q-0120.

> **Post-review status (2026-07-04, open-PR merge sweep):** written 2026-07-03 while PR #1691 was
> still open — the Prompt-B report (`presentation-verification-mechanics-2026-07-03.md`) has since
> **merged**, so the "Prompt B — low / unavailable" verdict below is about *this review's inputs*,
> not the landed report. The recommended synthesis-then-Stage-2 sequence has partly happened since:
> the Fable-5 capstone judgment (#1701), the foundational kernel design bridge (#1708), and the
> Gate-0 grammar-freeze + Phase-B L0 build-order (#1716, `gate-0/`) consumed both foundations
> reports. The ten verified Prompt-A samples and the owner-gated-decision filter remain live input.

## Required reading checked

- `docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`
- `docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md`
- `docs/planning/rebuild-critical-review-rubric-2026-07-03.md`
- `docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md`
- `docs/planning/rebuild-hub-navigation-presets-2026-07-03.md`
- Current source behind sampled high-impact Prompt A claims.

Prompt B's expected report file, `docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md`, was not present in this checkout. The only local foundations report was Prompt A's runtime/logic report.

## Overall trust verdicts

### Prompt A — runtime/logic: **high**

Prompt A is credible and useful enough to feed rebuild planning, but it is too large to consume raw.
It needs a synthesis pass before Stage 2 authors use it subsystem-by-subsystem.

Reasons for the high trust rating:

- It stayed mostly inside the runtime/logic lane: manifest/compiler, namespace, invocation logic,
  resolver, authority, audited mutation, composition/workflow, event bus, lifecycle, persistence,
  cooldowns, DB/import, settings, substrate-kit, and related engine-room seams.
- It explicitly excluded B-owned presentation/proving surfaces and marked handoff seams for spanning
  mechanics such as fuzzy matching and response/result grammar.
- Its top issue ledger is mostly supported by current source in the sampled claims.
- It self-reports refuted-and-dropped claims, plausible claims, unverified claims, and near-duplicate
  merges, which increases trust in the process.

Main caveat: the ledger has 246 issues and 33 owner-gated calls. It needs clustering into a smaller
set of Stage 2 foundations, owner decisions, and implementation follow-ups.

### Prompt B — presentation/proving: **low / unavailable**

Prompt B cannot be meaningfully trusted or scored yet because its final deliverable was unavailable
in this checkout. The foundational brief says Session B should land a report in the same folder as
Prompt A, but no `presentation-verification-mechanics-2026-07-03.md` file existed locally at review
time.

This is not a finding that Prompt B's claims are wrong; it is a finding that there were no final
Prompt B claims available to sample. The requested top-10 presentation/proving verification could
not be completed until Prompt B lands its report.

## Verified high-impact Prompt A findings

The review sampled high-impact runtime/logic claims rather than attempting to re-audit all 246
issues.

### 1. Stale claim: a central command-typo resolver already ships

**Verdict:** supported.

Prompt A's highest-ranked issue says planning text claiming there is no central command-typo resolver
is stale. Current source contains `utils.command_resolution`, with `AUTO`, `SUGGEST`, and `NONE`
outcomes, destructive-command carve-outs, ambiguity handling, and prefix-command wiring through
`bot1.py`'s `CommandNotFound` handler.

Planning implication: rebuild planning should re-baseline C-5 as **port and generalize the shipped
resolver**, not **invent fuzzy resolution from nothing**.

### 2. Runtime lock is released before gateway drain

**Verdict:** supported.

`bot1.py` explicitly drops the runtime lock before `bot.close()` drains, as an LP-4 fast-deploy
handoff. Prompt A's claim that this creates a bounded dual-live overlap risk is credible.

Planning implication: owner/planning must choose between release-after-drain and fast-release plus
durable idempotency keys for every event-driven mutation.

### 3. Scope locks are process-local only

**Verdict:** supported.

`core/runtime/scope_locks.py` documents that the primitive stays process-local and that distributed
locks are out of scope. This supports Prompt A's claim that scope locks do not protect against
cross-replica duplicate handling during overlap windows.

Planning implication: if fast deploy handoff remains, critical event-driven awards need durable
idempotency keys or an equivalent cross-instance correctness mechanism.

### 4. Post-commit event emission is best-effort, not durable outbox delivery

**Verdict:** supported.

`utils/db/pool.py` documents that event-bus emission belongs after the transaction commits, and
`core/events.py` documents an in-process publish-accepted event bus. Prompt A's outbox/idempotency
risk is credible.

Planning implication: the rebuild should classify event delivery as best-effort or at-least-once per
EventSpec, rather than leaving all post-commit side effects implicit.

### 5. Bot-owner override does not cover all channel-access denials today

**Verdict:** supported.

`core/runtime/command_access.py` allows bot-owner/operator bypass for bootstrap commands, but the
non-bootstrap `DISABLED_EXCEPT_BOOTSTRAP` and selected-channel denial branches do not include a
bot-owner override. That supports Prompt A's authority finding.

Planning implication: Q-0227's owner override should be implemented once at the resolver/authority
chokepoint and paired with transparent server audit logging.

### 6. Paid version-mismatch recovery can clear before refunding

**Verdict:** supported for the blackjack sample.

In blackjack tournament recovery, version-mismatched rows are cleared and skipped before the later
refund path. Prompt A's refund-before-drop invariant is therefore credible.

Planning implication: every pre-debited persisted session needs a declared version-mismatch policy,
including refund/compensation behavior.

### 7. C-1 resolver centralization is foundational, not optional polish

**Verdict:** supported.

The conventions doc defines C-1 as the convergence point for all four invocation rungs, authority,
argument validation/coercion, cooldowns, audit, and execution. Prompt A's many C-1 findings cluster
around one real foundation: every surface must pass through one resolver contract.

Planning implication: Stage 2 should not let each subsystem define command execution, authority,
cooldowns, audit, or error semantics independently.

### 8. Fuzzy matching has a clean A/B handoff seam

**Verdict:** supported.

Prompt A correctly covers fuzzy matching logic and leaves the private one-tap `did you mean` surface
to Prompt B. Current source reinforces the seam: logic classifies outcomes, while rendering today is
just a public text suggestion with no confirm button.

Planning implication: Prompt B should cover the rendering and interaction contract; Prompt A's logic
finding should not be treated as UI scope bleed.

### 9. Preset/template fragmentation is real but crosses the A/B boundary

**Verdict:** supported, with overlap risk.

Prompt A's preset/template finding is credible from a data/model/apply perspective, and the hub
planning doc independently says presets and help customization are working but fragmented. However,
B must own the UX/editor/preview/rendering side.

Planning implication: synthesis should define a shared preset contract with A owning storage/apply
semantics and B owning generated-hub preview/editor behavior.

### 10. The owner-gated queue is directionally useful but needs filtering

**Verdict:** supported with cleanup needed.

Prompt A generally flags rather than decides owner-gated calls. Some owner gates are genuinely owner
level, while others are architecture or implementation choices that should not burden the owner.

Planning implication: split Prompt A's owner queue into true owner/product decisions, architecture
lead decisions, and implementation-detail follow-ups.

## Unsupported, stale, duplicated, or overreaching findings

### Prompt A

- **Not enough synthesis:** the report is high quality but too large. Its 246 issues should not be
  fed directly into Stage 2 as independent tasks.
- **Duplicate clusters remain:** C-1 resolver, C-2/workflow atomicity, durable lifecycle/tasks,
  authority/owner override, cooldowns, and event delivery appear as many separate rows. That is
  useful evidence, but planning should consume each cluster as one foundation.
- **Owner-gated over-labeling:** some items marked owner-gated are likely architecture-lead or
  implementation-detail decisions. The owner should get only true product/operational trade-offs.
- **Limited scope bleed:** Prompt A mentions some B-owned presentation surfaces, but usually as
  explicit handoff seams. I did not find this to invalidate the runtime report.
- **Frozen dispositions mostly not reopened:** Prompt A generally pressure-tests frozen decisions
  by finding downstream failure modes, rather than re-litigating Q-0219 through Q-0236.

### Prompt B

- **Unavailable final report:** no presentation/verification report was available locally, so no
  Prompt B claims could be verified.
- **Stage 2 gap:** until Prompt B lands, the rebuild lacks the companion review for hub/navigation,
  panel rendering, card/media, interface presets UX, help projection, response rendering,
  correctness oracle, and layout simulator.

## Scope overlap / gap map

| Area | Prompt A status | Prompt B status | Review |
|---|---:|---:|---|
| Manifest grammar/compiler/snapshot | Covered | Not B-owned | Clean |
| Namespace registry/shared-verb naming | Covered | Help projection consumes names | Clean seam |
| Invocation ladder logic | Covered | Suggestion/help rendering B-owned | Clean seam |
| Fuzzy matcher | Logic covered | Rendering should be B-owned | Clean seam |
| C-1 resolver | Covered | B consumes results | Clean |
| Authority/owner override | Covered | B must re-check panel callbacks | Needs coordinated seam |
| Draft/preview/confirm internals | A covers apply semantics | B owns UX/preview rendering | Overlap risk |
| WorkflowResult/response grammar | A covers logic/error semantics | B owns presentation grammar | Needs synthesis |
| Presets/templates | A covers data/apply/preset kinds | B owns hub/editor/preview UX | Needs synthesis |
| Hub/nav/panels/persistent views | Excluded by A | B-owned | Gap until B lands |
| Card/media engine | Excluded by A | B-owned | Gap until B lands |
| Help/description projection | A covers input to resolver/NL/fuzzy | B owns projection/rendering | Needs seam |
| Correctness oracle/rubric/layout simulator | Excluded by A | B-owned | Major gap until B lands |

## Owner-gated decisions that genuinely need owner attention

1. **Deploy handoff posture:** release-after-drain versus fast-release plus idempotency keys.
2. **Atomicity semantics for Discord-side multi-step actions:** define what atomic means when
   Discord operations cannot be rolled back.
3. **Event delivery posture:** classify events as best-effort or durable/at-least-once.
4. **Bot-owner override scope and transparency:** confirm it spans permission, capability,
   channel-access, setup, and component callbacks, with visible server audit logging.
5. **Preset hide-versus-disable behavior:** when a hub preset excludes a bucket, decide whether the
   feature is hidden only or disabled for that guild.
6. **Free-for-everyone abuse/cooldown posture:** define default free usage, bypass predicates, and
   owner/cap tier interactions.
7. **Per-tenant guild lifecycle:** confirm whether join/leave lifecycle becomes an L0 kernel
   primitive before Stage 2.

## Recommended next action

**Finish Prompt B, then synthesize both reports before Stage 2.**

Do not run the full Stage 2 subsystem walk from Prompt A alone. Prompt A is credible, but it needs a
synthesis pass; Prompt B is still missing and owns several foundational presentation/proving
contracts that Stage 2 needs.

Recommended sequence:

1. Finish/merge Prompt B's presentation/verification report.
2. Synthesize Prompt A + Prompt B into a compact foundations checklist:
   - C-1 resolver contract;
   - authority/owner override contract;
   - C-2 workflow/preview/confirm/apply semantics;
   - event delivery/outbox posture;
   - lifecycle/restart/idempotency posture;
   - cooldown/free-use posture;
   - preset/hub hide-versus-disable contract;
   - correctness oracle/layout simulator obligations.
3. Run Stage 2 subsystem walk only after those shared contracts are explicit.

## Review commands used

- `pwd && rg --files -g 'AGENTS.md' -g 'docs/planning/**' -g 'docs/analysis/rebuild-discovery/foundations/**' | sed -n '1,120p'`
- `find .. -name AGENTS.md -print`
- `git status --short`
- `sed -n '1,220p' docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`
- `sed -n '1,260p' docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md`
- `gh pr view 1691 --json state,headRefName,files,title,body,url`
- `git fetch origin pull/1691/head:pr-1691 --no-tags`
- opened `https://github.com/menno420/superbot/pull/1691/files`
- `sed -n '1,260p' docs/planning/rebuild-critical-review-rubric-2026-07-03.md`
- `sed -n '1,260p' docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md`
- `sed -n '1,220p' docs/planning/rebuild-hub-navigation-presets-2026-07-03.md`
- `rg -n "^## Ranked|^### Issue|^\\| [0-9]+|Owner-decision|needs-owner" docs/analysis/rebuild-discovery/foundations/runtime-logic-mechanics-2026-07-03.md`
- `rg --files disbot | rg '(command_resolution|events.py|command_access.py)$'`
- `nl -ba disbot/utils/command_resolution.py | sed -n '1,220p'`
- `nl -ba disbot/core/events.py | sed -n '1,130p'`
- `nl -ba disbot/core/runtime/command_access.py | sed -n '330,420p'`
- `nl -ba disbot/bot1.py | sed -n '535,590p'`
- `nl -ba disbot/bot1.py | sed -n '830,895p'`
- `nl -ba disbot/cogs/blackjack_cog.py | sed -n '240,270p'`
- `nl -ba disbot/utils/db/pool.py | sed -n '165,185p'`
