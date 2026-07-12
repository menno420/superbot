# Prompt wait-language lint — an enforcing guard against presence-gating regressions

> **Status:** `captured` · **Subsystem:** none (agent-workflow / fleet-manager registry)
> **Origin:** session ender (2026-07-12, fleet re-arm session, PR #2048 / Q-0271)

## The idea

A small checker (fleet-manager-owned, since the registry is the prompt source of truth) that
lints every `projects/*/instructions.md` + `coordinator-prompt.md` + `failsafe-prompt.md` for
**wait-language** — the phrase patterns that teach a seat to gate work on owner presence:

- "wait for the owner / for approval / for review / until confirmed"
- "once the owner approves / when you get permission / ask before continuing"
- "pause here", "stop and wait", "do not proceed until"

…except inside an explicitly-marked OWNER-ONLY block (the Q-0271 list), which is the one place
wait-semantics are legitimate. Output: file + line + the offending phrase; severity error in the
registry's CI.

## Why it's worth having

The 2026-07-12 owner directive (Q-0271) exists because seats *hallucinated* review gates — but
prompt bodies themselves have historically *carried* wait-language (frozen-clicks gates, "awaiting
owner merge" facts, "park for owner review" phrasings), and every restamp risks reintroducing it.
The AUTONOMY RIDER fixes the posture at runtime; this lint fixes it at the **source**, in the
"enforce, don't exhort" shape Q-0194/Q-0132 prefer. It would have flagged the venture-lab
frozen-clicks staleness and the trading "PR #37 awaiting owner merge" drift found by the
2026-07-11 verification pass — both were wait-facts sitting in prompt bodies after their gates
had cleared.

## Sketch

Stdlib regex pass over the registry dirs + `UNIVERSAL.md`; an allowlist marker
(`<!-- owner-only -->` fence or the literal `OWNER-ONLY LIST` heading) exempts its span; ~50
lines + tests. Routes to the fleet-manager lane (registry single-writer owns its own CI); this
capture is the superbot-side intake so the Ideas Lab / manager can pick it up.
