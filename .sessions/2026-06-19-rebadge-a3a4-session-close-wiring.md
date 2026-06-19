# 2026-06-19 — Rebadge A3/A4 `historical` + wire drift check into /session-close

> **Status:** `complete`

Owner-directed (router **Q-0181**) follow-up: apply the fix-on-sight the new drift check surfaced, and
close the session-close loop so every future session does it automatically.

## What was done
- Rebadged **`games-economy-faucet-sink-diagnostic`** (A3) and **`p0-2-content-free-media-diagnostics`** (A4)
  `plan` → `historical`. Both verified present + wired + **tested** and shipped in **#1044** — not trusting
  the heuristic: confirmed each deliverable (DB fn, service, `!platform` subcommand, tests) in source first.
  Added SHIPPED banners + moved their rows Active → Historical in `docs/planning/README.md`.
- Wired **`scripts/check_plan_code_drift.py`** into **`/session-close` Step 4** (quality gate) + a rebadge
  instruction in the doc-audit prose — every session now surfaces its own rebadge candidates (the
  session-close half of Q-0181, applied).
- Updated router **Q-0181**: session-close wiring applied; the diff-aware Stop-hook stays *proposed*
  (it edits `settings.json`, so it awaits an explicit greenlight + a watched first fire).

## Decisions recorded
Q-0181 session-close wiring **applied** (owner-directed in-session 2026-06-19).

## Left open / next session
The **diff-aware Stop-hook** (Q-0181 part 2) — awaits owner greenlight + a watched first fire.

## 💡 Session idea
Extend the drift check with the **reverse direction**: flag a `historical`-badged plan whose
implementation has since been **deleted** from `disbot/` (a shipped feature later removed) — the inverse
drift class, equally misleading to the next agent.

## ⟲ Previous-session review
The #1135 session built the drift check well but deliberately left the rebadges + wiring as a follow-up
(correct — separate, lower-risk PR). This session applied them. Improvement surfaced: once a few sessions
confirm the check's STRONG tier is false-positive-free, graduate it to `--strict` in `/session-close` so a
shipped-but-`plan` doc *blocks* close instead of merely warning.
