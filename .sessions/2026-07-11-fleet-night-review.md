# 2026-07-11 — fleet night review + routine/model fix plan + owner vocab & skills

> **Status:** `complete`
<!-- born-red flow (Q-0133): in-progress while open; flip to complete as the final step. -->

📊 Model: Claude Opus 4.8 · owner-directed fleet review + docs session

## Declared at open (born-red)

Owner asked (2026-07-11, live) for: a **complete fleet night review** across all
Projects (who shipped valuable reports, who hasn't, what's stuck) — documented + sent
in chat with opinions/flags; the repo **prepared to manage the fleet today** (fix-first
priorities, lessons, what-went-well); the **routine findings** turned into a plan
(routines spawn without their repo — gba ~1/3 add_repo failures; owner can edit routines
to attach repos + set model; model mismatch: some routines run sonnet-5 while listed as
fable-5/opus-4.8, owner default opus-4.8); and a **keyword/shorthand → skills** system so
the owner can talk with fewer words.

This session:
1. `.claude/skills/fleet-review/SKILL.md` — the `/fleet-review` skill (encodes this
   review workflow + the questions to ask). *(committed)*
2. `docs/owner/fleet-vocab.md` — the owner shorthand dictionary (review/status/routines/
   plan/ship/groom → workflows). *(committed)*
3. `docs/eap/night-review-2026-07-11.md` — the full review (in progress; 3 survey agents
   fanned out over 13 lanes via GitHub MCP).
4. Routine + model owner-action checklist (attach repos per routine; set models) + the
   durable self-heal proposal.
5. A proposed one-line CLAUDE.md pointer to the vocab (owner-directed, flagged).

## What happened

- **Surveyed all 13 active lanes** via the fleet-manager roster (gen #5) + 3 read-only
  `general-purpose` survey agents (build / games / infra) over GitHub MCP — per lane:
  tonight's PRs, report quality, health/blockers, and model self-report.
- **Wrote `docs/eap/night-review-2026-07-11.md`** — per-lane digest, what's playable/valuable,
  concerning patterns, the two evidenced platform bugs, fix-first list, owner-action queue,
  lessons, what-went-well. Linked from `docs/eap/README.md` (new "Gen-2 night reviews" section).
- **Confirmed + evidenced the owner's two findings:** `add_repo` "[Unauthorized Persistence]"
  classifier denials ~1-in-2/1-in-3 on wake sessions (pokemon logs exact timestamps; gba
  corroborates) → routines that must call `add_repo` lose ⅓ of wake-hours; and the
  configured-vs-actual **model mismatch** (pokemon self-reports **sonnet-5**; substrate-kit
  ORDER-012 ruled the card authoritative but that's resolved-by-rule, not verified). The
  durable fix is owner-side (attach repos to routines) — an agent self-heal can't fix a
  *denied* call.
- **Built the shorthand system:** `.claude/skills/fleet-review/SKILL.md` (`/fleet-review`) +
  `docs/owner/fleet-vocab.md` (review/status/routines/plan/ship/groom) + a one-line CLAUDE.md
  pointer (owner-directed in-session).

## 💡 Session idea

**A `docs/owner/owner-action-queue.md` the manager keeps ruthlessly short** — tonight's #1
pattern is *value stranded behind owner clicks* (revenue, Pages, env vars, a Release, botsite
DB). Each lane flags its own owner items in its status, but there's no single deduped,
priority-ranked, always-current list the owner reads in one place. A manager-owned queue
(one row per real click, sorted by value-unblocked, stale items expired) would turn "the
fleet built a lot but shipped little" into a 10-minute morning sweep. Distinct from the
existing `fleet-manager/docs/owner-queue.md` (which exists but isn't ranked-by-value or
deduped against per-lane status).

## ⟲ Previous-session review

My own prior session (the instruction+env audit → ORDER 016) correctly identified the
merge-authority wall but I routed the *whole* fix through the manager; tonight's review shows
the manager is already saturated (roster mechanization, 5 kit releases relayed, 14/14 model
relay) — routing more P0s at it may queue behind its own work. Improvement: when a finding is
owner-actionable directly (like the routine repo-attach), put it in the owner's hands first,
not only in a manager ORDER. This review does that (§6 is an owner checklist, not a manager
order).

## Documentation audit (Q-0104)

`check_docs --strict` + `check_plan_homing --strict` run before push; night-review linked from
`docs/eap/README.md`; vocab linked from CLAUDE.md; skill registered. Chat-only material swept
into the review doc + vocab. No merged-PR ledger change (review is a new doc, not a PR record).
