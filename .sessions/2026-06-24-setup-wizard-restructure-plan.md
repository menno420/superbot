# Session — 2026-06-24 · setup-wizard restructure plan

> **Status:** `in-progress` — born-red. Researching + simulating + planning the setup-wizard
> restructure the owner asked for: now that nearly all setup-worthy functions exist, decide **what
> belongs in the wizard and in what step order**, so it's quick, intuitive, **needs zero Discord/bot
> knowledge, no jargon**, button/dropdown-driven, and **each step is one complete action that finishes
> a setup step properly**. Plan-first (+ a simulator); no runtime behaviour change this session.

## What I'm about to do

1. Map the *current* wizard end-to-end (sections, hub, depths, session, advisor → draft → Final Review).
2. Inventory every setup-worthy function across subsystems/cogs → what's in the wizard vs. missing.
3. Catalog the "never worked as intended" gaps + jargon/UX problems.
4. Build a setup-wizard simulator (`tools/sim/`) modelling a non-technical user completing setup
   (step count, completeness, jargon score) to validate the proposed structure.
5. Write `docs/planning/setup-wizard-restructure-plan-2026-06-24.md`.
