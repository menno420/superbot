# Fleet coordination protocol + the manager Project v2 (git-as-message-bus, 2026-07-09)

> **Status:** `plan` — the design + paste-ready materials for a single **manager Project** that is
> the owner's one control chair over the whole fleet, and a **file-based inter-Project protocol**
> (shipped in the substrate-kit) that lets Projects coordinate through committed files. Provenance:
> owner directive 2026-07-09 (this chat). Supersedes/upgrades the observe-only
> [manager brief](eap-manager-project-brief-2026-07-09.md) (v1 → v2: observe **and** dispatch).
> Grounded in the [fleet review](../eap/fleet-review-2026-07-09.md) + the lived findings in the
> [evaluation log](projects-eap-evaluation-log.md).

## 0. Goal, the validated insight, and the locked decisions

**Goal:** the owner talks to **one** Project — the manager. The manager tracks every repo, turns
the owner's intent (and the roadmap) into orders it dispatches to each Project, and surfaces back
only what needs the owner (decisions, blockers, problems). Each Project keeps its own state
current so the manager always knows what's going on.

**The insight that determines the architecture:** the EAP evaluation proved Projects **cannot talk
to each other directly** — no Project→Project channel, `SendMessage` to a session fails, a
coordinator can't reliably poke even its own children (evaluation log 2026-07-07/08). The **only**
shared medium every Project has is **committed git files**. So a file-based bus isn't one option —
it's the only mechanism that works. This protocol makes that medium a real message bus.

**Locked decisions (owner, 2026-07-09):**
- **Distributed, own-repo coordination** — each Project's `control/` files live in **its own repo**
  (not a shared hub repo). Rationale: the manager gets write on all repos *once*; each Project
  stays single-repo-simple (it already syncs+writes its own repo every session — zero new access).
  Complexity concentrates in the manager, which is built for many repos.
- **Self-poll routines** — each Project runs a routine that wakes it on a cadence to read its inbox
  and refresh its status (because writing an order file does **not** wake a sleeping Project).
- **Autonomous-director manager** — the manager keeps Projects moving on its own (decide-and-flag)
  and routes only genuinely new / risky / ambiguous calls to the owner.

## 1. The protocol (git-as-message-bus)

### File layout
Per Project, in **its own repo** (shipped by the substrate-kit on adopt):
```
control/
  inbox.md     # ORDERS to this Project. ONE writer: the manager (appends via GitHub Contents API).
  status.md    # STATE from this Project. ONE writer: this Project (overwrites each session).
```
Shared, in `superbot` (every Project already reads it; low-churn, normal docs CI):
```
docs/eap/fleet-manifest.md   # registry: every Project · repo · model · routine cadence · last-seen
```
The manager's **owner-desk** (the aggregated rollup *for the owner*) is primarily its **chat
rollup**; an optional dated snapshot can be committed to `superbot` as a normal docs PR (daily, not
per-event, to keep superbot's heavy CI quiet).

### The one rule that keeps it conflict-free
**One writer per file** — the exact lesson superbot's claim-dir already proved (Q-0195, 0% conflicts
vs ~98% for shared-append). The **manager** is the sole writer of every `inbox.md`; **each Project**
is the sole writer of its own `status.md`. Two writers never touch the same file, so there are no
cross-Project merge conflicts. Everything is **append-only / overwrite-own** — which also fits
forward-only git and the "create-but-can't-delete published state" permission wall exactly.

### `status.md` — what a Project writes every session (its heartbeat)
```markdown
# <project> · status
updated: <ISO8601>            # heartbeat — stale = the manager treats the Project as dark
phase: <what I'm doing right now, one line>
health: green | red-by-design (<why — e.g. parity born-red>) | broken (<what>)
last-shipped: #<PR> — <one line>
blockers: <what's stopping me, or `none`>
orders: acked=<ids> done=<ids>          # how I report order progress (I never edit inbox)
⚑ needs-owner: <a decision/action only the owner can give, or `none`>
notes: <anything the manager should know>
```

