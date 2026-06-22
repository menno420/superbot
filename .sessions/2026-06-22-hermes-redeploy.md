# 2026-06-22 — Hermes one-command + auto redeploy (no more Terminus)

> **Status:** `complete`

Owner-directed follow-on to the Q-0197 session. The owner's pain: applying a merged Hermes
change (SOUL.md / skills) meant hand-running git reset + install-soul + install-skills + a
gateway restart in Terminus every time — and the gateway can't restart itself from inside its
own process. Owner: "it would be easier if I didn't have to do it on terminus every time …
I wouldn't even need terminus anymore then."

## What this ships
- `scripts/hermes/redeploy.sh` — one command: sync mirror → install SOUL + skills → **detached**
  gateway restart (`systemd-run --on-active=3s`, so it's safe even when Hermes runs it itself).
  `--if-changed` / `--dry-run` flags; auto-detects user-vs-system gateway service to avoid sudo.
- `scripts/hermes/systemd/hermes-redeploy.{service,timer}` — user-level timer templates that run
  `redeploy.sh --if-changed` every ~10 min → **merge=deploy for Hermes** (Railway-worker analogue).
- `docs/operations/hermes-redeploy.md` — one-time install + both modes + sudo/kill-switch notes;
  linked from the terminal cheatsheet.
- Folded in the lingering **Q-0197 leftover**: `hermes-operating-prompt.md` still told Hermes it had
  the review-merge merge gate (lines 53/129/145) — removed.

## Verification
- `bash -n scripts/hermes/redeploy.sh` ✓ (syntax) · `install-soul.sh --dry-run` ✓ (SOUL still
  extracts, 0 review-merge mentions, 7142B)
- `check_docs.py --strict` ✓ (new doc reachable via the cheatsheet) · `check_quality.py --check-only` ✓
- Can't exercise systemd/the restart in CI (no VPS) — marked UNVERIFIED in the script header + doc;
  confirm on first VPS run via `journalctl --user -u hermes-redeploy.service`.

## ⚑ Self-initiated
The redeploy tooling is owner-requested (the Terminus pain point) — built directly per the go-ahead.
Not flagged as self-initiated feature work.

## 💡 Session idea
Same merge=deploy timer pattern could cover the **Hermes session-reset** and any future VPS-side
config: a single `~/.config/systemd/user/` "Hermes ops" bundle installer (`install-vps-units.sh`)
that drops session-reset + redeploy units in one step, so the VPS one-time setup is itself one
command. Worth an idea file if more VPS units appear.

## ⟲ Previous-session review
The Q-0197 session (this same chat) retired the label/rule well but **missed the
`hermes-operating-prompt.md` review-merge references** — caught only because the owner asked about
Hermes capabilities and I re-read the prompt. Improvement surfaced + applied: when retiring a
concept, grep the *operating prompt / SOUL source* explicitly, not just the skill docs — the SOUL
is the live prompt and drifts silently (it's only ~reachable via install-soul, not the doc-link
graph). Folded that fix into this PR.

## Doc audit
New doc linked from the cheatsheet; `check_docs --strict` green. No ledger entry needed until merge
(the reconciliation pass records it).
