# Rebuild — the test-guild design (companion C of the canonical plan, 2026-07-06)

> **Status:** `plan` — companion to
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) §6 / layer **V-4**.
> A concrete Discord test-guild layout — a proper channel per function so **every subsystem has a
> home to be exercised and observed** — plus the live-fidelity driver architecture (canonical-plan
> flag **F-4**). Spec only: **this doc does not stand the guild up** (that happens at §5 step 12 /
> CUT-1). Seeded from the brief's zone list and refined against the live `disbot/cogs/` roster
> (~55 cog modules, verified on disk 2026-07-06).

## 1. Design rules (why the layout looks like this)

1. **A channel is an observability unit.** A subsystem gets its **own** channel when its state is
   channel-scoped (counting, chain, starboard), its output is high-volume (games, logging sinks),
   or its live walk needs an uncontaminated transcript (`verified_live` evidence links point at
   channel history). Subsystems whose surface is ephemeral panels/commands **share** a zone
   channel — a panel leaves no channel residue worth isolating.
2. **Zones mirror the port bands** (Sequence C): the guild builds out in the same order the port
   does, so at any moment "which zones exist" *is* the live progress bar of P4, and CUT-1 smoke
   starts with zone 1 only.
3. **Sinks are separate from probes.** Channels the bot *writes into* as a side effect (logging
   routes, starboard board, spotlight feed, alerts) are distinct from channels where drivers
   *invoke* — so an assertion "this action produced exactly this log line" reads one channel.
4. **Negative-test surfaces are first-class.** A channel where AI is policy-OFF, a role with no
   capabilities, a locked channel — the deny paths are half of what governance goldens prove.
5. **Everything the guild needs is declarable** — the guild layout itself should eventually be a
   manifest the K2 compiler can emit as a "provision test guild" plan (the same
   channel/role-binding grammar the bot already declares; do not hand-maintain the guild once the
   grammar exists).

## 2. The channel manifest (9 zones, ~40 channels)

**Structural fixtures (guild-level):** persona role ladder **@tg-owner / @tg-admin / @tg-mod /
@tg-member / @tg-restricted** (matching parity's personas) + **@tg-driver** (low-privilege, for
the human-lane second account) · one **voice channel** (`🔊 counters-probe`) for member/voice
counters · a **`STRUCT-SANDBOX` category** where channel/role lifecycle tests may create/delete
freely without touching the fixed layout.

| Zone (category) | Channels | Subsystems homed (from live cogs) |
|---|---|---|
| **Z1 · operator-core** | `#op-settings` · `#op-admin` · `#op-setup` | settings, diagnostic, help (band-1 trio) · admin, server_management, general/utility diagnostics · setup + quicksetup + bootstrap_access (wizard runs here; its *created* objects land in STRUCT-SANDBOX) |
| **Z2 · moderation-safety** | `#mod-actions` · `#mod-image` · `#mod-log` *(sink)* · `#mod-quarantine` *(fixture)* | moderation, automod, security (raid/lockdown probes) · image_moderation (off-until-opt-in posture verified here) · logging's routed output — **the sink channel every Z2 golden asserts against** · cleanup + the quarantine action's target |
| **Z3 · server-structure** | `#struct-lifecycle` · `#tickets` (+ ticket category) · `#counters-config` (+ `🔊 counters-probe`) · `#proof` | channel + role + role_grants (lifecycle ops execute into STRUCT-SANDBOX) · ticket (open/claim/close/transcript) · counters · proof_channel (timed unlock — the restart-persistence golden lives here) |
| **Z4 · presentation** | `#welcome` *(sink)* · `#ux-lab` · `#cards` | welcome (fires on real member-join — the human-lane account joining/leaving is the probe) · ux_lab gallery · card-engine renders (rank/profile/leaderboard cards eyeballed + goldened) |
| **Z5 · economy-progression** | `#economy` · `#progression` · `#community` *(+ spotlight sink thread)* | economy, treasury, inventory · xp, karma, leaderboard, profile surface · community hub + community_spotlight feed |
| **Z6 · games** (one channel per game — state isolation) | `#game-blackjack` · `#game-rps` · `#game-deathmatch` · `#game-fishing` · `#game-farm` · `#game-creature` · `#game-casino` · `#game-counting` · `#game-chain` · `#game-420` · `#game-mining` · `#game-explore` · `#giveaways` · `#starboard-src` + `#starboard-board` *(sink)* | blackjack (+tournament), rps_tournament, deathmatch (the P-2 settle-once golden), fishing, farm, creature (+battle), casino, counting (channel-bound), chain (channel-bound), four_twenty, mining, explore-class, giveaways, starboard (source + board pair) |
| **Z7 · knowledge-ai** | `#ai-general` · `#ai-btd6` · `#ai-projmoon` · `#ai-off` *(negative)* | ai + ai_review (NL policy ON here; conversation memory, tool orchestration) · btd6 family (+events/ops/reference/strategy/paragon) · project_moon · a channel with AI policy OFF — the should-not-reply golden |
| **Z8 · utility-misc** | `#utility` | utility, general, media/health maintenance observability (`!platform` readouts) |
| **Z9 · control-plane** | `#ops-status` · `#verify-signoff` *(registry mirror)* · `#driver-log` *(sink)* · `#alerts` *(sink)* | dashboard/boards/migration/health readouts · the human-readable mirror of `verified_live` sign-offs (V-5 registry rows posted as they land) · the automated driver's run transcripts · Railway/CI alert webhooks (mirrors the HQ-guild `#railway-alerts` pattern) |

