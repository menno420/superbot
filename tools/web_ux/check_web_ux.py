#!/usr/bin/env python3.10
"""Web-UX budgets checker — task-success · nav coverage · perf · accessibility.

The pragmatic "sim-informed UX" harness for the program websites (the
2026-07-07 website design brief §2.4): instead of a full navigation-simulator
oracle, a **repeatable task-success checklist** — a defined list of real user
tasks ("find command X", "check the bot's status"), each executed in a real
Chromium via Playwright with an **interaction budget** (clicks + typed fields).
A redesign that makes a task impossible or over-budget fails the check, which
is the cheap, honest version of "layout decided by simulation".

Four check families:

1. **Task-success checklist** — the canonical user tasks, each with a
   max-interaction budget, executed against the v2 front-end.
2. **Nav coverage** — every SBDATA entity (area / feature / game + sampled
   commands) must render its page, not the 404 view.
3. **Perf budgets** — page-weight ceilings for the v2 shell and the data layer.
4. **Accessibility budgets** — per route × theme: exactly one h1, landmarks,
   labeled inputs, and token-contrast floors (ink vs surface), computed from
   the *rendered* page, both themes.

Run (local; Playwright + botsite deps needed, CI does not install them):

    python3.10 -m pip install -r botsite/requirements.txt playwright
    python3.10 tools/web_ux/check_web_ux.py            # starts its own server
    python3.10 tools/web_ux/check_web_ux.py --url http://127.0.0.1:8000

Provenance (Q-0105): added 2026-07-07 by the website-design session (Fable),
custom-built on Playwright (pre-installed in agent containers). UNVERIFIED:
confirm its verdicts against ground truth for a few sessions before trusting a
green; delete it if it proves unreliable over multiple sessions.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Agent containers pre-install Chromium at a pinned path (PLAYWRIGHT_BROWSERS_PATH);
# a pip-installed playwright may pin a NEWER browser build than the one on disk, so
# launch by explicit executable when the standard symlink exists (never run
# `playwright install` here — the environment forbids re-fetching browsers).
CHROMIUM = Path("/opt/pw-browsers/chromium")

# ── budgets ─────────────────────────────────────────────────────────────────
SHELL_WEIGHT_BUDGET = 150_000  # bytes: v2 html + css + js + ds assets (no data)
DATA_WEIGHT_BUDGET = 600_000  # bytes: /data.js (grows with the command surface)
CONTRAST_BODY_FLOOR = 4.5  # WCAG AA normal text
CONTRAST_MUTED_FLOOR = 3.0  # large/secondary text floor (ink-4 is caption-only)
COMMAND_SAMPLE = 24  # nav-coverage samples from the 365 command pages

VIEWPORTS = {"mobile": (375, 780), "tablet": (768, 1024), "desktop": (1280, 900)}


# ── task-success checklist ──────────────────────────────────────────────────
# Interactions: every click = 1, every text fill = 1, palette open = 1.
# `actions` is a list of (kind, *args); `expect` is (kind, value).
@dataclass
class Task:
    id: str
    desc: str
    budget: int
    actions: list[tuple]
    expect: tuple
    viewport: str = "desktop"
    failures: list[str] = field(default_factory=list)


TASKS: list[Task] = [
    Task(
        id="find-command-blackjack",
        desc="From home, open the !blackjack command page",
        budget=3,
        actions=[
            ("click", '[data-nav="commands"]'),
            ("fill", "[data-q]", "blackjack"),
            ("click", '.sb-cmdrow[href="#/command/blackjack"]'),
        ],
        expect=("hash", "#/command/blackjack"),
    ),
    Task(
        id="palette-find-fishing",
        desc="From home, learn what fishing does via the palette",
        budget=3,
        actions=[("palette", "fishing"), ("press_palette", "Enter")],
        # Any fishing entity page answers the question — the feature entry, the
        # game page, or the exact-name command page (all describe the minigame).
        expect=("hash_prefix_any", ["#/feature/", "#/game/", "#/command/"]),
    ),
    Task(
        id="check-status",
        desc="From home, check the bot's status",
        budget=1,
        actions=[("click", '[data-nav="status"]')],
        expect=("hash", "#/status"),
    ),
    Task(
        id="browse-games",
        desc="From home, browse the games list",
        budget=1,
        actions=[("click", '[data-nav="games"]')],
        expect=("hash", "#/games"),
    ),
    Task(
        id="filter-moderation-commands",
        desc="From home, list only moderation commands",
        budget=2,
        actions=[
            ("click", '[data-nav="commands"]'),
            ("click", '[data-f="moderation"]'),
        ],
        expect=("selector_text", ".v2-count", "of"),
    ),
    Task(
        id="latest-release",
        desc="From home, read the latest release notes",
        budget=1,
        actions=[("click", '[data-nav="changelog"]')],
        expect=("hash", "#/changelog"),
    ),
    Task(
        id="report-bug-about-warn",
        desc="From home, reach the real report form about !warn",
        budget=4,
        actions=[
            ("click", '[data-nav="commands"]'),
            ("fill", "[data-q]", "warn"),
            ("click", '.sb-cmdrow[href="#/command/warn"]'),
            ("click_nowait", 'a.sb-btn[href^="/submit?about=command%3Awarn"]'),
        ],
        expect=("url_contains", "/submit"),
    ),
    Task(
        id="find-mining-feature",
        desc="From home, open the mining feature's page",
        budget=3,
        actions=[
            ("click", '[data-nav="features"]'),
            ("fill", "[data-q]", "mining"),
            ("click_first", ".v2-feature-card"),
        ],
        expect=("hash_prefix", "#/feature/"),
    ),
    Task(
        id="deep-link-command",
        desc="A shared #/command/rank link renders the detail page directly",
        budget=0,
        actions=[("goto", "/v2#/command/rank")],
        expect=("selector", ".sb-cmd-name"),
    ),
    Task(
        id="mobile-menu-to-commands",
        desc="On a phone, open the menu and reach Commands",
        budget=2,
        viewport="mobile",
        actions=[
            ("click", "[data-menu-toggle]"),
            ("click", '[data-drawer] [data-nav="commands"]'),
        ],
        expect=("hash", "#/commands"),
    ),
]

A11Y_ROUTES = ["#/", "#/features", "#/commands", "#/games", "#/changelog", "#/status"]

A11Y_JS = """
() => {
  const problems = [];
  const h1s = document.querySelectorAll("h1");
  if (h1s.length !== 1) problems.push(`h1 count = ${h1s.length} (want exactly 1)`);
  if (!document.querySelector("main")) problems.push("no <main> landmark");
  if (!document.querySelector("nav")) problems.push("no <nav> landmark");
  if (!document.querySelector(".sb-skip")) problems.push("no skip link");
  document.querySelectorAll("input, textarea, select").forEach((el) => {
    const labelled = el.labels?.length || el.getAttribute("aria-label") ||
      el.getAttribute("aria-labelledby") || el.type === "hidden";
    if (!labelled) problems.push(`unlabeled <${el.tagName.toLowerCase()}> (${el.className})`);
  });
  document.querySelectorAll("button").forEach((el) => {
    const named = (el.textContent || "").trim() || el.getAttribute("aria-label") ||
      el.getAttribute("title") || el.querySelector("[class*=visually-hidden]");
    if (!named) problems.push(`nameless <button> (${el.className})`);
  });
  // token contrast, measured off the RENDERED theme
  const probe = document.createElement("div");
  document.body.appendChild(probe);
  const resolve = (v) => { probe.style.color = `var(${v})`; return getComputedStyle(probe).color; };
  const toRgb = (s) => (s.match(/[\\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
  const lum = ([r, g, b]) => {
    const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a, b) => {
    const [l1, l2] = [lum(toRgb(a)), lum(toRgb(b))].sort((x, y) => y - x);
    return (l1 + 0.05) / (l2 + 0.05);
  };
  const bg = resolve("--sb-bg"), surface = resolve("--sb-surface");
  const pairs = [
    ["--sb-ink-1", bg, 4.5], ["--sb-ink-2", bg, 4.5], ["--sb-ink-3", bg, 4.5],
    ["--sb-ink-1", surface, 4.5], ["--sb-ink-2", surface, 4.5], ["--sb-ink-3", surface, 4.5],
    ["--sb-ink-4", bg, 3.0], ["--sb-brand-ink", bg, 3.0], ["--sb-chart-mark", bg, 3.0],
  ];
  const contrast = pairs.map(([tok, base, floor]) => ({ tok, floor, ratio: ratio(resolve(tok), base) }));
  probe.remove();
  contrast.forEach((c) => { if (c.ratio < c.floor) problems.push(
    `contrast ${c.tok} = ${c.ratio.toFixed(2)} < ${c.floor}`); });
  return problems;
}
"""


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def local_server():
    port = free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "botsite.app:app", "--port", str(port)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(url + "/healthz", timeout=1)  # noqa: S310 - local http server
                break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("uvicorn did not come up on /healthz")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def run_task(browser, base_url: str, task: Task) -> tuple[bool, int, str]:
    """Execute one task; returns (ok, interactions_used, detail)."""
    w, h = VIEWPORTS[task.viewport]
    ctx = browser.new_context(viewport={"width": w, "height": h})
    page = ctx.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base_url + "/v2#/", wait_until="networkidle")
    used = 0
    try:
        for action in task.actions:
            kind = action[0]
            if kind == "goto":
                page.goto(base_url + action[1], wait_until="networkidle")
            elif kind in ("click", "click_nowait"):
                page.click(
                    action[1], timeout=4000, no_wait_after=(kind == "click_nowait")
                )
                used += 1
            elif kind == "click_first":
                page.locator(action[1]).first.click(timeout=4000)
                used += 1
            elif kind == "fill":
                page.fill(action[1], action[2], timeout=4000)
                used += 1
            elif kind == "palette":
                page.keyboard.press("Control+k")
                used += 1
                page.fill(".sb-palette input", action[1], timeout=4000)
                used += 1
            elif kind == "press_palette":
                page.keyboard.press(action[1])
                # navigation via keyboard, not a pointer interaction: free
            page.wait_for_timeout(150)
        kind, *args = task.expect
        ok = False
        if kind == "hash":
            ok = page.evaluate("location.hash").lstrip("#") == args[0].lstrip("#")
        elif kind == "hash_prefix":
            ok = (
                page.evaluate("location.hash")
                .lstrip("#")
                .startswith(args[0].lstrip("#"))
            )
        elif kind == "hash_prefix_any":
            h = page.evaluate("location.hash").lstrip("#")
            ok = any(h.startswith(p.lstrip("#")) for p in args[0])
        elif kind == "url_contains":
            # "commit" — landing on the URL is the success signal; the target page
            # may pull external assets (CDN) that stall the full load event here.
            page.wait_for_url(f"**{args[0]}**", timeout=4000, wait_until="commit")
            ok = args[0] in page.url
        elif kind == "selector":
            ok = page.locator(args[0]).count() > 0
        elif kind == "selector_text":
            ok = args[1] in (page.locator(args[0]).first.text_content() or "")
        if errors:
            return False, used, f"JS errors: {errors[:2]}"
        if not ok:
            return False, used, f"expectation {task.expect} not met (at {page.url})"
        if used > task.budget:
            return False, used, f"over budget: {used} > {task.budget}"
        return True, used, "ok"
    except Exception as exc:  # noqa: BLE001 - report any Playwright failure as task failure
        return False, used, f"{type(exc).__name__}: {exc}"
    finally:
        ctx.close()


def run_nav_coverage(browser, base_url: str) -> list[str]:
    problems: list[str] = []
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(base_url + "/v2#/", wait_until="networkidle")
    entities = page.evaluate(
        """() => ({
          areas: SBDATA.AREAS.map((a) => a.id),
          features: (SBDATA.FEATURES || []).map((f) => f.key),
          games: SBDATA.GAMES.map((g) => g.id),
          commands: SBDATA.COMMANDS.map((c) => c.name),
        })""",
    )
    step = max(1, len(entities["commands"]) // COMMAND_SAMPLE)
    routes = (
        [f"#/area/{a}" for a in entities["areas"]]
        + [f"#/feature/{k}" for k in entities["features"]]
        + [f"#/game/{g}" for g in entities["games"]]
        + [f"#/command/{c}" for c in entities["commands"][::step]]
    )
    for route in routes:
        page.evaluate(f"location.hash = {json.dumps(route.lstrip('#'))}")
        page.wait_for_timeout(60)
        if page.locator("text=Nothing here").count():
            problems.append(f"{route} renders the 404 view")
    ctx.close()
    return problems


def run_perf(base_url: str) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []
    shell_assets = [
        "/v2",
        "/v2/app.js",
        "/v2/app.css",
        "/ds/tokens.css",
        "/ds/components.css",
        "/ds/ds.js",
    ]
    shell = 0
    for path in shell_assets:
        with urllib.request.urlopen(base_url + path, timeout=5) as resp:  # noqa: S310 - local/CLI-given http url
            shell += len(resp.read())
    with urllib.request.urlopen(base_url + "/data.js", timeout=5) as resp:  # noqa: S310 - local/CLI-given http url
        data_len = len(resp.read())
    notes.append(f"shell weight {shell:,}B (budget {SHELL_WEIGHT_BUDGET:,}B)")
    notes.append(f"data.js {data_len:,}B (budget {DATA_WEIGHT_BUDGET:,}B)")
    if shell > SHELL_WEIGHT_BUDGET:
        problems.append(
            f"v2 shell weight {shell:,}B over budget {SHELL_WEIGHT_BUDGET:,}B"
        )
    if data_len > DATA_WEIGHT_BUDGET:
        problems.append(f"/data.js {data_len:,}B over budget {DATA_WEIGHT_BUDGET:,}B")
    return problems, notes


def run_a11y(browser, base_url: str) -> list[str]:
    problems: list[str] = []
    for theme in ("dark", "light"):
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto(base_url + "/v2#/", wait_until="networkidle")
        page.evaluate(f"SBDS.theme.set({json.dumps(theme)})")
        for route in A11Y_ROUTES:
            page.evaluate(f"location.hash = {json.dumps(route.lstrip('#'))}")
            page.wait_for_timeout(120)
            for p in page.evaluate(A11Y_JS):
                problems.append(f"[{theme} {route}] {p}")
        ctx.close()
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--url", help="use a running server instead of starting one")
    parser.add_argument(
        "--skip", default="", help="comma list: tasks,coverage,perf,a11y"
    )
    args = parser.parse_args(argv)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    from playwright.sync_api import sync_playwright

    server_cm = contextlib.nullcontext(args.url) if args.url else local_server()
    failures = 0
    with server_cm as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=str(CHROMIUM) if CHROMIUM.exists() else None,
        )
        if "tasks" not in skip:
            print("── task-success checklist ──")
            for task in TASKS:
                ok, used, detail = run_task(browser, base_url, task)
                mark = "PASS" if ok else "FAIL"
                failures += 0 if ok else 1
                print(
                    f"  [{mark}] {task.id:32s} {used}/{task.budget} interactions — {detail if not ok else task.desc}"
                )
        if "coverage" not in skip:
            print("── nav coverage (every entity renders) ──")
            problems = run_nav_coverage(browser, base_url)
            failures += len(problems)
            print(
                "  [PASS] all sampled entity routes render"
                if not problems
                else "\n".join(f"  [FAIL] {p}" for p in problems)
            )
        if "perf" not in skip:
            print("── perf budgets ──")
            problems, notes = run_perf(base_url)
            failures += len(problems)
            for n in notes:
                print(f"  [info] {n}")
            for p in problems:
                print(f"  [FAIL] {p}")
        if "a11y" not in skip:
            print("── accessibility budgets (both themes) ──")
            problems = run_a11y(browser, base_url)
            failures += len(problems)
            print(
                "  [PASS] landmarks/labels/contrast within budget"
                if not problems
                else "\n".join(f"  [FAIL] {p}" for p in problems)
            )
        browser.close()

    print(f"\n{'ALL CHECKS PASS ✓' if not failures else f'{failures} FAILURE(S)'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
