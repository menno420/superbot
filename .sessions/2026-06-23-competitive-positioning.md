# 2026-06-23 — Competitive-positioning north-star (what makes people choose us)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat follow-up to the Dank Memer visual work: "what would make people prefer
> ours over any other"; owner picked *capture a positioning vision doc* + *deep-research
> competitors* via AskUserQuestion). Docs-only PR #1352. Auto-merges on green (Q-0123).

## Arc

Second batch of the visual/strategy session (first batch = the card engine, PR #1349, merged). The
owner asked the broader question: not just "beat Dank Memer's visuals" but "what makes people pick
us over **any** bot." Ran a fan-out of research agents across the whole competitive field —
economy/games (Dank Memer, UnbelievaBoat, IdleRPG, Pokétwo/PokéMeow, OwO, Mudae), leveling/engagement
(MEE6, Arcane, Amari, Tatsu, Lurkr), moderation/all-in-one (Carl-bot, Dyno, ProBot, Wick, Sapphire),
and an AI-native + market-gaps synthesis. The patterns were strikingly consistent. This batch
captures the synthesis as a north-star positioning doc.

## Plan (this PR)

- `docs/ideas/competitive-positioning-north-star-2026-06-23.md` — the grounded positioning thesis:
  the universal incumbent failure modes (utility paywalls / pay-to-win / setup friction /
  jack-of-all-trades), our wedge (AI-operated, best-in-class-per-feature, cosmetic-only
  monetization), pillars ranked by defensibility, the honest counter-arguments, and the
  roadmap implication.
- `docs/ideas/README.md` index entry.

## Shipped (PR #1352)

- **`docs/ideas/competitive-positioning-north-star-2026-06-23.md`** — the north-star: four universal
  incumbent failure modes (utility paywalls · pay-to-win · setup friction · jack-of-all-trades),
  our wedge (AI-*operated*, best-in-class-per-feature, cosmetic-only-by-promise), five pillars ranked
  by defensibility × evidence confidence, the honest counter-arguments, and the roadmap implication.
- **`docs/ideas/README.md`** — index entry.

## Research provenance (the per-bot findings behind the doc)

Fan-out research pass (agents, web-sourced, citations in transcripts). Key load-bearing findings:
- **MEE6 backlash** is the central validation: it paywalled once-free *utility* (role rewards, custom
  commands, leveling config) at ~$11.95/mo *per server* → spawned `alternativestomee6.com` + durable
  "cash grab" sentiment. Lesson: paywalling depended-on utility breeds migration movements.
- **ProBot** retroactively paywalled leveling + reset levels + deleted non-payer data (purest bait-and-switch).
- **UnbelievaBoat** 2025 sub-switch froze legacy buyers; 25-item free cap.
- **Pay-to-win resented** everywhere it buys *advantage* (PokéMeow "locked out without Patreon",
  Pokétwo incense/charm, Mudae premium rolls, IdleRPG cooldown cuts + donor class, Tatsu 5× exchange cap);
  **OwO praised** because Patreon perks are *tradeable* → "fair". Cosmetic/tradeable accepted, advantage-for-cash rejected.
- **Setup friction** is the highest-confidence unsolved gap (Carl-bot "admin console"/JSON embeds, YAGPDB,
  UnbelievaBoat item→role, multiple-dashboards "four points of failure"); MEE6/ProBot win on ease then upsell.
- **AI lane:** "bolted-on chatbot" is crowded + shallow (Discord's own Clyde launched + killed in <1yr);
  the open lane is **AI-as-operator** (conversational config / NL admin / context-aware mod), claimed only by
  tiny unproven 2026 startups (PeakBot/VibeBot). Win = depth/execution, not the label.
- **Counter-thesis to respect:** CommunityOne's "specialize as you grow" — all-in-ones risk
  jack-of-all-trades; our answer must be genuine per-feature quality. Plus Discord's 2026 gambling
  headwind against casino-heavy economies.

## Verification

- `check_docs --strict` → all checks passed (new doc reachable from the ideas README; 432 docs).
- Docs-only PR — no `disbot/` code, so no arch/test surface changed.

## Session enders

- **♻ Grooming (Q-0015):** captured + routed one new idea (this positioning north-star) into the
  backlog with its README index entry; it gives future sessions a lens for prioritising the
  card-engine roadmap and the AI-setup wedge.
- **💡 Session idea (Q-0089):** *A user-visible "cosmetic-only monetization" pledge surface* — e.g. a
  short `!pledge` / about-page line stating "we will never paywall a feature you rely on." The
  research shows the *promise itself* is a differentiator (it's the inverse of the MEE6 betrayal
  narrative), so making it explicit and discoverable converts an internal principle into marketing.
  Tiny, contained. Dedup-checked `docs/ideas/` — not yet captured.
- **⟲ Previous-session review (Q-0102):** the predecessor batch (card-engine PR #1349, same session)
  executed cleanly — engine + first card + dedup + tests + vision doc, green CI, merged. *Did well:*
  built the foundation rather than only reporting, and sent the owner rendered theme samples (showed,
  didn't tell). *Workflow improvement it surfaces:* the research fan-out this batch spawned a **deep
  nested agent tree** (a parent that spawned children that spawned grandchildren), and resuming the
  top parent via a fresh `Agent` call (instead of continuing the same agent) started a confused new
  agent. Lesson for the workflow: **for fan-out research, prefer one flat batch of sibling agents
  over deep nesting**, and continue an existing agent by its id rather than re-spawning — deep trees
  make synthesis-collection error-prone.
- **📋 Doc audit (Q-0104):** `check_docs --strict` green; the full competitive research is preserved
  in this session log (not left chat-only); the positioning doc is reachable and cross-linked to the
  visual-card-engine vision + the superbot product vision.
