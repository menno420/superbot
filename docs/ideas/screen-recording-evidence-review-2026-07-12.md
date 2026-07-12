# Screen-recording evidence review helper (2026-07-12)

> **Status:** `ideas` — session ender (Q-0089), overnight-review / email-finalization session.
> **Subsystem:** none (agent workflow / EAP evidence tooling).
> **Gate:** ready — a tiny script + a doc note; no owner blocker. Disposable convenience
> (delete if it proves unused across a few sessions — provenance-header rule, Q-0105).

## The idea

A one-command helper for reviewing an owner-uploaded **screen recording** the way we already
review screenshots: extract scene-change frames (ffmpeg `select='gt(scene,N)'`) plus a
regular-interval fallback, drop them in a scratch dir, and hand the agent a numbered frame
set to read. Package the ffmpeg dependency so no ad-hoc install is needed at review time.

## Why it's worth having

The EAP evidence flow keeps producing **video**, not just stills — the owner sent a 32-second
Routines-surface recording this session that changed two of the email's findings (serialization
vs. real failure; the arrived run-surface). Reviewing it took an ad-hoc `pip install
imageio-ffmpeg` + a hand-built frame-extraction pipeline (Q-0194 friction: no tool existed,
built one live). The next recording — and there will be more, the owner records his screen
often — should be one command, not a rediscovery. Frames extracted this way are also directly
committable as `fig-NN` evidence (that's exactly what figs 33–35 became).

## Sketch

`scripts/extract_recording_frames.sh <video> <outdir>`: resolve ffmpeg via
`imageio_ffmpeg.get_ffmpeg_exe()` (lazy, dev-only, `pytest.importorskip`), emit scene-change
frames at a tunable threshold + a 1-per-Ns fallback, print a frame manifest. ~20 lines. Pairs
with the existing `screenshots-<date>/index.md` convention: reviewed frames that earn a caption
get copied in as `fig-NN`, the rest are dispositioned. Keep the raw video out of the repo
(device-only, like the phone shots).

## Dedup

Grepped `docs/ideas/` (`recording`, `video`, `ffmpeg`, `frame`, `screenshot`): nothing covers
video evidence; the screenshot-set convention exists only as prose in the `screenshots-*/`
index files. This is the video sibling of that convention.
