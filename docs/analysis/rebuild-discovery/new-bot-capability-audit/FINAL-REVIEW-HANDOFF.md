# Final review handoff — the Fable 5 capstone

> **Status:** `reference`. This is the startup context for the **final Fable 5 session** (ultracode or
> normal) that turns the seven lanes' findings into one durable go/no-go on the rebuild grammar.
> **All seven lanes (A–G + F) are merged to `main`** as of 2026-07-02 — every input below is present and
> source-verified; you are synthesizing a complete substrate, not waiting on anything.

## Your input (the whole substrate — all three axes)

- **The contract:** [`BRIEF.md`](./BRIEF.md) (mandate, method, schema, exit bar) + [`PARTITION.md`](./PARTITION.md).
- **Axis 1 — what we have:** `lanes/lane-A-governance.md` · `lane-B-economy.md` · `lane-C-games.md` ·
  `lane-D-knowledge-platform.md` (the 43 subsystems) + `lanes/lane-G-foundations.md` (the **L0 runtime
  skeleton** — bootstrap / cog-loader / env-config / `main.py` / helper-util architecture). Each: unit
  ledger + manifest sketch + tier-3 dispositions + fit numbers + structural-gap flags + reconsider/
  optimize recommendations. **L0 (Lane G) leads the build order — read it first.**
- **Axis 2 — what we planned:** `lanes/lane-E-plans-ideas.md` — the forward-capability ledger.
- **Axis 3 — what the ecosystem has:** `findings/ecosystem-benchmark.md` — the known-Discord-bot
  capability-gap catalog + any other Codex / deep-research addenda in `findings/`. **Guard:** the raw Lane F
  deep-research misread SuperBot's own surface (it flagged shipped subsystems — ticketing, reaction roles,
  casino, welcome image cards, web dashboard — as missing "gaps"); the doc's SuperBot-status column is
  already source-corrected, but **before you schedule any ADD-from-ecosystem, re-check the 43-subsystem
  ground truth that it isn't already shipped.** Treat the competitor catalog as directional (outperform
  targets), not as a build list.
- **The baseline:** [`tools/grammar_spike/RESULTS.md`](../../../../tools/grammar_spike/RESULTS.md) (the
  3-subsystem spike this extends) and the design spec §2 + §10.1 risk 5.

## Your job — synthesize + adversarially verify, then rule

1. **Verify before you trust (Q-0120).** The lanes are independent-agent output, including other
   providers. **Do not average their numbers blindly.** Spot-check the highest-leverage tier-3 verdicts
   against source (the ones that would force a new primitive family). The spike caught cross-agent maps
   mis-reading source 4× — a wrong "needs tier-3" inflates the amendment list; a wrong "tier-2 is fine"
   hides a real gap. Down-weight `⚠ unverified` rows; re-derive the disputed ones.

2. **Compute the real all-43 fit.** Aggregate the per-subsystem unit ledgers into one table (mirror
   RESULTS.md, 43 rows + overall), **as-written vs. with-amendments**. This is the number that replaces
   "85% is probably a floor" with a measured fact. Weight honestly — note if the mean is carried by a
   few high-fit CRUD subsystems while the stateful cluster drags.

3. **Consolidate the amendment list.** Merge every lane's proposed `G-<n>` into one deduplicated set.
   The set already runs **G-1…G-10**: G-1…G-6 from the spike (GatewayListenerSpec, list-valued settings,
   AnnouncementRouteSpec, CommandSpec.cooldown, validator bounds, per-kind namespaces) **plus Lanes D/F's
   G-7 `KnowledgeDomainSpec` · G-8 AI platform specs (`AITaskProfileSpec`/`AIProviderGatewaySpec`) · G-9
   `TimedTaskSpec` · G-10 `ModalFormSpec`** — extend/dedup, don't renumber. For each: what it adds, which
   subsystems need it, and whether it's a **soft** spec note or a **structural** new primitive family. Flag
   any amendment that implies real §2 redesign (not just a docs pass) — those are the durability-critical ones.

