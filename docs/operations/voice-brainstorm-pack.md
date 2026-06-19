# Voice-brainstorm pack — drop this into a Claude voice chat / Project to brainstorm SuperBot

> **Status:** `reference` — a *condensed* context pack for **voice / casual brainstorming** (separate from
> Claude Code). Owner-directed 2026-06-19. Deliberately SHORT: voice works best with a tight prime + a list
> of open threads, **not** a doc dump. Do **not** paste `current-state.md` into a voice chat (it's a dense
> ledger). For depth later, the real docs are `docs/ideas/README.md` + `docs/owner/maintainer-question-router.md`.

## How to use
Paste this whole file as the context — a Claude **Project's** custom instructions, or the first message of a
voice chat — then just start talking.

## Prime (the load-bearing part — this is the instruction to Claude)
> You are my brainstorm partner for a Discord bot called **SuperBot**. **I'm good at reacting to ideas but
> bad at generating from a blank slate — so YOU lead.** Pull ONE thread from "Open threads" below, pose it as
> a concrete fork or a "have you considered X?", and let me react; then sharpen what I say into something
> buildable. One thread at a time, conversational (this is voice). **Never suggest something already under
> "Already shipped" or "Already decided" — check those first; if unsure, ask me rather than assume.** When we
> land on something good, say so plainly and give me a one-line summary I can capture later.

## Already shipped — do NOT re-suggest these
- **Games:** mining (skill tree · Forge · Home · Vault · gear sets · titles), fishing v1, blackjack / RPS /
  deathmatch, a shared game-XP + leaderboards.
- **BTD6 AI:** deterministic grounded answers (towers/heroes/paragons/bosses/MK/relics + cost comparisons),
  a round-cash workflow.
- **Safety / moderation:** automod, server logging, welcome cards, image moderation, security tiers (raid /
  account-age).
- **Surfaces:** the read-only dashboard (status/aliases/games/env), the public bot-site + dev-site split
  (foundation), `/myprofile`, the owner review inbox (`/reviews`).
- **Workflow substrate:** the whole agent system (router, checks, drift guards, ground-truth protocol).

## Already decided — locked directions (don't re-litigate; refine instead)
- **One federated world:** mining/fishing/etc. share a character + currency + an **Explore hub** + a light
  survival/quest overlay, but each subsystem stays its own complete game. XP = three tracks (message → AI
  dungeon-master negotiation · global game-XP · per-game). Gear = hybrid, opt-in auto-best (default off).
- **AI memory:** opt-in; user picks global vs per-guild; declared via `remember this:`; see/forget controls.
- **AI reports back to the owner:** when corrected/asked, the AI files a ticket to the review inbox → an
  eventual **AI ticket service** (audience-routed, fail-closed). *Needs its own dedicated session.*
- **Monetization:** cosmetic-only donations (no bot-side billing).

## Open threads — pull on THESE (the brainstorm fuel)
1. **What the Explore hub literally IS in Discord** — a menu of buttons? a rendered PIL world-map with
   location buttons? location "rooms"? (The bot can render images.)
2. **The federated world's feel** — which resource loops (fish→food→deeper mining; mine→materials→better
   rod) and how survival pressure attaches *without* forcing it on cozy players.
3. **The AI ticket service's hard part** — how the AI decides *who a report is for* (owner / this server's
   mods / public) so a server-private bug never leaks to the public site.
4. **The bot-site's one-sentence pitch** — what is this bot *to a stranger*, in one line?
5. **What "lightly remembers you" should actually recall** — and the global-vs-per-guild default.
6. **The next world activity** — after fishing, what fits the federated world: farming? a tavern/social
   space? a pet/companion layer? something else?

## For depth (a Code session, not voice)
`docs/ideas/README.md` · `docs/owner/maintainer-question-router.md` · `docs/planning/README.md`.
