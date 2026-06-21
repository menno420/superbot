# 2026-06-21 — Reaction roles: listener self-heal for dead bindings

> **Status:** `complete` — owner-accepted continuation of #1248 (offered at its close; "continue").
> Q-0191 → merge on green. PR #1250.

> **Run type:** `manual`

## Arc

#1248 added a manual 🧹 Clean up button for bindings whose role was deleted. This makes that cleanup
**automatic**: when a member reacts (or un-reacts) on a binding whose role no longer resolves, the
binding is removed on the spot — dead config self-heals without anyone opening the panel.

- `services/reaction_role_service.py`:
  - `_self_heal_dead_binding(guild, message_id, emoji, role_id)` — removes a dead-role binding, audited
    as a **`system`** action; called early in `handle_reaction_add` / `handle_reaction_remove` (before
    the mode logic, so a dead binding never reaches `_apply`).
  - threaded an `actor_type` param through `unbind_emoji` / `_emit` (default `"admin"`; self-heal passes
    `"system"`) so automatic cleanup is distinguishable from an operator removal in the audit stream.

## Findings / decisions

- **Decision made alone — safe to auto-delete here.** Auto-removing config is normally risky, but a
  binding to a *deleted role* can never assign anything, and discord.py **fully caches guild roles**
  (unlike members), so `resolve_role` returning `None` means genuinely deleted, not a transient cache
  miss. So the self-heal won't wrongly drop a live binding. The manual 🧹 button (#1248) remains for
  bindings on messages that never get reacted on.
- **Decision made alone — audit as `system`, not `admin`.** An automatic cleanup has no human actor;
  threading `actor_type` keeps the audit honest (`actor_id=None`, `actor_type="system"`) and required
  only a small, backward-compatible param on `unbind_emoji`/`_emit`.
- **Process note:** the early born-red PR (Q-0189) slipped this run — an owner message (the deploy
  clarification) interrupted right as the build started, so the card/PR went up after the code was
  written. No partial-merge risk (everything pushed together, born-red still held the merge).

## Context delta

- **Needed but not pointed to:** the fact that **discord.py caches roles fully** (so `resolve_role`
  None ⇒ deleted) is the safety linchpin for auto-deleting dead bindings — it's not written down
  anywhere; I relied on library knowledge. Worth a one-line note wherever role-resolution is documented.
- **Discovered by hand:** the existing `handle_reaction` tests' fake `_Guild` had no `get_role`, so the
  new `resolve_role` call broke them — the fake had to gain a (configurable) `get_role`. A test fake
  that omits a method the production path now calls is a quiet trap.
- **Decisions made alone:** auto-delete-is-safe-here; audit-as-system (see Findings).
- **Weak point / unverified:** not live-walked — the self-heal only fires on a real reaction to a
  dead binding; unit-tested with mocks (resolve→None path), but the live gateway round-trip is unverified.
- **One docs/tooling change that would help:** still the modal-first-response rule for
  `discord-views.md` (carried; owner-governed, needs a router Q-block) — and a note that discord.py
  roles are fully cached.

## 📤 Run report

- **Did:** automatic dead-binding self-heal on the reaction listener path · **Outcome:** shipped
  (PR #1250, auto-merge on green)
- **Shipped:** #1250 — reaction-roles listener self-heal
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none — **merged = deployed** (Railway auto-deploys `worker` on merge; this
  has always been true — the old "merge ≠ deploy" CLAUDE.md line was wrong and was removed in #1247).
- **⚑ Self-initiated:** continuation I offered at #1248 close; owner greenlit via "continue".
- **↪ Next:** reaction-roles is complete *and* self-healing (manual + automatic). No further
  reaction-roles work queued; the open cross-cutting item is the modal-first-response docs rule.

## 💡 Session idea

**Persist the "merged = deployed" fact where sessions actually read it at the moment they'd misstate
it.** Q-0193 fixed CLAUDE.md, but the misinformation persisted for *months* because each session
re-derived "you should deploy" at PR-close time. A tiny Stop-hook / `/session-close` line — "never
tell the maintainer to deploy/restart; merge auto-deploys (Q-0193)" — would catch the misstatement at
the exact point it's made, not just in a doc someone has to recall. (Dedup-checked — Q-0193 fixed the
doc; this is about the *reminder surface*.)

## ⟲ Previous-session review

The #1248 session correctly chose the *actionable* cleanup over a read-only audit (good call, owner
confirmed). What this session exposed about the chain: I repeatedly told the owner "merge ≠ deploy,
restart is yours" — wrong, and the owner had to correct me. The root (a wrong CLAUDE.md line) was
fixed in #1247, but my messaging lagged the fix. **System improvement (this run's idea):** put the
"merged = deployed" reminder on the session-close surface, not only in a doc — recurring
misinformation needs a reminder at the point of utterance, which is exactly the kind of "improve the
workflow so the next agent gets it right" the project values.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1250, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design) |
| Repo-rule trips | 1 (early-PR mandate slipped due to an owner-message interrupt — noted) |
| New ideas contributed | 1 (merged=deployed reminder on the close surface) |
| Ideas groomed | 1 (built the #1248 listener-self-heal idea) |