4. **Answer the structural danger zones.** For each of stateful-games / gateway-listeners / `wait_for`
   wizards / scheduled-loops / voice: does the grammar (with amendments) express it, or does it stay a
   documented escape hatch, or does it need a new family? A subsystem class with *no* clean answer is a
   NO-GO signal — that is exactly the "needs re-rebuilding in a year" failure.

5. **Per-subsystem preserve / redesign / drop disposition.** One line each (fold with the existing
   [preserve-map synthesis](../codex-preserve-map-synthesis-2026-07-02.md) — this audit is its grammar
   layer).

## The verdict (the deliverable)

One of three, with the evidence behind it — never a soft "looks fine":

- **GO** — measured all-43 tier-1/2 fit clears 80% (or the shortfall is a bounded, owner-accepted
  amendment set), every tier-3 is dispositioned, every structural danger zone has a design answer, and
  the consolidated amendments are a **docs pass** into the spec (no redesign). → build can start.
- **GO-with-amendments** — as above but the amendment set is non-trivial; name them and their spec
  edits; build starts after the (bounded) spec pass.
- **NO-GO** — a subsystem class has no clean grammar answer, or fit is structurally low on a large
  cluster. Name the specific primitive-family redesign needed before build. Better a NO-GO now than a
  re-rebuild in a year — that is the whole point of this pass.

Write the verdict + the aggregated fit table + the consolidated amendment list to
`findings/FINAL-REVIEW.md`, and open the design-spec amendment PR (or a plan for it) it implies. This
review is the gate between "planning/discovery" and "creating the new repo" — treat it as owner-facing
go/no-go evidence, and hand the owner the explicit "what approval means" checklist.

## The unified build plan (the second — and ultimate — deliverable)

The grammar verdict answers *"can we build it durably?"* The owner's ultimate ask is bigger: **the next
bot must be built from ONE comprehensive unified plan, in a logical order, each layer production-grade
before the next, every function outperforming the best equivalent in any other bot.** So fold Axis 1
(kept/improved), **Axis 2 (Lane E, planned)**, and **Axis 3 (Lane F, ecosystem)** into a single ordered
build plan → `findings/NEW-BOT-BUILD-PLAN.md`. It has three parts:

**1. The capability corpus** — every capability, with its disposition:
- **KEEP** (optimal as-is) · **IMPROVE** (the better form, simulated where possible) · **MERGE** · **DROP**
  (Axis 1) · **ADD-from-plans** (Axis 2) · **ADD-from-ecosystem** (Axis 3 strong-fit) · **DEFERRED /
  known-options** (documented, not scheduled — the "known and clearly documented" menu).

**2. The build order (the part the owner cares most about).** Sequence every KEEP/IMPROVE/ADD into
**dependency layers**, foundations first:
- **L0 Foundations** — the kernel/grammar, state/db, config lanes, audit seam, permission/capability
  model, the manifest+simulator itself.
- **L1 Core management** — bot-management + server-management functions (setup/provisioning, roles,
  channels, moderation, logging) — the operator's control plane.
- **L2+ Features** — everything domain (economy, games, knowledge, community …), each depending only on
  layers already complete.
Each item lists its **dependencies** (what must be 100% done first). No item may sit in a layer above
an unbuilt dependency.

**3. Per-capability acceptance — done-before-next + outperform.** For every buildable item, state:
- **Production-grade "done"** = the concrete acceptance bar (which `parity/` golden it passes, tests,
  operational criteria) — a layer is not "done" until every item in it clears this.
- **Outperform target** = the best-in-class competitor (from Lane F) and the specific way ours must beat
  it (or the deliberate reason parity is enough).

Keep it **rich, filterable, honest** (deliberate omissions labeled *why*). This is both the "repo
overflowing with useful data the next bot can use" corpus **and** the singular ordered plan the owner
builds from — it outlives this review and is the thing the first build session picks up.