### `inbox.md` — how the manager delivers an order (append-only)
```markdown
## ORDER <nnn> · <ISO8601> · status: new        # manager flips new→done after seeing status.done
priority: P0 | P1 | P2
do: <the order — a POINTER to a committed doc/section + the ask, kept short>
why: <one line>
done-when: <acceptance test>
```
A Project **acknowledges + completes** orders by writing `orders: acked=… done=…` in its own
`status.md` — never by editing `inbox.md` (preserves one-writer-per-file). The manager reads the
Project's status to learn progress, then flips the order's `status:` on its next inbox write.

## 2. Substrate-kit changes (the thing every repo updates from)

The protocol ships **in the kit** so every adopting repo inherits it. New kit work (a KL band —
natural synergy with the render/engage fix the kit is already doing):
1. **`control/` scaffold in `ADOPT_PLAN`** — plant `control/inbox.md` + `control/status.md` (seeded
   skeletons) on adopt, skip-if-exists.
2. **Protocol spec template** — a generalized `control/README.md.tmpl` describing the contract
   above (roles, one-writer rule, the two file formats).
3. **A status-freshness checker** — `check_status_current.py`: warns (not reds) if `control/status.md`
   wasn't touched this session; graduates to the born-red post-adopt gate so an active repo can't go
   dark silently. (This *is* an instance of the render/engage "enforce, don't exhort" fix — the
   session-loop discipline the fresh repos skipped.)
4. **CI path-ignore for `control/`** — adopting repos' CI skips coordination-only writes (a
   `paths-ignore: [control/**]` on the heavy suites) so inbox/status churn never triggers a full run.
5. Cut a fresh kit release once it lands; adopters `bootstrap upgrade`.

## 3. The manager Project v2 (autonomous director)

The [v1 brief](eap-manager-project-brief-2026-07-09.md) is observe-only; v2 adds dispatch. Its loop:
1. **Read** every Project's `control/status.md` (GitHub `get_file_contents` — no clone). Note
   heartbeat/staleness, health, blockers, `⚑ needs-owner`, order progress.
2. **Roll up for the owner** (chat, on demand + daily): per-Project state · the **decision queue**
   (all `⚑ needs-owner`) · the live OWNER ACTIONS list · anything stuck · red-by-design vs broken.
   Lean on the `websites` control-plane board for the live signal grid; the rollup adds judgment.
3. **Dispatch:** translate owner intent + each repo's roadmap into orders → **append to each
   Project's `control/inbox.md`** via the Contents API (read-modify-write; it's the sole inbox
   writer, so no conflict). Orders are pointers to committed docs, never inline briefs (~4 KB reality
   is moot here since the manager writes files, but keep orders terse anyway).
4. **Autonomous director (decide-and-flag):** if a Project is green/idle and has roadmap work, issue
   the next order on its own; route only genuinely new initiatives / money / prod / external /
   ambiguous-intent to the owner. Silence = consent for reversible dispatches.
5. **Maintain** `docs/eap/fleet-manifest.md` (add a Project when one launches; mark last-seen).

Authority split (unchanged from v1): owner keeps product feel · money/spend · external publish ·
taste · vetoes; manager owns sequencing · which order next · when to parallelize · how to report.

## 4. The wake mechanism (self-poll routines)

Each Project gets a **routine** (Claude Code console Schedule / `create_trigger`) firing every **N
hours** into its coordinator session with a standing prompt: *"Sync; read `control/inbox.md`;
execute any `status: new` orders; then overwrite `control/status.md`."* The activation message (§5)
makes this the per-session ritual so it holds even between routine fires.

- **Cadence:** start ~**every 2–4 h** while a Project has live work; the manager can recommend
  pausing a Project's routine when it's idle (the hybrid cost posture) — decide-and-flag.
- **Cost:** each wake spends usage; before Friday's free window that's free, after it's metered —
  the manager reports the observed draw and the owner tunes cadence.
- **Owner setup:** scheduling tools gate owner-side in every permission mode (evaluation log
  2026-07-08), so **the owner clicks to create each routine** — pre-loaded on OWNER ACTIONS.

## 5. Activation messages (paste-ready)

