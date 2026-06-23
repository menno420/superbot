# 2026-06-23 — Cleanup panel: hint pointing at Command Access delete toggle

> **Status:** `in-progress` — owner-directed (owner accepted the follow-up I proposed). Add a one-line
> legibility tip to the Cleanup Policies diagnostics embed so the cleanup-level vs Command-Access-delete
> distinction is clear at the point of confusion. Open PR born-red per Q-0133; flip to `complete` last.

> **Run type:** `manual · owner-directed`

## What I'm about to do

This session's root finding (#1359) was that a cleanup *level* (Off/Light/Standard/Strict) only deletes
**blocked** commands, while "delete any command in a no-command channel" lives under **Command Access →
🗑️ Delete blocked commands**. That distinction tripped the owner up ("still hasn't changed much"). Add a
single `ℹ️ Tip` field to the Cleanup Policies diagnostics embed (both the empty and populated paths)
pointing operators at the Command Access toggle. View-only, one field + a test.

## What shipped

_(filled in at close)_
