# Stability Implementation Plan — Opus Refinement (next 2–3 PRs)

**Date:** 2026-06-05
**Author:** Claude Opus (dedicated planning session)
**Base verified:** `5e62578` (merge of #529; **== current remote `main`**)
**Refines:** `docs/archive/stability-preimplementation-plan-2026-06-05.md` (Codex first pass, PR #529)
> **Status:** `archive` — planning artifact — read-only by design. Intended next for the Revision-project

critique, then a final Opus revision, then execution. **No source was implemented in this pass.**

> **Post-merge update (2026-06-05):** this document was verified **pre-merge** at `5e62578`; it then
> merged via **#531** (and the CI docs-skip change via **#532**), so **current `main` is `7ffe3c7`** —
> the "`5e62578` == current main / only #530 open" lines below are **historical**. The GPT/Revision
> pass (R1–R5) was applied and **PR A has since been implemented** off a fresh branch from current
> `main`. All module paths in this doc are under the `disbot/` package root (e.g.
> `disbot/cogs/cleanup_cog.py`).

> **Why this exists.** Codex produced a first-draft stability sequence (A→H) but could not
> verify it against a live bot (its container lacked the credentials/Postgres), could not check
> open-PR state (`gh` absent), and treated several findings as gospel. This refinement verifies
> every near-term claim against source **and a clean live boot in this editing environment**,
> corrects what was inaccurate, and hardens **only the next 2–3 PRs** into an execution-ready
> shape. It deliberately does **not** re-plan the roadmap, restart BTD6 extraction, or expand AI.

---

## 1. Verification summary

### Branch / commit / PR state
| Item | Finding |
|---|---|
| Working branch | `claude/trusting-curie-zRheM`, clean tree, HEAD `5e62578`. |
| Remote `main` | `5e62578` (merge #529). **`main` == my HEAD — it has NOT moved beyond #529.** No "main moved" stop condition. |
| Open PRs | **Exactly one: #530** (`gpt/session-journal-cross-agent-workflow`), **docs-only** on `.session-journal.md`. **No overlap** with any PR A/B/C source file. (Resolves Codex F-note "open PR state unverified".) |
| PR #530 status | Open, not merged into this branch — so this container's journal does **not** yet carry the cross-agent-workflow note; that is expected, not drift. |

### Checks run (this session, `python3.10`, the CI interpreter)
| Check | Result |
|---|---|
| `scripts/check_architecture.py --mode strict` | **0 errors** / tracked warnings only (BaseView + known layer-boundary + raw-SQL). Matches the documented "0 errors / 87 warnings". |
| `scripts/check_quality.py --full` | **GREEN** — black/isort/ruff + mypy + **7461 passed, 3 skipped, 20 warnings** (~75 s). Clears the "full quality red after deps present" stop condition. |
| Quality-suite warnings | The 20 include `AutomationScheduler.run_forever` / RPS reminder / Blackjack auto-start un-awaited-coroutine warnings (Codex F25) — real but non-blocking. |

### Live bot availability — **AVAILABLE HERE** (Codex's biggest correction)
Codex reported the live runbook unusable (no token / DSN / Postgres). **This editing container has them**, and the maintainer confirmed the bot can be booted **only** in this environment:

- `DISCORD_BOT_TOKEN_PRODUCTION` present (len 72, 3 segments → real token); `DATABASE_URL` present (`postgresql://…localhost:5432/…`, len 54). Postgres 16 binaries + `postgres` user present.
- Stood up local Postgres per the journal runbook (`initdb` → `pg_ctl start` → create role/db `superbot`), then `python3.10 disbot/bot1.py`.
- **Clean boot:** migrations applied 001→… with **no errors**; all **34 cogs loaded**; `Identity-contract: clean (all four surfaces agree). STRICT=on`; `Logged in as Galaxy Bot#6724`; `Connected to 2 server(s)`; anchor recovery + live-update scheduler ready. **Zero ERROR/CRITICAL/Traceback.** Only benign WARNINGs: `DISCORD_WEBHOOK_URL not set`, `PyNaCl/davey not installed` (voice — cosmetic).
- **Implication:** discord.py **2.7.1** is the verified-good runtime (full suite green **and** the whole bot boots/loads under it). PR B's live cog audit is therefore **executable here** — but interactive panel-clicking still needs the maintainer in the private test server (I boot + watch logs + fix; the maintainer drives clicks).

### Mismatches with Codex's pass (what changed)
1. **Path artifact:** Codex cited `views/channels/delete_panel.py`; the package root is `disbot/`, so the real path is **`disbot/views/channels/delete_panel.py`**. The finding **is reproducible** (line 239). Not a stop condition.
2. **F2 live-test "unavailable" → CORRECTED:** available here; clean boot achieved.
3. **Open-PR/`main` state → RESOLVED:** one docs-only PR, no overlap; main unchanged.
4. **F12 severity → DOWNGRADED to docs drift** (see §2): the cleanup direct write is an *allowed* `accepted-direct-write` per `ownership.md:64`, so it is a stale-ledger wording bug, not an architecture violation.
5. **F15 remediation → REFRAMED** (see §2): amending the doc is the lower-friction fix; implementing guild presets is more invasive than Codex implied.
6. **One sub-agent mis-stated** that #528 fixed only RoleCog; in fact #528's merge also carries the DiagnosticCog fixes (commit `702cf48`), so the audit tracker's `🔴` DiagnosticCog **is** stale — F3 stands.

---

## 2. Decision review (Codex findings)

### Confirmed against source (near-term, in-scope)
- **F1 — discord.py unbounded.** `requirements.txt:1` = `discord.py>=2.3.0`. Installed/verified = **2.7.1**; full suite green + clean boot under it. → PR A.
- **F6 / F22 — channel delete-panel bypass + invariant gap.** `disbot/views/channels/delete_panel.py:239` `await channel.delete()` inside `_DeleteConfirmView.confirm_btn`, bypassing `ChannelLifecycleService`. `ownership.md:71` assigns `rename/move/delete/reorder` to that service. The invariant `tests/unit/invariants/test_no_direct_channel_mutations.py` scans **only the `ChannelCog` class body**, so the view path is invisible. **Concrete harm:** the panel emits **neither** the `audit.action_recorded` companion **nor** the `channel.lifecycle_changed` event (`ownership.md:168`, 326-330) — panel deletes are entirely absent from the audit trail. → PR A.
- **F10 / F11 — cleanup split + no dry-run.** Governance owns `cleanup_policies` via `GovernanceMutationPipeline.set_cleanup_policy` (`governance/writes.py`; `ownership.md:93,223`). Prohibited-word **writes are direct** from the cog at `disbot/cogs/cleanup_cog.py:354,373` (commands) and `:450,473` (modals), with process-local `_word_cache`/`_pattern_cache` (`:76-78`) and a static config whitelist `CLEANUP_WHITELIST_CHANNELS` (`:86`, rendered in `cogs/cleanup/panel.py`). History cleanup is a separate service (`services/history_cleanup.py`). No preview/dry-run/versioning exists. → PR C / queue PR8–PR9.
- **F18 / F20 — BTD6 gate.** `docs/decisions/006-btd6-data-provenance-ownership.md` = **Accepted**, extraction **PAUSED** until the follow-on provenance contract/schema PR (RC-10 gate). **No** `DataProvenance`/`SourceAttribution` symbol exists in source. → out of near-term scope.

### Confirmed but corrected / downgraded
- **F12 — direct-DB ledger stale → DOCS DRIFT (not a violation).** `docs/direct-db-exception-ledger.md:37` lists `cleanup_cog` as `accepted-read` ("db.fetchall + domain reads"), yet the cog writes prohibited words at four sites; the same doc even notes at `:33` that "prohibited-word writes live in `cleanup_cog`". `ownership.md:64` already classifies `cleanup → prohibited_words → direct via utils/db/moderation.py` as allowed (`accepted-direct-write`). **So the ledger text is wrong, but the write is sanctioned.** Fix is a ledger correction (+ optional drift test), not an INV fix. → PR C.
- **F3 — cog tracker stale/incomplete → CONFIRMED.** `docs/archive/cog-functionality-audit-2026-06-05.md`: **30 of 34 cogs `❓`**; DiagnosticCog `🔴` (master, line 67) / `❓` (detail) despite #528's `702cf48` fixing its 3 recorded issues; RoleCog inconsistent (`🔴→✅` master line 76 vs `🟡` detail line 124). Partly reconcilable from source now; the `❓` rows need the live walk. → PR B.
- **F15 — AI doc overstates guild presets → CONFIRMED, remediation reframed.** Doc (`docs/ai-config-ownership.md:128`, 219-223) claims preset application at **channel/category/guild** + a "guild button" + error `GuildScopeNotSupportedError`. Source: `services/ai_behavior_profile_service.py:151` `_SUPPORTED_SCOPES = frozenset({"channel","category"})`, raises **`InvalidBehaviorPresetScopeError`** (`:219`); `views/ai/behavior/chooser.py` exposes **Channel/Category only**; `test_ai_behavior_profile_service.py:251` asserts guild is refused. The doc-pin test (`tests/unit/docs/test_ai_config_ownership_doc.py`) does **not** assert scope, so **amending the doc needs no test change**. Implementing guild presets is more invasive than Codex implied (guild writes via `ai_policy_mutation.set_guild_policy` take **concrete values, no `UNCHANGED` sentinel** → "sentinel-safe" needs new mutation plumbing). The central mutation seam is otherwise healthy (F17). → **maintainer decision; keep out of next-3** (no-AI-expansion guardrail); near-term default = amend doc + fix the wrong error name.
- **F19 — provider parity piecemeal → CONFIRMED.** File/Cloud/Postgres providers (`services/btd6_data_provider.py`) are each tested in isolation; **no cross-backend parity test**. → BTD6 gate, out of near-term scope.

### Requires maintainer input
1. **discord.py pin band** — `>=2.7,<2.8` (matches the journal blocker + Codex; **recommended**) vs `>=2.7.1,<2.8` (the exact tested floor). *Default taken: `>=2.7,<2.8`.*
2. **PR sequence & whether C lands now** — confirm **A → B → C**; and whether PR C executes only after A+B's baseline is green, or its env-independent contract/ledger half runs in parallel.
3. **AI guild presets (F15)** — amend the binding doc (near-term, recommended) vs implement sentinel-safe guild presets (a later AI-config-correctness PR, *not* AI expansion).
4. **Cleanup ownership boundary (PR C)** — do prohibited-word/history writes get a canonical cleanup mutation owner, or stay `accepted-direct-write` with only the ledger corrected?
5. **PR B interactive audit** — maintainer drives the in-server clicks (I boot + watch + fix), or PR B is scoped to source-reconcilable statuses + log-only defect discovery if the maintainer is unavailable.

---

## 3. Recommended next PR sequence (refined; 2–3 PRs only)

Order unchanged from Codex (**A → B → C**), now with verified targets, the live-env correction,
and the cleanup work mapped onto the already-queued **PR8 (schema+versioning) / PR9 (builder+dry-run)**.

### PR A — Runtime/dependency + channel-lifecycle guardrails  *(first; execute now)*
**Objective.** Remove fresh-install runtime risk and close the audited-delete bypass, with a self-maintaining guard against the #528 collision class. Small, no migration, minimal blast radius.

**Scope.**
1. **Pin** `requirements.txt:1` → `discord.py>=2.7,<2.8` (verified 2.7.1; suite green + clean boot). discord.py lives **only** in `requirements.txt` (it is not a formatter/linter, so the "three pinned places" rule does not apply). Confirm no other dep constrains discord.py (none do).
2. **Route the delete confirmation through the service.** In `_DeleteConfirmView.confirm_btn`, replace the manual `for … channel.delete()` loop + four-bucket embed with the **established sibling pattern** from `move_panel._MoveSubView._apply` (`disbot/views/channels/move_panel.py:195-215`):
   ```python
   result = await ChannelLifecycleService().apply(
       interaction.guild,
       ChannelLifecycleRequest(operation="delete",
                               channel_ids=tuple(cid for cid, _ in self.channels)),
       interaction.user, confirmed=True, actor_type="admin",
   )
   ```
   Render `result.applied` / `result.failed` (each `StepResult` carries `.target_name` + `.error`, so per-channel reasons — not-found / missing-permission / Discord-error — are preserved). **Keep in the view:** the defer-before-deletes timing, the disabled-buttons result state, and the 2 s return-to-manager (`restore_parent_or_send_fresh`).
3. **Widen the invariant** (`tests/unit/invariants/test_no_direct_channel_mutations.py`) to also scan `disbot/views/channels/**` for direct **channel** `.delete()`/`.edit()`, **excluding message/interaction receivers** (`message`, `self.message`, `*.message`, `msg`) and **not** flagging `.set_permissions` (the deliberately-deferred overwrite path in `restrict_panel.py:179`). Verified: after the delete fix, `views/channels/**` has **no** direct channel `.delete`/`.edit` (channel views use `edit_message`/`safe_edit` helpers, not bare `.edit()`), so the widened scan is clean.
4. **Self-maintaining discord.py-collision guard.** Generalize `tests/unit/views/test_role_panels_discordpy_compat.py` (or add `tests/unit/views/test_discordpy_ui_collisions.py`) to scan **all** `views/**` for the two #528 patterns repo-wide: (a) a `discord.ui.View` subclass defining `_refresh`; (b) a `discord.ui.Item`/`Select`/`Button` subclass assigning `self.parent` / `self._parent`. (Maintainer preference: self-maintaining checks over hardcoded lists.)
5. **Update delete-panel tests** (`tests/unit/views/test_delete_panel_multi.py`) to the service-routing shape, using `tests/unit/views/test_channel_move_panel.py` as the template: patch `views.channels.delete_panel.ChannelLifecycleService`, assert `apply` awaited with `operation="delete", confirmed=True, channel_ids=(…)`, feed a synthetic `LifecycleResult`, and assert applied/failed rendering (incl. a partial-failure case).

**Out of scope.** New channel features; category lifecycle; clone/overwrite/create routing; arbitrary before/after reorder; any cleanup or AI/BTD6 work; broad interaction-helper rewrite.

**Exact files.** `requirements.txt`; `disbot/views/channels/delete_panel.py`; `tests/unit/invariants/test_no_direct_channel_mutations.py`; `tests/unit/views/test_delete_panel_multi.py`; `tests/unit/views/test_role_panels_discordpy_compat.py` (or new sibling). No doc change required (`ownership.md` already states the contract; source conforms to it).

**Migration impact.** None.

**Tests.** Updated delete-panel + invariant + collision tests; `check_quality.py --full`; `check_architecture.py --mode strict`.

**Live verification.** Boot here (Postgres bring-up + `python3.10 disbot/bot1.py`, boot-id-scoped log Monitor). `!channelmenu` → Delete → multi-select → Confirm: verify channels delete **and** that an `audit.action_recorded` companion + a `channel.lifecycle_changed` event now fire (they did not before). Re-run a clean boot to confirm the pin.

**Rollback risk.** Low–medium. The result embed changes from fixed buckets to applied/failed-with-reason; preserve defer timing, partial-failure detail, and the return-to-manager. **Thread nuance (verified, low-risk):** the picker uses `build_select_options(include_voice=True)` (text+voice, no threads) and the service resolves via `guild.get_channel`, so both resolve the same set — no thread-delete regression. Keep the pin and the routing as separate commits for independent revert.

**Stop conditions.** Service can't preserve batch partial-failure UX; pinning discord.py conflicts with another dep (verified: none); the widened invariant can't avoid message-edit false positives without over-broad exclusions; a new open PR touches these files.

---

### PR B — Live cog-audit completion + hard-failure fixes  *(second; executable here only)*
**Objective.** Convert the 30/34 `❓` cogs into a trustworthy ✅/🟡/🔴 baseline, fixing **only** confirmed hard failures and reconciling the stale tracker. Every later "stable enough" call depends on this.

**Scope.**
1. **Reconcile already-shipped statuses from source first** (no clicks): DiagnosticCog `🔴`→functional (3 issues fixed in #528 `702cf48`); unify RoleCog (`🔴→✅` vs `🟡`) to `🟡 unfinished` (crashes fixed; two UX warts remain — bulk "Clear missing", selector-ize Edit Role); add a "#528" banner to the audit doc.
2. **Live walk** each cog's commands + panels with the maintainer clicking in the private test server while I watch the boot-id-scoped log. Record per row: exact command, panel path, env-gate, log outcome, root cause.
3. **Fix only confirmed hard failures**, batched by cog + root cause; **one regression test per fix**; update the tracker row immediately.
4. **Classify env-gated** surfaces (AI off, scheduler off, YouTube/Paragon off, webhook off) as `⏸️ degraded`, never "broken".

**Out of scope.** Feature expansion; polish-only redesign; broad thin-cog migration; completing every future UX improvement; the cleanup redesign (PR C); AI/BTD6 expansion.

**Exact files.** `docs/archive/cog-functionality-audit-2026-06-05.md`; affected cogs/views + a regression test each (first likely targets from existing findings: **ProofChannelCog** — flagged "exception-swallow / no named tests"; plus whatever the walk surfaces); `.session-journal.md` (durable env lesson: **this container has the creds**; record the Postgres bring-up recipe).

**Migration impact.** Only if a specific fix requires it — additive only; none anticipated.

**Tests.** Per-fix slice + `check_quality.py --full` at the end; boot/log scan boot-id-scoped.

**Live verification.** This **is** the live-verification PR; boot here, maintainer drives clicks, watch logs.

**Rollback risk.** Per-cog; keep each fix independently revertible.

**Stop conditions.** A baseline failure invalidates assumptions; a fix would need a **new** architecture owner (route through an existing service instead); the maintainer is unavailable to drive interactive clicks (then PR B narrows to source-reconcilable statuses + log-only defect discovery).

---

### PR C — Cleanup ownership & policy contract  *(third; = queued PR8 — include now, build later)*
> Maps onto the existing dependency-ordered queue: **PR8 = cleanup policy schema + versioning (preserve RC-5 thread-inheritance)**, **PR9 = cleanup builder + dry-run + diagnostics** (Codex's PR D). Land PR C only after A+B are green, **or** run its env-independent contract/ledger half in parallel. Do **not** pull the builder UI forward.

**Objective.** Define the single cleanup ownership boundary + versioned policy model **before** any UI expansion cements the current split; correct the stale ledger.

**Scope.**
1. **Write the ownership/policy contract** reconciling the four "cleanup" meanings — command-feedback cleanup; prohibited-word automod (`cleanup_cog.py:354/373/450/473` + `_word_cache`/`_pattern_cache`); message-history cleanup (`services/history_cleanup.py`); static exemptions (`CLEANUP_WHITELIST_CHANNELS`). Keep `cleanup_policies` writes through `GovernanceMutationPipeline` (`ownership.md:93,223`). **Decide:** do prohibited-word/history writes gain a canonical cleanup mutation owner, or stay `accepted-direct-write`?
2. **Correct `docs/direct-db-exception-ledger.md:37`** — cleanup_cog is not reads-only; move it to `accepted-direct-write` (matching `ownership.md:64`). Add a drift check that inventories cog direct writes against the ledger.
3. **If schema/versioning is needed** (PR8 objective): an **additive** migration preserving current defaults + RC-5 thread inheritance; never edit historical migrations.

**Out of scope.** Full cleanup builder UI + dry-run (PR9); destructive redesign; setup-wizard expansion; Server Management Hub.

**Exact files.** `docs/ownership.md` (cleanup rows), `docs/direct-db-exception-ledger.md`; possibly a new cleanup mutation/orchestration module + `disbot/utils/db/` + an additive migration (**only if approved**); `disbot/cogs/cleanup_cog.py`, `disbot/cogs/cleanup/panel.py`, `disbot/services/cleanup_levels.py`, `disbot/services/history_cleanup.py`, `disbot/governance/writes.py`; tests under `tests/unit/{governance,services,db,invariants}`.

**Migration impact.** Possibly one **additive** migration (highest-risk part) → require exact legacy-default tests + bootstrap test.

**Tests.** Governance/cleanup/service/db/invariant; migration bootstrap; behavior-preservation cases; the ledger-drift check.

**Rollback risk.** High **if** defaults change → additive migration + legacy-default tests are mandatory.

**Stop conditions.** No agreed ownership split; migration would be destructive/non-additive; thread-scope semantics conflict with RC-5; the change would create a brand-new manager where extending governance/an existing service suffices.

---

## 4. Risk map
| Risk area | State after verification | Mitigation in the plan |
|---|---|---|
| **Runtime / dependency** | discord.py unbounded; 2.7.1 verified good (suite green **+ clean boot**). | PR A pins `>=2.7,<2.8` + a repo-wide self-maintaining collision invariant. |
| **Lifecycle boundary** | Delete panel bypasses the service → **unaudited destructive deletes** (no companion, no event). Invariant blind to views. | PR A routes through `ChannelLifecycleService` (template exists) + widens the invariant to `views/channels/**` (false-positive classes enumerated). |
| **Live audit** | 30/34 cogs `❓`; tracker stale. **Live env available here (only).** | PR B reconciles from source + a maintainer-driven live walk; fix hard failures only; regression test each. |
| **Cleanup ownership** | Split across governance policy / direct prohibited-word writes / history service / static whitelist; ledger text stale. | PR C writes the contract + corrects the ledger **before** the PR9 builder; additive-only migration. |
| **AI / BTD6 gates** | AI doc overstates guild presets (source/tests consistent + healthy seam); ADR-006 paused; no `DataProvenance`; provider parity piecemeal. | **Kept out of next-3.** F15 → maintainer decision (default: amend doc). BTD6 stays paused per ADR-006. |

---

## 5. Implementation prompt draft — PR A (copy-paste ready)

> **Implement PR A — runtime/dependency + channel-lifecycle guardrails — on branch `claude/trusting-curie-zRheM`.** Read first: `.claude/CLAUDE.md`, `.session-journal.md`, `docs/AGENT_ORIENTATION.md`, this plan, `docs/ownership.md` (rows 64/71/93/168/223 + §326-330), and the exact source/tests below. Base `5e62578` == current `main`; the only open PR (#530) is docs-only and does not overlap.
>
> **1) Pin discord.py.** `requirements.txt` line 1 → `discord.py>=2.7,<2.8`. Installed/verified is 2.7.1 (full suite green; the bot boots clean under it). It is the only place discord.py is pinned. Confirm no other dependency constrains it.
>
> **2) Route the delete confirmation through the service.** In `disbot/views/channels/delete_panel.py`, `_DeleteConfirmView.confirm_btn` currently loops over `self.channels` and calls `await channel.delete()` (line 239) — bypassing `ChannelLifecycleService`, emitting no `audit.action_recorded` companion and no `channel.lifecycle_changed` event. Replace the loop with a single `ChannelLifecycleService().apply(interaction.guild, ChannelLifecycleRequest(operation="delete", channel_ids=tuple(cid for cid,_ in self.channels)), interaction.user, confirmed=True, actor_type="admin")`, mirroring `move_panel._MoveSubView._apply` (lines 195-215). Render `result.applied`/`result.failed` (use `StepResult.target_name` + `.error` to preserve per-channel reasons). **Keep** the defer-before-deletes timing, the disabled-buttons result state, and the 2 s `restore_parent_or_send_fresh` return-to-manager. Note: the picker yields text+voice channels (no threads) and the service resolves via `guild.get_channel`, so there is no thread-delete regression — but confirm.
>
> **3) Widen the channel-mutation invariant.** Extend `tests/unit/invariants/test_no_direct_channel_mutations.py` to also scan `disbot/views/channels/**` for direct channel `.delete()`/`.edit()`. **Exclude** message/interaction receivers (`message`, `self.message`, `*.message`, `msg`) and **do not** flag `.set_permissions` (the deferred overwrite path in `restrict_panel.py:179`). After step 2, `views/channels/**` must be clean.
>
> **4) Add a self-maintaining discord.py-collision guard.** Generalize `tests/unit/views/test_role_panels_discordpy_compat.py` (or add `tests/unit/views/test_discordpy_ui_collisions.py`) to scan all `views/**` for: (a) a `discord.ui.View` subclass defining `_refresh`; (b) a `discord.ui.Item`/`Select`/`Button` subclass assigning `self.parent`/`self._parent`.
>
> **5) Update the delete-panel tests.** Rewrite `tests/unit/views/test_delete_panel_multi.py`'s confirm cases to the service-routing pattern, using `tests/unit/views/test_channel_move_panel.py` as the template (patch `views.channels.delete_panel.ChannelLifecycleService`; assert `apply` awaited with `operation="delete", confirmed=True, channel_ids=(…)`; feed a synthetic `LifecycleResult`; assert applied/failed rendering incl. a partial-failure case).
>
> **Verify:** `python3.10 scripts/check_architecture.py --mode strict` (0 errors) and `python3.10 scripts/check_quality.py --full` (green) — both via `python3.10 -m`, never bare exes. Then boot the test bot here (stand up local Postgres per `.session-journal.md`, `python3.10 disbot/bot1.py`, Monitor the boot-id log for `ERROR|CRITICAL|Traceback`) and exercise `!channelmenu` → Delete → Confirm, confirming the deletes plus the new audit companion + `channel.lifecycle_changed` event. Commit the pin and the routing as separate commits. **Stop and report** if: the service can't preserve batch partial-failure UX; the pin conflicts with another dep; the widened invariant can't avoid message-edit false positives; or an overlapping PR appears. **Do not** pull in cleanup, AI, BTD6, or new channel features.

---

## Appendix — key source coordinates (verified this session)
- Bypass: `disbot/views/channels/delete_panel.py:218-259` (`confirm_btn`, `await channel.delete()` @ 239).
- Routing template: `disbot/views/channels/move_panel.py:195-215` (`_MoveSubView._apply`).
- Service: `disbot/services/channel_lifecycle_service.py` (`apply`, `confirmed=True` gate @ 145-153; per-channel `StepResult`; audit + event @ 179-197). Owns `rename/move/delete/reorder`.
- Invariant (to widen): `tests/unit/invariants/test_no_direct_channel_mutations.py` (ChannelCog-only @ 24/30-34; `_FORBIDDEN={"delete","edit"}` @ 27).
- Channel views direct mutations (grep): only `delete_panel.py:239` (`.delete`, the bypass) and `restrict_panel.py:179` (`.set_permissions`, deferred — do not flag).
- Picker: `_build_channel_options` → `core.resources.channel_service.build_select_options(guild, include_voice=True, limit=25)` (no threads).
- discord.py compat regression: `tests/unit/views/test_role_panels_discordpy_compat.py`.
- Cleanup: `disbot/cogs/cleanup_cog.py:76-78` (caches), `:86` (whitelist), `:354/373/450/473` (prohibited-word writes); `disbot/cogs/cleanup/panel.py`; `disbot/services/history_cleanup.py`; `disbot/governance/writes.py` (`set_cleanup_policy`). Ledger drift: `docs/direct-db-exception-ledger.md:37` vs `ownership.md:64`.
- AI presets: `services/ai_behavior_profile_service.py:151,219`; `views/ai/behavior/chooser.py` (Channel/Category only); `docs/ai-config-ownership.md:128,219-223`; refusal test `tests/unit/services/test_ai_behavior_profile_service.py:251`.
- BTD6 gate: `docs/decisions/006-btd6-data-provenance-ownership.md` (Accepted; paused, RC-10); providers `services/btd6_data_provider.py`; composer `services/btd6_view_model_service.py`.
