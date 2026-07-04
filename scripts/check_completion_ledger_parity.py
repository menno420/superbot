#!/usr/bin/env python3.10
"""Registry↔completion-ledger parity guard — keep the completion ledger honest as the registry evolves.

The feature-completion ledger (`docs/planning/feature-completion/README.md`) certifies S1 bot
units "done-done", and the README is explicit that **the registry is the spine** — the immutable
list of units — while the ledger is a *living* index that merely references it:

    > Not a new source of truth for the unit list. The spine is the subsystem registry; this ledger
    > references it. (A registry↔ledger parity guard is a noted follow-up.)

This *is* that noted follow-up. Now that the ledger is at 36/36 ◐ assessed, the next thing that
will drift is the ledger itself: a new certifiable subsystem added to ``subsystem_registry.py``
will not automatically get a ledger row + cert, a retired/renamed registry key leaves an orphan
cert, and the documented exclusion set (routing-only hubs + knowledge domains) lives only in prose.
This guard asserts the registry ↔ ledger ↔ cert triangle is consistent, so any of those drifts
fails a check instead of sitting silently until someone re-reads the README.

The unit list is derived three ways and must agree:

1. **Registry** — top-level keys in ``disbot/utils/subsystem_registry.py`` ``SUBSYSTEMS``, minus the
   documented exclusion set (``EXCLUDED`` below — routing-only hubs / dev-internal + knowledge
   domains, mirroring the README "The unit = one registry entry" out-of-scope list). What remains is
   the set of **certifiable** units.
2. **Certs** — the ``**Unit:** `<key>` `` registry key each ``units/<file>.md`` certificate declares
   (a non-backticked Unit line marks a documented *non-registry* unit — the ``setup`` wizard — which
   must be on the ``NON_REGISTRY_UNITS`` allowlist).
3. **Ledger rows** — the ``[cert](units/<file>.md)`` link in each ledger table row.

Invariants (each is independent so one drift does not mask another):

* **A. registry == certs** — every certifiable registry key has exactly one cert declaring it, and
  every registry-backed cert maps to a live, non-excluded registry key (no missing cert, no orphan).
* **B. ledger == certs on disk** — every ledger row links a cert file that exists, every cert file is
  linked by exactly one ledger row (no unlinked cert, no dangling/duplicate link).
* **C. exclusion/allowlist hygiene** — every ``EXCLUDED`` key and every ``NON_REGISTRY_UNITS`` key is
  spelled correctly (the former is a live registry key; the latter has a cert + ledger row), and no
  excluded registry key accidentally carries a cert.

Reliability (Q-0105): **unverified** — confirm its flags against the actual ledger/registry over a
few sessions before trusting its green. If it false-positives on a legitimate ledger shape (or
misses a real parity break) over multiple sessions, **delete it** — it is a convenience guard for
the completion-arc bookkeeping, not load-bearing. Pure stdlib, like ``completion_scoreboard.py``.

Usage:
    python3.10 scripts/check_completion_ledger_parity.py            # advisory report (exit 0)
    python3.10 scripts/check_completion_ledger_parity.py --strict   # exit 1 on any parity break
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "disbot" / "utils" / "subsystem_registry.py"
LEDGER_DIR = REPO_ROOT / "docs" / "planning" / "feature-completion"
LEDGER = LEDGER_DIR / "README.md"
UNITS_DIR = LEDGER_DIR / "units"

# Registry keys that are NOT standalone certifiable units, mirroring the README
# "The unit = one registry entry" out-of-scope list. Keep this in sync with that prose:
#   - knowledge domains (their own sector/folio, not certified here)
#   - routing-only hubs / dev-internal subsystems (infrastructure, not a user-facing feature)
EXCLUDED = frozenset(
    {
        # knowledge domains
        "btd6",
        "project_moon",
        # routing-only hubs / dev-internal
        "games",
        "community",
        "server_management",
        "ux_lab",
        "general",
        "four_twenty",
    },
)

# Certifiable units that are deliberately NOT a registry subsystem (documented exceptions). Each
# must still have a cert + ledger row; the cert declares a non-backticked Unit name + a registry note.
NON_REGISTRY_UNITS = frozenset({"setup"})

# A ledger row's cert link, e.g. ``[cert](units/blackjack.md)``.
_CERT_LINK_RE = re.compile(r"\[cert\]\(units/([a-z0-9_]+)\.md\)")
# A top-level SUBSYSTEMS key, e.g. ``    "blackjack": {`` (4-space indent, opens a dict).
_REGISTRY_KEY_RE = re.compile(r'^    "([a-z0-9_]+)": \{', re.MULTILINE)
# A cert's declared registry key, e.g. ``> **Unit:** `casino` · ...`` (None when non-backticked).
_CERT_UNIT_RE = re.compile(r"\*\*Unit:\*\*\s*`([a-z0-9_]+)`")


def registry_keys() -> set[str]:
    """Top-level ``SUBSYSTEMS`` keys, scoped to the SUBSYSTEMS literal block."""
    text = REGISTRY.read_text(encoding="utf-8")
    start = text.find("SUBSYSTEMS: dict")
    if start == -1:
        raise SystemExit(
            "check_completion_ledger_parity: could not find the SUBSYSTEMS dict in "
            f"{REGISTRY.relative_to(REPO_ROOT)}",
        )
    return {m.group(1) for m in _REGISTRY_KEY_RE.finditer(text[start:])}


def ledger_links() -> list[str]:
    """Cert file stems referenced by ledger rows (order preserved, duplicates kept)."""
    return _CERT_LINK_RE.findall(LEDGER.read_text(encoding="utf-8"))


def cert_declared_key(cert: Path) -> str | None:
    """The registry key a cert declares via its ``**Unit:** `<key>` `` line, or None if non-backticked."""
    m = _CERT_UNIT_RE.search(cert.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def check() -> list[str]:
    """Gather the three views from disk and return parity violations (empty == clean)."""
    cert_files = sorted(p.stem for p in UNITS_DIR.glob("*.md"))
    declared: dict[str, str | None] = {
        stem: cert_declared_key(UNITS_DIR / f"{stem}.md") for stem in cert_files
    }
    return analyze(registry_keys(), declared, ledger_links())


def analyze(
    reg: set[str],
    declared: dict[str, str | None],
    links: list[str],
    units_on_disk: set[str] | None = None,
) -> list[str]:
    """Pure parity core — return human-readable violations (empty == clean).

    Inputs (all derivable from disk by :func:`check`, injectable here for tests):

    * ``reg`` — the set of live registry keys.
    * ``declared`` — ``{cert_file_stem: declared_registry_key_or_None}`` for every cert on disk.
    * ``links`` — the ordered list of cert file stems each ledger row links (duplicates kept).
    * ``units_on_disk`` — the set of cert file stems that exist (defaults to ``declared.keys()``;
      override only to model a ledger link to a missing file).
    """
    problems: list[str] = []

    certifiable = reg - EXCLUDED
    cert_files = sorted(declared)
    on_disk = set(declared) if units_on_disk is None else units_on_disk
    registry_backed = {k for k, v in declared.items() if v is not None}
    non_registry = set(cert_files) - registry_backed
    backed_keys = {
        declared[stem] for stem in registry_backed
    }  # the keys, not the file stems

    # --- A. registry == certs (registry-backed) ---
    for key in sorted(certifiable - backed_keys):
        problems.append(
            f"[A] registry key '{key}' is certifiable but no cert declares it "
            f"(add docs/planning/feature-completion/units/<file>.md with `**Unit:** `{key}``)",
        )
    for stem in sorted(s for s in registry_backed if declared[s] not in certifiable):
        key = declared[stem]
        why = "not a registry key" if key not in reg else "is on the EXCLUDED list"
        problems.append(
            f"[A] cert 'units/{stem}.md' declares Unit `{key}`, which {why} "
            f"(orphan cert — remove it, fix the Unit key, or update EXCLUDED/NON_REGISTRY_UNITS)",
        )

    # --- B. ledger rows == cert files on disk ---
    seen: dict[str, int] = {}
    for stem in links:
        seen[stem] = seen.get(stem, 0) + 1
        if stem not in on_disk:
            problems.append(
                f"[B] ledger links 'units/{stem}.md', which does not exist on disk",
            )
    for stem, n in sorted(seen.items()):
        if n > 1:
            problems.append(
                f"[B] ledger links 'units/{stem}.md' {n} times (expected exactly one row)",
            )
    for stem in cert_files:
        if stem not in seen:
            problems.append(
                f"[B] cert 'units/{stem}.md' exists but no ledger row links it (unlinked cert)",
            )

    # --- C. exclusion / allowlist hygiene ---
    for key in sorted(EXCLUDED - reg):
        problems.append(
            f"[C] EXCLUDED key '{key}' is not a live registry key (typo, or it was renamed/removed)",
        )
    for stem in sorted(non_registry):
        if stem not in NON_REGISTRY_UNITS:
            problems.append(
                f"[C] cert 'units/{stem}.md' has no `**Unit:** `key`` line and is not on "
                "NON_REGISTRY_UNITS (every cert must declare a registry key or be an allowlisted exception)",
            )
    for stem in sorted(NON_REGISTRY_UNITS):
        if stem not in on_disk:
            problems.append(
                f"[C] NON_REGISTRY_UNITS unit '{stem}' has no cert 'units/{stem}.md'",
            )
    for key in sorted(EXCLUDED & backed_keys):
        problems.append(
            f"[C] EXCLUDED key '{key}' carries a cert (an excluded routing-only/knowledge unit "
            "should not be certified — remove the cert or move the key out of EXCLUDED)",
        )

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Registry↔completion-ledger parity guard.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any parity break (default is advisory, exit 0).",
    )
    args = parser.parse_args(argv)

    problems = check()
    if not problems:
        print(
            "check_completion_ledger_parity: registry ↔ ledger ↔ certs are consistent.",
        )
        return 0

    print(
        f"check_completion_ledger_parity: {len(problems)} parity break(s):",
        file=sys.stderr,
    )
    for p in problems:
        print(f"  {p}", file=sys.stderr)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
