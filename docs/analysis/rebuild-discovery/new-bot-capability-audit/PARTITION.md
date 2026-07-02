# Partition — 43 subsystems × 4 disjoint lanes

> **Status:** `reference`. Lanes are **file-disjoint**: each subsystem is audited by exactly one lane,
> so parallel agents never collide and outputs merge cleanly. Assign one agent (or agent-team) per lane.

## Model → lane (suggested — strongest reasoning on the hardest grammar-fit lanes)

The spike showed fit collapses on **stateful game loops** (blackjack 44%) and event-driven surfaces,
and holds on CRUD/config (logging 97%). Put the deepest reasoners where the grammar strains most:

| Lane | Domain / axis | Scope | Expected difficulty | Suggested agent |
|---|---|---:|---|---|
| **A** | Governance & Safety (Axis 1) | 11 subsystems | Medium (moderation/CRUD, capability-gated) | **Sonnet 5 ultracode** |
| **B** | Economy & Character-sim (Axis 1) | 11 subsystems | **Hard** (deep persistent state) | **Opus 4.8 ultracode** |
| **C** | Games & Community (Axis 1) | 10 subsystems | **Hardest** (blackjack 44% + stateful loops) | **Opus 4.8 ultracode** |
| **D** | Knowledge, AI & Platform (Axis 1) | 11 subsystems | Mixed (logging easy; AI-domain novel) | **Codex / deep-research** |
| **E** | Plans & Ideas (Axis 2) | `docs/planning/` + `docs/ideas/` | Medium (doc reasoning) | **Codex / Opus** |
| **F** | Ecosystem benchmark (Axis 3) | known Discord bots ↔ our domains | Open-ended (web research) | **deep-research** |
| **G** | Foundations & Runtime Skeleton (L0) | bootstrap · cog-loader · env/config · `main.py` · helper/util arch | **Hard + highest-leverage** (everything depends on it) | **Opus 4.8 / Codex** |

Lanes **A–D** cover Axis 1 (what we have); **E** covers Axis 2 (what we planned); **F** covers Axis 3
(what the ecosystem has that we don't). A–D are file-disjoint by subsystem; E and F are cross-cutting
research lanes that reference A–D's output. The 3 spike-worked manifests
(`tools/grammar_spike/manifests/`) are shared calibration for all Axis-1 lanes.

## Lane A — Governance & Safety (→ Sonnet 5)

`admin` · `server_management` · `moderation` · `automod` · `image_moderation` · `security` · `cleanup` ·
`role` · `channel` · `welcome` · `ticket`

Watch for: capability/permission gates as declarations vs. code; the setup/provisioning wizards
(`wait_for` danger-zone); audit-seam mutations (should be tier-2 handler refs).

## Lane B — Economy & Character-sim (→ Opus 4.8 #1)

`economy` · `inventory` · `treasury` · `mining` · `fishing` · `creature` · `farm` · `xp` · `casino` ·
`four_twenty` · `counters`

Watch for: **deep persistent state** (mining grid, creature battles, farm growth) — the tier-3 pressure
point; transactional multi-write mutations; leaderboards/records (LeaderboardSpec vocabulary).

## Lane C — Games & Community (→ Opus 4.8 #2)

`games` · `blackjack` · `deathmatch` · `rps_tournament` · `counting` · `chain` · `leaderboard` ·
`community` · `community_spotlight` · `karma`

Watch for: **stateful game loops** (the 44% zone) — turn/round state machines, `wait_for` interaction
loops, timers. This lane most directly tests whether the grammar needs a **game-state primitive family**
(likely a new amendment). `blackjack` + `karma` already have spike manifests — calibrate against them.

## Lane D — Knowledge, AI & Platform (→ Codex / deep-research)

`ai` · `btd6` · `project_moon` · `help` · `settings` · `logging` · `diagnostic` · `ux_lab` · `utility` ·
`general` · `proof_channel`

Watch for: the **AI/knowledge-domain** shape (KnowledgeDomainSpec — commands + data sources + context
builder + eval suite; the spike never touched this) — deep-research value here; `settings`/`logging` are
the generated-panel payoff (should be near-100% fit — confirm); diagnostics as declarative providers.

## Lane E — Plans & Ideas, Axis 2 (→ Codex / Opus)

Everything **planned or ideated** for the new bot: `docs/planning/*.md` (active plans, not `historical`)
+ `docs/ideas/*.md` (the idea backlog) + the roadmap horizons. For each item: does it still belong in the
new bot? reconsider (keep/improve/merge/drop/redesign), express its target capability in the §2 grammar,
and note whether it's **already covered** by an Axis-1 subsystem (so it's not double-counted). Output: a
forward-capability ledger — what the new bot should add that isn't shipped yet, with the optimal form.

## Lane F — Ecosystem benchmark, Axis 3 (→ deep-research)

Review our domains against **known Discord bots and their full feature sets** — MEE6, Carl-bot, Dyno,
Dank Memer, Ticket Tool, YAGPDB, Arcane, Tatsu, ProBot, Mudae, and any domain-fit others (web-research
their feature/command docs). Per domain (align to the A–D groupings): catalog what they do that **we
don't**, with a one-line "what it is + which bot(s) + would it fit our design." **Not a build list —**
a *documented known-options corpus* (owner: "known and clearly documented," integrate later). Flag each
gap as: **strong fit** (the new bot should likely have it) · **maybe** · **deliberate omission** (why we
skip it). Cite sources. This is where the repo gets "overflowing with useful data the next bot can use."

## Lane G — Foundations & Runtime Skeleton, L0 (→ Opus 4.8 / Codex)

The substrate **under** all 43 subsystems — the L0 layer the build order builds *first*, so it is the
highest-leverage lane. Audit + reconsider + optimize + benchmark (owner directive 2026-07-02 — "we
already do this, but there's room for improvement"):

- **Bootstrap / `main.py`** — is it **lean and functional**? What belongs in it vs. extracted.
- **Dynamic cog discovery + auto-load** — the skeleton must **find and load every cog dynamically, with
  NO hardcoded initial-extensions list**. Audit how we do it today (`disbot/bot1.py` + the loader),
  reconsider, and design the optimal auto-discovery (folder-scan / entry-point / manifest-driven).
- **Env + config** — loading, validation, secrets, per-environment; the config lanes' foundation.
- **Helper / util architecture** — every applicable function in its **proper** helper/util home (align to
  `docs/helper-policy.md`); flag mis-homed functions and the ideal layering.
- **Kernel / runtime** — the engine that the manifest generates *into* (the §2 grammar's host).

Benchmark against best-in-class bot skeletons (discord.py cog-loader patterns, large open-source bots).
Output feeds the build plan's **L0 layer** directly — with its production-grade done-definition and the
outperform bar. This lane is not subsystem-partitioned; it reads across `disbot/bot1.py`, `disbot/core/`,
`disbot/utils/`, and the extension/loader path.

## Coverage guarantee

**Axis 1:** 11 + 11 + 10 + 11 = **43** = every subsystem in `disbot/utils/subsystem_registry.py::SUBSYSTEMS`.
Cross-check your lane's command counts against `ground-truth/command-surface.json`; if a subsystem spans
multiple cogs (e.g. `btd6` → `btd6_*_cog.py`), audit all of them. **Axis 2:** every non-`historical`
plan + every idea file. **Axis 3:** every domain has at least one comparable known bot benchmarked.
