#!/usr/bin/env python3.10
"""Session merge-gate — hold a PR red until its session card says it's done.

The merge race this closes (owner directive Q-0133, 2026-06-14)
--------------------------------------------------------------
Native auto-merge (Q-0123) merges a `claude/*` PR the instant the required
`Code Quality` check goes green. A session that pushes its code first and its
session-close docs (the ledger entry, the `.sessions/` log) second can therefore
merge **before** those docs are pushed — the #843 case: the PR merged without its
ledger entry, leaving a stranded follow-up.

The fix is the owner's: every session declares itself up-front in a single
per-session file that is *both* the start-declaration ("what is about to happen",
visible to parallel/next sessions on the open PR) **and** the end-record ("what
has happened"). That file is the existing `.sessions/<date>-<slug>.md` log, and
its `> **Status:**` badge gates the merge:

* Created in the **first** commit with a HOLD status (`in-progress`) → the PR is
  **born red**, so auto-merge arms but cannot fire (no race window — the gate is
  red from commit 1, not added later).
* Flipped to a READY status (`complete`) as the deliberate **final** step →
  `Code Quality` goes green → auto-merge fires.

Engage-when-present (the safe default Q-0133 chose over airtight): the gate fails
**only** when the PR touches a session card whose status is a hold/unknown token. A
PR that touches **no** session card behaves exactly as before (merges on green),
so workflow-authored PRs (btd6-data-refresh) and any routine that hasn't created a
card are never deadlocked. Creating the card is mandatory **by CLAUDE.md rule** +
the Stop-hook / `/session-close` reminder, not by hard CI enforcement.

Added **or modified** cards (`git diff --diff-filter=AM`) are inspected by the merge
gate (BUG-0027, 2026-06-28). The original gate looked at **added** cards only
(`--diff-filter=A`), which had a silent hole: if a session reused an existing
`.sessions/` slug (a same-day name collision), its born-red card landed as a
*modification* (`M`), not an addition (`A`), so the gate never engaged and the
partial PR auto-merged (PR #1523 — and the collision clobbered the prior session's
log). The merge gate now also catches a modified card left in a hold status. A
reconciliation PR that re-badges an *old* log to a terminal token
(`historical`/`archived`/…) is still never held — those statuses are in
``_TERMINAL_OK_STATUSES``. (The Codex ``--require-ready-card`` trigger keeps its
added-only semantics — it asks "did this PR *add* a card that just went ready?".)

Pure stdlib (runs in CI's `code-quality` job before any setup) and unit-tested.

Usage:
    python3.10 scripts/check_session_gate.py                 # auto (vs origin/main)
    python3.10 scripts/check_session_gate.py --base SHA --head SHA   # CI
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# READY = the current session declared itself done → the PR may merge. Anything else
# on a touched card holds it red, so a typo'd or still-in-progress status fails safe
# (held) rather than merging early.
_READY_STATUSES = {"complete", "done", "ready", "final", "merged", "shipped"}

# TERMINAL_OK = a re-badged *old* log (a reconciliation pass flips a finished session
# card to one of these). These are never a current in-flight session, so they must
# never hold a merge — even though they are not "ready" in the active-session sense.
# This is what keeps the merge gate's added-OR-modified scan (BUG-0027) from holding a
# reconciliation PR that re-badges an old `.sessions/` log.
_TERMINAL_OK_STATUSES = {"historical", "archived", "superseded", "deprecated"}

# A touched session card holds the merge unless its status is merge-OK: the current
# session is done (_READY) **or** it is an old re-badged log (_TERMINAL_OK).
_MERGE_OK_STATUSES = _READY_STATUSES | _TERMINAL_OK_STATUSES

# Terminator is an em/en-dash or pipe or end-of-line — NOT a plain hyphen, which is
# part of word-tokens like `in-progress`.
_STATUS_RE = re.compile(r"\*\*Status:\*\*\s*`?\s*([A-Za-z0-9 _-]+?)\s*`?\s*(?:[—–|]|$)")

# --- Telemetry-append guard (Q-0194 friction→guard; fleet-review 2026-07-09 #3) --
# Provenance + kill-switch (Q-0105): added 2026-07-09 because the telemetry-append
# rule in `telemetry/README.md` ("append your session's row at close") was
# exhortative only and already leaking — 3 rows in `telemetry/model-usage.jsonl`
# vs ≥4 sessions carded after the lane shipped (#1884, 2026-07-09 06:41). Enforce,
# don't exhort (Q-0132): a PR that ADDS a `.sessions/` card dated on/after the
# floor below must also append ≥1 line to the telemetry feed in the same PR.
# The date floor keeps the 866 pre-existing cards (and reconciliation re-badges,
# which are modifications, not additions) from going retroactively red.
# UNVERIFIED: confirm its output against ground truth a few times across sessions
# before trusting it. DELETE THIS GUARD (these constants, `_card_date`,
# `telemetry_required_cards`, `telemetry_rows_added`, the telemetry block in
# `main()`, and its tests) if it proves unreliable over multiple sessions.
_TELEMETRY_FILE = "telemetry/model-usage.jsonl"
_TELEMETRY_ENFORCE_SINCE = "2026-07-09"  # ISO date — string compare is date compare
_CARD_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def parse_status(text: str) -> str | None:
    """Return the lowercased `> **Status:** `<token>`` badge token, or None."""
    for line in text.splitlines():
        if "**Status:**" in line:
            m = _STATUS_RE.search(line)
            if m:
                return m.group(1).strip().lower()
    return None


def _diff_session_cards(
    base: str | None,
    head: str | None,
    diff_filter: str,
) -> list[Path]:
    """`.sessions/*.md` files matching ``diff_filter`` between base and head.

    ``diff_filter`` is a git ``--diff-filter`` value: ``"A"`` (added only — the Codex
    trigger's question) or ``"AM"`` (added or modified — the merge gate's question,
    after BUG-0027). README excluded.

    CI passes the PR base/head SHAs; locally we diff against ``origin/main`` (the
    merge base of this branch). Returns [] on any git failure — a gate that cannot
    read git must not block (fail-open here; the rule + reminder are the backstop).
    """
    if base and head:
        # CI: the card is committed in the PR — the committed diff is authoritative.
        cmds = [
            [
                "git",
                "diff",
                "--name-only",
                f"--diff-filter={diff_filter}",
                base,
                head,
                "--",
                ".sessions/",
            ],
        ]
    else:
        # Local: include not-yet-committed cards (staged or untracked) so a pre-push
        # run reflects what the PR will contain.
        cmds = [
            [
                "git",
                "diff",
                "--name-only",
                f"--diff-filter={diff_filter}",
                "origin/main...HEAD",
                "--",
                ".sessions/",
            ],
            ["git", "ls-files", "--others", "--exclude-standard", "--", ".sessions/"],
        ]
    found: set[str] = set()
    for cmd in cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        except OSError:
            continue
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith(".sessions/") and line.endswith(".md"):
                if Path(line).name != "README.md":
                    found.add(line)
    return [REPO_ROOT / p for p in sorted(found)]


def added_session_cards(base: str | None, head: str | None) -> list[Path]:
    """`.sessions/*.md` files **added** between base and head (README excluded).

    The Codex ``--require-ready-card`` trigger's view: "did this PR *add* a card?".
    """
    return _diff_session_cards(base, head, "A")


def gate_session_cards(base: str | None, head: str | None) -> list[Path]:
    """`.sessions/*.md` files **added or modified** between base and head.

    The merge gate's view (BUG-0027): a born-red card that collided with an existing
    slug lands as a modification, so the gate must see modifications too — otherwise
    it fails open and a partial PR auto-merges (PR #1523).
    """
    return _diff_session_cards(base, head, "AM")


def _card_date(card: Path) -> str | None:
    """ISO date from a `.sessions/YYYY-MM-DD-<slug>.md` filename, or None."""
    m = _CARD_DATE_RE.match(card.name)
    return m.group(1) if m else None


def telemetry_required_cards(cards: list[Path]) -> list[Path]:
    """Cards whose filename date is on/after the telemetry enforcement floor.

    Undated filenames are skipped (fail-open — the born-red status gate still
    applies to them; this guard only ever *adds* a requirement, never blocks a
    card it cannot date).
    """
    required: list[Path] = []
    for card in cards:
        date = _card_date(card)
        if date is not None and date >= _TELEMETRY_ENFORCE_SINCE:
            required.append(card)
    return required


def telemetry_rows_added(base: str | None, head: str | None) -> bool | None:
    """Did the diff append ≥1 line to ``telemetry/model-usage.jsonl``?

    Returns True (rows added), False (no rows added), or None when git could not
    answer — the same fail-open bias as `_diff_session_cards` (a gate that cannot
    read git must not block; the README rule + session enders are the backstop).

    CI diffs base..head; locally we diff origin/main...HEAD **plus** the working
    tree vs HEAD, so a pre-push run sees a not-yet-committed row.
    """
    if base and head:
        cmds = [["git", "diff", "--numstat", base, head, "--", _TELEMETRY_FILE]]
    else:
        cmds = [
            ["git", "diff", "--numstat", "origin/main...HEAD", "--", _TELEMETRY_FILE],
            ["git", "diff", "--numstat", "HEAD", "--", _TELEMETRY_FILE],
        ]
    answered = False
    for cmd in cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
        except OSError:
            continue
        if result.returncode != 0:
            continue
        answered = True
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 3 and parts[2].strip() == _TELEMETRY_FILE:
                try:
                    if int(parts[0]) > 0:
                        return True
                except ValueError:  # binary diff marker "-"
                    continue
    return False if answered else None


def _cards_not_in(
    cards: list[Path],
    ok_statuses: set[str],
) -> list[tuple[Path, str]]:
    """Return (card, status) for each card whose status is NOT in ``ok_statuses``."""
    held: list[tuple[Path, str]] = []
    for card in cards:
        try:
            text = card.read_text(encoding="utf-8")
        except OSError:
            continue
        status = parse_status(text) or "(no Status badge)"
        if status not in ok_statuses:
            held.append((card, status))
    return held


def held_cards(cards: list[Path]) -> list[tuple[Path, str]]:
    """Return (card, status) for each card NOT in a READY status (Codex trigger view)."""
    return _cards_not_in(cards, _READY_STATUSES)


def merge_blocking_cards(cards: list[Path]) -> list[tuple[Path, str]]:
    """Return (card, status) for each card that holds the merge.

    Merge-OK = the active session is done (_READY) **or** the card is a re-badged old
    log (_TERMINAL_OK). Everything else (in-progress, missing/typo'd badge) holds —
    the fail-safe bias Q-0133 chose.
    """
    return _cards_not_in(cards, _MERGE_OK_STATUSES)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot session merge-gate.")
    parser.add_argument("--base", help="base commit SHA (CI: PR base)")
    parser.add_argument("--head", help="head commit SHA (CI: PR head)")
    parser.add_argument(
        "--require-ready-card",
        action="store_true",
        help=(
            "Codex-trigger mode: exit 0 ONLY when the PR adds at least one session "
            "card AND every added card is in a ready status (the 'card just flipped "
            "to complete' signal). A PR with no card, or any held card, exits 1. Used "
            "by codex-final-review.yml to fire `@codex review` on the final head."
        ),
    )
    args = parser.parse_args(argv)

    if args.require_ready_card:
        # Codex trigger: only ADDED cards count — "did this PR add a card that just
        # went ready?". Modifications (e.g. a reconciliation re-badge) never trigger.
        cards = added_session_cards(args.base, args.head)
        if not cards:
            print(
                "check_session_gate: no session card — no Codex final-review trigger.",
            )
            return 1
        if held_cards(cards):
            print("check_session_gate: session card not ready — no Codex trigger yet.")
            return 1
        names = ", ".join(c.name for c in cards)
        print(
            f"check_session_gate: session card ready — Codex final-review trigger ✓ ({names})",
        )
        return 0

    # Merge gate: ADDED **or MODIFIED** cards count (BUG-0027) — a born-red card that
    # collided with an existing slug lands as a modification, and must still hold.
    cards = gate_session_cards(args.base, args.head)
    if not cards:
        print(
            "check_session_gate: no new/modified session card in this PR — not gated. ✓",
        )
        return 0

    added_cards = added_session_cards(args.base, args.head)

    # Telemetry-append guard (Q-0194; provenance header above): a PR that ADDS a
    # card dated >= the floor must also append a telemetry row in the same diff.
    telemetry_held = False
    required = telemetry_required_cards(added_cards)
    if required and telemetry_rows_added(args.base, args.head) is False:
        telemetry_held = True

    held = merge_blocking_cards(cards)
    if not held and not telemetry_held:
        names = ", ".join(c.name for c in cards)
        print(
            f"check_session_gate: session card(s) ready — merge unblocked ✓ ({names})",
        )
        return 0

    if telemetry_held:
        names = ", ".join(c.name for c in required)
        print(
            "check_session_gate: MERGE HELD — telemetry row missing (Q-0194 guard).\n"
            f"  This PR adds session card(s) dated >= {_TELEMETRY_ENFORCE_SINCE} "
            f"({names})\n"
            f"  but appends no line to {_TELEMETRY_FILE}.\n"
            "  Fix: append your session's one-line JSONL row (schema + field rules: "
            "telemetry/README.md;\n"
            "  copy the shape of the existing rows) to "
            f"{_TELEMETRY_FILE} in this same PR.",
        )
        if not held:
            return 1

    added = {p.resolve() for p in added_cards}
    print("check_session_gate: MERGE HELD — session card not marked ready.")
    for card, status in held:
        rel = card.relative_to(REPO_ROOT) if card.is_relative_to(REPO_ROOT) else card
        print(f"  - {rel}: Status `{status}` (held)")
        if card.resolve() not in added:
            print(
                "    ⚠ this card was MODIFIED, not added — if you reused an existing "
                "session slug, rename your card to a unique slug (BUG-0027 / the #1523 "
                "collision that clobbered a prior log).",
            )
    ready = ", ".join(sorted(_READY_STATUSES))
    print(
        "\nThis is the born-red session gate (Q-0133): flip the card's "
        "`> **Status:**` badge to a ready token to merge.\n"
        f"  Ready tokens: {ready}\n"
        "  (Do this as the deliberate final step, after the session-close docs "
        "are written — so auto-merge fires on a complete PR, not a partial one.)",
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
