# Session logs — `.sessions/`

> One file per working session, named `YYYY-MM-DD-<slug>.md`, **newest-first by
> filename** (reverse-sort the glob). Process memory / history only — **not** project
> state (that's `docs/current-state.md`) and **not** the working model (that's
> `docs/collaboration-model.md`).

## Why per-session files

A single shared Session Log meant every session inserted a new entry at the *same* top
anchor, so any two concurrently-open PRs collided there (it bit #529→#530 and
#530→#531). Per-session files have no shared anchor → no structural merge conflict.

## Convention

- **Write** a new file at session end: `.sessions/<date>-<short-slug>.md`.
- Start it with an H1 `# <date> — <title>`, then the usual arc / shipped / findings /
  gates shape.
- **Always include a `Context delta` section** (this is the self-improvement loop — see
  `docs/collaboration-model.md` § "Why this system exists"). Produce it — and the two
  flag lines below — by running the **reflection interview** before writing the log: a
  standing six-question self-interview the maintainer used to run manually in chat
  nearly every session (formalized at his request, 2026-06-09, after the Lane-3/#634
  session's answers proved their value).
  1. **Where did the orientation route fail to cover you?** — context you had to find
     that orientation/folios didn't route you to (a file, a contract, a gotcha).
     → `Context delta`: **Needed but not pointed to**.
  2. **What were you pointed to that didn't pay off?** — reading the route sent you to
     that wasn't needed (candidate to de-emphasize).
     → `Context delta`: **Pointed to but didn't need**.
  3. **What did you reverse-engineer from source?** — tribal knowledge that deserves a
     home (e.g. a rule only living in a code comment).
     → `Context delta`: **Discovered by hand**.
  4. **What consequential decision did you make alone** that the maintainer should
     consciously ratify (a default you picked, a contract shape, a gate keyed on a
     label)? → a short **Decisions made alone** line in the log; if it's product
     intent, also a router entry.
  5. **What is the genuine weak point of what shipped** — the limitation or unverified
     half you'd want the next agent (or the prod check) to know?
     → the log's **Flagged for maintainer** / known-limits line.
  6. **What one docs/tooling change would have most helped this session?**
     → execute it in the grooming pass if small, else file it under `docs/ideas/`.
  7. **What interrupted your workflow — and did you ship a guard so the next session can't
     hit it?** A footgun, a silently-failed command, a stale/wrong-state trap, a manual
     fixup you had to repeat, anything that cost recovery time. **The reflex: don't just note
     it — convert it into the cheapest *durable, enforcing* prevention,** and do it *this*
     session (that's the "enforce, don't exhort" rule — a prose reminder is the weakest
     option). Prefer, in order: **a checker / CI guard / test** that fails on the bad state →
     **a hook** (`scripts/*` + `.claude/settings.json`) → **a journal Rule** as the last
     resort. Route by ownership: a docs/journal/test/checker guard is **free to ship now**; a
     **hook / `.claude/settings.json` / binding-`CLAUDE.md` rule** is **owner-gated** — build
     it if the owner directed it in-session (Q-0106), else propose it as a router DISCUSS Q.
     → the log's **`🛠 Friction → guard`** line (name the friction + the guard you shipped or
     proposed; `none` only if the run genuinely hit no friction — never invent one).
  Answer honestly and specifically — a near-miss is more valuable written down than a
  success story. A periodic REVIEW (`.session-journal.md`) mines these deltas and
  promotes recurring gaps into the orientation route / folios. Keep it to what you'd
  want the *next* agent to have known.
- **Always include a `📊 Model:` line** — the model family the session's own
  harness/environment reports, **family-level name only** (e.g. `fable-5`, `opus-4.8`,
  `sonnet-5`), committed in the card. Per-session self-report in the committed card is
  the fleet's only reliable attribution surface — the Routines screen is not (fleet
  standard, adopted 2026-07-11 via the fleet-manager ORDER 010 relay; see
  `control/inbox.md` ORDER 001; family-level policy: fleet Q-0262).
- **Don't** edit older session files — they're history. Durable rules / runbook facts
  graduate into `.session-journal.md` (the guidebook) or `.claude/CLAUDE.md`.
- **Find** past work by grepping this directory — don't read it top-to-bottom.
- Pre-migration history lives in `.session-journal-archive.md`.

## 📤 Run report footer (owner-facing — required, 2026-06-16)

End every session log with a `📤 Run report` block — the **owner's at-a-glance inbox** for the run.
Its job is to stop owner-facing notes (a decision only the owner can make; a step only the owner can
take) from evaporating into prose, where they get reconstructed ad-hoc or lost. Hermes rolls these
blocks up across the day, so the two ⚑ lines are **required** — write `none` when empty.

```markdown
## 📤 Run report

- **Did:** <one line — what this run shipped> · **Outcome:** shipped / blocked / partial
- **Shipped:** #PR — one line each (or "no PR — <why>")
- **Run type:** `routine · dispatch` / `routine · reconciliation` / `manual` (Q-0165)
- **⚑ Owner decisions needed:** <Q-#### + one line, or `none`>
- **⚑ Owner manual steps:** <a thing only the owner can do, or `none`>
- **⚑ Self-initiated:** <idea promoted to a plan/build with no dispatch or owner ask — name + link, or `none`> (Q-0172)
- **↪ Next:** <the sharpened current-state ▶ Next action>
```

The **`Run type`** line (Q-0165, 2026-06-17) lets the owner tell routine work from his own at a
glance — the **dashboard updates feed badges any log whose Run type contains `routine`**
(`scripts/export_dashboard_data.py` → `/updates`). A routine (dispatch / reconciliation) sets it
from its prompt; a manual session writes `manual`.

The **`⚑ Self-initiated`** line (Q-0172, 2026-06-17) is the accountability half of the **open
idea→plan gate**: the maintainer removed the approval gate so any agent may promote an idea → a
`docs/planning/` plan → an implementation **without asking first** — provided it is *flagged here*.
List any idea built/planned **without a dispatched order or an owner request** (name + `docs/ideas/`
or `docs/planning/` link); write `none` when the run only did dispatched / requested / bug / docs
work. The **dashboard updates feed badges any log whose `⚑ Self-initiated` line is non-`none`**
(`scripts/export_dashboard_data.py` → `/updates`), so the owner can see, filter, and review
unprompted work on the website — that filterable surface is the point of the line.

The `⚑ Owner manual steps` line is **not** for "deploy the fix" — **a merge to `main` auto-deploys
to Railway** (~CI build time; a failing build never deploys; the old container stays up until the
new one connects — see [`operations/production-deployment.md`](../docs/operations/production-deployment.md)).
A real manual step is an *off-repo owner action*: re-paste a routine prompt to the console, set a
Railway env var, run a Discord `!command` in a guild, or make a product/abuse decision.

## 📊 Telemetry footer (gap-analysis §4, light version — 2026-06-12)

End every session log with a `📊 Telemetry` table so the system's learning trend is
measurable (evidence for Q-0083's trust-tier promotions instead of vibes):

```markdown
## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | N |
| CI-red rounds | N (rounds from push → green on the session's PR) |
| Repo-rule trips | N (arch check errors / rule violations hit) |
| New ideas contributed | N (Q-0089 ideas) |
| Ideas groomed | N (backlog moves made) |
```

Keep it honest — a CI-red-rounds count of 2 is more useful than 0. The caretaker
weekly rollup (the heavier half of gap-analysis §4) is not yet built; the footer
makes the data available when it is.