**Own-channel vs shared, decided:** every Z6 game owns a channel (channel-scoped state +
uncontaminated transcripts); counting/chain/starboard/proof/welcome/logging **structurally
require** their channels (the feature *is* channel-bound); everything else shares its zone
channel — panels and commands leave assertable output without needing isolation.

## 3. How the layout maps onto CUT-1 (and the port bands)

CUT-1 = the new bot boots **container-only on the test-bot token** into this guild (Q-0222). The
guild is provisioned in band order:

| Port band (Sequence C) | Zones lit up | CUT-1 smoke that must pass there |
|---|---|---|
| band 1 settings/diag/help | Z1 (+Z9 skeleton) | boot → `/ready` → settings panel opens → help projection renders → diagnostic providers report |
| band 2 operator spine | Z2 + Z3 | mod action writes audit + `#mod-log` line; ticket lifecycle; lifecycle ops create/delete in STRUCT-SANDBOX; proof-channel unlock survives a bot restart |
| band 3–4 economy/progression | Z5 | credit/debit writes audit row; xp level-up fires event; leaderboard renders |
| band 5 platform/control | Z9 full + Z8 | boards/health readouts live |
| band 6 games (late) | Z6 | per-game happy path + the settle-once concurrent golden (deathmatch) |
| band 7 knowledge/AI | Z7 | NL reply in `#ai-general`, silence in `#ai-off`, grounded BTD6 answer, tool-call round-trip |

The guild is also where the **five non-game replacement oracles** (P-4: wager-idempotency,
settle-once, deathmatch-stats, economy/xp, mining whole-stack) run their live legs — service-layer
harnesses in-container, per Arm D's pattern.

## 4. The fidelity architecture — driving the FULL pipeline (canonical flag F-4)

**What's already solved:** `parity/` drives the full real command pipeline **in-process** — real
`parse_message_create`/`parse_interaction_create` through real converters, cooldowns, the
governance `before_invoke` gate, and the error handler; only HTTP is fake
(`parity/README.md:11-18`, `harness/boot.py:272/292/316`). It bypasses `author.bot` legitimately:
synthetic payloads carry `"bot": false` (`harness/world.py:298`).

**What's structurally closed (verified against source — do not spend effort here):**

- A **bot-token wire driver cannot invoke message commands** — discord.py's library default drops
  bot-authored messages (`ext/commands/bot.py:1413`), and disbot's own passive pipeline drops them
  again (`core/runtime/message_pipeline.py:279`, plus per-cog guards) — so **passive pipelines
  (XP, logging, AI passive answering) are also unreachable from a second bot**, contradicting the
  wire-level idea doc's coverage claim.
- **Slash/component interactions cannot be fabricated over real HTTP** — interaction tokens are
  Discord-minted and no bot API invokes another application's commands. *(✅ VALIDATED against
  official Discord docs 2026-07-07, final-review session: no cross-application invocation endpoint
  exists; interaction tokens are Discord-generated and 15-min-scoped; the outgoing-webhook path is
  Ed25519-signed (`X-Signature-Ed25519` — unforgeable without Discord's key) and gateway delivery
  exposes no attacker-facing HTTP surface at all; user-installable apps (`integration_types`/
  `contexts`) and Components v2 change where commands appear, not the user-initiated invocation
  model. Docs: docs.discord.com/developers/interactions/{receiving-and-responding,
  application-commands} + /components/reference. The constraint is FROZEN; lane B's scope is
  final.)*
