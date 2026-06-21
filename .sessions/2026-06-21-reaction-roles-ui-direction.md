# 2026-06-21 — Reaction-roles plan: UI-direction refinement (web vs in-Discord)

> **Status:** `complete` — follow-up to #1215. The owner shared a screen recording of Carl's
> reaction-role "menu we need" and asked whether it's even possible in discord.py + to make it
> nicer/smoother. Refined the plan to settle that. Docs-only → self-merge on green.

> **Run type:** `manual`

## Arc

The recording is **Carl-bot's web dashboard** (`carl.gg/dashboard`) in a phone browser — HTML
web-form UI (native `<select>` modes, radio list, role multi-selects, Get Premium upsell), **not**
a Discord message. So the "exact menu" is unbuildable in *any* Discord library — it's a website.
discord.py renders Discord components (buttons/selects/modals), not web forms. But we already own a
website + React/Tailwind design system, so we can build it **nicer** — on two surfaces.

Adding §3.5 to `reaction-roles-overhaul-plan-2026-06-21.md`: the web-vs-Discord answer + the
two-surface direction (A = web builder, control-API-gated; B = in-Discord modern builder,
buildable now) + a 4th owner design Q (surface priority).

## Findings / decisions

- **Verified from the video** (extracted frames via `imageio-ffmpeg`, since `ffmpeg` wasn't
  installed): it is unambiguously a **mobile browser** rendering Carl's dashboard — Android status
  bar + nav buttons, web `<select>`/radio/multiselect controls, a "Get Premium" upsell card. Each
  mode's live description is captured in §3.5 (unique/verify/drop/limit/binding all shown).
- **Decision made alone:** framed the feature as **two surfaces on one foundation** and recommended
  **Surface B (in-Discord) first** because Surface A (web) is control-API-gated. Routed the call to
  the owner as plan §9 Q4 rather than presuming it.

## 📤 Run report

- **Did:** settled the "is Carl's menu possible in discord.py?" question (it's a web app, not a Discord UI) and added the two-surface UI direction to the plan · **Outcome:** shipped (plan refinement)
- **Shipped:** #1216 — reaction-roles plan §3.5 UI direction (docs-only)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** plan §9 Q4 — ship in-Discord builder (Surface B) first, then the web builder when the control-API write side opens? (+ the 3 prior design Qs)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (direct owner request)
- **↪ Next:** owner picks the surface priority (Q4) + answers Q1–Q3; then build reaction-roles PR 1 (audited seam, unblocked) → PR 2 (Surface B in-Discord builder)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1215); 1 pending (#1216) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 0 (this is a refinement of the #1215 idea/plan) |
| Ideas groomed | 0 |
