# Feature completion — certifying S1 bot units "done-done"

> **Status:** `reference` — the system definition + convention for completion certification.
> The **completion ledger** below is a living index (updated as units are assessed / certified);
> **source code and merged PRs win** over any certificate. Owner decision **Q-0209** (2026-06-27).

## What this is — and how it differs from production-readiness

A way to mark a part of the bot **complete** — *feature- and UX-complete*: it has every function it
should, the right buttons in the right places, it works as intended, and it is the most convenient
version of itself. And a way to **prove and show** that, instead of asserting it.

This is a **different axis** from [`docs/planning/production-readiness/`](../production-readiness/README.md):

| Axis | Question it answers | Tiers / states | Home |
|---|---|---|---|
| **Production-readiness** | Is it *safe / hardened*? (won't lose money, won't leak, has regression guards) | P0 integrity · P1 correctness · P2 drift | `production-readiness/*` maps |
| **Feature completion** *(this)* | Is it *feature- & UX-complete*? (all functions · right buttons · most convenient · works as intended) | `▢ unassessed` → `◐ assessed` → `✔ certified` | this directory |

The two are **orthogonal**. A game can be 100% money-safe (readiness ✔) yet still be missing buttons
(completion `◐`). A unit is "done-done" only when it is high on **both** — readiness covers the
*floor* (it won't hurt anyone), completion covers the *ceiling* (there's nothing left to add or
move). This layer is the ceiling.

The completion axis **ends in the owner's judgment**: "right buttons / most convenient / works as
intended" is a human call, so certification requires the maintainer's sign-off (see the state
machine).

## The unit = one registry entry

The completable unit is **one user-facing feature** — one game, or one server function — keyed to
its entry in `disbot/utils/subsystem_registry.py`. That registry is the immutable spine (the list of
units); completion **state** is a *living* property, so it lives **here**, keyed by registry key —
never inside the frozen registry.

Out of scope for this ledger (tracked elsewhere, do not duplicate):

- **Knowledge domains** — BTD6 (sector **S2**, its own readiness map + folio) and Project Moon — are
  tracked under their own sector/folio, not certified here. See `docs/subsystems/btd6.md`.
- **Routing-only hubs / dev-internal** subsystems (`games`, `community`, `server_management` as a
  pure hub, `ux_lab`, `general`, `four_twenty`) are infrastructure, not standalone certified units.

## Definition of Complete (the rubric)

"Complete" needs a concrete, checkable definition, or it is just vibes. There are **two** rubrics,
because *complete* means different things:

- **Games** → [`rubric-game.md`](rubric-game.md)
- **Server functions** → [`rubric-server-function.md`](rubric-server-function.md)

Both are grounded in the standards that already encode "the right buttons in the right places":
[`command-integration-standard`](../../building-roadmap/command-integration-standard.md),
[`hub-ui-standard`](../../building-roadmap/hub-ui-standard.md), and
[`config-input-standard`](../../building-roadmap/config-input-standard.md).

## State machine + evidence

| State | Meaning | What it takes |
|---|---|---|
| `▢ unassessed` | No certificate yet | (default for every unit) |
| `◐ assessed` | Scored against the rubric; **gaps listed** as a punch-list | a certificate file under [`units/`](units/) with the rubric filled in + an explicit gaps list |
| `✔ certified` | Owner-signed complete | every rubric item ticked **or explicitly waived-with-reason** · green tests for the loop + edges · a recorded **live walkthrough** (verify-bot boot + scripted click-through + screenshots) · **owner ✔** |

The leap to `✔ certified` requires **evidence you can point at** — that is the "prove and show it"
half the project was missing. The agent assembles the filled rubric + tests + walkthrough and hands
the owner either a punch-list or a ✔-ready packet; the **owner gives the final ✔** (owner decision
Q-0209: *evidence + owner sign-off*).

A certified unit is **not frozen** — a later regression, or a new best-in-class bar, reopens it to
`◐`. "Complete" means "nothing left we'd add or move *today*," recorded with its date + evidence.

## Completion-first policy (soft default)

The reason to certify completeness is to **finish what exists before starting what doesn't.** As a
**soft default** (owner decision Q-0209):

- Work that **completes or deepens an already-started unit** is **in-scope and prioritized** — this
  includes a new idea *directly related* to an existing game/function (a variant, a depth layer, a
  missing action). That is *deepening*, not new.
- An idea for a **brand-new unit** is still captured in `docs/ideas/` — but **parked behind a
  completion gate** by default. The owner can greenlight one at any time.

This is a *soft* bias, not a freeze: it steers sessions toward certification without blocking the
owner's explicit "build this new thing." Wired into the promotion path,
[`docs/ideas/README.md`](../../ideas/README.md) § "Completion-first gate."

## Completion ledger

Legend: `▢` unassessed · `◐` assessed (punch-list open) · `✔` certified (owner-signed). The `State`
column uses the bare word; the scoreboard below is generated from it.

<!-- COMPLETION_SCOREBOARD:START (generated by scripts/completion_scoreboard.py) -->
**36 units · 0 certified (0%) · 36 assessed · 0 unassessed.**