- **Automating a user account is a ToS-prohibited self-bot.** Never.
- `ctx.invoke`/Context-construction bypasses skip exactly the checks under test — the repo's own
  code rejects that pattern (`bot1.py:562-572`).

**The two lanes:**

| Lane | Mechanism | Covers | Produces |
|---|---|---|---|
| **A · automated** | the in-process synthetic-gateway technique, extended with a **real (non-faked) HTTP boundary for prefix commands** — the bot runs in its CUT-1 container against the real test guild; the driver feeds synthetic non-bot message payloads in-process; responses go out over **real HTTP** and land visibly in the zone channels | full command pipeline for **prefix** commands with Discord-visible live output; plus the existing faked-HTTP parity replay for slash/components (pipeline-true, not live) | golden replays + `#driver-log` transcripts; agent-runnable, repeatable |
| **B · human** | the maintainer (or a manually operated **@tg-driver** second account) walks slash commands, component clicks, modals, and panels per zone | the interaction surfaces automation cannot reach, **plus** the Q-0234 "self-explanatory" judgment only a human can make | **`verified_live` sign-off rows** (schema: verification-review §3.3 — command, guild/persona, steps, expected visible + DB/audit effects, signer, timestamp + build SHA, evidence link), mirrored into `#verify-signoff` |

**Build prerequisite:** the `verified_live` registry has **zero implementation today** (docs-only
across five files) — build it (V-5) before CUT-1, recording *which lane* produced each sign-off.

**Known gap to staff:** no low-privilege second human account exists in the current test guild
(Arm D's blocker) — the owner adds/operates one for lane B; until then lane-B rows are
maintainer-walked only.

## 5. Per-zone "what you'd exercise / what proves it"

| Zone | Exercise (lane A unless marked) | Proof |
|---|---|---|
| Z1 | settings read/mutate per key; help render paths; diagnostic providers; wizard dry-run (B: panel walk) | settings goldens (today **2% key coverage — the P-5 depth work lands here first**); help projection goldens; `verified_live` rows for the wizard |
| Z2 | warn/timeout/kick paths incl. **deny** paths per persona; automod trigger corpus; lockdown/slowmode; image-mod stays OFF until opt-in | audit rows + `#mod-log` lines per action (the audited-seam contract P-1 asserts here); deny-path goldens per persona; B-lane component walks |
| Z3 | create/rename/delete into STRUCT-SANDBOX; ticket lifecycle; counter refresh; proof-channel unlock **across a bot restart** | lifecycle audit + teardown goldens; the restart-persistence golden (Arm D pattern); ticket transcript artifact |
| Z4 | real member-join (B: driver account joins) → welcome fires; card renders | welcome sink message matches golden; card renders eyeballed (B) + pixel/layout goldens where stable |
| Z5 | credit/debit/transfer; xp award → level-up event; karma give; leaderboard | **the atomic multi-leg contract (P-1)**: balance + audit row + event all present or all absent; event/table goldens (the 21%/25% depth work) |
| Z6 | per-game happy path; **concurrent settle race** (deathmatch — P-2); wager escrow race; idle-accrual across restart (mining/farm) | settle-once goldens (exactly-one-True); escrow idempotency (`double_paid=False`); time-driven behavior is a **named non-golden class** — assert via DB state after driver-controlled clock steps |
| Z7 | NL prompts per policy scope; grounded QA per domain; tool-call round-trip; **silence in `#ai-off`** | decision-audit row per message (exactly one); grounding-verifier pass; the routing-disjointness invariant; evals corpus replay (`tests/evals/`) |
| Z8 | utility commands; `!platform` readouts | smoke goldens |
| Z9 | dashboards read; sign-off mirror; alert webhook fire | registry rows accumulate; alert lands in `#alerts` |

## 6. What this design deliberately defers

Standing the guild up (CUT-1, §5 step 12 of the canonical plan) · the guild-provisioning manifest
(post-K2, rule 5) · widening lane A to slash/components if the interaction-token constraint ever
falls (validate once, then revisit) · multi-guild scale testing (a second minimal guild only if a
cross-guild-bleed golden needs it — `cache_scope` makes that a declaration-level concern first).
