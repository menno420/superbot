# Per-command AI-moderated feedback threads ("Codex for the bot's features")

> **Status:** `ideas` — **owner-directed (2026-06-19)**, captured during the website two-site-split fan-out.
> A real new feature, distinct from the v1 static-notes placeholder. Ready to promote to a `docs/planning/`
> plan + build after the v1 bot site lands (Q-0172: any agent may promote → build, flagged self-initiated).

## The vision (owner's words, 2026-06-19)

On the bot site, every command (and cog) carries an **optional feedback box**: **anyone** can leave a
note — a question, a bug, an improvement — **right on that command**. It works like **Codex reviewing our
PRs**: a **thread** of questions / bugs / improvements that accumulates per command.

Three goals:
1. **The owner** can browse the cogs/commands and **leave thoughts inline, right there, to review later.**
2. **Every user** can **see whether a bug they found or an improvement they want has already been raised**
   by someone else (dedup, transparency).
3. **Everyone gets to give honest feedback** about the bot's actual functions.

## The moderation gate (the key mechanic)

Every submitted note passes through an **Anthropic-API review** *before* it posts (the bot already runs on
Claude — an API key exists):
- **suggests a cleaner phrasing** of the note where possible (so threads stay readable/useful);
- **blocks or rewrites foul language / abuse** entirely;
- (extension) can de-duplicate against existing notes on the same command ("this looks like the existing
  thread X — add to it?") and classify the note (question / bug / improvement) to match the Codex-style
  thread shape.

This is the same spirit as Codex's PR review: an AI pass that turns raw input into a clean, useful,
safe contribution.

## Where it fits the architecture

- **Home:** the **command detail view** (website plan §"Site identity & experience" → the interactive
  browser, unit P2). The feedback thread lives under each command/cog; this **supersedes the v1 static
  `notes` field** (which was a help-text placeholder — the real notes are these dynamic threads).
- **Store:** a new table in the **dashboard-owned Postgres** (the same store as `submissions`, §2.3 of the
  plan), keyed by cog/command, threaded. Reuses the submissions infrastructure pattern.
- **Intake (public, no login — "anyone"):** post → **Anthropic-API moderation** → (clean/blocked) → store
  → display. Inherits the public-submission **abuse plan** (honeypot + rate-limit + salted IP hash, plan
  §4.2) *plus* the AI content gate. Render **escaped**.
- **Display:** public, per-command thread (moderated entries only). Users browse existing feedback before
  adding (goal 2).
- **Owner side:** the dev site's moderation surface (the P5 moderation UI's sibling) lets the owner
  review/hide/curate threads and **promote** a note to a GitHub issue via the existing least-privilege
  mirror (§4.3) — so a good bug/idea flows into the real backlog. The owner's own inline notes (goal 1)
  are first-class authored entries.

## Relationship to the `/submit` form (P4)

`/submit` is a **general** bug/suggestion form → moderation → GitHub issue. These feedback threads are
**per-command, inline, threaded, AI-moderated discussion**. They converge at moderation: a thread entry the
owner deems actionable can mirror to GitHub on the same pipeline. Design decision for the plan: whether
`/submit` becomes "post to the relevant command's thread" or stays a separate general intake (recommend:
keep both; `/submit` for "I don't know which command," threads for "I'm looking at this command").

## Open design decisions (for the plan/build)

- **Anthropic moderation contract:** model + prompt for the clean-up/block/classify pass; fail-safe
  behaviour (if the API is down — queue for owner review rather than auto-post; never auto-post unmoderated).
- **Identity:** fully anonymous vs optional contact vs Discord-OAuth attribution (affects spam + dedup).
- **Cost/rate:** an Anthropic call per submitted note — rate-limit + cap to bound cost.
- **Public display threshold:** auto-post after the AI gate, or owner-approve first (recommend: AI-gate
  auto-post for clean notes, owner can hide; foul → blocked; borderline → held for owner).

## Why it's worth having

It turns the public site from a brochure into a **living, honest feedback loop on every function** — the
internal mirror of how Codex/agents review our code, pointed at the bot's features and opened to users.
It also gives the owner a frictionless inline "leave a thought on this command" surface (goal 1), which is
exactly the kind of low-friction capture this whole agent-workflow project values.

→ relates: website plan `planning/website-two-site-split-plan-2026-06-19.md` (P2 detail view · §2.3
submissions store · §4.2 abuse plan · §4.3 mirror) · `idea-to-cog-command-mapping-2026-06-19.md` (threads
key on the same cog/command mapping) · the bot's existing Anthropic/Claude integration.
