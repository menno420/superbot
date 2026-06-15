# Session — Hermes model swap RESOLVED (gpt-5.4-mini live; it was propagation lag)

> **Status:** `complete`

## What happened

Final resolution of the long Hermes thread. The owner confirmed **gpt-5.4-mini now answers reliably**
on his own OpenAI key (custom provider) — clean in both Telegram and the OpenAI Playground, no errors.
The earlier intermittent "no access" denials **were OpenAI allowlist-propagation lag after all** — a
*slow, uneven* one: after the alias `gpt-5.4-mini` was added to the project allowlist it flapped (some
calls allowed, some denied) for >15 min before fully converging. (My earlier "it's been 15 min, so not
propagation" call was wrong — recorded as the lesson below.)

## What shipped (this PR, docs-only)
- `hermes-control-plane.md` § Model/provider: ticked the ⬜ open item → **✅ CONFIRMED WORKING**;
  recorded the slow-uneven-propagation lesson; kept the exact dated id (`gpt-5.4-mini-2026-03-17`) as
  the "if it ever flaps again" fallback.
- Playbook trap #6: added the "alias access propagates unevenly, can flap >15 min — wait it out or use
  the exact dated id" caveat.
- Cleared the `active-work` claim (PRs #913–#919 merged).

## The full session arc (for the record)
PRs **#913–#919**, all merged & live: compaction-root-cause fix + SOUL `git pull` sync fix (#913),
`apply_context_fixes.sh` + SOUL size guard (#914), self-healing repo sync (#915), model/provider
record (#916/#917), model-switch playbook + accurate state (#919), and this resolution. Hermes is now
a compaction-tuned, self-syncing, **capable + independent (gpt-5.4-mini on own key)** control plane.

## 💡 Session idea (Q-0089)
**Pin external models by dated snapshot, not alias, in control-plane configs.** The whole flapping
ordeal came from the alias `gpt-5.4-mini` resolving unevenly through OpenAI's allowlist; dated
snapshots (`gpt-5.4-mini-2026-03-17`) are granted deterministically and skip the propagation wait.
Worth making the default guidance for any own-key model setup (a one-liner in the operating prompt /
cheatsheet). Distinct from the prior per-role-model idea. Dedup-checked `docs/ideas/` — none.

## ⟲ Previous-session review (Q-0102)
Previous: `2026-06-15-hermes-model-playbook.md` (#919). It rightly refused to mark the switch "done"
while it flapped (good discipline — `configured` ≠ `stable`). What it got **wrong**: it asserted
"flapped >15 min, so NOT propagation" — false; OpenAI allowlist propagation genuinely flaps that long.
**Lesson:** for OpenAI allowlist/verification changes, "it's been 15 min" is *not* evidence against
propagation — they converge slowly and unevenly. Patience (or the dated id) beats hunting a phantom
second cause.

## 📋 Doc audit (Q-0104)
`check_docs --strict` green. The control-plane doc now accurately reads **CONFIRMED WORKING** (no more
stale "NOT YET STABLE"); the active-work claim is cleared; no runtime open item remains on the Hermes
model thread. Ledger unaffected (docs-only).
