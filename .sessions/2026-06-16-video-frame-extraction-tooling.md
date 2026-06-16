# Session — video frame-extraction tooling (so future sessions can see uploads immediately)

> **Status:** `in-progress`

## What I'm about to do

Follow-up to the BTD6 live-events fix (#953, merged): the maintainer asked me to **document the
best/most efficient way to view/extract a video they send**, so a future session knows it
immediately instead of rediscovering it (this session burned ~10 tool-calls finding it).

The findings worth encoding: there is no `ffmpeg`/`ffprobe` binary and no video player in the remote
env, but `imageio` + `imageio-ffmpeg` (bundled static ffmpeg) work once installed onto **python3.10**
(bare `pip` targets 3.11); the `pyav` plugin isn't installed so use `plugin="FFMPEG"`; you must
**stream** frames (a ~90s phone clip is ~2600 frames ≈ 19 GB if listed → OOM-killed); downscale with
Pillow before saving; a **contact sheet** of evenly-spaced frames is the fastest whole-clip overview;
uploads live at `/root/.claude/uploads/<dirs>/<file>`.

Ship it as a reusable, verified script + a journal Quick-reference pointer:
1. `scripts/extract_video_frames.py` — one command builds a labelled contact sheet + sample frames
   (and `--range … --crop-top` to zoom a transition). Lazy-imports the video stack with a clear
   install hint; Q-0105 provenance/"delete-if-unreliable" header; pure dev tool (nothing in
   `disbot/`/tests imports it).
2. A `.session-journal.md` ⚡ Quick-reference row pointing at it.

## What was done

- `scripts/extract_video_frames.py` — created + verified end-to-end on the actual upload
  (2591-frame recording → `_contact_sheet.png` + samples; contact sheet Read back and legible).
  black/isort/ruff clean (used `tempfile.gettempdir()` for the default out-dir to satisfy S108 and
  renamed a param to satisfy N803 rather than broadening `scripts/*` lint ignores).
- `.session-journal.md` — added the "See a video the maintainer sent" Quick-reference row (no
  ffmpeg in-env → bundled `imageio-ffmpeg`; stream, never list; contact-sheet-first; uploads path).

## 💡 Session idea

(pending)

## ⟲ Previous-session review

(pending)
