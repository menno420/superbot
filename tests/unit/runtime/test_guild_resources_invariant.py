"""INV gate: no raw guild-resource lookups outside core.runtime.guild_resources.

Phase D enforces a single canonical site for all guild member / role /
channel resolution.  Once the migration is complete this test guards
the invariant so a new ``guild.get_member`` / ``discord.utils.get(
guild.roles, ...)`` etc. can't sneak back in.

The gate scans ``disbot/**/*.py`` (excluding tests + the allow-list
below) for the patterns the resolver canonicalises.  If any new
pattern lands, fix it by calling the matching helper in
``core.runtime.guild_resources`` (re-exported as ``resources``).

Allow-list rationale:

  guild_resources.py          The resolver IS the canonical site.
  utils/channels.py           Channel-creation helper; uses
                              ``discord.utils.get`` internally to
                              check existence before create.
                              Migrating it would introduce an
                              upward dep on core/runtime that the
                              creation primitive doesn't need.
  rps_tournament/_bot_matches.py
                              Uses ``guild.get_member_named`` — a
                              name-based lookup distinct from the
                              id-based ``get_member``.  No equivalent
                              in the resolver yet (resolve_member
                              takes an id, not a username).  A
                              future ``resolve_member_by_name`` could
                              absorb it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_ROOT = REPO_ROOT / "disbot"

ALLOW_LIST = {
    "disbot/core/runtime/guild_resources.py",
    "disbot/utils/channels.py",
    "disbot/cogs/rps_tournament/_bot_matches.py",
}

# Each pattern is (compiled-regex, human-readable label).  The regex
# is matched line-by-line so the line number can be reported.
PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bguild\.get_member\("),
        "guild.get_member — use resources.resolve_member",
    ),
    (
        re.compile(r"\bguild\.get_role\("),
        "guild.get_role — use resources.resolve_role",
    ),
    (
        re.compile(r"\bguild\.get_channel\(\s*int\("),
        "guild.get_channel(int(...)) — use resources.resolve_channel",
    ),
    (
        re.compile(r"\bbot\.get_channel\(\s*int\("),
        "bot.get_channel(int(...)) — use resources.resolve_settings_channel",
    ),
    (
        re.compile(r"discord\.utils\.get\([^)]*\.roles\s*,"),
        "discord.utils.get(... .roles, ...) — use resources.resolve_role(name=...)",
    ),
    (
        re.compile(r"discord\.utils\.get\([^)]*\.categories\s*,"),
        "discord.utils.get(... .categories, ...) — use resources.resolve_channel(kind='category')",
    ),
    (
        re.compile(r"discord\.utils\.get\([^)]*\.text_channels\s*,"),
        "discord.utils.get(... .text_channels, ...) — use resources.resolve_channel(name=...)",
    ),
    (
        re.compile(r"discord\.utils\.get\([^)]*\.voice_channels\s*,"),
        "discord.utils.get(... .voice_channels, ...) — use resources.resolve_channel(kind='voice')",
    ),
]


def _iter_py_files():
    for path in SCAN_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOW_LIST:
            continue
        yield path, rel


def test_no_raw_guild_lookups_outside_resolver() -> None:
    violations: list[str] = []
    for path, rel in _iter_py_files():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, label in PATTERNS:
                if pattern.search(line):
                    violations.append(f"{rel}:{lineno}: {label}\n    > {line.strip()}")
    assert not violations, (
        "raw guild-resource lookups found outside core.runtime.guild_resources:\n\n"
        + "\n\n".join(violations)
    )
