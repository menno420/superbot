# Rebuild Phase A · Stage 2 readiness review (2026-07-03)

> **Status:** `plan` — readiness review for starting the Phase-A **Stage 2 subsystem walk**.
> This document answers whether the current planning corpus provides enough common rules to walk
> all BUILD-PLAN rows consistently, and defines the proposed Stage-2 review contract. It does **not**
> execute the subsystem walk, approve implementation, or start Phase B.
>
> **Verdict:** `ready after Prompt B merge`.

---

## 1. Readiness verdict

Stage 2 is **ready after Prompt B merge**.

The repo is not blocked: the Stage-2 purpose, most cross-cutting rules, the ordered subsystem row
universe, and the critical-review rubric already exist. The current corpus is strong enough to
show what the subsystem walk must decide, but it is not yet safe to run 43 rows in parallel because
one companion foundation report is still missing from the repo: **Prompt B** from PR #1691, if
available.

Prompt A explicitly scopes itself to runtime/logic mechanics and states that Prompt B covers the
presentation/interaction and verification half. Since Stage 2 must decide hub placement, panel
semantics, preset membership, visual/card/media seams, and verification oracles for every
subsystem, starting the full walk before Prompt B lands risks producing inconsistent or incomplete
outputs.

**Start condition:** Stage 2 may begin when either:

1. Prompt B is merged/available and its owner-gated issues are folded into the template below, or
2. the owner explicitly waives Prompt B as a precondition and accepts that presentation/verification
   gaps may be discovered during Stage 2.

Recommendation: **wait for Prompt B unless the owner explicitly waives it.**

---

## 2. Required preconditions before Stage 2 starts

### 2.1 Document/state preconditions

- **Prompt B available or waived.** Prompt A says Prompt B is the companion presentation/
  interaction half; the repository currently only contains Prompt A under
  `docs/analysis/rebuild-discovery/foundations/`.
- **Use BUILD-PLAN §1.1 as the row universe.** Stage 2 walks the capability rows from
  `NEW-BOT-BUILD-PLAN.md`, including added rows such as the visual card engine, profile surface,
  giveaways, starboard, explore hub, shared ingestion, boards, migration assistant, and ops plane.
- **Do not reopen the capstone feasibility verdict.** Phase A turns the frozen capstone's
  dispositions into exact surface decisions; it does not re-run the all-43 fit audit.
- **Freeze one vocabulary before parallel work.** The corpus currently contains both BUILD-PLAN
  dispositions (`KEEP`, `IMPROVE`, `MERGE`, `REDESIGN`, `ADD`) and Stage-1 D-5 triage
  (`bring back`, `defer`, `drop`, `re-place`). Stage 2 needs one normalized verdict vocabulary.

### 2.2 Mechanical inputs required before Stage 2 starts

- **Shared-verb set.** Compute and publish the shared-verb set from
  `command_surface_ledger.build_ledger()` / the manifest-qualified command walk, not from
  `ground-truth/command-surface.json`; Prompt A says the JSON undercounts grouped command verbs.
- **Slash cap policy.** Decide whether Stage 2 should mark every viable command slash-capable or use
  a `slash-common + prefix-long-tail` policy to fit Discord's top-level/group limits.
- **Command `effect` / safety classification.** Add a Stage-2 column for command effect so the
  safe-default rule is enforceable: read/common commands may have no-argument defaults;
  destructive/ambiguous commands may not.
- **Preset vocabulary.** Freeze the initial preset names Stage 2 can assign. At minimum, use
  `safe-default/full`, `game-server`, `community-server`, `moderation-heavy`, `knowledge-ai`, and
  `custom/owner` until the owner changes them.
- **Preset exclusion semantics.** Decide whether a preset-excluded feature is disabled for that
  guild or merely hidden from the hub.

### 2.3 Owner decisions that should be settled before Stage 2

- **G-22 staging lanes:** one `StagedBuilderSpec` or multiple staging lanes.
- **Slash cap policy:** all slash where possible vs. slash-common/prefix-long-tail.
- **Custom trigger scope:** alternate whole-surface prefixes, word-to-command triggers, or both.
- **NL routing model:** universal manifest-description inheritance vs. per-command/domain opt-in.
- **Error/result envelope home:** inside C-1 / `WorkflowResult` or a separate kernel primitive.
- **Preset exclusion behavior:** hidden-but-runnable vs. disabled.
- **Prompt B owner-gated calls:** any presentation/verification calls that affect Stage-2 columns.

