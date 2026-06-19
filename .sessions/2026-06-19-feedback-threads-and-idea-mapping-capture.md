# 2026-06-19 — Capture: per-command feedback threads + idea→cog/command mapping

> **Status:** `complete`

## Arc

While the website back-half fan-out builds, the owner expanded the vision twice (the command-detail
"notes" + the status rule). Captured both as durable idea docs so nothing's lost — they're follow-on
features, not part of the v1 fan-out currently building. Non-overlapping with the 5 fan-out agents (this
touches only `docs/ideas/`).

## Shipped (this PR)

- `docs/ideas/per-command-feedback-threads-2026-06-19.md` — the owner's **AI-moderated per-command
  feedback-thread** feature ("Codex for the bot's features"): anyone posts questions/bugs/improvements on a
  command/cog → an **Anthropic-API pass** cleans wording + blocks/rewrites foul language → threaded display.
  Goals: owner inline review · user dedup · honest feedback. Reuses the submissions store + moderation
  pipeline; **supersedes the v1 static `notes` field**.
- `docs/ideas/idea-to-cog-command-mapping-2026-06-19.md` — the **idea/bug → cog/command mapping** effort
  (explicit tag + validator; heuristic interim) that is the truth source for the site's per-command
  `status` + `linked_ideas`. "As fast as possible, not rushing."
- Indexed both in `docs/ideas/README.md`.

## Decisions confirmed / context delta

- **Status rule** (owner): a command is `in-progress` if it has **any related ideas/bugs**, else
  `finished` — this **matches what the running browser agent (S1.1) is already building**, so no change to
  the fan-out; accuracy improves as the mapping effort fills in (the agent uses a subsystem heuristic now).
- **Notes are dynamic, not static:** the owner's "notes" = the feedback-thread system above (DB + AI
  moderation + threading), not the help-text placeholder. The v1 browser's static `notes` field is a
  harmless interim (mostly `null`); the feedback system replaces it. Left the running agent undisturbed
  (its command-detail view is the right home for the future threads).
- These two are **follow-ons after the v1 site lands** — captured now, promotable to plans + build under
  Q-0172 once the fan-out is in.

## 📤 Run report

- **Did:** captured the owner's two new visions (per-command AI-moderated feedback threads + idea→command
  mapping) as durable, indexed idea docs; confirmed the status rule matches the in-flight build. · shipped.
- **Run type:** `manual` (owner vision capture, mid-fan-out).
- **⚑ Self-initiated:** `none` (owner-directed capture).
- **↪ Next:** the fan-out (5 agents) is building v1; on completion, verify + (per Q-0172) these two ideas
  are prime follow-on builds. Still pending from earlier: the control-panel router lock + rollout/security
  ops checklists.
