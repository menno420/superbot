# Session — 2026-07-12 — fleet re-arm pack (autonomy doctrine + per-seat dispatch for tonight)

> **Status:** `complete`
> **Branch:** `claude/project-autonomy-workflow-bo1cjn` · **PR:** #2048
> **Venue:** owner-live chat (remote container). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** owner-directed. The owner sent every Project seat its session-ender prompt and asked
> for the fleet to be re-armed for the next run (tonight) with the **owner-presence-gating stall
> class designed out** — seats hallucinating "I need the owner to review/continue", stalling on
> open PRs, idling on drained queues; only substrate-kit ships consistently unattended. He also
> asked for his interlock vision to be expanded into an improved, better-structured version.

## What shipped (all docs; no `disbot/` runtime)

1. **[`docs/owner/fleet-rearm-2026-07-12.md`](../docs/owner/fleet-rearm-2026-07-12.md)** — the pack:
   §1 the owner's vision expanded (the fleet as one production economy: organs, per-seat "finished
   unit" definitions, 7 interlock contracts, the run KPI, the **round-trip proof**); §2 the stall
   taxonomy S1–S8 (each observed in the 07-11/07-12 runs) → one enforcing fix per class; §3 the
   **AUTONOMY RIDER v1 (Q-0271)** — 12 rules that kill presence-gating (owner-absent=normal,
   silence=consent, open-PR-never-stops-you, probe-before-wall, decide-and-flag, the OWNER-ONLY
   park list, queue-and-continue, never-idle ladder, SIM-REQUEST valve, wake hygiene, end-of-turn
   invariant, volatile-facts-expire, CI floor unchanged); §4 **8 complete paste-and-go re-arm
   prompts** (rider embedded verbatim per the one-paste directive + per-seat mission/targets/
   generative rung/boot, with seat-specific failsafe fixes for the seats that went dark);
   §5 firing order + the **3-click owner list** (superbot-next merge queue · fm #121/#122 ·
   kit #220/#238); §6 the morning read (roster lines, round-trip flag, dropped-tick report) and
   how the run's lessons feed the 07-13 v3.4 reboot.
2. **Router Q-0271** — the owner's in-session directive recorded verbatim: fleet-wide never-wait
   generalization of Q-0241; OWNER-ONLY list as the sole park class; queue-and-continue;
   SIM-REQUEST routing; prod-bot Q-0213 brake + CI floor unchanged.
3. **Pointers:** `docs/current-state.md` top block (▶ TONIGHT first) + the 07-13 brief §1.3 (the
   rider IS its "bake the new discipline" item, ready to lift verbatim into the v3.4 bodies).
4. **Idea capture + index:** [`prompt-wait-language-lint-2026-07-12.md`](../docs/ideas/prompt-wait-language-lint-2026-07-12.md).
5. **Groom pass (Q-0015):** routing note on `scheduler-independent-trigger-watchdog-2026-07-12.md`
   (its in-band half shipped as ORDER 020; only the Actions-substrate half remains novel).

## Key design decisions (decide-and-flag, Q-0240)

- **Bridge, not fork:** tonight's re-arm rides startup prompts over the currently-pasted
  instructions; the 07-13 website-served v3.4 reboot stays the durable path — the rider text is
  written to be lifted verbatim there (fm #121/#122 lane, manager-applied).
- **Rider embedded 8×** rather than "prepend Part A"-style assembly — the owner's 2026-07-11
  one-paste directive explicitly rejects bolt-on riders; drift risk accepted because the doc is a
  dated one-shot superseded by v3.4.
- **The round-trip proof** as the run's system-level success criterion (one idea → verdict →
  routed → built → merged → surfaced, hands-free) — makes "the projects actually work together"
  observable in one flag on the morning roster.
- **Owner-queue as interface, not wait state** — the S7 fix; venture's quantity thesis
  operationalized as "publish-READY + click queued + next product started same turn".
- Per-seat failsafe callouts baked into rider item 9 for the three seats the night review showed
  unprotected (SuperBot 2.0 no failsafe · kit daily-only · websites parked, Game Lab no triggers).

## Session enders

- **💡 Session idea (Q-0089):** the **prompt wait-language lint** (file above) — a fleet-manager
  registry CI check failing on wait-language outside OWNER-ONLY blocks; the at-source enforcing
  complement to the runtime rider. Dedup-grepped (`prompt lint` / `wait-language` — no hits).
- **⟲ Previous-session review (Q-0102):** the owner-queue-execution session (#2043) was the
  strongest rescue-venue session yet (queue executed, root causes fixed, ORDER 019/020 delivered)
  and its 07-13 brief is a genuinely good plan-of-record. The gap tonight exposed: the brief
  framed prompt delivery entirely as the *next sitting's* website-served reboot, leaving **no
  bridge for a run happening before that sitting** — the owner needed a same-day re-arm and had
  no pack. **Workflow improvement:** every next-session brief should carry a minimal "if the
  fleet must run before this sitting" fallback line; this pack now IS that fallback and §0 names
  the bridge→destination relationship explicitly, so the pattern is established for future briefs.
- **📄 Doc audit (Q-0104):** `check_docs.py --strict` ✓ (5 supersede warnings = the known honest
  cross-repo class, carried); `check_current_state_ledger.py --strict` ✓ (only benign
  newest-merge lag past marker #2040); Q-0271 recorded in the router; the pack reachable from
  current-state + the brief; idea indexed. Nothing captured only in chat.
- **⚑ Self-initiated (Q-0172):** the Q-0271 generalization itself was **owner-directed
  in-session** (his verbatim words in the router entry). Self-initiated within it: the rider's
  12-rule composition, the production-economy framing + interlock contracts + round-trip metric,
  the per-seat targets and generative rungs, the 3-click list selection, the groom-pass routing
  note.
- **🛠 Friction → guard (Q-0194):** the friction class this session addresses (prompt bodies
  teaching seats to wait) got its enforcing-guard **proposal** as the session idea (fleet-manager
  lane owns it — cross-repo, so proposed + routed rather than built here). In-repo friction hit:
  two existing guards fired exactly as designed — `check_docs --strict` caught an invalid idea
  badge (`captured` → `ideas`) and the Q-0194 **telemetry-append session gate** (#1894) held the
  merge until the `model-usage.jsonl` row landed. Both fixed same-session; no new guard needed —
  this is the enforce-don't-exhort loop catching its own author, working as intended.
- **Context delta:** orientation route worked as designed (CLAUDE.md → collaboration-model →
  current-state → journal → owner docs); the 07-13 brief + night review + 8-seat structure +
  founding-prompt kit + dispatch kit carried ~90% of the needed context. Discovered by hand: the
  router's newest entries use `###` headings (a bare `## Q-` grep undercounts — matters for
  next-free-Q lookups); fleet-manager's live registry (fm #121/#122 bodies) is out of this
  session's repo scope, so the pack was written to compose with any pasted body version rather
  than quoting v3.4 verbatim — the right shape anyway.