---

## 3. Normalized Stage-2 verdict vocabulary

Every BUILD-PLAN row gets exactly one primary verdict from this set:

| Verdict | Meaning |
|---|---|
| `keep` | Return substantially as-is, with manifest/generated implementation. |
| `improve` | Return, but with explicit gaps closed or features added. |
| `merge` | Functionality returns inside another subsystem or kernel primitive. |
| `redesign` | The user job remains, but the shape changes materially. |
| `drop` | Does not return; record rationale and dependency fallout. |
| `defer` | Not planned now; blocked until owner/prior-art/scope complete. |
| `re-place` | Returns but in a different hub/layer/user-facing shape. |
| `add` | New capability not present in the old 43-subsystem corpus. |

A row may also carry secondary tags such as `blocked-by-gate-0`, `blocked-by-owner`,
`missing-prior-art`, `source-uncertain`, `prompt-a-issue`, or `prompt-b-issue`.

---

## 4. Proposed Stage-2 subsystem template

Use this template for every BUILD-PLAN §1.1 row.

```md
## <Subsystem / Capability Name>

### 0. Row identity
- BUILD-PLAN row:
- Layer:
- Existing BUILD-PLAN disposition:
- Stage-2 triage verdict:
  - one of: `keep`, `improve`, `merge`, `redesign`, `drop`, `defer`, `re-place`, `add`
- If `merge`, merged into:
- If `re-place`, new hub/layer/shape:
- If `drop` or `defer`, dependent rows to re-check under S-2:
- Source confidence:
  - `source-confirmed`
  - `capstone-only`
  - `prompt-a-issue`
  - `prompt-b-issue`
  - `owner-memory`
  - `competitor-derived`
  - `uncertain`

### 1. User/job summary
- Primary user:
- Core job-to-be-done:
- What would be embarrassing to launch without:
- Current prior art in old bot:
- Competitor/prior-art references to benchmark:

### 2. Command surface
| Current/planned command | Final slash form | Final prefix form | Aliases | Shared verb? | Kind (`slash`/`prefix`/`both`/`panel-only`/`event-only`/`NL-only`) | Effect (`read`/`safe-write`/`destructive`/`money`/`moderation`/`external-egress`) | Default with no args? | Notes |
|---|---|---|---|---|---|---|---|---|

Required notes:
- If shared verb: final grouped namespace = `/area verb`.
- If flat: K1 reserved flat name.
- If prefix-only: explain why it is not slash.
- If slash-only: record old prefix compatibility/alias decision.
- If panel-only: name the command/deep-link entrypoint to reach it.
- If event-only: name the listener and authority/audit path.

### 3. Invocation and routing
- Exact invocation:
- Fuzzy typo eligibility: `auto-run safe`, `confirm`, `silent`, or `none`
- NL intent eligibility:
- NL orchestration eligibility:
- Custom trigger eligibility:
- C-1 resolver requirements:
- Authority label(s):
- Bot-owner override implications:
- Cooldown/rate-limit declaration:
- Argument/ParamSpec needs:

### 4. Namespace and collision review
- Shared-verb classification:
- Flat-name reservation:
- Alias reservation:
- Tombstone/legacy reservations:
- Discord slash cap impact:
- Collision risks found:
- Visibility/help projection requirement:

### 5. Hub, navigation, and preset membership
- Top-level bucket:
  - `Games / World`
  - `You`
  - `Community`
  - `Knowledge / AI`
  - `Admin`
  - `Other / needs owner`
- Sub-hub path:
- Direct-open command(s):
- Semantic parent:
- Back/Home expectations:
- Persistent/restart-safe panel requirements:
- Admin/permission-gated node?
- Preset membership:
  - `safe-default/full`
  - `game-server`
  - `community-server`
  - `moderation-heavy`
  - `knowledge-ai`
  - `custom/owner`
  - `not in preset by default`
- Preset exclusion behavior: `disabled`, `hidden-only`, or `blocked-pending-owner`

### 6. Capability triage and exact scope
- Keep:
- Improve:
- Merge:
- Redesign:
- Drop:
- Defer:
- Add:
- Scope explicitly out of Stage 2 / future known-option:
- One-line reason for verdict:

### 7. Concrete outperform targets
| Target type | Target |
|---|---|
| Parity target | |
| Competitor benchmark | |
| Specific features to match | |
| Specific features to beat | |
| Free/privacy/audit edge | |
| UX/self-explanatory edge | |

Rules:
- Do not write only "beat Dyno" or "match Ticket Tool".
- List concrete behaviors/features.
- If no public comparator exists, mark `no comparator found` and define a source-confirmed parity
  or live-test target.

### 8. Required engines/specs/seams
| Engine/spec/seam | Tier (`T1 data` / `T2 composition` / `T3 handler`) | Exists in plan? | New or reused? | Owner decision needed? |
|---|---|---|---|---|

Must explicitly consider when relevant:
- CommandSpec / ParamSpec / EntityResolverRef
- Authority label
- WorkflowResult / result envelope
- Audited mutation seam
- ModerationActionSpec
- ManagedTaskSpec / timed task
- StoreSpec and import mapping
- PanelSpec / NavigationSpec
- CardTemplateSpec / media source
- Preset/template primitive
- Cooldown/rate-limit engine
- ProviderRef / egress policy

### 9. Data, import, and lifecycle
- Stores required:
- Old DB tables/columns likely involved:
- Import mapping: `imported`, `fresh-start`, `drop with reason`, or `unknown-blocked`
- Guild join bootstrap needs:
- Guild leave teardown needs:
- Member data erasure concerns:
- Persistence/restart/catch-up needs:
- Migration/cutover notes:

### 10. Verification oracle
- Oracle type: `parity golden`, `competitor benchmark + live co-test`, or `both`
- Existing parity goldens:
- New goldens required:
- Live co-test checklist:
  - works
  - logical
  - self-explanatory
  - beats old bot or named competitor
- `verified_live` per-command sign-off entries:
- Failure/edge cases:
- Source uncertainty tests:

### 11. Rubric pass — 10 probes
| Rubric class | Result | Evidence / disposition |
|---|---|---|
| 1. Dependency-order inversion | | |
| 2. Forgotten capability | | |
| 3. Thin / underspecified step | | |
| 4. Stale / unanchored state claim | | |
| 5. Fragmentation / reinvention | | |
| 6. Under-/wrong-generalization | | |
| 7. Missing cross-cutting standard | | |
| 8. Verification hole | | |
| 9. UX / lifecycle-contract gap | | |
| 10. Naming / visibility / collision risk | | |

A row is incomplete until all ten are answered or marked `N/A + why`.

### 12. Blockers and decisions
| Blocker type | Details | Owner question / needed artifact |
|---|---|---|
| Gate-0 grammar | | |
| Owner decision | | |
| Missing prior art | | |
| Source uncertainty | | |
| Prompt A/B issue | | |
| Dependency not settled | | |

### 13. Stage-3 consolidation notes
- Changes to BUILD-PLAN row:
- Changes to Gate-0 inputs:
- Changes to shared vocabulary/template:
- Dependencies to re-check:
- Owner ratification needed:
```

