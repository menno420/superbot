# Architecture atlas & structure review — capture + agent judgment

> **Status:** `ideas` — capture + evaluation. **Not a plan, not approval.** Source code, the binding
> contracts, and `docs/current-state.md` win over anything here. Owner-uploaded review (2026-06-16) +
> the agent's cross-checked verdict. Routing for each derived idea is in § "Routed proposals".

## What this is

The owner uploaded an external repo-architecture review (the *"SuperBot repository-architectuuratlas
en evidence-based structuurreview"*, Dutch) and asked for **ideas we can use plus a cross-checked
final judgment** on the document's own recommendations — *"these seem quite good but I'd like your
final judgement as well."*

The review was produced from a **pinned older commit** (`1ad7ca4…`) and **states openly that it could
not re-verify the repo live** in its session — it treats its own facts as "confirmed-at-pinned-research
level," not "re-counted from source." So the right thing to do here is exactly what `.claude/CLAUDE.md`
demands: **verify its claims against live source before acting.** That verification is below, and it
changes the picture in a few places.

**Headline verdict.** The review's *direction* is correct and well-argued: SuperBot is a healthy
modular monolith; the answer is a better **lens** (generated facts, drift checks), **not** a filesystem
reorganization. But its *current-state diagnosis is overstated*, and its flagship recommendation is
**~80% already shipped** in this repo. The genuinely additive ideas are narrower than the review frames
them — and one of its recommendations contradicts an explicit repo decision it didn't know about.

---

## The review in one paragraph

SuperBot = a hybrid modular monolith (vertical feature slices on a shared layered platform). The
foundation is sound (runtime contracts, subsystem registry, mutation ownership, CI gates, multiple
navigation maps). The real problem is **visualization/documentation drift** between source, the map
layers, subsystem folios, and hand-maintained inventories — *not* the physical tree. Recommendation:
**Option A** (keep the structure; replace hand-copied inventories with one **generated architecture
atlas** — a provenance-stamped front page that, per file, answers *where it belongs · who owns the
writes · what it may import · who depends on it · which tests/docs apply · blast radius* — with a
`--check` CI drift mode), plus a **selective Option B** (fix the few real boundary violations). Reject
**Option C** (feature-package migration) and **Option D** (big reorg) and a `src/` layout as
unjustified by the evidence. External backing: C4 (multiple views), arc42, hexagonal (adapters
outside the core), Fowler monolith-first, Nygard ADRs, Home-Assistant-style integration
classification.

---

## Cross-check against live source (2026-06-16, commit `5d03b3d`)

| Review claim | Live finding | Verdict |
|---|---|---|
| "High drift" in **extension counts** (43 live vs historical 28/36) | **No current doc pins an extension count.** The `28`/`36` figures live only in `docs/audits/repo-wide-audit-2026-05-29.md` — a correctly-badged *dated audit snapshot*, not a live map. | **Overstated** — drift already retired by the anti-drift machinery. |
| "High drift" in **migration counts** | **Real.** `docs/architecture.md:60` says `(51 migrations)`; live = **74**. | **Confirmed** → fixed in this PR. |
| "Medium drift" in **workflow inventory** | **Real.** `docs/repo-navigation-map.md:45` implies 1–2 workflow files; live = **6**. `architecture.md:41` also says `cogs/ (×28)`; live = **43**. | **Confirmed** → fixed in this PR. |
| Build a generated **per-file "maintainer dashboard"** (layer · owner · imports · dependents · tests · docs · blast radius) | **~80% already exists** as `scripts/context_map.py` — it emits exactly: module, layer, review-unit, file role/authority (mutation-owner facts), layer-may-import, module-level **and** lazy imports, imported-by, blast radius, related docs, relevant tests, risk flags, recommended read-set, post-edit checks. EventBus wiring is `scripts/wiring_map.py`; review partition is `scripts/review_scope.py`; per-area packs are `tools/agent_context/`. | **Already shipped** (per file, on demand). The *delta* is real but narrow — see below. |
| **No extension-type taxonomy / crosswalk** exists | **Confirmed.** 43 extensions vs **33** registered subsystems; the registry (`utils/subsystem_registry.py`) has rich metadata (`visibility_tier`, `category`, `parent_hub`, `hub_group`, `tags`) but **no lifecycle-role field** (bootstrap / maintenance / hub / adapter / lab / specialized-surface). Nothing maps the **10** non-registry extensions. | **Confirmed + genuinely missing** — strongest idea (now shipped, PR #958). |
| **Boundary debt**: `views→cogs`, `core/runtime→services`, `utils→core/services` | **Accurate**, and already **tracked**: `architecture_rules/layers.yaml` `known_violations` — `arch-fix-13` (≈18 `views/<game\|economy\|xp\|diagnostic>/ → cogs.<x>._helpers/_state`), `arch-fix-11` (≈17 `core/runtime → services`), `arch-fix-6/7/8`. | **Confirmed but not new** — these are ticketed; value = *burn down*, not discover. |
| Add a minimal **root README** as a pointer | The repo made an **explicit, deliberate decision against one**: *"There is intentionally **no top-level README** — `docs/` is the documentation surface"* (`repo-navigation-map.md:51`). The review didn't know this. | **Contradicts a stated decision** — legitimate to revisit (public-era GitHub landing UX), but **owner-only** → Q-0151. |
| Reject `src/` layout, Option C, Option D, microservices | Matches this repo's own posture (modular monolith, executable import contracts already in place). | **Endorsed.** |

**Net:** the review is a high-quality outside-in read whose *recommended direction is right*, but it
(a) over-weights drift that the repo's checkers have already largely eliminated, (b) proposes a
flagship artifact that mostly exists, and (c) makes one recommendation against an explicit repo
decision. Its honesty about its own provenance limits is a point in its favor and is why the
cross-check mattered.

---

## What's genuinely additive (the real signal)

Stripping out what already exists, three ideas survive — in priority order:

### 1. Extension-type taxonomy crosswalk (strongest; genuinely missing) — ✅ APPROVED + SHIPPED (PR #958)
Make the **43 extensions ↔ 33 subsystems** mapping legible so the **10** non-1:1 extensions
(`bootstrap_access`, the two `*_maintenance` cogs, the five `btd6_*`/`paragon` surfaces, `setup`,
`hermes`) read as *classified*, not as a gap. A `role` classification (product-subsystem · hub/router ·
shared-platform · maintenance · operational-adapter · bootstrap · specialized-surface · lab), surfaced
as a **generated crosswalk table**, plus a **CI guard** that every entry in `config.INITIAL_EXTENSIONS`
is classified — so a new unclassified extension fails CI instead of silently widening the gap. This is
the one place the review found a true blind spot. **Built (Q-0151c, owner-approved) as a curated overlay
`architecture_rules/extension_roles.yaml` + `scripts/extension_crosswalk.py` →
[`docs/architecture/extension-taxonomy-crosswalk.md`](../architecture/extension-taxonomy-crosswalk.md), enforced by
`tests/unit/scripts/test_extension_crosswalk.py`** — see
[the plan](../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md).
*(Count-correction: the live registry has **33** identities, not the 32 first written here — fixed
2026-06-16; the crosswalk is now the self-correcting source.)*

### 2. A *thin* unified atlas — compose, don't duplicate — ✅ APPROVED + SHIPPED (PR #960)
Built per the owner's Q-0151a choice (companion to `AGENT_ORIENTATION`, body not committed,
CI-`--check` + on-demand): **`scripts/atlas.py`** composes `context_map` / `_review_units` /
`extension_crosswalk` into a repo-wide provenance-stamped index; the down-payment surfaces `role` in
`scripts/context_map.py`; the curated companion is
[`docs/architecture/repo-atlas.md`](../architecture/repo-atlas.md). See
[the plan](../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md) § "PR 2".

The review's real surviving insight: the facts are all generable but **scattered** across
`context_map` / `wiring_map` / `review_scope` / `command_surface_dump` / `settings_lane_matrix` /
the agent context packs, with **no single provenance-stamped front page and no repo-wide `--check`
drift mode**. A thin `scripts/atlas.py` that (a) emits a **repo-wide** file→{layer, review-unit,
subsystem/role, owner, tests, docs} index by *importing the existing modules as libraries* (never
re-implementing them), (b) stamps **provenance** (commit SHA, generator version, timestamp), and
(c) offers `--check` for CI. **Risk:** this overlaps the agent context-pack system and raises real
owner-policy questions (atlas as the primary entry vs a companion; commit the generated artifacts vs
CI-only). → **DISCUSS**, not auto-build.

### 3. Count-citation guard (generalizes an existing backlog idea) — ✅ SHIPPED (PR #964)
Built as a **soft** `check_docs` rule (`inventory_count_flags` / `print_inventory_count_report`): a
bare `N migrations/workflows/extensions/cogs/subsystems` in a **binding** doc warns unless it cites a
regen command (`scripts/*.py`), is marked generated, or carries `<!-- count-ok -->`. Pinned-to-code
docs are exempt (their doc-test already guards their counts). Baseline is clean (the #957 fixes + the
exemption). It also effectively **resolves** the existing backlog idea
[`readiness-maps-cite-regen-command-2026-06-13.md`](./readiness-maps-cite-regen-command-2026-06-13.md):
its readiness-map widening was investigated and **dropped as not-worth-it** — the
`production-readiness/*` maps are `audit`-badged (frozen by design), and the one live settings map
already self-cites its regen command.

The three drift instances fixed in #957 share one root cause: a **bare integer count hand-typed
into a binding doc**. The durable fix is the existing backlog idea
[`readiness-maps-cite-regen-command-2026-06-13.md`](./readiness-maps-cite-regen-command-2026-06-13.md),
generalized: a soft `check_docs` rule that flags a bare `N migrations` / `N workflows` / `N extensions`
claim in a binding/living doc unless it cites its regen source or is marked generated. Fold into that
idea rather than opening a new one.

---

## Routed proposals (idea-lifecycle § ROUTE)

| Proposal | Size / risk | Route |
|---|---|---|
| Fix the 3 confirmed drift counts in binding docs | tiny / reversible | **Executed in this PR** (bugs-first; source wins). De-numbered to point at source so they can't re-rot. |
| **Extension-type taxonomy crosswalk + CI guard** (#1) | medium — touches `subsystem_registry` (a `REGISTRY_SCHEMA_VERSION` bump + validation) and adds a generated artifact + guard | **Structure into a plan** — needs its own `docs/planning/` plan (ownership: registry; reuse: existing metadata seam; mechanics: schema-version bump, validation, generated crosswalk, guard). Not a drive-by. |
| **Thin unified atlas** `scripts/atlas.py` (#2) | medium — composes existing tools; new generated artifact | ✅ **SHIPPED (PR #960)** — Q-0151a answered (companion, body not committed); composer + `context_map` role line + companion doc + tests. |
| **Count-citation guard** (#3) | small — `check_docs` rule | ✅ **SHIPPED (PR #964)** — soft `inventory_count_flags` in `check_docs` over binding docs (cite/`generated`/`<!-- count-ok -->` exempt; pinned docs exempt). Resolves `readiness-maps-cite-regen-command` (the readiness-map widening was investigated + dropped — audit docs frozen-by-design; live map self-cites). |
| Selective boundary-debt burndown (Option B) — start with `arch-fix-13` `views→cogs` (≈18 entries) | medium, scoped, test-covered | **Roadmap candidate** (S1 / shared-platform). Already ticketed; this is execution, not discovery. Each cluster (blackjack, economy, xp, diagnostic) is its own small PR moving `_helpers`/`_state` to `utils/` or a shared module. |
| Root README pointer | tiny but overrides a stated decision | **DISCUSS → Q-0151** (owner-only — contradicts `repo-navigation-map.md:51`). |
| Reject `src/` layout / Option C / Option D / microservices | n/a | **Endorse the rejection** — consistent with repo posture; no action. |

## Promotion gates not yet met (per `docs/ideas/README.md`)
None of #1/#2 are promoted to active work here. #1 needs a plan (ownership ✓ registry; reuse ✓
metadata seam; risk — low; mechanics — schema bump + guard) before it graduates. #2 needs the Q-0151
owner answer first. The drift fixes are the only thing executed, and they qualify as bugs-first
(contained, reversible, source-wins).
