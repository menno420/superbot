# New-bot capability audit — shared brief (the contract every lane agent works to)

> **Status:** `reference` — the binding contract for the parallel new-bot capability audit (the
> new-bot-capability-audit pass is its technical spine).
> **Prepared:** 2026-07-02 (Opus 4.8) as the substrate for a fleet of independently-launched agents.

## The mandate — reconsider and optimize the whole intended surface (owner, 2026-07-02)

This is **not a passive map.** After these sessions, **every capability intended for the new bot** —
every command and the behavior behind it, plus the planned/ideated features (`docs/planning/`,
`docs/ideas/`) meant to land in the rebuild — must be **mapped → reconsidered → simulated → optimized**:

1. **MAP** — inventory the capability and its units (the grammar-fit layer below).
2. **RECONSIDER** — should it exist as-is? verdict: **keep · improve · merge · drop · redesign**. Nothing
   is grandfathered in just because it ships today.
3. **SIMULATE** — express it in the §2 manifest and run it through the simulation substrate (the §2.10
   manifest simulator / write-surface derivation, `tools/grammar_spike/measure.py`, and the `parity/`
   golden behavioral harness) to check the *reconsidered* form actually reproduces the intended behavior.
4. **OPTIMIZE** — deep-reason: **is this the most optimal form?** If not, propose the concrete better
   version — and, where feasible, simulate the alternative to show it wins.
5. **BENCHMARK** — review the domain against **known Discord bots and their full feature sets** (MEE6,
   Carl-bot, Dyno, Dank Memer, Ticket Tool, YAGPDB, Arcane, Tatsu, ProBot, Mudae, and any others that
   fit the domain). Catalog what **they** do that **we don't**. This is deep-research work (Lane F).

**The three scope axes** (nothing intended for the new bot falls outside them):

- **Axis 1 — what we have** (the 43 subsystems, Lanes A–D): map → reconsider → simulate → optimize.
- **Axis 2 — what we planned** (`docs/planning/` + `docs/ideas/`, Lane E): reconsider each for the new bot.
- **Axis 3 — what the ecosystem has that we don't** (Lane F, deep-research vs known bots): catalog the
  gaps. **These are NOT commitments to build** — they are *documented known options*. The bar is
  "known and clearly documented," so a future session can pull from a rich menu instead of rediscovering.

**The deliverable is a capability corpus, not a verdict page.** The owner's goal is a repo *overflowing
with useful, well-documented data the next bot can use* — every capability (ours + planned + ecosystem)
captured with: what it is · do we have it · is it optimal · the better form · which bots have it · should
the new bot have it. Filterable, durable, and honest about what's a real gap vs. a deliberate omission.

**Granularity (bounded so it's actionable):** the unit of analysis is the **capability** (a command +
its handler/service logic), not each of the ~21k Python functions — "function" here means the behavior
behind a capability. The per-capability output is a *recommendation* backed by grammar-fit + simulation
+ reasoning + ecosystem comparison — never just a tier label.

## The end goal — one unified, ordered, best-in-class build plan (owner, 2026-07-02)

Everything above serves one outcome: **the next bot is built from a single comprehensive unified plan,
not speculation or trial-and-error** — so every function works the same way and the whole feels like one
coherent picture (which is exactly what the §2 manifest grammar enforces: one pattern, generated). The
audit's ultimate product (assembled by the capstone) is therefore not a menu but **THE build plan**, with:

- **A logical build order.** Foundations first → the core bot-management + server-management functions →
  then features. The capstone sequences every kept/improved/added capability into dependency layers.
- **Production-grade, done-before-next.** Each layer is **100% complete and operational at production
  grade** before the next begins — the plan states, per capability, what "done" means (the acceptance
  tests / the `parity/` golden it must pass), not just "build it."
