# 2026-06-16 — install-skills.sh staleness guard (stale-skill root cause)

> **Status:** `in-progress` — third small PR this session. Bash-only; one push.
> Session enders (Q-0089 idea, Q-0102 review, Q-0104 audit) were satisfied in this session's first
> card (`2026-06-16-model-comparison-gpt5mini.md`, merged in #978) — not repeated here.

## Why

After the owner switched Hermes to `gpt-5-mini` (the 500K-TPM fix — confirmed working), the morning
briefing + idea spotlight ran cleanly, **but** the idea-spotlight skill reported
`scripts/hermes/idea_spotlight.py` "missing in this checkout" and fell back to manually picking an
idea. Diagnosis: the script **is** in `main` (added #959, `07ed7de`) and the skill self-syncs the
checkout in its step 1 — so the real cause is the **installed SKILL.md on the VPS is stale**
(installed from a clone that predated #959/#971). Root cause one level up: `install-skills.sh` copies
whatever is checked out with **no staleness check**, so installing from a behind clone silently ships
old skills (and their helper scripts can be absent).

## Fix (root cause, contained, bash-only)

`scripts/hermes/install-skills.sh`:
- **`--pull`** — syncs the checkout to `origin/main` (`git fetch + checkout -B main origin/main`, the
  same sync the skills' own step 1 uses) **before** installing, so skills + helper scripts always match.
- **Default best-effort warning** — does a quiet `git fetch` and warns loudly if the checkout is N
  commits behind `origin/main` ("you may install STALE skills — re-run with --pull"). Non-destructive.
- Header documents the staleness guard + cites the 2026-06-16 incident.

`bash -n` ✓ · dry-run live-verified the warning fires (correctly caught my own 2-behind checkout) and
that `idea-spotlight` is a committed skill artifact.

## Owner's immediate unblock (no repo change needed)

On the VPS as `hermes`: `cd ~/repos/superbot && bash scripts/hermes/install-skills.sh --pull && sudo
systemctl restart hermes-gateway`, then re-run the spotlight — the selector will be present.
