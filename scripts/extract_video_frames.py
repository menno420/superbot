#!/usr/bin/env python3.10
"""Extract frames from a video the maintainer sends (screen recordings etc.).

WHY THIS EXISTS / PROVENANCE (Q-0105):
  Added 2026-06-16 after a session spent ~10 tool-calls rediscovering how to
  *see* a Discord screen-recording the maintainer uploaded (there is no video
  player and no `ffmpeg`/`ffprobe` binary in the remote env). This script is
  the distilled "do it immediately" path so a future session doesn't repeat
  that. UNVERIFIED beyond that one session — confirm its output against the
  real video a couple of times before fully trusting it. **Delete this script
  if it proves unreliable / unused across several sessions** (it's a pure dev
  convenience — nothing in `disbot/` or the test suite imports it).

THE KEY FACTS THIS ENCODES (the parts that cost time to find):
  1. No `ffmpeg`/`ffprobe` binary exists, but the `imageio` + `imageio-ffmpeg`
     pip packages bundle a *static* ffmpeg. Install them onto the CI
     interpreter — bare `pip` resolves to a *different* Python (3.11) than the
     `python3.10` everything else uses:
         python3.10 -m pip install imageio imageio-ffmpeg
  2. The `pyav` imageio plugin is NOT installed — pass plugin="FFMPEG".
  3. NEVER load every frame into memory. A ~90s phone recording is ~2600
     frames at ~1080x2340x3 ≈ 7.5 MB each ≈ 19 GB → the process is killed.
     Stream with `imageio.v3.imiter(...)` and only keep the indices you want.
  4. Downscale each saved frame with Pillow (height ~1000px) so the PNGs are
     small enough to Read back quickly but still legible.
  5. Uploaded files land under  /root/.claude/uploads/<dirs>/<file>.
  6. Do NOT `cd` in the Bash tool — it wedges the shell for the turn; this
     script takes absolute paths so you never need to.

USAGE (from the repo root):
  python3.10 scripts/extract_video_frames.py <video> [options]

  # Fastest first look — a single contact-sheet image of the whole video:
  python3.10 scripts/extract_video_frames.py /root/.claude/uploads/.../clip.mp4

  # Then zoom into a transition you spotted (dense range, top-cropped for
  # readable embed titles):
  python3.10 scripts/extract_video_frames.py clip.mp4 --range 700 1010 25 --crop-top

Options:
  --out DIR        output dir (default: /tmp/vidframes)
  --contact N      build an NxN-ish contact sheet of N frames (default 48; 0 disables)
  --sample N       also save N individual evenly-spaced frames (default 12; 0 disables)
  --range A B STEP save individual frames for indices in range(A, B, STEP)
  --height H       downscale saved frames to H px tall (default 1000)
  --cols C         contact-sheet columns (default 8)
  --crop-top       crop saved/sheet frames to the top ~62% (Discord embed area)

Then Read the PNGs in /tmp/vidframes (the contact sheet first).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

_DEFAULT_OUT = str(Path(tempfile.gettempdir()) / "vidframes")

_INSTALL_HINT = (
    "Missing video deps. Install them onto the CI interpreter (NOT bare pip):\n"
    "    python3.10 -m pip install imageio imageio-ffmpeg"
)


def _load_deps():  # type: ignore[no-untyped-def]
    """Lazy-import the optional video stack; print the install cmd if absent."""
    try:
        import imageio.v3 as iio  # noqa: PLC0415
        from PIL import Image  # noqa: PLC0415
    except ImportError:
        print(_INSTALL_HINT, file=sys.stderr)
        raise SystemExit(2) from None
    return iio, Image


def _count_frames(iio, src: str) -> int:  # type: ignore[no-untyped-def]
    """Count frames by streaming (one cheap pass, no frames retained)."""
    return sum(1 for _ in iio.imiter(src, plugin="FFMPEG"))


def _prep(img, image_mod, height: int, crop_top: bool):  # type: ignore[no-untyped-def]
    """Downscale a frame ndarray to `height` px tall, optionally top-crop."""
    pic = image_mod.fromarray(img)
    w, h = pic.size
    scale = height / h
    pic = pic.resize((max(1, int(w * scale)), height))
    if crop_top:
        pic = pic.crop((0, 0, pic.size[0], int(height * 0.62)))
    return pic


def _even_indices(total: int, n: int) -> list[int]:
    if n <= 0 or total <= 0:
        return []
    if n >= total:
        return list(range(total))
    return [round(i * (total - 1) / (n - 1)) for i in range(n)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", help="path to the video file (absolute is safest)")
    ap.add_argument("--out", default=_DEFAULT_OUT)
    ap.add_argument("--contact", type=int, default=48)
    ap.add_argument("--sample", type=int, default=12)
    ap.add_argument("--range", type=int, nargs=3, metavar=("A", "B", "STEP"))
    ap.add_argument("--height", type=int, default=1000)
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--crop-top", action="store_true")
    args = ap.parse_args(argv)

    src = str(Path(args.video).expanduser())
    if not Path(src).is_file():
        print(f"No such file: {src}", file=sys.stderr)
        return 1

    iio, Image = _load_deps()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    total = _count_frames(iio, src)
    print(f"frames: {total}")
    if total == 0:
        print("No frames decoded — is this a video file?", file=sys.stderr)
        return 1

    # Which individual frames to save: explicit range wins, else even sample.
    if args.range:
        a, b, step = args.range
        wanted = {idx for idx in range(a, min(b, total), max(1, step))}
    else:
        wanted = set(_even_indices(total, args.sample))

    # Contact-sheet frames (separate, evenly spaced across the whole video).
    sheet_idx = {idx: i for i, idx in enumerate(_even_indices(total, args.contact))}
    cellw = max(1, int(args.height * 0.45))  # portrait-ish thumbnail width
    cellh = args.height
    cols = max(1, args.cols)
    rows = (len(sheet_idx) + cols - 1) // cols if sheet_idx else 0
    sheet = (
        Image.new("RGB", (cols * cellw, rows * cellh), (20, 20, 20)) if rows else None
    )
    draw = None
    if sheet is not None:
        from PIL import ImageDraw  # noqa: PLC0415

        draw = ImageDraw.Draw(sheet)

    saved = 0
    for idx, frame in enumerate(iio.imiter(src, plugin="FFMPEG")):
        if idx in wanted:
            _prep(frame, Image, args.height, args.crop_top).save(
                out / f"frame_{idx:05d}.png",
            )
            saved += 1
        if sheet is not None and idx in sheet_idx:
            cell = Image.fromarray(frame).resize((cellw, cellh))
            i = sheet_idx[idx]
            r, c = divmod(i, cols)
            sheet.paste(cell, (c * cellw, r * cellh))
            if draw is not None:
                draw.text((c * cellw + 4, r * cellh + 4), str(idx), fill=(255, 255, 0))

    if sheet is not None:
        sheet.save(out / "_contact_sheet.png")
        print(f"contact sheet: {out / '_contact_sheet.png'}")
    print(f"saved {saved} individual frame(s) to {out}")
    print("Read the PNGs (the _contact_sheet.png first) to see the video.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
