# SuperBot — bot changelog

> **Status:** `living-ledger` — the **curated, user-facing** "what's new in the bot"
> source. One entry per *user-visible* bot change (a new command, a new game, a fix a
> user can feel). The public bot site renders this at `/changelog`
> (`scripts/export_dashboard_data.py` parses it into `site.json.bot_changelog`).
> Decided in router **Q-0179** / plan §7.5 (2026-06-19): a curated file, **not**
> auto-derived from session logs — the run-type seam classifies *how a session ran*,
> not whether a change is user-relevant, so auto-deriving would leak dev-internal noise
> onto a user surface.

## What belongs here (and what does not)

- **Belongs:** a new command or game; a visible new feature; a behaviour or bugfix a
  user would notice; a meaningful UX change. Write it in **user language** — "you can
  now…", not "refactored the X service".
- **Does not belong:** internal refactors, docs/tooling/workflow changes, CI work,
  test-only changes, routine reconciliation passes. Those live in the dev site's
  `/updates` feed (the `.sessions/` logs), never here.

## Format (parsed — keep it stable)

Each entry is a level-2 heading `## YYYY-MM-DD — <title>`, optionally tagged with a
**kind** in parentheses — `(feature)`, `(fix)`, or `(improvement)` — followed by a
short user-facing description. Newest first. The parser reads the date, the title, the
kind, and the first description line; everything else is for humans.

> **Seeding note (2026-06-19).** This file is **seeded** as part of the website
> two-site split foundation (plan §5, unit S1). The entries below are an initial,
> deliberately small set so `/changelog` renders something honest on day one; the
> ongoing discipline is to add one entry here whenever a *user-visible* change ships.

---

## 2026-06-19 — New public bot website (improvement)

A brand-new public website for the bot is taking shape — a marketing + reference site
(features, command reference, changelog, status) separate from the developer dashboard,
plus a public form to send in bugs and suggestions. More to come as it rolls out.

## 2026-06-12 — Owner review inbox on the dashboard (improvement)

The developer dashboard now surfaces an owner review inbox, so feedback and review
notes have a durable home instead of getting lost in chat.

## 2026-06-08 — Command-alias suggestions (feature)

You can now suggest a friendly alias for any command from the dashboard's Aliases page,
with a live check that the alias doesn't collide with an existing command or synonym.
