#!/usr/bin/env python3
"""Generate installable Hermes ``SKILL.md`` files from the repo's skill docs.

The human-readable source of truth for each Hermes skill is its doc under
``docs/operations/hermes-skills/<name>.md`` (prose + a ``## Prompt`` fenced
block). Hermes itself, however, loads skills as ``SKILL.md`` files carrying a
YAML frontmatter header (``name``/``description``/``version``/``author``/
``license`` + ``metadata.hermes`` extras) — see
https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills/.

This builder bridges the two: it reads each skill doc, lifts the prompt body
and purpose line, and emits a frontmatter-wrapped ``SKILL.md`` under
``scripts/hermes/skills/<name>/`` ready to copy onto the VPS with
``scripts/hermes/install-skills.sh``.

It mirrors the ``tools/agent_context`` pattern: **edit the doc, never the
generated file** — every emitted ``SKILL.md`` carries a ``GENERATED`` marker.

Pure stdlib (no PyYAML) so the freshness test runs in CI without installing
anything — same discipline as ``scripts/check_docs.py``.

Usage:
    python3.10 scripts/hermes/build_skills.py            # (re)generate artifacts
    python3.10 scripts/hermes/build_skills.py --check    # exit 1 if stale (CI)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DOCS_DIR = REPO_ROOT / "docs" / "operations" / "hermes-skills"
SKILL_OUT_DIR = REPO_ROOT / "scripts" / "hermes" / "skills"

GENERATED_MARKER = "GENERATED — DO NOT EDIT"

# Name token in the doc H1: `# Skill: \`superbot-foo\``.
_NAME_RE = re.compile(r"`(superbot-[a-z0-9-]+)`")


@dataclass(frozen=True)
class SkillExtras:
    """Frontmatter fields the doc prose does not carry, keyed by file stem.

    Kept here (not in the doc) so the doc stays clean prose; the substantive,
    drift-prone content — the prompt — lives only in the doc.
    """

    tags: list[str]
    # Optional self-scheduling blueprint: (cron, human task line). Hermes runs
    # the skill on this schedule and delivers to the home channel. Closes the
    # "daily health digest" loop with no extra cron wiring on the VPS.
    schedule: tuple[str, str] | None = None
    related: list[str] = field(default_factory=list)


# Stem -> extras. Add an entry here when a new skill doc is added.
EXTRAS: dict[str, SkillExtras] = {
    "session-brief": SkillExtras(tags=["Orientation", "SuperBot", "Planning"]),
    "repo-health": SkillExtras(
        tags=["Monitoring", "SuperBot", "Health"],
        schedule=(
            "0 8 * * *",
            "Run a SuperBot repo health check and deliver the traffic-light report.",
        ),
    ),
    "ideas-triage": SkillExtras(tags=["Planning", "SuperBot", "Ideas"]),
    "prompt-builder": SkillExtras(tags=["Planning", "SuperBot", "PromptEngineering"]),
    "open-questions": SkillExtras(tags=["Planning", "SuperBot", "Decisions"]),
    "btd6-status": SkillExtras(tags=["Monitoring", "SuperBot", "BTD6"]),
    "log-triage": SkillExtras(
        tags=["Monitoring", "SuperBot", "Diagnostics"],
        related=["superbot-repo-health"],
    ),
    "review": SkillExtras(
        tags=["Review", "SuperBot", "Quality"],
        related=["superbot-session-brief"],
    ),
    "review-merge": SkillExtras(
        tags=["Review", "SuperBot", "MergeGate"],
        related=["superbot-review"],
        schedule=(
            "30 7 * * *",
            "Review the needs-hermes-review PR queue and report verdicts "
            "(merge sound + green PRs when calibrated; otherwise escalate).",
        ),
    ),
    "dispatch": SkillExtras(
        tags=["Automation", "SuperBot", "Dispatch"],
        related=["superbot-prompt-builder", "superbot-review"],
    ),
    "skill-author": SkillExtras(
        tags=["Meta", "SuperBot", "SelfExtension"],
        related=["superbot-prompt-builder"],
    ),
}

VERSION = "1.0.0"
AUTHOR = "SuperBot agents"
LICENSE = "MIT"


@dataclass(frozen=True)
class Skill:
    stem: str
    name: str
    description: str
    prompt: str


def _extract_purpose(lines: list[str]) -> str:
    """Lift the ``**Purpose:**`` blurb (may wrap across lines) into one line."""
    collected: list[str] = []
    capturing = False
    for line in lines:
        if "**Purpose:**" in line:
            capturing = True
            collected.append(line.split("**Purpose:**", 1)[1].strip())
            continue
        if capturing:
            if not line.strip():
                break
            collected.append(line.strip())
    return " ".join(collected).strip()


def _extract_prompt(lines: list[str]) -> str:
    """Return the first fenced block following the ``## Prompt`` heading."""
    in_prompt_section = False
    in_fence = False
    body: list[str] = []
    for line in lines:
        if line.strip() == "## Prompt":
            in_prompt_section = True
            continue
        if not in_prompt_section:
            continue
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```"):
                in_fence = True
            continue
        if stripped == "```":
            break
        body.append(line)
    return "\n".join(body).strip()


