# SuperBot — Ideas Lab (brainstorm backlog)

> **Status:** `ideas` — planning artifact / **advisory** backlog — **except** §2 (Operating
> decisions) and §6 (Rejection ledger), which are **binding** for how this
> backlog is handled. The rest is a menu of candidate work, not a spec.
>
> **Date:** 2026-06-05
>
> **Provenance:** a read-only idea scan (ChatGPT "Idea" project) reconciled
> against current source by Claude during session S1 (after PR #513 / RC-2 +
> RC-5 + RC-15 merged). Duplicates were collapsed and the PR-1-adjacency trio
> was verified to ride existing read seams before promotion.
>
> **Companions:** `superbot-next-session-roadmap-2026-06-05.md` (PR sequence),
> `superbot-architecture-priority-map-2026-06-05.md` (priority/dep graph),
> `superbot-audit-consolidation-2026-06-05.md` (RC-n evidence),
> `superbot-source-of-truth-index-2026-06-05.md` (what to trust).
>
> **The one rule:** when a doc and a source file disagree, **the source file
> wins** (`.claude/CLAUDE.md`). These are *ideas* — re-verify against source
> before implementing any of them.

---

## 1. How to use this doc

Every entry carries a **gate** (the milestone or decision it waits on) and an
**architecture-fit** note. Tiers:

| Tier | Meaning |
|---|---|
| **COMMITTED** (§3) | Approved to build next session. Gate cleared *and* it rides an existing seam (see D1). |
| **SUGGESTION** (§4) | Real candidate, but gated — do not build before its gate clears. |
| **FUTURE** (§5) | Too broad for the current roadmap; needs its own planning project. |
| **REJECTED** (§6) | Binding "do-not-propose". Re-open only by changing the governing doc cited. |

**Promotion rule:** a SUGGESTION becomes COMMITTED only when (a) its gate is
cleared and (b) it satisfies D1 (rides an existing read/write seam). New scans
append here; they do not re-litigate §6.

---

## 2. Operating decisions (BINDING for this backlog)

These bind *how we treat the ideas below*. They are applications of existing
contracts, not new architecture — each cites its governing source.

- **D1 — Previews/explainers reuse existing read models; never a second system.**
  Operator-facing preview / explain / diagnostics ideas must be built on the
  existing read seams: `governance.snapshot.build_governance_snapshot` /
  `SubsystemEffectiveState` (the `/why` read model), `services.diagnostics_service`
  + the `!platform` group, the `*_audit` read paths, and `ReadinessSnapshot`.
  No parallel governance / panel / router / provenance / helper system.
  *Grounded in:* roadmap "out-of-scope warnings" (no second system),
  `docs/helper-policy.md`, `docs/ownership.md`.

