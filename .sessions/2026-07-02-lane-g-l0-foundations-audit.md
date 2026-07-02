# 2026-07-02 — Lane G: L0 Foundations & Runtime Skeleton audit

> **Status:** `complete`
> **Branch:** `claude/lane-g-l0-audit-1736ye` · **PR:** #1666
> **Session type:** new-bot capability audit — Lane G (L0 foundations), docs-only, read-only on runtime

## What happened

Produced the **Lane G L0 foundation audit** —
`docs/analysis/rebuild-discovery/new-bot-capability-audit/lanes/lane-G-foundations.md` — the substrate
audit under all 43 subsystems and the first layer the new bot builds. Verified the audit substrate
(#1661: BRIEF/PARTITION/ground-truth/lane file all present), read every load-bearing L0 file first-hand,
and wrote the full required structure: L0 exec summary · source-cited foundation map · preserve/improve/
replace/drop verdicts · dynamic-loader recommendation · helper/util + config + namespace recommendations
· manifest-host requirements · dependency-ordered K0–K10 L0 build sequence · per-component done-definitions
· outperform targets · risks/stop-conditions · 5 open owner decisions + capstone carry-forward.

**Headline findings.** The current L0 is *strong in primitives, weak in composition root*. Six primitives
are production-grade and should be **preserved field-for-field** (lifecycle FSM `lifecycle.py`, task
supervisor `tasks.py`, publish-accepted EventBus `events.py`, startup-outcome recorder, health probes
`healthserver.py`, asyncpg DB seam `utils/db/`) — discipline is real (the only bare `asyncio.create_task`
in `disbot/` production is `bot1.py:1005`). Against that, `bot1.py` is a **1463-line composition root** to
extract, and two structural gaps the new bot's directive names are real: **no dynamic cog discovery** (a
hardcoded 60-cog `config.INITIAL_EXTENSIONS`) and **no central pre-boot namespace reservation** (the exact
gap that crash-looped prod twice — Q-0211 `give`, BUG-0030 `dock`/`sail`). Verdict for the capstone's L0
layer: **GO** — buildable as designed, K0–K10, with the six grammar amendments already folded in.

**Method.** Comprehensive first-hand read (bot1/config/events/tasks/lifecycle/startup_outcome/healthserver/
subsystem_registry + design-spec §1/§3/§6/§9 + linchpin validation + grammar spike + helper-policy +
INV-A…INV-N). Then a background **Workflow** (23 agents, 0 errors, ~1.46M tokens): 10 area-maps + 3 external
benchmark researchers (context7/web, properly URL-cited) + 10 adversarial citation-verify batches. Verify
result: **79/80 citations CONFIRMED, 1 FALSE** (a sub-agent over-claim about `entry_points`, not a doc
citation) → drove the §2.3 wording correction. Benchmark URLs folded into §5 (discord.py `setup_hook`/
`reload_extension`/no-dep-system, Red `required_cogs`-declared-but-unenforced, stevedore per-plugin
isolation, 12.1-factor/pydantic-settings/k8s three-probe/born-red-deploy).

## ⚑ Self-initiated

All within the owner-directed Lane G mandate (the audit was the task). Self-initiated *within* it: (1) ran
the verification fan-out as an explicit Q-0120 adversarial-verify pass rather than trusting first-hand reads
alone; (2) surfaced two L0 findings the prompt didn't name — the **failed-cog → silent-INTERNAL-hide**
behavior (`bot1.py:722-736`) as a "hides broken production state" risk (R-A / owner decision §11.2), and the
**INV-K↔INV-T naming reconciliation** (current INV-K = task-spawn rule; spec reassigns it) as an owner
decision (§11.4). Both flagged for the capstone/owner, not applied.

## 💡 Session idea

**A generated `check_foundation_boot_order.py` L0 guard for the new repo.** The audit's central L0 correctness
property is the *boot order* — "validate config → validate namespace (before any network I/O) → DB+migrations
→ … → gateway connect." That ordering is exactly the class that, when violated, produces the crash-loops this
whole rebuild exists to kill, yet nothing *enforces* it (today it's prose in `bot1.main`). Idea: an
AST/import-time checker that asserts the `app/` composition root performs namespace + config validation
strictly before the first network call, failing CI if a future edit moves a `bot.start()`/gateway call ahead
of a validation gate. It's the "enforce, don't exhort" (Q-0132) form of the fail-before-connect design. Dedup:
distinct from the existing `check_namespace`/`check_session_gate`/boot-smoke-test guards — those check *what*
is declared, not the *ordering* of the boot sequence. Grounded in §8's lean boot order.

## ⟲ Previous-session review

Previous session (#1662, "harden the capability-audit BRIEF with launch preconditions") did the right thing:
it added the substrate-verification precondition + the precise docs-only write boundary + the capstone
carry-forward fields *before* firing the fleet — which is exactly what made this Lane G session frictionless
(I could verify the substrate and know my exact write boundary in the first minutes). Good pre-flight
discipline. **What it could improve / system improvement:** the lane files A–D shipped with pre-extracted
inventories but the *foundation* lane (G) shipped as a bare scaffold, so Lane G had no ground-truth
pre-extraction to start from (the other lanes' `command-surface.json` doesn't cover bootstrap/loader/kernel).
A cheap future improvement: add a `ground-truth/foundation-inventory.json` (a mechanical dump of `bot1.py`
concerns + `core/runtime/*` module list + `INITIAL_EXTENSIONS` + the INV table) so a foundation lane starts
from extracted facts like the subsystem lanes do — the same "extract-mechanically-then-judge" shape the
substrate session (#1661) applied to the 43 subsystems, extended to L0.

## Grooming (Q-0015)

Deferred by design: **Lane E is concurrently auditing `docs/ideas/` + `docs/planning/`** in this same fleet,
so grooming an idea from here would collide with an active parallel lane (the exact duplicate-work the claim
system prevents). The one new idea above (Q-0089) is captured in this log; a substantial version can be filed
by Lane E or a later session without a collision.

## 📊 Telemetry

- PR #1666 · Lane G L0 foundation audit (docs-only) · `check_docs --strict` green · ledger unaffected.
- Verification fan-out: 23 agents, 0 errors, ~1.46M subagent tokens; 79/80 citations CONFIRMED.
- Document: ~11 required sections + capstone carry-forward + verification notes; every `disbot/` claim cited.
- Zero runtime code touched (no `disbot/`, tests, migrations, configs, generated files).

## Doc audit (Q-0104)

`check_docs --strict` green (badges + reachability; the two dead relative links to the planning docs were
caught + fixed). `check_current_state_ledger --strict` in sync (docs-only change, ledger unaffected). New
owner decisions surfaced are recorded *in the lane doc's §11* (the audit's proper home) for the capstone, not
duplicated into the router (this is a lane finding, not an owner ruling). Claim file released at close.
