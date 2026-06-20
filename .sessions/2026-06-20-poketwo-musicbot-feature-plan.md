# 2026-06-20 — Pokétwo + MusicBot research report → feature mapping plan

> **Status:** `in-progress`

## Arc

Owner uploaded a research report on **Pokétwo** (Pokémon catching bot) and **JMusicBot**
(music bot) and asked: *"review this … create a plan so we can implement as much of these
features in a proper way."* Owner steered this session to **plan only, build nothing yet**
(answered in-session), and for the music half **architecture-review pack only** (respect the
Q-0041 voice gate, don't build playback).

Deliverable: a docs-only feature-mapping plan + the music architecture-review pack + routing
of the gated owner decisions. No runtime (`disbot/`) code this session.

## Plan (what this PR adds)

- `docs/planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md` — the report → repo
  mapping (every feature classified: extend-existing / buildable-now / owner-gated / rejected),
  with PR-sized specs for the net-new buildable lanes.
- `docs/planning/voice-music-architecture-review-2026-06-20.md` — the Q-0041-required
  voice/music decision pack (legal · infra · architecture fit · permissions · cost).
- `docs/ideas/wild-encounters-activity-spawning-2026-06-20.md` — capture of the signature
  net-new mechanic (no existing analog) + README index entry.
- Router: Q-0186 (Pokétwo build-sequencing DISCUSS) appended; the music pack feeds existing Q-0041.

(In-progress; flipped to `complete` as the final step.)
