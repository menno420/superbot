# 2026-07-11 — verify + improve project prompts/instructions for the next batch

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed (verify all project prompts → improve for next round)

## What this did

Owner asked (while the wrap-up prompt runs across projects): verify all current project
prompts/instructions, improve them for the next batch, keep every existing one, create new
ones for anything really different, and improve existing where the main goal stays the same.

VERIFIED the whole set (2 read-only subagents + direct reads of UNIVERSAL v4 + venture/idea/sim
instructions):
- The canonical registry is `fleet-manager/projects/<repo>/{instructions,coordinator-prompt,
  failsafe-prompt}.md` + `UNIVERSAL.md` (manager is the ONLY writer → I produced a reviewable
  superbot proposal, did not touch the registry, to avoid colliding with the live fm lane).
- All 15 live `instructions.md` are CURRENT (v2/v3, 2026-07-11, every one carries the canonical
  permissions block). The drift is concentrated in the v1 companion prompts (coordinator +
  failsafe, one revision behind — stale PR/trigger refs: trading #37 merged, fm deleted trigger,
  venture boot-state, websites/forge re-paste-owed, kit re-arm).
- Games are currently 4 separate Projects → the owner's decision collapses them to one Games
  Project (flagship mineverse); idea+sim merge to one Ideation→Evidence seat.

PRODUCED `docs/owner/next-round-founding-prompts-2026-07-11.md`: the verification result, the
next-batch IMPROVEMENT DELTA (gen-3 hygiene rider v5 + the portfolio stop-rule/release-operator
posture), the per-Project fate map (keep/update/new/retire — incl. the venture-lab unfreeze
stale-fix + the companion re-sync), and 2 NEW paste-ready merged-Project instruction bodies
(Ideation→Evidence, Games). Edit-registry-first: the manager applies it.

Landed on the same PR as the consolidation blueprint (#2005) — the branch was rebased to
resolve its stale conflict and this kit stacked on top; both are the next-round prep arc.

Docs-only; `check_docs --strict` clean.

## 💡 Session idea (Q-0089)

A `check_companion_version.py` for the registry: assert every `coordinator-prompt.md` +
`failsafe-prompt.md` version header is >= its seat's `instructions.md` header (no companion may
lag its instructions). The whole drift this verification found is companions one revision behind
— a 20-line checker turns "re-sync owed" from a manual sweep into a gate. Extends the
edit-registry-first discipline with an enforcing guard (Q-0132 enforce-don't-exhort).

## ⟲ Previous-session review (Q-0102)

The registry's edit-registry-first + one-writer discipline is genuinely good — it made
verification clean (one canonical home, version-stamped). The gap it surfaced: the companion
prompts drift because only `instructions.md` gets the ORDER-fold re-issue while coordinator/
failsafe are hand-updated later. Improvement: fold companions into the same re-issue pass (the
session idea's checker enforces it), so a re-issue never leaves a seat half-updated.

## Documentation audit (Q-0104)

Docs-only. The kit is a proposal for the manager to apply (edit-registry-first); no registry
write. Telemetry appended. Claim deleted at close. Reachable via the current-state pointer.

## 📤 Run report

- **Did:** verified all project prompts/instructions (2 subagents + direct reads) + produced the
  improved/consolidated next-round founding-prompt kit · **Outcome:** shipped
- **Run type:** `owner-directed`
- **⚑ Self-initiated:** none (owner-directed); the kit is a proposal, applied by the manager
- **↪ Next:** on the wrap-up replies, the manager folds the §2 rider + §3 updates into the
  registry + creates the 2 merged-Project dirs; owner re-pastes changed Custom Instructions
