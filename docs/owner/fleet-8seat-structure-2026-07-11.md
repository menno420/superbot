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