def parse_skill_doc(path: Path) -> Skill:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    stem = path.stem

    name_match = _NAME_RE.search(lines[0] if lines else "")
    name = name_match.group(1) if name_match else f"superbot-{stem}"

    description = _extract_purpose(lines)
    if not description:
        raise ValueError(f"{path.name}: no **Purpose:** line found")

    prompt = _extract_prompt(lines)
    if not prompt:
        raise ValueError(f"{path.name}: no ## Prompt fenced block found")

    return Skill(stem=stem, name=name, description=description, prompt=prompt)


def _yaml_str(value: str) -> str:
    """Double-quote a scalar for YAML, escaping quotes/backslashes."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_skill_md(skill: Skill) -> str:
    extras = EXTRAS.get(skill.stem, SkillExtras(tags=["SuperBot"]))
    tags = ", ".join(extras.tags)

    fm: list[str] = [
        "---",
        f"name: {skill.name}",
        f"description: {_yaml_str(skill.description)}",
        f"version: {VERSION}",
        f"author: {_yaml_str(AUTHOR)}",
        f"license: {LICENSE}",
        "platforms: [linux, macos]",
        "metadata:",
        "  hermes:",
        f"    tags: [{tags}]",
    ]
    if extras.related:
        related = ", ".join(extras.related)
        fm.append(f"    related_skills: [{related}]")
    if extras.schedule is not None:
        cron, task = extras.schedule
        fm += [
            "    blueprint:",
            f"      schedule: {_yaml_str(cron)}",
            "      deliver: origin",
            f"      prompt: {_yaml_str(task)}",
            "      no_agent: false",
        ]
    fm.append("---")

    header = (
        f"<!-- {GENERATED_MARKER}. Source of truth: "
        f"docs/operations/hermes-skills/{skill.stem}.md. "
        "Regenerate with scripts/hermes/build_skills.py. -->"
    )
    return "\n".join(fm) + "\n\n" + header + "\n\n" + skill.prompt + "\n"


def build_all() -> dict[Path, str]:
    """Return ``{output_path: rendered_content}`` for every skill doc."""
    out: dict[Path, str] = {}
    for doc in sorted(SKILL_DOCS_DIR.glob("*.md")):
        if doc.name == "README.md":
            continue
        skill = parse_skill_doc(doc)
        out_path = SKILL_OUT_DIR / skill.stem / "SKILL.md"
        out[out_path] = render_skill_md(skill)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any generated SKILL.md is missing or stale (CI gate)",
    )
    args = parser.parse_args(argv)

    rendered = build_all()

    if args.check:
        stale: list[Path] = []
        for path, content in rendered.items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("build_skills --check: stale or missing generated skill(s):")
            for p in sorted(stale):
                print(f"  {p.relative_to(REPO_ROOT)}")
            print("\nRun: python3.10 scripts/hermes/build_skills.py")
            return 1
        print(f"build_skills --check: {len(rendered)} skill(s) up to date ✓")
        return 0

    for path, content in rendered.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"build_skills: wrote {len(rendered)} skill(s) to {SKILL_OUT_DIR.relative_to(REPO_ROOT)}/")
    for path in sorted(rendered):
        print(f"  {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