---

## 5. Non-negotiable review rules

1. **Stage 2 is owner-led and decision-capturing, not implementation.** Agents pressure-test and
   record decisions; they do not autonomously approve surface choices.
2. **Do not start Phase B.** Phase B begins only after Stage 2 and Stage 3 consolidation/owner
   ratification.
3. **Every BUILD-PLAN row gets a verdict.** Return is not automatic; `drop`, `defer`, and
   `re-place` are valid outcomes.
4. **Apply S-1 everywhere.** Recurring behavior is engine + declaration + seam; handlers are leaves
   and must not orchestrate flow or transactions.
5. **Apply S-2 everywhere.** Engine-class dependencies must precede consumers; peer dependencies may
   be dormant declared seams only when explicitly labeled.
6. **Shared-verb namespacing is mechanical.** Shared verbs become `/area verb`; unique verbs stay
   flat and are reserved by K1.
7. **Slash is the discoverable default; prefix stays supported.** Any exception must be explained
   against the slash cap policy and usability.
8. **No destructive no-arg defaults.** Safe/read/common commands may default; destructive,
   ambiguous, money, moderation, and external-egress actions require explicit arguments or confirm.
9. **Every action has one authority label.** Bot-owner override is global but visible in server audit
   logs.
10. **Every panel honors the navigation contract.** Back, Home, direct-open command, semantic parent,
    and persistent/restart-safe rendering are framework responsibilities.
11. **Preset membership is declared by the feature.** Presets decide per-guild visibility/enablement;
    Stage-2 triage decides whether the feature exists at all.
