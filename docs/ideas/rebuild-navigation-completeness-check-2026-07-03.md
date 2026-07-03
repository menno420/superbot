# Idea — navigation-completeness check (enforce the Back+Home contract)

> **Status:** `ideas` — capture only. **Subsystem:** none (rebuild interaction runtime / nav).
> **Provenance:** Phase-A hub/navigation session (PR #1684), the enforcement arm of Q-0231.

## The idea

Q-0231 guarantees **Back + Home on every rendered panel state, at every depth, across unlimited
re-renders** — framework-injected, not per-panel discipline. Rules like that decay unless a test
proves them (Q-0132 "enforce, don't exhort"). So in the new repo: a **navigation-completeness
golden** that drives the panel framework through every declared node and every re-render path and
asserts each resulting state carries both a working **Back** (resolves to the real parent / stack)
and a working **Home** (resolves to the help root) — plus a **preset-coverage** assertion that
every feature belongs to ≥1 preset (nothing is unreachable in *every* preset).

## Why it's worth having

The whole point of making Back/Home a *framework guarantee* is that no panel can forget them — but
"the framework injects them" is only true until someone adds a render path that bypasses it. A
golden that walks every node turns the guarantee into something CI proves, which is exactly the
promise the owner asked for ("no matter how many times the panel got updated"). Cheap because the
hub is generated — the checker just enumerates the manifest.

## Routing

Belongs to Gate-0 / the NavigationSpec + hub-engine plan (Phase B); ships with the panel framework.
Detail: [`../planning/rebuild-hub-navigation-presets-2026-07-03.md`](../planning/rebuild-hub-navigation-presets-2026-07-03.md)
§2. Not current-repo work.
