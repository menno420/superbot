# 2026-07-11 — fold gen-3 coordinator lessons into the dispatch-kit permissions block

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed follow-up (routed report → next-session-better)

## What this does

The substrate-kit gen-3 coordinator returned a ~24h honest-lessons report (owner-relayed).
Verified the source-checkable claims (Q-0120): the born-red 3×-webhook noise (two
`legacy-alias-{test,smoke}` jobs in substrate-kit `ci.yml` that `exit 1` when kit-quality
isn't success) and the four gate loopholes (fixed in kit #228) both CONFIRMED against source;
the runtime incidents (trigger-MCP stalls, env leak into spawned CLIs, clone drift) are
coordinator-attested but their workarounds are sound + low-risk.

Folded the **portable** lessons into the dispatch kit's Part-A permissions block
(`docs/owner/dispatch-prompts-2026-07-11.md`) so the next dispatch is born knowing them:

- Items 11–14 (new "Multi-agent / long-run hygiene" section): **one trigger-MCP call per
  worker** (sequenced chains stall under parallel load) · **clear env for any spawned CLI**
  (`env -u` — leaked env decomposed a run into rogue subagents) · **hard-sync to origin at
  session start** (an 88-commit clone drift) · **born-red holds emit CI-failure webhooks —
  expected, not real**.
- Session-hygiene add: **preflight volatile facts** ("expect X, or later" + re-verify at HEAD).
- Owner companion add: coordinator-routine tuning (direct trigger access / 15-min cron vs
  one-shot re-arm chains ~40 spawns/day) · retire the kit legacy-alias jobs (also kills the
  born-red webhook noise) · name a canonical owner for `kit:`-line bumps.
- Pointer: the same walls belong in `fleet-manager/docs/capabilities.md` (master) — a
  fleet-manager-session item (that lane is live), left as a pointer to avoid a cross-repo
  collision.

Docs-only; `check_docs --strict` clean (the doc is already reachable via the current-state
pointer).

## 💡 Session idea (Q-0089)

The "born-red holds emit CI-failure webhooks" noise (item 14) cost 6+ sessions a diagnosis
round fleet-wide. Beyond retiring the kit legacy aliases, the durable cross-fleet fix is a
**webhook-side suppressor**: when a subscribed session receives a `check_run: failure` whose
failing step is the *designed* born-red session gate (detectable by the gate's own log line),
auto-classify it as HOLD-not-failure and don't surface it as actionable. That converts a
recurring "is this real?" tax into a one-time rule — the same enforce-don't-exhort move as
the required-check swap, but at the notification layer where the noise actually lands.

## ⟲ Previous-session review (Q-0102)

The earlier turn this session built the Part-A block by hand from the capability ledger — and
this report is the immediate proof of why the `gen_dispatch_block.py` generator idea (that
turn's session idea) matters: new verified walls arrived within hours and had to be
hand-merged. The generator would have made this a ledger append that flows to every prompt
automatically. No fix owed; it reinforces routing that idea into the fleet-manager
centralization build.

## Documentation audit (Q-0104)

Docs-only; no ledger/decision changes. Telemetry appended. Claim deleted at close. The
master-ledger counterpart is explicitly flagged as a fleet-manager item (pointer in the doc).

## 📤 Run report

- **Did:** verified + folded the gen-3 coordinator lessons into the dispatch-kit permissions
  block · **Outcome:** shipped
- **Run type:** `owner-directed` (routed report → improve next-session orientation)
- **⚑ Self-initiated:** none (owner-relayed report; folding it in is the routing step)
- **↪ Next:** the master-ledger copy (fleet-manager capabilities.md) is a live-lane item;
  owner-action items (coordinator trigger access, retire kit legacy aliases) surfaced to owner
