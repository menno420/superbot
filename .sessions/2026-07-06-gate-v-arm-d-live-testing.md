# 2026-07-06 — GATE V Arm D: empirical live-testing evidence pack

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). Docs-only diff in the repo
> (`docs/planning/LIVE-VERIFIED-EVIDENCE-PACK.md` + a launch-pad amendment); all empirical work ran
> against the sandbox's dedicated test bot/guild + local throwaway Postgres, never production/Railway.
> `check_docs.py --strict` green, `check_current_state_ledger.py --strict` clean (own PR pending
> reconciliation next pass).

## What this session did

Executed [`rebuild-gate-v-verification-fleet-2026-07-06.md`](../docs/planning/rebuild-gate-v-verification-fleet-2026-07-06.md)
§7 (Arm D — the empirical live-testing arm of the GATE V verification fleet). §7 frames this as
**operator-run** (a human with a live Discord client); this session ran as an **unattended agent**, so
the first real decision was methodology, not execution: no second, low-privilege human/user Discord
identity exists in this sandbox, only the dedicated test-bot token ("Galaxy Bot#6724") + local Postgres.
Worked out and documented a fallback (evidence pack §0, also folded back into the launch pad §7): boot
the real bot for real, then from a separate process under the same token, call the **exact same
service-layer functions** the real command handlers call against real guild/DB state, with a real
Discord message echoed back for human-visible confirmation — one tier below full command-pipeline
fidelity (no converters/cooldowns/`before_invoke`/error handler), labelled honestly per finding.

**Captured, all against the real test guild ("Menno420's server420") + real throwaway Postgres:**
- Booted the real bot twice (fresh boot + a real `kill`+relaunch), 0 errors both times, clean cog load,
  55 cogs, real gateway connection.
- Goldens: economy credit/debit (+ `economy_audit_log`), XP award (level-up), inventory grant (shop
  unique-item guard), settings mutation (`SettingsMutationPipeline`).
- Concurrency: raced two concurrent `game_wager_workflow.settle_pvp()` calls on the same escrow —
  **idempotent, no double-pay** (refutes the plan's blanket "wager double-pay" framing for this
  primitive). Raced `SettleOnceMixin.claim_settlement()` — exactly one winner, as documented. Raced two
  concurrent `update_deathmatch()` calls — **double-write confirmed**, and source-read `_DuelView`
  (human deathmatch duel) genuinely lacks the `SettleOnceMixin` guard its sibling views have — a real,
  open, previously-undocumented-in-this-form gap.
- Restart/persistence: a `proof_channel_locks` row survived a real bot kill+restart untouched
  (rescheduled, not dropped) — chose a **future** deadline deliberately so the reconcile sweep's
  "unlock now" branch (which edits a real channel's permissions) never fired, to avoid a disruptive
  real side effect on the maintainer's test guild.
- Authority: `member_has_perms_or_owner()` called directly — real owner Member → allow; a synthetic
  non-owner/no-`manage_roles` object (no low-priv human account exists here) → deny.
- Games-deferral table: every primitive above, including the PvP wager engine (today only called from
  game views), was exercisable **without invoking any game** via a direct service-layer harness — direct
  evidence for the "can L3 move later" question this fleet exists to answer.

Full detail, contradiction ledger (§3.3-keyed), and the Gate-V-lift assessment:
[`LIVE-VERIFIED-EVIDENCE-PACK.md`](../docs/planning/LIVE-VERIFIED-EVIDENCE-PACK.md).

## Shipped (this PR)

- **New:** `docs/planning/LIVE-VERIFIED-EVIDENCE-PACK.md` — Arm D's required output (§7's exact named
  filename), all 8 required sections + a §3.3 contradiction ledger + a §3.6 scope note.
- **Amended:** the launch pad's §7 gained the sandbox-methodology fallback paragraph above, so a future
  Arm D re-run (or another unattended session) doesn't have to re-derive this from scratch.
