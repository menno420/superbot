# Session — 2026-06-27 · Setup wizard: "Where can people use commands?" (per-channel command access)

> **Status:** `in-progress` — born-red card (Q-0133); flip to `complete` as the final step. Run type: owner-directed (chat).

## What this run is doing (HOLD)

Owner flagged that the new Essential Setup wizard is missing **"allowed commands per channels."**
Investigation confirmed it + mapped the surrounding gaps; this run ships the contained, enforced,
high-value half.

**About to do:** add a new plain-language spine step **"Where can people use commands?"** to
`disbot/views/setup/essential_setup.py`, backed by the already-enforced + cached **Command Access**
seam (`services.command_access_service.set_policy`): whole server / only chosen channels / off for
members (admins keep access). Direct-apply, audited, jargon-clean. + tests + docs.

Findings + the deferred follow-on (fine-grained per-feature `cog_routing`, which needs missing
runtime enforcement wired into the command gate) are written up in the run report below at close.
