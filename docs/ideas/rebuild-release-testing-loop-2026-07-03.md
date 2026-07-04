# Idea — the in-server release → test → verify loop (announce · coverage · test-mode · approve)

> **Status:** `ideas` — capture (owner-originated). **Subsystem:** none (rebuild platform /
> verification tooling — touches diagnostic, help, command-surface, every cog's dispatch seam).
> **Provenance:** owner idea-drop, 2026-07-03, immediately after the Fable-5 final judgment
> (PR #1701). Closes judgment gaps #5 (change-communication), #7 (field-signal), #8 (co-test
> throughput) and is the missing *mechanism* for the already-decided Q-0234 oracle + Q-0222 CUT-1
> `verified_live` sign-off. Source wins over this doc (Q-0120).

## Why this matters — it closes known holes, it's not new scope

The Fable-5 judgment flagged, as gaps that survived the whole planning day: **no user-facing
change-communication mechanic** (§4 #5 — merge=deploy + D-5 drops + Q-0224 renames all change
user-visible behavior with no way to tell users), **no field-signal / feedback intake after
cutover** (§4 #7), and **the live co-test serializes 271 commands through one human with no
throughput mechanism** (§4 #8, stress oracle-gatev). The owner's idea is the concrete machinery for
all three — and the confirm/approve half is the *implementation* of the `verified_live` per-command
sign-off that Q-0234 and Q-0222 already decided but left as an abstract registry.

## The loop (four components, ship incrementally)

### A. In-server release announcer
On a **new release** (not every merge=deploy boot — see fork 1), the bot posts a digest to a
designated channel: **new / changed / improved commands and functions**, so members know what to
test. Generated from the **manifest** (every command is declared, with its version/changed-at) ×
the **changelog** (`docs/bot-changelog.md` today) — the same declared surface the whole rebuild is
built on, so the announcer is *generated*, not hand-written.

### B. Per-command "tested-since-change" coverage
The manifest declares each command's **changed-at version**; a small **usage store** records each
command's **last-invoked-at (+ by-whom / where)**. Derived signal: **"changed since vN but not
exercised since the change"** — live test-coverage from real usage, surfaced in the announcer ("3 of
today's 7 changed commands haven't been tried yet") and to the operator. This is a genuinely novel
oracle: coverage measured from *production usage*, complementing the parity goldens (which measure
coverage from a fixed corpus).

### C. Dedicated test/debug mode
A per-scope toggle (see fork 3). When on, every command execution emits a **full debug trace** to a
dedicated channel — resolved inputs, the authority decision, DB deltas, events emitted, timing —
and **actions self-explain** wherever possible. This is the observability half the runtime audit
already wants; in test mode it's surfaced live instead of buried in logs.

### D. Explain-then-approve (the `verified_live` sign-off, in Discord)
In test mode, an action is **explained and then confirmed via a button** before/after it runs — and
that confirmation **doubles as the `verified_live` sign-off** (Q-0234/Q-0222). This unifies two
things the plan already has: the **C-2 preview/confirm/apply** pipeline (extended from setup drafts
to any command under test) *and* the per-command live-test checklist. It turns the owner's
"command-by-command, does it beat the old bot" co-test from an external checklist into an in-Discord
button flow — directly relieving the one-human-bottleneck (judgment §4 #8).

## Open design forks (resolve when promoted)

1. **Trigger: release-triggered, not every boot.** merge=deploy reboots the worker many times a day
   (Q-0193); "announce every boot" would spam. Announce only when there is **something new since the
   last announced version**, dedup'd by a stored last-announced marker.
2. **"Approve" semantics — both, unified.** Reading it as (a) a *safety gate* (explain the action,
   press to let it commit — the C-2 preview/confirm extended to arbitrary test-mode commands) and
   (b) a *verification sign-off* (press = "this did the right thing" → feeds `verified_live`). The
   same button serves both: confirm-to-run in test mode, and the confirmation is recorded as the
   sign-off.
3. **Test-mode audience:** owner-only · per-guild admin opt-in · or open to designated community
   testers. The debug channel's **verbosity + PII policy** depends on this (a public tester channel
   must scrub member data; an owner-only channel need not).
4. **Coverage store scope:** per-command last-used is cheap; per-(command × guild) or per-user is
   richer but larger — bound it.

## Routing

- **New capability-corpus entries for Stage 2** (like D-2 media generation was added mid-review):
  the announcer, the coverage signal, and the test/verify mode become named capabilities the
  subsystem walk places and the Gate-0 grammar supports (a `changed_at`/version field on CommandSpec
  for A/B; the test-mode dispatch hook; the sign-off store for D).
- **Amends the verification/cutover story at Gate-0:** folds into the Q-0234 oracle (D is its live
  half) and the Q-0222 CUT-1 `verified_live` registry (D is its UI); the announcer is the
  user-comms half CUT-3 currently lacks (judgment §4 #9/#11).
- **A/C could also ship in the *current* bot now** (a release announcer + a debug channel are
  buildable against today's `command_manifest` + `docs/bot-changelog.md`) if the owner wants a
  near-term win before the rebuild lands — but D (sign-off) is best built once on the new manifest.

## Pointers

- Judgment gaps this closes: `final-judgment-fable5-2026-07-03.md` §4 (#5, #7, #8), §5 (the co-test
  bottleneck).
- Decisions it implements/enriches: Q-0234 (oracle) · Q-0222 (CUT-1 `verified_live`) · C-2 (draft
  preview/confirm/apply, Q-0228) · Q-0193 (merge=deploy, why trigger ≠ boot).
- Companion idea (the off-Discord surface for the announcer + coverage):
  `rebuild-websites-cutover-role-2026-07-03.md`.
