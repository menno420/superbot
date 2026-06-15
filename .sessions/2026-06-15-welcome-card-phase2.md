# Session — Welcome phase 2: PIL greeting card on join (safety lane, decade-queue slot 7)

> **Status:** `in-progress`

## What I'm about to do

Band-#900 decade queue **slot 7** — the safety-lane quick-win (Q-0110). The welcome v1
feature greets joining members with an embed; phase 2 attaches an optional **PIL greeting
card** (avatar initials-disc + greeting + member number) to the join embed, gated by a new
`welcome_card_enabled` setting (OFF by default), degrading cleanly to embed-only when Pillow
is unavailable or the toggle is off.

Plan:
- Promote the `render_welcome_card` prototype (currently a UX-lab gallery sample in
  `utils/ux_patterns/image_builders.py`) into a production renderer `utils/welcome_render.py`,
  and have the gallery import it (one source of truth — kills the prototype/feature split).
- Add the `card_enabled` setting end-to-end: `settings_keys/welcome.py`, the
  `welcome_config` default + `WelcomePolicy` field + `load_policy` read, the
  `cogs/welcome/schemas.py` SettingSpec.
- Wire `welcome_service.handle_member_join` to render + attach the card when enabled.
- Tests for the renderer, the new setting, the schema parity, and the service attach path.