12. **Every subsystem declares an oracle.** Ported features need parity goldens; new features need
    competitor benchmark + live co-test.
13. **Run all ten rubric probes.** Silence on a rubric class is not a pass.
14. **Outperform targets must be concrete.** Comparator names are not enough; list behaviors to match
    and beat.
15. **Every uncertainty has exactly one owner.** If Stage 2 cannot decide it, the row must say which
    Gate-0/Phase-B plan owns it.

---

## 6. Open owner decisions before/during Stage 2

### Ask before Stage 2 if possible

- May Stage 2 start before Prompt B is merged, or is Prompt B required?
- What slash cap policy should Stage 2 use?
- What does preset exclusion mean: disabled or hidden-only?
- Is G-22 one staging primitive or multiple staging lanes?
- Does Stage 2 compute shared verbs from `command_surface_ledger.build_ledger()` as recommended?
- Is the normalized verdict vocabulary in this document approved?

### Can be asked during Stage 2, but must be captured per row

- Final command names and aliases.
- Prefix/slash/both/panel-only/event-only kind.
- Legacy prefix compatibility: retained, hidden alias, renamed, or retired.
- Hub bucket and sub-hub path.
- Preset membership.
- Concrete competitor features to match/beat.
- Merge/drop/defer/re-place decisions.
- Missing prior art or source uncertainty requiring follow-up.

### Route to Gate-0 / Phase B rather than deciding in Stage 2

- Compound workflow audit semantics.
- R-12 world-store dataclass vs convention.
- P-1 event-feed ratify vs hold.
- Detailed C-1 through C-7 engine contracts.
- Store/import mappings at field-level detail, unless the Stage-2 row needs a triage-level import
  decision.

---

## 7. Recommended parallel lane split

Parallel Stage 2 is safe only after the common template and shared inputs above are frozen.

### Lane 0 — coordination / namespace / shared inputs

Owns shared-verb set, slash cap budget, K1 reservation notes, owner-decision ledger, verdict
normalization, and cross-lane conflict resolution.

### Lane 1 — L1 operator/admin substrate

Rows: settings, diagnostic, help, admin, server_management, moderation, logging, automod,
image_moderation, security, cleanup, welcome, counters, channel, role, ticket, proof_channel,
ux_lab, visual card engine.

### Lane 2 — L2 identity/economy/community substrate

Rows: economy, inventory, treasury, xp, karma, community hub, community_spotlight, leaderboard,
profile surface.

### Lane 3 — L3 games/world loop

Rows: games hub, blackjack, rps_tournament, deathmatch, fishing, farm, creature, casino, counting +
chain, four_twenty, giveaways, starboard, explore hub + wild encounters, mining.

### Lane 4 — L4/L5 AI, knowledge, utility, dashboard, migration, ops

Rows: ai platform, btd6, project_moon, youtube/shared ingestion, utility, general, web dashboard/live
editor, boards family, bot-migration assistant, Railway/ops control-plane.

### Lane 5 — presentation/verification companion lane, if Prompt B lands with substantial issues

Owns Prompt-B-derived presentation/verification normalization: PanelSpec, NavSpec, CardTemplateSpec,
media source seams, preset semantics, and verification-oracle consistency across all rows.

---

## 8. Stop conditions for Stage-2 agents

A Stage-2 agent must stop and escalate if:

1. Prompt B is required but unavailable/unwaived.
2. The shared-verb classification for a command is unavailable.
3. A command-kind decision depends on unresolved slash cap policy.
4. The row's verdict would drop/defer/re-place a dependency used by another lane.
5. A missing cross-cutting standard appears that would affect multiple rows.
6. The row cannot declare a verification oracle.
7. The row only has a vague outperform target such as "beat Dyno" with no concrete behaviors.
8. Any of the ten rubric probes cannot be answered or marked `N/A + why`.
9. The discussion drifts into Phase-B plan writing or implementation approval.
10. Source evidence conflicts with planning docs and the conflict cannot be resolved immediately.

---

## 9. Bottom line

The planning corpus is strong enough to define a consistent Stage-2 contract, but Stage 2 should
start only after Prompt B is merged/available or explicitly waived. Once that happens, use the
subsystem template in §4 for every BUILD-PLAN row, keep Lane 0 as the normalization authority, and
stop on any unresolved shared vocabulary or source-confidence issue rather than letting 43 outputs
drift.
