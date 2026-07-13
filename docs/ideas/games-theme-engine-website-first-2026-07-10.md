# Games program: theme-engine architecture + website-first provisioning

> **Status:** `ideas` — owner-raised and owner-shaped (2026-07-10, round-3 dispatch
> part-4e; provenance router **Q-0267**, owner's words verbatim there). This file is the
> expanded design the owner asked for ("can you expand and improve on my ideas") — the
> input to the two games founding packages and the manager's conformed mapping.

## The owner's frame (decided, not proposed)

1. **Seat A — one Project on `menno420/superbot-games`** (the repo where exploration and
   mining already live, both gen-1 lanes terminal): the whole **world ecosystem** —
   exploration + mining + **fishing** + anything world-adjacent. Gen-2 merges the two
   former lanes into one seat.
2. **Seat B — a new repo + Project for the egg-farm idle game**, built **template-first**:
   the deliverable is templates/themes, eventually **choosable before the bot is even
   invited**.
3. **Website-first onboarding:** you go to the website first, select which features you
   want, then invite a bot that arrives already configured.
4. **Core/skin split:** the game core stays the same; different **theme skins** ship over
   it so every Discord server can have an idle game matching its own theme.

## 1. Theme packs are data, not code — the load-bearing seam

Split every themeable game into:

- **Core** (code, owned by the game seat): state machines, economy math, persistence
  schema, command surface, balance tables, tick/offline-progress logic. Fixed across all
  servers.
- **Theme pack** (one data file, no code): display names, emoji, item/creature/building
  names, flavor strings, embed colors, art URLs, and *optionally* bounded balance
  multipliers (validated ranges only, so a theme can feel different without breaking the
  economy). `themes/<name>.yaml` against a published **theme-manifest schema**.

Consequences worth designing for from day one:

- **Theme-gate CI:** a schema validator (every required slot filled, strings within
  length caps, multipliers in bounds) makes shipping a theme merge-on-green — no human
  review of mechanics needed because a theme *cannot touch* mechanics.
- **Volume-first payoff (Q-0266):** once the core is stable, theme packs are
  mass-producible by agents at near-zero risk. The idle seat's backlog never runs dry —
  "produce 10 more themes" is always a valid, correct slice. This is the single best
  populate-phase fit in the whole games program.
- **One shared manifest format, not per-game:** the world game gets the same treatment
  later (mining → asteroid-mining skin, fishing → void-fishing). The theme contract is
  therefore **plugin-contract material**, not idle-repo-internal (see §4).

## 2. Egg farm = the first theme of an idle ENGINE, not the game itself

Name the seat/repo for the engine (suggest `superbot-idle`), and make the egg farm
`themes/egg-farm.yaml` — the flagship default. The engine models the genre loop once:

    generators → currency → upgrades → prestige/rebirth → collections/achievements
    (+ offline progress, timed boosts, occasional events)

All nouns in that loop are theme slots. Candidate follow-on themes proving the seam
(each one small enough for a single slice): space mining colony · potion brewery ·
cyber server-farm · bakery · kingdom builder · crystal cavern (cross-flavors with the
world game) · zoo. A server picks its theme; two servers running different themes are
mechanically identical — support, balance, and bugfixes stay ONE codebase.

## 3. Website-first provisioning — the web↔bot contract's second half

The read-only **data API** (part-4d relay) is the bot→web read path. The owner's
pre-invite selection is the **web→bot write path**: a versioned **server provisioning
manifest** (features on/off + theme per game + config), exactly the
dashboard-data-contract discipline applied in the other direction.

- **Target flow:** Discord OAuth on the website → pick server → choose features +
  themes (live theme *gallery* rendered from the committed theme packs) → site stores
  the manifest → invite link → bot reads the manifest at guild join and self-configures.
- **Phase-1 shortcut (buildable now, no hosted backend):** the site generates a **setup
  code** (signed/encoded blob of the manifest); the owner runs one command
  (`!setup apply <code>`) after inviting. Same UX promise ("designed before it
  arrived"), a fraction of the infrastructure — and it validates the manifest format
  the join-time path later consumes unchanged.
- **Product story this buys:** most Discord bots configure post-join via command
  archaeology. "Design your server's game on the website, then invite it" is a real
  differentiator, and the theme gallery is its shop window.

> **Groom note (2026-07-13, mineverse FLAG 2 session):** the web→bot *write* seam this
> section presupposes now has a bot-side reference implementation — PR #2061 ships the
> HMAC-signed, idempotent, audited `POST /relay/mining/action` executor (mineverse WRITE
> contract v1, test-guild-only). A provisioning manifest write path can reuse its
> transport-auth + idempotency + audit pattern wholesale; the read half (part-4d relay)
> shipped bot-side in PR #2058. Both are held draft pending the owner's deploy.

## 4. Plugin-seam convergence (nothing new to invent)

Games already ship as **plugin packages** consumed by `superbot-next` via its
manifest/plugin contract (its ORDER 002; `superbot-plugin-hello` — owner-created
2026-07-10 — is the contract's validation repo). The owner's feature selection maps
1:1 onto that seam: **selecting features = choosing the per-guild plugin enable set;
choosing a theme = a per-guild parameter on a game plugin.** So:

- The **theme-manifest schema** belongs in the plugin-contract family. To avoid
  blocking on the Builder: the idle seat drafts v1 in its own repo and flags it for
  promotion into the contract (decide-and-flag, Q-0240).
- The provisioning manifest is then mostly *derived*: plugin enable set + per-plugin
  params. One contract family covers data API (read), provisioning (write), themes
  (skin) — three versioned schemas, one discipline.

## 5. Seat mapping + first shippables

| Seat | Repo | Scope | First shippables (volume-first order) |
|---|---|---|---|
| **World Games** | `superbot-games` (existing) | exploration · mining · fishing · shared world systems (inventory, tools, locations, encounters) | gen-2 relaunch as ONE Project (succession packages committed in-repo are the boot input) → **fishing as a pure-domain package reusing mining's encounter/energy substrate** → unified inventory/resource contract across the three |
| **Idle Engine** | new (suggest `superbot-idle`) | idle-engine core + theme system | core loop v1 → theme-manifest schema v1 + theme-gate CI → `egg-farm` theme → 2–3 more themes proving the seam → setup-code provisioning format v1 |

Both seats: gen-3 founding packages on the standard (continuous Q-0265 + volume-first
Q-0266), plugin-native against superbot-next's contract with old superbot as oracle
where old code exists (the superbot-games gen-1 method, kept).

## 6. Cross-fleet synergies (already live, just route to them)

- **sim-lab:** idle-economy balance is *numerically simulable* (progression pacing,
  prestige timing, generator cost curves). The idle seat pre-registers economy params →
  sim-lab verdicts them — the pipeline's first fully-numeric game consumer.
- **websites lane:** owns the selector UI + theme gallery; games seats own the
  manifests it renders. The part-4d data-API placement ask now has a twin (provisioning)
  — same owner, same contract family.
- **idea-engine:** theme concepts are perfect INTAKE material (cheap, data-only,
  mass-producible).

## 7. Decided-and-flagged (Q-0240 — veto at the mapping react)

1. **Plugin-native, no old-bot port** for the idle game: it isn't live in Discord until
   superbot-next hosts plugins, but it *is* buildable, testable, and sim-lab-verdictable
   now — and porting to the dying old bot would be consolidation-phase waste.
2. **Setup-code before join-time provisioning** (§3): ships the owner's UX promise
   without a hosted backend.
3. **Theme contract drafted in the idle repo, promoted later** (§4): don't serialize
   the games program behind the Builder's contract work.
4. **`superbot-idle` as the new repo name** — owner picks the final name at creation.
