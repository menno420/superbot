# Routine-activity visibility — see active/running sessions at a glance

> **Status:** `ideas` — capture only, owner-observed 2026-06-14. **Not a plan, not approval.**
> Source code, the binding contracts, and `docs/current-state.md` win over anything here.

**Observed (owner, 2026-06-14, in-session).** Routine *run* sessions do **not** appear among
normal sessions in the **Recents** tab. To find a running routine the owner must open the
**Routines** tab → tap a routine → scroll down → tap the active run. There is no at-a-glance
"is any session active right now?" signal when he comes online.

## Why it's like this (upstream, not ours)

This is an intentional Claude Code **product** behavior: scheduled-routine runs are hidden from
Recents so daily runs don't flood the list with hundreds of items. It is a known gap with an open
Anthropic feature request —
**[anthropics/claude-code#54517](https://github.com/anthropics/claude-code/issues/54517)**
"Allow scheduled agent / Routine runs to appear in Recents or be pinnable in the sidebar" (related:
[#33095](https://github.com/anthropics/claude-code/issues/33095), surface active CLI sessions in the
mobile/web app). **We cannot change the app UI** — the real lever there is 👍 / commenting on #54517.

## Existing workarounds (no build needed)

- **Calendar tab** on the routines page → a visual timeline of all scheduled runs across routines,
  faster than tapping each routine individually. ([routines docs](https://code.claude.com/docs/en/routines))
- **Mobile app Code tab** shows sessions with a **green status dot** when active — but only for
  sessions that *appear in the list*, so it does not help for Recents-hidden routine runs.

## DIY angle that fits *our* ecosystem (the real opportunity)

SuperBot is a Discord bot — so a routine can **announce itself**: have each routine's prompt (or a
shared step) post a one-line **Discord webhook** ping to a private ops/`#routines` channel on
**start** and **finish** ("🟢 routine X started 10:31" / "✅ finished — PR #N"). That turns "is
anything running?" into a phone notification the owner already gets, independent of whether the app
surfaces the session. Cheap, self-hosted, and independent of the upstream FR.

- **Cost:** a webhook URL as a cloud-environment env var + ~10 lines in the routine prompt or a hook.
- **Caveat (ask-gated):** posting to Discord is an *external publish* and needs a webhook/secret plus
  the owner picking the channel — so it is an **ask before building**, not a free-rein change.

## Classification

- **Lane:** small/safe **once the owner okays the channel + webhook** (then it is a contained hook).
- **Upstream half:** track-only — 👍 #54517; nothing for us to implement there.
- **Next step:** owner decides whether to build the Discord-ping; if yes, it is roughly a 1-PR add.
