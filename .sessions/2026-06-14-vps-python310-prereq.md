# Session: record Python 3.10 VPS prerequisite (deadsnakes, verified)

> **Status:** `in-progress` — recording the verified VPS python3.10 prereq; flip to complete last.

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** docs (ops record, owner-verified)

## What this session did

The owner installed Python 3.10 on the Hermes VPS (Ubuntu 24.04 noble) via the deadsnakes PPA —
verified live: `python3.10 --version` → 3.10.20, `python3.10 scripts/hermes/build_skills.py --check`
passes — keeping the system `python3` at 3.11. Recorded the now-verified setup step in
`docs/operations/hermes-control-plane.md` § VPS → new **Python toolchain** subsection (the exact
deadsnakes commands + the note that PR #869 de-pinned the helpers, so 3.10 is for doc-command parity,
not a hard requirement). This survives a VPS rebuild instead of living only in a Telegram screenshot.

`check_docs --strict` ✓. Docs only.