- **The outperform bar (standard rule).** Every capability we keep or build must **outperform the best
  equivalent in any other bot.** This is where Axis 3 (Lane F) earns its keep: for each capability, name
  the best-in-class competitor and the concrete way ours beats it (or the deliberate reason it needn't).

So each lane's per-capability recommendation carries forward into the plan as: *its dependency layer · its
production-grade done-definition · its outperform target.* Keep those three in view while you audit.

## The grammar spine — the future-proofing bet

The rebuild's entire wager is the **declarative §2 manifest grammar**: one typed `SubsystemManifest`
per subsystem, from which commands, panels, settings, events, and help are **generated** — "no
hand-written views layer." That bet only holds if ~**80%+ of every subsystem's real surface** expresses
as **tier-1/2 declarations** rather than **tier-3 escape-hatch code**. Enough tier-3 and the rebuild
re-inherits the fragmentation it set out to kill — i.e. *it needs re-rebuilding in a year.* Avoiding
that is the **dominant constraint** (owner, 2026-07-02): get the design durable, not fast.

**The gap this audit closes:** the grammar spike ([`RESULTS.md`](../../../../tools/grammar_spike/RESULTS.md))
measured fit on **3 of 43 subsystems** (karma 80→87%, logging 79→97%, blackjack **44%**) → **73%
as-written, 85% with six amendments.** "85% is a floor" is currently an *assumption* ("most subsystems
are karma/logging-shaped"). The named danger zone — **stateful games (~44%), gateway-event listeners,
`wait_for` wizards, scheduled loops, voice** — is **unmeasured across the other 40 subsystems.** That
untested surface *is* the future-proofing risk. This audit turns "probably a floor" into a **measured
fact across all 43** and produces the complete amendment list.

## The method — replicate the spike, at scale

The worked example already exists; **do not reinvent it, extend it**:

- **The grammar:** [`tools/grammar_spike/spec.py`](../../../../tools/grammar_spike/spec.py) — the §2
  manifest prototype (frozen dataclasses; every field tagged **S**emantic / **A**rrangement /
  **O**bjective; behavior behind `HandlerRef`/`PanelRef`, never inline). Canonical spec:
  [`docs/planning/rebuild-design-spec-2026-07-02.md`](../../../planning/rebuild-design-spec-2026-07-02.md) §2.
- **The worked manifests:** [`tools/grammar_spike/manifests/`](../../../../tools/grammar_spike/manifests/)
  `karma.py` · `blackjack.py` · `server_logging.py` — each subsystem expressed AS a manifest. **Your
  output for each assigned subsystem is a manifest sketch + a unit ledger in this exact shape.**
- **The tier semantics + measure:** [`tools/grammar_spike/measure.py`](../../../../tools/grammar_spike/measure.py)
  and its docstring define **tier-1** (pure kernel declaration, generated) / **tier-2** (declaration +
  a registered thin handler/provider ref) / **tier-3** (bespoke logic — the escape hatch the grammar
  can't remove).
- **The six existing amendments** (fit gaps the spike already found; extend this list, don't repeat it):
  **G-1** `GatewayListenerSpec` (no gateway-listener primitive in §2 — every event-driven feature is
  tier-3 without it) · **G-2** list-valued settings + add/remove workflows · **G-3**
  `AnnouncementRouteSpec` · **G-4** `CommandSpec.cooldown` · **G-5** declarative validator bounds ·
  **G-6** per-kind command namespaces (prefix/slash disjoint).

## What each lane agent produces (the output schema — so all outputs compose)

For **each subsystem in your lane**, write one section into your lane file
(`lanes/lane-<X>-<name>.md`) with these parts, in this order:

1. **Surface-unit ledger** — a table with the spike's columns. Start from the pre-extracted inventory
   in your lane file (commands from the ground-truth dump + the unit-kind checklist); **verify and
   complete it against source** — every unit kind must be covered:
   `command · panel · setting · listener · event · store · game · help`.

   | Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
   |---|---|---|---|---|---|

2. **Manifest sketch** — the subsystem expressed in the §2 grammar (Python-ish, spike style). It need
   not import/run; it must show *where each unit lands* (which Spec, which field role, which handler ref).

3. **Tier-3 findings → amendments** — for every tier-3 unit: is it (a) a **grammar gap** → propose a
   named amendment `G-<n>` (or reuse G-1…G-6), or (b) a **legitimate deliberate escape hatch** (thin
   domain logic that *should* stay code)? State which, with the one-line reason.

4. **Fit numbers** — `units total`, `tier-1/2 count`, `fit % as-written`, `fit % with amendments`
   (mirror the RESULTS.md table for your subsystem).

5. **Structural-gap flags** — explicitly note if the subsystem uses any of the danger-zone patterns
   (stateful game loop · gateway/`@bot.event`/`bus.on` listener · `wait_for` wizard · scheduled loop ·
   voice) and whether the grammar (with amendments) can express it or it needs a new primitive family.

## Hard rules (guardrails)

- **Read-only. No runtime code, no `disbot/` edits, no new-repo code.** This is discovery. Output is
  docs only, under this directory.
- **Verify every tier-3 claim against shipped source (Q-0120).** The prior Codex preserve-maps got
  command names/paths wrong 4× — a "needs tier-3" verdict that's really "I didn't see the tier-2 form"
  poisons the amendment list. Cite `file:line`. When unsure, mark `⚠ unverified` rather than assert.
- **Cover the whole subsystem, not just its commands.** Panels, settings, listeners, events, stores,
  and help are where the grammar actually strains (commands are the easy 80%).
- **Stay in your lane** (see `PARTITION.md`) — subsystems are assigned disjointly so lanes never
  collide. If you finish early, do a *verify* pass on an adjacent lane's tier-3 findings, don't re-audit.

## Exit bar — when the design is "durable enough to start building"

The final review (see `FINAL-REVIEW-HANDOFF.md`) declares GO when, **across all 43 subsystems**:
1. Tier-1/2 fit is **measured** (not extrapolated) and clears the spec's **80%** bar — or the shortfall
   is a named, bounded set of amendments the owner accepts;
2. **Every tier-3 unit** is dispositioned: grammar-amendment **or** documented deliberate escape hatch;
3. The **structural danger-zone patterns** (stateful games, gateway listeners, wizards, loops, voice)
   each have a design answer (a primitive family or an accepted escape hatch);
4. The consolidated **amendment list G-1…G-N** is folded into the design spec — a docs pass, no redesign.

Miss any of these and the verdict is **GO-with-amendments** (name them) or **NO-GO** (the grammar needs
a structural rethink before build) — never a soft "looks fine."
