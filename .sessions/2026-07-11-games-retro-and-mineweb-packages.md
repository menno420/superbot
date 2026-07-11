# Session — round-3 games program: Retro-Games + mining-browsergame founding packages

> **Status:** `complete`
> **Run type:** owner-directed ("a few others I want to start before I sleep — at least
> the gba games and one that makes usable things, an interactable browsergame that links
> to the discord bot's mining game")
> **Model/time:** opus-4.8 · 2026-07-11

## What is about to happen

The owner is running the SuperBot Projects-EAP fleet and wants to start two more game
Projects tonight. Owner picks (AskUserQuestion this session):

1. **GBA lane → a dedicated Retro-Games studio seat spanning BOTH repos** — gba-homebrew
   (polish *Lumen Drift* → playable ROM, invent new original homebrew) + pokemon-mod-lab
   (continue ROM QoL mod patches). Fills the 3rd Q-0259 games-project slot.
2. **Browsergame → the full read-write version** — Discord OAuth → your real Discord miner
   → mine/craft/trade in the browser, persisting back to the live bot economy through the
   bot's **audited mutation seam** (never direct DB writes). New repo, its own game Project.
   Read-only frontend ships first as the safe walking skeleton; live-prod cutover behind an
   owner flag.

Deliverable: two paste-ready founding packages on the gen-3 standard (§0 clicks / §1
custom instructions ≤7,500 chars / §2 coordinator brief / §3 env / §4 boot verification),
mirroring the six existing round-3 packages; homed in the planning README.

## What happened

- **Oriented** in the normal reading order (CLAUDE.md → collaboration-model → current-state
  → journal → AGENT_ORIENTATION); read the EAP corpus (`docs/eap/README.md`,
  `fleet-manifest.md`, the 07-11 next-session brief, the two existing games packages, the
  games-theme-engine-website-first idea, the launch-pack Q-0259 rulings). Confirmed live
  state: superbot 0 open PRs, HEAD #1971; the fleet's core seats + World Games + Idle Engine
  are LIVE/BOOTED; the two retro repos and the mining-web lane are the gaps the owner named.
- **Two owner picks** (AskUserQuestion): Retro-Games studio seat over both repos; the FULL
  read-write mining browsergame.
- **Drafted two paste-ready founding packages** on the gen-3 standard, mirroring the six
  existing `round3-founding-package-*` docs:
  - `round3-founding-package-games-retro-2026-07-11.md` — the 3rd Q-0259 game Project;
    one studio seat over `gba-homebrew` + `pokemon-mod-lab`; integrity/legal floor
    (original-only homebrew · **patches-not-ROMs** for mods · reproducible builds ·
    emulator-verified "it plays"); one-PR-one-repo; ORDER 000 = a real build artifact +
    a missing-toolchain OWNER-ACTION path; failsafe `50 */2`.
  - `round3-founding-package-mining-web-2026-07-11.md` — new repo (`superbot-mineverse`);
    the **safety architecture** as the repo's reason to exist (web app never touches
    Postgres / never holds the token; reads via a versioned bot→web data contract; writes
    via a bot-side audited action endpoint routed through `mining_workflow` +
    `emit_audit_action`); five-stage ladder (read-only → read contract → OAuth → write on a
    test guild → **live behind an owner flag**, the one decision never decide-and-flagged);
    failsafe `20 */2`.
- **Homed** both in the planning README (Active plans); `check_plan_homing --strict` +
  `check_docs --strict` green.
- Opened PR #1972 born-red (Q-0133), armed auto-merge (SQUASH), subscribed to PR activity.

## ⚑ Self-initiated

- **The retro seat owning TWO writable repos** deviates from the one-writable-repo norm
  (Q-0260) — but it is owner-directed via the AskUserQuestion pick, so it's applied and
  flagged (not a self-invented rule bend). Cross-repo *writes* are still forbidden
  (one PR = one repo).
- **Read-only-first as the mining-web walking skeleton** even though the owner chose the
  full read-write target: the read contract IS the write contract's foundation and the safe
  first PR — decided-and-flagged (Q-0240); vetoable at calibration.
- **Failsafe crons `50 */2` (retro) / `20 */2` (mineweb)** chosen off the fleet's even-hour
  wake spike and clear of the taken minutes (world 15, idle 45, manager/superbot 30).

## 💡 Session idea

**A `web↔bot contract` folio + one versioned schema family** — the mining browsergame's
read/write contracts, the idle seat's setup-code provisioning format, and the part-4d data
API are all the *same discipline* (a versioned, schema-gated projection between the bot and
the web) pointed in different directions. Right now each seat is inventing its own. A single
`docs/subsystems/web-bot-contract.md` folio + a shared `contracts/` schema convention
(read = data projection, write = audited action, skin = theme/provisioning manifest — three
schemas, one gate) would let the websites, idle, and mineverse seats converge instead of
fork, and gives superbot-next one plugin-contract family to host. Dedup: the
games-theme-engine-website-first idea (§4) gestures at this for themes/provisioning but not
the read-write *game* contract; not in the roadmap. Home: a new folio flagged to the manager
for cross-lane adoption.

## ⟲ Previous-session review

The 07-11 part-4h close-out did the handoff-brief-as-a-named-doc move well (a fresh session
finds it fast) and its Q-0104 audit was thorough. What it *couldn't* do — and this session
inherited — is that the games program's "3rd project" slot (Q-0259 r.5) was left implicit:
World Games + Idle Engine filled two slots, but the third (retro/GBA + the mining-web idea)
had no founding package, so the owner had to re-open it tonight. **Improvement surfaced:**
when an owner ruling names a *count* of things to launch (here "3 dedicated game projects"),
the reconciliation/dispatch pass should track the count explicitly (2/3 packaged) rather than
leaving the remainder to be re-discovered — the same "track the target, not just the last
action" logic as the reconciliation marker. Fits the fleet-manifest as a "Q-0259 games
slots: 3/3 packaged" line.

## Documentation audit (Q-0104)

`check_plan_homing --strict` ✓ · `check_docs --strict` ✓ (the printed SUPERSEDED-banner
lines are pre-existing advisories on three *other* 07-10 packages — product-forge /
simulator / substrate-kit — superseded by their live seats; out of this session's scope,
and check_docs still reports all-passed). `check_current_state_ledger` not re-run (no merged
PR added; only benign newest-merge lag). Chat-only material swept into durable homes: the two
owner picks → the package headers + this card; the possibility-space reasoning → the mineverse
package's staged ladder; the "most advanced" framing → the session idea (web↔bot contract
family). Claim file deleted this commit.

## Handoff

Both packages are paste-ready; nothing is started until the owner does the §0 clicks. Owner
path tonight (also given in chat):
- **Retro Games:** create env `superbot-retro` attaching both repos (retro toolchain, not
  plain python-lab) → create the Retro Games Project → paste retro §1/§2. Keep
  pokemon-mod-lab PRIVATE.
- **Mining Browsergame:** create an EMPTY public repo (`superbot-mineverse`) → tell the
  dispatch chat (copilot seeds) → settings (auto-merge + `substrate-gate`) → env
  `superbot-mineverse` (no vars at boot) → create the Mining Browsergame Project → paste
  mineverse §1/§2.
Both seats self-verify at boot per their §4 and open a Runbook §5 row. The mineverse seat
will ⚑ the bot lane for the read-projection + the audited action endpoint (cross-repo work
the manager routes). Live-prod for mineverse is the owner's flag, never the seat's.

