#!/usr/bin/env python3.10
"""export_pattern_library.py — generate docs/ux/pattern-library.md from the registry.

Provenance: UX Lab plan PR C (`docs/planning/ux-lab-interface-gallery-plan-
2026-06-12.md` §3/§8) — the registry in ``utils/ux_patterns`` is the source
of truth; this doc is its rendered export, so the two cannot drift
(``tests/unit/docs/test_pattern_library_doc.py`` regenerates and compares).

Usage::

    python3.10 scripts/export_pattern_library.py          # rewrite the doc
    python3.10 scripts/export_pattern_library.py --check  # exit 1 on drift
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "ux" / "pattern-library.md"

_CATEGORY_TITLES = {
    "buttons": "🔘 Buttons",
    "selects": "📋 Selects",
    "modals": "⌨️ Modals",
    "embeds": "🪧 Embed archetypes",
    "layout_v2": "🧱 Components V2 (experimental)",
    "image": "🎨 PIL image cards",
    "mockup": "🎭 Mock studio / review patterns",
    "probe": "🔬 Limit probes",
}

_STATUS_BADGES = {
    "stable": "🟢 stable",
    "experimental": "🟠 experimental",
    "deprecated": "⚪ deprecated",
    "rejected": "🔴 rejected",
}


def _bullets(items: tuple[str, ...]) -> str:
    return "; ".join(items) if items else "—"


def generate() -> str:
    sys.path.insert(0, str(REPO_ROOT / "disbot"))
    import views.ux_lab  # noqa: F401, PLC0415 — registration side effect
    from utils.ux_patterns import REGISTRY, PatternCategory  # noqa: PLC0415

    lines: list[str] = [
        "# SuperBot UX pattern library",
        "",
        "> **Status:** `living-ledger` — **GENERATED, NOT SOURCE OF TRUTH.**",
        "> The registry in `disbot/utils/ux_patterns/` (populated by the",
        "> `views/ux_lab/` wings) is canonical; regenerate with",
        "> `python3.10 scripts/export_pattern_library.py` after changing it",
        "> (`tests/unit/docs/test_pattern_library_doc.py` pins the sync).",
        "> Browse everything live: `!uxlab`.",
        "",
        "## How to use this library",
        "",
        '- **Plans and PRs reference patterns by id** — "the apply flow uses',
        '  `settings_multi_select_preview`" replaces re-describing a layout.',
        "- **Adopting a pattern?** Add your view to its `adopted_by` tuple in",
        "  the wing module and regenerate — adoption is tracked, not assumed.",
        "- **Verdicts** (`uxlab-verdict: <id> — adopt|reject|tweak — note`)",
        "  from the ⚖️ Compare panel are routed here by the receiving session:",
        "  adopt → keep/extend; reject → status `rejected` (kept as a warning);",
        "  tweak → edit the exhibit, then re-judge.",
        "- **Don't invent a near-duplicate** of a listed pattern — extend the",
        "  exhibit instead (the whole point is one vocabulary).",
        "",
    ]
    for category in PatternCategory:
        specs = [s for s in REGISTRY.values() if s.category is category]
        if not specs:
            continue
        lines.append(f"## {_CATEGORY_TITLES[category.value]}")
        lines.append("")
        for s in specs:
            flags = []
            if s.uses_components_v2:
                flags.append("CV2")
            if s.requires_modal:
                flags.append("modal")
            if s.requires_pil:
                flags.append("PIL")
            flag_txt = f" · {'/'.join(flags)}" if flags else ""
            lines.append(
                f"### `{s.pattern_id}` — {s.title}",
            )
            lines.append("")
            lines.append(f"{_STATUS_BADGES[s.status.value]}{flag_txt}")
            lines.append("")
            lines.append(f"- **Use for:** {_bullets(s.recommended_for)}")
            if s.anti_patterns:
                lines.append(f"- **Avoid for:** {_bullets(s.anti_patterns)}")
            lines.append(f"- **Limits:** {_bullets(s.limits)}")
            lines.append(
                f"- **Adopted by:** {_bullets(s.adopted_by) if s.adopted_by else '— (not adopted yet)'}",
            )
            if s.notes:
                lines.append(f"- **Notes:** {s.notes}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str]) -> int:
    content = generate()
    if "--check" in argv:
        current = DOC_PATH.read_text() if DOC_PATH.exists() else ""
        if current != content:
            print(
                "pattern-library.md is stale — regenerate with "
                "python3.10 scripts/export_pattern_library.py",
            )
            return 1
        print("pattern-library.md is in sync ✓")
        return 0
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(content)
    print(f"wrote {DOC_PATH.relative_to(REPO_ROOT)} ({len(content)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
