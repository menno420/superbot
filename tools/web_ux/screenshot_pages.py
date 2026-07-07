#!/usr/bin/env python3.10
"""Screenshot every program-site page in both themes at three widths.

The visual half of the website verification loop ("design claims without
rendered proof don't count"): drives the real FastAPI app in Chromium and
captures full-page screenshots of every v2 page, the living style guide, and
the program console — dark + light × mobile/tablet/desktop.

    python3.10 tools/web_ux/screenshot_pages.py --out /tmp/shots
    python3.10 tools/web_ux/screenshot_pages.py --out shots --widths 1280 --themes dark

Provenance (Q-0105): added 2026-07-07 by the website-design session (Fable).
UNVERIFIED: eyeball a few outputs before trusting a batch; delete if unreliable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_web_ux import CHROMIUM, VIEWPORTS, local_server  # noqa: E402

PAGES = {
    "home": "/v2#/",
    "features": "/v2#/features",
    "feature-mining": "/v2#/feature/mining",
    "area-games": "/v2#/area/games",
    "commands": "/v2#/commands",
    "command-blackjack": "/v2#/command/blackjack",
    "games": "/v2#/games",
    "game-fishing": "/v2#/game/fishing",
    "changelog": "/v2#/changelog",
    "status": "/v2#/status",
    "styleguide": "/design",
    "console": "/console/",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, help="output directory")
    parser.add_argument("--url", help="use a running server instead of starting one")
    parser.add_argument(
        "--widths", default="mobile,tablet,desktop", help="comma list of viewport names"
    )
    parser.add_argument("--themes", default="dark,light", help="comma list of themes")
    parser.add_argument(
        "--pages", default=",".join(PAGES), help="comma list of page keys"
    )
    parser.add_argument(
        "--quality", type=int, default=60, help="JPEG quality (screenshots are .jpg)"
    )
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    widths = [w.strip() for w in args.widths.split(",") if w.strip()]
    themes = [t.strip() for t in args.themes.split(",") if t.strip()]
    pages = {
        k: PAGES[k] for k in (p.strip() for p in args.pages.split(",")) if k in PAGES
    }

    import contextlib

    from playwright.sync_api import sync_playwright

    server_cm = contextlib.nullcontext(args.url) if args.url else local_server()
    count = 0
    with server_cm as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=str(CHROMIUM) if CHROMIUM.exists() else None
        )
        for vp_name in widths:
            w, h = VIEWPORTS[vp_name]
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            for theme in themes:
                for key, path in pages.items():
                    page.goto(base_url + path, wait_until="networkidle")
                    page.evaluate(f"window.SBDS && SBDS.theme.set({json.dumps(theme)})")
                    page.wait_for_timeout(250)
                    shot = out / f"{key}--{theme}--{vp_name}.jpg"
                    page.screenshot(
                        path=str(shot),
                        full_page=True,
                        type="jpeg",
                        quality=args.quality,
                    )
                    count += 1
                    print(f"  {shot}")
            ctx.close()
        browser.close()
    print(f"\nwrote {count} screenshots to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
