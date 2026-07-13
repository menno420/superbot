# Fleet reading path — multi-repo orientation for new sessions

> **Status:** `reference` — the canonical cross-repo reading route. **Provenance:** owner
> directive **Q-0272** (2026-07-12, in-session): *"all repos except the pokemon mod lab are
> public, so you can view any file just as easily as you could view superbot"* + *"make sure
> there is a properly suggested multi repo reading path for new sessions, so that we can save
> 3 turns of discovery."* This doc is that path. **Kit-graduation candidate:** the pattern
> (per-repo copy naming *its* siblings) belongs in the substrate-kit templates so every fleet
> repo carries its own; until then this is the hub copy.

## 0 · The standing authorization (what saved-turns hinge on)

**Read-only cross-repo access is standing-authorized for every session in this repo** — do
not burn turns re-deriving whether you may look:

- Every fleet repo is **public except `pokemon-mod-lab`** (DARK — skip, never guess).
- The sanctioned read mechanics (none is api-gated, none needs `add_repo`):
  `https://raw.githubusercontent.com/menno420/<repo>/main/<path>` · `git clone` (public) ·
  `git ls-remote` (HEAD pins). Set a real User-Agent on scripted fetches (Cloudflare 403s
  urllib's default on some hosts — the mineverse #45 lesson).
- **`api.github.com` is proxy-403 for sibling repos in hub sessions** (measured 2026-07-13,
  five survey agents independently) — don't burn turns on REST list endpoints. Derive PR
  state from `git ls-remote 'refs/pull/*/merge'` probes + the repo's own control/heartbeat
  records instead; label anything you can't derive that way "unverified", never guess.
- **Boundaries that stand:** GitHub **MCP** calls stay scoped to the session's attached
  repo(s); **writes** stay in your own repo — cross-repo *work* routes via the fleet-manager
  inbox (ORDERs), never direct pushes; `add_repo` + clone remains the path for **deep/audit**
  work in a sibling (see `AGENT_ORIENTATION.md` § "Auditing / verifying a sibling EAP Project
  repo").

## 1 · The one command

```bash
python3.10 scripts/fleet_status.py            # per-seat heartbeat table (active seats)
python3.10 scripts/fleet_status.py --all      # + parked/archived long tail
python3.10 scripts/fleet_status.py --repo X   # one repo's status.md in full
python3.10 scripts/fleet_status.py --save DIR # keep the raw files for deep reading
```

It fetches each seat's `control/status.md` (+ the manager's roster and owner-queue), parses
the conventional header (`updated / phase / health / blockers`), and flags `⚑` owner-asks.
That table **is** Tier 1+2 below — run it before asking "what's the fleet doing?".

## 2 · The repo map (who is who)

| Repo | Seat | What it is / its truth files |
|---|---|---|
| `superbot` | hub (this repo) | Prod Discord bot + the fleet's memory. Truth: `docs/current-state.md` (no heartbeat file). |
| `fleet-manager` | Project Manager | Registry `projects/<seat>/{instructions,coordinator-prompt,failsafe-prompt}.md` + `UNIVERSAL.md` · `docs/roster.md` (generated) · `docs/owner-queue.md` (six-field, OQ- slugs) · `control/inbox.md` ORDERs · `docs/capabilities.md` (fleet walls master). |
| `idea-engine` | Ideas Lab (generate) | `ideas/**` one file per head · probe battery in README · blueprints (e.g. the makerbench gift blueprint under `ideas/venture-lab/`). |
| `sim-lab` | Ideas Lab (verify) | `sims/<slug>/` one subtree per verdict · verdicts V001… · validity gate in README/CONVENTIONS. |
| `venture-lab` | Venture Lab | Products + listings + publish queue; revenue evidence. |
| `trading-strategy` | Venture Lab (parked) | Research toolkit; weekly Friday grading only. |
| `superbot-next` | SuperBot 2.0 | The rebuild. `control/status.md` carries the parity program state (ported rows, gate/report split, parked-PR list); plugin contract `docs/game-plugin-contract.md`. |
| `superbot-mineverse` | SuperBot World (flagship) | Mining browser game. Its `control/status.md` **also carries the games/idle cross-repo notes** + the FLAG 1/2 spec pointers. |
| `superbot-games` / `superbot-idle` | SuperBot World | Engines/themes. **Their status files are FROZEN archives** — current World state lives in mineverse's heartbeat. |
| `substrate-kit` | Self Improvement | The portable kit every seat runs on; templates + CHANGELOG (release ~daily — pin tags, never HEAD). |
| `websites` | Websites | Control plane + review site + arcade; `docs/owner/OWNER-ACTIONS.md` is its ask ledger; merge=deploy to four Railway services. |
| `gba-homebrew` | Game Lab | GBA homebrew; `docs/PLATFORM-LIMITS.md` is its walls file. |
| `curious-research` | Curious Research (9th seat) | Maker/3D-print research + the friend gift studio; public, raw-readable (verified 2026-07-13); heartbeat `control/status.md`, reports in `control/outbox.md`. |
| `pokemon-mod-lab` | Game Lab (dark) | **PRIVATE** — skip, never guess. |
| `product-forge` · `superbot-plugin-hello` · `codetool-lab-*` · `mobile-lab` | long tail | On-demand incubator · plugin example (near-empty) · archived CLIs · parked. `--all` sweeps them. |

## 3 · Tiered reading path (spend turns by task depth)

- **Tier 0 — hub-only task:** superbot's own boot order (`.claude/CLAUDE.md` →
  `collaboration-model` → `current-state` → journal). No cross-repo reads needed.
- **Tier 1 — "what's the fleet doing?":** `fleet_status.py` table + the manager's
  `docs/owner-queue.md`. One command + one file.
- **Tier 2 — acting on/with a seat:** that seat's full `control/status.md` (`--repo X`),
  its `⚑` blocks, its `docs/CAPABILITIES.md` / walls file, its open PRs
  (`git ls-remote` / raw PR pointers in the heartbeat — MCP only if the repo is attached).
- **Tier 3 — deep dive:** the named files a heartbeat points at (blueprints, specs, plans) —
  fetch exactly those, not the tree. For write/audit depth: `add_repo` + clone (orientation
  route § cross-repo audit).

## 4 · Truth rules (carry these into every cross-repo read)

1. **Heartbeats are dated snapshots** — `updated:` tells you how stale; verify load-bearing
   claims at HEAD (`git ls-remote`, a fresh raw fetch) before acting (Q-0120; "expect X, or
   later").
2. **Frozen archives mislead:** games/idle statuses are archives by design; World truth rides
   mineverse's heartbeat (its "CROSS-REPO NOTES" section).
3. **One writer per file:** never edit a sibling repo's control-bus files from here — inbox is
   manager-written, status is that seat's coordinator-only. Route work as a manager ORDER.
4. **⚑ blocks are the owner interface** — read them before inventing an owner-ask; the
   canonical queue is fleet-manager `docs/owner-queue.md`.

## 5 · Why this exists (the incident)

On 2026-07-12 an owner-live hub session spent ~3 turns re-discovering that (a) the fleet is
readable, (b) raw reads are the sanctioned mechanism, and (c) which files carry seat truth —
knowledge every prior fleet doc *implied* but no orientation surface *stated as a route*.
The owner directed this doc + `scripts/fleet_status.py` + the boot-path pointers as the fix
(Q-0272). If this path saves you the same turns, the fix worked; if you find it stale, correct
it in place — it is orientation, and orientation is first-class work.