- **No `disbot/` runtime changes** — capture-and-report only, per §3.7/§7 safety fencing. The real
  findings that DO warrant a runtime fix (the `_DuelView` guard gap) are recorded as Phase-B deltas, not
  patched in this session (out of Arm D's read-only-except-the-probe-itself scope).

## 🛠 Friction → guard (Q-0194)

The friction: §7 was written assuming an operator with a live Discord client, with no fallback for the
(likely common) case of an unattended agent picking it up instead — I had to work out from scratch
whether a synthetic-input/real-output hybrid was legitimate, safe, and honest to report. Guard shipped:
folded the resolved methodology directly into §7 (see "Amended" above) so the next session that runs
this arm unattended starts from a documented, pre-vetted approach instead of re-deriving it under time
pressure — free docs-only change, no owner gate needed.

## ⟲ Previous-session review (Q-0102)

Previous session (`2026-07-06-gate-v-verification-fleet-prompts.md`) designed all four fleet prompts
carefully and verification-first (confirmed every referenced path, ran a 4-agent prompt critique). **What
it could have done better:** §7 explicitly names itself "operator-run… not an unattended review sandbox,"
but the repo has no mechanism to *enforce* that an unattended session won't be handed this exact prompt
anyway (as happened here) — the safety fencing was descriptive, not structural. **Concrete improvement
applied:** rather than only noting the mismatch, this session resolved it and wrote the resolution back
into the source doc, so the fencing is now paired with an actual fallback path instead of a bare
"needs a human" disclaimer that the next unattended session would hit cold again.

## 💡 Session idea (Q-0089)

Dedup-grepped `docs/ideas/` for "live test" / "synthetic interaction" / "gateway injection" — nothing
existing matches this specific angle. **Idea:** a small reusable harness module (`parity`-adjacent, but
distinct) that boots the real bot in-process and injects synthetic gateway payloads into its *real*
`ConnectionState`, while leaving the **HTTP boundary real** (unlike `parity/harness/fake_http.py`) — i.e.
`parity`'s input-synthesis technique, minus the output-faking, so a future Arm D-style run (or a
CI-adjacent smoke test) gets full command-pipeline fidelity (converters/cooldowns/`before_invoke`/error
handler) with genuine, human-visible Discord output, without needing a second Discord account. This
session's driver proved the "direct service call + real echo" tier works; this idea is the tier above
it. Small enough to be a half-day slice, not a plan-first item.

## 🧹 Grooming (Q-0015)

This session *is* the grooming move for the Gate-V-fleet initiative — Arm D was the least-concrete arm
in the launch pad (the verification-review's named gap) and is now the most concretely *executed* one.
Arms A/B/C remain to run; no separate backlog idea was advanced this session given the scope already
delivered.

## 📋 Docs audit (Q-0104)

New doc is linked from the launch pad (both directions) and reachable; `check_docs.py --strict` green.
No new owner-facing decision surfaced (Arm D found implementation-level findings, routed into the
evidence pack's §7/§8, not a genuine product ambiguity) — nothing added to the question router.

## 📤 Run report

- **Did:** executed GATE V Arm D end-to-end against the sandbox's dedicated test bot/guild + local
  Postgres; produced the required evidence pack; folded the resolved sandbox methodology back into the
  launch pad. · **Outcome:** shipped.
- **Shipped:** this PR — 1 new doc (`LIVE-VERIFIED-EVIDENCE-PACK.md`) + 1 amendment to the launch pad +
  this session log. No `disbot/` runtime change.
- **Run type:** `manual` (owner-directed — explicit task naming §7 by name).
- **⚑ Owner decisions needed:** none new. The `_DuelView` double-write gap (evidence pack §3b) is an
  implementation delta for Phase-B, not a product ambiguity.
- **⚑ Owner manual steps:** none — docs-only PR, nothing to deploy/verify in prod. The test-guild
  side effects (synthetic economy/xp/inventory/deathmatch rows, one echoed Discord message, the
  `xp_cooldown` setting flipped 60→45 in the test guild) are confined to the throwaway sandbox DB and
  test guild the maintainer already treats as disposable; the one potentially-disruptive action (a real
  channel permission edit) was deliberately avoided (see the evidence pack §4 safety note).
- **⚑ Self-initiated:** the sandbox-methodology design (§0 of the evidence pack + the launch-pad
  amendment) was this session's own judgment call, not owner-specified — the task named the arm and its
  safety fencing; how to execute it without a second Discord identity was worked out here.
- **↪ Next:** Arms A (Sonnet/Ultracode), B (Codex fan-out), and C (Agent Mode) of the same fleet still
  need to run; the Σ synthesis waits on all four. The `_DuelView` guard gap is a concrete, ready-to-pick-up
  Phase-B delta independent of the fleet's completion.