### 5a. Generic — send to EVERY build Project (fill `<project>`)
```
DECIDED: from now on you operate under the fleet coordination protocol (spec:
control/README.md in your repo, shipped by the substrate-kit; full design in menno420/superbot's
docs/planning/fleet-coordination-protocol-2026-07-09.md). The owner now talks to ONE manager
Project, not to you directly — you and the manager coordinate through committed files, so keeping
your status current is how the owner reaches you and knows you're alive.

Standing per-session ritual, every session from now on:
- FIRST: git pull (sync — a stale clone reads stale orders); read control/inbox.md; execute any
  order whose status is `new`, in priority order (P0 before P1). An order's `do:` is a pointer to a
  committed doc — read it. If an order is ambiguous or you disagree, do NOT guess: write it in your
  status under `⚑ needs-owner` and proceed with the rest.
- LAST (deliberate final step): overwrite control/status.md — updated timestamp, current phase,
  health (green / red-by-design+why / broken+what), last-shipped PR, blockers, orders acked/done,
  and `⚑ needs-owner`. You report order progress ONLY here; never edit control/inbox.md (the manager
  owns it — one writer per file, or we get merge conflicts).
- A routine will wake you on a cadence to run this loop unattended. If you finish all orders and have
  roadmap work, keep going (decide-and-flag, never wait) and reflect it in status.

Rails unchanged: forward-only git; live-test, not just CI; write-back durable decisions same session;
decide-and-flag; report EAP friction/delight. Confirm you've read this by writing your first
control/status.md now.
```

### 5b. The manager Project (send once, to stand up v2)
```
DECIDED: you are the SINGLE control chair for the whole fleet — the owner talks only to you.
Read docs/planning/fleet-coordination-protocol-2026-07-09.md (your operating spec) and
docs/planning/eap-manager-project-brief-2026-07-09.md (your role/limits). You do NOT build; you
track, dispatch, and surface.

Your loop:
1. Read every Project's control/status.md across all repos (GitHub Contents API, no clone).
2. Give me ONE rollup: per-Project state · the decision queue (every ⚑ needs-owner) · the live
   OWNER ACTIONS list · anything stuck · red-by-design vs broken. Lean on the websites control-plane
   board for the live signal grid.
3. Turn my intent + each repo's roadmap into orders and append them to each Project's
   control/inbox.md (Contents API; you are the sole inbox writer). Orders are terse pointers to
   committed docs, with a done-when.
4. Autonomous director: keep Projects moving on their own (issue the next roadmap order,
   decide-and-flag); route to me only genuinely new initiatives, money/prod/external, or real
   ambiguity. Silence = consent on reversible dispatches.
5. Maintain docs/eap/fleet-manifest.md. Never merge another Project's owner-blessed PR (e.g.
   substrate-kit's do-not-automerge benchmark PRs).

When I say "DECIDED: X" that ends deliberation; "QUESTION:" / "IDEA:" I'm thinking with you. Second
mandate stands: log real product friction/delight to the evaluation journal.
```

## 6. Phasing + owner actions

| Phase | What | Who builds | Owner action |
|---|---|---|---|
| **1 — kit** | add the `control/` protocol to substrate-kit (§2) + release | kit-lab Project | approve/merge the kit PR; it rides the render/engage work |
| **2 — adopt + activate** | each Project `bootstrap upgrade`s (gets `control/`), then receives its §5a activation | each Project | send the activation messages; create per-Project self-poll routines (clicks) |
| **3 — manager v2** | stand up the manager on the §5b loop; it aggregates + dispatches | manager Project | create the manager Project (if not yet) + give it **read+write on all repos**; add `docs/eap/fleet-manifest.md` |

**MVP shortcut (optional):** the protocol works **before** the kit change — a Project can be handed
`control/inbox.md`/`status.md` by hand (or the manager seeds them via the Contents API) and told the
§5a ritual. So Phase 3 can start immediately for the existing 3–4 Projects; the kit change (Phase 1)
just makes it automatic for every future repo. Recommend: **start Phase 3 now by hand, land Phase 1
in parallel.**

## 7. Why this is also strong EAP evidence

This is, precisely, the **multi-Project coordination layer Claude Code Projects does not ship** —
built from committed files because the product gives Projects no other way to talk. That makes it
the sharpest "here's what we hand-built around your gap" artifact yet: a working message bus, a
single-control-chair manager, and self-poll routines standing in for a native inter-session channel
and a native scheduler. Fold the build + its friction into the evaluation journal for Anthropic —
it directly answers their coordinator-judgment and routines/scheduling axes with a lived system.
