# Product catalog — everything the fleet has produced, in plain language

> **Status:** `living-ledger` — the owner-facing answer to "what do I actually have?"
> One entry per product: what it is, who it's for, how to use it, what's left for you.
> Created 2026-07-11 from a full-fleet survey (every claim verified against live
> GitHub that day). Update on "explain" requests and fleet reviews; retire entries
> when products die. The canonical *task* queue stays fleet-manager
> `docs/owner-queue.md` — this file explains the products those tasks belong to.

## Ready to sell (owner clicks away from revenue)

### 1. Membership-Site Boilerplate Kit — $49 (venture-lab)
- **What:** a starter kit someone buys to add a "paid members area" to their own
  website: customer pays via Stripe Checkout → the included server verifies the
  payment webhook → the member is granted access. Works with a simple file store by
  default; optional Supabase (hosted database) mode.
- **Who for:** indie developers who want paid memberships without building the
  payment plumbing.
- **Use/deploy:** buyer downloads a zip and follows its README. The sellable zip is
  already built and committed: `candidates/membership-kit/dist/membership-kit-v0.2.zip`.
- **You (only you):** create a free Stripe account and paste test keys into
  `server/.env` (proves the end-to-end purchase once); then publish on
  Gumroad/Lemon Squeezy — the exact 9-click script is in
  `venture-lab docs/launch/membership-kit/owner-actions.md`.
  **Recommended: run the Codex pre-publish review first** (prompt 2 in
  `docs/owner/codex-review-prompts-2026-07-11.md`).

### 2. Stripe Webhook Test Kit — $29 (venture-lab)
- **What:** a command-line tool developers run to test their Stripe webhook code: it
  fires realistic, correctly-signed fake Stripe events at their local server, and its
  `--forge` mode proves their handler rejects forged (unsigned) events. Also catches
  two classic Stripe gotchas automatically.
- **Who for:** any developer integrating Stripe webhooks (a huge, evergreen audience).
- **Use/deploy:** buyer downloads the zip, runs the CLI. Ranked the fleet's best
  venture bet (venture-eval score 4.05).
- **You:** publish click (`docs/launch/stripe-webhook-test-kit/publish-owner-action.md`)
  + publish the free companion "gotcha article" — that article click **starts the
  14-day market-validation clock** the lane is waiting on.

### 3. Agent-Workflow Template Pack — $19 pay-what-you-want (venture-lab)
- **What:** packaged, reusable templates of this fleet's own agent-working
  conventions (session logs, question routers, checkers) for people running AI
  coding agents.
- **You:** publish click (`docs/launch/template-packs/owner-actions.md`). A $59
  bundle listing of all three products is drafted and goes live once #1 and #3 have
  URLs.

## Playable now

### 4. Lumen Drift v1.3 — original GameBoy Advance game (gba-homebrew)
- **What:** a finished, original GBA game: you are a mote of light descending an
  endless cave — collect spark shards, graze crystals for light refunds, outrun the
  surge. Deterministic caves, save-best-depth. 100% original assets, publish-safe.
- **Who for:** anyone with a GBA emulator; also the fleet's proof it can ship a
  complete game.
- **Play it:** download `dist/lumen-drift.gba` (~160 KB) from the repo → open in
  mGBA (desktop/Android) or Delta (iOS). No build step. Controls in `docs/PLAYING.md`.
- **You:** one click to create the GitHub Release `lumen-drift-v1.3` (agents get 403
  on releases); optional itch.io publish decision; and the "graze feel" playtest —
  the machine proves it works, only you can say it feels right.

### 5. Pokémon Emerald QoL+ mod (pokemon-mod-lab — PRIVATE, never distributed)
- **What:** your personal modded Emerald: 16 toggleable quality-of-life patches
  (instant text, auto-run, faster HP bars/hatching/fishing, tutorial skips, second
  R-button item…). Every patch is proven with headless-emulator screenshot evidence
  and byte-identical rebuild checks.
- **Who for:** you. (Nintendo-copyrighted base — private repo, ROMs never leave it.)
- **Play it:** build per `docs/build-presets.md`, load the ROM in any GBA emulator.
- **You:** ONE play session to verdict the six feel-patches (keep/tune/drop each) +
  the one-word Match Call decision. That's the only thing the lane is waiting on.