| Completion | Units | Share |
|---|---:|---:|
| ✔ certified | 0 | 0% |
| ◐ assessed | 36 | 100% |
| ▢ unassessed | 0 | 0% |
| **Total** | **36** | **100%** |

> _Generated by `scripts/completion_scoreboard.py` from the ledger tables below. **Certified %** is the headline “done-done” number — the share of S1 units the owner has signed off as feature-complete._
<!-- COMPLETION_SCOREBOARD:END -->

### Games — competitive

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Blackjack | game | competitive | assessed | [cert](units/blackjack.md) |
| Casino (poker) | game | competitive | assessed | [cert](units/casino_poker.md) |
| Deathmatch | game | competitive | assessed | [cert](units/deathmatch.md) |
| RPS / tournament | game | competitive | assessed | [cert](units/rps_tournament.md) |

### Games — activity / idle

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Mining | game | activity | assessed | [cert](units/mining.md) |
| Fishing | game | activity | assessed | [cert](units/fishing.md) |
| Chicken farm | game | activity | assessed | [cert](units/farm.md) |
| Creatures | game | activity | assessed | [cert](units/creature.md) |
| Counting | game | activity | assessed | [cert](units/counting.md) |
| Word chain | game | activity | assessed | [cert](units/chain.md) |

### Moderation & safety

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Moderation | server-fn | moderation | assessed | [cert](units/moderation.md) |
| Cleanup | server-fn | moderation | assessed | [cert](units/cleanup.md) |
| Automod | server-fn | moderation | assessed | [cert](units/automod.md) |
| Image moderation | server-fn | moderation | assessed | [cert](units/image_moderation.md) |
| Security | server-fn | moderation | assessed | [cert](units/security.md) |
| Proof channel | server-fn | moderation | assessed | [cert](units/proof_channel.md) |

### Economy & progression

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Economy | server-fn | economy | assessed | [cert](units/economy.md) |
| Inventory | server-fn | economy | assessed | [cert](units/inventory.md) |
| Treasury | server-fn | economy | assessed | [cert](units/treasury.md) |
| XP & levels | server-fn | progression | assessed | [cert](units/xp.md) |
| Karma | server-fn | progression | assessed | [cert](units/karma.md) |
| Leaderboards | server-fn | progression | assessed | [cert](units/leaderboard.md) |

### Community

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Welcome | server-fn | community | assessed | [cert](units/welcome.md) |
| Support tickets | server-fn | community | assessed | [cert](units/ticket.md) |
| Community spotlight | server-fn | community | assessed | [cert](units/community_spotlight.md) |
| Counters | server-fn | community | assessed | [cert](units/counters.md) |

### Server management

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| Roles | server-fn | management | assessed | [cert](units/role.md) |
| Channels | server-fn | management | assessed | [cert](units/channel.md) |
| Setup wizard | server-fn | management | assessed | [cert](units/setup.md) |

### Platform & meta

| Unit | Type | Family | State | Certificate |
|---|---|---|---|---|
| AI assistant | server-fn | platform | assessed | [cert](units/ai.md) |
| Logging | server-fn | platform | assessed | [cert](units/logging.md) |
| Settings | server-fn | platform | assessed | [cert](units/settings.md) |
| Diagnostics | server-fn | platform | assessed | [cert](units/diagnostic.md) |
| Utility | server-fn | platform | assessed | [cert](units/utility.md) |
| Help | server-fn | platform | assessed | [cert](units/help.md) |
| Admin | server-fn | platform | assessed | [cert](units/admin.md) |

## How to use it

**Assess a unit (`▢ → ◐`)** — pick a unit, read its rubric, read its source (the folio + the unit's
cog/views/service), and fill a certificate under [`units/<key>.md`](units/) from the rubric template.
Every unticked item becomes a **punch-list** line. Flip the ledger `State` to `assessed`, link the
cert, and run `python3.10 scripts/completion_scoreboard.py --write`.

**Certify a unit (`◐ → ✔`)** — clear the punch-list, add/confirm tests for the loop + edges, record
a **live walkthrough** (`/verify-bot` boot + a scripted click-through + screenshots), and present the
packet to the owner. On the owner's **✔**, flip `State` to `certified`, stamp the cert with the date
+ evidence links, and re-run the scoreboard.

**Each completion certificate** carries: the unit + registry key, the rubric type, the filled rubric,
the punch-list (open gaps), evidence links (tests · walkthrough), and the current state + date.

## What this is NOT

- **Not the production-readiness maps.** Those are the *risk/hardening* axis (see the table up top).
  A unit needs both; this is the completeness ceiling, that is the safety floor.
- **Not a new source of truth for the unit list.** The spine is the subsystem registry; this ledger
  references it. The **registry↔ledger parity guard**
  (`python3.10 scripts/check_completion_ledger_parity.py --strict`) enforces this: every certifiable
  registry subsystem (registry minus the documented routing-only / knowledge-domain exclusion set) has
  exactly one ledger row + a `units/<key>.md` cert, and every cert maps to a live registry key (or the
  documented non-registry `setup` exception).
- **Not a hard freeze on new features.** Completion-first is a *soft* default; the owner greenlights
  new units freely.
- **Not self-certifying.** No unit reaches `✔` without owner sign-off (Q-0209).
