# Session — Welcome phase 2: opt-in PIL welcome card

> **Status:** `in-progress`

## What I'm about to do

Dispatch run, no explicit work order → take the next ▶ startable plan slice: the band-#900
decade-queue **slot 7 — welcome phase 2 (PIL cards)** (`ready` quick-win, Q-0110). The
`render_welcome_card` prototype already exists in `utils/ux_patterns/image_builders.py` (the UX
Lab gallery). This run promotes it to a real, opt-in feature: when a new `welcome_card_enabled`
setting is ON (under the master + join toggles), the join greeting attaches a rendered welcome
card image. Fully additive — default OFF means byte-identical behaviour on every existing guild.

Plan: a production `utils/welcome_render.py` renderer (pure, lazy-PIL, `bytes | None`) · the
`welcome_card_enabled` scalar setting + schema spec · `WelcomePolicy.card_enabled` +
`renders_card` · the `welcome_service.handle_member_join` attach (fail-safe, `to_thread`) · tests.
