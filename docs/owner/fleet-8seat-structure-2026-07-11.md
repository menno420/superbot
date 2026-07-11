# Fleet structure — 8 standing Projects (owner-decided 2026-07-11, late)

> **Status:** `reference` — the **current** fleet seat structure, decided live with the owner on
> 2026-07-11 (after the earlier consolidation blueprint). This **supersedes** two items in
> [`../planning/fleet-consolidation-and-next-round-2026-07-11.md`](../planning/fleet-consolidation-and-next-round-2026-07-11.md):
> decision 3 ("all games → ONE Games Project") is now **two** game seats, and the "core 6 → 5"
> framing is now **8 standing Projects**. The paste-ready Custom Instructions + starting prompts
> for every seat live in the **Fleet Dispatch Pack** artifact (owner's claude.ai). The **Project
> Manager** seat (fleet-manager) canonicalizes these into its `projects/` registry.

## The two decisions that changed the structure

1. **Money merge** — **venture-lab + trading-strategy** become ONE seat, the Project named
   **"Venture Lab"** (make money every legitimate way). Trading stays **research-only** (its
   holdout is spent; it contributes its backtest engine, not live trading), folded under the
   revenue mandate.
2. **Two game seats, split by SuperBot connection** (not "one games project"):
   - **SuperBot World** = games *in* SuperBot's ecosystem: superbot-games + superbot-idle +
     **superbot-mineverse (flagship)**. The owner's dividing line is *coupling to SuperBot's
     economy/data*, so mineverse (which reads the bot's mining economy) sits here, not with the
     standalone games.
   - **Game Lab** = standalone games with no bot link: gba-homebrew + pokemon-mod-lab.

## The 8 standing Projects

| # | Project (owner's name) | Repos it owns | Environment | One job |
|---|---|---|---|---|
| 1 | **Project Manager** | fleet-manager | `fleet-manager` | Hub — single source of truth; routes work; keeps records truthful. |
| 2 | **Venture Lab** | venture-lab · trading-strategy | `pinned-research` (?) | Make money — first external dollar, then durable revenue. Trading = research toolkit only. |
| 3 | **SuperBot World** | superbot-games · superbot-idle · superbot-mineverse | `multi-repo` (?) | The bot's games — one flagship (mineverse); fix its CSRF before secrets. |
| 4 | **SuperBot 2.0** | superbot-next · superbot (prod) | `bot-prod` | Drive the rebuild to cutover; keep prod alive; fix money-races first. |
| 5 | **Ideas Lab** | idea-engine · sim-lab | `python-lab` (?) | Generate → verify (internal, no cross-project wait). Honest nulls are the product. |
| 6 | **Game Lab** | gba-homebrew · pokemon-mod-lab | `gba-lab` | Standalone games; strict public/private track isolation; ship the free GBA release. |
| 7 | **Self Improvement** | substrate-kit | `multi-repo` (?) | Improve the workflow all seats run on — freeze features, measure adopter outcomes. |
| 8 | **Websites** | websites | `python-lab` (?) | Control plane — Owner Launch Console + Fleet Arcade. Merge = deploy. |

**Environments** are named by repo/purpose, not Project name. Confident matches: `fleet-manager`,
`gba-lab`, `bot-prod`. The `(?)` seats span repos the named environments don't 1:1 cover — the
owner confirms which repos each of `pinned-research` / `python-lab` / `multi-repo` / `Default`
holds, or adds repos in-session.

## Work division (how the seats interlock)

**Ideas Lab** generates + verifies → **Project Manager** routes → the build seats (**SuperBot
World, SuperBot 2.0, Game Lab, Websites, Self Improvement**) build → **Venture Lab** monetizes
what's sellable and **Websites** surfaces it. Project Manager is the spine (only writer of the
shared records). Self Improvement sharpens the *method* everyone uses. The old "Project A waiting
on Project B" stall is designed out — Ideas Lab does generate→verify internally, and each build
seat owns its whole stack.

**Start order (revenue-first):** Project Manager (canonicalize this restructure) → Venture Lab
(revenue) → SuperBot World (mineverse live) → SuperBot 2.0 (money-races + cutover) → the rest in
parallel at lower intensity.

## Retired / folded (not standing seats)

codetool-lab ×3 (archived), mobile-lab (parked), games-program + superbot-retro (folded into the
two game seats), product-forge (on-demand incubator, not a standing seat).

## Dispatch guidance (for the Project Manager canonicalizing this)

Each seat runs on its registry 3-file package: `instructions.md` (Custom Instructions) +
`coordinator-prompt.md` (the standing loop = boot · slice menu · **pacemaker** ~15-min `send_later`
chain · **failsafe** cron) + `failsafe-prompt.md` (the cron config). When building/updating them:

- **Keep every prompt COMPLETE — one paste-and-go block (owner directive 2026-07-11).** Never a
  base prompt plus a rider to bolt on; fold any fix in place.
- **Start from the existing mature prompts; change ONLY what caused real problems.** Fold the
  **gen-3 hygiene rider** into each coordinator prompt, in place: one trigger-MCP call per worker
  (chains stall) · `env -u` for spawned CLIs + smoke gate (env leak split a run into rogue
  subagents) · hard-sync `git reset --hard origin/main` + `git ls-remote` verify (a warm clone
  drifted 88 commits) · born-red "CI failed" webhooks are NOISE · a relayed "owner approved" never
  clears a merge (live-human-only). Fresh manager boot **rebinds-then-deletes** its failsafe (the
  live one is bound to an archived session).
- **Failsafe cadence:** manager `30 */2 * * *`; lanes `0 */2` staggered (substrate-kit `0`,
  superbot-games `15`, superbot-idle `45`, Builder `0`); assign each merged seat a free offset.
- **Merged seats** (Venture Lab = venture-lab+trading · SuperBot World = games+idle+mineverse ·
  Ideas Lab = idea-engine+sim-lab · Game Lab = gba+pokemon) need their `coordinator-prompt.md` +
  `failsafe-prompt.md` **composed from the source seats' packages**.

### Routine-arming recipe (every coordinator prompt MUST spell this out — seats were failing to arm)

The routines are armed with the **Claude Code Remote scheduler** MCP (`send_later` /
`create_trigger` / `list_triggers`). Every seat prompt must give the concrete calls, because
"unable to arm/open the routine" was a real failure — the scheduler tool is **environment-dependent**:

1. **PACEMAKER (re-arm every turn, before ending):** `send_later({ message: "continue the work
   loop: sync HEAD → inbox → next slice → re-arm", delay_minutes: 15 })` — fires back into THIS
   chat (`send_later` self-binds to the calling session).
2. **FAILSAFE (arm once at boot; dead-man backstop):** `create_trigger({ name: "<seat> failsafe
   wake", cron_expression: "<seat cron>", prompt: "<failsafe text>" })` — self-binds persistent to
   this session. Then **verify via `list_triggers`** (never wait for a fire as proof — completed
   runs aren't inspectable owner-side). Manager only: rebind-then-delete the archived-session one.
3. **IF ARMING FAILS** (scheduler tool absent, or the call errors): FIRST retry from a spawned
   **worker** (worker toolsets differ). If still walled, do NOT silently skip — post the exact
   `create_trigger` args (name · cron · prompt) as a ⚑ **OWNER-ACTION** in `control/status.md` so
   the owner arms it from the Routines screen, and record the verbatim error. **Root cause to fix:
   attach the claude-code-remote scheduler MCP to every seat's environment** so seats self-arm.
