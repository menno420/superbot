# /fleet-review

Run a complete **fleet night/status review** across every Project in the SuperBot
EAP fleet: what each lane shipped, whether it produced a valuable report (or hasn't
yet), health/blockers, the routine + model config, then synthesize an opinionated
report + a "manage-today" plan — documented and sent in chat.

> **Owner vocabulary:** when the owner says **"review"** (in the fleet-management
> context — not a code diff), they mean *this*. See `docs/owner/fleet-vocab.md`.
> For a code-diff review use `/code-review`; for a GitHub PR use `/review`.

## What this does

1. **Baseline** — read the fleet-manager roster (`menno420/fleet-manager` →
   `docs/roster.md`, machine-generated each manager wake) + `control/status.md`.
   That already covers every lane's freshness, orders, kit version, and wake
   config. Trust it as the backbone; verify anything load-bearing against the tree
   (Q-0120).
2. **Bring the fleet into scope** — `add_repo` each active lane repo (they're not
   in the default session scope). `get_file_contents` works post-add without a full
   clone; status files are huge, so read only heads + target reports/PRs.
3. **Fan out survey agents** (grouped, e.g. build / games / infra) — per lane:
   tonight's merged PRs + headlines, *did they add a valuable report?* (check
   `docs/findings`, `docs/retro`, dated docs — name it or say "none yet"), health
   + blockers + anything stuck, and the **model each session self-reports**
   (`📊 Model:` line) for the model-attribution check.
4. **Routine + model audit** — from the roster's trigger table: which routine drives
   which lane, its cron, and whether the **repo is attached** (the known failure:
   routines spawn without their repo, ~1/3 add_repo failures on gba). Flag any
   model mismatch (routine lists one family, sessions self-report another; owner
   default is opus-4.8).
5. **Synthesize** — an opinionated report: per-lane digest, what's strong / what's
   concerning, **fix-first priority list**, lessons, what-went-well-repeat, and a
   crisp **owner-action queue** (the human-only clicks: attach repos to routines,
   set models, publish/settings). Document it in `docs/eap/night-review-<date>.md`
   and send a well-organized version in chat with opinions + flags.

## Questions to ask the owner (only if they block; otherwise decide-and-flag)

- Scope: **all lanes** or a subset? (default: all active + archived-noted)
- Depth: quick status sweep, or deep report-quality assessment per lane? (default: deep)
- Any specific concern to center the review on tonight (a lane, a metric, an incident)?
- Where to document: `superbot docs/eap/` (default) or `fleet-manager docs/findings/`?

## Invocation

```
/fleet-review                 # full review, all active lanes, document + chat
/fleet-review <focus>         # center on a lane/topic, e.g. /fleet-review games
```

## Instructions for Claude

1. Read `fleet-manager/docs/roster.md` + `control/status.md` first (the aggregation).
2. `add_repo` the active lanes; use `get_file_contents` / `list_pull_requests` /
   `list_commits` (since ~last-evening UTC) — do NOT clone unless you need local ops,
   and do NOT dump whole `control/status.md` files (read heads / offsets).
3. Dispatch grouped `general-purpose` survey agents (3–4 lanes each) with the per-lane
   checklist in "What this does" §3; have each return a tight cited digest, not narration.
4. Do the routine + model audit from the roster trigger table + the agents' model
   self-reports.
5. Write `docs/eap/night-review-<date>.md` (per-lane table · strong/concerning ·
   fix-first · lessons · what-went-well · owner-action queue) and send the chat version.
6. End with the standard session close (`/session-close`) — born-red card, PR, merge.

**Honesty bar:** "no report yet" and "stuck on X" are the valuable findings — never
paper over a quiet or broken lane. Cite PRs/paths. Family-level model names only.
