# 2026-06-21 — Reaction-roles plan: UI-direction refinement (web vs in-Discord)

> **Status:** `in-progress` — follow-up to #1215. The owner shared a screen recording of Carl's
> reaction-role "menu we need" and asked whether it's even possible in discord.py + to make it
> nicer/smoother. Refining the plan to settle that. Docs-only. Flips to `complete` last (Q-0133).

## Arc

The recording is **Carl-bot's web dashboard** (`carl.gg/dashboard`) in a phone browser — HTML
web-form UI (native `<select>` modes, radio list, role multi-selects, Get Premium upsell), **not**
a Discord message. So the "exact menu" is unbuildable in *any* Discord library — it's a website.
discord.py renders Discord components (buttons/selects/modals), not web forms. But we already own a
website + React/Tailwind design system, so we can build it **nicer** — on two surfaces.

Adding §3.5 to `reaction-roles-overhaul-plan-2026-06-21.md`: the web-vs-Discord answer + the
two-surface direction (A = web builder, control-API-gated; B = in-Discord modern builder,
buildable now) + a 4th owner design Q (surface priority).

(Body filled at close.)