### 6. games-web — mining character sheet in the browser (product-forge)
- **What:** a zero-dependency web app showing an RPG "mining character sheet" from a
  versioned game-data format — the public demo of how superbot game data becomes web
  pages.
- **Use:** locally `products/games-web/run.sh`; publicly it's **one settings toggle
  away**: enable GitHub Pages (Settings → Pages → Source: GitHub Actions) and it
  publishes to `menno420.github.io/product-forge/` on the next push.
- **You:** that one Pages click.

## Live services

### 7. SuperBot — the production Discord bot (superbot)
- **What:** the original bot, live on Railway, auto-deploying on every merge to main.
  Games, economy, moderation, setup panels, dashboards — the substrate of the whole
  program.
- **You:** nothing pending beyond normal live-verification of merges.

### 8. Fleet oversight site (websites — SHIPPED and live)
- **What:** a web control-plane over the whole fleet: per-repo readiness board (18
  lanes — rulesets, required checks, secrets, auto-merge), cross-repo journal +
  decision browser. Merge-to-main = deploy on its own Railway project.
- **Also in the repo:** rebuilt versions of superbot's two public sites (botsite +
  dashboard), waiting on cutover.
- **You:** (a) provision a Postgres on Railway + set `DATABASE_URL` (turns on the
  moderated /submit intake), (b) mint a fine-grained GitHub PAT as `GITHUB_TOKEN`
  (the fleet board currently crawls at the anonymous rate limit), (c) the **cutover
  decision** — retire superbot's old dashboard/botsite in favor of these
  (recommendation on file: go — but it retires live surfaces, so it's yours).

## The rebuild program (production-bound, not yet cut over)

### 9. superbot-next — the rebuilt bot
- **What:** ground-up rebuild of SuperBot on the kit foundation: 41 subsystems, 276
  commands, all seven port bands built, boots against real PostgreSQL as a test bot
  ("Galaxy Bot"), continuously verified against the old bot's recorded behavior
  (212/212 golden parity green).
- **You:** nothing blocking today — the token cutover (CUT-3) is a later, flagged
  tier. Two friction clicks help the lane: relax the require-up-to-date rule (or
  merge queue), and an API key envelope when you want live-AI evidence. **The Codex
  review (prompt 1) is the most valuable next quality input.**

### 10. superbot-plugin-hello — the plugin contract example
- **What:** the minimal "hello world" plugin proving games can live in their own
  repos and plug into superbot-next. The repo exists but is **empty**; the seed
  package is built and sitting in superbot-next's tree.
- **You:** I attempted the seed push 2026-07-11; the safety classifier requires your
  live word for cross-repo publication. **Say "push the plugin seed" in a session
  and it's done** — this also unblocks superbot-idle (below).

## Game engines waiting on the plugin contract

### 11. superbot-idle — idle game engine + 12 themes (superbot-idle)
- **What:** a complete idle/incremental game (generators → currency → upgrades →
  prestige, exact offline progress) where the entire theme is a data file — 12 themes
  shipped (egg farm, space colony, potion brewery, dragon hoard…). 827 tests green.
  A server owner will eventually pick a theme on the website before inviting the bot.
- **You:** nothing — it's cleanly parked until the plugin contract (#10) exists.

### 12. superbot-games — mining/fishing/exploration engines + D&D design (superbot-games)
- **What:** the deterministic game-world engines for the rebuilt bot, all
  player-visible content moved into swappable data tables (re-skinnable), plus a
  designed (not yet built) AI-DM D&D story game.
- **State today:** I merged its 4 clean PRs (#34/#36/#46/#47) this session; the last
  3 (#38/#32/#27) have conflicts its own next wake rebases. No click needed.

### 13. superbot-mineverse — the mining game in your browser
- **What:** a web page where players watch (later steer) their real superbot miners.
  Runs today in read-only demo mode: `python3 server/app.py` → localhost:8000.
- **You:** six env vars (Discord OAuth + signing keys) turn on sign-in and writes —
  **but run the Codex security review (prompt 3) first, then provision.** Also: make
  `pytest` a required check there (a PR once auto-merged 28s before tests finished).

## Research & infrastructure

### 14. trading-strategy — honest quant research (trading-strategy)
- **What:** a backtesting lab with unusual discipline: pre-registered protocols,
  one-shot holdout (now spent), every negative documented. Final verdict: **no
  strategy cleared significance** — which is the honest, valuable result. A paper
  lane (no real money, ever) now runs forward; first grading 2026-07-17.
- **You (decision, not click):** whether to authorize *drafting* a new pre-registered
  protocol for the 5 surviving dev-candidates on post-2026 data. Recommendation: yes
  — drafting is free and nothing runs on a yes alone.

### 15. substrate-kit — the thing that builds all of this (substrate-kit)
- **What:** the portable agent-working-system: one file planted into any repo gives
  agents binding docs, session discipline, checkers, hooks, and a benchmark lab that
  measures whether the kit actually helps. 7 repos run on it; v1.11.0 is the sixth
  release in ~2 days.
- **You:** ratify-or-reject PR #181 (one click, it's parked for exactly that);
  the required-check swap in its settings; and the MIT-license one-worder when
  you want it public.

### 16. idea-engine + sim-lab — the fleet's brain and its lie detector
- **What:** idea-engine generates and grooms ideas fleet-wide (147 PRs in 14h) and
  routes the build-worthy ones to sim-lab, which settles them with seeded
  simulations and formal verdicts (8 verdicts shipped — e.g. proof the mining
  encounter cap can't be farmed past 6/hr). Together they're the autonomous
  idea→evidence loop.
- **You:** nothing structural. sim-lab wants its `harness-v0.1.0` tag pushed (agents
  403 on tags) and a Codex-capacity decision for its external-reviewer step.

### 17. fleet-manager — the manager (fleet-manager)
- **What:** the coordinator's repo: machine-generated fleet roster each wake, orders
  inbox, owner queue, findings. It ran the relay that merged your self-review order
  into all 14 lanes today.
- **You:** the **HOT item 16** — land the corrected merge-authority clause in
  `projects/UNIVERSAL.md` (owner-provenance text; verbatim paste block in
  `docs/owner-queue.md` item 16) together with the PR #47 permissions fold. This
  single paste ends the fleet's nightly merge-stall class.

### 18. codetool-labs ×3 — envdrift, mdverify, cfgdiff (parked)
- **What:** three small finished developer CLIs from the model-comparison
  experiment: env-drift detector, markdown verifier, config differ. mdverify's
  releases are live; envdrift + cfgdiff wait on your tag/release clicks (details in
  the owner queue, Parked section).

---

## The distilled "only you" list (2026-07-11, deduped, priority order)

1. **Anthropic email #2 + Matt interview — before Tue 7/14** (the standing top item).
2. **Revenue sitting (~30 min):** Stripe test keys → publish membership-kit,
   template-packs, test-kit → publish the gotcha article (starts the validation
   clock). Ideally after Codex prompt 2 comes back clean.
3. **Fleet-manager item 16 + PR #47:** the UNIVERSAL.md merge-clause paste
   (owner-provenance) — the single highest-leverage fleet fix.
4. **One-click unblocks:** product-forge Pages toggle · substrate-kit #181 ratify ·
   lumen-drift v1.3 Release · sim-lab tag · "push the plugin seed" (one word to me).
5. **Settings sweep (one sitting, ~10 min):** allow-auto-merge + required checks on
   venture-lab / trading-strategy / mineverse (`pytest`) / pokemon (`ROM builds`);
   kit required-check swap + auto-update-branches; superbot-next ruleset relax;
   branch-delete sweeps (agents 403 on all of these).
6. **Playtests (taste, whenever):** pokemon 6-patch verdict pass + Match Call
   one-worder; Lumen Drift graze feel.
7. **Decisions with recommendations on file:** websites cutover (rec: go) ·
   trading protocol draft (rec: yes) · kit MIT/public/Railway items · the paste
   wave (owner-queue item 13, gated on item 16/PR #47 landing first).

Decided FOR you this session (Q-0240 decide-and-flag — veto anytime):
- Merged superbot-games #34/#36/#46/#47 (your in-chat merge authorization).
- gba Track B concept: continue deepening/releasing Lumen Drift (was already the
  running default + the standing recommendation).
- pokemon concept ask is redundant — you already ruled QoL+ (Q-0262.7); lane should
  retire its OWNER-ACTION 2.
- Codex review targets: superbot-next, venture-lab, superbot-mineverse,
  substrate-kit (rationale in the prompts doc header).