- **D2 — Counting health surfaces the existing signal, not a new monitor.**
  The counting persistence-health idea (IL-3) must surface the
  `task_outcome_total{name=~"counting:save:.*",outcome="error"}` metric + ERROR
  log that RC-15 (PR #513) already emits, via `!platform` / a
  `diagnostics_service` snapshot. It must **not** introduce a new monitoring
  subsystem. *Grounded in:* RC-15, `core.runtime.tasks`, ADR-002.

- **D3 — The §6 rejection ledger is binding "do-not-propose".**
  Each rejected row cites the ADR/RC that governs it. Treat them as settled;
  re-open only by amending that governing doc — not by re-adding the idea here.

---

## 3. Committed next-session work (post-PR 1)

The PR-1-adjacency trio, **promoted from suggestion to committed**. All three are
read-only / observability-only, ride an existing seam (D1), and their gate
("after PR 1") is **cleared** — PR #513 merged. None expands a mutating surface.

| ID | Idea | Seam it rides | Sketch | Gate |
|---|---|---|---|---|
| **IL-1** | Thread/channel-aware **access explainer** ("Can I use this here?") — *collapses scan #1 + the §5 "command access simulator"; ship thin, grow into the simulator* | `build_governance_snapshot` / `SubsystemEffectiveState` with a thread context | New thin read-only command/panel: pick channel/thread → show visible/denied subsystems + resolved-from source. Validates RC-2. | ✅ cleared |
| **IL-2** | Cleanup policy **dry-run / preview** | RC-5 `_VALID_CLEANUP_SCOPE_TYPES` + cleanup scope resolution; render via the setup-wizard preflight path (don't add a 2nd preview renderer) | Show requested scope, accepted/rejected scope-type + reason, target, and whether the write would reach the DB — *before* mutating. Pairs with RC-5. | ✅ cleared |
| **IL-3** | Counting **persistence health** line | D2 — existing `task_outcome_total` + ERROR log | A `!platform` subcommand / `diagnostics_service` snapshot turning RC-15's now-observable failures into an operator-visible signal. | ✅ cleared |

> These are *committed scope*, not yet *implementation prompts* — per the
> session decision, prompts are written when the work is actually started.

---

## 4. Suggestions — tiered by gate

Value/Size/Risk use the scan's scale (S=small … L=large). "Fit" = how cleanly it
sits on the existing architecture per D1.

### 4.1 Safe now (no gate)

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| Help route **labels** ("opens panel" / "typed-only" / "admin-only" / "deprecated") | Help | Med | XS/S | Low | Discovery-only over the shared Help resolver |
| **Deprecated-command badge** in Help | Help / command ledger | Med | XS/S | Low | Uses command metadata; already a deferred item (ADR-003 §3) |
| Channel-visibility **cap wording** (copy for the first-25 cap) | Channel panel | Med | XS | Low | Copy-only, no backend |
| Game **refund-contract hint** (panel copy on restart/refund behavior) | Games panels | Med | XS | Low | Aligns with ADR-002; copy-only |
| **RPS matchup** button (expose `rpsmatchup` from the panel) | RPS tournament | Med | S | Low | Known command→panel gap |
| Chain **"clear limit"** button | Chain panel | Low/Med | XS/S | Low | Known command→panel gap |
| **Panel-class drift pinning** (docs test for views extending `discord.ui.View`) | docs tests | Low | XS | Low | Recommended by the UI-adoption audit |

### 4.2 After PR 1 (UX cluster, beyond the committed trio)

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| Operator **regression-checklist card** | Diagnostics | Med | XS | Low | Docs/UI card; extends `!platform` |
| Thread-specific **Help visibility preview** | Help + resolver | Med | S | Low | Extends IL-1's read model into Help |
| **Cleanup history** panel shortcut | Cleanup | Med | S/M | Low | Known command→panel gap |
| Counting **Start / End / Rules** buttons | Counting panel | High | S/M | Med | Known coverage gap |

### 4.3 After RC-3 decision / PR 2 (panels, fail-open) — **do not build before the posture call**

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| Missing-anchor / **stale-panel re-open** explanation copy | Persistent panels | High | S | Med | Policy-consistent UX (needs the decision first) |
| Panel **recovery button** | Panel manager / anchors | Med | S/M | Med | Reuses the existing anchor manager |
| **Fail-open posture map** | docs + diagnostics | Med | XS/S | Low | Documents the per-surface decision |
| **Duplicate-panel render detector** | Panel-manager metrics | Med | S/M | Med | Needs the RC-3 serialisation verification first |
| Platform-anchors **next-action hints** | Diagnostics | Med | XS/S | Low | Extends existing `!platform anchors` |

### 4.4 After PR 3 / PR 4 (tooling, migrations)

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| ~~**Architecture-warning summary** (count/categories from RC-1 report mode)~~ | Diagnostics | Med | S/M | Low | ✅ **shipped** in PR #515 — checker prints a `by check:` per-rule breakdown |
| **Migration health card** (latest migration, gaps/checksum) | Diagnostics | Med | S | Low | After PR 4 / RC-6 (RC-6 invariants already exist; this surfaces them) |

### 4.5 Capability-native authority — **RC-4 shipped (#518); these are now buildable**

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| Settings **capability preview** | Settings UI | Med | S | Low | After typed-capability authority |
| **"Why can't I edit this setting?"** explanation | Settings mutation / UI | Med | S | Low | Read-only over the authority result |
| Settings **provenance cards** (default/env/guild/override) | Settings resolution | Med | S/M | Low | Reuses `settings_resolution` |
| **Capability audit mini-report** | Diagnostics | Med | S | Low | Operator read-only tool |
| **Visibility pagination** for large guilds (replace first-25 channel cap) | Channel/visibility | Med | M | Med | Write side depends on RC-4/RC-5 |

### 4.6 After PR 7 / PR 8 (Direct-DB ledger, thin-cog) — **ledger first, UI second**

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| **Direct-DB ledger viewer** | Diagnostics | Med | S | Low | After the PR 7 docs ledger |
| **Cog-cleanup status** panel | Diagnostics | Med | S/M | Med | Read-only |
| **Command-classification gap** report | Help / command ledger | Med | S | Low | After the command-annotation sweep (deferred) |

### 4.7 After RC-10 / PR 9 (BTD6 provenance) — **no new extraction before this**

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| BTD6 **source-health dashboard** | BTD6 diagnostics | Med | S/M | Med | After the single provenance model |
| BTD6 **answerability checker** ("Can SuperBot verify X?", no AI generation) | BTD6 read model | Med | M | Med | Deterministic read-only |
| BTD6 **source/freshness badges** everywhere | BTD6 panels | Med | M | Med | After provenance model |
| BTD6 **data-inventory index** (docs/facts/backends/gaps map) | BTD6 docs | Med | S/M | Low | Docs-only version can precede RC-10 |
| **Provider-parity report** panel (file/postgres/cloud) | BTD6 diagnostics | Med | S/M | Low | After provider-parity execution |

### 4.8 After PR 10 / RC-11 (AI readiness) — **guard tests first; preserve the choke point**

| Idea | Feature | Val | Size | Risk | Fit |
|---|---|---|---|---|---|
| AI **decision explainer** (last reply/denial/skip in plain language) | AI audit surface | High | M | Med | Reuses the AI snapshot/audit read model (`ai-config-ownership.md`) |
| AI **guard status card** | AI diagnostics | Med | S | Med | After PR 10 guard tests |
| AI **support-report presets** (operator/debug/user) | AI diagnostics | Med | S/M | Low | After guard tests |
| AI **guard-regression dashboard** (test categories, not model internals) | AI diagnostics | Med | M | Med | After PR 10 |
| AI **tool-coverage explainer** (enabled read-only tools + why some are off) | AI diagnostics | Med | S | Low | After guard tests |

### 4.9 Medium-term, cross-cutting (own gate noted per row)

| Idea | Feature | Gate | Fit |
|---|---|---|---|
| Help **search by phrase** (commands/panels/aliases/hubs) | Help | optional after PR 1 | Good |
| **Feature-maturity labels** (alpha/beta/stable/deprecated) | Help | deferred (ADR-003) | Needs its own planning item |
| **Slash front doors** for main hubs (`/games`, `/economy`, `/settings` …) | Slash | after panel stability; **wrappers only** | Good only if they open existing panels |
| **User profile card** (rank/coins/inventory/last audit) | Economy/XP/inv | none | Good if read-only |
| **Coin history** panel + **"why did my coins change?"** shortcut | Economy audit | none | Good — read-only audit view |
| **Inventory filters/search** | Inventory | none | Good — UX only, no state-model change |
| **Game refund lookup** (restart/guild-remove refunds by user/game) | Economy audit | none | Good if read-only |
| **Mod case timeline** (target history from moderation reads) | Moderation | none | Good if read-only |
| **Logging route health view** (configured / channel exists / last test) | Logging | none | Good — extends current route UI |
| **Runtime error-publisher plan** | Logging | after publisher-ownership decision | Extend existing event/logging paths only |
| **Setup resume/recovery** panel | Setup | after setup-recovery verification | Good |
| **Final-review preflight diff** | Setup | deferred (ADR-003) | Good |
| **ReadinessSnapshot "what changed since boot"** card | Diagnostics | after current roadmap | Extend the snapshot, not a new dashboard |
| **Smoke-checklist runner status** | Diagnostics | future; off by default | Good if env-gated + read-only |

---

## 5. Future / large (needs dedicated planning)

| Idea | Val | Size | Risk | Gate | Verdict |
|---|---|---|---|---|---|
| Shared **media / video-reference** subsystem | Med | M/L | Med | after RC-12 | Good if kept separate from BTD6 |
| **Operator changelog** panel | Med | M | Med | deferred (ADR-003) | Good if backed by a release manifest |
| **Automated Discord smoke runner** | High | L | Med | future | Good if env-gated + read-only |
| **AI-assisted setup-advisor actions** | High | L | High | after AI guard tests + RC-4 | Dedicated planning project |
| **Server insights / analytics** panel | Med | L | Med | future metrics/event design | Good if privacy-bounded |
| **BTD6 strategy workspace** | High | L | High | after RC-10 + AI guard tests | Separate BTD6 planning |
| **Rule / automation builder** | High | L | High | after capability authority | Dedicated planning project |
| **Web dashboard** | Med | XL | High | future only | Risky; let Discord panels mature first |
| **Cross-process / sharding readiness** | Low now | XL | High | ADR-001 triggers only | Defer |

---

## 6. Rejection ledger (BINDING — do not propose)

Re-open only by amending the governing doc cited.

| Idea | Decision | Governed by |
|---|---|---|
| Resume BTD6 extraction now | Reject for now | RC-10 (provenance/ownership must land first) |
| Add AI write/action tools now | Reject for now | RC-11 / PR 10 (guard tests + audit guarantees first) |
| Build a second governance *simulator service* | Reject | D1 + `docs/ownership.md` (use existing resolver/pipeline reads) |
| Build a second panel/router framework | Reject | D1 + `docs/runtime_contracts.md` §3 (router/persistent-views/anchors are canonical) |
| Global fail-closed for **every** interaction | Reject | priority-map (posture is **per-surface**, not blanket) |
| Redis-backed sessions/cache | Reject | ADR-001 (no-redis-backed-state) |
| Universal game checkpointing / restart-safe game state | Reject | ADR-002 (restart cancels games; staked coins refunded) |
| Expand settings UI before RC-4 | **Cleared** | RC-4 shipped (#518): settings UI is now buildable on capability-native authority — see `docs/capability-authority.md` §5 |
| Big "all-cogs-at-once" thin-cog sweep | Reject | RC-8 (Direct-DB ledger first; staged per-feature) |
| One slash command per sub-action | Reject | command-integration-standard (slash = front doors to panels only) |
| Separate "danger" dashboard | Reject | ADR-003 (extend `ReadinessSnapshot` instead) |
| New generic/grab-bag helper module | Reject | `docs/helper-policy.md` (no parallel abstractions) |

---

## 7. Idea → session mapping (quick index)

| Session / phase | Ideas |
|---|---|
| **Committed (post-PR 1)** | IL-1 thread access explainer · IL-2 cleanup dry-run · IL-3 counting health |
| Safe now | Help labels · deprecated badge · channel cap copy · refund hint · RPS matchup · chain clear-limit · panel-drift pin |
| After PR 1 | regression-checklist card · thread Help preview · cleanup history panel · counting Start/End/Rules |
| After RC-3 / PR 2 | stale-panel/anchor copy · recovery button · fail-open posture map · dup-render detector · anchor next-action hints |
| After PR 3 / PR 4 | arch-warning summary · migration health card |
| After RC-4 / PR 6 | settings capability preview · "why can't I edit" · provenance cards · capability audit · visibility pagination |
| After PR 7 / PR 8 | Direct-DB ledger viewer · cog-cleanup status · command-classification gap report |
| After RC-10 / PR 9 | BTD6 source-health · answerability checker · freshness badges · data-inventory index · provider-parity report |
| After PR 10 / RC-11 | AI decision explainer · guard status card · support-report presets · guard-regression dashboard · tool-coverage explainer |
| Dedicated planning | media subsystem · changelog panel · smoke runner · AI setup-advisor actions · insights panel · BTD6 strategy workspace · automation builder · web dashboard |

---

## 8. Changelog

- **2026-06-05** — Created from the ChatGPT idea-scan, reconciled against source
  in session S1 (post-PR #513). Collapsed scan #1 + §5 simulator into IL-1;
  promoted IL-1/2/3 to COMMITTED after verifying they ride existing seams; set
  binding decisions D1–D3 and the §6 rejection ledger.
- **2026-06-05** — §4.4 "architecture-warning summary" shipped in PR #515
  (alongside RC-1). RC-7 (feature-cleanup-provider registry) also shipped; the
  "migration health card" foundation (the RC-6 invariants) is confirmed present.
  IL-1/2/3 remain committed-but-unbuilt.
