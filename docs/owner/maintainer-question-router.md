# Maintainer Question Router

> **Status:** `reference` — owner-facing guidance and question router.
>
> **Audience:** maintainer first, agents second.
>
> **Purpose:** collect agent questions, preserve maintainer answers, and route
> answered owner intent to the correct documentation home.
>
> **Not a roadmap:** unanswered questions are not approval. Answered questions that
> affect code, architecture, priorities, or product behavior still need the normal
> decision/planning/promotion path before implementation.
>
> **Archive:** old, fully answered + routed `Q-0NNN` blocks move to
> [`maintainer-question-router-archive.md`](./maintainer-question-router-archive.md) on the
> reconciliation cadence (convention **Q-0210**) — numbers are never moved/renumbered, so every
> `Q-0XXX` reference stays grep-resolvable wherever the block lives.

## 1. What this file is for

Use this file when an agent needs the maintainer's intent to avoid guessing. Questions
may cover product vision, priority, user experience, architecture, safety, workflow,
or clarification of an earlier answer.

It gives the maintainer one place to answer at their own pace. It also supports a
dedicated Claude/Opus-style session that prepares a small batch of plain-language,
multiple-choice questions for quick answers.

Maintainer answers are **leading owner intent by default**. Agents must preserve the
original answer, use it faithfully, and route durable conclusions to their proper
home.

## 2. What this file is not

This file is not:

- an implementation plan, roadmap, active queue, or approval to change code;
- an ADR, architecture contract, ownership map, runtime contract, or current-state
  ledger;
- a replacement for `.claude/CLAUDE.md`, `.session-journal.md`, subsystem folios,
  `docs/planning/`, `docs/decisions/`, or `docs/ideas/`;
- a bypass around server-management sequencing, AI/BTD6 gates, privacy review,
  security review, or any other binding decision;
- a place to silently convert unanswered questions into assumed approval.

Source code and merged PRs win where they describe shipped behavior. Binding docs and
active trackers keep their existing authority. This router preserves and routes owner
intent; it does not override those sources by itself.

## 3. Maintainer preferences

- Prefer clear explanations before coding jargon.
- Preserve the maintainer's product vision, not only a technically convenient
  implementation.
- Ask when owner intent is genuinely unclear instead of guessing at product intent.
- Continue safe, reversible, source-verified work when possible, but do not decide
  unresolved product, safety, privacy, or architecture questions on the maintainer's
  behalf.
- Agents may challenge an answer that is impossible, unsafe, inefficient, too costly,
  or conflicts with architecture or binding decisions, but must explain why in plain
  language and offer a safer alternative.
- Prefer safe, modular, observable, service-owned changes over broad rewrites or
  duplicate systems.
- Keep AI, automation, BTD6 expansion, privacy-sensitive features, and
  server-management changes behind their documented gates.

## 4. How agents should use this file

1. Check authoritative source and the correct existing documentation home before
   asking; do not ask the maintainer to resolve a question the repo already answers.
2. Add a focused question only when the answer materially affects product intent,
   safety, architecture, priority, or an irreversible/expensive choice.
3. Write in plain language, explain why the answer matters, and give a safe default.
4. Do not bundle unrelated decisions or steer the maintainer toward a preferred answer
   without saying why it is preferred.
5. Preserve the maintainer's original answer block exactly. Agents may add a concise
   interpretation below it, but must not silently ignore, rewrite, or reinterpret it.
6. Route or copy the durable conclusion to the correct home, then record the routing
   result here. Do not dump whole conversations into multiple docs.
7. If the answer cannot safely be followed, use the reproposal rule in §8.

Unanswered questions are **not approval**. Their safe defaults describe what agents
should do while waiting; they do not promote work into an active plan.

## 5. How the maintainer can answer

The maintainer may:

- answer directly inside the preserved answer block;
- choose an option and add a short reason;
- say “defer” or “not sure yet” without approving anything;
- identify something agents keep misunderstanding;
- ask for a clearer explanation or safer alternative;
- answer several small questions in a dedicated multiple-choice session.

Short answers are valid. Agents are responsible for making the question understandable
and routing the conclusion, not for making the maintainer write technical documents.

## 6. Question lifecycle

Use one of these statuses:

| Status | Meaning |
|---|---|
| **Inbox** | Captured but not yet prepared for the maintainer. |
| **Awaiting maintainer answer** | Ready for the maintainer; no answer yet. |
| **Answered in chat — needs repo update** | The maintainer answered outside this file; preserve the answer here before routing. |
| **Answered — needs routing** | Answer is preserved here but its durable conclusion has not reached the correct home. |
| **Routed** | The concise conclusion is linked/copied to the correct authoritative or reference home. |
| **Kept here as general guidance** | The answer is reusable owner intent and has no better home. |
| **Needs follow-up** | The answer exposes another material question or unresolved conflict. |
| **Superseded** | A later maintainer answer or authoritative decision replaced it; link the replacement. |

Optional priority values are **Low**, **Medium**, **High**, and **Blocking**. “Blocking”
means a specific decision cannot safely continue; it does not make the question an
approved implementation priority.

## 7. Routing destinations

After an answer, copy or link only the concise durable conclusion to the correct home:

| Destination | What belongs there |
|---|---|
| `.claude/CLAUDE.md` | Binding agent workflow or session behavior. |
| `.session-journal.md` | Operational/session gotchas and short-lived working memory. |
| `docs/current-state.md` | Active project status only, when truly current-state relevant. |
| `docs/architecture.md` | Broad system design constraints. |
| `docs/ownership.md` | Ownership boundaries and mutation authority. |
| `docs/runtime_contracts.md` | Runtime guarantees, lifecycle behavior, and failure semantics. |
| `docs/decisions/` | Binding technical decisions or ADR-like outcomes. |
| `docs/planning/` | Approved implementation plans; an answer alone does not create approval. |
| `docs/subsystems/<area>.md` | Area-specific durable guidance and links. |
| `docs/ideas/` | Explicit brainstorms and unapproved future ideas. |
| **Keep here** | General owner intent or reusable clarification with no better home. |

Preserve the original maintainer answer here even after routing. Link to the destination
and record what was copied; do not move the only copy or repeat the full conversation
across the repo.

## 8. Reproposal rule

Maintainer answers are leading owner intent. Agents should follow them unless the
answer is impossible, unsafe, inefficient, too costly, or conflicts with existing
architecture or binding decisions.

If an agent believes a maintainer answer should not be followed, the agent must:

1. summarize the maintainer answer fairly;
2. explain the problem in plain language;
3. name the conflicting source, constraint, or risk;
4. propose at least one safer alternative;
5. ask the maintainer to confirm the revised direction before treating it as settled.

Do not blindly implement the original answer, and do not silently substitute the
agent's alternative.

## 9. Question block template

Copy this block into the Question inbox or the appropriate lifecycle section:

`````markdown
## Q-0001 — <short question title>

**Asked by:** <agent/session if known>
**Date:** YYYY-MM-DD
**Area:** AI / BTD6 / Server management / Docs / Workflow / General
**Type:** Vision / Priority / UX / Architecture / Safety / Workflow / Other
**Priority:** Low / Medium / High / Blocking
**Status:** Awaiting maintainer answer
**Suggested destination after answer:** CLAUDE.md / architecture / current-state / session-journal / planning / decisions / subsystem folio / ideas / keep here

### Question

<Plain-language question>

### Why agents need this

<What this answer affects>

### Options, if useful

A. ...
B. ...
C. ...
D. Defer / not sure yet

### Safe default until answered

<What agents should assume for now>

### Maintainer answer

```text
Answer:

Reason:

Anything agents keep misunderstanding:

Keep open for later:
```

### Agent interpretation, if needed

```text
Do not rewrite the maintainer answer. Add a concise interpretation here only if useful.
```

### Routing result

```text
Destination:
Moved/copied on:
Notes:
```
`````

## 10. Multiple-choice batch format

When many small maintainer decisions are needed, agents may prepare a batch of short
multiple-choice questions.

Each question should:

- avoid jargon;
- explain why it matters in one sentence;
- provide 2–4 clear options;
- include a safe default;
- avoid bundling unrelated decisions together;
- avoid treating unanswered choices as approval.

Keep batches small enough to answer without a long research session. Route each answer
individually when the destinations differ.

### Batch question example

**Q:** Should coding sessions prefer many small PRs or fewer longer PRs?

**Why it matters:** This affects review size, context switching, and how quickly
features land.

**Options:**

A. Prefer small focused PRs.
B. Prefer longer sessions that finish a whole feature.
C. Use small PRs for risky areas and longer PRs for docs/simple work.
D. Decide case by case.

**Safe default:** C.

## 11. Question inbox

The starter questions below were **answered by the maintainer on 2026-06-07 — see §12**
(answers preserved verbatim; durable conclusions routed in §12–§13). The §11 recommended
directions were *not* approval; the maintainer's answers are the leading owner intent.

### Q-0001 — Should AI stay explanation-only, or eventually help prepare actions?

**Area:** AI / Server management
**Type:** Vision / Safety
**Priority:** High
**Status:** Answered (2026-06-07) — Routed → `docs/subsystems/ai.md` (see §12)
**Suggested destination after answer:** decisions / AI folio / ideas

**Question:** Should AI permanently stay read-only and explanation-only, or could it
eventually prepare a preview that a human confirms through the normal service-owned
action path?

**Why agents need this:** The answer shapes long-term AI product direction, but cannot
bypass AI-readiness, authority, confirmation, audit, or rollback gates.

**Options:** A. Explanation-only. B. Explanation-only now; maybe prepare previews
later. C. Eventually allow broader actions after dedicated decisions. D. Defer.

**Safe default:** A — AI stays read-only/explanation-only.
**Recommended direction:** A now; reconsider preview → confirm → apply → audit only
after the documented gates and a dedicated decision.

### Q-0002 — Should the owner-facing control center stay Discord-first?

**Area:** Server management / Product
**Type:** Vision / UX
**Priority:** Medium
**Status:** Answered (2026-06-07) — Routed → `docs/subsystems/server-management.md` (see §12)
**Suggested destination after answer:** server-management folio / ideas / decisions

**Question:** Should Discord panels remain the primary owner experience even if a web
companion becomes possible later?

**Why agents need this:** The answer affects long-term information architecture and
whether future surfaces must reuse Discord-first services and read models.

**Options:** A. Discord only. B. Discord-first, with a later reusable web companion.
C. Web-first eventually. D. Defer.

**Safe default / recommended direction:** B — Discord remains primary, services stay
reusable, and no web dashboard is started yet.

### Q-0003 — How should agents handle unclear maintainer vision?

**Area:** Workflow / General
**Type:** Workflow / Safety
**Priority:** High
**Status:** Answered (2026-06-07) — Kept as guidance (confirms CLAUDE.md act-vs-ask; see §12)
**Suggested destination after answer:** CLAUDE.md / keep here

**Question:** When the desired product outcome is unclear, which work should agents
continue and which decisions should wait for the maintainer?

**Why agents need this:** This balances progress against the risk of guessing the
maintainer's product, safety, privacy, or architecture intent.

**Options:** A. Stop all work. B. Continue safe/reversible work but pause material
product, safety, privacy, and architecture decisions. C. Let agents infer everything.
D. Decide case by case.

**Safe default / recommended direction:** B — continue safe, reversible work; add a
question and block only the material unresolved decision.

### Q-0004 — Should answered maintainer questions be copied or moved?

**Area:** Docs / Workflow
**Type:** Workflow
**Priority:** Medium
**Status:** Answered (2026-06-07) — Kept here (confirms §7/§14; see §12)
**Suggested destination after answer:** keep here / CLAUDE.md

**Question:** After an answer belongs in another doc, should the original answer stay
here?

**Why agents need this:** Preserving the original prevents later summaries from
silently changing owner intent while still respecting one-fact-one-home.

**Options:** A. Preserve the original here and copy/link a concise conclusion. B. Move
the original entirely. C. Leave everything here only. D. Defer.

**Safe default / recommended direction:** A.

### Q-0005 — How should agents challenge inefficient or impossible answers?

**Area:** Workflow / General
**Type:** Safety / Workflow
**Priority:** High
**Status:** Answered (2026-06-07) — Kept as guidance (confirms §8 reproposal rule; see §12)
**Suggested destination after answer:** CLAUDE.md / keep here

**Question:** What should an agent do when the maintainer's requested direction cannot
safely or realistically be followed?

**Why agents need this:** Blind implementation can create safety, cost, architecture,
or reliability problems; silent substitution loses owner control.

**Options:** A. Implement it anyway. B. Silently choose another approach. C. Explain
the conflict plainly, cite it, propose safer alternatives, and ask for confirmation.
D. Defer without explanation.

**Safe default / recommended direction:** C.

## 12. Answered — 2026-06-07

The maintainer answered the starter batch on 2026-06-07. Answers are preserved verbatim
as **leading owner intent**; the §11 recommended directions were *not* approval — these
answers are. Durable conclusions are routed in §13.

### Q-0001 — AI scope → **C: eventually broader actions**

> *Maintainer answer (2026-06-07):* AI may **eventually** gain broader / action
> capabilities (beyond explanation-only).

**Interpretation — not an approval.** This is long-term owner intent. Any AI action
capability stays behind *all* AI-readiness, orchestration, authority, confirmation,
audit, and rollback gates **and** a dedicated decision before it ships. Today AI stays
read-only / explanation-only. Routed → `docs/subsystems/ai.md`.

### Q-0002 — Owner control surface → **B: Discord-first, web companion possible later**

> *Maintainer answer (2026-06-07):* Discord panels remain the primary owner surface;
> keep services / read-models reusable so a web companion is possible later; no web work
> starts now.

Routed → `docs/subsystems/server-management.md`.

### Q-0003 — Unclear maintainer vision → **B: continue safe, pause material**

> *Maintainer answer (2026-06-07):* Continue safe, reversible, source-verified work;
> pause and ask on material product, safety, privacy, and architecture decisions.

Kept as guidance — confirms the act-vs-ask envelope in `.claude/CLAUDE.md` and
`docs/collaboration-model.md`.

### Q-0004 — Answer routing → **A: preserve original + route a conclusion**

> *Maintainer answer (2026-06-07):* Keep the original answer in this router; copy/link a
> concise durable conclusion to its home.

Kept as guidance — confirms §7 and §14 (this is now how this file operates).

### Q-0005 — Challenging impossible/unsafe answers → **C: explain, cite, propose, confirm**

> *Maintainer answer (2026-06-07):* Explain the conflict plainly, name the source/risk,
> propose safer alternatives, and ask for confirmation before proceeding.

Kept as guidance — confirms the reproposal rule (§8) and CLAUDE.md act-vs-ask.

## 13. Routed answers

| Answer | Routed to | Concise conclusion copied |
|---|---|---|
| **Q-0001** — AI may eventually gain broader actions (owner intent, still fully gated) | `docs/subsystems/ai.md` | owner-intent note + "stays behind all AI gates + a dedicated decision; not approved now" |
| **Q-0002** — Discord-first, web companion possible later | `docs/subsystems/server-management.md` | one-line product-direction note |

Original answers stay preserved in §12; these destinations carry only the concise
durable conclusion (one fact, one home).

## 14. General owner intent that should stay here

The maintainer has explicitly established these rules for this router:

- Maintainer answers are leading owner intent by default.
- Agents must preserve original answer blocks and must not silently ignore, rewrite,
  or reinterpret them.
- Unanswered questions are not approval.
- Agents route concise durable conclusions to the correct home while preserving the
  original answer here.
- Agents must explain and re-propose, rather than blindly implement, answers that are
  impossible, unsafe, inefficient, too costly, or conflict with binding decisions.
- This router is owner-facing guidance, not a planning system or gate bypass.

## 15. Related future questions / captures

These are **capture-only future ideas**, not questions answered by the maintainer and
not approved implementation work. If reviewed later, route them through
`docs/ideas/README.md` and preserve existing owners rather than creating parallel
systems.

| Capture | Future question | Existing systems/constraints to preserve |
|---|---|---|
| **Owner-question workflow follow-up** | After real usage, does this router need a smaller index, archive convention, or batch-answer guide? | Keep this docs-only unless a separately approved need proves otherwise; do not create a planning system. |
| **Source confidence field for readiness cards** | Should readiness facts expose owner/source, observed time, freshness, and confidence? | Extend typed health facts and `ReadinessSnapshot`; no second dashboard or monitor. |
| **Decision Preview Contract** | Should policy/config/provisioning previews share a reusable shape? | Reuse owning read models, capability checks, provisioning previews, and service-owned mutation paths. |
| **Read-only AI answer envelope** | Should AI explanations consistently show answer, evidence used, stale/missing facts, risk, manual next actions, and forbidden actions not taken? | Remain read-only and grounded behind AI-readiness/orchestration gates. |
| **Operator incident digest** | Should owners receive a startup/restart digest over existing health and log facts? | Owner-gated, read-only, privacy-safe, and built over existing diagnostics/logging facts. |
| **Fact ownership map before audit timeline** | Which domain owns every fact before a unified audit/event timeline read projection is considered? | Complete the ownership/redaction/retention map first; do not create another event or audit-write pipeline. |

## 16. Plain-language glossary

| Term | Plain-language meaning |
|---|---|
| **Owner intent** | What the maintainer wants the product or working process to achieve. |
| **Leading** | The default direction agents should follow unless a concrete conflict or risk requires reproposal. |
| **Safe default** | Temporary behavior while waiting for an answer; it is not approval. |
| **Route** | Copy or link a concise conclusion to the one doc that should own it. |
| **Binding decision** | A rule or decision agents must not override casually. |
| **Promotion** | The normal review path that turns an idea or answer into approved planned work. |
| **Reproposal** | A fair explanation of why the original answer cannot safely be followed, plus a safer alternative for maintainer confirmation. |

## 17. AI roadmap decision batch — AR-2026-06-07

> **Status:** Awaiting maintainer answer. These questions come from
> `docs/planning/ai-roadmap-2026-06-07.md`. Safe defaults are temporary and do not
> approve implementation. Preserve answers here, then route concise conclusions to the
> suggested destination.

### AR-01 — Which AI-adjacent track should follow orchestration?

**Area:** AI / Priority
**Priority:** High
**Suggested destination after answer:** AI roadmap / current-state only if promoted

**Question:** After the shared AI orchestration foundation is planned, should the next
planning track be Update Awareness or command/help/discovery metadata?

**Why it matters:** Update Awareness directly serves release confidence, while richer
command metadata gives update/help features cleaner stable identifiers and audiences.

**Options:** A. Update Awareness first. B. Command/help metadata first. C. Plan both,
but implement command metadata first. D. Defer both.
**Safe default / recommended direction:** C — plan both dependencies, implement the
smallest compatibility-first command metadata slice before release-linked features.

### AR-02 — How should updates enter the canonical update log?

**Area:** Update Awareness / Product
**Priority:** Blocking for Update Awareness PR1
**Suggested destination after answer:** Update Awareness implementation plan

**Question:** How should a release/update first become structured bot truth?

**Why it matters:** Automatic PR/Markdown import is convenient but can silently make
unreviewed text runtime truth.

**Options:** A. Manual structured registration only. B. Manual first, later offer a PR
metadata draft that a human confirms. C. Automatic PR import. D. Both manual and
automatic without confirmation.
**Safe default / recommended direction:** B — manual authoritative records first; a
future importer may only prepare a reviewable draft.

### AR-03 — What should “tested since update” mean?

**Area:** Update Awareness / Release confidence
**Priority:** Blocking for test-status design
**Suggested destination after answer:** Update Awareness plan and read-model contract

**Question:** Which signals should count, and should they remain separate?

**Why it matters:** A command succeeding once does not necessarily prove a feature was
intentionally verified.

**Options:** A. Any successful command execution counts as tested. B. Only owner/staff
manual verification counts. C. Only CI/smoke verification counts. D. Track runtime-used,
manual-verified, CI-smoked, and failed separately.
**Safe default / recommended direction:** D — preserve separate facts; never collapse
runtime use into verified truth.

### AR-04 — Should update/test status be global, guild-specific, or both?

**Area:** Update Awareness / Data model
**Priority:** High
**Suggested destination after answer:** Update Awareness plan

**Question:** At what level should release-confidence facts be stored and shown?

**Why it matters:** Global releases are platform facts, while some command paths depend
on guild configuration and permissions.

**Options:** A. Global only. B. Guild-specific only. C. Global release status plus
optional guild-specific evidence. D. Decide per feature without a shared rule.
**Safe default / recommended direction:** C — global canonical update truth with bounded
optional guild evidence where configuration makes it meaningful.

### AR-05 — Who may see update and test status?

**Area:** Update Awareness / Audience
**Priority:** Blocking before user-facing surfaces
**Suggested destination after answer:** Update Awareness plan / AI folio

**Question:** Who should see recent updates, guide cards, untested paths, and failures?

**Why it matters:** Public guides help users, but detailed failures and verification gaps
may expose owner-only operational information.

**Options:** A. Platform owner only. B. Server admins and platform owner. C. Public-safe
updates/guides for users, detailed test/failure state for admins/owner. D. Everything to
everyone.
**Safe default / recommended direction:** C, with the first deterministic surface owner-
only until the projection is proven.

### AR-06 — Should every user-visible PR require a feature guide card?

**Area:** Update Awareness / Workflow
**Priority:** Medium
**Suggested destination after answer:** collaboration workflow / Update Awareness plan

**Question:** Should a structured “what changed / how to use it / who can use it” card be
required for every user-visible change?

**Why it matters:** Required cards improve help/update quality but add maintenance work
and need a clear exception path.

**Options:** A. Required for every user-visible PR. B. Required only for major changes.
C. Recommended, not required. D. No guide cards.
**Safe default / recommended direction:** B — require them for major/new user-visible
features first, then evaluate burden and coverage.

### AR-07 — Which docs may the AI knowledge base search?

**Area:** AI knowledge / Privacy
**Priority:** Blocking for knowledge-search planning
**Suggested destination after answer:** approved-corpus plan / AI folio

**Question:** Should AI search only user-safe documentation, or also internal planning
and owner docs for restricted audiences?

**Why it matters:** Internal docs contain useful context but may include stale plans,
operational detail, or owner-only information.

**Options:** A. User-safe docs only. B. User-safe plus a separately classified owner-only
corpus. C. All repo docs with runtime filtering. D. No docs search.
**Safe default / recommended direction:** A for v1; consider B only after classification,
audience-isolation, freshness, and secret-leak tests exist.

### AR-08 — Which AI capabilities belong to each audience?

**Area:** AI / Permissions
**Priority:** High
**Suggested destination after answer:** AI folio / capability-specific plans

**Question:** What broad capability posture should normal users, server admins, and the
platform owner receive?

**Why it matters:** A consistent posture prevents every future tool from inventing its
own access model.

**Options:** A. Users get public help/BTD6; admins get guild setup/health; owner gets
platform/update/connector detail. B. Admins and users receive the same reads. C. Owner-
only for all net-new AI capabilities. D. Decide every tool independently.
**Safe default / recommended direction:** A, while each deterministic owner may narrow
further and no role inherits action authority from read access.

### AR-09 — Should AI ever prepare action drafts, and what category comes first?

**Area:** AI actions / Safety
**Priority:** High but not blocking read-only work
**Suggested destination after answer:** future action-proposal decision / AI folio

**Question:** After all action gates exist, should AI be allowed to prepare a reviewable
action draft, and which low-risk category should be considered first?

**Why it matters:** Q-0001 permits eventual broader actions in principle, but does not
approve a category or implementation.

**Options:** A. Keep explanation-only indefinitely. B. First consider a recurring-report
draft. C. First consider a notification draft to an allowlisted target. D. First consider
an owner-only maintenance-action draft.
**Safe default / recommended direction:** A now; if revisited, B is the lowest-risk first
category because deterministic automation can own confirmation and execution.

### AR-10 — What is the preferred first Opus planning target?

**Area:** AI / Workflow
**Priority:** High
**Suggested destination after answer:** AI roadmap / session handoff

**Question:** Which focused Claude Opus planning session should happen first after this
roadmap?

**Why it matters:** The roadmap is intentionally broad; a single explicit next target
prevents parallel plans from competing or silently implying approval.

**Options:** A. Lock the AI orchestration foundation. B. Plan deterministic Update
Awareness PR1. C. Plan command/help/discovery metadata. D. Plan approved-docs search.
**Safe default / recommended direction:** A — it is the shared safety and compatibility
foundation for every later AI tool.

## 18. AR batch — answered (2026-06-07)

The maintainer answered the **decision-gating** AR questions on 2026-06-07, after an Opus
review of the AI roadmap ([`../planning/ai-roadmap-2026-06-07.md`](../planning/ai-roadmap-2026-06-07.md)).
Answers are leading owner intent; they do **not** approve implementation — each phase still
needs source-verified Opus planning and the normal promotion path.

### Answered now (these gate the next move)

- **AR-10 → A. Lock the AI orchestration foundation.** The first focused Opus AI planning
  session locks the shared orchestration foundation (tool descriptors / toolsets / budgets /
  evidence envelope). **Net-new AI tools wait until that is locked.** Routed → `docs/subsystems/ai.md`
  + `docs/roadmap.md` (AI section).
- **AR-08 → A. Tiered by audience.** Standing posture: users → public help / BTD6; admins →
  guild setup / health; owner → platform / update / connector detail. **Read access never
  confers action authority**, and each deterministic owner may narrow further. Routed → `docs/subsystems/ai.md`.
- **AR-09 → A now (explanation-only); a recurring-report draft is the first category *if*
  ever revisited.** Confirms today's read-only posture; sets the eventual first action
  category as *direction only* — still behind all AI gates + a dedicated decision (Q-0001).

### Deferred — safe default holds until the lane is active

AR-01 (next track after orchestration), AR-02–AR-06 (Update-Awareness import / "tested
since update" / scope / audience / guide-card policy), and AR-07 (knowledge-base corpus)
are **not** decided yet. Each question's recommended safe default applies provisionally;
revisit when that lane is greenlit. Unanswered ≠ approval.

## 19. Server-management PR10 decision batch — answered (2026-06-07)

Two decisions gating the **remaining PR10 items** (the cross-cutting moderation work).
Answers are leading owner intent; they do **not** by themselves approve implementation —
mod-roles still needs an ADR + the normal review path.

### Q-0006 — How should a configured moderator role grant authority?

**Area:** Server management / Architecture / Safety
**Type:** Architecture
**Priority:** High (gates the last PR10 item; changes *who can ban members*)
**Status:** Answered (2026-06-07) — **Routed** → [ADR-008](../decisions/008-moderator-role-capability-native-authority.md) (implemented 2026-06-07)
**Suggested destination after answer:** `docs/decisions/` (ADR) + server-management folio/tracker

**Question:** Mod/trusted roles + capabilities lets non-admins moderate. Should a
configured role (a) resolve to the existing `moderator` tier routed through the
capability resolver, (b) drive a full general per-capability tier matrix, or (c) be a
cog-level allowlist beside Discord perms?

**Why agents need this:** `capability-authority.md` §5 deliberately defers the
per-capability tier matrix to "revisit per the ADR-005 re-evaluation criteria"; this is
the single highest-stakes change in the server-management plan.

**Maintainer answer**

```text
Answer: A — "Role → moderator tier" (capability-native).
A configured role resolves to the existing `moderator` tier; route the mod cog +
panel/modals through the capability resolver so moderation needs `moderator` (not the
admin floor). Reuses the tier system + the documented `moderation.*.apply` capabilities,
scoped to moderation.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Build behaviour-preserving: PRESERVE the existing Discord-perm checks as an alternative
allow so no one currently able to moderate loses access — the configured role only
*grants*. Wire trusted_tier_role_id (currently inert) symmetrically. The sync
get_member_visibility_tier stays UI-only; execution authority needs an async role-aware
resolver. Record the model in a new ADR + thorough authority tests (grant via role, no
escalation, no regression, cross-guild deny) when implemented.
```

**Routing result**

```text
Destination: docs/decisions/008-moderator-role-capability-native-authority.md (the ADR,
  implemented 2026-06-07) + the server-management tracker's PR10 record + folio +
  capability-authority.md §5/§6.
Moved/copied on: 2026-06-07 — implemented: a configured moderator_role grants the
  `moderator` tier via governance.resolver._resolve_member_tier; OR-gated on the mod cog +
  panel (behaviour-preserving); settable in the Settings hub (admin floor); trusted_role
  wired symmetrically. Answer A built as specified.
Notes: ADR-008 is the decision of record; current-state.md ▶ Next action now points at PR11.
```

### Q-0007 — What should a PUBLIC moderation-log entry reveal?

**Area:** Server management / Privacy
**Type:** UX / Safety
**Priority:** Medium
**Status:** Answered (2026-06-07) — **Routed** (shipped in the public-log slice)
**Suggested destination after answer:** server-management folio + `docs/server-logging.md`

**Question:** For the optional public moderation log (default-OFF, operator opt-in), what
should a public entry show — given reason text can contain sensitive details?

**Maintainer answer**

```text
Answer: "Include reason, not mod."
Public entries show the action + affected member + reason, but NOT which moderator acted.
```

**Routing result**

```text
Destination: docs/server-logging.md (public-log section) + the server-management folio.
Moved/copied on: 2026-06-07 — implemented: format_public_log_embed shows member + reason,
  no actor; the staff mod-log keeps the full record.
Notes: one fact, one home — server-logging.md owns the embed-content contract.
```

### Q-0008 — How far to take PR11 (setup role/moderation/governance sections)?

**Area:** Server management / Setup wizard
**Type:** Scope / Sequencing
**Priority:** Medium
**Status:** Answered (2026-06-07) — **Routed** (built this session)
**Suggested destination after answer:** server-management tracker (Remaining queue) + folio

**Question:** PR11 nominally bundles three setup-wizard sections (roles, moderation,
governance). Source analysis showed the **moderation** section maps cleanly onto the
existing `set_setting` dispatch (no new infra), **roles** (time/XP automation) needs a
small new `set_role_threshold` op-kind, and **governance** is ambiguous in scope — its
main write (cleanup policy) is already a wizard section, so what remains
(capability-overrides / command-access) is a distinct feature needing its own design.
How far should PR11 go this session?

**Maintainer answer**

```text
Answer: "Moderation + Roles."
Build the Moderation setup section and the Roles setup section (with the new
set_role_threshold op-kind) this session. Defer the Governance section.
```

**Routing result**

```text
Destination: docs/planning/server-management-status-2026-06-05.md (Remaining queue) +
  the server-management folio + docs/current-state.md (▶ Next action).
Moved/copied on: 2026-06-07 — built: views/setup/sections/moderation.py (set_setting
  drafts for dm_on_action / require_reason / warn_escalation_action / moderator_role) and
  views/setup/sections/roles.py (set_role_threshold drafts for time/XP tiers), plus the
  new set_role_threshold op-kind routed through services.role_automation.set_{time,xp}_
  threshold. Governance section deferred — cleanup already covers the main governance
  write; capability-override/command-access setup is a separate, design-led follow-up.
Notes: the server-management tracker owns the PR11→PR14 queue; governance setup is not yet
  a committed PR11 deliverable and needs a scope decision before it is built.
```

### Q-0009 — How much autonomy do agents have to shape the workflow itself?

**Area:** Workflow / Meta (the self-improving ecosystem)
**Type:** Autonomy boundary
**Priority:** High
**Status:** Answered (2026-06-07) — **Routed**
**Suggested destination after answer:** `docs/collaboration-model.md` + `.claude/CLAUDE.md`
+ `.session-journal.md` (REVIEW/Authority)

**Question:** The journal said durable workflow rules only land in CLAUDE.md/hooks with
per-rule maintainer approval. The vision (AI runs the workflow, owner oversees vision)
suggests agents could self-improve the workflow faster. How much autonomy for shaping the
workflow?

**Maintainer answer**

```text
Answer: "Docs free, ask for config."
Free rein to improve docs / journal / orientation / folios without asking. Ask before
changing executable config — hooks, .claude/settings.json, or the binding *rules* in
.claude/CLAUDE.md (architecture / CI / layer rules).
```

**Routing result**

```text
Destination: docs/collaboration-model.md § "Why this system exists" (the boundary) +
  .claude/CLAUDE.md Working-agreement bullet + .session-journal.md REVIEW + Authority.
Moved/copied on: 2026-06-07 — encoded the boundary in all three. Adding a pointer/ethos to
  CLAUDE.md counts as docs; adding an enforced rule or a hook counts as config (ask).
Notes: this is the operating rule for the self-improving-ecosystem loop.
```

### Q-0010 — Do you want the top-level docs/ pile actively shrunk?

**Area:** Docs / Workflow
**Type:** Scope / Priority
**Priority:** Medium
**Status:** Answered (2026-06-07) — **Routed**
**Suggested destination after answer:** `docs/current-state.md` Next candidates +
`scripts/check_docs.py` census ratchet

**Question:** The top-level `docs/` pile is 41 files; the new census ratchet stops growth.
Long-term, do you want a dedicated session to actively shrink it (move plans/audits/
historical into subdirs behind the folios, target ~15)?

**Maintainer answer**

```text
Answer: "Schedule it soon."
A near-term dedicated docs session does the 41 → ~15 consolidation, then lowers the ratchet.
```

**Routing result**

```text
Destination: docs/current-state.md "Next candidates" (scheduled item) + the
  _TOP_LEVEL_DOCS_BUDGET ratchet comment in scripts/check_docs.py.
Moved/copied on: 2026-06-07 — recorded as a near-term docs lane. The census prints the live
  count every run; the ratchet holds the line until the consolidation lowers it.
Notes: consolidation moves content into subdirs behind folios — it does not delete content;
  reachability + freshness gates must stay green.
```

### Q-0011 — What should the deferred governance setup section configure?

**Area:** Server management / Setup wizard
**Type:** Scope
**Priority:** Medium
**Status:** Answered (2026-06-07) — **Routed** (records intent; not built yet)
**Suggested destination after answer:** server-management status tracker (PR11 subsection)

**Question:** PR11's deferred "governance" setup section — what should it eventually
configure, if anything?

**Maintainer answer**

```text
Answer: "Capability overrides + Command-access policy."
The governance section, when built, should configure (1) per-guild capability overrides
(delegate moderation/admin to a role) and (2) command-access policy (which channels the bot
responds in).
```

**Routing result**

```text
Destination: docs/planning/server-management-status-2026-06-05.md (PR11 "Remaining" note).
Moved/copied on: 2026-06-07 — scope recorded: capability_execution_overrides (governance) +
  command_access_service, staged through Final Review like other sections, likely via new
  set_capability_override / set_command_access op-kinds (mirroring set_cog_routing). Not
  started; sequence after PR12 unless pulled forward.
Notes: this is intent capture, not approval to build now.
```

### Q-0012 — Should each session record a structured "context delta"?

**Area:** Workflow / Meta (the self-improving ecosystem)
**Type:** Process
**Priority:** High
**Status:** Answered (2026-06-07) — **Routed**
**Suggested destination after answer:** `.sessions/README.md` template + `.session-journal.md`
(END + REVIEW)

**Question:** To make "every session improves the next" measurable, should each session log
a short structured "context delta" — what it needed vs. what orientation pointed it to, and
what it had to discover by hand — that a periodic review mines to promote recurring gaps?

**Maintainer answer**

```text
Answer: "Yes, in the log template."
Add a required short "context delta" field to the .sessions/ log template + a REVIEW step
that mines it.
```

**Routing result**

```text
Destination: .sessions/README.md (required Context-delta section in the convention) +
  .session-journal.md END protocol (write it) + REVIEW step (mine it) +
  docs/collaboration-model.md § "Why this system exists" (the loop).
Moved/copied on: 2026-06-07 — added the three-bullet Context-delta field (needed-not-pointed /
  pointed-not-needed / discovered-by-hand) and the REVIEW mining step.
Notes: this is the measurement that turns "hopefully better" into "demonstrably better".
```

### Q-0013 — Agent stage spec batch (60 questions, 2026-06-08)

**Area:** Workflow / Meta
**Type:** Workflow / Process
**Priority:** High
**Status:** Answered (2026-06-08) — **Routed** → `docs/owner/agent-workflow-spec.md`
**Suggested destination after answer:** `docs/owner/agent-workflow-spec.md` +
`docs/AGENT_ORIENTATION.md` + `docs/owner/README.md` + `docs/owner/ai-project-workflow.md`

**Question:** A 60-question multiple-choice batch defining the operational spec for every
stage of the multi-agent pipeline: Analysis, Decisions, Revision, Prompt Forge, and the
Executor agent. Covers stage scopes, output formats, prompt anatomy, cross-cutting rules
(truth layers, ideas routing, gate checks, act-vs-ask), and where the answers should live.

**Maintainer answer**

```text
All 60 answers confirmed recommended directions, with one exception:
Q22 — Should prompts include a handoff section? Maintainer chose C (Never) over
recommended B (cross-stage only). No handoff section in generated prompts.
```

**Routing result**

```text
Destination: docs/owner/agent-workflow-spec.md (new dedicated spec doc; canonical home
  for all 60 decisions); wired into docs/AGENT_ORIENTATION.md ("Working on the
  multi-agent pipeline" task route), docs/owner/README.md, and
  docs/owner/ai-project-workflow.md §2.
Moved/copied on: 2026-06-08.
Notes: ChatGPT projects (Analysis, Decisions, Revision, Prompt Forge) should use
  agent-workflow-spec.md as their operational reference.
```

### Q-0014 — Executor latitude: tooling, prerequisites, branch, disagreement (2026-06-08)

**Area:** Workflow / Meta (Executor stage)
**Type:** Process / Autonomy
**Priority:** High
**Status:** Answered (2026-06-08) — **Routed** → `.claude/CLAUDE.md`
**Suggested destination after answer:** `.claude/CLAUDE.md` (binding rules);
`docs/owner/maintainer-working-profile.md` §2 (working-style color)

**Question:** End-of-chat Q&A in the PR12 session — standing executor-autonomy preferences on
(1) which branch to work on, (2) latitude to adopt tools/packages, (3) requests that need an
unstated prerequisite step, (4) how much friction when the executor sees a better path or
disagrees.

**Maintainer answer**

```text
Branch: "it doesn't matter to me on which branch you work or create a PR, as long as they
  are all shipped in logical modular batches." (The strict "develop only on branch X" rule
  is session-PROMPT-TEMPLATE residue — grep finds it nowhere in the repo.)
Tooling: "you are free to download and try any package available, and implement anything
  that's verifiable, but state why you did it and note when this was added and that it
  should be verified for consistency a few times before trusted."
Prerequisites: "if there was just a step required to do before being able to actually do the
  thing I asked for, you can see that as me giving you permission to execute it fully ...
  when I approve a certain function I give you the freedom to get there in the way you think
  is best, as long as the final output is structured and matches the intended idea."
Disagreement / better way: "if you think my proposed direction is not the right next step you
  should state why" + "if you think my idea is not logical because there is a better way to
  do it, assume I only stated it in such a way because I am unaware of the better plan."
```

**Routing result**

```text
Destination: .claude/CLAUDE.md —
  · Tooling bullet (Session & plan workflow): "custom over new deps" relaxed — a verifiable
    package is fair game with a provenance header (why + date + "unverified: confirm a few
    times before trusting"); dev-deps stay lazy + pytest.importorskip, runtime-deps pinned.
  · Session-workflow: "branch identity is not significant; ship in logical modular PRs."
  · Working agreement (Constraints serve the goal): goal-approval = path-approval — execute an
    unstated prerequisite to an approved goal (don't refuse on a missing-step technicality);
    take a better implementation than the one stated and say why; bound = output stays
    structured + matches the intended idea.
  Also: docs/owner/maintainer-working-profile.md §2 — the concurrent-chat working style.
Moved/copied on: 2026-06-08 (this session).
Notes: routed to CLAUDE.md (binding), NOT only maintainer-working-profile.md (the maintainer's
  literal suggestion) — per one-fact-one-home these are executor RULES, and the tooling rule
  CONTRADICTED the old "custom over deps / ask first," so CLAUDE.md had to change or the old
  rule wins. The "state disagreement / propose alternative" half was already in
  maintainer-working-profile.md §4 + agent-workflow-spec.md §7.2 — not restated. Relax the
  strict-branch rule in the session-prompt template, not the repo.
```

### Q-0015 — The system's purpose: productivity-per-step + the idea conveyor (2026-06-08)

**Area:** Workflow / Meta (the self-improving ecosystem)
**Type:** Vision / Process / Autonomy boundary
**Priority:** High
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** `docs/ideas/README.md` (the lifecycle) +
`docs/collaboration-model.md` + `.claude/CLAUDE.md` (session workflow) +
`docs/owner/agent-workflow-spec.md` §7.6 + `.session-journal.md` (END protocol)

**Question:** What is the docs/workflow system actually optimizing for — and how should an
idea the maintainer drops at random flow to "done"?

**Maintainer answer**

```text
On the goal (NOT full autonomy):
"it's not intended to be 100% autonomous ... there are still steps that require my
verification and multi agent revisions, and that is a deliberate step so this project
stays managable and reviewable. The goal of this is to make each step more productive, and
to make the actual building session be able to execute more things in one session because
similar ideas and problems are mapped and laid out ... prompting them to increase
productivity by verifying files, coming up with improvements, and generally improving the
workflow once the context is clear, so an agent knows where to start and where to stop and
what its role is in the process."

On the idea conveyor:
"the goal should be for me to be able to enter ideas on a random basis, these ideas should
be mapped, and then the agents should route these ideas to reasonable places in the
roadmap, if an idea seems too excessive etc it should first be discussed, but eventually
all ideas should either be implemented or discussed. So the goal of this is also to guide
agents into following up with extra tasks once their session is done, like browsing the
idea folder, finding something that can be promoted into the roadmap, maybe it's something
small they can execute immediately or create into a more structured plan for the next
agent ... so an agent always has something to do other than its main task."
```

**Agent interpretation (not a rewrite of the answer)**

```text
Two durable rules:
1. The human-verification + multi-agent-revision gates are DELIBERATE and stay — the
   system optimizes for productivity-PER-STEP and role clarity (where to start / stop /
   what's my role), NOT for removing the maintainer from the loop. Do not add
   "agent self-approves a plan unmonitored" behavior.
2. The idea backlog is a productive conveyor: random intake → map → route (roadmap horizon
   / structured plan / discuss-if-excessive via this router) → groom → every idea ends
   implemented or discussed (never orphaned). Grooming the backlog is the standing
   end-of-session SECONDARY TASK so an agent always has a next thing to do.
```

**Routing result**

```text
Destination: docs/ideas/README.md (rewritten as the canonical idea lifecycle + grooming
  secondary task); docs/collaboration-model.md ("What a good session looks like" — the
  productive-queue ethos); .claude/CLAUDE.md (Session & plan workflow — the grooming-pass
  pointer); docs/owner/agent-workflow-spec.md §7.6 (Executor secondary task);
  docs/owner/ai-project-workflow.md §4 (pipeline-level link); .session-journal.md END
  protocol (the grooming step); docs/roadmap.md (ideas route onto a horizon).
Moved/copied on: 2026-06-08 (this session — the docs-management + idea-lifecycle batch).
Notes: rule 1 explicitly REPLACES the earlier "unmonitored-mode / self-approval" direction a
  draft of this session proposed — the maintainer clarified that is not the goal. Uses
  existing homes (roadmap horizons, this router, the rejection ledger, ai-project-workflow
  §5 idea-states); NO parallel tracker created.
```

### Q-0016 — Should the Server Management hub be a first-class subsystem? (2026-06-08)

**Area:** Server management (PR14 hub) / Architecture
**Type:** Architecture / Product surface
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** `docs/planning/server-management-status-2026-06-05.md`
(PR14 subsection) + `docs/subsystems/server-management.md` + this file.

**Question:** PR14's hub was built as a registered `PersistentView`, but a persistent view
whose `SUBSYSTEM` is not in `SUBSYSTEMS` is an `auto_healable` identity-contract orphan, and
every other hub (admin/moderation/settings/games/…) is a registered subsystem. Resolve by
(1) registering `servermanagement` as a first-class subsystem + hub, (2) a non-persistent nav
`HubView` (drops restart-persistence), or (3) shipping as-is with two advisory diagnostics + the
self-heal footgun?

**Maintainer answer**

```text
Make it a first-class subsystem.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Durable rule: an operator HUB is a first-class subsystem, consistent with every existing hub
(admin/moderation/settings/games/community/utility/diagnostic/economy/btd6). A new hub gets a
SUBSYSTEMS + HUBS entry (administrator tier for operator hubs) so it is help-discoverable and
the identity-contract / orphan-cog / db-anchor diagnostics stay clean. Do NOT ship a registered
PersistentView whose SUBSYSTEM has no SUBSYSTEMS entry — that leaves an auto_healable orphan the
platform's own self-heal would unregister. The registry key follows cog_name_to_subsystem (e.g.
servermanagement, no underscore); module paths may stay readable (server_management).
```

**Routing result**

```text
Destination: server-management status tracker (PR14 subsection, "registered first-class");
  server-management folio (current state); this Q-block.
Implemented this session: SUBSYSTEMS["servermanagement"] + HUBS entry (administrator),
  KNOWN_PANEL_COMMANDS entry, the hub view/cog/service, and the help/discoverability
  enumerations updated. Live boot: identity-contract clean (STRICT=on), 0 ERROR/CRITICAL.
Moved/copied on: 2026-06-08 (this session — server-management PR14).
Superseded note (2026-06-08, Q-0026): the registry key was renamed servermanagement →
  server_management when cog_name_to_subsystem was fixed to snake_case. The interpretation
  above (key "follows cog_name_to_subsystem, no underscore") was correct only against the
  then-buggy collapsing function; the canonical key is now server_management. The
  !servermanagement command name is unchanged.
```

---

### Q-0017 — Adaptive Setup/Access/Routine Platform: planning document structure (2026-06-08)

**Area:** Setup / Access / Automation platform (new)
**Type:** Planning process / Doc organization
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** Brief note in `docs/ideas/` capture file for this
  platform (once created); the planning doc itself in `docs/planning/`.

**Question:** The Adaptive Setup, Access, Preset, and Routine Platform covers 8 distinct
concepts (Guild Feature Profiles, Unified Access Map, Help Preview, Setup Health, Preset
Loader, Routine Engine, Time-based Unlocks, Personal Setup Wizard). Should Codex produce
one comprehensive planning doc in `docs/planning/`, a summary capture in `docs/ideas/` plus
a planning doc in `docs/planning/`, or separate planning docs per major concept?

**Maintainer answer**

```text
One comprehensive doc in docs/planning/
```

**Agent interpretation (not a rewrite of the answer)**

```text
All 8 concepts should land in a single comprehensive planning doc in docs/planning/.
The doc should include the readiness matrix, phased roadmap, do-not-build section, and
file-ownership mapping — consistent with how server-management-roadmap and ai-roadmap
are structured. docs/ideas/ does not need a separate capture file for this platform;
the planning doc is the authoritative home.
```

**Routing result**

```text
Destination: the new planning doc in docs/planning/ (to be created by Codex).
  This Q-block is the durable record of the doc structure decision.
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0018 — Adaptive Setup/Access/Routine Platform: Guild Feature Profiles starter set (2026-06-08)

**Area:** Setup / Guild Feature Profiles
**Type:** Product definition
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** The Q-0017 planning doc (profiles section).

**Question:** Six example Guild Feature Profiles were proposed: Minimal Utility Bot,
Community Server, Game Server, Moderation Heavy, Private/Friends Server, BTD6-Focused
Server. Should Codex treat these 6 as the definitive starter set, limit to general-purpose
profiles only (parking BTD6-Focused Server until BTD6 ships), or revise/extend the set
based on what the subsystem registry actually models?

**Maintainer answer**

```text
Let Codex suggest revisions based on what the codebase subsystem registry actually models.
```

**Agent interpretation (not a rewrite of the answer)**

```text
The 6 profiles are a starting suggestion, not a fixed list. When Codex maps the repo,
it should compare the proposed profiles against the actual subsystem registry entries and
cog routing capabilities, then propose additions, name changes, or removals as warranted.
BTD6-Focused Server may be deferred or merged with Game Server depending on BTD6 readiness.
The planning doc should mark which profiles are implementable today vs. dependent on
features still in-flight.
```

**Routing result**

```text
Destination: Q-0017 planning doc (profiles section) — Codex incorporates this when
  building the doc.
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0019 — Adaptive Setup/Access/Routine Platform: Routine Engine default safety posture (2026-06-08)

**Area:** Routine Engine / Automation
**Type:** Architecture / Safety policy
**Priority:** High
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** The Q-0017 planning doc (Routine Engine section) +
  `docs/planning/` once the engine spec is written.

**Question:** When a Routine Engine trigger fires, should the default safety posture be
(1) conservative — all actions require an approval draft, (2) progressive — low-risk
actions auto-apply, medium/high-risk need approval, or (3) whitelist — nothing auto-applies
until the owner marks individual routines as trusted?

**Maintainer answer**

```text
Progressive: low-risk auto-applies, medium/high-risk needs approval.
```

**Agent interpretation (not a rewrite of the answer)**

```text
The Routine Engine's default posture is progressive. "Low-risk" actions (post/update
panel, send staff notification, enable quiet mode, hide/show help category, start setup
checklist) auto-apply. "Medium/high-risk" actions (apply feature profile, modify cog
routing, change command access, queue Final Review draft) create an approval draft and
notify staff. The planning doc must define the risk classification table explicitly so
implementers don't have to guess the line. Audit logging is mandatory for all actions
regardless of risk level.
```

**Routing result**

```text
Destination: Q-0017 planning doc (Routine Engine section) — the risk classification table
  and safety posture live there.
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0020 — Adaptive Setup/Access/Routine Platform: Personal Setup Wizard planning depth (2026-06-08)

**Area:** Personal Setup Wizard (/my-setup)
**Type:** Scope / Prioritization
**Priority:** Low
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** The Q-0017 planning doc (Phase 5 section).

**Question:** How much planning depth should Codex give the Personal Setup Wizard
(/my-setup, per-user preferences)? Options were: capture-only (short paragraph, park as
future), sketch the data model and privacy boundary only, or full Phase 5 spec covering
/my-setup, /my-preferences, onboarding checklist, timezone, help ordering, DM settings,
and account links.

**Maintainer answer**

```text
Full Phase 5 spec.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Even though /my-setup is Phase 5 (guild-level features not yet complete), Codex should
document it at full spec depth: user preference table shape, privacy layering
(global safety → guild → channel → role → user preference), /my-setup and /my-preferences
command surfaces, onboarding checklist, per-user timezone for reminders/routines,
personalized help ordering, DM notification settings, and optional per-feature
favorites/hiding. The spec should clearly mark which pieces depend on Phase 2-4
guild-level work completing first. The key invariant: user preferences can hide, sort,
or personalize but must not grant access.
```

**Routing result**

```text
Destination: Q-0017 planning doc (Phase 5 / Personal Setup Wizard section).
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0021 — Adaptive Setup/Access/Routine Platform: Routine Engine framing (2026-06-08)

**Area:** Routine Engine / Automation scheduler
**Type:** Architecture / Scope framing
**Priority:** High
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** Q-0017 planning doc (Routine Engine section).

**Question:** The repo already has a live automation system (`automation_scheduler`,
`automation_executor`, `automation_registry`) with trigger kinds (scheduled_time, interval,
member_join, setup_readiness_below, binding_missing, channel_inactive, manual) and action
kinds (send_message, assign_role, remove_role, notify_owner, post_readiness_summary,
post_leaderboard_summary, bind_channel, create_channel). The planning brief rates Samsung
Routines as "Low readiness," but most of the engine already exists. Should Codex frame Phase 4
as (1) extending the existing system, (2) replacing it with a broader design, or (3) treating
config-orchestration routines as a separate parallel system?

**Maintainer answer**

```text
Extend the existing system.

Existing: scheduled_time, interval, member_join triggers
Existing: send_message, assign_role, notify_owner, bind_channel actions
Gap: apply_feature_profile, switch_cog_routing, enable_quiet_mode actions
Gap: condition model (role_present, setup_stage_completed, event_active)
```

**Agent interpretation (not a rewrite of the answer)**

```text
The Phase 4 Routine Engine work is NOT a new engine — it is a targeted extension of the
existing automation_scheduler / automation_executor / automation_registry system.

What to add:
  Trigger kinds: (none new needed — existing set covers time, interval, and member_join)
  Condition model: new condition layer evaluated before action dispatch
    role_present, setup_stage_completed, event_active, cooldown_state, account_age
  Action kinds: config-mutation actions
    apply_feature_profile, switch_cog_routing_preset, enable_quiet_mode, hide_show_help_category,
    queue_final_review_draft
  Safety gate: apply the Q-0019 progressive posture — low-risk actions (send, notify,
    enable_quiet_mode, hide_show) auto-apply; config-mutation actions (apply_feature_profile,
    switch_cog_routing) create an approval draft.

The planning doc's readiness rating was wrong because it missed the existing automation
infrastructure. Codex should note this and reframe the effort as "medium readiness" with
a well-understood extension path.
```

**Routing result**

```text
Destination: Q-0017 planning doc (Routine Engine section) — Codex uses this framing.
  Also informs the readiness matrix update (automation_scheduler is Tier 1, not starting
  from scratch).
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0022 — Adaptive Setup/Access/Routine Platform: canonical naming — Profile vs. Preset (2026-06-08)

**Area:** Guild Feature Profiles / naming
**Type:** Domain language / Naming convention
**Priority:** High
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** Q-0017 planning doc (glossary/naming section) +
  code comments when the new concept is implemented.

**Question:** The repo already has `ServerPreset` in `automation_templates.py` meaning
"automation rule template" (welcome-message, daily-readiness-reminder, etc.). The planning
brief uses "preset" and "profile" loosely for Guild Feature Profiles. To avoid a naming
collision, should the canonical term be "Guild Feature Profile" (distinct from preset), should
both merge under the "preset" concept, or should existing ServerPresets be renamed to free up
the word?

**Maintainer answer**

```text
Guild Feature Profile = distinct concept; keep 'preset' for automation templates.

Guild Feature Profile: 'Community Server', 'Game Server', 'Moderation Heavy'
  → generates a setup draft with cog routing + command access + channel bindings

Automation Preset (existing): 'welcome-message', 'daily-readiness-reminder'
  → generates scheduled automation rules
```

**Agent interpretation (not a rewrite of the answer)**

```text
Canonical naming from this point forward:

  Guild Feature Profile  — a named server configuration bundle (which features are
    enabled/visible, where they live, who has access). Generates a setup draft via
    existing setup_operations primitives. Lives in a new service (feature_profiles or
    similar). Display name: "Feature Profile" or "Server Profile" in the Discord UI.

  Automation Preset (existing ServerPreset)  — an automation rule template that generates
    scheduled/triggered automation rules. Unchanged; no rename.

  Preset (in setup_operations context)  — already used for setup draft operations tagged
    with metadata.source = "preset:<slug>". This third meaning coexists but is internal
    only (not user-facing).

When implementing Guild Feature Profiles, avoid using the word "preset" in code symbols,
DB column names, or Discord UI strings for the new concept. Use "profile" instead.
```

**Routing result**

```text
Destination: Q-0017 planning doc (glossary section); implementation files for the new
  Guild Feature Profile service should follow this naming.
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0023 — Adaptive Setup/Access/Routine Platform: Help Preview audience access (2026-06-08)

**Area:** Help Preview
**Type:** Product / UX access control
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** Q-0017 planning doc (Help Preview section).

**Question:** Should `/help preview` (or however help preview is surfaced) be accessible to
any user for their own view, to staff/admins for cross-role diagnostic views, or both?

**Maintainer answer**

```text
Staff and admins only.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Help Preview is a setup diagnostic tool, not a self-service user feature. It is
restricted to staff and admin roles only. Regular users do not get a "what can I see?"
self-serve preview command. Rationale: it reveals the server's permission structure
(which roles see which features), which is operator-sensitive information.

The Phase 2 implementation should gate the command on the same capability level as other
setup/admin diagnostic commands (likely operator or administrator tier). A regular user
who wants to know "why can't I see command X?" should get a clear locked-reason message
from the command itself (see time-based unlock UX in the planning doc), not a preview tool.
```

**Routing result**

```text
Destination: Q-0017 planning doc (Help Preview section — access control constraint).
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0024 — Adaptive Setup/Access/Routine Platform: Access Map Phase 2 scope (2026-06-08)

**Area:** Unified Access Map
**Type:** Scope / phasing
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Routed**
**Suggested destination after answer:** Q-0017 planning doc (Access Map section).

**Question:** The Access Map is described as a "read model + editing surface." In Phase 2,
should it support editing (adjusting command access and cog routing directly from the map
view), or should it be read-only with editing remaining in the existing setup wizard?

**Maintainer answer**

```text
Read-only in Phase 2, editing in Phase 3.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Phase 2 Access Map: read-only diagnostic view only.
  Answers: who can use what, where, and what will they see.
  Combines: cog routing state, command access grants/denies, subsystem visibility,
    help visibility, setup visibility, channel/role scope.
  Does NOT allow mutation in Phase 2.

Phase 3 Access Map: add editing surface.
  Allow adjusting command access presets and cog routing profiles directly from the
  map, generating setup draft operations → Final Review flow.
  This is the "editing surface" part of the original description.

The read-only Phase 2 build lets the map be validated as accurate before trusting it
with mutations. All Phase 2 mutations still go through the existing setup wizard.
```

**Routing result**

```text
Destination: Q-0017 planning doc (Access Map section — phasing note).
Captured: 2026-06-08 (pre-Codex clarification session).
```

---

### Q-0025 — Subsystem/hub addition: scaffold script vs. doc guide (2026-06-08)

**Area:** Developer tooling / Subsystem onboarding
**Type:** Tooling / Process
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Needs routing**
**Suggested destination after answer:** `docs/ideas/` (backlog capture) + future
  implementation session; eventual home is `scripts/new_subsystem.py`.

**Question:** Adding a hub/subsystem requires ~8 coordinated edits (SUBSYSTEMS, HUBS,
KNOWN_PANEL_COMMANDS, build_help_menu_view, help-surface-map §1+§2, command-map section,
four enumeration tests) with no guide or automation. Should the fix be a canonical doc
checklist, a `new_subsystem.py` scaffold script, or a doc now + script as backlog?

**Maintainer answer**

```text
Build a scaffold script: new_subsystem.py
```

**Agent interpretation (not a rewrite of the answer)**

```text
The authoritative fix is a scaffold script (scripts/new_subsystem.py) that automates
the ~8 required touch-points when adding a new subsystem/hub:
  - Adds the SUBSYSTEMS entry
  - Adds the HUBS entry (if it's a hub)
  - Adds the KNOWN_PANEL_COMMANDS entry
  - Scaffolds stub cog / service / view files
  - Adds the help-surface-map §1+§2 entries
  - Adds the command-map ### section

Until the script is built, a checklist doc is acceptable as a stopgap. But the
canonical deliverable is the script. Capture as a backlog item in docs/ideas/.

The script should follow the tooling provenance rule (CLAUDE.md): custom tooling
built on the repo's own AST + architecture_rules/. No external scaffolding packages.
```

**Routing result**

```text
Destination: docs/ideas/ — capture as a backlog item with 'decided: build scaffold
  script' so it doesn't get re-debated.
Captured: 2026-06-08 (repo friction audit session).
Not yet implemented.
```

---

### Q-0026 — cog_name_to_subsystem: fix CamelCase → snake_case conversion (2026-06-08)

**Area:** Core runtime / Subsystem registry / Naming convention
**Type:** Technical debt / Bug fix
**Priority:** High
**Status:** Answered in chat (2026-06-08) — **Routed / implemented 2026-06-08**
**Suggested destination after answer:** `disbot/core/runtime/command_surface_ledger.py`
  (function fix) + any doc/comment that describes the subsystem key convention.

**Question:** `cog_name_to_subsystem` strips "Cog" and calls `.lower()` with no
CamelCase→snake_case conversion. `servermanagement` is the first multi-word subsystem
key (correct output would be `server_management`). Should the function be fixed to
do proper CamelCase→snake_case conversion (and the key renamed), a single-word-only
convention be documented, or both styles be tolerated?

**Maintainer answer**

```text
Fix the function — convert CamelCase → snake_case.
```

**Agent interpretation (not a rewrite of the answer)**

```text
Action required (a concrete implementation task, not just a doc note):

1. Update cog_name_to_subsystem in disbot/core/runtime/command_surface_ledger.py
   to do proper CamelCase → snake_case conversion after stripping "Cog":
     ServerManagementCog → strip "Cog" → ServerManagement → snake → server_management

2. Rename the subsystem key "servermanagement" → "server_management" everywhere:
   - utils/subsystem_registry.py SUBSYSTEMS dict
   - HUBS entry
   - KNOWN_PANEL_COMMANDS entry
   - Any string reference in views/services/tests that uses the literal key

3. The function fix is a one-time cost; the rename is a grep-and-replace. Together
   they make every future multi-word subsystem work correctly without manual key tricks.

4. Add a brief doc comment to the function noting the snake_case output contract.

Risk: medium — touches the identity-contract / diagnostics that key off subsystem names.
Run check_architecture.py + full test suite after the rename.
```

**Routing result**

```text
Destination: implementation task — disbot/core/runtime/command_surface_ledger.py +
  utils/subsystem_registry.py rename.
Captured: 2026-06-08 (repo friction audit session).
Implemented 2026-06-08 (Adaptive Setup Phase 0 / P0A): cog_name_to_subsystem now does a
  two-pass CamelCase → snake_case conversion; the SUBSYSTEMS / HUBS / KNOWN_PANEL_COMMANDS /
  PersistentView.SUBSYSTEM / panel-anchor key for the hub were renamed servermanagement →
  server_management; the same fix repaired the pre-existing collapse of ProofChannelCog →
  proof_channel and FourTwentyCog → four_twenty (both registry keys were already snake_case
  and had been silently orphaning). The user-facing !servermanagement command + aliases +
  /server-management slash are unchanged (command names, not subsystem keys). Regression
  tests pin the snake_case output contract so a future multi-word subsystem cannot regress.
```

---

### Q-0027 — Session prompt template contradictions: update the ChatGPT template (2026-06-08)

**Area:** Workflow / Session prompt
**Type:** Process / Template maintenance
**Priority:** Medium
**Status:** Answered in chat (2026-06-08) — **Kept here as general guidance**
**Suggested destination after answer:** This Q-block (action is external to the repo —
  the template lives in ChatGPT, not in the codebase).

**Question:** The ChatGPT session prompt template re-introduces two contradictions every
session: (1) "develop only on branch X / never push elsewhere" (overridden by Q-0014:
branch identity is not significant) and (2) "don't open a PR unless explicitly asked"
(overridden by CLAUDE.md standing rule: always create an end-of-session PR). Should the
ChatGPT template be updated, CLAUDE.md get an explicit override list, or agents just
resolve it from the binding docs?

**Maintainer answer**

```text
Update the ChatGPT template to remove the contradictions.
```

**Agent interpretation (not a rewrite of the answer)**

```text
The maintainer will update the ChatGPT session prompt template to:
  1. Replace the "develop only on branch X / never push elsewhere" line with a note
     that branch identity is not significant (Q-0014) and agents should use the
     session-assigned branch as a default but are not locked to it.
  2. Replace "don't open a PR unless explicitly asked" with a note that the standing
     rule is always create an end-of-session PR (CLAUDE.md Session & plan workflow).

Until the template is updated, agents should resolve the contradiction from CLAUDE.md
and Q-0014 as they do now. No repo-side change is needed; this is an external action
for the maintainer.

Note for agents: if you see these contradicting lines in a session prompt, treat them
as template residue and apply the binding repo rules (CLAUDE.md + this router).
```

**Routing result**

```text
Destination: kept here — the fix is external (ChatGPT template update by the maintainer).
  No code or doc change needed in the repo.
Captured: 2026-06-08 (repo friction audit session).
Action owner: maintainer (ChatGPT template).
```

---

## 20. Adaptive Setup/Access/Routine follow-up batch — 2026-06-08

> **Planning home:** [`docs/planning/adaptive-setup-access-routine-platform-2026-06-08.md`](../planning/adaptive-setup-access-routine-platform-2026-06-08.md).
> These questions begin where answered Q-0017–Q-0027 end. Safe defaults allow Phase 0/read-only work to continue; answers are required before the named mutation/privacy surfaces ship.

### Q-0028 — Which Guild Feature Profiles should form the first catalogue?

**Area:** Setup / Guild Feature Profiles
**Type:** Product definition
**Priority:** Medium
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §6.1 (catalogue set committed)
**Question:** After source mapping, should the first preview catalogue be **Essential Utility, Community Core, Games Community, Moderation Focused**, with **BTD6 Community** experimental/gated; or should any be added, removed, or renamed?

**Why agents need this:** The catalogue determines the versioned compiler contract, tests, and UI language. Registry presence alone is not enough to infer owner intent.

**Safe default until answered:** Build only catalogue/compiler infrastructure and previews; use the proposed set as examples, not a committed public catalogue.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Commit the proposed set** — Essential Utility, Community Core, Games Community, Moderation Focused, with BTD6 Community experimental/gated. The names are committed product language (compiler contract, tests, UI); profiles stay preview-only until the apply pipeline is separately approved.

**Suggested destination after answer:** Q-0017 planning doc §6.1 and future profile catalogue source.

### Q-0029 — Where does quiet mode belong?

**Area:** Access / Automation
**Type:** Ownership / Product behavior
**Priority:** Medium
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §6.5–6.6 (availability policy is sole owner)
**Question:** Should quiet mode be a central availability policy that routines may request, a routine-owned setting, or both with availability policy as the sole owner?

**Why agents need this:** Two owners would create disagreement between command availability, help, and routine state.

**Safe default until answered:** Availability policy owns effective quiet mode; a routine may only request a change through that canonical owner.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Availability policy owns it** — quiet mode is a central availability policy and the sole owner of effective state; a routine may only *request* a change through that owner. One source of truth: Help, command checks, and routines can never disagree.

**Suggested destination after answer:** Q-0017 planning doc §6.5–6.6 and ownership/runtime contracts if implemented.

### Q-0030 — When are rollback snapshots mandatory?

**Area:** Setup / Safety
**Type:** Safety / Mutation contract
**Priority:** High
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §8 Phase 3 (snapshots: compound + high-risk)
**Question:** Must every setup-draft apply capture an immutable before-state snapshot, only compound profile/routine applies, or only medium/high-risk applies?

**Why agents need this:** This changes Phase 3 storage, Final Review UX, audit linkage, and what “rollback” can honestly promise.

**Safe default until answered:** Require snapshots for compound profile/routine applies and any high-risk apply; retain explicit manual rollback notes elsewhere.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Compound + high-risk** — immutable before-state snapshots are mandatory for compound profile/routine applies and any high-risk single apply; simple low-risk edits keep lightweight undo notes instead.

**Suggested destination after answer:** Q-0017 planning doc §8 Phase 3, data model, observability; ownership/runtime contracts.

### Q-0031 — Approve the first profile/routine risk policy?

**Area:** Automation / Setup safety
**Type:** Safety classification
**Priority:** High
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §6.5 + future automation registry (policy approved as written)
**Question:** Is this starting policy correct: bounded messages/panels/notifications/checklists may auto-apply; routing, bindings, channel creation, thresholds, and multi-setting changes require approval; broad access/capability changes, role creation, and full profiles require high-risk approval; destructive role/permission/mass-channel changes never auto-apply?

**Why agents need this:** Q-0019 sets progressive posture but not the classification of each new action.

**Safe default until answered:** Any ambiguous configuration action queues Final Review; only clearly bounded messaging/notification actions auto-apply.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Approved as written** — bounded messages/panels/notifications/checklists may auto-apply; routing, bindings, channel creation, thresholds, and multi-setting changes require approval; broad access/capability changes, role creation, and full profiles require high-risk approval; destructive role/permission/mass-channel changes never auto-apply.

**Suggested destination after answer:** Q-0017 planning doc §6.5 and future automation registry/risk policy.

### Q-0032 — What should the Discord entry points be called?

**Area:** Access / Help UX
**Type:** Naming / Information architecture
**Priority:** Low
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan Phase 1 (staff-hub subpanels only; no new command names yet)
**Question:** Should Access Map and Help Preview be subpanels linked only from Server Management/Settings, named slash commands (for example `/access-map` and `/help-preview`), or both?

**Why agents need this:** Command names become subsystem/help/ledger identity contracts and should not be casually renamed later.

**Safe default until answered:** Build services first and expose later through existing staff hubs; do not reserve new command names.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Staff-hub panels only** — Access Map and Help Preview are subpanels reachable from Server Management / Settings; **no new top-level command names are reserved yet**. Names can be chosen later once the panels have been used; nothing locks in before the surfaces stabilize.

**Suggested destination after answer:** Q-0017 planning doc Phase 1 and future command/help maps.

### Q-0033 — How should Personal Setup account links begin?

**Area:** Personal Setup / Privacy
**Type:** Privacy / Product scope
**Priority:** High (before Phase 5)
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §6.7 (account links deferred entirely)
**Question:** Should Personal Setup eventually support a generic account-link framework, begin with specific domain-owned links (such as game profiles), or defer all account links until after preferences/onboarding ship?

**Why agents need this:** Generic links introduce cross-domain ownership, privacy, deletion/export, credential, and cross-guild questions that simple preferences do not.

**Safe default until answered:** Defer account links; ship privacy-bounded preferences/onboarding first when Phase 5 is approved.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Defer links entirely** — ship privacy-bounded preferences/onboarding first when Phase 5 is approved; account links return later as their own decision with the privacy/deletion/export questions answered. No cross-domain identity surface now.

**Suggested destination after answer:** Q-0017 planning doc §6.7 and a future privacy/data-ownership decision.

### Q-0034 — In a continuation session, how many lanes should I chain before pausing?

**Area:** Workflow / Execution cadence
**Type:** Workflow
**Priority:** Medium
**Status:** Answered (2026-06-08) — confirms existing `docs/collaboration-model.md` rule ("approved plan = execute without stopping"); no binding-doc edit needed, record kept here.
**Question:** When you say "continue with the plan," should I keep executing successive plan lanes (code+tests+PR) without pausing, pause after each shippable PR, or run to a phase boundary before reporting?

**Why agents need this:** This session shipped P0C → source re-scope → `routing_access_conflict` but checkpointed back after each; the cadence trades momentum against steering.

**Maintainer answer (2026-06-08):** **Chain lanes** — keep executing successive lanes; **pause only at a genuine architectural fork** (e.g. the audience-sim/governance decision) or a UX/product call that is the maintainer's. Over-checkpointing on a continuation directive is the anti-pattern.

**Suggested destination after answer:** Reinforces `docs/collaboration-model.md` (executor "approved plan = execute") + `docs/owner/maintainer-working-profile.md`.

### Q-0035 — How should agents handle binding-doc "dead weight" (e.g. heavy CodeGraph guidance)?

**Area:** Workflow / Docs autonomy
**Type:** Workflow / Autonomy boundary
**Priority:** Low
**Status:** Answered (2026-06-08) — Routed → `.session-journal.md` autonomy-boundary note (propose-first now covers CLAUDE.md *content*, not just enforced rules).
**Question:** When orientation in a binding file (`.claude/CLAUDE.md`) is heavier than its real usage — e.g. the CodeGraph reliability tiers went unused this session while `context_map.py` + the turn-key §16.5 recipe carried it — should I rebalance it myself, propose first, or only add (never trim)?

**Why agents need this:** Clarifies whether the "docs are free to improve" autonomy extends to *guidance* (not enforced rules) inside the one binding file every session reads.

**Maintainer answer (2026-06-08):** **Propose first, then apply** — surface the proposed change for a quick OK before editing `.claude/CLAUDE.md`. This tightens the autonomy boundary: even non-rule guidance in CLAUDE.md is propose-first; everything outside CLAUDE.md (journal, `docs/`, folios, orientation, planning) stays free-to-improve.

**Suggested destination after answer:** `.session-journal.md` autonomy-boundary note (done) + `docs/collaboration-model.md` "autonomy boundary" (propose-first when next editing that binding doc).

**Follow-up (2026-06-08):** the concrete instance — rebalancing the `.claude/CLAUDE.md` CodeGraph section — was proposed, its reasoning **verified against the source section** (the trust tiers + 5 critical safety rules are load-bearing; the v3.10→v3.11.2 verification narrative was changelog dead-weight), and **applied with maintainer approval**: condensed the version-provenance paragraph (kept the availability gotcha + revert instruction), kept every trust tier + critical rule intact, and added a task-size tool-routing note (`context_map` + turn-key recipe for contained work; CodeGraph for unfamiliar multi-file navigation).

### Q-0036 — Who authors the user-facing locked-reason denial copy (P1B)?

**Area:** Access / Help UX
**Type:** UX / Product copy
**Priority:** Medium (before the P1B denial-message integration)
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §6.3/§16.3 (Claude drafts, maintainer reviews in PR)
**Question:** When P1B wires `LockedReason.safe_text` into live command-access/availability denial paths, the strings in `access_projection._SAFE_TEXT` are what every denied user sees. Do you want to author/approve that copy yourself, or have me draft it for your later review?

**Why agents need this:** Denial messages are user-facing UX (the maintainer's design domain). The read-only drift providers (e.g. `routing_access_conflict`, shipped) don't touch this, but the denial-integration step does.

**Safe default until answered:** Keep `_SAFE_TEXT` an internal draft; do **not** wire it into live denial paths until the wording is confirmed. The read-only drift work proceeds independently.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Claude drafts, maintainer reviews** — the agent writes the full denial-copy set and presents it in a PR for the maintainer's read-through before any of it goes live. Nothing user-facing ships unseen; the maintainer keeps final word on tone without authoring from scratch.

**Suggested destination after answer:** Q-0017 planning doc §6.3 / §16.3 + the P1B denial-integration step.

### Q-0037 — BTD6 data provenance: dump vs. wiki precedence (2026-06-08)

**Area:** BTD6 data / extraction
**Type:** Data provenance / decision principle
**Priority:** Medium (governs every BTD6 cutover)
**Status:** Answered (2026-06-08) — Routed → `docs/btd6/btd6-gamedata-decode-status.md` provenance note + the `--bloons`/cutover tooling.
**Question:** When the game-data dump and the curated bloonswiki value disagree on a fact (e.g. BAD's DDT children, a bloon's health), which wins?

**Why agents need this:** BTD6 data is sourced from two places — the BTD Mod Helper dump (a direct export of the game's internal files) and curated bloonswiki prose. Cutovers (children/immunity shipped; tower stats pending) need a precedence rule so an agent doesn't have to ask per-field.

**Maintainer answer (2026-06-08):** **Always trust the dump wherever it is complete and accurate** — it's a direct copy of the game's internal files and is the most recent. So dump > wiki when the dump's value is present and unambiguous.

**Critical caveat (agent-added, earned this session):** "complete and accurate" requires reading the **right** model. The dump carries template/variant models that look internally consistent but aren't the canonical one — the base `Ddt` template is non-camo (spawns `CeramicRegrow`) while the real in-game DDT is `DdtCamo` (spawns `CeramicRegrowCamo`); and a `DiamondbackDiamondBloon` variant reads health 60 while the canonical `DiamondBloon` is 80. **Both times a naïve "first matching file" pick produced a wrong value the maintainer's domain knowledge caught.** So: trust the dump, but select the model by the bloon's own properties (`_select_bloon_model`) and sanity-check a surprising value against gameplay before asserting it. Net effect this session: the BAD→Camo-DDT correction stands (dump was right, wiki incomplete); the Diamond "60" was withdrawn (variant artifact — canonical is 80, already matching).

**Suggested destination after answer:** `docs/btd6/btd6-gamedata-decode-status.md` (provenance precedence note) + applied by the `--bloons` cutover's model-selection logic.

### Q-0038 — What is the identity and tenancy boundary for player guilds/clans?

**Area:** Social / community / progression
**Type:** Product + architecture boundary
**Priority:** High (blocks guild, guild-bank, guild-battle, guild-profile, and guild-leaderboard planning)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → social roadmap decision note; draft answer below approved as written
**Question:** Is a player guild/clan scoped independently inside each Discord server, or may one player guild span multiple Discord servers? If cross-server identity is wanted, what consent, discoverability, moderation, ownership-transfer, retention, deletion/export, and main-server behavior should apply?

**Why agents need this:** The answer determines the canonical keys and owner for membership, treasury, battles, profiles, and leaderboards. Guessing would create either a duplicate per-server system or an unapproved cross-server identity system.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** Treat the social roadmap as planning-only. Do not create a guild/clan schema or expose cross-server profiles. Preserve existing Discord-guild scoping.

**Suggested destination after answer:** `docs/planning/social-community-progression-roadmap-2026-06-08.md` and a dedicated ownership/ADR decision if a new social domain is approved.

**Draft answer — awaiting maintainer markup** *(Lane 6, 2026-06-09, per Q-0051 — proposed for approve / adjust / reject per item; nothing below is decided until marked up)*

**Proposed answer:** **Server-scoped clans.** A player clan lives entirely inside one
Discord server; nothing about it crosses servers. Per sub-question:

- **Tenancy / canonical keys:** every clan row is keyed `(guild_id, clan_id)`; membership
  is `(guild_id, clan_id, user_id)`. One clan per player per server (switching allowed,
  with a cooldown so treasuries/leaderboards can't be hopped). The same player may be in
  different clans on different servers — those are unrelated facts.
- **Cross-server identity:** none in v1 — no cross-server membership, treasury, battles,
  profiles, or leaderboards. A later "cross-server clan showcase" would be a separate,
  consent-first decision after the server-scoped model is stable; it is not part of this
  answer.
- **Consent / discoverability:** no consent machinery needed (nothing leaves the server);
  clans are discoverable in-server via a clan list / clan leaderboard panel.
- **Moderation:** server staff fully own what happens in their server — clan names and
  descriptions are moderatable content; staff can rename/disband through the same audited
  service path the clan owner uses.
- **Ownership transfer:** explicit owner action (or staff override), audited.
- **Retention / deletion / export:** clan data follows the existing guild-lifecycle rules —
  when the bot leaves a server or its data is cleaned, its clans go with it. Disband
  liquidates the treasury back through `economy_service` (audited) so coins are never
  orphaned. No export surface in v1.
- **Main-server behavior:** nothing special — the main server is just another tenant.
- **Naming:** code/schema say **"clan"** (`player_clans`, `clan_id`) to avoid colliding
  with discord.py's `Guild` (= Discord server) throughout the codebase; user-facing copy
  may still say "guild" if preferred — that choice is cosmetic and reversible.

**Why this fits current SuperBot direction:** the owner's own architecture note says new
features must keep scoping data per-server (`docs/ideas/owner-vision-ideas-2026-06-08.md`
§9); every existing table follows guild-scoped tenancy; ADR-001 keeps the bot
single-process with no shared external state, which cross-server identity would strain;
and the future-product capture explicitly bars cross-server profiles before dedicated
privacy/consent/retention decisions. Server-scoped clans need none of that machinery and
unblock everything the owner actually selected (§4a shared bank + officer spending,
battles, upgrades/levels; §14 guild leaderboard).
**Safe default until approved:** unchanged — the safe default above stands (planning-only;
no schema, no cross-server exposure).
**Implementation implication if approved later:** the social roadmap's phase 1 becomes
specifiable: schema/ownership with `(guild_id, clan_id)` keys, a new social domain owner
declared in `docs/ownership.md` (+ likely an ADR), treasury mutations through
`economy_service`, and officer authority as a small capability surface.
**Rejected / avoided direction:** cross-server clan identity in v1 — it imports consent,
moderation-jurisdiction, retention/export, and abuse problems the bot does not have
today, for no feature the owner selected (every §4a selection works server-scoped). Also
avoided: multi-clan membership per player per server (treasury/leaderboard exploit
surface).

**Maintainer answer (2026-06-09, structured choices — markup of the draft above):**
**"Leave as drafted"** — the draft answer is approved as written: server-scoped clans,
`(guild_id, clan_id)` keys, one clan per player per server, no cross-server identity in
v1, "clan" naming in code/schema. The offered alternatives (design-for-cross-server-later,
cross-server-from-start, multi-clan membership) were not chosen.
*Answer scope:* approves the **tenancy/identity posture** — the social roadmap's phase-1
decision input. It does not approve implementation, schema work, or a roadmap promotion;
the social lane still needs its new-owner/ownership decision + the normal promotion path.
**Routed to:** `docs/planning/social-community-progression-roadmap-2026-06-08.md`
(decision note) + `docs/roadmap.md` (gate line).

### Q-0039 — Which VIP/donation benefits are acceptable under the no-pay-to-win rule?

**Area:** Economy / rewards
**Type:** Product, monetization, and fairness boundary
**Priority:** High (blocks VIP planning)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → economy roadmap decision note; draft answer below approved as written
**Question:** Should VIP/donation tiers be limited to cosmetic identity and supporter recognition, or may they include convenience benefits? Which exact benefits are explicitly allowed or forbidden, and should donation status ever be stored or processed by SuperBot itself?

**Why agents need this:** “No pay-to-win” is binding owner intent, but convenience, lottery entries, marketplace privileges, and economy-adjacent perks can still create gameplay advantage or external billing/privacy obligations.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No paid/donation benefit affects XP, coins, drops, odds, cooldowns, market access/fees, guild power, or game outcomes. Do not add billing/provider integration.

**Suggested destination after answer:** `docs/planning/economy-marketplace-rewards-roadmap-2026-06-08.md` and, if external payment data is approved, the integrations/privacy decision set.

**Draft answer — awaiting maintainer markup** *(Lane 6, 2026-06-09, per Q-0051 — proposed for approve / adjust / reject per item; nothing below is decided until marked up)*

**Proposed answer:** **Donation benefits = cosmetic identity + supporter recognition only;
convenience perks live on the earned track only; SuperBot never stores or processes
payment data.**

- **Donation track (real money) — allowed:** supporter badge/title on the profile card,
  cosmetic name color / banner / flair variants, supporter-only *cosmetic* shop items,
  a thank-you/credits surface. All purely presentational.
- **Donation track — explicitly forbidden:** anything touching XP, coins, drops, odds,
  cooldowns, daily/streak claims, lottery entries, market access/fees, guild/clan power,
  or game outcomes — and also "soft convenience" with economic effect (cooldown skips,
  extra claims, fee discounts). Lottery entries are named deliberately: the lottery pays
  coins, so a purchasable entry is pay-to-win with extra steps.
- **Earned in-game VIP track (milestones, no money):** may carry convenience and
  progression perks — that is normal game progression, governed by game balance, not by
  this fairness rule. The two tracks stack visually (both badges can show), per the
  owner's "two separate tracks that can stack."
- **Donation status storage:** none. SuperBot runs no billing and stores no payment or
  donor data. Supporter status enters as a **Discord role** managed outside the bot
  (e.g. Patreon's own role sync, or manually granted by the owner); the bot *reads* that
  role live to render cosmetics. Role gone → cosmetics deactivate. No schema, no PII,
  no chargeback handling.
- **Enforcement:** add an invariant test asserting no supporter/VIP predicate appears in
  any odds / reward / cooldown / fee code path — the no-pay-to-win rule becomes
  CI-checkable instead of reviewer-remembered.

**Why this fits current SuperBot direction:** it is the owner's own §13 selection
(`docs/ideas/owner-vision-ideas-2026-06-08.md`: donation VIP = "cosmetic perks only, no
gameplay advantage"; earned + donation as two stacking tracks) made precise; the
not-selected markers already exclude XP multipliers and pay-to-win consumables (§2a/§2b);
and keeping billing out of SuperBot avoids the entire payment-privacy/provider obligation
the safe default warns about.
**Safe default until approved:** unchanged — the safe default above stands (no paid
benefit touches gameplay; no billing/provider integration).
**Implementation implication if approved later:** the economy roadmap's VIP phase becomes
specifiable: a `supporter_only` flag on the cosmetic catalog, rendering keyed off the
configured supporter role (existing role/binding patterns), the CI invariant above, and
zero payment schema.
**Rejected / avoided direction:** convenience benefits on the donation track (each is a
quiet economy advantage); SuperBot-native billing or donation processing (a privacy/legal
surface far above current posture); purchasable lottery entries or purchasable odds of
any kind.

**Maintainer answer (2026-06-09, structured choices — markup of the draft above):**
**"Leave as drafted"** — the draft answer is approved as written: donation = cosmetic
identity + supporter recognition only; convenience/progression perks only on the earned
milestone track; supporter status read live from an externally-managed Discord role;
SuperBot stores no payment/donor data; a CI invariant enforces the no-pay-to-win line.
The offered alternatives (mild donor convenience, earned-track-cosmetic-only tightening,
bot-owned supporter table) were not chosen.
*Answer scope:* approves the **fairness boundary**, not the VIP feature itself — the
economy roadmap's VIP phase still sits behind economy-health evidence + the normal
promotion path.
**Routed to:** `docs/planning/economy-marketplace-rewards-roadmap-2026-06-08.md`
(decision note) + `docs/roadmap.md` (gate line).

### Q-0040 — What operational posture should an AI dungeon master use?

**Area:** AI / games / social
**Type:** Product, cost, moderation, and retention boundary
**Priority:** High (blocks AI dungeon-master and player-prompted event planning)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → AI routing addendum + AI folio owner-voice block; draft below **adjusted**: bounded-menu selection, not pure narration
**Question:** For thread, persistent-channel, and DM modes, what should persist; who may start/join/control a session; what content/moderation limits apply; what cost/rate limits are acceptable; and may AI ever propose mechanics/rewards beyond narrative wrapping of deterministic game-owned outcomes?

**Why agents need this:** The answer governs state ownership, privacy, content safety, provider spend, and whether the feature remains explanation/narrative-only or requires a future action-authority decision.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No implementation. AI may not own rewards, difficulty, quests, or state mutations; all current AI expansion/action gates remain binding.

**Suggested destination after answer:** `docs/ai/ai-product-extension-routing-2026-06-08.md` and the authoritative `docs/planning/ai-roadmap-2026-06-07.md`.

**Draft answer — awaiting maintainer markup** *(Lane 6, 2026-06-09, per Q-0051 — proposed for approve / adjust / reject per item; nothing below is decided until marked up)*

**Proposed answer:** **AI is the narrator, never the game-owner — thread-first,
budget-capped, public-surface-first.**

- **Authority posture (the core rule):** AI writes story/flavor around outcomes that
  deterministic, audited game services own. Rewards, difficulty, odds, and state
  mutations always come from deterministic owners (reward tables, `economy_service`);
  AI never computes an amount or mutates state. Of the four selected event styles
  (owner-vision §3b), **narrative flavor text** and **player-prompted events** (the
  prompt seeds the *story* around a deterministically rolled event) fit this posture
  and come first; **dynamic difficulty scaling** and **fully AI-generated quests with
  AI-chosen rewards** require AI influence over mechanics, so they stay sequenced last,
  behind the dedicated action-authority decision (the Q-0001 / AR-09 path) — deferred,
  not rejected.
- **Mode order:** thread-per-session first (the owner's own suggested priority), then
  persistent-channel world, then DM mode. Threads are ADR-002-honest: a restart ends the
  session and refunds any stake — no restart-safe promise. DM mode comes last because it
  has the least moderation visibility.
- **What persists:** per-session bounded summary state only (the existing
  `game_state_service` versioned-JSONB pattern, if a session wants resume), cleared on
  completion; **never** raw transcripts or model reasoning. Persistent-channel mode
  persists a bounded world summary under the same rules.
- **Who may start/join/control:** per-guild opt-in feature, **off by default**; starting
  a session follows the guild's normal command-access policy; joining is open to
  thread/channel members up to a player cap; end/kick = session starter + server staff.
- **Content/moderation:** sessions run on public surfaces (threads/channels) first so
  server moderation sees everything; provider safety + the existing instruction stack +
  guild content settings apply; standard moderation tools work on the messages.
- **Cost/rate limits:** hard per-guild daily budget + per-session turn cap,
  operator-configurable with conservative defaults, riding the shipped orchestration
  budget machinery (Phase 2 `AIToolBudget` / Phase 3 profiles); budget exhausted → the
  feature degrades closed with a clear message, never silent overspend.

**Why this fits current SuperBot direction:** it keeps the owner's #1 regret-if-missing
feature (owner-vision §25) moving with a concrete, gate-respecting shape; it is exactly
the AI routing addendum's "narrative wraps deterministic domain outputs" rule; AR-09's
explanation-only posture stays intact (narration is presentation, not action); and the
budget seam is the orchestration foundation that just shipped (#612/#618/#619) doing the
job it was built for.
**Safe default until approved:** unchanged — the safe default above stands (no
implementation; AI owns no rewards, difficulty, quests, or state mutations; all AI
expansion/action gates remain binding).
**Implementation implication if approved later:** approving this is a *posture* approval,
not a build green-light — the feature still needs its own plan plus the per-exposure lift
(it writes, costs money, and adds UI, so the Q-0048 standing lift explicitly does **not**
cover it). Likely sequence: a deterministic games-side event/reward owner first, then a
`dungeon_master` orchestration profile/toolset, then the thread-mode pilot.
**Rejected / avoided direction:** AI-owned rewards/difficulty/quest mechanics in v1
(deferred behind the action-authority decision, per AR-09); raw transcript or reasoning
retention; DM-mode-first rollout; uncapped provider spend.

**Maintainer answer (2026-06-09, structured choices — markup of the draft above):**
**"AI picks from bounded menus"** — adjusts the draft's pure-narrator v1: the AI does
not just narrate; it **chooses** the quest template, reward tier, and difficulty from
**pre-approved menus with hard caps enforced by deterministic code**. Quests feel
genuinely AI-generated from day one; the worst case is always a capped, game-approved
outcome. Chosen over both "leave as drafted" and "full AI authority sooner", after the
narrator posture was clarified (the owner had flagged he partly disagreed and may have
partly misread it — the concern was pure narration under-delivering his §3b selection).
Everything else in the draft stands unchanged: thread-per-session first, per-guild
opt-in off by default, hard budgets on the orchestration seams, bounded summary
persistence only, public-surfaces-first, DM mode last.
*Answer scope:* sets the **authority posture** (bounded-menu selection, not free-form
invention). Still not a build green-light: the feature needs its own plan, the
per-exposure lift (it writes, costs money, and adds UI — Q-0048's standing lift does not
cover it), and one **small bounded-authority decision** formalizing AI-selects-from-menus
before anything ships (lighter than the full Q-0001/AR-09 action gate because every cap
stays deterministic). Fully AI-*invented* rewards/difficulty (no menu) remain behind the
dedicated action-authority decision.
**Routed to:** `docs/ai/ai-product-extension-routing-2026-06-08.md` (posture note),
`docs/subsystems/ai.md` (Q-0062 owner-voice seed), `docs/roadmap.md` (gate line).

### Q-0041 — What privacy and provider posture should integrations and voice use?

**Area:** Integrations / media / voice
**Type:** Privacy, credentials, moderation, retention, and degraded-provider policy
**Priority:** High (blocks Twitch, YouTube alerts, Spotify/Last.fm, Steam, music, SFX, and speech commands)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → integrations roadmap decision note; draft answer below approved as written
**Question:** Which provider integrations should be considered first, who supplies/owns credentials, what user/server consent is required, what data/content may be cached and for how long, what moderation rules apply, and how should alerts/voice features behave when providers fail or rate-limit the bot?

**Why agents need this:** These ideas share secrets, personal activity, third-party terms, moderation, retention/deletion, rate-limit, and outage behavior. Implementing one ad hoc would create a parallel provider or delivery path.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No new provider or voice implementation; retain only the existing ADR-007-owned media seams and require opt-in, bounded retention, and safe degraded behavior in future plans.

**Suggested destination after answer:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md` and the media folio/ADR if the shared platform boundary changes.

**Draft answer — awaiting maintainer markup** *(Lane 6, 2026-06-09, per Q-0051 — proposed for approve / adjust / reject per item; nothing below is decided until marked up)*

**Proposed answer:** **YouTube-alerts pilot first on operator-owned keys with dual opt-in,
metadata-only bounded caches, and fail-quiet degradation; voice sequenced behind its own
architecture decision, speech recognition last.**

- **Provider order:** (1) **YouTube upload alerts** — reuses the ADR-007 media seams the
  bot already owns (fetch/context/cache services), so it is the cheapest proof of the
  shared provider contract; (2) **Twitch live alerts** — a second adapter on the *same*
  alert-delivery contract, proving reuse; (3) **Spotify/Last.fm and Steam** — only after
  the alert pattern is proven, because both need per-user account linking (a much bigger
  consent surface; pairs with the deferred account-links direction in Q-0033).
- **Credentials:** operator-owned, platform-level API keys via environment config (the
  existing env-gated pattern — AI provider and YouTube keys already work this way). Users
  never supply bot-level secrets. Per-user account links (Spotify/Steam) would be explicit
  user-initiated OAuth connects, revocable any time — and need their own consent decision
  before those providers ship.
- **Consent:** dual opt-in — the **operator** enables the integration and binds the
  destination channel (existing bindings pattern), and the **individual user** opts in
  before the bot announces anything about *them* (going live, listening status). No
  member-activity tracking by default.
- **Cache/retention:** metadata only (IDs, titles, timestamps, thumbnails) in bounded-TTL
  caches with provenance/freshness labels (the existing video-cache pattern). No media
  content, no transcripts, no accumulated listening/watch history.
- **Moderation:** alerts post only to operator-bound channels; any operator-customizable
  alert text passes the same content rules as other settings.
- **Degraded providers:** provider down / rate-limited → skip the cycle quietly and
  surface it in health/readiness (the degraded-not-broken posture current-state already
  uses for env-gated features). Never queue-and-burst missed alerts on recovery.
- **Voice (music / SFX / speech):** wanted (the owner explicitly rejected "no voice") but
  **sequenced behind a dedicated architecture review** after the first two alert
  integrations prove the provider contract — playback infrastructure is the bot's biggest
  operational-cost step. **Speech recognition comes last, if ever, with its own
  consent/retention decision** — continuous audio capture is the most privacy-sensitive
  item in the whole vision and must not ride in on a music-playback approval.

**Why this fits current SuperBot direction:** ADR-007 already makes media a shared
platform subsystem — YouTube-first is reuse, not new surface; dual opt-in and
metadata-only retention match the consent/bounded-cache posture every related capture
demands; fail-quiet matches the accepted degraded-in-sandbox behavior; and one shared
provider contract prevents the per-provider parallel pipelines the integrations roadmap
warns against.
**Safe default until approved:** unchanged — the safe default above stands (no new
provider or voice implementation; ADR-007-owned media seams only).
**Implementation implication if approved later:** integrations roadmap phases 2–3 become
specifiable (shared provider contract + the YouTube pilot); every provider registers
under media subsystem ownership (ADR-007), never as a per-feature pipeline; AI/tool
exposure of provider data stays separately gated (the Q-0048 standing lift covers
neither external calls nor new UI).
**Rejected / avoided direction:** user-supplied bot-level credentials; default-on
tracking of member activity; storing listening/watch history or transcripts;
speech-recognition-first voice; one-off per-provider delivery pipelines.

**Maintainer answer (2026-06-09, structured choices — markup of the draft above):**
**"Leave as drafted"** — the draft answer is approved as written: YouTube-alerts pilot
first on the ADR-007 seams, then Twitch on the same contract, Spotify/Steam only after
an account-link consent decision; operator-owned platform keys; dual opt-in (operator
enables + the announced user consents); metadata-only bounded caches; fail-quiet
degradation; voice behind its own architecture review; speech recognition last, if
ever, with its own consent/retention decision. The offered alternatives (Twitch-first,
earlier voice review, dropping speech outright) were not chosen — speech stays
deferred-not-dropped.
*Answer scope:* approves the **privacy/provider posture and ordering**, not any
integration's implementation — integrations roadmap phases 2–3 still need the normal
promotion path, and external calls / new UI remain per-exposure gated.
**Routed to:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md`
(decision note) + `docs/roadmap.md` (gate line).

### Q-0042 — Should a full web dashboard become a future product surface?

**Area:** Website / cross-cutting UI
**Type:** Product investment + architecture boundary
**Priority:** Medium (future-only; blocks website planning)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → integrations roadmap decision note; draft answer below approved as written
**Question:** Is the intended website a read-only companion, a full management surface, or not a priority? If management is wanted, what authentication/authorization model, hosting/operations budget, privacy posture, and limit on website-specific behavior should apply?

**Why agents need this:** A website can easily become a second control plane, duplicate Discord-native panels, or bypass domain mutation/audit/permission paths.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** Keep the website at Someday. Mature Discord-native panels and canonical read/mutation services first; do not create website-specific authority or mutations.

**Suggested destination after answer:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md` and a dedicated architecture decision if promoted.

**Draft answer — awaiting maintainer markup** *(Lane 6, 2026-06-09, per Q-0051 — proposed for approve / adjust / reject per item; nothing below is decided until marked up)*

**Proposed answer:** **Yes as a destination, in two stages — read-only companion first,
management second, never a second control plane — and it stays at Someday until the
Discord-native foundations mature.**

- **Stage A — read-only companion (the first web work, when promoted):** public-safe
  profiles, leaderboards, and server feature status rendered from the read models the
  bot already exposes (the AR-08 audience tiers apply on the web exactly as in Discord).
  Login = **Discord OAuth2 only** — identity stays Discord-native; no separate account
  system.
- **Stage B — management surface (a separate later decision):** every write calls the
  same audited domain mutation services with the same capability resolution, evaluated
  server-side per request. The web layer owns **no** authority, no web-only mutations,
  no web-only tables. If a panel exists in Discord and on the web, both call the same
  service.
- **Hosting/architecture posture (decided at promotion; the boundary now):** the bot
  process does **not** serve the website. A web app is a separate process — which makes
  Stage B exactly ADR-001's re-evaluation trigger 3 (a cross-process state requirement),
  so promotion requires the dedicated ADR by design, not as an afterthought. Hosting and
  ops budget are decided in that ADR.
- **Privacy:** the web surface renders only what the viewer's audience tier already
  permits in Discord; public pages are opt-in per server (an operator setting), never
  default-published.
- **Timing / gate:** stays **Someday** until (a) the Discord-native panel lanes
  (settings/help/hub) mature, (b) the tiered read models cover what the site would show,
  and (c) a dedicated security architecture review is approved. No web work starts now.

**Why this fits current SuperBot direction:** it is Q-0002's answered posture
("Discord-first, web companion possible later; keep services/read-models reusable")
extended to the owner's full-dashboard end-state (owner-vision §21) — the full dashboard
is honored as the destination while the staging prevents the second-control-plane
failure mode the integrations roadmap and the future-product capture both warn about.
The tiered introspection/projection read models shipping now (e.g. #616) are already the
Stage-A foundation, so current work builds toward the site with zero web-specific effort.
**Safe default until approved:** unchanged — the safe default above stands (website at
Someday; mature Discord-native panels and canonical services first; no website-specific
authority or mutations).
**Implementation implication if approved later:** approving this answer sets *shape*,
not schedule — promotion still needs the dedicated web-architecture ADR (auth/session/
CSRF, hosting, ops budget) plus the integrations roadmap's phase 6; until then the only
"web work" is keeping read models reusable, which is already the rule.
**Rejected / avoided direction:** website-specific mutation authority, tables, or a
separate account system; serving the web UI from the bot process; starting web work
before panel/read-model maturity; default-public web exposure of guild data.

**Maintainer answer (2026-06-09, structured choices — markup of the draft above):**
**"Leave as drafted"** — the draft answer is approved as written: yes as a destination,
staged (read-only companion via Discord OAuth2 first; management later through the same
audited services; no web-only authority/tables; the bot process never serves the site;
Stage B = an ADR-001 revisit by design); timing stays **Someday** until Discord-native
panels, tiered read models, and a security architecture review mature. The offered
alternatives (pull Stage A to Later, one full-dashboard project, drop the website) were
not chosen.
*Answer scope:* approves the **shape and staging** — explicitly not a schedule change;
the website remains Someday and no web work starts now.
**Routed to:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md`
(decision note) + `docs/roadmap.md` (gate line).

### Q-0043 — How is BTD6 "cash from round A to B" defined: inclusive sum or wallet-delta?

**Area:** BTD6 / AI answerability
**Type:** Product semantics (changes the user-facing number)
**Priority:** Medium (blocked the round-cash answerability slice; now resolved)
**Status:** Answered (2026-06-09) — **Routed** → instruction stack + `btd6_round_cash` tool + `docs/btd6/btd6-smoke-test-checklist.md` (shipped this session)

**Question:** For "how much cash do you earn from round A to B?", does the range count both
endpoints (inclusive sum of rounds A..B) or only the wallet gain between checkpoints
(exclusive `cumulative(B) − cumulative(A)`)? The two readings give different numbers for the
same question (r50→r60 = $19,840 inclusive vs $16,824 exclusive), and the bot's *prior*
instruction stack + smoke-test checklist used the exclusive reading while the answerability
roadmap recommended inclusive — a direct conflict surfaced while building Phase 1B.

**Why agents need this:** It defines the deterministic `range_cash` the `btd6_round_cash`
tool returns and what the model is grounded on; getting it wrong makes the bot contradict
its own smoke checklist on the headline answerability question.

**Maintainer answer (verbatim selection):** "Inclusive sum (roadmap)."

**Decision:** Range cash is **INCLUSIVE of both endpoints** — `range_cash(A,B)` = sum of each
round's cash for A..B = `cumulative(B) − cumulative(A−1)`. r50→r60 = **$19,840**. The
deterministic `btd6_data_service.round_cash` owner already implements this; the instruction
stack and smoke-test checklist were updated to match (they previously taught the exclusive
`cumulative(B) − cumulative(A)`).

**Routed to:** `disbot/services/ai_instruction_service.py` (range-cash guidance),
`disbot/services/ai_tools.py` (`btd6_round_cash` tool description), and
`docs/btd6/btd6-smoke-test-checklist.md` (expected values). Plan:
`docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md` §1A/§5.7/§9.

## 21. Repo review batch — 2026-06-09

### Q-0044 — Community Spotlight: integration depth + the greedy `!hub` / `!server` aliases

**Area:** Community / Help surface / subsystem platform
**Type:** Product intent + platform integration scope
**Priority:** Medium (the feature works; it is outside the Help/hub/settings platform)
**Status:** Answered (2026-06-09) — **Routed** → Q-0025 scaffold task + help-surface-map §3 banner + the cog (aliases dropped same day)

**Question:** The Community Spotlight cog (merged side-lane via #613/#614, then hotfixed by
#615/#617) ships `!spotlight` with aliases `!hub`, `!activity`, and `!server`, its own
in-cog views, and a direct `xp`-table read — but is **not** registered in
`utils/subsystem_registry.py` / `utils/hub_registry.py`, so it is invisible to typed Help,
the Help dropdown, governance visibility, and the settings platform. Three sub-questions:
(a) Should it become a *registered subsystem* (the ~8-touch-point Q-0025 scaffold task),
a child surface of the existing `community` hub, or stay a deliberately lightweight
standalone command? (b) Keep or drop the `!hub` and `!server` aliases? They are greedy
grabs on platform vocabulary — "hub" is the mother-hub concept and a likely future
top-level entry, and "server" collides with server-management mindshare. (c) Should its
panel adopt the hub-navigation standard (back-to-Help routing)?

**Why agents need this:** Every future Help/hub/governance feature iterates the
registries; an unregistered user-facing surface silently drifts out of every inventory,
audit, and doc-test. And alias choices are user-facing product identity an agent should
not change unilaterally.

**Safe default until answered:** Feature stays as shipped (works, has tests since
2026-06-09, reads via the canonical `utils/db/xp.py` owner). The gap is bannered in
`docs/help-command-surface-map.md` §3 and the navigation map. No registration, no alias
change.

**Maintainer answer (2026-06-09, gate-lifting interview):** (a) **Register via the scaffold** — build the Q-0025 `new_subsystem.py` scaffold first, then use it to register Community Spotlight as a child of the existing `community` hub (Help-visible, governed; the scaffold gets battle-tested on a real consumer). (b) **Drop `!hub` and `!server`, keep `!spotlight` + `!activity`** — frees platform vocabulary ("hub" is the mother-hub concept; "server" collides with server-management). *Implemented same session:* the alias drop (one-line cog change). The registration ships with the scaffold lane. (c) Panel adopts hub-navigation standard as part of registration.

**Suggested destination after answer:** `docs/help-command-surface-map.md` (§2 row +
remove the §3 banner), `utils/subsystem_registry.py` (+ the Q-0025 scaffold if chosen),
and the games/community folio that takes ownership.

### Q-0045 — Audience simulation for Help Preview / `help_advertises_locked` (P1B/P1C gate)

**Area:** Adaptive Setup/Access platform (governance axis)
**Type:** Architecture decision (formalizes plan §16.8 item 3)
**Priority:** High (blocks P1B's `help_advertises_locked` provider and the P1C Help Preview panel)
**Status:** Answered (2026-06-09) — **Routed** → adaptive plan §16.8 item 3 (option (b): governance tier-input path)

**Question:** The governance axis (`governance.get_visible_subsystems(GovernanceContext)`)
needs a real `discord.Member`; Help Preview (Q-0023) and the drift "baseline audience"
want to simulate an audience by **tier/role set** instead. Pick one: **(a)** synthesize a
member-like object from the simulated tier/roles and pass it through the existing axis
(keeps the change inside the projection layer), or **(b)** add a tier-input read path to
governance so the axis prefers `AccessContext.member_tier` when set (cleaner, but touches
governance). Either way the simulation must label its limits (it cannot model live
channel-permission overrides it wasn't given — plan §16.4).

**Why agents need this:** Two queued deliverables (P1B `help_advertises_locked`, P1C Help
Preview) both build on whichever path is chosen; building one ad hoc would lock the other
in. This was an "implicit" open decision buried in plan §16.8 — promoted here so it has a
canonical, answerable home.

**Safe default until answered:** Ship P1B/P1C surfaces that don't need audience
simulation (`routing_access_conflict` is already member-independent and shipped in #592);
defer `help_advertises_locked` + Help Preview.

**Maintainer answer (2026-06-09, gate-lifting interview):** **Option (b) — teach governance tiers**: add the read-only tier-input path so the governance axis prefers `AccessContext.member_tier` when set (the forward hook exists for exactly this). Durable, one source of truth; the simulation must still label its limits (it cannot model live channel-permission overrides it wasn't given — plan §16.4). This unblocks both P1B `help_advertises_locked` and the P1C Help Preview.

**Suggested destination after answer:** plan §16.8 item 3 + §16.4 (simulation limits),
`services/access_projection.py` (`AccessContext.member_tier` consumption), and — if (b) —
`docs/capability-authority.md` / the governance folio.

## 22. Gate-lifting interview batch — answered 2026-06-09

> All six asked and answered in the 2026-06-09 gate-lifting interview (same session as the
> repo review / PR #621). Recorded as already-answered entries so each decision has a
> citable Q-number; verbatim selections preserved.

### Q-0046 — Orchestration Phase 4: what is the MVP slice?

**Area:** AI / tool orchestration
**Type:** Scope definition (plan §7 described ideals without an MVP)
**Priority:** High (next step of an active lane)
**Status:** Answered (2026-06-09) — **Routed** → `docs/ai/ai-complex-request-tool-orchestration-plan.md` (Phase 4 MVP note)

**Maintainer answer (2026-06-09, gate-lifting interview):** **One vertical slice** — build the
plan→execute→verify workflow for ONE question family (round-cash style: "how much cash from
round A to B and can I afford X?") with **one** typed answer-with-evidence contract. Proves the
whole pattern end-to-end; the remaining contracts follow the proven template. Full §7 scope and
the §12.1 durable audit trace stay deferred behind it.

### Q-0047 — Answerability Phase 3: committed tool list + gate lift

**Area:** AI / answerability
**Type:** Exposure gate lift + scope commit
**Priority:** High (next step of an active lane)
**Status:** Answered (2026-06-09) — **Routed** → `docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md` Phase 3

**Maintainer answer (2026-06-09, gate-lifting interview):** **All three tools in one slice,
gate lifted for them** — tools-available ("what can you do here?"), policy-explanation ("why
didn't you reply?"), and answerability-summary ("what do you know?"), all read-only over the
shipped #616 read model with audience-tier filtering enforced at construction.

### Q-0048 — AI exposure gate posture: standing lift for read-only deterministic tools

**Area:** AI / expansion gate (cross-cutting)
**Type:** Standing policy change (supersedes per-exposure lifts for one risk class)
**Priority:** High (changes every future AI session's ask-vs-act line)
**Status:** Answered (2026-06-09) — **Routed** → `docs/current-state.md` Gates + `docs/roadmap.md` AI section + the AI folio

**Maintainer answer (2026-06-09, gate-lifting interview):** **Auto-allow read-only tools** —
a standing lift for AI tools that are **read-only AND deterministic** (no writes, no external
calls, audience-tiered): they may ship without a per-case ask. Anything that **writes, costs
money, calls external services, or adds UI** still requires the per-exposure lift. (Decided
after two per-case lifts — `btd6_round_cash` #612, `ai:tools` UI #619 — established the
pattern.)

### Q-0049 — BTD6 data-refresh automation: commit as manual-dispatch workflow

**Area:** BTD6 data / CI
**Type:** Sign-off (was "Next (needs sign-off)" in the roadmap)
**Priority:** Medium
**Status:** Answered (2026-06-09) — **Routed** → `docs/btd6/btd6-data-refresh-pipeline-plan.md` + roadmap BTD6 section

**Maintainer answer (2026-06-09, gate-lifting interview):** **Manual-trigger workflow** —
commit the GitHub Actions refresh workflow as `workflow_dispatch`-only (one click on GitHub,
no schedule). One-click refresh after a game update with zero unattended-fetch risk. Building
the workflow is queued lane work, not done in the interview session.

### Q-0050 — Mining descent lights: permanent (owner confirm of §6.8 P2)

**Area:** Games / mining
**Type:** Shipped-behaviour confirm (was "flagged for owner confirm" in #607)
**Priority:** Low
**Status:** Answered (2026-06-09) — **Routed** → `docs/ideas/mining_exploration_brainstorm.md` §6.8

**Maintainer answer (2026-06-09, gate-lifting interview):** **Keep lights permanent** — torch/
lantern are craft-once gear; depth is a progression unlock, not an upkeep cost. The Workshop
durability slice (§7.5) carries the recurring-sink role instead: one sink, clearly owned.

### Q-0051 — Handling the five open product-vision questions (Q-0038–Q-0042)

**Area:** Workflow / product vision
**Type:** Meta-decision (how to answer, not the answers)
**Priority:** Medium
**Status:** Answered (2026-06-09) — **Routed** → handling notes on Q-0038–Q-0042; draft-answer session queued

**Maintainer answer (2026-06-09, gate-lifting interview):** **Claude drafts answers** — a
dedicated session drafts a concrete proposed answer per question (clans identity, VIP
fairness, AI dungeon master, integrations/voice privacy, web dashboard), grounded in existing
decisions + safe defaults, for the maintainer to mark up (approve / adjust / reject per item).
Nothing implements until approved; safe defaults hold meanwhile.

## 23. Session-workflow follow-up — answered 2026-06-09

### Q-0052 — Open the session PR as a draft at first push (restore the old habit)

**Area:** Workflow / session protocol
**Type:** Workflow change (binding-doc edit, maintainer-approved in chat)
**Priority:** Medium (kills the only recurring docs-drift class found in the 2026-06-09 review)
**Status:** Answered (2026-06-09) — **Routed** → `.claude/CLAUDE.md` § Session & plan workflow + `.session-journal.md` (Quick reference + Protocol END step 1) + the multi-lane execution plan §2

**Question:** Session PR numbers don't exist when end-of-session docs are written, so
sessions left "(this session) — reconcile PR # next session" placeholders in
`current-state.md` that piled up across five sessions (the drift the 2026-06-09 review
cleaned). Should sessions open their PR as a **draft right after the first push**, so the
real number is available for every doc touched, marking it ready at session end?

**Maintainer answer (verbatim, 2026-06-09):** "about the PR at the start of a session, I
think that's a perfect idea and that's how it used to be previously, but somewhere along
the way that stopped, so please change that for me"

**Decision:** Restored as binding workflow: **open the session PR as a draft immediately
after the first push; reference its real # in all docs; mark it ready at session end.**
Per-lane drafts in multi-lane sessions follow the same rule. The companion
`check_docs.py` gate extension (fail on "(this session)" markers) remains a separate
**proposal** — executable config, not yet approved.

**Routed to:** `.claude/CLAUDE.md` (SESSION_WORKFLOW block — edited with this explicit
approval per the Q-0035 propose-first rule), `.session-journal.md`, and
`docs/planning/multi-lane-execution-plan-2026-06-09.md`.

## 24. Fun & ease brainstorm batch — answered 2026-06-09

### Q-0053 — Fun/ease brainstorm: owner cluster picks + session scope

**Area:** Product direction / games / UX
**Type:** Owner preference (answered in-session via structured choices)
**Priority:** Medium (steers idea-backlog grooming order)
**Status:** Answered (2026-06-09) — **Routed** → `docs/ideas/fun-and-ease-brainstorm-2026-06-09.md` §2 (capture) + `docs/planning/pets-companions-plan-2026-06-09.md` (structure) + `docs/roadmap.md` (games Later row + Someday line)

**Question:** The 2026-06-09 brainstorm produced 24 dedup-verified new fun/ease ideas.
Which clusters should lead the routing, and what should the session ship beyond the
capture doc?

**Maintainer answer (2026-06-09, structured choices):**
- Fun cluster pick: **Pets & companions** (over server goals/mascot, social memory,
  competition layer).
- Ease picks: **context-menu actions** and **persistent reminders**.
- Session scope: **capture + structure the top cluster into a plan** (no feature code
  that session).

**Decision:** Pets & companions structured into a games-lane plan at **Later** (gated
behind the Wave-1 keystone slices + balance review + owner promotion). Context-menu
actions and persistent reminders are marked **top quick-win candidates** in the capture
doc's routing table — strong next-session picks; both stay `captured`, not approved.
The other 21 ideas are captured with states/destinations (no orphans). Predictions
(A6) explicitly rides the existing economy chance-reward review gate.

**Routed to:** the three docs above; grooming sessions pull ⭐ rows first.

### Q-0054 — Mining durability tuning + the Q-0050 "craft-once" interplay

**Area:** Games — mining character platform (Wave 1)
**Type:** Balance confirmation (agent call already shipped in PR #624, fully reversible data)
**Priority:** Low-medium (live and self-consistent; one semantic overlap with Q-0050 to settle)
**Status:** Answered (2026-06-09) — **Routed** → brainstorm §6.8 P5 (owner-confirmed) + §7.5 (queued duels-wear) + roadmap games row

**Maintainer answer (2026-06-09, structured choices):** **(1) Lights keep wear** as
shipped — Q-0050's "craft-once" referred to the *descent* mechanic (no consume-per-
descend), not to durability; one sink covers all gear. **(2) Numbers stay as shipped**
(pickaxe 60 / iron 150 / torch 40 / lantern 100 / charm 80; `REPAIR_RATE` 0.5).
**(3) Duels SHOULD tick weapon/armor wear — queued as its own later slice** (combat
gear joins the craft→break→repair loop; maxes already defined).

**Question:** The Workshop + durability slice (PR #624) shipped with agent-chosen numbers,
picked generous-side per the §6.8 P5 caution ("a resource sink, not an annoyance").
Confirm or retune: **(1) maxes** — pickaxe 60 uses, iron pickaxe 150, torch 40, lantern
100, lucky charm 80 (combat gear has maxes — sword 60 / iron sword 150 / shield 90 /
armor 120 — but **no wear path yet**: duels don't tick durability); **(2) wear plan** —
mining wears tool always + light underground; exploring wears light underground + charm;
harvest/descent wear nothing (descent stays persistent-gated per Q-0050); **(3) repair
price** — `REPAIR_RATE` 0.5 × gear-shop price, scaled by missing durability, so the shop
catalogue is the single tuning knob; **(4)** should **duels** eventually tick weapon/armor
wear, and should the **lucky charm** (buy-only treasure, 80 🪙) wear at all?

**The Q-0050 interplay (the real question):** Q-0050's answer says lights are
"**craft-once gear**; depth is a progression unlock, not an upkeep cost" — answered about
the *descent* mechanic (no consume-per-descend; PR #624 honours that: descent is free).
But the shipped durability slice has lights **wear per underground action** (torch 40
uses, lantern 100) as part of "the Workshop durability slice carries the recurring-sink
role". If "craft-once" was meant broadly (lights never break), the fix is one-line data:
remove torch/lantern from `MAX_DURABILITY` so only tools + charms wear.

**Routed to:** brainstorm §6.8 P5 (P5 entry now owner-confirmed) + §7.5 (duels-wear
queued), `docs/roadmap.md` games section (queued slice).

## 25. Help customization decisions — 2026-06-09

### Q-0055 — Is hiding a command from Help display-only or execution-blocking?

**Area:** Help / governance / command access
**Type:** Product + architecture boundary
**Priority:** High (blocks Help-overlay mutation semantics)
**Status:** Answered (structured choices, 2026-06-09) — **EXECUTED 2026-06-10 in PR #659** (HLP-3): the overlay can only set `display_hidden`; an import fence pins that no admission path (`command_access` / `command_routing` / `governance`) consults it — `tests/unit/services/test_help_overlay.py`

**Maintainer answer (2026-06-09, structured choices):** **Display-only** — hiding changes
presentation only; execution stays governed by command access / routing / governance /
capabilities. Operator views label "hidden from Help but still executable".
*Answer scope:* decides hide **semantics** only — Q-0056–Q-0059 (names / order / debug
display / home-message format) stay open with their safe defaults, and this does **not**
green-light overlay storage/editor work (that whole lane still waits on the rest of the
batch).

**Question:** When an operator hides a command from a guild's Help panels, should that action
only remove the command from discovery, or should the same control also block execution?

**Why agents need this:** Help classification is currently informational/display-only, while
command access, routing, and governance own execution. Combining them in one mutation would
change security/policy ownership and could make hidden commands unexpectedly unusable.

**Safe default until answered:** Help hiding is display-only. Execution changes require a
separate explicit command-access/routing/governance action and confirmation.

**Suggested destination after answer:**
`docs/planning/help-cog-customization-audit-2026-06-09.md` §6/§9 and the future Help overlay mutation contract.

### Q-0056 — Where should custom cog/subsystem names appear?

**Area:** Help / settings / shared panels
**Type:** Product presentation scope
**Priority:** High (blocks overlay/read-model scope)
**Status:** Answered (structured choices, 2026-06-09) — **EXECUTED 2026-06-10 in PR #659** (HLP-3): overlay renames flow as `HubPresentation`/`SubsystemPresentation` consumed by Help surfaces exclusively; settings/setup/audit/diagnostics keep stable names

**Maintainer answer (2026-06-09, structured choices):** **Help-only** (the
recommendation as written) — custom names render in Help surfaces only; stable/default
names continue everywhere else (settings, setup, logs, audit, diagnostics).
*Answer scope:* presentation scope only — does not decide storage shape or schedule the
overlay work.

**Question:** Should a guild's custom cog/category/subsystem display name affect only Help, or
should every bot panel (Settings, setup, Access Explorer, mother hubs, diagnostics) use it?

**Why agents need this:** Help-only naming is a bounded presentation overlay. Global naming
requires every shared catalogue/panel to consume the overlay and creates a larger migration,
cache, and test surface.

**Safe default until answered:** Custom names affect Help surfaces only; stable/default names
continue everywhere else.

**Suggested destination after answer:** Future Help Catalogue/Projection contract and Settings/setup editor plan.

### Q-0057 — Is command ordering global or panel-local?

**Area:** Help / command panels
**Type:** Product customization model
**Priority:** High (blocks structured overlay schema)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → future command/panel catalogue + Phase 4 overlay schema (help audit)

**Maintainer answer (2026-06-09, structured choices):** **Panel-local** (the
recommendation as written) — each panel/page carries its own optional order; no
cross-surface coupling.
*Answer scope:* the ordering **model** only — the safe-default rider still binds: no
ordering UI ships until stable panel/action identities exist.

**Question:** Should a guild define one global command order reused everywhere, or customize
order independently within each Help/hub/command panel?

**Why agents need this:** Commands and actions can appear in multiple hubs, and dedicated panels
contain non-command actions. A global ordering key is simpler but cannot express panel-specific
composition; panel-local ordering requires stable panel/action identities and more storage.

**Safe default until answered:** Ordering is panel-local, and no ordering UI ships until stable
panel/action identities exist.

**Suggested destination after answer:** Future command/panel catalogue and Phase 4 overlay schema.

### Q-0058 — Should admin/debug views preserve default names beside custom names?

**Area:** Help / diagnostics / operator UX
**Type:** Product safety and explainability
**Priority:** Medium
**Status:** Answered (structured choices, 2026-06-09) — **EXECUTED 2026-06-10 in PR #659** (HLP-3): every presentation carries `default_display_name`/`default_*` + the stable key alongside the custom label, so admin/debug surfaces can render custom + default + key

**Maintainer answer (2026-06-09, structured choices):** **Custom + default** (the
recommendation as written) — public Help shows the custom label; admin/debug/audit
views show custom label + canonical default + stable key.
*Answer scope:* display rule only — no toggle/knob for it (the "toggle per guild"
option was not chosen).

**Question:** When a guild renames a cog/category/subsystem, should admin/debug/audit views show
the canonical default name and stable key beside the custom label?

**Why agents need this:** Operators and support need an unambiguous identity for diagnostics,
audit logs, stale-override repair, and documentation even when public labels differ by guild.

**Safe default until answered:** Public Help shows the custom label; admin/debug/audit views show
custom label + canonical default label + stable key.

**Suggested destination after answer:** Help overlay diagnostics, audit rendering, and reset UX.

### Q-0059 — What formats may a guild-specific Help Home message use?

**Area:** Help / settings / content safety
**Type:** Product format decision
**Priority:** High (blocks storage/editor choice)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → structured Help-overlay schema + preview/editor tests (help audit)

**Maintainer answer (2026-06-09, structured choices):** **Embed builder** — structured
title/description/color fields rendered as an embed. **Deviates from the plain-text
recommendation** (owner chose the richest option), which settles the storage question
the audit raised: the Help Home message needs the **structured overlay model**, not a
scalar setting.
*Answer scope:* format only. The safety floors stay mandatory regardless of format:
bounded field lengths, Discord embed limits enforced, mentions suppressed, validation +
preview before save, reset-to-default. **Variables/templating were not chosen** and
remain out unless asked separately. Until the overlay ships, the current default Help
Home stands — this schedules nothing.

**Question:** Should guild-specific Help Home copy support plain text only, structured rich
embeds, or a constrained template with variables? If variables are allowed, which values are
safe and useful?

**Why agents need this:** Plain text fits the existing scalar settings path. Rich embeds or
templates require structured validation, preview, Discord-limit enforcement, mention safety,
and likely a dedicated overlay model.

**Safe default until answered:** Plain text only, no variables, mentions suppressed, with a
bounded length and reset-to-default.

**Suggested destination after answer:** Settings declaration or structured Help-overlay schema,
plus preview/editor tests.
## 26. Agent-memory system review batch — answered 2026-06-09

### Q-0060 — Parallel sessions: stay accept-and-reconcile, or add session visibility?

**Area:** Workflow / multi-agent coordination
**Type:** Workflow preference
**Priority:** Medium (the cost is real but bounded — one five-file merge this session)
**Status:** Answered (2026-06-09) — **Routed** → `docs/owner/ai-project-workflow.md` §9

**Maintainer answer (2026-06-09, verbatim batch approval):** "yes I agree with your
recommended answers" → **(a) accept-and-reconcile stays the policy**, with the §9
collision rules as the documented resolution method. The active-sessions ledger (b)
is revisited only if deliberately-parallel sessions become routine. *Not decided:*
nothing about CI/branch mechanics — this is purely the docs-hotspot write policy.

**Recurrence note (2026-06-10, the #677/#678 collision):** first *accidental*
same-item parallel execution — two sessions built the Help-editor plan's PR A
simultaneously (nothing claims queue items); cost = one duplicate build, cleanly
reconciled (#678 closed superseded, deltas salvaged). One more accidental
recurrence is the evidence bar for revisiting option (b); interim mitigation is
the journal rule "check open PRs before starting an implementation slice".

**Question:** Two sessions ran concurrently on 2026-06-09 and collided on the doc
hotspots (router numbers, current-state, roadmap) — resolved cleanly via the §9
conventions, but at ~a small feature's worth of context. Options: **(a)** keep
**accept-and-reconcile** (current; zero coordination overhead, occasional merge cost),
**(b)** a tiny **active-sessions ledger** (each session appends one line — focus +
branch — at start, removes it at end; siblings see who else is writing and which
hotspot to avoid), or **(c)** a soft convention that only one concurrent session does
**docs-hotspot** work (router/current-state/roadmap edits) while others stay code-only
until their END step.

**Agent recommendation (approved):** (a) unless parallel sessions become routine —
the §9 rules made the reconcile mechanical, and (b)/(c) add ceremony every session to
save cost in the rare colliding one.

**Routed to:** `docs/owner/ai-project-workflow.md` §9 (policy note on the router row).

### Q-0061 — Make the end-of-session structured interview a standing convention?

**Area:** Workflow / decision throughput
**Type:** Workflow change (affects how you're pinged)
**Priority:** Medium-high (decision latency is the #1 lane blocker class)
**Status:** Answered (2026-06-09) — **Routed** → `.session-journal.md` Protocol → END step 6a

**Maintainer answer (2026-06-09, verbatim batch approval):** "yes I agree with your
recommended answers" → **yes, scoped**: sessions end with one structured-choices batch
when open questions (1) block a lane or (2) are answerable in ≤1 minute; **≤4 choices
per batch**; deep product questions stay router-only for a dedicated interview session.
*Not decided:* no obligation to interview when nothing blocks — silence stays fine.

**Question:** The two highest-leverage decision moments on 2026-06-09 were structured
choice batches: the gate-lifting interview (16 decisions) and this session's
AskUserQuestion round (4 answers → Q-0054 closed + lane choice in one minute). Should
sessions adopt a standing END-step: *when open router questions touch the session's
area (or block any lane), batch them into one structured-choices prompt before
wrapping up* — making the router primarily an **archive of answers** rather than a
queue of opens?

**Agent recommendation:** yes, scoped — batch only questions that are (1) blocking a
lane or (2) answerable as structured choices in ≤1 minute; never more than ~4 at once
(the AskUserQuestion ceiling); deep product questions stay router-only for a dedicated
interview session. This keeps your interrupt small and kills the "open question ages
three sessions" pattern.

**Routed to:** `.session-journal.md` Protocol → END (new step 6a).

### Q-0062 — Per-area "vision ledger": capture what each area is FOR, in your words

**Area:** Workflow / vision transfer
**Type:** Documentation convention (closes the honest gap in the 2026-06-09 review §4)
**Priority:** Medium
**Status:** Answered (2026-06-09) — **Routed** → `docs/owner/maintainer-working-profile.md` (the convention); folio blocks grow lazily

**Maintainer answer (2026-06-09, verbatim batch approval):** "yes I agree with your
recommended answers" → **yes, lazily**: a ≤10-line owner-voice block per area folio
("what this area is for · what right feels like · one example of wrong"), written
**only when an interview already touches that area** (the interviewer routes ~3 extra
lines per answer); seed from the Q-0051 draft-answer session. *Not decided:* no
backfill sessions — areas without interviews simply don't have blocks yet.

**Question:** Agents can reliably catch a plan that *contradicts a recorded decision*,
but a plan that's internally consistent and merely *off your taste* passes silently —
the decision trails capture what you chose, rarely **why / what the area is for**.
Should each area folio gain a short owner-voice block (≤10 lines: "what this area is
for · what right feels like · one example of wrong"), seeded from the Q-0051
draft-answer session and grown one block per interview?

**Agent recommendation:** yes, but lazily — only write a block when an interview
already touched that area (zero dedicated sessions; the interviewer routes 3 extra
lines per answer). Over a few weeks every active area gets one, and "does this plan
fit the vision?" becomes checkable instead of guessable.

**Routed to:** `docs/owner/maintainer-working-profile.md` (the convention; folios
gain blocks lazily as interviews touch their areas).
## 27. Settings centralization audit — 2026-06-09

### Q-0063 — Is AI's partial scalar-to-policy projection the durable ownership model?

**Area:** AI / Settings platform
**Type:** Architecture + product-surface decision
**Priority:** Important (blocks broad AI Settings redesign, not Phase 1 display correctness)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → settings audit Phase 3 row + `docs/ai-config-ownership.md` projection note + consolidated plan §7

**Maintainer answer (2026-06-09, structured choices):** **Converge gradually** (the
recommendation as written): keep and visibly diagnose the tested seven-key projection
now, **freeze new projected keys**, and plan typed policy/profile panel convergence at
settings **Phase 3** planning; memory stays its own scalar family.
*Answer scope:* decides the **direction** only — it does not fix migration mechanics or
timing, does not approve removing any scalar yet (parity + migration proof first), and
does **not** lift the per-exposure gate on AI UI changes.

**Question:** The generic Settings Manager owns ten AI `SettingSpec`s. Seven guild-policy
keys are already projected after scalar mutation through
`ai_policy_mutation.project_from_legacy_settings` into the typed `ai_guild_policy` row;
memory settings intentionally remain scalar-owned; and the free-text guild-instruction
scalar is explicitly not projected to typed instruction profiles. Should this hybrid
remain the durable contract, or should AI gradually converge on typed policy/profile
panels while retaining only genuinely separate scalar memory settings?

**Recommendation:** Converge gradually on typed policy/profile panels for policy-owned
fields, while keeping memory as its own declared scalar family. Until parity and migration
are proven, preserve and visibly diagnose the existing seven-key projection rather than
removing it.

**Why agents need this:** The projection is already implemented and tested, so describing
AI as an unbridged source-of-truth conflict would be wrong. However, projection is
best-effort: the legacy KV mutation can commit while typed projection fails and emits a
diagnostic event. Agents need to know whether to harden that compatibility seam or plan
its eventual retirement. AI UI changes also remain per-exposure gated.

**Safe default until answered:** Preserve the tested seven-key projection; do not add more
projected keys or new AI UI; surface the hybrid/effective source in plans and diagnostics.

**Suggested destination after answer:**
`docs/planning/settings-cog-centralization-audit-2026-06-09.md`,
`docs/ai-config-ownership.md`, AI subsystem docs, and the Phase 0 target-test plan.

### Q-0064 — Should BTD6 CT-team and announcement pointers become first-class configuration?

**Area:** BTD6 / Settings / bindings
**Type:** Product-surface + ownership decision
**Priority:** Medium (does not block Phase 1 display correctness)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → settings audit Phase 2 BTD6 rows + BTD6 folio/schema plan + consolidated plan §7

**Maintainer answer (2026-06-09, structured choices):** **Binding + guided flow** (the
recommendation as written): promote the **announcement channel** to a first-class BTD6
**binding** with a native channel selector; the **CT group** becomes a **guided advanced
flow** (accept URL/ID → parse → preview → confirm), not a generic scalar text field.
*Answer scope:* decides the **target shapes** only — it does not schedule the work (it
lands with settings Phase 2's BTD6 rows, after Lane 7), and internal BTD6 cache knobs
remain unexposed.

**Question:** BTD6's version-announcement channel and CT team group are operator-settable
through typed command services that directly write allowlisted legacy KV keys, but neither
is declared in the BTD6 schema or discoverable/editable in Settings. Should the
announcement channel become a first-class BTD6 binding with a native channel selector,
and should the CT group become a first-class advanced BTD6 setting/guided flow or remain
an operational command-only pointer?

**Recommendation:** Promote the **announcement channel** to a binding and expose it through
a structured selector. Keep the **CT group** as an advanced guided BTD6 configuration
flow (accept URL/ID, parse, preview, confirm) rather than a generic scalar text field.

**Why agents need this:** The current services are intentional direct-write exceptions,
so an implementation agent must not silently force them through the scalar pipeline.
Owner intent determines whether they are hidden operational pointers or real guild
configuration deserving discovery/audit/UI coverage.

**Safe default until answered:** Keep both typed services and commands unchanged; document
them as command-only exceptions and do not expose internal BTD6 cache keys.

**Suggested destination after answer:** BTD6 schema/service plan, settings command map,
and Phase 2/3 of the settings-centralization audit.

## 28. Consolidated productive-session plan — 2026-06-09

### Q-0065 — Appended scoreboard Lanes 7–8: keep at end of queue, or pull Lane 7 forward?

**Area:** Cross-lane sequencing (Settings / Help)
**Type:** Priority decision
**Priority:** Low-friction (a one-line scoreboard reorder either way)
**Status:** Answered (structured choices, 2026-06-09) — **Routed** → scoreboard Lane 7/8 provenance notes + consolidated plan §7

**Maintainer answer (2026-06-09, structured choices):** **End of queue** (the
recommendation as written) — Lanes 2–6 run in the decided order; Lanes 7–8 follow after
Lane 6.
*Answer scope:* decides **position** only — it does not re-rank Lanes 2–6, does not
change Lane 7/8 scope, and the owner can still pull Lane 7 forward later with a one-line
scoreboard edit.

**Question:** The 2026-06-09 end-of-day consolidation
(`docs/planning/consolidated-productive-session-plan-2026-06-09.md`) appended two
audit-sourced lanes to the multi-lane scoreboard after your owner-ordered Lanes 1–6:
**Lane 7** — settings audit Phases 0+1 (Settings hub lists only *actionable* groups +
every group reachable past Discord's 25-option select cap; today all 28 non-internal
subsystems are listed and 3 are silently unreachable) — and **Lane 8** — help
surface-map count reconciliation + Help characterization tests. Their default position
is **end of queue** (after Lane 6). Should Lane 7 jump forward (e.g. right after
Lane 2), since the 25-option truncation is the only operator-visible *defect* in the
queue, or is end-of-queue fine?

**Recommendation:** Keep end-of-queue. Lanes 2–6 are your decided order, each is
unblocked and small-to-medium, and the truncation is bounded (3 of 28 dropdown
entries, deterministically the lowest-priority ones). Pull Lane 7 forward only if the
truncation bothers you in live use.

**Why agents need this:** Lane order is an owner decision; the appended lanes are
agent-recommended (audit-sourced, #625/#627). Without an explicit answer, agents
execute in scoreboard row order — the safe default — and must not re-order on their
own judgment.

**Safe default until answered:** End of queue — execute scoreboard rows strictly in
order.

**Suggested destination after answer:** the scoreboard lane order
(`docs/planning/multi-lane-execution-plan-2026-06-09.md`) + one line in
`docs/planning/consolidated-productive-session-plan-2026-06-09.md` §7.

## 29. BTD6 cutover decisions — answered 2026-06-09 (data-mapping continuation session)

> Asked as one structured round at the end of the dump-mapping continuation
> (PR #638: ABR + income sets ingested; subtower tail 7/7; buffs 14→15/38).
> All four answers were the recommended options. Answer scope: posture/sequencing
> for the towers cutover — nothing here changes committed combat numbers today.

### Q-0066 — Towers `--all` cutover: dedicated session

**Area:** BTD6 data / cutover
**Type:** Sequencing sign-off
**Priority:** High (the cutover is the remaining decode end-goal)
**Status:** Answered (2026-06-09) — **EXECUTED 2026-06-10 (PR #649: all 25 towers + 17 heroes + 13 paragons game-native v55.1 via the cutover merge; name guard green 55/55; full CI mirror 8543 passed)**

**Maintainer answer (verbatim, 2026-06-09):** "Yes — dedicated session" — the next
BTD6 session executes the `--all` cutover end-to-end (game-native committed stats,
name joins via the name guard, the ~25 value-pinned test updates, maintainer
reviews the full diff). All confirmable pre-cutover decode work is done as of
PR #638.

### Q-0067 — Farm/Village get minimal tier structures at the cutover

**Area:** BTD6 data / schema
**Type:** Schema decision (unblocks the income-multiplier class)
**Priority:** Medium
**Status:** Answered (2026-06-09) — **EXECUTED 2026-06-10 (PR #649: Farm/Village 0 → 64 committed tiers each; nominal attacks suppressed damage-based — Village's Mega Ballista kept; Central Market ×1.1 / Banana Central ×1.25 / Monkey City ×1.2 + discounts/camo/MIB/pierce/cash-per-pop decoded, each prose-pinned)**

**Maintainer answer (verbatim, 2026-06-09, two rounds):** first round: "Yes —
minimal tiers at cutover"; **re-asked the same evening with refined options and
the final answer SUPERSEDES it: "Full tier structure"** — Banana Farm + Monkey
Village get the same game-native tier nodes as every other tower at the cutover
(with attack suppression for Farm's nominal `AttackModel`), not a buffs-only
shape. The prose-confirmed Central Market ×1.1 (+10% Merchantman income), Banana
Central ×1.25 and the Village Primary Training auras land as structured,
renderable buffs inside ordinary tier nodes — one tower-file shape, no second
schema to maintain.

### Q-0068 — Beast Handler subtowers adopt per-tier game names at cutover

**Area:** BTD6 data / naming
**Type:** Curated→curated rename approval (name guard allows it deliberately)
**Priority:** Low
**Status:** Answered (2026-06-09) — **EXECUTED 2026-06-10 (PR #649: beast subtowers carry per-tier names derived from the path's upgrade cards — the leash model keeps the base name at every tier, so Piranha→…→Megalodon / Microraptor line / Gyrfalcon→…→Pouākai come from upgrade names; "Beast" retired via the guard's approved-retirements list)**

**Maintainer answer (verbatim, 2026-06-09):** "Per-tier game names" — committed
"Beast" labels become the game's own per-tier names (Piranha → Barracuda → Great
White → Orca → Megalodon; Microraptor line; Gyrfalcon → … → Pouākai) at the
cutover, making per-tier beast questions answerable by name.

### Q-0069 — Projectile-speed buff semantics: multiplier 0.25 = +25%

**Area:** BTD6 data / decode semantics
**Type:** Gameplay-knowledge confirmation (the committed data had no pinning value)
**Priority:** Low
**Status:** Answered (2026-06-09) — **Routed** → `parse_gamedata._BUFF_FIELD_MAP` comment + decode-status; **implemented same session** (PR #638: `ProjectileSpeedSupportModel.multiplier → projectileSpeedPercentage`, rendered "+25% projectile speed")

**Maintainer answer (verbatim, 2026-06-09):** "Yes, +25%" — Village Primary
Training's projectile-speed buff (and Ezili's totem variant) is a fraction like
the RangeSupport family, not a true multiplier.
---

## 30. Settings preset posture — 2026-06-10

> Numbering note: **Q-0066–Q-0069 belong to the #638 block** (§29 above; merged
> 2026-06-10); this section was numbered Q-0070 in parallel so both landed without
> renumbering (the Q-0060 accept-and-reconcile policy working as designed).

### Q-0070 — Should every setting offer defined presets (+ manual entry + preset-then-edit)?

**Area:** Settings / customization platform (all subsystems)
**Type:** Product UX posture
**Priority:** Medium (directs settings-audit Phase 4 — "structured editors / less text")
**Status:** Answered (owner-stated in chat, 2026-06-10) — **Routed** → settings audit §7
conversion table + §11 Phase 4; the AI-advisor part →
[`../ideas/settings-presets-and-ai-template-advisor.md`](../ideas/settings-presets-and-ai-template-advisor.md)

**Maintainer answer (2026-06-10, verbatim):** "Yes wherever possible everything should
definitely have clear defined presets, aswell as an option for a custom AI design, this
should be treated as an idea for later because it means we would need to hardcore multiple
promt designs/styles as modular settings for the AI cog, so the AI can suggest the right
kind if templates/presets for every task, there should also always be an option for a
completely manual entry, aswell as an option to choose a preset and then edit from there"

**Decoded posture (three requirements for every setting editor, wherever feasible):**

1. **Clear defined presets** are the primary path.
2. **Preset-then-edit** — choose a preset, then customize from it.
3. **Completely manual entry** stays available, always.

*Answer scope:* UX posture for settings editors only. It upgrades the settings audit §7
"keep as plain text" rows (DM template, AI instruction body): even genuinely-authored-text
settings should offer curated starting presets + preset-then-edit, with manual entry
retained. It does **not** approve the AI part — the "custom AI design" / AI-suggested
templates idea ("hardcode multiple prompt designs/styles as modular settings for the AI
cog, so the AI can suggest the right kind of templates/presets for every task") is
explicitly **an idea for later**, captured in the ideas file above, behind the AI
per-exposure gates. It also does not reorder the settings lane — implementation home is
settings-audit **Phase 4**, in its already-decided sequence.

**Question (context):** Shown four live editor modals still requiring free-typed values
(`moderation.warn_timeout_minutes` required-int modal, `ai.ai_default_model`,
`moderation.dm_template`, `ai.ai_guild_instruction_profile`): should the platform
end-state be presets-everywhere, and which fallbacks must always exist?

**Why agents need this:** Phase 4 implementers need to know the target editor shape per
setting class. Numeric/enum/pointer settings already had a structured-editor direction;
this decides the authored-text class too (presets + edit-from-preset + manual), and sets
the bar for any new setting's editor design.

**Suggested destination after answer:** settings audit §7 + §11 Phase 4 (done — pointer
added 2026-06-10); the AI template-advisor slice promotes via the ideas-file lifecycle
only after Phase 4 ships its preset infrastructure.

---

## 31. Untapped-map reconciliation batch — 2026-06-10

> Source: the two merged Codex mapping audits (**#646** runtime/services/workflows ·
> **#647** docs/tests/verification), reconciled in PR #648. These four are the
> *blocking-grade* questions from that work; the maps' remaining question candidates
> (Q-A02 · Q-A03 · Q-B02/Q-DT03) are **held at their map-recommended / no-change
> defaults** — nothing is blocked on them (dispositions:
> [`../planning/consolidated-implementation-plan-2026-06-10.md`](../planning/consolidated-implementation-plan-2026-06-10.md) §7,
> mapping standard §7.1).

### Q-0071 — Who owns a workflow that atomically spans coins + a domain inventory?

**Area:** Economy / inventory / mining (mutation architecture)
**Type:** Architecture ownership decision
**Priority:** High (blocks consolidated-plan **Batch 7** — the economy purchase
two-commit fix, then mining workflow convergence)
**Status:** Answered (structured choices, 2026-06-10) — **Routed** →
`docs/ownership.md` § "Cross-domain transactions" + consolidated plan Batch 7

**Maintainer answer (structured choices, 2026-06-10): A — the domain workflow
service owns ONE DB transaction** calling transaction-aware primitives; coins +
inventory commit or roll back together.
*Answer scope:* mutation-architecture ownership for coin+inventory workflows
(purchase, mining market/repair). It does not start Batch 7 by itself — the batch
runs in its plan order; primitives gaining transaction-awareness is in-scope
plumbing, not a schema change.

**Question (context):** Verified (#646 FIND-RS01/RS02/RS11): a shop purchase debits
coins via the audited `economy_service`, then grants the item via a **separate**
direct `db.add_item` commit — a failure between the two charges the user without the
item; mining market/repair flows have the same split shape. `docs/ownership.md` makes
`economy_service` the sole *coin* writer and inventory direct-lane, but no owner is
defined for the **cross-domain transaction**.

- **A (recommended, both maps):** the **domain workflow service** (e.g. a purchase
  workflow) owns ONE DB transaction and calls transaction-aware low-level primitives —
  coins + inventory commit or roll back together.
- **B:** `economy_service` grows to own all coin+inventory transactions.
- **C:** keep separate commits; add compensation/refund handling only.

**Why agents need this:** it decides where the new purchase/mining workflow modules
live, what the DB primitives must accept (an external transaction/connection), and
what the "no view-level purchase writes" invariant fences.

**Suggested destination after answer:** `docs/ownership.md` (cross-domain transaction
rule) + consolidated-plan Batch 7 design.

### Q-0072 — Mining: which slice is next?

**Area:** Games / mining character platform (active lane)
**Type:** Product sequencing (merges the maps' Q-DT04 + Q-RS02 with GME-1)
**Priority:** Medium-high (the active games lane is ambiguous without it — docs
currently advertise two different "next" slices)
**Status:** Answered (structured choices, 2026-06-10) — **Routed** →
roadmap games row + current-state lane 1 + consolidated plan Batch 7

**Maintainer answer (structured choices, 2026-06-10): C — the workshop-workflow
service boundary first** (FIND-RS02); structures and the game-XP service follow on
the safer base.
*Answer scope:* sequencing only — structures (§7.5) and game-XP (§7.4) stay queued
behind the boundary slice, and the duels-wear slice (Q-0054) is unaffected.

**Question (context):** Wave 1 shipped through Workshop+durability (#624). The
roadmap/brainstorm name **structures** (Forge/Vault/Home, §7.5 sinks) *or* the
**game-XP service** (Wave 2, §7.4) as next; mapping FIND-RS02 found mining's
multi-step writes are orchestrated directly from cogs/views (partial-commit risk —
workshop has the densest multi-write invariant) and recommends a **workflow service
boundary first**.

- **A:** functional **structures** (Forge/Vault/Home) — the next player-visible sinks.
- **B:** the **game-XP service** — the first Wave-2 platform layer.
- **C (recommended):** the **workshop-workflow service boundary first** (FIND-RS02) —
  hardens the densest mutation path before more mining writes land; A/B follow on a
  safer base. Pairs with the Q-0071 answer for the coin legs.

**Why agents need this:** two sessions could otherwise pick incompatible "next"
slices or skip the characterization the chosen slice needs.

**Suggested destination after answer:** games folio + roadmap games row +
consolidated-plan Batch 7/`Q-0072` notes.

### Q-0073 — `!setlogchannel`: Economy-owned, Settings-projected, or moved?

**Area:** Settings / bindings vs Economy (ownership seam)
**Type:** Ownership routing decision (mapping Q-A01 / Q-DT01 — FIND-A02)
**Priority:** Medium (blocks moving/re-projecting the command; Settings Phase 2 can
proceed without it)
**Status:** Answered (structured choices, 2026-06-10) — **Routed** →
consolidated plan Batch 4 (projection rides Settings Phase 2/3)

**Maintainer answer (structured choices, 2026-06-10): B — keep the Economy
implementation but project it into Settings** (it appears in the Settings hub like
any binding; the typed command stays) until a migration/deprecation plan is approved.
*Answer scope:* no command move, no behavior change — a Settings-hub projection row
only. A future full move (option A) would need its own migration plan + a fresh ask.

**Question (context):** Economy owns `!setlogchannel`, a platform-binding-shaped
channel pointer that bypasses the canonical bindings/selector surface (#643
FIND-A02).

- **A (Agent A's pick):** move/reroute it through the platform **binding owner**,
  keeping a compatibility alias.
- **B (recommended safe default):** keep the Economy implementation but **project it
  into Settings** (it appears in the Settings hub like any binding; typed command
  stays) until a migration/deprecation plan is approved.
- **C:** keep as-is, typed-only.

**Why agents need this:** decides mutation ownership, Help/Settings placement, and
whether a migration + compatibility tests are in scope for Settings Phase 2/3.

**Suggested destination after answer:** settings audit §11 (Phase 2 or 3 row) +
`docs/ownership.md` if moved.

### Q-0074 — Admin surface: metadata tier vs administrator-admitted routes?

**Area:** Admin hub / registry metadata / command access
**Type:** Display-vs-execution posture (mapping Q-B01 / Q-DT02 — FIND-B03)
**Priority:** Medium (blocks FIND-B03 implementation only)
**Status:** Answered (structured choices, 2026-06-10) — **EXECUTED 2026-06-10
in PR #657** (consolidated plan Batch 6 rode it along): `admin` subsystem
`visibility_tier` owner → administrator (source-backed inventory in the PR:
`!adminmenu`/stats are `has_permissions(administrator=True)` routes; cog
load/unload/reload + slash sync keep `commands.is_owner()` execution checks).
Placement == admission is pinned by the help-catalogue `tier_mismatch`
finding (`tests/unit/services/test_help_catalogue.py`) for **every** hub.

**Maintainer answer (structured choices, 2026-06-10): A — make registry/Admin-Help
placement administrator-visible** (after a quick source-backed inventory), keeping
owner-only checks on the genuinely dangerous actions.
*Answer scope:* display/placement posture only — no execution-admission loosening;
the inventory step decides which actions stay owner-checked, pinned by a
placement-tier == admission-tier test when implemented.

**Question (context):** Admin registry/Help metadata presents owner-tier while some
admin routes are administrator-admitted — display placement and execution admission
disagree (#644 FIND-B03).

- **A (recommended, Agent B's pick):** make registry/Admin-Help placement
  **administrator-visible** (after a quick source-backed inventory) while keeping
  owner-only checks on the genuinely dangerous actions.
- **B:** make the entire Admin panel owner-only.
- **C:** split owner-only controls from admin tools into separate surfaces first.

**Why agents need this:** Help/registry tiering and admission checks must agree
before classification work (consolidated-plan Batch 2) touches the Admin rows.

**Suggested destination after answer:** governance/access docs + the Admin hub
registry metadata + a pinning test that placement tier == admission tier.

## §32 — Mining/tool/gear finalization session decisions (2026-06-10)

> Asked and answered live (structured choices) during the mining-finalization
> planning session; recorded here so the canonical home isn't the plan file.

### Q-0075 — recipes.json ↔ item catalog: trim, extend, or both lanes?

**Area:** Mining / crafting content
**Type:** Product taste (content scope)
**Priority:** High at the time (blocked the RS02 recipe reconciliation)
**Status:** Answered (structured choices, 2026-06-10) — **Executed** →
RS02 stage 2 (trim + alignment lint) and PR 3 (the new tiers)

**Maintainer answer (structured choices, 2026-06-10): "Curated economy +
deeper ladders" (the recommended option).** The item catalog
(`utils/mining/items.py`) is the single source of truth; recipes whose
outputs are real mining-game items stay; the tool ladders get **new
in-economy tiers** (gold/diamond pickaxe, a depth-3 light, stronger combat
gear — each with stats, durability, shop/repair prices); the
Minecraft-flavor leftovers (furnace, enchantment table, bow, golden apple,
shovels…) are trimmed.
*Answer scope:* content direction for the mining economy; the alignment
lint (`tests/unit/utils/test_recipes_catalog_alignment.py`) governs all
future additions.

**Question (context):** the legacy `recipes.json` carried 47
Minecraft-style recipes; ~25 products were unknown to the catalog
(unclassified, non-equippable, valueless) and 7 used unobtainable
materials. Options were (A) curated trim + deeper ladders, (B) integrate
the full 47-recipe tree, (C) curated gear + legacy recipes as trophies.

**Suggested destination after answer:** done — `docs/subsystems/games.md`
(economy loop bullet) + the alignment lint.

### Q-0076 — How much PIL visual work in the finalization session?

**Area:** Mining / profile visuals (brainstorm §7.6)
**Type:** Scope (visual roadmap pacing)
**Priority:** Medium
**Status:** Answered (structured choices, 2026-06-10) — **Executed** → PR 3

**Maintainer answer (structured choices, 2026-06-10): "Inventory card +
stat card" (the recommended option).** Wire the existing tested
`utils/mining_render.py` inventory-card renderer into the Inventory panel
AND add a PIL **stat card** for `!character` (level/XP bar + gear +
durability + net worth, zero custom art, graceful embed fallback). The
paper-doll stays Wave 3.
*Answer scope:* this session's visual slice only; the §7.6 visual roadmap
(stat card → paper-doll) is unchanged.

**Suggested destination after answer:** done — brainstorm §7.6 stays the
visual-roadmap home; `docs/subsystems/games.md` records the shipped card
seam.

## 33. Production data-lane batch — 2026-06-10 (eval session live findings)

### Q-0077 — Should the BTD6 blob store auto-sync from the bundled files at boot?

**Area:** BTD6 data lane / production operations
**Type:** Operational posture (boot-time DB write)
**Priority:** Medium (the drift class is now *surfaced* — this decides whether it also self-heals)
**Status:** ✅ **IMPLEMENTED 2026-06-21 (PR #1255)** — built per the 2026-06-19 decision **(b)**. Owner **re-confirmed (b) over a content-aware variant** in-session (2026-06-21) when asked: strict version-newer only, accepting that **same-version data edits (e.g. the #1249/#1251 buff windows) still need a manual `!btd6ops seed-data`** — they do NOT auto-apply. `btd6_data_service.auto_seed_enabled()` (postgres + `BTD6_AUTO_SEED` kill-switch) + `bundled_newer_than_served()` (strict version compare) gate a `seed_postgres_from_files()` call in `btd6_cog.cog_load`, beside the #676 drift warning. *(Prior: ✅ ANSWERED 2026-06-19 (owner, question panel) — (b) auto-seed when the bundled files are strictly newer; never clobbers a deliberately-newer store. Original question below.)*

**Question:** Production serves BTD6 fixtures from the `btd6_data_blobs`
Postgres table (`BTD6_DATA_BACKEND=postgres`), so a data PR updates the
bundled files but the store keeps serving its old copy until someone runs
`!btd6ops seed-data` — this silently confused the 2026-06-10 eval ("(55.0)"
stamps, empty boss roster, on current code). PR #676 makes the drift loud
(boot log warning + a `!btd6 status` ⚠️ field) and makes seed-data apply
immediately. Should the bot go further and **auto-seed at boot when the
bundled files are newer than the store** (true zero-touch: merge → deploy →
data current)?

**Why it needs the owner:** auto-seed is a **DB write at boot** and would
overwrite a blob store that was *deliberately* seeded with newer data than
the repo (the refresh-workflow direction). Options: **(a)** keep
surface-only (current after #676 — recommended until the drift recurs),
**(b)** auto-seed only when the bundled version is strictly newer,
**(c)** auto-seed whenever versions differ.

**Safe default until answered:** (a) — loud surfacing, manual seed-data
(now one command, immediate effect).

**Suggested destination after answer:** `docs/subsystems/btd6.md` data-lane
note + `btd6_cog.cog_load` (if (b)/(c): implement beside the drift warning).

## 34. Product-vision capture session decisions — 2026-06-10

> Asked and answered live (structured choices, one round) during the
> vision-ideation capture session (PR #680); the capture doc is
> [`../ideas/superbot-vision-2026-06-10.md`](../ideas/superbot-vision-2026-06-10.md)
> (items V-01…V-12 / AG-01…AG-15, tensions T-1…T-5).

### Q-0078 — Vision-capture routing picks (difficulty switching · pets reconcile · help home layout · next planning targets)

**Area:** Games / Help-interface / product routing
**Type:** Product posture + planning-queue selection (batched structured choices)
**Priority:** Medium (each answer unblocks its lane's design work; nothing was implementation-gated this session)
**Status:** Answered (structured choices, 2026-06-10) — **Routed** → capture doc §5/§6 updated; RPG survival design structured into [`../planning/rpg-survival-difficulty-design-2026-06-10.md`](../planning/rpg-survival-difficulty-design-2026-06-10.md); roadmap rows updated

**Question (4 sub-questions, one round):** (1) Can a player change RPG
difficulty after starting (T-3)? (2) How do the vision's story pets reconcile
with the existing egg-based pets plan (T-1)? (3) Which top-level Help Home
button layout (T-4)? (4) Which idea clusters become the next planning targets?

**Maintainer answers (2026-06-10, all four verbatim from the structured round):**

1. **Difficulty switching = "One-way ascent"** — start anywhere; may move
   easy→medium→hard at any time, never back down; leaderboard entries carry a
   difficulty flag (⭐/⭐⭐/⭐⭐⭐). *(The recommended option.)*
2. **Pets = "Both paths"** — eggs stay the common acquisition (existing pets
   plan unchanged in shape); quest-rescue becomes the rare/unique-species path
   once the quest engine exists; party cap grows 1→3 across phases; the
   vision's journey buffs (scout / gold-sense) implement as small
   encounter-table modifiers. *(The recommended option.)*
3. **Help Home = "4 buttons"** — 🎮 Play (games·btd6·economy) · 🧭 Server &
   Info (utility·community·stats·tickets) · 🙋 My Stuff (profile·my
   settings·reminders — needs the per-user prefs feature, V-04) · ⚙️ Manage
   (settings·server-mgmt·moderation·admin·diagnostics, staff-visible only).
   *(The recommended option.)*
4. **Next planning targets = "RPG survival design" + "Help home +
   navigation"** (two picks). Per-user preferences and AI DM v1 stay
   captured-only for now.

*Answer scope:* product **posture + planning-queue** decisions. Nothing here
approves implementation: the survival design doc and the help-home/navigation
plan each still promote through `docs/ideas/README.md` gates, and the Help
work sequences with the in-flight Help lane (overlay editor UI plan) per
capture-doc T-4. The pets answer **amends the pets plan's future phases**
(party 1→3, rescue path) without changing its P1–P4 shape.

**Routed to:** capture doc §5 (T-1/T-3/T-4 marked answered) + §6 ledger;
`docs/planning/rpg-survival-difficulty-design-2026-06-10.md` (new, the
grooming move); `docs/roadmap.md` games + interface lanes;
`docs/planning/pets-companions-plan-2026-06-09.md` (amendment note).

### Q-0079 — "Cleaner UX" clarified: no per-panel button caps; better-defined buttons over removal

**Area:** Help-interface / UX doctrine (V-03, V-12, AG-01)
**Type:** Owner correction of a captured idea (unprompted statement, follow-up to Q-0078)
**Priority:** Medium (binds the help-home/navigation plan before it is structured)
**Status:** Answered (owner statement, 2026-06-10) — **Routed** → capture doc §1/§3/§4/§6 notes; roadmap interface row

**Owner statement (2026-06-10, verbatim):** "the 3 buttons per panel is never
going to work, but we can definitely aim for a cleaner UX, with less or better
defined buttons, tho we can't just remove buttons because almost all of them
are actually useful." *(In response to the agent's closing pitch for AG-01's
"≤3-clicks check" as a CI invariant; he affirmed the captured ideas overall.)*

**Durable conclusions:**

1. **No numeric per-panel button budget — ever.** Panels keep every useful
   button, and almost all existing buttons are useful. Any future UX lint that
   counts buttons per panel is rejected posture.
2. **The vision's "3" is navigation depth.** "Maximum of 3 buttons to reach
   any game, setting, or action" (capture doc §1 / V-03) means **presses from
   Help Home** — an aim to design toward, not a cap on how many buttons a
   panel may show.
3. **"Cleaner UX" = fewer *or better-defined* buttons.** The levers are
   clearer labels, grouping, row order/placement, and consistent conventions.
   Removing a button is allowed only when that specific button is genuinely
   redundant — never to satisfy a quota.
4. **AG-01 bounded accordingly.** If promoted, the CI-checkable UX invariants
   are (a) reachability **depth** over the help projection / hub registry and
   (c) zero-dead-buttons. A button-count check is out.

**Routed to:** capture doc (`../ideas/superbot-vision-2026-06-10.md`) §1
owner-voice clarification + V-03 + AG-01 + §6 ledger row; `docs/roadmap.md`
interface planning row. The help-home/navigation plan (the named next grooming
target) inherits these as design constraints.

## 35. Deep product-posture round — 2026-06-10 (same session, agent-initiated)

> The owner asked the agent to pose its own highest-value questions ("specific
> or maybe even very broad … questions that I would possibly really need to
> think about"). One structured round, four areas — each checked against the
> router + idea docs first as genuinely undecided. (A fifth candidate — bot
> personality — was dropped before asking: owner-vision-2026-06-08 §16 already
> decided it: **funny/sarcastic, dry wit, consistent across all commands**.)

### Q-0080 — Distribution ambition: is SuperBot ever for servers the owner doesn't run?

**Area:** Product / platform posture
**Type:** Owner posture decision (agent-initiated deep round)
**Priority:** High (a design filter every future plan inherits)
**Status:** Answered (2026-06-10) — **Routed** → roadmap posture line; capture doc §5 (T-6) + §6

**Question:** Technical multi-tenancy is law (owner-vision §9: no
single-server assumptions), but the *ambition* was undecided: should SuperBot
ever run on servers the owner doesn't control — up to a public listing?

**Answer (2026-06-10): "Public bot is the goal."** Anyone can invite it one
day; multi-tenant hardening, per-guild AI budgets, onboarding polish, and
abuse-resistance are first-class concerns, not nice-to-haves.

**Durable conclusions:**

1. **V-01's 2-minute setup is for strangers** — it is the public bot's front
   door, not a convenience for the owner's own installs; its KPI weight rises.
2. **No feature may assume a trusted/home guild.** Per-guild scoping stays
   law; new surfaces consider rate-limiting/abuse-resistance at design time.
3. **Every AI feature needs a per-guild cost story** (Q-0082 + tension T-6);
   per-guild opt-in, off by default (Q-0040) is confirmed as the public-scale
   posture, not just caution.
4. **Nothing is promoted by this answer** — it is a design filter, not a
   workstream. A dedicated public-readiness audit is a future grooming
   candidate once the RPG survival layer + Help Home land.

### Q-0081 — Flagship RPG core: solo-alongside or shared world?

**Area:** Games / character platform / quest engine
**Type:** Owner posture decision (agent-initiated deep round)
**Priority:** High (the queued quest-engine/AI-DM plan forks on it)
**Status:** Answered (2026-06-10) — **Routed** → survival plan posture note; future quest-engine plan inherits

**Question:** Is the flagship RPG ultimately a *solo* adventure played
alongside others (own world-state; leaderboards; opt-in co-op moments) — or
one *shared persistent world* per server where players deplete, discover, and
trigger events affecting everyone?

**Answer (2026-06-10): "Solo core + co-op moments"** *(the recommended
option)*. Each player owns their world-state forever; multiplayer — duels,
expeditions (AG-10), party quest sessions, server-wide events — is an opt-in
overlay on the solo core.

**Durable conclusions:**

1. **The quest engine / AI-DM plan is single-party first.** Shared state, if
   any, lives only inside opt-in session/overlay scopes — never in the
   persistent world.
2. Mining's "personal position, per-guild seed" is confirmed as the
   **end-state shape**, not just v1 caution; shared dig-sites stay a separate
   bounded overlay if ever built.
3. Server-wide *events* on solo worlds (one shared scoreboard, communal
   moments) remain compatible overlays — they ride the solo core.

### Q-0082 — AI spend posture: what do the budget caps protect?

**Area:** AI lane / product economics
**Type:** Owner posture decision (agent-initiated deep round)
**Priority:** Medium-high (binds the AI-DM plan's budget gates; compounds with Q-0080)
**Status:** Answered (2026-06-10) — **Routed** → capture doc §5 (T-6) + §6; the AI-DM plan cites it when structured. **Interim € figure set 2026-06-12 (question panel): €30/month** — see conclusion 2.

**Question:** The cost *mechanism* is decided (Q-0040: budget-capped seams,
degrade-closed, never silent overspend) — but no number or posture exists for
what the caps protect. What is the spend posture?

**Answer (2026-06-10): "Hard ceiling, graceful degrade"** *(the recommended
option)*. The owner names a comfortable €/month; per-guild and global caps
derive from it; at the cap, AI features visibly rest ("the storyteller is
sleeping") until reset.

**Durable conclusions:**

1. **One owner-set global ceiling → derived per-guild budgets.** Predictable
   forever; no silent growth.
2. **The € figure: interim ceiling set 2026-06-12 (owner, question panel) = €30/month
   global hard ceiling** (picked over the recommended €15 — headroom for joint
   live-testing + the new metered lanes; datapoint at decision time: ~€12 spent total).
   Refine after the first real prod measurements; per-guild budgets derive from it.
   *Answer scope: the interim global number only — mechanism/degrade behavior unchanged
   from the 2026-06-10 answer; metered designs (NL events Q-0112, YouTube summarization)
   build against €30/mo until remeasured.*
3. **Degradation is visible and in-world** (storyteller-resting copy), never
   silent — matches Q-0040's "never silent overspend".
4. Public ambition (Q-0080) × cosmetic-only donations (Q-0039) × a fixed
   ceiling = **tension T-6** (capture doc §5): at public scale this forces
   default-off AI + tiny per-guild budgets + heavy caching; if AI ever proves
   core to the public product, Q-0039 is the lever to revisit — owner's call,
   flagged so nobody resolves it silently.

### Q-0083 — Workflow autonomy end-state: how self-driving does the system get?

**Area:** Collaboration model / agent ecosystem
**Type:** Owner north-star decision (agent-initiated deep round)
**Priority:** Medium (orients tooling/health/deploy work; changes nothing today)
**Status:** Answered + clarified (2026-06-10) — **Routed** → collaboration-model north-star note; bot-awareness lane cites it when resumed. **Timing corrected same day by Q-0088 (§37): the foundation starts now, small** — the end-state remains staged/not-near-term.

**Question:** Today agents build and push; the owner merges, deploys,
prod-checks; a 3am breakage waits for his next session. How self-driving
should the system ultimately become — for breakage and for green mergeable
work?

**Answer (2026-06-10): "Full self-driving is the goal."** The bot detects its
own issues, spawns its own fix sessions, merges green work, deploys with
canary + auto-rollback; the owner steers by vision drops and vetoes.

**Owner clarification (same conversation, verbatim):** "just to be clear,
completely self driving is not yet a near term goal, but ultimately there
will not be much else left to do if I keep implementing at the current
speed."

**Durable conclusions:**

1. **End-state, not a grant.** Nothing changes today: agents do not merge or
   deploy; the owner remains the merge/deploy/prod-check gate.
2. **The path is graduated trust** — the Q-0048 standing-lift pattern
   generalized into a ladder: autonomy tiers get proposed area-by-area through
   this router as track record accumulates; each tier is its own owner
   decision.
3. **Arrival is demand-driven, not scheduled.** Full self-driving becomes
   relevant as the implementation backlog thins ("not much else left to do").
   Design health/deploy/tooling work so the system *could* get there
   (bot-awareness plan, canary/rollback ideas align) without promoting it now.

### Q-0084 — Merge autonomy granted: agents merge their own session PRs when done

**Area:** Collaboration model / agent ecosystem — the **first granted Q-0083 trust tier**
**Type:** Owner grant (unprompted, same conversation as Q-0083)
**Priority:** High (changes every session's end protocol immediately)
**Status:** Granted (2026-06-10) — **Routed** → CLAUDE.md session workflow; collaboration-model north-star note; ai-project-workflow §9

**Owner statement (2026-06-10, verbatim):** "I do think claude agents should
be able to merge, because now there are still often problems with merge
conflicts when multiple agents are working, and I try to keep only 1 or 2
agents active at the same time but I have too many ideas that I want to
discuss and plan and execute, so it would be great if agents would merge
their PRs whenever they feel like they are done."

**The grant:** an agent **merges its own session PR itself** when it judges
the work done — no waiting for the owner. Motivation: stale open PRs are the
parallel-agent conflict window; prompt merges shrink it, which is what lets
the owner run more agents at once (his stated goal — more ideas in flight).

**The envelope (the existing quality bar, no new ceremony):**

1. **CI green on the final head** — never merge red or unverified.
2. **Re-fetch + merge `origin/main` first** (the §9 END-protocol sync);
   UNION-resolve conflicts — the merging agent is the reconciler.
3. **Merge-commit method** (repo convention on `main`).
4. **Scope: your own session PR** (or one you were explicitly asked to
   drive). Draft → ready → merge replaces draft → ready → wait.
5. **Merge ≠ deploy.** Production restart / prod-checks / live eval items
   remain the owner's — Q-0083's other gates are unchanged by this tier.
6. The grant covers *completion*, not *scope approval*: if you're genuinely
   unsure the work is wanted (not whether it's green), the existing act-vs-ask
   rules still apply before merging.

**First exercise:** PR #680 (this conversation) — main re-synced (#681
absorbed, current-state same-line UNION), then merged by the agent.

**Routing addendum (2026-06-10, same conversation):** the owner will **rework
his ChatGPT session-prompt templates himself** and apply the right ones across
his AI projects, so future session prompts stop carrying pre-Q-0084 residue
("never push elsewhere / don't merge"). Until that lands, treat such lines as
template residue per CLAUDE.md — the repo rules win.

## 36. Production deployment & toolchain — 2026-06-10 (outage session)

### Q-0085 — CI/local (3.10) vs production (3.13) interpreter drift: align, and in which direction?

**Area:** Toolchain / CI parity / production deployment
**Type:** Technical posture with owner-visible cost — needs an owner pick
**Priority:** Medium (latent risk, not blocking; now documented and visible)
**Status:** **DECIDED 2026-06-16 (owner, in-session) — option 1: align CI/local UP to 3.13.** One
planned toolchain-migration session moves the workflow pins, `requirements-dev` wheels, the
`python3.10 -m` rule (CLAUDE.md/hooks/scripts/docs), and the sandbox env to 3.13 so the suite runs on
the interpreter that serves users. **Not yet built** — it needs its own focused session + verification
pass (every check command changes); tracked as the next toolchain task. Context below.

**Context (discovered during the 2026-06-10 Railway build outage, PR #685):**
CI and every local check run **Python 3.10** (workflow pin + the repo-wide
`python3.10 -m` rule). Production on Railway has **always run 3.13** — the
unpinned railpack default, now pinned to `3.13.13` (see
[`operations/production-deployment.md`](../operations/production-deployment.md)). Nobody had written
this drift down: the test suite literally never runs on the interpreter that
serves users. It has not bitten yet (8,900+ tests green on 3.10, prod stable on
3.13), but version-specific behavior (asyncio timing, stdlib deprecations,
c-extension wheels) would surface in prod first.

**Options:**

1. **Align CI/local up to 3.13** *(recommended eventually)* — one planned
   toolchain-migration session: workflow pins, `requirements-dev` wheels,
   the `python3.10 -m` rule in CLAUDE.md/hooks/scripts/docs, sandbox env.
   Cost: touches every check command; needs its own verification pass.
2. **Pin prod down to 3.10** — matches the tested surface exactly, but
   *changes* the interpreter prod has run stably for months; riskier than it
   looks and goes backwards in support lifetime.
3. **Accept documented drift** (status quo) — cheapest; the drift is now at
   least visible in `operations/production-deployment.md`.

**Recommendation:** option 1 as its own session once the active lanes allow —
not as a rider on anything else. Until then option 3 holds.

### Q-0086 — Joint live-testing: owner provisions AI provider keys into the agent session environment

**Area:** AI tooling / production verification / collaboration workflow
**Type:** Owner commitment (process + infrastructure)
**Priority:** High for the AI lane (it unblocks the standing prod-check gate)
**Status:** **Committed** (2026-06-10) — pending the owner's setup

**Owner statement (2026-06-10):** "I will try to add my AI api keys to your
environments variables, so we can test together while you (different session)
have direct access to the logs and will be able to implement live changes
while I test everything, that will probably be the best and most secure way."

**What this changes when done:** the standing constraint "model loop awaits
the maintainer's production check (**no sandbox provider key**)" on the
orchestration P4 (#634) and answerability P3 (#639) features partially
lifts — a session can boot the **test bot** (Galaxy Bot, journal runbook)
with real provider keys, watch its logs directly, and fix live while the
owner tests from Discord. The intended mode is a **joint session**: owner
drives Discord, agent drives logs + code.

**Agent rules when keys are present (standing):** treat them as secrets —
never print/echo them, never write them to a file/commit/PR/log, never send
them to any tool output; use them only via the bot's own env mechanisms.
Scope note: this gives sessions the *test bot* + provider keys, not Railway
access — production logs/dashboard stay owner-side.

## 37. Brainstorm round 2 — balance philosophy + the self-driving correction — 2026-06-10 (same conversation)

### Q-0087 — RPG balance philosophy: casual-core, grinder-prestige, never mandatory — and simulation approved as the balance methodology

**Area:** Games / RPG survival design (binds the survival plan's numbers)
**Type:** Owner design principle (unprompted, reacting to the simulation idea)
**Priority:** High for the games lane (it defines what "balanced" means)
**Status:** **Answered** (2026-06-10) — **Routed** → survival plan **D0** (philosophy) + **P0** (simulation harness) + **G2** (numbers confirmed from sim outputs)

**Owner statement (2026-06-10, verbatim):** "that would be a great way to
test if my game idea would be fun and playable for everyone, we can decide a
perfect balance between gaining items and spending them, so users could just
play for a few minutes a day and gain real progress, but there should also be
a reward for grinders who play for a long time and achieve certain goals, tho
it should never feel like those goals are mandatory to increase your level
and the things you can do."

**Reading:** dual-track progression — the **casual track owns capability**
(levels, unlocks, "the things you can do"); the **grind track owns prestige
and surplus** (records, surplus wealth, leaderboards), never core capability.
Plus an explicit methodology approval: **simulate before shipping** — the
survival plan now carries a P0 balance-simulation harness whose output bands
(casual progress/day · grinder surplus/hour · the capability-gap
"mandatory-feel" metric) ship as CI-pinned tests, and G2's owner round
presents simulation evidence instead of guesses.

### Q-0088 — Self-driving timing corrected: build the foundation now, small — bounded sessions + automatic continuation

**Area:** Collaboration model / agent ecosystem (corrects Q-0083's timing)
**Type:** Owner correction + direction (unprompted, explicit self-correction)
**Priority:** High (changes session protocol design; queues a build)
**Status:** **Direction set** (2026-06-10) — **Routed** → `ai-project-workflow.md` §10 (the foundation design); roadmap session queue (Stage 0 build); collaboration-model north-star note updated; Q-0083 entry cross-stamped

**Owner statement (2026-06-10, verbatim core):** "at the moment the level of
AI is so advanced that the only thing I should realistically be doing is
adding more ideas and setting strict guidelines on what the desired functions
and UX should be, apart from that everything should be automated, and I know
I said that that is an idea for much later, but I have to correct myself, and
I'm not saying I want everything automated right away, but I do think we
should at least create a foundation, and implement this in a small way."

**Two operational problems he put on record (the foundation's requirements):**

1. **Runaway unguided sessions:** "a few times now I thought a session was
   done, but then it produced a few more PRs unguided, and that caused one
   duplicate function to be build" (the #678-class collision — Q-0060's
   recurrence data point is the same event family).
2. **Long-context degradation:** "you can work pretty well up untill you get
   to about 700-800K context, and then your code noticably starts to become
   a little worse over time."

**His proposed shape (verbatim):** "the best thing would be to have a clear
stop condition for each session, like, always do 2 tasks and clean up the
docs + guide the next session, but that would only work if we have a way to
automatically start a next session aswell."

**The routed design (workflow §10):** a **bounded-session protocol**
(~2 substantial tasks → ledger/docs cleanup → handoff → END; wrap before
~700K context; no new unguided PRs past declared scope — extra work goes into
the handoff queue, not the session) + a **staged continuation mechanism**:
**Stage 0** = a `workflow_dispatch` GitHub Action that starts a fresh
Claude Code session from the standing handoff (one click, fresh context, no
schedule, no surprise spend) · **Stage 1** = the scheduled caretaker (cron)
once Stage 0 has proven itself. The protocol **activates when Stage 0
lands** (his conditional, honored). Owner provides: the Anthropic API key as
a repo secret + a per-run budget choice. Until activation, the ~700K
guidance + no-unguided-PRs rule apply as journal guidance immediately.

### Q-0089 — Mandatory session ender: every agent contributes ≥1 new idea

**Area:** Collaboration model / agent ecosystem (session END protocol)
**Type:** Owner directive (unprompted, brainstorm round 4)
**Priority:** High (changes every session's END protocol immediately)
**Status:** **Directed** (2026-06-10) — **Routed** → CLAUDE.md § Session & plan workflow (new bullet); journal END checklist + QR row; ideas README intake note

**Owner statement (2026-06-10, verbatim core):** "I noticed that AIs don't
really come up with many ideas or improvements themselves, while if they did,
and they would do it consistently, then you are pretty much guaranteed to
eventually come up with a good idea, so there I have another idea, we should
make it a mandatory session ender for each agent to come up with 1 new idea
for the bot or for the AI network, it can be anything as small as a change of
wording in an embed, or as big as a whole new cog or function, or an
architectural refractor, maybe a new document for the AI memory, the point
is, I've been trying to get AI to be more creative and to be part of the
improvement process."

**The rule as installed:** at session END, before the log is written, the
agent contributes **one new idea it genuinely believes in** — bot-facing or
network/workflow-facing, any size (embed wording → new cog → refactor → new
memory doc). Mechanics: dedup-grep `docs/ideas/` + the roadmap first (a
duplicate doesn't count); capture it in the session log under a `💡 Session
idea` flag with one line of *why it's worth having*; if it's substantial,
give it an idea file / README index entry like any captured idea. Quality
bar: a forced-feeling filler idea is worse than none — the owner's intent is
**consistent generation**, volume-over-time, not ceremony; "genuinely
believes in" is the filter. The grooming pass (Q-0015) *moves existing*
ideas; this rule *generates new* ones — both run at END.

**First execution:** this session's 💡 idea — the **owner's morning digest**
(see the session log + ideas README): the bot/caretaker posts a daily
"what changed in your bot yesterday" summary built from merged PR titles,
so the owner experiences the network's velocity as a product feature.

## 38. Gap-analysis round — 2026-06-11 (owner probe: "what's still missing?")

### Q-0091 — Cross-server character identity: per-guild, global, or hybrid?

**Area:** Games / open-world architecture / public-bot posture (Q-0080)
**Type:** Architectural product decision — currently *unasked anywhere*
**Priority:** High-before-ecosystem-#2 (re-keying tables later = migration nightmare)
**Status:** **Answered** (2026-06-11) — the owner invented a **fourth model**
none of the offered options contained: **conservation-based optional transfer
with a destination-aware cap.**

**Owner statement (2026-06-11, verbatim):** "I think it should be an option,
but it should be very nuanced, for instance, I don't think it's a good idea
to just let people take their full high lvl player into a new server, that
would be kinda unfair, what if the server is new or something like that, what
I do think, that based on the average lvls of the server they join as their
second server, thay should be able to choose between either starting from 0
or transferring up to 10% of they cash and items and gear etc from the other
server, and it would actually take the items from their inventory there and
give them to their other character, so it's not free and always optional and
still fair to the players of the server that didn't start somewhere else."

**The model as canon (binds the V-13 federation + ecosystem-#2 design):**

1. **Characters stay per-guild** (tables keep their `(user, guild)` keys —
   no re-keying migration ever needed).
2. **Joining another server offers a choice:** start from 0, **or** transfer
   **up to 10%** of cash/items/gear from an existing character.
3. **Transfer = conservation, not duplication:** the items/cash are *removed*
   from the source character and given to the destination one. Not free,
   always optional, fair to native players.
4. **Destination-aware calibration:** the offer is shaped by the destination
   server's **average level** (a high-roller can't stomp a brand-new server).
   Exact calibration mechanics = build-time design (+ a P0-style simulation
   pass before shipping; anti-abuse review per Q-0080 — transfer round-trips
   as a laundering vector must be checked).

**Substrate consequence (V-13):** items/gear need a **serializable,
audited cross-guild transfer seam** — design it into the shared-substrate
extraction when ecosystem #2 work starts.

**Original options + context (superseded by the owner's model):**

**Context:** every game table is keyed `(user, guild)` — a player's character
exists per server. Public-bot era makes this the biggest invisible decision:

1. **Per-guild (status quo):** every server a fresh start — clean local
   economies, equal-start PvP preserved, zero migration; progression doesn't
   travel, players restart everywhere.
2. **Global identity:** progression travels with the player; but server
   economies bleed (a whale arrives pre-rich), equal-start dies, and the
   per-guild balance story (Q-0087 bands) fractures.
3. **Hybrid** *(agent lean)*: **local progression** (levels, wealth, gear —
   per-guild like today) + **global veneer** (cosmetics, titles,
   collection-log completion, account-level achievements travel). Preserves
   every economy invariant while giving players a portable identity. Maps
   cleanly onto Q-0039 cosmetic-only monetization later.

**Sequencing:** decide before ecosystem #2 multiplies the keyed tables; the
full gap list is [`ideas/gap-analysis-2026-06-11.md`](../ideas/gap-analysis-2026-06-11.md).

### Gap-round addenda (2026-06-11, same conversation)

- **Blanket grant:** the owner approved the remaining gap items —
  "I agree and you can implement all of them or make the preperations for
  it." Routed: item 6 (actions Node-24 bump) **executed in PR #694**; items
  2 (data export/erasure), 4 (session telemetry), 5 (AI spend metering) =
  **granted, queued for implementation/prep** (roadmap session queue);
  item 3 (alerting) stays owner-deferred.
- **Q-0082 cost datapoint:** "I have spend about 12 euro so far on the API
  requests made by my bot and we have tested it a very long time" — actual
  spend is tiny; ceiling pressure low. The **meter** (item 5) remains wanted
  for the public era, but the € figure is even less urgent than assumed.
- **Real-user testing culture (recorded):** the owner runs his friends as a
  growing tester community and *teaches eval methodology* — steering them
  from exhaustive enumeration ("every tower's upgrades by name") to
  **abstract multi-step questions that require calculation/research**, which
  find non-working commands "in one or two messages." He keeps inviting more
  people "for randomness." This is live input for the commissioned
  untested-surface checklist session: the human battery exists and is being
  trained.

### Q-0092 — Gear-lane night-session round (structured choices, answered so the session runs unattended)

**Area:** Games / gear lane (V-16 phase 1) — the prepared night session
**Type:** Structured choices (asked at the owner's request before he slept)
**Priority:** Immediate (the night session executes on these)
**Status:** **Answered** (2026-06-11)

1. **Slot model = set-pieces + set bonus** (the ambitious option): replace
   the single `armor` slot with **helmet / chestplate / leggings / boots**,
   `shield` as its own slot, sword→`weapon` (≈9 slots total, matching the
   asset pack 1:1), **plus a small same-tier full-set stat bonus** — full-set
   collection becomes a goal.
2. **New ores = YES:** **bronze and silver join the mining depth ladder** as
   real ores (loot-table rows at sensible depths), giving every gear tier a
   clean smelt-the-ore → forge-the-gear path. Mining deepens for free.
3. **Stat numbers = full authority** (owner verbatim: "I will run this with
   fable 5, so I trust that with a little guidance it will create proper
   code, it can go as far as it can") — the session sets the tier
   damage/defense tables itself: simulation-sane, monotonic per tier,
   documented; a later owner round can retune.
4. **Priority = all three required** (items+recipes · picker previews ·
   compositor seam) — the owner explicitly authorizes pushing past the
   bounded-session default for this session; it should go as far as it can,
   handing off cleanly wherever it stops.

**Routing:** the Next-session handoff (session log) updated to the decided
scope; current-state ▶ pointer updated (model: **Fable**, owner's choice).
**Executed 2026-06-11 — PR #702** (all four decisions implemented as decided;
numbers record: `docs/planning/gear-set-numbers-2026-06-11.md`; session log:
`.sessions/2026-06-11-gear-set-slice.md`).

### Q-0090 — Open-world federation round: ecosystem #2, currencies, cross-links, research scope

**Area:** Games / open-world architecture (V-13) + research direction (V-14)
**Type:** Structured choices (agent-initiated round, owner-requested questions)
**Priority:** High for the games lane (binds all future ecosystem design)
**Status:** **Answered** (2026-06-10) — **Routed** → vision doc V-13/V-14 (updated in place); roadmap session queue (V-14 research added, gateway status)

**The four picks (structured choices, same conversation):**

1. **Ecosystem #2 = let the research decide.** The V-14 competitive teardown
   runs first and proposes ecosystem #2 from evidence (candidates the round
   offered: farming/homestead · combat/dungeons · fishing-promoted). This
   **elevates V-14 to gateway status** for the open-world expansion.
2. **Currencies = local per-ecosystem, no exchange** (recommended option).
   Each ecosystem earns/spends its own currency internally; **main coins stay
   the one universal layer**; no conversion market — no arbitrage, local
   sinks, per-ecosystem identity preserved.
3. **Cross-links = medium, special tools only** (recommended option — and the
   owner's own words: "invest a little time in another section… for some
   tools"). A few advanced **optional/prestige-class** tools may require
   another ecosystem's basics; **no core capability may ever be gated
   cross-ecosystem** — this is the Q-0087 never-mandatory boundary applied
   to the federation.
4. **V-14 research scope = game & economy bots first** (Dank Memer, EPIC RPG,
   OwO, idle bots) — feeds the open-world design while its momentum is live;
   admin-suite and engagement teardowns remain later passes.

**Design consequence recorded:** decisions 2+3 are *posture for future
ecosystems* — current mining/coins are untouched until ecosystem #2 work
actually starts; the substrate extraction (tools/energy/game-XP as shared
identity) happens then, on the mining patterns proven by that point.

### Q-0093 — Session-end merge mechanics: why did a CI-green PR sit unmerged, and should sessions skip the draft step?

**Area:** Agent workflow / PR lifecycle (refines Q-0052 draft-first + Q-0084 self-merge)
**Type:** Process correction (owner-observed miss) + owner suggestion
**Priority:** High (every session's end-state depends on it)
**Status:** **Answered by diagnosis + rule installed** (2026-06-11) — **Routed** → journal Rules (binding default) · `.sessions/2026-06-11-ai-knowledge-screenshot-fixes.md`; the draft-vs-regular choice stays open for the owner if he still prefers regular PRs after reading the diagnosis.

**Owner (verbatim, 2026-06-11):** "Any reason why you never merged it, maybe
it's a better idea if a session just opens a regular PR instead of a draft,
because it seems like you don't get CI notifications about draft PRs"

**Diagnosis (PR #703, same day):** the draft status was NOT the cause. CI ran
on every push of the draft and went green at 10:01; the platform delivers
CI **failures**, comments, and reviews as session-waking events — **CI
success is never delivered for any PR, draft or regular**. The session's
backstop was a background *unauthenticated* `curl` poll of api.github.com,
which rate-limited into silent failure (`curl -sf` swallowed the 403s), so
the loop produced nothing and the session never woke to merge.

**Rule installed (journal → Rules):** a session PR whose only remaining gate
is CI is merged **in-turn** — poll the authenticated GitHub MCP
(`pull_request_read get_check_runs`, a few calls over the ~3-5 min suite)
and merge on green before ending the turn; never park the merge on a
background poll or on webhook hope. Draft-first (Q-0052) keeps its original
benefit (a real PR # for docs from the first push); it costs nothing once
the merge is in-turn. If the owner still prefers regular-from-the-start
PRs, that is a one-line Q-0052 amendment — flag it in any session.

### Q-0094 — AI conversation memory default: off, except an always-on last-3-messages floor

**Area:** AI natural-language / conversation memory / product default
**Type:** Owner directive (stated mid live-testing, first Q-0086 session)
**Priority:** Settled — records canon so it is never "cleaned up" away
**Status:** **Answered** (2026-06-11) — **already the implemented design**; pinned here as owner-confirmed canon. Routed → `docs/subsystems/ai.md` (current state), bug-book context for BUG-0006/0007.

**Owner (verbatim, 2026-06-11):** "AI memory should be off by default except
for the last 3 messages so it always feels natural in direct follow ups"

**Source state at the time:** `services/ai_conversation_service.py`
`MIN_FLOOR_TURNS = 3` — the memory *window* defaults to 0 (off), but the last
3 turns per channel are always retained and fed to the model
(`ai_memory_service.gather_recent_turns` honours the floor regardless of the
window). The owner's directive and the shipped design coincide exactly; no
change was needed. **Scope note:** the "unnatural follow-ups" he observed in
the same session were NOT memory — the routing/guard layer discarded the
context the model could already see (BUG-0006/BUG-0007, fixed same session).
Any future proposal to change the floor (size or existence) is an owner
decision against THIS entry.

### Q-0095 — Canonical AI model allocation: Haiku 4.5 for the two NL tasks; the guild-default-provider trap

**Area:** AI platform / model routing / cost (Q-0082-adjacent)
**Type:** Owner directive (config canon)
**Priority:** Settled
**Status:** **Answered** (2026-06-11, first Q-0086 live session) — routed → journal Runbook boot recipe · `docs/subsystems/ai.md`.

**Owner (2026-06-11):** "btd6 and nl general should both run on haiku4.5" —
"production has haiku routed for these 2 specific tasks".

**Canonical allocation:** `AITask.BTD6_ANSWER` and `AITask.GENERAL_NL_ANSWER`
→ `anthropic:claude-haiku-4-5-20251001` (env:
`AI_ROUTING_BTD6_ANSWER` / `AI_ROUTING_GENERAL_NL_ANSWER`); every other task
stays on the OpenAI defaults (`AI_DEFAULT_PROVIDER=openai`, gpt-4o-mini);
`AI_FALLBACK_PROVIDER=openai` gives the gateway a fault cascade. Sandbox
sessions boot the test bot with exactly this split (journal Runbook).

**The trap found live:** `ai_guild_policy.default_provider` (a panel write)
**silently outranks** the env task routing (`gateway._overlay_guild_policy`
precedence: guild row > env > defaults). The owner's panel walk set
`openai` on the test guild and the Haiku routing was bypassed until the row
was cleared. Keep guild `default_provider` EMPTY unless a guild-wide
override is genuinely intended; the AI-panel rework capture
(`docs/ideas/ai-panel-inplace-navigation-2026-06-11.md`) lists surfacing
this coupling as a requirement.

**Addendum — sandbox floor-testing posture (owner, same session):** "it would
be a good idea to also test with chat gpt keys in the sandbox, both to save
costs and to make it extra failsave, because if we can get chat gpt to give
correct answers we will be 100% fine when we switch to haiku." Sandbox live
testing therefore defaults to the **OpenAI floor model** (gpt-4o-mini —
cheaper AND a stricter test of the deterministic pipeline); the Haiku
prod-mirror boot is used for final verification passes. Evidence from this
session: after the BUG-0005…0008 routing/grounding fixes, gpt-4o-mini
produced the correct, subject-stable farm-income answers — the pipeline, not
the model, was the bottleneck.

### Q-0096 — Claude Code plugins: adopt the Context7 / Postgres-MCP shortlist, or stay plugin-free?

> **ANSWERED (partial) 2026-06-12 — adopt Context7 (trial).** Owner: "go ahead, it seems very
> useful and time-saving." Wired `@upstash/context7-mcp@3.2.0` as a pinned `.mcp.json` server
> (keyless to start), approved via `enabledMcpjsonServers`, tools pre-allowed. Operational home +
> key-setup + Q-0105 delete-if-unreliable note: [`../operations/mcp-servers.md`](../operations/mcp-servers.md).
> **Maintainer follow-up:** optionally add a free `CONTEXT7_API_KEY` to the environment for the
> higher rate limit (keyless ≈ 500 req/mo ceiling). Postgres-MCP / `pyright-lsp` remain open
> under this Q — revisit if wanted.

**Area:** Agent workflow / tooling / executable config (`.claude/settings.json`, `.mcp.json`)
**Type:** Owner decision (adoption gate — plugin enablement is ask-first executable config)
**Priority:** Low-medium (quality-of-life for agent sessions; nothing is blocked)
**Status:** ✅ **RESOLVED 2026-06-19 (owner, question panel) — stay as-is, Context7 only.** Postgres-MCP and `pyright-lsp` are **declined for now** (nothing is blocked; ad-hoc `psql` + CodeGraph cover the need; conservative supply-chain posture). Re-open this Q if a concrete need appears. *(Originally asked 2026-06-12, prompted by the owner's own question "are there any good plugins for claude that would be useful for us?")*

**Question:** The 2026-06 plugin-ecosystem survey
([`docs/ideas/claude-code-plugins-evaluation-2026-06-12.md`](../ideas/claude-code-plugins-evaluation-2026-06-12.md))
found most plugin categories duplicate or conflict with our bespoke
workflow (review skills, journal memory, PR process, CodeGraph). Three
candidates add a genuinely missing capability. Which, if any, should a
session wire in (pinned, provenance-headered, Q-0014 trial discipline)?

- **(a) Context7** — live version-pinned library docs (discord.py / asyncpg
  API truth instead of model memory). Recommended **yes, as a pinned
  `.mcp.json` server**, trialed a few sessions before trusted. Note: hosted
  endpoint wants a free API key; can also run locally via npx.
- **(b) Read-only Postgres MCP** (`crystaldba/postgres-mcp`,
  `--access-mode=restricted`) — schema-aware DB work in sandbox sessions.
  Optional; ad-hoc `psql` already covers most of this.
- **(c) `pyright-lsp`** (official marketplace) — LSP ground truth beside
  CodeGraph. Trial-only if curious; unknown overhead on 1,400 files.
- **(d) none** — stay plugin-free; current posture is the safest
  supply-chain stance and nothing is blocked today.

**Why agents need this:** plugin/MCP enablement edits `.claude/settings.json` /
`.mcp.json` — the one seam the working agreement marks ask-first, and the seam
2026 CVEs target. Silent adoption is off the table by design.

**Safe default until answered:** plugin-free status quo (CodeGraph remains the
only MCP server beyond the environment's GitHub MCP).

**Suggested destination after answer:** the evaluation doc's §Lifecycle (flip
state), `.mcp.json` + journal Runbook if anything is adopted, CLAUDE.md
CodeGraph-style pin note for any new server.

### Q-0097 — Who owns operational-health finding lifecycle transitions?

**Area:** Health / Diagnostics / persistent operational findings
**Type:** Owner/product decision exposed by production-readiness review
**Priority:** High before Health / Diagnostics is declared production-ready
**Status:** ✅ **ANSWERED 2026-06-12 (owner, question panel) — (a) operator-managed lifecycle.**

**Question:** Persistent findings support `open`, `resolved`, and `ignored` states, and
retention only rolls up/prunes `resolved`/`ignored` rows. Source currently provides only
record/list/count/retention paths: there is no service or operator path that changes a
finding out of `open`. Which lifecycle is intended?

- **(a) Operator-managed lifecycle (recommended):** add minimal resolve/ignore/reopen
  mutations through the existing sole writer, `services.health_findings_service`, and
  expose them from an explicitly privileged existing diagnostics surface.
- **(b) Automatic lifecycle:** define a deterministic rule for resolving a finding after
  it is absent from later bounded snapshots; ignored remains an explicit operator action.
- **(c) Open-only history:** remove or de-scope the unresolved resolved/ignored/retention
  claims and treat rows as permanent open recurrence counters.

**Why this needs owner intent:** automatic absence does not necessarily mean recovery,
while operator mutation adds a privileged control surface to a subsystem intentionally
kept read-only so far. Implementing either silently would choose product semantics.

**Decision (2026-06-12): (a) operator-managed lifecycle** — minimal resolve/ignore/reopen
mutations through the existing sole writer (`services.health_findings_service`), exposed
from an explicitly privileged existing diagnostics surface; audited like every other
mutation. An automatic absence-based resolve rule may layer on later as a separate ask.
*Answer scope: the lifecycle-transition owner only — retention mechanics and the P1-2
scheduling/drift items proceed under the hardening roadmap as planned.*
**Routed:** hardening roadmap P1-2 (now unblocked) · health readiness map · this entry is
provenance.

**Safe default until answered:** keep the existing sole-writer/store unchanged; do not
add a second writer or direct cog/view DB mutation. Treat finding lifecycle and effective
retention roll-up as **Not Done** for production readiness.

**Source review:**
[`docs/planning/production-readiness/health-diagnostics-production-readiness-map-2026-06-12.md`](../planning/production-readiness/health-diagnostics-production-readiness-map-2026-06-12.md)

### Q-0098 — Do delegated Setup admins have apply authority for settings/bindings/provisioning?

> **ANSWERED 2026-06-12 — (a) Delegates may apply.** Add a non-escalating delegated-setup
> capability route so the mutation pipelines authorize the same actor the Setup gate did
> (preserve execution-time re-checks). Unblocks roadmap **P0-3**.

**Area:** Settings / Bindings / Provisioning · Setup delegation
**Type:** Owner/product + authority decision exposed by production-readiness review
**Priority:** High before Settings / Bindings / Provisioning is declared production-ready

**Question:** The Setup Final-Review gate authorizes the owner **or a delegated setup admin**
to apply a staged draft, but the three mutation pipelines (settings/binding/provisioning)
enforce an administrator floor in `governance.capability.actor_holds_capability()` that does
**not** represent delegated-setup authority. A delegate can therefore stage and pass Final
Review, then fail the canonical write per operation. Which is intended?

- **(a) Delegates may apply (recommended if delegation is a real feature):** add a
  non-escalating delegated-setup capability route so the pipelines authorize the same actor
  the Setup gate did. Preserve execution-time re-checks.
- **(b) Delegates may stage only:** keep the admin floor; change Setup copy/gates so they
  stop promising apply authority a delegate doesn't have.

**Why this needs owner intent:** it's a product call about what "delegated setup" means, and
either path changes an authority surface. Implementing either silently picks the semantics.

**Safe default until answered:** leave both gates as-is; treat the delegated-apply path as
**Not Done** and surface the mismatch in operator UX rather than widening capability.

**Source review:**
[`docs/planning/production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md`](../planning/production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md)

### Q-0099 — What is the retention & data-minimization policy for cached YouTube data?

> **ANSWERED 2026-06-12 — (a) Bounded projection + scheduled purge.** Store only the bounded
> fields the runtime uses, wire purge through a managed task, verify deletion against Postgres.
> Unblocks roadmap **P0-2**.

**Area:** Media / YouTube (shared platform)
**Type:** Owner/product + privacy decision exposed by production-readiness review
**Priority:** High before Media / YouTube is declared production-ready (privacy-sensitive)

**Question:** The video cache stores `metadata_json` as the **full unsanitized** YouTube API
item (including full descriptions), and `purge_expired_video_cache()` has **no caller** — so
expired rows (transcripts + raw metadata) persist indefinitely. For a public bot, what is the
allowed policy?

- **(a) Bounded projection + scheduled purge (recommended):** store only the bounded fields
  the runtime actually uses, define a deletion/purge owner, and schedule physical expiry
  through a managed task; verify deletion against production Postgres.
- **(b) Raw payload with a defined TTL:** keep full payloads but justify it, document the
  retention window, and still wire the purge so expiry is physical, not just logical.

**Why this needs owner intent:** data-minimization and retention are privacy/product calls,
not implementation defaults — especially for stored third-party content.

**Safe default until answered:** treat retention as **Not Done**; do not expand YouTube
storage or surfaces; wiring the existing purge on the current schema is a safe interim fix.

**Source review:**
[`docs/planning/production-readiness/media-youtube-production-readiness-map-2026-06-12.md`](../planning/production-readiness/media-youtube-production-readiness-map-2026-06-12.md)

### Q-0100 — Who is the canonical owner for direct channel mutations (create/clone/overwrite/category)?

> **ANSWERED 2026-06-12 — (a) Converge under the existing seams.** Creation/category through
> `ResourceProvisioningPipeline` (keep its confirmation rule), clone/overwrite through
> `ChannelLifecycleService` with audit+events; then extend the channel invariant. Unblocks
> roadmap **P0-4**.

**Area:** Server management · channel lifecycle / resource provisioning
**Type:** Architecture/ownership decision exposed by production-readiness review
**Priority:** High before Server management is declared production-ready

**Question:** Channel **creation, clone, permission-overwrite, and category-lifecycle** paths
currently mutate Discord outside the one audited lifecycle/provisioning seam, so the same
operator action gets different audit, confirmation, and failure behavior by path. What is the
canonical owner for each?

- **(a) Converge under the existing seams (recommended):** route creation/category through
  `ResourceProvisioningPipeline` (preserving its confirmation rule) and clone/overwrite
  through `ChannelLifecycleService` with audit + events; then extend the channel invariant to
  pin `.set_permissions()`/`.clone()`/create.
- **(b) A new dedicated channel-mutation owner:** if those paths don't fit the existing seams,
  declare one canonical audited owner for them with the same confirmation/audit/event contract.

**Why this needs owner intent:** it's an architecture decision about confirmation semantics on
destructive guild mutations (e.g. should every clone/overwrite require confirmation like
provisioning does?) before code converges.

**Safe default until answered:** leave paths as-is; the channel invariant intentionally pins
only `.edit()`/`.delete()` until the owner is chosen — do not widen `ChannelLifecycleService`
unilaterally.

**Source review:**
[`docs/planning/production-readiness/server-management-production-readiness-map-2026-06-12.md`](../planning/production-readiness/server-management-production-readiness-map-2026-06-12.md)

### Q-0101 — Do the ~24 smaller subsystems need their own folio/context-pack, or is the cheat-sheet enough?

> **ANSWERED 2026-06-12 — (a) Cheat-sheet is enough.** Folios stay for the high-traffic /
> complex areas only; the gap is **intentional** and now documented in
> [`docs/subsystems/README.md`](../subsystems/README.md). No stub folios. Idea #4 resolved.

**Area:** Docs & agent system · orientation
**Type:** Workflow/orientation decision (doc-maintenance burden vs. uniformity)
**Priority:** Low — quality-of-life for agents working in the smaller cogs

**Question:** Seven areas have a [folio](../subsystems/README.md) (+ generated context pack);
the other ~24 cog subsystems (economy, moderation, xp, role, inventory, counting, …) have
only the `repo-navigation-map.md` cheat-sheet row + `ownership.md`. The review-map implies
"every slice has one entry page", which is currently uniform for 7 and ad-hoc for the rest.

- **(a) Accept the cheat-sheet as the entry for small cogs (recommended default):** keep
  folios for the high-traffic/complex areas only, and document that the gap is *intentional*
  (so it reads as a decision, not an omission). Lowest maintenance.
- **(b) Generate lightweight stub folios/context-packs per remaining subsystem:** uniform
  "one entry page per slice", at the cost of ~24 more docs to keep fresh.
- **(c) Hybrid:** add a folio only for a small cog once it crosses a complexity threshold
  (e.g. has a view package + a service + a DB module), cheat-sheet otherwise.

**Why this needs owner intent:** it's a maintenance-burden vs. uniformity trade-off on the
docs surface — generating 24 stubs that then rot would be worse than the current gap.

**Safe default until answered:** leave as-is; the cheat-sheet + ownership are the entry
point for non-folio cogs.

**Source review:** [`docs/ideas/repo-manageability-2026-06-12.md`](../ideas/repo-manageability-2026-06-12.md) #4.

### Q-0102 — Mandatory session ender: every session reviews the previous session + surfaces one system improvement

> **DIRECTED 2026-06-12 (owner directive, voice).** Not a question — a standing rule the
> maintainer asked to be **required**. Recorded here for provenance; the binding form lives
> in `.claude/CLAUDE.md` § "Session & plan workflow".

**Area:** Agent system · workflow / self-improvement
**Type:** Standing workflow rule (process)
**Priority:** Standing — every session

**Directive:** Every session, at close, adds a short **⟲ Previous-session review** note to
its `.sessions/` log: one genuine remark on the *previous* session (what it did well / what
it missed) **plus one concrete improvement to the system/workflow itself**. Every session
**assumes the system is still in development** and *initiates* improvement thinking on its
own rather than waiting to be asked.

**Guardrails (owner-stated):** keep it short and useful; **if there is genuinely nothing to
improve, say so and why — do not hallucinate filler** (same bar as the Q-0089 idea rule).

**Why:** the maintainer observed this was "sort of a rule already" but inconsistently done
(improving lately). Making it a required session-ender turns the session chain into a
**self-auditing loop** — each session reviews its predecessor. It is the internal mirror of
the Hermes-as-independent-reviewer seam
([`docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`](../ideas/autonomous-improvement-loop-vision-2026-06-12.md)).

**Home:** `.claude/CLAUDE.md` (binding) · this entry is the provenance record.

### Q-0103 — Drop draft-first PRs (open ready); every session PR must reach a terminal state

> **DIRECTED 2026-06-12 (owner, voice).** Refines Q-0052. The maintainer observed sessions
> "creating draft PRs and then forgetting about them" and asked whether the draft step gives
> any benefit. Agreed assessment: in our self-merge flow it does not.

**Area:** Agent system · workflow / PR lifecycle
**Type:** Workflow decision (refines Q-0052)
**Priority:** Standing — every session

**Decision:**
1. **Open the session PR READY, not draft.** Q-0052's real benefit was opening *early* (for
   the PR number, so docs can reference it without a rotting placeholder). The *draft* state
   added nothing here — nothing auto-merges or auto-requests review — and the "mark ready"
   step was being forgotten, producing abandoned drafts. Drop it.
2. **Every session drives its PR to a terminal state — merged or closed — before ending.**
   Merge when the work is good (Q-0084 envelope: reconcile main, CI green on final head,
   merge-commit, own PR only); otherwise close with a one-line reason. **Never leave a
   session PR open/abandoned.** This is the actual fix for the forgotten-PR problem and is
   load-bearing for full autonomy.

**Enforcement:** `scripts/check_session_log.py` + the Stop-hook advisory remind on an
incomplete close; the `/session-close` skill performs the terminal-state step. (Hooks can't
call GitHub MCP, so the merge/close itself is agent/skill-driven, not hook-driven.)

**Home:** `.claude/CLAUDE.md` § "Session & plan workflow" (binding) · this entry is provenance.

### Q-0104 — Mandatory session ender: close with a documentation/drift audit

> **DIRECTED 2026-06-12 (owner, voice).** The owner's closing question — "is anything
> important from this session not yet documented?" — surfaced multiple drifted `current-state.md`
> ledger entries (#730/#733 missing, untested-surface mislabeled #730→#731, #724–#728 absent).
> He asked that this question be put to *every* agent ending a session.

**Area:** Agent system · workflow / documentation integrity
**Type:** Standing workflow rule (process)
**Priority:** Standing — every session

**Directive:** Every session, before ending, performs a documentation audit: ask *"is anything
important from this session not yet in its durable home?"* Concretely — run
`check_current_state_ledger.py --strict` (merged PRs in the ledger), confirm new owner
decisions are in the router and new docs are reachable (`check_docs --strict`), and sweep for
anything captured only in chat. The automated half runs in `/session-close`; the judgment half
(the "only in chat?" sweep) is the agent's.

**Home:** `.claude/CLAUDE.md` § "Session & plan workflow" (binding) · `scripts/check_current_state_ledger.py`
is the automated teeth · this entry is provenance.

### Q-0105 — Adopt tooling freely, with a "delete if unreliable" kill-switch in its header

> **→ Program law: [PL-008]** — this block's durable conclusion is canonicalized as program law **PL-008** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

> **DIRECTED 2026-06-12 (owner, voice).** Extends Q-0014. The owner: *"implement whatever you
> think would work, but make sure another agent knows it should be deleted if it's been proven
> unreliable over multiple sessions."*

**Area:** Agent system · tooling / autonomy
**Type:** Autonomy grant + provenance discipline (refines Q-0014)
**Priority:** Standing

**Decision:** Agents may implement/adopt whatever tooling or check they judge will help —
custom or third-party — **without asking first**. The cost of that autonomy is a **provenance +
reliability header** on every such tool: *why* + *date* + *"unverified: confirm against ground
truth a few times before trusting"* **+ an explicit "delete this if it proves unreliable over
multiple sessions"** instruction. The kill-switch matters because a convenience guard that
misfires should be *removed* by a later agent, not silently worked around (which would leave a
lying check in place). Load-bearing checks graduate out of "unverified" once proven across
sessions.

**Home:** `.claude/CLAUDE.md` § "Session & plan workflow" (the Q-0014 tooling bullet) · this
entry is provenance.

### Q-0106 — Agents never self-edit CLAUDE.md on their own initiative; propose for live review

> **DIRECTED 2026-06-12 (owner, voice).** For full autonomous improvement, agents must not
> edit `.claude/CLAUDE.md` (or binding rules) when *they* have an idea — they document the
> proposal for live review. The owner's framing: the instructions "may be binding for their
> session, but they are not locked/pinned — they are still in development just like the rest
> of the system."

**Area:** Agent system · governance / self-modification boundary
**Type:** Standing workflow rule (process + safety)
**Priority:** Standing — every session, load-bearing for autonomy

**Decision:**
- **`CLAUDE.md` is binding *for* a session but not *pinned*.** It is in development like the
  rest of the system. Agents follow it this session and may *evolve* it — but only by
  **proposing**, not self-applying.
- **Agent-originated rule changes → a router Q-block (DISCUSS lane), never a direct edit.**
  The change lands in `CLAUDE.md` only after the owner decides.
- **Exception — maintainer-directed in-session changes apply directly.** When the owner
  directs a rule change live (as with Q-0102–Q-0106), the owner *is* the live reviewer, so
  the agent applies it and records the provenance Q-number.
- **In a fully autonomous session (no human live), `CLAUDE.md` is read-only to the agent** —
  it only ever writes proposals. This is *why* the `Edit(.claude/CLAUDE.md)` permission prompt
  is kept (it is the live-review gate when a human is present); see
  `docs/operations/claude-code-hooks-and-plugins.md` § Permissions posture.

**Why:** self-modification of one's own binding instructions is the highest-risk autonomous
action — the prime prompt-injection / value-drift target. Routing all rule changes through
owner review keeps the agent's "constitution" under human control while still letting the
system evolve. This is the governance counterpart to the Q-0102/Q-0104 self-audit loop.

**Home:** `.claude/CLAUDE.md` Working agreement (binding) · this entry is provenance.

### Q-0107 — Reconciliation + planning pass at every 10th PR (docs-only)

> **DIRECTED 2026-06-12 (owner, voice).** "After every 10 PRs there should be a docs-only
> cleanup and plan reconciliation that reviews the state of the repo and refocuses our
> attention." Refined: "every 10, 20, 30 etc should be docs-only reviewing and planning," and
> "every planning session should focus on what the next 9 PRs can realistically achieve —
> modular but not too segmented; each PR should ship a reasonable change unless it really is
> only a small required change."

> **AMENDED 2026-06-12 (owner, in-session, autonomous-routines wiring):** cadence raised
> **10 → 20**. Rationale: "some sessions create a lot of small PRs, so [the threshold]
> shouldn't be too low" — every 10 fired too often. The pass is also now **fired automatically**
> by a GitHub Action (`.github/workflows/reconciliation-trigger.yml`) that opens a
> `reconcile`-labeled issue at the boundary, triggering the **superbot docs reconciliation**
> routine (`docs/operations/autonomous-routines.md`). Agents/maintainer may also open a
> `reconcile` issue by hand to fire the pass when they spot docs drift off-cycle.

**Area:** Agent system · workflow / planning cadence
**Type:** Standing workflow rule (process)
**Priority:** Standing — every 20th PR

**Directive:**
- PR numbers crossing a **multiple of 20** (#20, #40, #60, …) are a **docs-only review +
  planning** pass — no runtime / `disbot/` code.
- **Reconcile:** review the ledger, active lanes, open Q-blocks, idea backlog, roadmap; prune
  stale docs; restate current priorities.
- **Plan the next ~9 PRs:** what is realistically achievable in the upcoming band of PRs,
  **modular but not over-segmented** — each planned PR ships a *reasonable, meaningful* change,
  not a trivial fragment (small PRs only when the change genuinely is small/required).
- **Cadence guard:** `scripts/check_reconciliation_due.py` (`STEP = 20`) tracks the
  `Last reconciliation pass:** PR #N` marker in `current-state.md` and flags when a pass is due;
  reset the marker after a pass. Surfaced by `/session-close` and the trigger Action.

**Home:** `.claude/CLAUDE.md` § "Session & plan workflow" (binding) · `current-state.md` holds
the marker · `docs/operations/autonomous-routines.md` (the routine + Action) · this entry is provenance.


### Q-0108 — Automod rules engine + image moderation: wanted? Which scope to start?

> **ANSWERED 2026-06-12 (owner, question panel).**

**Area:** Moderation platform · automod + image moderation
**Type:** Product direction + provider choice

**Decision:**
- **Automod v1 rule types:** all four — spam burst · discord.gg/ invite links · mass
  @mentions · excessive caps. Expand from the minimal set to the full first-tier suite.
- **Image moderation:** yes, **OpenAI omni-moderation-latest only** (free, uses the
  existing key, covers sexual/violence/harassment/hate categories). No paid provider
  (API4AI or Hive) at this stage.

**Home:** `docs/ideas/server-safety-and-automod-2026-06-12.md` — routing updated to
reflect these decisions. Planning can begin for `services/automod_service.py` +
`services/image_moderation_service.py`.

---

### Q-0109 — Server logging service: event scope and channel layout

> **ANSWERED 2026-06-12 (owner, question panel).**

**Area:** Moderation platform · server event logging
**Type:** Product direction + UX design

**Decision:**
- **Event scope (v1):** message edits and deletions · member join and leave · role
  grants/revocations (non-bot actions). Voice channel activity **not included** in v1.
- **Channel layout:** **owner-configurable** — the setup panel lets server operators
  choose a single combined log channel *or* assign separate channels per event category.
  Both layouts are supported; neither is forced.
- **Privacy disclosure:** deleted-message logging must be clearly surfaced in the setup
  wizard (staff can see content that was deleted).

**Home:** `docs/ideas/server-safety-and-automod-2026-06-12.md` §2 — routing updated.
Planning can begin for `services/server_logging_service.py`.

---

### Q-0110 — Welcome service: PIL image cards on day one, or start with embeds?

> **ANSWERED 2026-06-12 (owner, question panel).**

**Area:** Community platform · welcome service
**Type:** Product direction + implementation scope

**Decision:**
- **Phase 1:** embed-only welcome message (fast to ship, zero PIL complexity).
- **Phase 2 follow-up:** PIL avatar-composited image cards added once the service is stable.
- Join DM and goodbye message scope remain open — not asked; agent should propose
  defaults when planning (join DM opt-in, goodbye message enabled by default).

**Home:** `docs/ideas/community-platform-features-2026-06-12.md` §1 — routing updated.
Planning can begin with an embed-first scope; PIL card slice planned as a follow-up PR.

---

### Q-0111 — Security service: which tiers are wanted, given privacy tradeoffs?

> **ANSWERED 2026-06-12 (owner, question panel).**

**Area:** Server security · account screening
**Type:** Product direction + privacy/legal boundary

**Decision:**
- **Tier 1 (raid detection): APPROVED.** Monitor join rate, auto-slowmode + staff alert.
- **Tier 2 (account-age filter): APPROVED.** Reject/quarantine accounts younger than N
  days on join; configurable threshold.
- **Tier 3 (alt detection): NOT selected.** GDPR/privacy implications; declined.
- **Tier 4 (VPN/proxy blocking): NOT selected.** GDPR/privacy implications; declined.

**Home:** `docs/ideas/server-safety-and-automod-2026-06-12.md` §4 — routing updated.
Planning can begin for `services/security_service.py` (tiers 1 + 2 only).

---

### Q-0112 — Event scheduler: simple RSVP tier standalone, or needs NL parsing?

> **ANSWERED 2026-06-12 (owner, question panel).**

**Area:** Community platform · event scheduling
**Type:** Product direction + AI cost boundary

**Decision:**
- **Natural-language time parsing wanted from day one** ("next Friday 8pm" → parsed
  datetime via LLM call). This is the primary UX, not just a follow-up add-on.
- Adds one LLM call per event creation → must be metered under the Q-0082 spend ceiling.
- Availability polling scope not explicitly decided; agent should propose it as a
  day-one feature in the planning doc (fits naturally alongside NL events).
- Agent must check for existing scheduler infrastructure before designing reminder timers.

**Home:** `docs/ideas/community-platform-features-2026-06-12.md` §3 — routing updated.
Planning required before implementation (NL parsing + AI cost need explicit design).

---

### Q-0113 — Autonomous loop: merge gate for routine-driven PRs

> **ANSWERED 2026-06-12 (owner, question panel).** Asked while wiring the autonomous-loop
> seams (Hermes-reviewer + dispatch bridge + phase gate).

**Area:** Agent ecosystem / workflow · autonomy boundary
**Type:** Owner decision (autonomy/safety)

**Question:** for unattended/routine-driven PRs (the dispatch-bridge loop), where should the
merge gate sit — open-only + one-tap confirm, auto-merge docs/test-covered only, or full
self-merge on green CI?

**Decision: full self-merge on green CI** — routines self-merge any green-CI PR, the same grant
interactive sessions already have (Q-0084), now extended to unattended runs. Bounded by: CI
**required-green on the final head**, **`claude/`-only** branch pushes, and the Q-0114 feature
carve-out (agent-originated *features* never self-merge — they wait for approve/deny). Merge ≠
deploy; production restart stays the maintainer's (auto-deploy on merge is already true).

**Home:** `docs/operations/hermes-dispatch-bridge.md` (the routine's saved gate prompt enforces
it) · `docs/owner/ai-project-workflow.md` §12 · this entry is provenance.

---

### Q-0114 — Autonomous loop: where the human approve/deny gate applies

> **ANSWERED 2026-06-12 (owner, question panel).** Companion to Q-0113.

**Area:** Agent ecosystem / workflow · autonomy boundary
**Type:** Owner decision (autonomy/safety)

**Question:** what must reach the maintainer before it ships — every agent-originated feature,
everything above docs/bug-fix, or only above a risk threshold?

**Decision: agent-originated *features* only.** Features the agents invent themselves go through
the maintainer's approve/deny (Hermes explains them in plain language — the `superbot-review`
`## Maintainer summary` block). Bug fixes, UX polish, docs, and correctness work **flow freely**
under the Q-0113 merge gate. The ordering ("bugs first … only then features", vision §2) is
enforced by `scripts/check_phase_gate.py`: a feature may only be *originated* in **invent-phase**
(zero OPEN bugs, zero `Not Done` readiness rows) — otherwise it is captured as an idea, not built.

> **Clarification (2026-06-15, owner-stated in-session; recorded here for discoverability).**
> The gate is scoped to **agent-self-originated** features — ones an agent invents mid-session.
> A **dispatched** work order (one fired at a routine via the `/fire` endpoint, even when tagged
> `CLASS: feature`) is **owner-directed** and therefore **flows freely like a bug fix** — the
> phase gate does *not* gate it. *(Provenance: the owner corrected this exact scenario when a
> dispatched mining feature hit a FIX phase; the routine then correctly built mining Slice D
> (#891) and Slice A / Vault v2 (#897). Background + the still-open "gate at the dispatcher"
> mechanism idea: `docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md`.)* So an agent
> resolving a `feature` work order splits on **origin**: dispatched ⇒ build (owner-directed);
> self-invented ⇒ run `check_phase_gate.py --require-invent`, and in fix-phase capture-and-stop.

**Home:** `docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md` (the loop this gates) ·
`scripts/check_phase_gate.py` (the phase mechanism) · `docs/operations/hermes-dispatch-bridge.md`
· `docs/owner/ai-project-workflow.md` §12 · this entry is provenance.

---

### Q-0115 — Continuation dispatch: one seam (the Routine bridge) or two (+ Stage 0's GH Action)?

> **ANSWERED 2026-06-12 (owner, question panel).** Raised by the Q-0107 reconciliation pass
> the day #742 wired the Hermes → Claude Code Routine dispatch bridge.

**Area:** Agent ecosystem / workflow · session continuation
**Type:** Owner direction decision (de-duplicating two designed dispatch mechanisms)

**Question:** Stage 0 (workflow §10 — a `workflow_dispatch` GitHub Action that boots a
fresh bounded session from the standing handoff; owner-side API-key secret) overlaps the
#742 dispatch bridge (Hermes fires a Claude Code **Routine** `/fire` endpoint). Keep both,
fold one in, or decide after calibration?

**Decision: fold Stage 0 into the Routine seam** *(the recommended option)*. The Claude
Code Routine becomes **the one dispatch mechanism** — Hermes-fired, one-click, and (later)
scheduled continuation runs all use it. Stage 0's separate GitHub-Action dispatcher is
**dropped, not built**; the **bounded-session protocol (workflow §10) activates once the
Routine is wired + calibrated** (the Q-0105 calibration steps in the bridge runbook) instead
of "when Stage 0 lands". One mechanism to trust, audit, and calibrate.
*Answer scope: the dispatch mechanism only — the bounded-session protocol's content, the
Q-0113/Q-0114 gates, and Stage 1+ staging are unchanged; revisit only if the Routine proves
insufficient (e.g. a Hermes/VPS outage making a GitHub-side fallback worth its upkeep).*

**Routed:** `ai-project-workflow.md` §10 (Stage 0 superseded note) · roadmap 🤝 workflow
lane · the reconciliation-pass queue (Stage 0 entry re-pointed) ·
`ideas/hermes-claude-dispatch-bridge-2026-06-12.md` · this entry is provenance.

### Q-0116 — UX Lab (interface gallery cog): scheduling + audience

> **ANSWERED 2026-06-12 (owner, in-session, ~35 min after the design merged):**
> *"you can start building it, let me know if you need anything from me."*
> **Scheduling = immediate** — built the same session as an owner-steered slice
> (PRs **#758 → #760 → #762**, merged 2026-06-12; the decade queue otherwise
> unchanged). **Audience = the recommended option applied**: admin-gated
> (`has_permissions(administrator=True)` + author-locked panels,
> `visibility_tier=administrator`). *Answer scope: the owner's message approved
> building; the audience choice is the standing recommendation acted on per the
> act-vs-ask envelope — say the word to narrow it to owner-only. The non-decision
> stands: CV2 adoption for real panels remains a future ADR.*

**Area:** Building / interface · new subsystem `ux_lab`
**Type:** Scheduling + product-audience decision (the design itself is pinned)

**Context:** The owner commissioned "the most versatile and inclusive UX testing cog" —
a zero-write, admin-gated gallery of every Discord interaction/layout pattern (buttons /
selects / modals / embeds / Components V2 / PIL cards), a platform-limit probe bench,
and clickable mockups of the approved Q-0108–Q-0112 safety/community features. Full
design: [`../planning/ux-lab-interface-gallery-plan-2026-06-12.md`](../planning/ux-lab-interface-gallery-plan-2026-06-12.md)
(3 PRs: A core wings · B Components-V2 + PIL · C mock studio + pattern-library export).

**Question 1 — scheduling:** the decade queue (reconciliation pass §4) is full and
allows owner-steered swaps. Where do UX Lab PRs A–C sit?
*Recommended:* PR A as a near-term steered slice (it is additive/zero-risk and
immediately useful), and PR C **before or with** the safety-lane family plan (decade
slot 8) so the Q-0108–Q-0112 UX decisions are reviewed on rendered, clickable panels
instead of prose. Alternative: after the current decade completes.

**Question 2 — audience:** admin-gated (*recommended* — staff can browse styles too;
every callback re-checks authority) vs owner-only. Hidden from Help either way
(workbench, not a member feature).

**Non-decision pinned in the plan:** the lab does NOT authorize migrating real panels
to Components V2 — that stays a future ADR taken on the lab's evidence.

**Routed:** roadmap 🖥️ lane (SHIPPED bullet) · the plan's banner (`historical`, PR
numbers) · `ideas/ux-lab-interface-gallery-2026-06-12.md` (state: implemented) · the
durable export `docs/ux/pattern-library.md` · this entry is provenance.


### Q-0117 — Hermes as the independent-reviewer merge gate for big executor steps

> **DIRECTED 2026-06-12 (owner, in-session, executor wiring).** When the nightly executor
> advances a *substantial* plan step: "if possible we should have hermes review the work first,
> and then it should send the trigger to merge, if that is possible, if that's not possible then
> just merge."

**Area:** Agent ecosystem / workflow · autonomy boundary · the Hermes-reviewer keystone
**Type:** Owner decision (autonomy/safety — expands Hermes' role)

**Decision:** for a **substantial** executor step (feature-sized plan work, multi-file refactor,
migration — anything wanting a second pair of eyes), the executor opens a PR labeled
`needs-hermes-review` and does **not** self-merge. **Hermes** — a *different model* — reviews the
diff (`superbot-review-merge` skill) and **merges it if sound on green CI**, else requests
changes. This is the **independent-reviewer seam** (autonomous-loop vision §3): a non-Claude mind
between Claude's big steps and `main`, breaking the author-reviews-self monoculture. Small
fixes/docs keep self-merging on green (Q-0113); only big steps carry the label.

- **It expands Hermes' read-only model by exactly one write:** `gh pr merge` (+ review
  comments/labels) on a PR it just reviewed. Hermes still never edits code, pushes, or touches
  prod/Railway/Neon. Recorded in `hermes-operating-prompt.md`.
- **Fallback (owner-stated):** if Hermes review is not available, the step's green PR may
  self-merge — "if that's not possible then just merge."
- **Calibration (Q-0105, vision open-question 1):** Hermes' review earns the *merge* trigger only
  once proven to catch real issues. Until then it runs in **ADVISORY** mode (review + escalate to
  the maintainer for the merge); graduate to auto-merge after it reliably catches planted issues.

**Home:** `docs/operations/autonomous-routines.md` (the executor + the three labels) ·
`docs/operations/hermes-skills/review-merge.md` (the skill) · `hermes-operating-prompt.md`
(the read-only carve-out) · this entry is provenance.

### Q-0118 — Autonomous executor stalled on a `git push -u origin main` permission prompt

> **DIRECTED 2026-06-13 (owner, in-session).** A nightly-executor routine run (no human present)
> stopped at an interactive "Allow Claude to run `git push -u origin main`?" prompt while pushing a
> ledger update. Owner: "this should not ask for permissions, especially not on an autonomous run …
> it should just work exactly like in a normal session."

**Area:** Executable config (`.claude/settings.json` permissions) · autonomy boundary
**Type:** Owner decision (in-session directed edit to executable config — provenance per Q-0106)

**Root cause:** `permissions.ask` listed `Bash(git push origin main*)` and `Bash(git push -u origin
main*)`. In Claude Code, `ask` outranks `allow`, so those direct-to-main pushes overrode the broad
`Bash(git push*)` allow and forced a prompt. In an autonomous routine (no human to click *Allow*),
that hangs the run. The `ask` guard was meant to catch *accidental* direct-to-main pushes in
interactive sessions, but the executor's normal session-close flow **is** a direct ledger push to
`main`, so the guard was pure friction there.

**Decision:** removed the two plain direct-to-main entries from `ask`; they now fall through to the
existing `Bash(git push*)` allow → no prompt. **Kept gated** the genuinely destructive ops a *normal*
session also gates: `git push --force*`, `git push -f*`, `git reset --hard*`, `git clean*`. Net: a
plain push to main "just works exactly like a normal session," force-pushes/history-rewrites still
prompt.

**Home:** `.claude/settings.json` (`permissions.ask`) is the change; this entry is provenance.

### Q-0119 — Where do the governance role-pointer bindings live? (P0-3 family 3)

> **ANSWERED 2026-06-13 (owner, structured-choices round) → option (a), the reserved-schema
> path.** Raised 2026-06-13 during the P0-3 convergence session (#794); decided same day in a
> follow-up `AskUserQuestion` round. **Verbatim choice: "Give authority its own home."** Give
> server-wide authority settings their own reserved-namespace `governance` schema home — *not*
> re-home under `moderation` (b), *not* a permanent legacy exception (c).
>
> **Answer scope:** unblocks pointer-family 3 (the governance trusted/moderator role pointers)
> for a future P0-3 arc PR. **No behavior change today** and no code shipped this round — reads
> keep working via the legacy scalar + the binding ladder; recorded for the next session to
> execute (teach the identity-contract validator to expect a reserved-namespace `governance`
> schema, declare the two role bindings there, graduate the keys `DEFERRED_KEYS` → `MIGRATED_KEYS`,
> and retire the scalars with `pointer_retired=True` like families 1+2).

**Area:** Settings/bindings lane integrity · governance authority namespace
**Type:** Architecture decision (blocks pointer-family 3 convergence)

**Context:** `config_arbitration.get_{trusted,moderator}_tier_role` already read the
moderator/trusted role pointers through `governance.{trusted,moderator}_role` bindings, and
the binding-backfill targets them — but **`governance` is a *reserved* capability namespace**
(`utils.subsystem_registry._RESERVED_CAPABILITY_PREFIXES`), deliberately **not** a feature
subsystem, so those bindings have **no clean `SubsystemSchema` home**. The backfill was
therefore permanently `BLOCKED_NO_SCHEMA` for these keys (the settings readiness map's High
finding). This session **reframed** the backfill (the two governance role keys moved to
`DEFERRED_KEYS`), which unblocks the broken machinery; the *home* decision is this Q.

**Options (full trade-offs in the plan §5):**
- **(a) Reserved-schema path (recommended)** — let `SubsystemSchema` register a
  reserved-namespace `governance` schema that the identity-contract validator *expects* (a
  small allowlist of reserved schema subsystems), so no `schema_subsystem_unknown` finding.
  Keeps governance authority in the governance namespace; generalizes to future reserved
  bindings; costs one validator allowlist.
- **(b) Re-home under `moderation`** — declare `moderation.{trusted,moderator}_role` bindings
  and repoint arbitration + backfill from `governance.*` to `moderation.*`. No validator
  change, but conflates cross-cutting authority tiers with the moderation feature and touches
  the live governance read path.
- **(c) Permanent legacy exception** — accept the two role pointers as documented
  governance-tier scalars, exempt from the lane rule. Cheapest; abandons lane uniformity.

**Home:** `docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md` §5 (full
analysis + the family-3 gate); this entry is the router pointer. **Decided → option (a);**
execute in a future P0-3 arc PR (family 3).

### Q-0120 — Promote the earned candidate rules from `.session-journal.md` into `.claude/CLAUDE.md`?

> **→ Program law: [PL-006]** — this block's durable conclusion is canonicalized as program law **PL-006** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

> **DECIDED 2026-06-16 (owner, in-session): promote all three.** Applied directly under the Q-0106
> in-session exception. Mapping: **(a)** open-PR / merged-since check was already in CLAUDE.md
> § Session & plan workflow (the "claim work before starting" bullet) — no change needed; **(b)**
> generalized the "session prompts are guidance" bullet to **all cross-agent output** (Codex/Gemini/
> ChatGPT reviews = input to verify against source, not orders); **(c)** added as CI-parity **rule 6**
> ("a green check that contradicts visible evidence is a bug in the *check*"). Struck from the journal
> candidate list. Original proposal + context below.

**Area:** Agent workflow / binding rules (`.claude/CLAUDE.md`)
**Type:** Owner decision (rule promotion — the journal's ★ "earned across multiple sessions" set)

**Context:** `.session-journal.md` § "Rules / Conventions (candidate — not yet promoted)" has
accumulated ★-marked rules that are *earned across multiple sessions* but were never proposed for
promotion (the Q-0106 step was skipped — a forgotten lifecycle step this pass found). Three are
broadly-applicable process rules not yet in CLAUDE.md and worth promoting:

- **(a) Open-PR / merged-since check before starting a slice** — before any implementation slice,
  check live GitHub for an open PR on the same item **and** scan what merged to `main` since your
  orientation docs. (Proven: the #677/#678 duplicate-plan collision; #701 merged minutes before a
  same-topic session. This very pass found main moved #775→#778 mid-planning.)
- **(b) Treat cross-agent output (Codex/ChatGPT/Gemini reports) as input to verify, not orders** —
  verify each "rewrite X" against shipped source before acting. (This pass: a ChatGPT revision was
  sound at the conclusion level but wrong on 4 specifics — e.g. "create `claude_stop_check.py`" when
  it already exists; verifying caught them.)
- **(c) A green audit check that contradicts visible evidence is a bug in the CHECK** — verify the
  tool against ground truth, not just *with* it. (The #763 false-green: both ledger/cadence checkers
  matched `Merge pull request #N` but not `Merge PR #N:`, reporting green while 5 PRs were missing.)

The remaining journal candidates ((d) booting the test bot is always safe — an environment fact
better kept in the Runbook; (e) Discord caps 25/1024/5/100 — already in `discord-platform-limits.md`;
(f) guard at the mutation seam; (g) cog 800-LOC ceiling — already enforced by a test) are left as
journal candidates unless the owner wants any of them promoted too.

**Recommendation:** promote (a)+(b)+(c) into the CLAUDE.md Working agreement / CI-parity sections;
keep the rest as journal candidates. **Owner picks per-item (approve / adjust / reject).**

**Home:** on approval, the rules land in `.claude/CLAUDE.md` (the agent applies the owner-approved
wording in a follow-up, recording this Q as provenance) and are struck from the journal's candidate list.

### Q-0121 — Give Hermes a second sanctioned write (`gh issue create`) for the bug-triage flow?

> **DECIDED 2026-06-16 (owner, in-session): YES.** Hermes may call `gh issue create` **scoped to
> `bug`/`reconcile`/`continue` labels only** (its second sanctioned write, after `gh pr merge`,
> Q-0117). This un-gates the [`hermes-bug-triage-flow`](../ideas/hermes-bug-triage-flow-2026-06-13.md)
> build: route `/bugreport` through Hermes (triage → curated `bug` issue) instead of firing an
> unscreened fix-and-self-merge to prod. **Build in a control-plane session** per the idea's build
> order; same Q-0105 calibration discipline as Q-0117 (trust the curation after it proves out).
> Original question + context below.

**Area:** Agent control plane (Hermes) · the read-only-model write boundary
**Type:** Owner decision (expands Hermes' sanctioned writes by one)

**Context:** today `/bugreport` (HermesCog, #757) POSTs **directly** to the Routine `/fire` endpoint →
the routine reproduces, fixes, and **self-merges to `main`** on green CI. So every report = one routine
run + one auto-merge to prod, **unscreened** — cap-hungry and the pattern the owner wants replaced. The
[bug-triage design](../ideas/hermes-bug-triage-flow-2026-06-13.md) routes `/bugreport` *through Hermes*
(spam/genuine triage → reproduce/reword/fetch logs → save a curated `bug` issue) → the nightly executor
batch-fixes. That requires Hermes to **file the curated issue**, i.e. a second sanctioned write
(`gh issue create`) added to its read-only model — today it has exactly one (`gh pr merge` in
`review-merge`, Q-0117).

**Question:** May Hermes call `gh issue create` (scoped to `bug`/`reconcile`/`continue` labels only)?
Same Q-0105 calibration discipline as Q-0117 — trust the curation after it proves out.

**Interim safety (independent of this decision):** a one-line `hermes_cog.py` change can make bug-fix
dispatches **open a PR and hold** (not self-merge to prod) until reviewed — runtime code, so deferred
from this docs/tooling session, but available the moment `/bugreport` sees real use.

**Home:** on decision, record here; build per the idea doc's build order in a control-plane session.

### Q-0122 — Stop-hook end-of-session advisory (PR-lifecycle + grooming reminders)

> **DIRECTED 2026-06-13 (owner, in-session).** The owner selected the "enforcement hooks" scope of the
> 2026-06-13 workflow-hardening pass — the in-session direction Q-0106 requires for an executable-config
> change (agents don't self-edit hooks on their own initiative). This entry is provenance; the change is
> **non-blocking** (advisory only).

**Area:** Executable config (`scripts/claude_stop_check.py`, the wired Stop hook) · session-ender enforcement
**Type:** Owner-directed in-session edit to executable config (provenance per Q-0106)

**Problem:** several mandatory session-enders relied purely on the agent remembering — **Q-0052** (open
the PR early), **Q-0103/Q-0084** (the PR must reach a terminal state), **Q-0015** (grooming). Nothing
flagged them. The existing Stop-hook session-log advisory only fired when the `.sessions/` log was
*incomplete*, so a session that wrote a complete log but **forgot to merge its PR** got no nudge — the
exact Q-0103 abandoned-open-PR failure.

**Change:** broadened `_session_log_advisory` → `_end_of_session_advisory`, which — when HEAD is ahead
of `origin/main` — **always** prints a terse, **non-blocking** reminder of the PR-lifecycle + grooming +
session-log obligations. It stays advisory because the Stop hook runs locally with **no GitHub access**:
it cannot verify PR state, only remind. No `.claude/settings.json` change (the hook is already wired).

**Calibration (Q-0105):** advisory-first; consider a harder gate only if the reminder proves it needs
teeth across sessions. Relax/delete if it proves noisy.

**Home:** `scripts/claude_stop_check.py` is the change; this entry is provenance.

### Q-0123 — Merge mechanics move off the Claude session (GitHub-native auto-merge)

> **DIRECTED 2026-06-13 (owner, in-session).** The owner directed live that merging be removed
> from Claude's side ("completely remove merging from claude's side") and chose the **"Native
> auto-merge + enabler"** path plus a **behavior rule (router proposal)**. This is the in-session
> direction Q-0106 requires to edit `.claude/CLAUDE.md` directly; this entry is the provenance.
> **Supersedes the Q-0084 manual self-merge grant** (its envelope is struck from CLAUDE.md);
> **preserves Q-0103** — a session PR must still reach a terminal state, now satisfied
> automatically on green (or by an explicit close).

**Area:** Session/PR workflow · merge mechanics · agent context budget
**Type:** Owner-directed in-session change (provenance per Q-0106) + a recorded behavior rule

**Problem:** on #778 a session *deferred* its own merge on a stale CI read and ended the turn with
the PR left open — the abandoned-open-PR / parallel-agent-conflict failure (Q-0103). Manual
self-merge (Q-0084) put a server-side, timing-sensitive step *inside* the agent turn and carried a
multi-line "re-fetch + UNION-resolve + CI-green-on-final-head" envelope in the always-loaded
CLAUDE.md context.

**Decision:**
> 1. **Native auto-merge does the merge.** `.github/workflows/auto-merge-enabler.yml` (on `main`
>    since #779) arms GitHub-native auto-merge on every non-draft `claude/*` PR at open; GitHub
>    merges it the moment the required **Code Quality** check is green. Server-side ⇒ it cannot
>    "forget". One-time maintainer setup (done 2026-06-13): *Allow auto-merge* ON · `main` requires
>    the **Code Quality** check · `ROUTINE_PAT` widened to Pull requests + Contents write (so the
>    merge attributes to a real user and keeps `reconciliation-trigger.yml` firing — the #778
>    bot-author gotcha).
> 2. **Claude no longer merges by hand.** The Q-0084 envelope is removed from CLAUDE.md.
> 3. **Behavior rule (defense-in-depth, for any *residual* hand-merge — a carve-out, or auto-merge
>    unavailable):** re-verify **CI green on the final head** before merging, and **never defer a
>    merge to the maintainer's next message** (the #778 root cause).

**Carve-outs preserved:** a PR labelled `needs-hermes-review` (Q-0117) or `do-not-automerge`
(Q-0114) is never auto-armed — Hermes or a human reviews and merges those.

**Follow-up (handed to the Q-0107 reconciliation sweep, not chased here):** `self-merge on green`
wording still lives in `docs/operations/autonomous-routines.md` (routine prompts) and several
`.sessions/` logs / idea docs; reconcile those to "auto-merge on green" in the next docs pass.

**Home:** CLAUDE.md SESSION_WORKFLOW (envelope struck → auto-merge bullet); `auto-merge-enabler.yml`
is the mechanism; this entry is provenance.

### Q-0124 — The Q-0107 reconciliation pass is the routines' job, not a manual session's

> **DIRECTED 2026-06-13 (owner, in-session).** Verbatim: *"please make a note that the
> reconciliation is always done automatically by the routines so that should not be part of a
> manually started session unless explicitly asked."* This is the in-session direction Q-0106
> requires to edit `.claude/CLAUDE.md` directly; this entry is the provenance.

**Area:** Session/PR workflow · the Q-0107 reconciliation cadence · manual-vs-routine task scope
**Type:** Owner-directed in-session clarification (provenance per Q-0106)

**Problem (the trigger):** a manually-started session ("continue where PR #800 ended") read the
SessionStart `Recon: DUE` banner + the `current-state` "next pass is due" line and **diverted into
running the reconciliation pass itself** — which (a) was not what the owner asked (PR #800's lane was
the P0-3 hardening arc), and (b) duplicated a pass the routine was already running concurrently
(merged as #804). The banner's wording ("the next session should be a docs-only reconciliation
pass") read as an instruction to whatever session saw it.

**Decision:**
> The docs-only Q-0107 reconciliation pass is **always run automatically by the routines** (the
> `reconcile`-issue trigger → the *superbot docs reconciliation* routine). A **manually-started
> session does NOT run it unless the owner explicitly asks**; it pursues the work it was started for.
> The `Recon: DUE` banner is a signal *for the routine*, not an instruction to a human-started
> session.

**Applied this session (provenance = this Q):** CLAUDE.md Q-0107 bullet gained the manual-session
clause; `scripts/check_reconciliation_due.py`'s DUE banner reworded to say the routines run it and a
manual session should not unless asked; journal Quick-reference + Rules note added.

**Home:** CLAUDE.md § Session & plan workflow (Q-0107 bullet); `check_reconciliation_due.py` banner;
`.session-journal.md` (Quick reference + Rules). This entry is provenance.

### Q-0125 — Stale open PRs must be dispositioned (sessions + the reconciliation pass)

> **OBSERVED 2026-06-13 (owner, in-session).** Verbatim: *"there are still a few PRs open … one of
> them even has a failing CI that should be fixed"* and *"they are all quite old, I … was curious if
> a session would see them, or if the reconciliation session would clean them up, but none of that
> happened."* The owner deliberately left stale PRs to test whether the workflow self-heals; it did
> not. Treated as an in-session directive to close the gap (provenance per Q-0106).

**Area:** Session/PR workflow · open-PR hygiene · reconciliation-pass scope
**Type:** Owner-observed workflow gap → recorded behavior rule

**The gap:** four PRs sat open (#704 owner · #766 **red CI** · #771 redundant + conflicted · #805
green/auto-merging). Neither ordinary sessions nor *two* reconciliation passes (#782 noted #771 as
"recommend close" but never closed it; #804 didn't act either) dispositioned them. Sessions checked
open PRs only for *title collisions* (the Q-0060 rule), never for *health* (red/stuck/redundant).

**Decision (behavior rule):**
> 1. **A session checks open-PR _health_, not just titles.** At orientation, `list_pull_requests`
>    (state=open) + each one's CI/mergeable state; a red or stuck PR adjacent to your work is a
>    bugs-first item.
> 2. **The reconciliation pass _dispositions_ open PRs** (added to the Q-0107 reconcile scope):
>    close redundant/stale, fix or flag a red-CI one, leave owner PRs. "Noting" a PR for close is
>    not disposition — close it.
> 3. **The autonomous docs-reconciliation routine** does the same (its prompt names the open-PR
>    sweep), since a routine — not a manual session — runs the cadence pass (Q-0124).

**Applied this session:** #766 CI fixed (3 idea files were `check_docs` reachability orphans → linked
from the README index); #771 closed (redundant — its #765/#767/#769 entries are already in the ledger
— and `dirty`/conflicted); CLAUDE.md Q-0107 reconcile bullet + the routine prompt gained the open-PR
sweep; journal Quick-reference updated.

**Home:** CLAUDE.md § Session & plan workflow (Q-0107 bullet); `docs/operations/autonomous-routines.md`
(reconcile routine prompt); `.session-journal.md` (Quick reference + Rules). This entry is provenance.

### Q-0126 — Code-quality CI cost + duplicate-work prevention (early-claim convention)

> **OBSERVED 2026-06-14 (owner, in-session).** Verbatim: *"can you come up with a good way to
> make the code quality work more efficient or have it get triggered less … also something
> [to] help prevent agents from duplicating work … they should immediately open a small docs
> only PR or an empty PR … where they will shortly list all the things they expect to ship …
> so when another agent thinks to work on something they can first check the open and closed
> recent PRs so they can prevent duplicate work, and once that is done just wait pushing until
> the PR is complete and ready for the code quality check … how does it currently work? does
> it always scan the entire repo or only the new files?"*

**Area:** CI cost · session/PR workflow · duplicate-work prevention
**Type:** (a) infra improvement — **APPLIED**; (b) workflow convention — **ANSWERED in-session** (owner picked via AskUserQuestion)

**Context (measured this session).** `code-quality.yml` is the repo's dominant CI cost —
**940 runs / 2,396 min this month** (next workflow: 52 runs). Avg run 1m50s. Root causes:
1. **No `concurrency` block** — every push to a PR ran to completion even when superseded
   (every other workflow already cancels; this one didn't).
2. **No pip / mypy caching** — every run re-downloaded the pinned tools + re-type-checked all of `disbot/`.
3. **Full-repo scope, all-or-nothing** — a docs-only detector skips heavy steps for `*.md`/`docs/`-only
   changes, but any non-docs file triggers black/isort/ruff over the whole repo, `mypy disbot/`, and the
   **entire 9,422-test suite**. The diff is used only for the docs-only skip, not to scope checks.
4. **pytest is the bottleneck** — 9,422 tests in **109s** serial.

**(a) APPLIED (PR #814) — auto-merges on green like a normal PR (see (b) gate decision):**
  - **Concurrency cancellation** — `group: code-quality-${{ github.ref }}`, `cancel-in-progress`
    on everything except `main`. Biggest lever on the 940-run count.
  - **pip download cache** (setup-python) + **`.mypy_cache`** (`actions/cache`) — cut per-run minutes.
  - **`pytest -n auto` (xdist) — TRIED AND REVERTED.** Measured 109s→35s (~3×) and green locally
    (even at `-n 4`, CI's worker count), but CI went **red: 9 failed**. Re-running locally showed the
    failures are **non-deterministic** — a *different* set fails each run (`-n auto` green; `--dist
    loadscope` failed 7, then a different 1; CI failed 9). The suite has pervasive cross-test **state
    pollution** that only surfaces under parallel scheduling, so **green locally ≠ green in CI** and no
    `--dist` flag fixes it. Parallelization is **deferred** to a follow-up that makes the suite
    isolation-safe *first* (the ~3× unlock). The self-testing gate catching this is the system working.

**(b) ANSWERED in-session (owner via AskUserQuestion, 2026-06-14):**
  - **Duplicate-work mechanism = claim ledger** (option 1): new append-only `docs/owner/active-work.md`;
    agents scan it + open/recent PRs before starting, append a one-line claim, prune at close. Chosen
    over WIP-PR+label / WIP-issue. The literal "open a docs-only PR immediately" was rejected because a
    ready docs-only PR *arms auto-merge and self-merges empty* before real work lands (Q-0123).
  - **Push-batching adopted** — hold intermediate pushes; push when the PR is complete. The behavioral
    half of (a)'s concurrency cancel.
  - **Gate-workflow changes auto-merge like normal** (not auto-`do-not-automerge`): the owner chose to
    keep verified gate changes landing on green; #814 follows this.

**Applied this session:** (a) the two safe wins in `.github/workflows/code-quality.yml` (xdist reverted
there + in `scripts/check_quality.py` / `requirements-dev.txt`); (b) CLAUDE.md § Session & plan workflow
gained the claim-ledger + push-batching bullet, and `docs/owner/active-work.md` was created. Provenance
per Q-0106 (owner-directed in-session).

**Home:** CLAUDE.md § Session & plan workflow (the convention); `docs/owner/active-work.md` (the ledger);
`.github/workflows/code-quality.yml` + `scripts/check_quality.py` (the CI wins). Follow-up (parallel-safe
test suite → re-enable xdist) captured in
[`docs/ideas/ci-cost-and-duplicate-work-prevention-2026-06-14.md`](../ideas/ci-cost-and-duplicate-work-prevention-2026-06-14.md).

---

### Q-0127 — Native auto-merge never arms for MCP-created PRs (the `auto-merge-enabler` doesn't fire)

> **DECIDED + APPLIED 2026-06-16 (owner, in-session): option (a) — the session arms it.** Under the
> Q-0106 in-session exception, CLAUDE.md § Session & plan workflow now states: after opening a PR via
> the GitHub MCP, call `enable_pr_auto_merge` yourself (the enabler workflow can't fire for
> app-token-created PRs); the enabler stays the backstop for branch-pushed PRs. First exercised on
> **PR #956** this session. The original finding + options are preserved below.

**Area:** merge mechanics · the Q-0123 native-auto-merge workflow
**Type:** automation gap — needs an owner call on the durable fix

**The finding (measured).** `auto-merge-enabler.yml` triggers on `pull_request:[opened, reopened,
ready_for_review]` and would have matched #817 (non-draft, `claude/` head, no carve-out label).
But it had **0 workflow runs for `claude/funny-bohr-skbaoz`** — and **none for the concurrent
`claude/trusting-goldberg-po4p7s` band (#815/#816) either** (checked `list_workflow_runs` for the
enabler: newest run predates this band entirely). So native auto-merge was **never armed**; #817
did not self-merge despite `code-quality` passing green and `mergeable_state: clean`. I merged it
by hand in-turn per the Q-0123 carve-out (CI verified green on the final head, not deferred).

**Likely root cause (same class as #778).** PRs opened via the GitHub MCP `create_pull_request`
(an app/integration token) don't emit a `pull_request` event that triggers a workflow — GitHub's
"events from `GITHUB_TOKEN` / a GitHub App don't start new workflow runs" recursion-guard, the
**exact gotcha #778 documented for bot-authored issue triggers**. The Q-0123 design ("session just
opens the PR; GitHub does the gated merge") therefore silently doesn't hold for the way agent
sessions actually open PRs — they've apparently been merging by hand all along (the #786 "hands-off"
claim predates this band and may have used a different path).

**Proposed fix (two options — owner picks):**
- **(a) Session arms it directly (smallest, works today).** After `create_pull_request`, the session
  calls `mcp__github__enable_pr_auto_merge` (a PAT-authenticated MCP call, not a workflow trigger) →
  native auto-merge arms regardless of the event gotcha. Add a CLAUDE.md bullet; the enabler workflow
  becomes a backstop. *(Recommended — sidesteps the trigger entirely, keeps merge off the session's
  critical path.)*
- **(b) Re-trigger the enabler.** Have it also run on `workflow_dispatch` / a `push`-to-`claude/*`
  branch event, or re-author PR creation so it fires `pull_request`. More moving parts; doesn't fix
  the underlying app-token-doesn't-trigger rule.

**Until decided:** after opening a PR, a session should call `enable_pr_auto_merge` **or** merge by
hand once `code-quality` is green on the final head (Q-0123 carve-out). Recorded in the #817 session
log handoff.

**Home (once answered):** `.github/workflows/auto-merge-enabler.yml` + CLAUDE.md § Session & plan
workflow (the merge-mechanics bullet).

---

### Q-0128 — Eliminate all permission-confirmation prompts (bypassPermissions in committed settings)

> **OBSERVED 2026-06-14 (owner, in-session, via mobile screenshot of a routine session).** Verbatim:
> *"This happened during a routine, so that's a session I would normally not check, this needs to be
> prevented, I never want to see such a prompt asking me for my confirmation ever again, no matter
> what it is for I want them gone completely from every chat and every action."* The screenshot showed
> the standard CLI permission prompt ("Allow Claude to run … `git checkout … ; git reset --hard
> origin/main ; … check_docs.py`") blocking the **superbot docs reconciliation** routine.

**Area:** harness permission config · executable config (`.claude/settings.json`) · autonomous routines
**Type:** owner-directed config change — **APPLIED** (Q-0106 in-session exception: owner is the live reviewer)

**Root cause (measured this session).** `.claude/settings.json` ran `permissions.defaultMode:
"acceptEdits"` with a curated `allow` list and an `ask` list containing `git reset --hard*`,
`git push --force*`/`-f*`, `git clean*`. `acceptEdits` auto-accepts file edits but still **prompts for
any Bash command outside `allow`** — and the routine's command was both a *compound* command (`;`-joined)
and contained `git reset --hard`, which was explicitly in `ask`. So it prompted, and a routine session
(which the owner doesn't watch) silently stalled on the confirmation.

**Why this mechanism (verified against the docs + live evidence):**
- Claude Code on the web confirms *"user-level settings don't carry over to cloud sessions … only [config]
  committed to the repo run[s],"* and the repo's `.claude/settings.json` is "part of the clone." So the
  durable home for routine (cloud) sessions is the **committed** `.claude/settings.json` — not
  `~/.claude/settings.json` (lost on the ephemeral container) and not a gitignored local file.
- The routine *prompted* (rather than running prompt-free) — proof it is driven by this file's `defaultMode`,
  not a higher-precedence CLI/managed override (precedence: Managed > CLI > Local > Project > User). Flipping
  `defaultMode` here therefore takes effect for routines.
- `bypassPermissions` is the only `defaultMode` that skips **all** prompts regardless of command (`auto`
  still prompts on classifier-flagged/destructive commands — i.e. the exact `git reset --hard` case). The
  cloud sandbox ("Security and isolation") is the safety envelope that makes prompt-free autonomous
  execution the documented intent.

**Applied (this session):** in committed `.claude/settings.json` — `defaultMode` `acceptEdits` →
`bypassPermissions`; `ask` list emptied (`[]`); added top-level `skipDangerousModePermissionPrompt: true`
(pre-accepts the bypass-mode dialog so it never surfaces, incl. local/desktop opens). The `allow` list is
kept as a harmless documented fallback if the mode is ever reverted; all hooks (pre/post-edit, Stop,
SessionStart) are untouched — bypass removes permission *prompts*, not the repo's quality gates. Verified no
repo hook emits an interactive `ask` permissionDecision, so the permission system was the only prompt source.

**Trade-off (explicitly accepted by owner).** Every tool/command — including destructive/irreversible ones
(`git reset --hard`, force-push, `rm`, external publishes) — now runs without confirmation in every session
on this repo. The owner directed exactly this ("no matter what it is for"). Reversible at any time by setting
`defaultMode` back to `acceptEdits`/`auto` (and restoring the `ask` entries). If prompts are ever wanted for a
specific dangerous class only, prefer `defaultMode: "auto"` + an `ask` list over full `acceptEdits`.

**Home:** `.claude/settings.json` (the change); this Q-block (provenance per Q-0106). The
`docs/current-state.md` Recently-shipped entry lands when the PR merges (merged-PRs-only convention).
CLAUDE.md is unchanged — this configures the harness, it does not alter a written rule.

---

### Q-0129 — `send_later` noise + owner endorsement of unattended self-initiated work

> **OBSERVED 2026-06-14 (owner, in-session, same conversation as Q-0128).** Two things. (1) On the
> harness referencing a `send_later` tool: *"i noticed a lot of sessions mention that, but that only
> started about a week ago … now all of the sudden every session is trying to use send later but it's
> never there."* (2) Directive on autonomy: *"it should be clear in the repo that I do not oppose
> unattended action, as long as it is something that improves the workflow, this whole project's main
> idea is that AI gets more freedom to run its own project with only a little guidance"* — and earlier
> in the thread, approving the self-initiated journal note: *"that is exactly the kind of self
> initiated action I like."*

**Area:** harness/system-prompt behavior · collaboration-model autonomy stance
**Type:** (1) operational note — **APPLIED** (journal); (2) owner directive — **APPLIED** (ethos to docs)

**(1) `send_later` — what it is and why the noise.** `send_later` is a tool from Anthropic's internal
**`claude-code-remote`** MCP server that lets a session schedule a future self check-in (re-wake to
re-check a PR's CI/merge state — the events webhooks don't push). ~A week ago the remote/web harness
**system prompt** (platform-injected, *not* this repo) gained a PR-watching instruction: "arm a
`send_later` self check-in before ending your turn, *if available*." The tool is **not provisioned in
this environment** (a direct ToolSearch returns only `Monitor`/`WebFetch`), so every session checks,
falls back to subscribe-and-report, and narrates the attempt — the noise the owner saw. Harmless
(conditional instruction; PRs auto-merge server-side regardless). **Recorded the skip-it note in the
journal** (§Cross-agent & git workflow): don't chase it; subscribe + report (+ optional git-ancestor
`Monitor`) is the working fallback; delete the note if `send_later` ever resolves. The human-set-up
equivalent is a one-off Routine (`/schedule in 1h, check PR #N`). Not in this repo's power to enable —
it's platform/feature-flag gated.

**(2) Unattended initiative is *wanted*, not merely tolerated.** The owner made his autonomy stance
explicit: unattended, self-initiated action is welcome **whenever it improves the workflow** — the
project's premise is AI running its own project with light guidance. This *strengthens* (does not
replace) the existing "Autonomy boundary — docs free, config asks" rail: the irreversible / external /
new-enforced-rule pauses still hold, but inside them the default posture is **act and improve**, not
wait to be watched. Homed as **ethos** (not a new *enforced* rule — so "docs," free-rein per
collaboration-model.md §"Autonomy boundary"; recorded here for provenance since owner-directed
in-session): a clause on the CLAUDE.md "Act vs. ask" bullet + a paragraph in
`docs/collaboration-model.md` §"Why this system exists."

**Home:** `.claude/CLAUDE.md` §Working agreement (Act vs. ask clause); `docs/collaboration-model.md`
§"Why this system exists" (the endorsement); `.session-journal.md` §Cross-agent & git workflow (the
`send_later` skip note). This Q-block is provenance.

---

### Q-0130 — Railway access for agents: read-only logs now; broader-access ladder to decide

> **OBSERVED 2026-06-14 (owner, in-session, with two Railway dashboard screenshots).** Verbatim:
> *"I also want to create a railway API for hermes so it can check the bots logs"* and *"if I can
> grant claude more access to railway I'd love to do so."*

**Area:** production access / security trust-tier · Hermes tooling · `production-deployment.md` posture
**Type:** (1) read-only log access — **APPLIED** (owner-directed); (2) broader access — **DISCUSS** (owner picks the tier)

**Context.** `docs/operations/production-deployment.md` had stated *"agents have no Railway access."*
The `superbot-log-triage` skill was a stub — step 1 said "production logs unavailable — read-only
Railway token not configured." The owner asked to close that gap and signalled openness to more.

**(1) APPLIED — read-only log access (this PR).** New `scripts/hermes/railway_logs.py` (stdlib-only)
reads the bot's latest-deployment logs via the Railway public GraphQL API
(`backboard.railway.com/graphql/v2`; cookbook-verified queries `deployments` + `deploymentLogs`).
**Read-only by construction** — queries only, no mutation. The `log-triage` skill is rewired to use it
(doc source + regenerated `SKILL.md`). Owner setup (read-only token + ids as VPS env vars, least-priv
project token) is documented in `production-deployment.md` § "Hermes read-only log access (Railway API)".
Mocked unit test `tests/unit/scripts/test_railway_logs.py` (14 cases). The "no Railway access" posture
is narrowed to "no *write/deploy* access; read-only logs allowed."

**(2) DISCUSS — the broader-access ladder (owner picks how far to go).** Granting agents more Railway
power is a deliberate trust-tier step (the collaboration-model "graduated trust tiers" / Q-0048 pattern),
so it is *proposed*, not applied. Proposed ladder, least → most privileged:
  - **T0 (done):** read-only **logs**.
  - **T1:** read-only **status / metrics** — deployment status, restart count, resource usage, recent
    deploy history (powers a richer health digest). Still query-only; same read-only token.
  - **T2:** scoped **write — restart only** (`deploymentRestart` / `serviceInstanceRedeploy`). The first
    *operate* power — recovers a crash-looped bot. Needs a mutating token (higher blast radius); gate
    behind an explicit allow + an `emit_audit_action`-style log line, mirroring the Q-0084 merge grant.
  - **T3:** broader **write** — env vars, scaling, rollbacks, new deploys. Highest risk; almost certainly
    stays maintainer-only ("merge ≠ deploy; restarts / rollbacks / prod-checks stay the owner's",
    Q-0084 + production-deployment.md).
**Recommendation:** **T1** next (pure read, high value, no new risk class); keep **T2** behind an explicit
owner grant + audit; hold **T3**.

**DECIDED 2026-06-14 (owner, in-session) — env-var read+write GRANTED (a T3 subset), APPLIED.** Asked which
tier, the owner chose to go straight to **service env-variable read _and write_**: *"would that mean that you
could see and edit my env variables? honestly that would be kinda useful … I give you full access to
implement this, I know there is some risk but honestly not a lot more than I already have, and I'm willing
to take the gamble."* Shipped as `scripts/hermes/railway_vars.py` (`list` / `get` / `set` / `unset`) with
guardrails: masked `list`, audit lines to stderr, secrets via stdin, and `--no-deploy` to stage without a
redeploy (a `set` otherwise triggers a Railway redeploy). The **other** T3 powers — deploy / restart /
scale / rollback — were **not** granted and stay maintainer-only. **T1 (read-only metrics)** remains open
and available on request. Setup the owner must do: a **write-capable** token + all three ids in the agent
environment (see `production-deployment.md` § "Env variable read/write (Railway API)").

**Home:** `scripts/hermes/railway_logs.py` + `docs/operations/production-deployment.md` (access posture +
setup) + the `log-triage` skill (doc + generated SKILL.md). This Q-block is provenance for T0 and the
open decision for T1–T3.

---

### Q-0131 — Maintainer follows provided steps without vetting → label the risk class of every manual step

> **OBSERVED 2026-06-14 (owner, in-session).** Verbatim: *"the only thing I do is follow the steps
> you provide, so if you wanted to add something destructive you could have easily achieved that by
> steering me, since I don't really know what I'm doing anyways."*

**Area:** owner working profile · agent-behavior safeguard
**Type:** owner-surfaced trust dynamic → guideline **ADOPTED** (in the working profile)

**The dynamic.** The maintainer executes agent-provided manual steps literally, without the technical
judgment to vet them himself (consistent with the §2 "harder for him to: read coding jargon; tell at a
glance whether a decision is architectural/…"). That makes any manual step an agent hands him a real
position of trust.

**Guideline (adopted in `maintainer-working-profile.md` §2).** When handing the maintainer a manual step
— especially anything touching secrets, production, money, deletion, or an external service — **label its
risk class plainly** (`✅ safe/read-only` · `↩️ reversible` · `⚠️ irreversible/destructive`) so he can
judge it without the internals, and never bury a destructive/irreversible action inside routine-looking
steps. The structural safeguards that keep the trust sound — reviewable/revertible PRs, cross-agent
review, and "ask what it does" always being answerable — must be preserved, not eroded.

**Home:** `docs/owner/maintainer-working-profile.md` §2 (the observation + rule). If this should be
elevated to a *binding* executor rule (`docs/collaboration-model.md` / CLAUDE.md), that's a one-line owner
yes — flagged here, not self-applied (Q-0106).

---

### Q-0132 — Durable items mined from the owner's exported strategy chats (2026-06-14)

> **→ Program law: [PL-007]** — this block's durable conclusion is canonicalized as program law **PL-007** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

> **CAPTURE 2026-06-14 (owner-directed).** The owner exported his claude.ai chat history (13 plain
> chats — Claude Code *sessions* are not in that export) and asked the session to "see if anything is
> worth remembering in the repo." A sub-agent mined all 13 (human messages prioritized) + dedup-grepped
> the owner docs; the durable, novel items were captured to their homes (below). This block is the
> provenance index.

**Headline owner-decision rationale recorded here (its proper home): why the bot's AI routes to
Anthropic/Claude, not GPT.** The bot routes its NL tasks to `anthropic:claude-haiku-4-5` (Sonnet
fallback) — the *env wiring* is in the repo but the *why* was never recorded. The owner's reason, stated
repeatedly: GPT **failed his eval battery** on the two axes a moderation/server-management bot cannot
compromise — *prompt-injection resistance* and *reliable instruction/tool-calling*: "I can't trust
chatGPT's AI… not resistant against weaponized prompts… very bad at correctly following instructions and
tool calling," vs. Claude where "it's 99.9% impossible to 'trick'… into saying something it isn't allowed
to." So the model routing is a **trust/safety decision**, not a cost/quality one — keep it Anthropic for
any path handling untrusted user input or relying on trustable data. (Source: "Comparing
Grok/Claude/ChatGPT/Gemini" + "Verifying ChatPlayground…", 2026-06-02.)

**Other captures (homes):**
- **`maintainer-working-profile.md` §7** — operating reality + verification discipline: phone-only
  zero-stakes hobby (why low-guarding autonomy works) · his code-reading boundary (catches
  awaits/imports + run-correctness, not deeper → show your reasoning) · "do the math, don't hand it
  back" · "green tests ≠ verdict; extracted ≠ reachable ≠ answerable" · friends' exact phrasings ARE the
  regression suite · the "can't pick the lesser model" cost tendency (a 22-agent audit burned the 5-hr
  limit + ~$60).
- **`.session-journal.md` §Cross-agent & git workflow** — generalized the `send_later` skip-note to the
  **phantom-tool keyword-injection pattern** (the owner-traced `workflow`→non-existent `Workflow` tool, a
  platform-side dangling reference).
- **`.session-journal.md` §CI & quality gates** — candidate rule: a doc claim mirroring code state must be
  **CI-backed (a test that fails on divergence)** or date-stamped as a snapshot, never refreshed by
  per-session human discipline (the rebuttal to "document every mention-worthy edit" at 10–40 PRs/day).
- **`docs/ideas/future-product-direction-2026-06-07.md`** — BTD6 answer-cache design constraint: key on
  resolved-entity + data-version (never question text), cache only provenance-stamped tool results,
  invalidate on ingest.

**Considered, not captured:** the AI read-only-actions ceiling + DnD-quest concept (already in
future-product-direction's "AI explanations only, no write tools") and the ChatGPT "Revision project"
grounding contract (the repo already enforces grounding-first/cite-everything) — both already covered.

**Home:** this block (provenance index); the four docs above hold the items.

---

### Q-0133 — Born-red session card: hold the merge until the session flips it ready (2026-06-14)

> **DECISION 2026-06-14 (owner-directed, applied in-session per the Q-0106 in-session-exception —
> the owner is the live reviewer for this CLAUDE.md + workflow change).**

**Problem.** Native auto-merge (Q-0123) merges a `claude/*` PR the instant **Code Quality** is
green. A session that pushes its code first and its close-out docs (ledger entry, `.sessions/`
log) second merges a **partial** PR before those docs land — the **#843** case: it merged without
its ledger entry, leaving a stranded follow-up (#846). Push-batching discipline (Q-0126) alone did
not prevent it; the owner asked to **enforce** a hold.

**Owner's mechanism (his words, refined live).** "Enforce a rule so that the first docs PR…has a
document with failing CI, and only when you want to merge do you change the document and CI goes
green" → refined to: "the **same file** is also the session-start and session-end file, so it shows
the next/parallel session **what is about to happen and what has happened**."

**Decision — adopted as designed.** That single file is the existing **`.sessions/<date>-<slug>.md`
session log**, and its `> **Status:**` badge gates the merge:
- Created in the **first** commit with `Status: in-progress` + a one-line "what's about to happen"
  → the PR is **born red** (race-free: the gate is red from commit 1, not a label added later).
- Flipped to `Status: complete` as the **deliberate final step**, after the close-out docs (and the
  Q-0089/Q-0102 enders) are written → Code Quality green → auto-merge fires on a *complete* PR.
- Per-session filename → no parallel-chat collision, no `main` conflict; it lands on `main` as the
  durable "what happened" record (already the `.sessions/` convention). Coordination ("what's about
  to happen") is visible on the open PR; complements the pre-PR `active-work.md` claim ledger.

**Strictness chosen — engage-when-present (not airtight).** The `check_session_gate` step in
`code-quality` fails **only** when the PR *adds* a session card whose status isn't a ready token;
a PR that adds no card merges as before. This is deliberate: it **cannot deadlock the autonomous
loop** (workflow-authored PRs like `btd6-data-refresh`, or a routine that hasn't created a card,
are never blocked). Creating the card is mandatory **by the CLAUDE.md rule** + the Stop-hook /
`/session-close` reminder, not by hard CI. *Can be tightened to airtight (absent = red, with
carve-outs for workflow-authored PRs) later if routine adoption proves reliable — left as the
follow-up.* Reliability (Q-0105): UNVERIFIED — `scripts/check_session_gate.py` + the workflow step
are deletable if the gate ever holds a PR it shouldn't.

**Home:** `.claude/CLAUDE.md` § Session & plan workflow (the rule); `scripts/check_session_gate.py`
+ `.github/workflows/code-quality.yml` (the gate); `.claude/skills/session-close/SKILL.md` (the
flip-ready step). Shipped this session (born-red dogfooded on its own PR).

---

### Q-0134 — Reconciliation cadence widened 20 → 30 PRs (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session — the live reviewer for this workflow change,
> per the Q-0106 in-session exception).** Asked during the workflow-health review session.

**Problem.** The Q-0107 docs-reconciliation cadence fired on every **multiple-of-20** PR band.
At the project's burst velocity a 20-band crossed in **under a day** (#800→#820→#840 all on
2026-06-13/14), so the docs-only pass fired **several times per day** — re-scoring a band that
had barely moved and spending a cloud session each time. The owner had already raised it 10→20
(2026-06-12) for the same reason; the symptom returned.

**Decision.** Widen the band to **30** (`STEP = 30` in `scripts/check_reconciliation_due.py`).
Considered a time-floor hybrid (≥N PRs AND ≥M hours) but the owner chose the simpler one-number
change. Retune the constant if it drifts again. With the marker at #840 the next pass is due at
**#870** (was #860).

**Home:** `scripts/check_reconciliation_due.py` (`STEP`); `.claude/CLAUDE.md` § Session & plan
workflow (the rule); `docs/current-state.md` marker note; `docs/operations/autonomous-routines.md`.
The `reconciliation-trigger.yml` workflow reads the script, so the change propagates with no
workflow edit.

---

### Q-0135 — Loop-health probe: re-verify the control-plane state from live GitHub (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session).** Asked in the same review session.

**Problem.** The autonomous loop's wiring (ROUTINE_PAT, backups, whether it has self-fired) lived
only in a hand-ticked table in `autonomous-routines.md` § Control-plane state, which no repo
checker can see — and it **drifted**: it marked `ROUTINE_PAT` unverified and the loop "never
self-fired" when live GitHub already proved both true (the trigger issues were authored by the
PAT owner, and #819→#821→#825 had run unattended).

**Decision.** Add `scripts/check_loop_health.py` — a stdlib, `gh`-backed, read-only probe that
re-derives the verifiable rows from recent issues (trigger-issue author = ROUTINE_PAT state;
open backup-failure issue = DATABASE_PUBLIC_URL unset; closed scheduled-executor issue = loop
self-fired) and prints PASS/FAIL/SKIP. Degrades to SKIP where `gh` is absent (never reddens a
session). Folded into the **reconciliation routine** STEP 2 (not a new fleet routine — no extra
run-cap cost) so the table is re-checked every pass. Pure `classify` core unit-tested (+9 tests).
Reliability (Q-0105): unverified — delete if its heuristics misclassify over multiple sessions.
The repo-side sibling — an env-credential preflight at SessionStart — stays the captured idea
`docs/ideas/agent-env-credential-smoke-check-2026-06-14.md`.

**Home:** `scripts/check_loop_health.py`; `tests/unit/scripts/test_check_loop_health.py`;
`docs/operations/autonomous-routines.md` (STEP 2 + See also).

---

### Q-0136 — Hermes dispatch: authorize secret-env use (the "sensitive information" balk) (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session).** The owner reported Hermes "has a problem
> dispatching the routines, something about sensitive information"; asked me to diagnose.

**Diagnosis.** The `superbot-dispatch` skill prompt gave Hermes only a *prohibition* — "Never
print secrets … reference env vars by name only" — with no explicit *authorization* of the
action it must take (sourcing `$CLAUDE_ROUTINE_TOKEN` into the `/fire` curl). A safety-cautious
Claude-based agent reads "this involves a credential" and declines/stalls. Most likely the whole
cause; the only other candidate is mechanical (`~/.hermes/routine.env` not loading / token
expired → a *correct* refusal per STEP 4).

**Decision.** Add an AUTHORIZED rule to the dispatch prompt: using the named secret env vars in
the authenticated `/fire` call is sanctioned, not a leak (the value goes only to the Anthropic
endpoint, never printed/logged/echoed) — do not refuse on a sensitive-data basis. Documented the
diagnosis + both hypotheses + the VPS env-file check in the skill's Notes. **Owner action:**
re-paste the updated skill into Hermes' config; if the balk persists, check the env file on the
VPS. Deferred deeper investigation (owner: "we'll come back to that later") — this is the
first-pass fix.

**Home:** `docs/operations/hermes-skills/dispatch.md` (the AUTHORIZED rule + Notes diagnosis).

---

### Q-0137 — Planning sectors + Hermes-dispatched routines + staged deep-clean reconciliation (2026-06-14)

> **PARTLY DECIDED — owner design conversation, 2026-06-14.** Three linked threads dropped in chat;
> captured in full (owner direction + agent opinion) in
> [`../ideas/routine-dispatch-and-staged-reconciliation-2026-06-14.md`](../ideas/routine-dispatch-and-staged-reconciliation-2026-06-14.md).
>
> **DECISION 2026-06-14 (Thread 3 — sectors):** owner adopted a **5-sector** planning taxonomy with
> the **mechanism-vs-content split** — **S1 Bot · S2 BTD6 · S3 AI-Memory system (the *mechanism* — a
> shippable engine of its own) · S4 Documentation system (the *content/product* the engine generates) ·
> S5 Operations/control-plane.** Owner's rationale: "the docs are not the system, the docs are a product
> of the system" — so Memory and Docs are separate sectors (the substrate is NOT folded into the docs).
> Built as [`../repo-sector-map.md`](../repo-sector-map.md) (the 3-tap nav top layer). **Threads 1 & 2
> (dispatch + staged deep-clean) remain open** for owner decision.

**Thread 1 — dispatch.** Owner wants a more reliable dispatch with **every routine started by Hermes
except reconciliation**. *Agent view:* endorse — dispatch is already Hermes (`/fire`); the concrete
change is moving the **night executor** off GitHub's flaky `schedule:` cron onto the always-on Hermes
VPS. **Keep reconciliation independent** because it is the **watchdog** (it runs `check_loop_health`);
if it depended on Hermes, a Hermes outage would silently disable outage-detection. **Add a rail:** keep
GitHub `schedule:` as a *degraded backstop* so a Hermes outage means "late," not "stopped."

**Thread 2 — staged deep-clean.** Reconciliation should grow from docs-only into a staged deep-clean
(surface problems · de-stale docs · dispose of open PRs/branches · review shipped work · refactor the
roadmap · keep a healthy stability-vs-features backlog). *Agent view:* strong agree; (a) generate the
*mechanical* findings via checkers into a punch-list so judgment-time goes to planning; (b) make it a
**resumable staged program** (self-chains like the executor) with a **terminal condition** =
every sector has live Now/Next horizons, zero rotting PRs/branches, ledger+docs green, control-plane
verified. That operationalizes "always enough outstanding work."

**Thread 3 — planning sectors.** Divide the repo into standing planning sectors: **bot · BTD6 · agent
substrate · documentation system** (in-bot AI integrated into the bot). *Agent view:* the key reframe
is **planning taxonomy ≠ review taxonomy** — `repo-review-map.md` Axis A already partitions for
*review scoping*; the owner wants a *planning* partition the roadmap organizes around, which doesn't
exist yet. Proposed coarsening: **S1 Bot product · S2 BTD6 (standing, spans A1 runtime + A2 pipeline) ·
S3 Agent substrate (memory + docs-system + governance + tooling + loop — the owner's "AI-memory" and
"documentation" are two faces of one sector) · S4 Operations / control-plane (THE FORGOTTEN ONE —
no home today for non-file operational health: routine firing, backups, secrets, Hermes uptime; every
recent real failure lived here) · (S5 substrate-as-product, future).** Reconcile S→A in both
`repo-review-map.md` and the roadmap so two taxonomies don't compete.

**Open decisions for the owner:** (1) adopt the S1–S4 planning-sector taxonomy (and create S4
Operations as a first-class sector)? (2) move the executor to Hermes-dispatch + keep a cron backstop?
(3) approve the staged-deep-clean shape + terminal condition before it's built? **Home on decision:**
`docs/operations/autonomous-routines.md` (dispatch + deep-clean), `docs/roadmap.md` + `repo-review-map.md`
(sectors).

---

### Q-0138 — Branch-freshness advisory hook (conflict/staleness guard) (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session — the Q-0106 exception: maintainer directs an
> executable-config change live, so it is applied directly and recorded here with provenance).**

**Context.** The owner asked for "a hook that tells any session that's about to merge something to
check for recently merged PRs / outstanding PRs to fix any possible merge conflicts." Initially
withdrawn (a parallel session self-handled a dirty merge), then re-requested after **#857 sat
CONFLICTED and unmerged unnoticed** — a parallel PR (#855) merged a shared ledger file *after* #857
was pushed, GitHub auto-merge silently waited on the dirty PR, and no event woke the session
(webhooks don't deliver merge-conflict transitions).

**Decision.** Add `scripts/check_branch_freshness.py`, a **non-blocking** advisory wired two ways in
`.claude/settings.json`: (1) **PreToolUse on Bash** — acts only on `git push` (the "about to ship"
moment, warn if already behind); (2) **Stop** — checks the branch every turn, so a branch that falls
behind *after* its last push (the #857 case) is flagged on the next turn. It fetches `origin/main`,
and if behind, lists the merged PRs + flags high-conflict ledger files (`active-work.md`,
`current-state.md`, `ideas/README.md`, the router, `roadmap.md`), pointing at the fetch+UNION-merge
fix. Always exits 0 (never blocks a push/turn). 7 unit tests; disposable kill-switch header per
Q-0105 (delete if noisy over multiple sessions).

**Home:** `scripts/check_branch_freshness.py` + `.claude/settings.json` (PreToolUse Bash + Stop).

---

### Q-0139 — Hook policy: when a fix becomes a hook vs. a rule/checker/config/doc (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session).** Owner asked for "a ruleset for what a hook
> should define — what something needs to have/do/cause to qualify for a hook, so we know in which
> future situations to fix something by making it a hook vs. adding it to CLAUDE.md / settings.json."

**Decision.** Created [`../operations/hook-policy.md`](../operations/hook-policy.md) — the
executable-config analogue of `helper-policy.md`. It names the **five mechanisms** (hook · checker ·
CLAUDE.md rule · settings.json config · doc), a **five-part test** for what qualifies as a hook
(automatic & forgettable · event-anchored · mechanizable at fire-time · cheap & safe/non-blocking ·
recurring), a **quality bar** (defensive, self-filtering, kill-switch header, paired test), a
**decision tree**, and worked examples. Does **not** lift the Q-0106 boundary (hooks/settings.json/
CLAUDE.md are still propose-unless-owner-directed). Prompted by the Q-0138 freshness hook built the
same session.

**Home:** `docs/operations/hook-policy.md`.

---

### Q-0140 — Hermes may author docs-only PRs directly (second sanctioned write) (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session, relayed from the owner's Telegram chat with
> Hermes).** The owner told Hermes: *"the only thing you should edit directly is a docs-only PR,
> that either contains a summary of the expected work done, or contains some bugs or problems I or
> someone in the discord told you."*

**Decision.** Hermes' write scope expands from "read-only **except** the `review-merge` gate
(Q-0117)" to **two** sanctioned writes: (1) the review-merge gate, and (2) **docs-only PRs** —
a work summary, a bug/problem report, or a new skill source (`superbot-skill-author`). Anything
touching **code/runtime** is still **dispatched** to Claude Code, never edited by Hermes. Reading
Railway env vars/logs for verification stays sanctioned (Q-0130); mutating production config is not,
unless the owner explicitly directs it.

**Why:** it lets Hermes close its own loop — capture a Discord/owner bug as a tracked docs PR, post
a verified work summary, and (with `skill-author`, Q-0140's first use) author new skills back into
the repo instead of leaving them VPS-only — without granting it code-write power.

**Also recorded this session (related):** the **`superbot-skill-author` meta-skill** (the
self-extension bootstrap), and the owner's operating directives now in
`docs/operations/hermes-operating-prompt.md`: there is always a next thing (review ideas + propose
a continuation when nothing's obvious; the continuation handoff lives in `current-state.md` + the
newest `.sessions/` log); reconciliation is automated (ignore it); verify-don't-assume; the
five-sector mental model.

**Home:** `docs/operations/hermes-operating-prompt.md`, `docs/operations/hermes-skills/README.md`
(Shared operating rule), `docs/operations/hermes-skills/skill-author.md`.

---

### Q-0141 — Hermes may write code (not docs-only); + routine_fire.py dispatch helper (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session).** While live-testing Hermes' new operating
> prompt, Hermes diagnosed a real bug (the dispatch curl is shell-quoting-fragile for multi-line
> work orders) and started writing `scripts/hermes/routine_fire.py` itself — crossing the Q-0140
> docs-only boundary. Asked the owner whether to hold that line; owner answered: *"yes it may write
> its own code, I also think it can be pretty capable"* (Hermes runs StepFun Step 3.7 Flash,
> ~74.4% SWE-bench).

**Decision.** Hermes' write scope **expands beyond docs-only to code**, via **PRs (CI-gated)**:
- It may author code — including its own small self-tooling — through PRs; it never pushes to `main`
  and never mutates production config outside the gates.
- It should still **prefer to DISPATCH big/risky code to Claude Code** (the primary builder, full CI
  mirror; Hermes is self-admittedly weaker on long 20+-tool-call loops). Write directly when small,
  self-contained, verifiable.
- `review-merge` (Q-0117) remains its merge action (calibrating). Q-0140's docs-only framing is
  superseded by this broader scope; the *content* (Hermes may PR work summaries / bug reports / skill
  sources) still holds.

**Also shipped:** `scripts/hermes/routine_fire.py` — the canonical robust dispatch helper (work order
on stdin → no shell quoting; loads CLAUDE_ROUTINE_* from env/`~/.hermes/routine.env`; never prints the
token; `--dry-run`). The `superbot-dispatch` skill now fires via it. **Opened as a DRAFT PR on purpose:
the owner is running a "nice test" — Hermes is authoring its own version in parallel, to be compared.**

**Home:** `docs/operations/hermes-operating-prompt.md`, `docs/operations/hermes-skills/README.md`,
`scripts/hermes/routine_fire.py`, `docs/operations/hermes-skills/dispatch.md`.

### Q-0142 — Hermes picks the next slice from LIVE state, never a plan's PR numbers (2026-06-14)

> **DECISION 2026-06-14 (owner-directed in-session).** The owner showed the Telegram trace of a
> "dispatch a continuation worker" run: Hermes built a work order to *reconcile the ledger for
> #848–#856* — work that no longer existed. He'd run the live ledger guard (it returned CLEAN) but
> dispatched a reconciliation task anyway, because he read the band-#840 reconciliation plan's
> forward range — *"the next ~9 PRs (band #841–#860)"* — as the schedule. The plan was written at
> HEAD #840; by dispatch time live `main` was at #866, so those numbers were stale. Owner: *"he
> always seems to be a bit behind which is weird"* → asked to fix how Hermes picks work.

**Root cause.** PR numbers in planning docs are a **dated snapshot** — GitHub assigns them globally
across all parallel + housekeeping PRs, so any forward "#AAA–#BBB" band range (or "slot N = #NNN"
mapping) is wrong the moment an unplanned PR merges. The `superbot-dispatch` skill had **no procedure
for the no-explicit-task ("continuation worker") case**, so Hermes fell back to those plan numbers
instead of live state.

**Decision / fix (this PR).** When no specific task is given, Hermes derives the next slice from
**live state**: (1) read `current-state.md` ▶ Next action; (2) run `check_current_state_ledger.py
--strict` — drift = the only reconciliation task, CLEAN = nothing to reconcile (reconciliation passes
fire automatically — never hand-dispatch one); (3) pick the slice by **description/lane**, not a PR
number; (4) confirm it isn't already shipped. Standing rule: **when a plan and live state disagree,
live state wins** (merged PRs > current-state > plans). Plan-doc forward ranges are de-numbered to
slot-sequence framing so the misleading artifact is gone at the source.

**Home:** `docs/operations/hermes-skills/dispatch.md` (STEP 1b + the PLAN-NUMBERS-ARE-DATED rule;
artifact regenerated via `build_skills.py`), `docs/operations/hermes-operating-prompt.md` ("pick by
description, not PR number"), `docs/planning/reconciliation-pass-2026-06-14-band840.md` §4 heading.
**Re-paste the operating prompt + `superbot-dispatch` skill into Hermes' config on the VPS for this
to take effect.**

---

### Q-0143 — Dispatch contract: the executor dimension + the startability tag (2026-06-14)

> **DECIDED 2026-06-14 (owner-delegated "decided-by-derivation").** Refines **Q-0137 Thread 1**
> (dispatch). Provenance: a live **dogfooding test** of the 5-sector dispatch structure this session
> (traced S1/S2/S5 from *dispatched → ready-to-work*). The owner reviewed the three findings and chose
> to build all three into one docs PR, delegating the design call to the agent. Recorded here so the
> derivation is durable.

**Context — what the test found.** The structure passed on **speed** (dispatch-to-ready was 2–3
targeted reads per sector; all links resolved; the index ranked even the 8-area S1 down to one `Now`;
a 20-min-stale `Now` self-corrected at the linked authority in one hop). It surfaced three gaps in the
*dispatch model* (not the structure): (1) per-sector `Now` lags merges until the next reconciliation;
(2) a non-empty `Now` can be **un-startable** (S2's was demand-driven + maintainer-only — the startable
item was in `Next`); (3) the model `sector + action` silently assumed a **Claude-in-repo** executor,
but most of **S5** runs on the Hermes VPS or is a maintainer action.

**Decision (derived).** A complete dispatch is **`sector + action + executor`**, and every roadmap
`Now` item carries a **startability tag**:

- **Executor dimension** — three runners: **Claude-in-repo** (default for S1–S4), **Hermes-on-VPS**
  (read-only ops; sanctioned writes = Q-0117 review-merge + Q-0140 docs-only PRs), **maintainer**
  (deploy · secrets · Railway token · live spot-checks). **S5 is the outlier** — route an S5
  token/deploy task to Hermes or the maintainer, *not* a repo-editing agent. (This sharpens Q-0137
  Thread 1's "every routine started by Hermes": *which* runner depends on the sector.)
- **Startability tag** — **▶ startable** (no gate) · **⛔ gated** (decision/dependency/creds) ·
  **👤 maintainer**. A sector whose `Now` is entirely ⛔/👤 is **not autonomously dispatchable** —
  surface the first ▶ item (often in `Next`) as the de-facto target.

Also fixed in the same PR (finding 1): S1's `Now` de-drifted for #878 (offline eval/smoke matrix
shipped) + P1-1's plan linked directly from the S1 block.

**Home:** `docs/repo-sector-map.md` § "The sectors as dispatch targets" (the stable contract — executor
table + startability legend) · `docs/roadmap.md` per-sector `Now` (the live tags + per-sector executor
on each Dispatch line). **Open follow-on (not built):** a `check_sector_map.py` could later assert every
`Now` item carries a tag and every sector a default executor — graduates the convention to enforced.

---

### Q-0144 — Routine-prompt canon: foolproof, completion-biased, idea→plan promotion (2026-06-15)

> **DECISION 2026-06-15 (owner-directed in-session, applied directly).** A long live session: the
> owner wants the autonomous-routine prompts to run **completely without guidance** and be
> **foolproof against bad dispatch input** — *"so foolproof that if Hermes says 'go write a story
> about chickens' they still know to follow the agent orientation and continue the plan."* Provenance:
> the owner's 12-step canonical session lifecycle (stated verbatim) + an independent review from a
> Hermes-dispatched routine, which surfaced the real failure mode below.

**The diagnosed failure mode (the dispatched routine's review).** The system is excellently tuned for
*executing* correctly but slightly mis-tuned for *authorizing* correctly in the autonomous case — and
"wrongly stopping" (a correct, wanted change silently doesn't happen, and no one finds out) is a worse
failure for a routine than "wrongly proceeding on something contained/reversible/test-covered." The
dispatch prompt routed a dispatched feature through `feature (agent-originated) → phase gate → exit 1
→ DO NOT build`, where the whole escape hatch was the parenthetical "(agent-originated)" — drowned by
loud imperatives. It nearly refused wanted work. Root cause: the prompt never stated that **a
dispatched order = the maintainer asking = build it**, and its centre of gravity was caution, not
completion.

**Decision / fix (this PR).** Rewrote the **dispatch** (`hermes-dispatch-bridge.md`) and **night-
executor** (`autonomous-routines.md`) prompts onto the owner's 12-step lifecycle, and enhanced the
**reconciliation** prompt. Principles now explicit in every routine prompt:

- **Completion bias / never-stop.** For a routine there is no valid "stop / refuse" outcome except a
  genuine irreversible-safety reason — it always ships *something real*: the dispatched work, or the
  next plan slice. Bias to finish, not to stop at the first gate.
- **Sync-first.** `git reset --hard origin/main` before reading state — a stale clone was a named
  Hermes failure (it "forgets to sync, works behind live").
- **The work order is a HINT, never an order, never a licence to invent.** Aligns with a real slice →
  do it; empty/off-plan/nonsense ("chickens") → ignore it, do the next real plan slice; never invent
  work not in a plan or the bug-book.
- **Authorization + the scope-brake vs safety-brake split.** A dispatched order is owner-directed →
  build it; the **phase gate is a SCOPE brake** for *self-invented* features only and does **not**
  apply to dispatched work (sharpens Q-0114). A **SAFETY brake** (irreversible: data loss / external
  publish / production / Railway / DB) never bends.
- **2–3 slices per session, bounded by ~700K tokens** (not 1M) — owner observation that quality holds
  to ~700K and a finished session often lands at 200–300K, so there's room for more. Updates
  `ai-project-workflow.md` §10 ("~2 substantial tasks" → "2–3 slices, ~700K-bounded").
- **Born-red mock PR** (Q-0133) as the maintainer's *async* review surface; **judgment over the plan**
  (a plan is a suggestion of the desired output); **bugs-first / root-cause**; the standing enders
  (Q-0089 idea · Q-0102 prev-run review · Q-0104 doc audit).

**Idea→plan promotion (owner directive).** The **reconciliation** routine — the one that reliably
fires — now does the idea→plan step the owner always intended: when the executable plans are running
low on real work, it reviews `docs/ideas/` and promotes the best owner-aligned idea into a **fully
complete, executable plan** scoped against the repo's house style, indexed so it becomes the
executor's next ▶ Next action. This is the "any idea easily becomes a plan becomes reality" lever for
the owner's goal of *less hands-on planning* — drop a one-word idea, trust the loop to realize it.

**Home:** `docs/operations/hermes-dispatch-bridge.md` (dispatch prompt) · `docs/operations/autonomous-routines.md`
(night-executor + reconciliation prompts) · `docs/owner/ai-project-workflow.md` §10. **The in-repo
prompts are the canonical mirror — the maintainer re-pastes the final text into each routine's console
config for it to take effect** (the console is the live source; the doc is the reviewable source of
truth).

---

### Q-0145 — Consolidate to 2 routines: dispatch absorbs the night-executor (2026-06-15)

> **DECISION 2026-06-15 (owner-directed in-session, applied directly).** Immediately after Q-0144 the
> owner: *"the dispatch will just take the job of both routines, they were already meant to do the same
> thing — the dispatch was just supposed to be more steerable while the night agent had a set prompt.
> Now I'll just use the one dispatch routine for everything except the reconciliation, so please turn
> both of their prompts into one, so we have a total of 2 prompts."*

**Decision / fix (this PR).** The **night-executor** and the **dispatch** routine always did the same
job — advance the plan. Dispatch is simply the more steerable one (it takes a work order) and the
fixed-prompt night agent added nothing it couldn't do, so they are now **one routine**. The two
prompts (already rewritten onto the identical 12-step lifecycle in Q-0144) are merged into the single
**dispatch** prompt (canonical home `hermes-dispatch-bridge.md`), which absorbed the executor's three
distinct bits: the "single execution routine" framing, `docs/health/bug-book.md` in the orient list,
and the bounded-continuation handoff. The routine fleet is now **2 prompts**: **dispatch** (all
execution) + **docs reconciliation**. The night-executor section in `autonomous-routines.md` is
replaced with a pointer; the fleet/label tables and prose are de-staled (executor/caretaker → dispatch).

**Trigger consequence (superseded same day by Q-0146).** This PR assumed the cadence would be driven
by **Hermes' VPS cron → `routine_fire.py`**, replacing the GitHub `schedule:` cron (proven to deliver
only ~1 run/night, hours late — run history 2026-06-13/14/15). Hermes then proved unreliable for the
cadence too, and the owner found a reliable way to set the **console Schedule** trigger — so the final
trigger is the console Schedule (Q-0146), not Hermes. See Q-0146.

**Home:** `docs/operations/hermes-dispatch-bridge.md` (the one execution prompt) ·
`docs/operations/autonomous-routines.md` (fleet table → 2 routines; night-executor section → pointer).
Owner re-pastes the merged dispatch prompt into the routine console; deletes the separate
night-executor routine.

---

### Q-0146 — Dispatch cadence = the console Schedule trigger, every 2h (2026-06-15)

> **DECISION 2026-06-15 (owner-directed in-session, applied directly).** Owner: *"hermes is proving
> unreliable for this, and the reason we did the actions in the first place was because I couldn't
> correctly set the schedule time, but now I found a way to make that work."* The original move to
> Hermes-dispatch (Q-0136/Q-0145) existed only to work around the owner not being able to set the
> Claude Code console **Schedule** trigger; once that was solved, the simpler path won.

**Decision.** The **dispatch** routine's cadence is the Claude Code console **Schedule** trigger,
firing every **2 hours** — cron **`0 */2 * * *`** (UTC), owner-enabled 2026-06-15 for the first
autonomous day. A scheduled fire carries **no work order**, so the routine advances the next plan
slice from `current-state.md` ▶ Next action (the dispatch prompt's "empty work order → take the next
real plan slice" path handles this with no prompt change needed). The API (`/fire`) trigger stays for
**on-demand** work-order fires (a `/bugreport`, a phone request). This **supersedes** the
Hermes-VPS-cron / GitHub-`schedule:` cadence plan (both proved unreliable: GitHub `schedule:` delivered
~1 run/night hours late; Hermes proved unreliable for cadence). The legacy
`.github/workflows/executor-nightly.yml` was **removed 2026-06-15** (owner deleted the night-executor
console routine; the workflow followed).

**Prompt review (owner asked, "I don't think it needs changes").** Correct — functionally none: the
scheduled (no-work-order) fire routes through the existing empty-input path → advance the plan. Only
two self-description references were stale ("Hermes cron" → console Schedule); de-staled in this Q's
PR. Owner fixed the console-pasted prompts directly; this PR brings the in-repo mirrors + docs to match.

**Home:** `docs/operations/hermes-dispatch-bridge.md` (prompt intro + step 8 + Maintainer setup) ·
`docs/operations/autonomous-routines.md` (fleet table · Stage-1 note · trigger note · timing caveat) ·
`docs/current-state.md` stamp-line. **Owner action — DONE:** `executor-nightly.yml` removed
2026-06-15 (the last legacy trigger).

### Q-0147 — myprofile PR C: may a public bot DM strangers at join-time? (onboarding gate) (2026-06-16)

> **DECIDED 2026-06-16 (owner, in-session).** **No join-time DM — onboarding is in-guild only.**
> Standing DM policy the owner set here: **all profile/onboarding DMs are opt-in and never fire on
> join.** The *only* DMs that may be sent without the recipient opting in are **moderation/warning
> DMs**, and only when the **server owner enables them** with a **clear way to configure which
> actions trigger a DM** — a separate feature, captured as
> [`server-owner-configurable-moderation-dms-2026-06-16`](../ideas/server-owner-configurable-moderation-dms-2026-06-16.md).
> PR C is un-gated with this shape in
> [`myprofile-foundation-plan`](../planning/myprofile-foundation-plan-2026-06-10.md) §4.3
> (in-guild `profile_welcome_hint`, off by default, **no DM path**).
>
> *Question, for the record (raised at PR B close, #940):* whether/how to surface the profile hub
> on join — DM vs in-guild vs nothing — and whether a public bot may DM strangers at all (Q-0080
> abuse posture). The agent recommended in-guild opt-in / no unsolicited DMs; the owner confirmed
> and broadened it into the standing policy above.

**The question (plan §4.3).** When a member joins a guild, should the bot proactively surface the
profile hub, and if so **how**:

1. **Channel:** a **DM** to the joiner, or an **in-guild** welcome (e.g. a line in the existing
   welcome embed / a system-channel nudge), or **nothing** (discoverable via Help only — the
   current state)?
2. **Abuse posture (Q-0080 stranger-grade):** this is a **public** bot. May it **DM strangers**
   at all on join? DMing unsolicited users is a Discord-flaggable pattern and a spam/abuse vector;
   the safe default is **in-guild only, opt-in**, never an unsolicited DM. Owner confirms the line.
3. **Copy + frequency:** one-time on first join? Re-show on rejoin? What does it say?

**Why it's a real gate (not a technical prerequisite the agent may just take).** Unlike a missing
build step, this is a **product + safety/abuse** decision with an irreversible-ish external footprint
(messaging users who didn't ask). It sits squarely in the Q-0080 stranger-grade envelope and the
"external publish / outward-facing" ask-first class — exactly what stays owner-decided.

**Recommendation (agent, for the owner to accept/override).** Default to **in-guild, opt-in,
no unsolicited DMs**: add a single discoverable line to the existing welcome surface pointing at
`/myprofile` ("set your preferences with `/myprofile`"), and never DM. This keeps the public-bot
abuse posture conservative while still closing the discoverability gap. If the owner wants a DM
path, gate it behind an explicit per-guild setting (default off) and a first-join-only guard.

**Home when answered:** `docs/planning/myprofile-foundation-plan-2026-06-10.md` §4.3 (un-gate PR C
with the decided shape) + this Q-block records the provenance.

---

### Q-0148 — the dispatch routine is never "docs only"; only reconciliation is (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly).** Testing whether Hermes
> could send work orders, Hermes fired a real one but stamped it **"CLASS: docs · this is a
> living-ledger reconciliation only; no runtime code or feature scope."** The owner: *"it's never
> docs only, only the reconciliation routine should be docs only, please update the repo in such a
> way that this is absolutely clear."*

**The error.** The fleet has exactly two routine prompts (Q-0145): the **dispatch** routine, which
does **ALL build work** (runtime code, migrations, tests, docs, fixes, dispatched features), and the
**docs reconciliation** routine, which is **docs-only** and is **auto-triggered** by a `reconcile`
issue. Stamping a *dispatch* work order "docs only / no runtime code / no feature scope" conflates
the *task's nature* with a *routine-level scope fence* — a category error that could make a build
run wrongly refuse the runtime work it exists to do.

**Decision / fix (this PR).** Make the one-way split unmistakable on both sides of the dispatch
bridge, and forbid the bad stamp at the source:
- The saved **dispatch prompt** (`hermes-dispatch-bridge.md` step 3) now states a work order's
  `CLASS:` / scope notes label the task's nature to pick the merge gate and **never** fence what the
  routine may touch; if a dispatch order is stamped "docs only", honor the task's real shape, not the
  stamp. *(Also fixed a real bug found there: step 8 had an accidental duplicate-paste of four lines
  that had ridden into the live routine system prompt.)*
- `autonomous-routines.md` — the docs/runtime-split paragraph + fleet framing now say loudly: the
  dispatch routine is **never** docs-only; "docs-only" is **exclusively** the reconciliation lane.
- **Hermes' `superbot-dispatch` skill** (`hermes-skills/dispatch.md`) — a CLASSIFY note + a RULES
  bullet forbid Hermes from ever scope-restricting a dispatch order, and from hand-dispatching a
  reconciliation / docs-only job as a build order (a clean ledger guard means there is nothing to
  reconcile anyway).

**Note on the test fire itself:** the dispatched task *happened* to be a genuine ledger
reconciliation, so the run (PR #942) built the right thing — but the "docs only / no runtime code"
framing was the wrong shape for a dispatch order regardless, which is what this Q corrects.

**Home:** `docs/operations/hermes-dispatch-bridge.md` (saved prompt) ·
`docs/operations/autonomous-routines.md` (split + fleet) · `docs/operations/hermes-skills/dispatch.md`
(the source of work orders). **Owner action:** re-paste the corrected dispatch prompt into the
routine console and the `superbot-dispatch` skill into Hermes' config (the in-repo copies are the
source of truth; the live copies must be synced to match).

---

### Q-0149 — Expand `.claude/settings.json` permission allow-list so routines don't stall on prompts (2026-06-16)

> **APPLIED — owner-directed in-session (the Q-0106 exception).** Not a DISCUSS proposal: the
> maintainer directed this change live (mid-routine, after a permission prompt interrupted a
> scheduled run), so per CLAUDE.md "the one exception is a change the maintainer directs in-session"
> it was applied directly. This Q-block records the provenance.

**Trigger.** A scheduled DISPATCH routine run hit a Claude Code permission prompt
(`grep … || echo … >> .git/info/exclude && git status …`) and **stalled** — an unattended routine
has no human to click "Allow", so a prompt silently wastes the whole run. The maintainer asked, from
the mobile app, to "make this get auto-accepted."

**Root cause.** `.claude/settings.json` already set `permissions.defaultMode: "bypassPermissions"`,
but the **Claude Code web / remote-execution environment does not honor `bypassPermissions`** (it
downgrades to a gated mode for safety). The effective lever is therefore the `permissions.allow`
list. The existing allow-list covered git + `python3.10` dev commands but **not** the common
read-only shell tools (`grep`/`cat`/`head`/`find`/`sed`/`awk`/`jq`/…), compound-command parts, or
`>>` redirect targets — so anything outside the narrow allow-list prompted.

**Decision (applied).** Expanded `permissions.allow` with the safe, frequently-used command surface
a routine relies on (read-only shell inspection, safe file ops `mkdir`/`touch`/`cp`/`mv`/`ln -s`,
more git read/local-history verbs, `python3.10 -c`/`scripts/*`/`tools/*`, `npx … @optave/codegraph`),
and added a `permissions.ask` list that keeps the **safety-brake** commands prompting (so a routine
stalls rather than runs them unattended): `rm`, `git push --force`/`-f`, `git clean -f`, `railway*`,
`sudo*`, `psql`/`pg_dump`/`pg_restore`, `curl`/`wget`, `docker*`. This matches the CLAUDE.md safety
brakes (never touch prod / DB / external-publish / force-history directly from a routine).

**Caveats / residual (recorded for the owner).**
1. **Takes effect next scheduled run, not this one** — settings load at session start.
2. **Not bulletproof for novel compound commands** — `allow` is prefix-matched per command; an
   unusual `A && B || C >> file` shape can still prompt if a part isn't covered. The allow-list
   reduces prompts to rare; it does not eliminate them for arbitrary shell.
3. **The fully-decisive lever is environment-level**, not this file: the Claude Code **web console
   → the routine's environment** can run the routine in an autonomous permission mode. That is the
   owner's console setting (outside the repo); this Q only widens the in-repo allow-list, which is
   the part an agent can change. If prompts still interrupt routines after this, set the
   environment's permission mode in the console.

**Home:** `.claude/settings.json` (`permissions.allow` / `permissions.ask`) + this Q-block.

### Q-0150 — Make the `.claude/settings.json` hooks cwd-robust (kill the cwd-deadlock trap) (2026-06-16)

> **APPLIED — owner-directed in-session (the Q-0106 exception).** The maintainer asked for the hook
> explanation, then directed "yes go ahead" to apply the fix. Applied directly to executable config;
> this block is the provenance. Implements the durable fix the `.session-journal.md` cwd-deadlock
> entry had been pointing at ("make the hooks use `$CLAUDE_PROJECT_DIR/scripts/…` — router Q-block,
> since hooks aren't self-edited per Q-0106").

**The trap.** Every hook command in `.claude/settings.json` invoked its script by a **relative path**
(`python3.10 scripts/<hook>.py`). The Bash tool's cwd **persists across calls**, so a single compound
`cd <subdir> && …` leaves cwd in that subdir; from there the PreToolUse hooks (which fire on **Bash,
Edit, AND Write**) resolve `<subdir>/scripts/<hook>.py`, which doesn't exist → `FileNotFound` → the
hook exits non-zero → the harness **blocks the tool call**. Because all three mutating tools share the
relative-path hooks, the session **deadlocks**: the very tools needed to `cd` back or patch anything
are themselves blocked, and an ordinary subagent inherits the same stuck cwd. (Hit live this session
*and* previously — it is the journal's documented "cwd-deadlock trap".)

**Fix (applied).** Prefix **every** hook command with a cwd guard that resolves the repo root
regardless of the stuck cwd, with no dependency on an env var that may be unset:
```
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}" && <original command>
```
- Prefers `$CLAUDE_PROJECT_DIR` (the documented Claude Code hook var) but **falls back to
  `git rev-parse --show-toplevel`** when it is empty/unset — and it *was* observed empty in the
  shell here, so the fallback is load-bearing, not decorative. `git rev-parse --show-toplevel` returns
  the repo root even when run from a stuck subdir (git searches upward).
- The `cd` runs in the **hook's own subshell**, so it never affects the tool's persistent cwd; it also
  fixes any *internal* relative paths the scripts use. All 7 hook commands updated (PreToolUse
  Bash + Edit|Write, PostToolUse Edit|Write + create_pull_request, Stop ×2, SessionStart).

**Proof.** Each wrapped command was pipe-tested **from a deliberately-stuck `disbot/` cwd** and exited
0 (`check_branch_freshness`, `claude_pre_edit`, `claude_post_edit`, `claude_pr_subscribe_reminder`,
`claude_stop_check`), confirming the exact failure scenario is now handled. JSON validated.

**Caveat.** Like all hook changes, it **takes effect next session** (hooks load at session start), so
the avoidance note in `.session-journal.md` stays useful until this ships and one fresh session
confirms it live; the journal entry is updated to mark the durable fix applied. The "never `cd` into
a subdir" habit remains good hygiene regardless.

**Home:** `.claude/settings.json` (`hooks`) + this Q-block; `.session-journal.md` cwd-deadlock entry
updated to "durable fix applied (Q-0150)".

---

### Q-0151 — Architecture-atlas review: unified atlas? root README? taxonomy enforcement? (2026-06-16)

> **ANSWERED 2026-06-16 — owner accepted the agent recommendations.** Owner: *"yes I agree with your
> recommendations, and the readme is not required but not off limits."* Raised by the owner-uploaded
> repo-architecture review (captured + cross-checked in
> [`docs/ideas/architecture-atlas-and-structure-review-2026-06-16.md`](../ideas/architecture-atlas-and-structure-review-2026-06-16.md),
> PR #957). Resolution:
> - **a (atlas):** build it thin, as a **companion** to `AGENT_ORIENTATION.md`, **CI-`--check` +
>   on-demand generate, body not committed**. Sequenced as PR 2 of
>   [`../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md`](../planning/extension-taxonomy-crosswalk-plan-2026-06-16.md).
> - **b (root README):** *not required but not off limits* — optional 5-line pointer-only README if a
>   public landing page is later wanted; the deliberate no-README posture otherwise stands. Not built now.
> - **c (taxonomy):** classify **all 43**, **CI-enforced** — but via a **curated overlay
>   (`architecture_rules/extension_roles.yaml`) + a `--check` guard**, *not* a registry schema bump
>   (lower risk; roles are editorial, not runtime; and the 10 most-interesting extensions have no
>   registry entry to put a field on). **SHIPPED in PR #958.** (Rationale in the plan §"Design decision".)
>
> The original DISCUSS framing + per-question agent recommendations are preserved below for provenance.

**Q-0151a — A thin unified atlas?** The review's flagship "per-file maintainer dashboard" is ~80%
already shipped (`context_map.py` + `wiring_map.py` + `review_scope.py` + the agent context packs).
The surviving delta is a **repo-wide, provenance-stamped index** with a single `--check` drift mode,
built by *composing* the existing scripts (never re-implementing them). If we build it:
**(i)** is the atlas the **primary** architecture entry point, or a **companion** to
`AGENT_ORIENTATION.md` (which stays the human/agent reading-order router)? **(ii)** do we **commit**
the generated Markdown/JSON to git, or keep it **CI-artifact-only**?
*Agent recommendation:* build it thin, as a **companion** (not a replacement — orientation is curated
intent, the atlas is generated facts), **CI-`--check` + on-demand generate**, do **not** commit the
generated body (commit only the generator + a provenance header), to avoid a new drift surface. It
overlaps the context-pack system, so confirm before building.

**Q-0151b — Revisit the "no root README" decision?** The review recommends a minimal root README
pointer. The repo made an **explicit decision against one** (`repo-navigation-map.md:51` — *"There is
intentionally no top-level README — docs/ is the documentation surface"*). Now that the repo is
public-era, a tiny GitHub-landing pointer (→ `AGENT_ORIENTATION.md` + `current-state.md`) may be worth
it. *Agent recommendation:* add a **5-line pointer-only** README (no content duplication) **iff** the
owner wants a public landing page; otherwise keep the deliberate no-README posture. Owner's call —
it overrides a stated decision.

**Q-0151c — How far to enforce extension classification?** The strongest finding: no taxonomy maps the
43 extensions ↔ 33 subsystems (the 10 non-1:1 are unclassified). Should classification cover **only
the 10 non-subsystem extensions**, or **all 43**? And should the `role` be **advisory metadata** or a
**CI-enforced** guard (a new `INITIAL_EXTENSIONS` entry must declare a role or be a registered
subsystem)? *Agent recommendation:* classify **all 43** (cheap, and partial taxonomies rot), role as a
registry field, **CI-enforced** so the gap can't silently re-grow — but this is a
`REGISTRY_SCHEMA_VERSION` bump, so it ships via its **own plan**, not a drive-by.

**Home when answered:** a `docs/planning/` plan for the taxonomy (Q-0151c) + atlas (Q-0151a) if
approved; the README decision (Q-0151b) records here + `repo-navigation-map.md`. The capture doc holds
the full evidence and routing table.

---

### Q-0152 — Act on the autonomous-run review: run-report footer · ledger guard-exemption + drift line · bug-fix-guard · auto-deploy correction (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly).** After reviewing the first
> overnight autonomous run, the owner directed implementing the loop-closing changes its self-audit
> kept flagging, and corrected two propagating errors. Recorded here per CLAUDE.md Q-0106 because one
> piece touches **executable config** (the SessionStart banner) — applied under the in-session
> exception (the owner is the live reviewer). The rest are docs/tooling (free rein), batched here for
> provenance. (Renumbered from Q-0151 → Q-0152 to yield Q-0151 to the concurrent #957 atlas block.)

**What shipped (PR #956):**

- **Run-report footer** (docs) — a required owner-facing `📤 Run report` block (`.sessions/README.md`
  + both routine prompts), with `⚑ Owner decisions needed` / `⚑ Owner manual steps` lines (`none`
  when empty) so Hermes rolls up what needs the owner instead of it evaporating into prose.
- **Ledger guard-exemption** (tooling) — `check_current_state_ledger.py` skips a self-referential
  reconciliation PR (`reconcil` in its merge subject); it can't list its own number, so its absence
  isn't drift. Kills recurring busywork (idea: `ledger-guard-exempt-reconciliation-prs-2026-06-16`).
- **SessionStart ledger-drift line** (⚠ **executable config** — Q-0106 exception) —
  `claude_session_summary.py` prints `Ledger : ⚠ N merged PR(s) not yet in current-state` at session
  start, fail-silent, so drift is seen *growing* rather than discovered only at close.
- **Bug-fix-ships-its-guard** (docs) — the bug-book convention now requires a fixed bug's stays-fixed
  guard to ship in the *same* PR (never deferred — the deathmatch #933 deferral three sessions flagged).
- **Auto-deploy misinformation fix** (docs) — corrected the false "needs a Railway prod deploy to
  clear it live" lines in `bug-book.md` + `current-state.md` (the bot **auto-deploys on merge**); the
  bug-book convention + run-report footer now forbid re-adding a phantom manual-deploy step. The
  legitimate authority-sense "Merge ≠ deploy" usages (prod-checks/restarts stay the owner's) are left.

**Provenance note:** the run-report footer was specified in
[`routine-system-improvements-2026-06-14`](../ideas/routine-system-improvements-2026-06-14.md)
§ "Priority 1" (filed, never adopted) — this adopts it. Q-0147 (the DM gate) was decided in the same
session — see its block.

**Home:** the files above + this Q-block.

### Q-0153 — Hermes efficiency: new skills (idea-spotlight · morning-briefing · dispatch-resolve) + a 6h interactive session auto-reset (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly).** The owner asked to make the
> Hermes control-plane agent more efficient with specialised skills and an automatic chat-session
> reset, and (via `AskUserQuestion`) chose the specific set below. Recorded for provenance per the
> CLAUDE.md working agreement (owner decisions get a home). All pieces are docs / Hermes-skill /
> stdlib-tooling — **free rein**, no executable-config (`.claude/settings.json` / hooks) touched, so
> no Q-0106 exception is needed; this block is the durable record, not an approval gate.

**What shipped (PR #959):**

- **`superbot-idea-spotlight`** (NEW scheduled skill, the headline ask) — picks **one** active
  `docs/ideas/` capture per day (deterministic, rotating, via `scripts/hermes/idea_spotlight.py`)
  and posts a card with **pros · cons/risks · options & expansions**, so the owner can mull it and
  **report a verdict at end of day**; the EOD reply routes through `superbot-intake`.
- **`superbot-morning-briefing`** (NEW scheduled skill) — one consolidated morning digest (health ·
  open PRs · CI · overnight routine activity · decisions waiting on the owner). Absorbs
  `repo-health`'s former daily schedule — the owner's explicit "**one message instead of several
  pings**"; `repo-health` stays a full on-demand traffic-light.
- **`superbot-dispatch-resolve`** (NEW skill) + **`scripts/dispatch_menu.py --json`** — resolves a
  vague "work on sector SX" into a concrete work order routed by the resolved executor. This is the
  **Hermes-wiring half** of `dispatch-resolution-json-hermes` (the **Q-0137 Thread 1 read-side**),
  greenlit here; the broader Thread-1 cron-backstop decision stays owner-undecided.
- **Interactive session auto-reset every 6h** — `scripts/hermes/session_reset.sh` + the runbook
  [`hermes-session-reset.md`](../operations/hermes-session-reset.md) (systemd timer, `OnCalendar`
  every 6h). Owner's rationale: "**never a long session, and the repo updates fast so old context
  isn't always valuable.**" Scheduled *skills* already run stateless, so this targets only the
  interactive chat thread.

**Owner manual steps (VPS, off-repo):** re-install the skills + SOUL.md and restart the gateway
(`install-skills.sh` → `install-soul.sh` → `systemctl restart hermes-gateway`); then wire the 6h
reset per the runbook (confirm the `HERMES_RESET_CMD` for your Hermes build — the one UNVERIFIED knob).

**Home:** `docs/operations/hermes-skills/{idea-spotlight,morning-briefing,dispatch-resolve}.md` ·
`docs/operations/hermes-session-reset.md` · `scripts/hermes/{idea_spotlight.py,session_reset.sh}` ·
`scripts/dispatch_menu.py` · `scripts/hermes/build_skills.py` (EXTRAS) · this Q-block.

### Q-0154 — Behind/conflicted PRs must not sit silently: auto-update behind + red-on-conflict (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly — ⚠ executable config, Q-0106
> exception).** Surfaced live: PR #959 stalled because 12 PRs merged during the work, leaving the
> branch `behind` main — and the owner pointed out this defeats the original intent, which was that a
> problematic branch should go **red so an agent sees and acts**, not sit green-and-unmergeable. I
> verified the actual behavior: a merge conflict/behind state is a *git property, not a test result*,
> so GitHub does **not** redden a check for it, native auto-merge does **not** auto-update a behind
> branch (no merge queue), and nothing in the repo turned conflicts red (born-red Q-0133 only covers
> *incomplete* session cards; the Q-0125 reconciliation sweep is only every ~30 PRs). The owner chose
> **build both** halves (via `AskUserQuestion`). Touches `.github/workflows/` (executable config), so
> recorded under the Q-0106 in-session exception (owner is the live reviewer).

**What shipped (PR #965; token hotfix #966; noise-reduction refinement as a follow-up):**

- **`.github/workflows/pr-auto-update.yml`** — on `push: main`, brings open non-draft `claude/*` PRs
  that are `BEHIND` up to date (`update-branch`, with `ROUTINE_PAT`) so they re-test against current
  main and auto-merge fires. Carve-outs (`needs-hermes-review` / `do-not-automerge`) are left alone.
  A branch that can't be cleanly updated (a real conflict) fails update-branch and is left for the
  guard. *Behind = handled silently.* (Would have prevented the #959 stall.)
- **`.github/workflows/pr-conflict-guard.yml`** — posts a **red `conflict-guard` commit status** on any
  `DIRTY` PR and clears it to green when resolved (skips `UNKNOWN` to avoid flapping). *Conflict = loud
  red.* Non-required status (visibility, not an extra merge gate — a DIRTY PR already can't merge), so
  **no branch-protection change is needed**. Uses the default **`GITHUB_TOKEN`** (it needs
  `statuses: write`, which `ROUTINE_PAT` is not scoped for — the #966 hotfix). Scope (the refinement):
  a PR's **own** push evaluates **only that PR**; the all-PR **sweep** runs only on `push: main` +
  schedule (when a PR can newly conflict) — the earlier sweep-on-every-PR was needless noise that made
  parallel sessions investigate a red check that wasn't theirs.

**Why `push: main` is the key trigger:** a conflict/behind state appears when *main moves* (another
PR merges) — which is not an event on the stale PR — so both workflows hinge on `push: main`, which
fires reliably on every merge. (GitHub `schedule:` cron is a laggy backstop only.)

**Owner manual steps:** none beyond what already exists — `ROUTINE_PAT` (auto-update) already has the
Pull requests + Contents write it needs for `auto-merge-enabler.yml`; `conflict-guard` uses the
`GITHUB_TOKEN` the workflow grants. Optionally make `conflict-guard` a *required* check if you want a
conflict to hard-block (not necessary — it already can't merge).

**Dogfooding tail (2026-06-16):** the guard's first run failed on its own PR (`bash -e` + a
`gh api` 403 because `ROUTINE_PAT` lacks `statuses: write`) and, being non-required, #965 merged it
broken to main → it red-flagged other sessions' PRs for ~6 min until hotfix #966 (token → GITHUB_TOKEN
+ errexit-safe). Then the owner flagged the sweep-on-every-PR noise → the scope refinement above.

**Home:** `.github/workflows/{pr-auto-update,pr-conflict-guard}.yml` ·
`docs/operations/autonomous-routines.md` § "PR mergeability keepers" · this Q-block.

### Q-0155 — Developer dashboard (personal website): the four shaping decisions (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly via `AskUserQuestion`).** The
> owner asked for a personal website / developer dashboard linked to the project (checklist, update
> tracker, bot-function catalogue, ideas/bug board, **public** bug reporting, multi-AI linking, project
> integration, and a secrets store that maps where each env value is used) and chose the four options
> below. Recorded for provenance per the working agreement (owner decisions get a durable home). The
> work is a new, **decoupled** `dashboard/` web app + docs + stdlib tooling — no `disbot/` runtime and
> no executable-config touched, so no Q-0106 exception is needed; this block is the durable record.

**Decisions:**

- **Link multiple AIs → a control board over the current flow** (pipeline stages + trigger the
  existing Claude routines via the `/fire` API + an agent activity feed). A live multi-provider
  dispatcher was the explicitly *deferred* alternative.
- **Secrets → usage map + manage values via Railway.** Railway stays the single source of truth (no
  second copy of secrets); the dashboard is a UI over its env vars, plus a static "where is each env
  var used" map.
- **Bug reports → stored in the dashboard AND mirrored to GitHub issues.**
- **Start → design doc + a read-only MVP this session.**

**Shipped (PR #967):** Phase 1 read-only MVP — a decoupled FastAPI app under `dashboard/` (function
catalogue, ideas, bugs, updates feed, public showcase) fed by `scripts/export_dashboard_data.py`,
deployable as a second Railway service. Phases 2–4 (auth + checklist + public bug form; env/secrets
usage-map + Railway management; multi-AI control board) remain in the plan.

**Home:** [`docs/planning/developer-dashboard-plan.md`](../planning/developer-dashboard-plan.md) ·
[`docs/ideas/developer-dashboard-2026-06-16.md`](../ideas/developer-dashboard-2026-06-16.md) ·
`dashboard/` · `scripts/export_dashboard_data.py` · this Q-block.

### Q-0156 — Dashboard live editor: edit help & command panels from the website (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly via `AskUserQuestion`).** Owner:
> *"I'd also like to be able to edit the help message and command panels directly from the website, so
> you can move buttons to wherever you want."* Recorded for provenance. The editor's bot-side half
> touches `disbot/` runtime, so it is **designed first** (this block + the plan doc) and built as its
> own focused PR(s) — not bundled into the read-only showcase work.

**Decisions:**

- **Edits change the live bot** (not a website-only mockup). Because the bot's audited-seam rule
  forbids bypassing `services.help_overlay_mutation`, the website edits the live bot **through the
  bot**, via a private-network control API the bot exposes over the existing seam — never by writing
  `help_overlay` rows directly (that would skip audit + leave the bot's overlay cache stale).
- **Help text & visibility first.** The per-guild Help overlay (hide / rename / re-describe + Home
  message) is already data-driven and audited, so the website editor is a second front-end over it.
  **Moving panel buttons is greenfield** (panels are hardcoded `@discord.ui.button`) and needs a new
  DB-backed panel-layout engine in the bot first — deferred to a later phase (L3).
- **Login = Discord OAuth** (ties identity to the servers the owner admins → per-server editing is
  naturally scoped; the bot re-checks `administrator` on every write).
- **Read-only showcase expansion → all four areas** (settings/config catalogue, permissions/access
  map, live bot status/health, games & economy). Settings catalogue + access map shipped first.

**Home:** [`docs/planning/dashboard-live-editor-plan.md`](../planning/dashboard-live-editor-plan.md)
(architecture + phased build L0–L3) · `services/help_overlay_mutation.py` (the seam it fronts) ·
`views/help/editor.py` (the in-Discord editor it mirrors) · this Q-block.

### Q-0157 — Edit settings from the website: global (owner) + per-server scopes (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session).** Owner: *"would it be possible to edit the
> settings from the website? It's fine if that has to trigger a redeploy. As bot owner give me the
> option to change things globally instead of only for the server, as well as a per-server option if
> available."* Recorded for provenance; the bot-side half touches the hot settings path, so it's
> designed first and built as a focused runtime PR.

**Decisions / findings:**

- **Both scopes wanted:** a **global** (bot-owner, all-servers) default **and** a **per-server**
  override. Per-server already exists (`guild_settings` KV); the **global layer is new**.
- **Design (mirrors `feature_flags` per-guild → global → default):** add a global row space
  (`guild_id = 0` or a `global_settings` table); change `get_setting` resolution to
  per-guild → global → caller default (one function, hot path → focused runtime PR); an audited
  `settings_mutation` seam; the website (owner auth) edits via the control API with a scope picker
  (global = owner-gated, per-server = admin-gated, re-checked bot-side).
- **"Redeploy is fine"** → with the DB global layer, **neither scope needs a redeploy** (it applies
  live); the redeploy path is only relevant to the code-default fallback, which is messier.
- **Prerequisite:** a **settings-metadata registry** (key → type/default/label/scope) — needed to
  render an editor and to enrich the read-only `/settings` page. Safe, additive; build first.
- Shares the **same auth + control-API foundation** as the help/alias editors (Q-0156).

**Home:** [`docs/planning/dashboard-live-editor-plan.md`](../planning/dashboard-live-editor-plan.md)
§ "Settings editor — global + per-server" · `utils/db/settings.py` · `core/runtime/feature_flags.py`
(the resolution pattern) · this Q-block.

### Q-0158 — The dashboard is the bot's main website; `/commands` becomes a management surface (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session).** Owner set the scope and added asks:
> *"this will be the main website for the bot — later a broader project-management site (review repo
> sectors like the AI memory system). It should integrate well with the bot, but the bot itself stays
> the top focus: everything must remain correctly manageable in the bot. The website is a shortcut to
> manage everything faster with more oversight. Each command should get its own alias box; it should be
> possible to enable/disable each command from the website; plus a search and a Manage button on every
> command and cog."*

**Decisions / findings:**

- **Scope:** this `dashboard/` site is the **main bot website**; a separate broader project site comes
  later. Standing principles: (1) the **bot stays the source of truth + top priority** (everything
  manageable in the bot itself); (2) the website **front-ends existing audited bot seams** — never a
  parallel system.
- **Enable/disable commands** → front-end **`services.command_routing`** (migration 036): per-guild,
  scope-aware **per-cog** enable/disable, already audited (`set_policy`). Per-*individual-command* is
  finer than the bot does today → a later extension; start at cog level.
- **Per-command alias box** (correction): the global `/aliases` form stays as broad search/quick-add;
  *additionally* each command gets its own alias box in `/commands`. Backing = the synonym layer.
- **`/commands` → management surface:** existing search + a **Manage button on every command and cog**.
  Read side (current aliases + routing state + buttons) builds now; write side lands with the
  control-API + auth foundation (Q-0156 L0–L2).
- This session shipped the **settings read-model**: `/settings` now surfaces each setting's typed
  `SettingSpec` (type/default/hint/choices) via `scripts/scan_setting_specs.py` — confirming the
  settings editor + metadata already exist in the bot (front-end them, don't rebuild).

**Home:** [`docs/planning/dashboard-live-editor-plan.md`](../planning/dashboard-live-editor-plan.md)
§ "Command management surface" + "Strategic framing" · `services/command_routing.py` ·
`services/settings_mutation.py` · this Q-block.

### Q-0159 — Free multi-user control panel: Discord-login identity, per-user config, bot-ready-first (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session).** Owner: *"we are building a **free-to-use**
> control panel of this bot, so we need verification set up — Discord-account login — then the website
> can see what your permissions are and for which guild/user the changes are. Everyone should be able
> to change it personally how they like, so we need not only per-guild memory of the configuration but
> also **per-user**. This was already the plan, but we should **not rush it — first the bot needs to be
> ready for this**."*

**Decisions / findings:**

- **Free multi-user:** the site is a public control panel (anyone with Discord login), not just the
  owner. Discord OAuth → identity + guild list; **the bot decides authority** per request.
- **Per-user config already exists** (don't rebuild): `user_participation` (migrations 027/028) +
  `services.participation_mutation` + `core/runtime/user_config.py` + the in-Discord profile editor
  (`views/profile/`). Per-guild exists too. The site front-ends both.
- **The real "bot-ready" gap is the control API + an identity→authority bridge** — the control API
  resolves `(user_id, guild_id)` to a member and runs the **existing** capability checks
  (`governance.capability.actor_holds_capability`), so the site shows only allowed controls and every
  write is bot-verified. The site stores only a session; no second source of truth.
- **Sequencing (owner: don't rush):** bot-ready first (control API → identity/authority bridge) →
  *then* the website Discord login + editors.

**Home:** [`docs/planning/dashboard-live-editor-plan.md`](../planning/dashboard-live-editor-plan.md)
§ "Free multi-user control panel" · `services/participation_mutation.py` ·
`governance/capability.py` · this Q-block.

### Q-0160 — Command enable/disable granularity: cog-level now, per-command later (2026-06-16)

> **DECISION 2026-06-16 (owner-directed in-session, applied directly via `AskUserQuestion`).** While
> building the `/commands` management surface (Q-0158), the open fork the handoff flagged was put to
> the owner: Q-0158 literally asked to *"enable/disable each command from the website,"* but the bot
> today routes only at **cog (subsystem)** level (`services.command_routing`, migration 036).
> Per-individual-command disable would be a **new, finer routing layer in the bot** (a new DB table +
> an enforcement hook in the dispatch path). Asked which direction the enable/disable affordance
> should take.

**Decision:**

- **Cog-level now, per-command later.** The website's enable/disable **front-ends the existing
  audited `command_routing`** (per-cog, scope-aware channel → category → guild → default-on, via
  `set_policy`) — no new bot runtime. **Per-command** enable/disable stays a **documented future bot
  layer**, not built now.
- **Read-side impact (this session):** the `/commands` Manage panels show **cog-level** routing state
  and front the synonym layer for the per-command **alias** suggest box; they do **not** imply a
  per-command on/off toggle. The live write side (toggling, live aliases) still lands with the
  control API + Discord OAuth (Phase 2), which the owner has not yet set up.
- Confirms the interpretation already recorded in Q-0158; this Q-block is its explicit owner sign-off
  so a later session doesn't reopen the fork.

**Home:** [`docs/planning/dashboard-live-editor-plan.md`](../planning/dashboard-live-editor-plan.md)
§ "Command management surface" · `services/command_routing.py` · `dashboard/templates/commands.html` ·
this Q-block.

### Q-0161 — Narrow the `rm` permission brake to recursive deletes so a routine's scratch-file cleanup never stalls (2026-06-16)

> **APPLIED — owner-directed in-session (the Q-0106 exception).** Mid-routine the maintainer saw the
> docs-reconciliation routine stall **twice** on permission prompts and directed: "resync to main and
> start over, also find out how to prevent this from happening again, add them to the settings always
> allow list." Applied directly to executable config; this block is the provenance. A direct refinement
> of Q-0149 (same problem, sharper root cause).

**Trigger.** The band-#960 docs-reconciliation routine stalled twice, each on a **compound** Bash
command that performed ledger surgery via a temp Python script and then cleaned it up — e.g.
`python3.10 _recon_ledger.py && rm _recon_ledger.py && python3.10 scripts/check_…` and
`git reset --hard origin/main; rm -f _recon_ledger.py; …`. The `git reset`, `python3.10 scripts/*`,
and root-level `python3.10 *.py` parts were all allowed; **only the `rm` of the scratch file** matched
the `permissions.ask` brake `Bash(rm *)` (Q-0149), and `ask` outranks `allow`, so the whole compound
command prompted — and an unattended routine has no one to click "Allow", silently wasting the run.

**Root cause (sharpening Q-0149 caveat #2).** Q-0149 deliberately kept **all** `rm` on the `ask` brake
as a safety measure. But the dangerous case is a **recursive** delete (`rm -rf <dir>`), not removing a
file or two — and routines legitimately create + clean up scratch files every run, so a blanket `rm`
brake guarantees a stall on the most ordinary cleanup. The brake was too wide.

**Decision (applied).** Narrowed the `rm` brake in `permissions.ask` to **recursive deletes only** —
`Bash(rm -r*)`, `Bash(rm -R*)`, `Bash(rm -fr*)`, `Bash(rm -fR*)` (plus `rmdir`) — and added explicit
`permissions.allow` entries for the safe, frequently-used cleanup surface: `Bash(rm -f*)`,
`Bash(rm /tmp/*)`, `Bash(rm _*)`, `Bash(python3.10 *)`, `Bash(python3 /tmp/*)`. Net effect: a
non-recursive `rm file` / `rm -f file` (and tracked files are git-recoverable anyway) no longer
prompts; an `rm -rf <dir>` **still** prompts (the genuine data-loss brake is intact). The other
safety brakes (force-push, `git clean -f`, `railway`/`sudo`/`psql`/`pg_dump`/`curl`/`docker`) are
unchanged.

**Behavioral complement (recorded for the next agent).** The deeper fix is to **not shell out for
file surgery at all** — prefer the Edit/Write tools (always allowed, no Bash brake) over a temp
`python3.10 _scratch.py && rm _scratch.py` dance; if a scratch script is unavoidable, write it under
`/tmp/` (now allow-listed) rather than the repo root. Captured in `.session-journal.md` recurring
problems.

**Caveats.** Same as Q-0149: takes effect next session (settings load at start); `allow` is
prefix-matched, so a truly novel compound shape can still prompt; the fully-decisive lever remains the
console environment's permission mode (owner-side, outside the repo).

**Home:** `.claude/settings.json` (`permissions.ask` / `permissions.allow`) + this Q-block;
`.session-journal.md` (recurring problems).

### Q-0162 — Finalized dashboard vision: the manifest spine + owner-zone future scope (2026-06-16)

> **DECIDED 2026-06-16 (owner question-panel — both forks chose the agent recommendation).** Raised while
> synthesizing the owner's uploaded deep-research report + Codex PR #998 into one north-star vision plan
> ([`docs/planning/dashboard-vision-finalized-state.md`](../planning/dashboard-vision-finalized-state.md)).
> These **two architectural/early-IA forks** were routed here because guessing wrong on them is expensive
> or hard to reverse; the other panel decisions (homepage, authority UX, first-write order, mobile depth,
> panel-editor timing, setup readiness) are **Q-0163**.

**Fork 1 — the manifest spine (go/no-go + priority).** Both external reviews recommend the bot build a
**typed runtime manifest** (command / panel / settings) at startup as the long-term source of truth for
dashboard metadata, demoting the AST scanner (`scan_commands.py`) to a *drift-detection* role. Today the
website's command/button metadata is AST-derived and "probably right" — fine for read-only docs, fragile
for *management* (the UI could offer a control the runtime can't honor). The manifest spine is the cure but
it's a real bot-side investment (a startup builder + a panel registry + reconciliation tests).

- *Plain-language why it matters:* it's the difference between a dashboard that *guesses* what's manageable
  and one that *knows*. It's also the hard prerequisite for any reliable command/panel **editor**.
- *Agent recommendation / safe default:* **yes, build it — but sequence it after OAuth + read-only
  workspaces and before live management of commands/panels**, so reliable manageability metadata exists
  exactly when the editors that depend on it arrive (vision-doc Phase D, before F/H).

**Fork 2 — owner-zone future scope.** Should the owner/developer zone stay **owner-only forever**, or be
designed now for later **delegated scopes** (e.g. observability-only · issue-triage · content-editing ·
runtime-control) for trusted operators/moderators? The report's point: this is "better decided early in the
IA than repaired late in permissions."

- *Plain-language why it matters:* if others will ever get limited platform access, the zone's routes and
  authority checks should be *scope-shaped* from the start; retrofitting roles onto an owner-only zone is a
  painful permissions rewrite.
- *Agent recommendation / safe default:* **build owner-only now, but keep the owner zone scope-shaped** so
  delegation is an additive grant later, not a rewrite. (No delegated roles built until the owner asks.)

**Decision (owner, 2026-06-16):** **both forks → the agent recommendation.** Fork 1: **build the manifest
spine, sequenced after OAuth/read-only workspaces (Phase C) and before live command/panel editing
(F/H).** Fork 2: **owner-only now, scope-shaped** for later delegated roles (no delegated roles until
asked). Applied to the vision-doc roadmap (Phase D) + § "The four zones".

**Home:** [`docs/planning/dashboard-vision-finalized-state.md`](../planning/dashboard-vision-finalized-state.md)
§ "The manifest spine" + § "The four zones" / "Roadmap" · this Q-block.

### Q-0163 — Finalized dashboard vision: homepage, authority UX, edit order, mobile, panel timing, setup (2026-06-16)

> **DECIDED 2026-06-16 (owner question-panel).** The remaining six dashboard-vision forks (the two
> architectural ones are Q-0162), answered in one panel pass so the
> [vision plan](../planning/dashboard-vision-finalized-state.md) is fully solidified. Preserved as
> asked + chosen.

| Fork | Owner choice | Applied |
|---|---|---|
| **Homepage** | **Hybrid router landing** — newcomers → product tour, logged-in → straight to workspace (not a pure product-marketing page). | vision § "Homepage (finalized)" |
| **Authority UX** | **Cautious edits, open info** — show edit controls only when near-certain allowed; show read-only info + the authority preview freely. | vision § "Security & authority model" |
| **First live-write order** | **Help → settings → aliases/routing → panels** (lowest architectural resistance first; global-settings runtime tier in parallel). | vision § config-capability map + roadmap F |
| **Mobile** | **Full management on mobile** — not just oversight; a first-class per-screen constraint on every editor. | vision § "Mobile (finalized)" |
| **Panel-layout editor** | **Last**, after the simpler editors (greenfield panel-layout model is the prerequisite). | vision roadmap H |
| **Setup readiness** | **Already complete & confirmed working** — Discord OAuth + the shared control token are set on Railway; phases C/E/F are **no longer owner-setup-gated**. | vision roadmap "Setup gate cleared" note |

**Notable shifts from the agent defaults:** homepage went **hybrid router** (not pure product-site), and
mobile went **full management** (not oversight-only) — both raise the design bar and are recorded as
binding intent for the vision. The setup-done answer **unblocks the whole live-editing path** (the write
side — control-API mutation endpoints #993 + OAuth/editors #996 — had already merged in parallel lanes).

**Home:** [`docs/planning/dashboard-vision-finalized-state.md`](../planning/dashboard-vision-finalized-state.md)
§ "Decisions (owner question-panel, 2026-06-16)" · this Q-block.

### Q-0164 — Planning depth: reconciliation plans the *full band* (depth ≥ cadence) + a low-backlog flag (2026-06-17)

> **DECIDED + APPLIED — owner-directed in-session (`AskUserQuestion`, 2026-06-17, the first
> unattended-routine-day review).** The owner observed routines reporting "running out of plans"
> while the bot/website clearly have lots left to build. Root cause found this session: the
> reconciliation pass fires every **30** PRs but planned only the next **~9** ("9 PRs" leftover from
> the old every-10-PR cadence) — so the buildable queue drained ~20 PRs before each refill. The owner
> chose **"plan the full band + flag when the backlog can't fill it."**

**Decision:** The reconciliation pass plans **enough genuine buildable work to reach the next pass
(depth ≥ the 30-PR cadence)** — as **larger multi-PR initiatives OR more slices**, whichever keeps
each a real change; **never pad to 30 with filler**. **If the idea backlog genuinely can't fill the
band**, that is the *signal*: promote what's honest, then raise a loud `⚠️ PLAN BACKLOG THIN` flag
(current-state ▶ Next action + the run-report ⚑ Owner-decisions line) so the owner drops ideas or a
dedicated planning session runs. This is how the owner stops needing to plan: the loop keeps itself
fed and tells him *early* when it can't.

**Home:** `.claude/CLAUDE.md` (reconciliation bullet) · `docs/operations/autonomous-routines.md`
(reconciliation prompt PLAN step) · this Q-block. Verified-signal follow-up: a disposable
`check_plan_backlog.py` ([agent-tooling shortlist](../ideas/agent-tooling-automation-shortlist-2026-06-17.md) §B).

### Q-0165 — Routines self-label their run type in the session log; the dashboard badges it (2026-06-17)

> **DECIDED + APPLIED — owner-directed in-session, 2026-06-17.** Owner: *"make the routines list
> whether they were a routine or not, just with a simple keyword at the end of their session log."*

**Decision:** Every session log's **📤 Run report** carries a **`Run type:`** line
(`routine · dispatch` / `routine · reconciliation` / `manual`). Both routine prompts set it; a manual
session writes `manual`. The **dashboard updates feed badges any log whose Run type contains
`routine`** (`scripts/export_dashboard_data.py` parses it → `/updates`), so the owner sees routine
work at a glance — which also serves his "use updates to see the work done through the routines" ask
(Q-0167).

**Home:** `.sessions/README.md` (footer spec) · `hermes-dispatch-bridge.md` + `autonomous-routines.md`
(both prompts) · `scripts/export_dashboard_data.py` (`_run_type`) · `dashboard/templates/updates.html` ·
this Q-block. Related: [`routine-activity-visibility-2026-06-14.md`](../ideas/routine-activity-visibility-2026-06-14.md).

### Q-0166 — Spotted docs/ledger drift is fixed on sight, not deferred to the reconciliation failsafe (2026-06-17)

> **DECIDED + APPLIED — owner-directed in-session, 2026-06-17.** Owner: multiple sessions noticed
> "ledger drift" but declined to fix it because "that is the job of the doc reconciliation" — *"that
> is not a reason to continue leaving the repo in a bad state."*

**Decision:** **Bugs-first applies to docs.** Any session that **sees** real drift (a wrong ledger
entry, a clearly-missing older merge, a stale pointer) **fixes it on sight**. The every-30-PR
reconciliation pass is a **failsafe for the comprehensive sweep + planning + next-band prep — not a
licence to leave drift already spotted**. The one exception is **benign newest-merge lag** (the 1–2
merges newer than the `Last reconciliation pass: #N` marker, which the next pass records); drift
*older* than the marker is a bug → fix now. (Pairs with the
[lag-vs-drift guard idea](../ideas/ledger-guard-benign-lag-vs-drift-2026-06-14.md), which makes the
`--strict` red unambiguous.)

**Home:** `.claude/CLAUDE.md` ("Bugs first, durably") · `hermes-dispatch-bridge.md` (step 6) ·
this Q-block.

### Q-0167 — The website's updates feed must auto-refresh (dashboard.json regenerated on merge) (2026-06-17)

> **DECIDED + APPLIED — owner-directed in-session, 2026-06-17.** Owner: the website's bug/idea/update
> lists are going stale; *"the updates are not actually updating because it's still stuck at one from
> a few days ago … this should ideally update automatically so I can also use it as a way to see the
> work done through the routines."*

**Decision (root cause + fix):** the committed `dashboard/data/dashboard.json` only regenerated at
the every-30-PR reconciliation pass, so the feed lagged ~30 PRs. A new **`dashboard-data-refresh.yml`**
workflow regenerates it on **every source-touching merge to `main`** (paths-gated + `[skip ci]` so it
can't loop) and commits it back — the dashboard (a `dashboard/`-only Railway service that can't see
the source dirs at runtime) then serves a current JSON. Disposable (Q-0105); the reconciliation regen
stays the cadence backstop.

**Home:** `.github/workflows/dashboard-data-refresh.yml` · `scripts/export_dashboard_data.py` ·
this Q-block. Generalization: [`generated-artifact-freshness-umbrella-2026-06-17.md`](../ideas/generated-artifact-freshness-umbrella-2026-06-17.md).

### Q-0168 — Hermes output → a shared plain-language house style (approved + rolled out) (2026-06-17)

> **DIRECTED + APPROVED + ROLLED OUT — owner-in-session, 2026-06-17.** Owner: Hermes
> "doesn't feel like part of the system yet," its output is "hard to read, filled with stuff that is
> unnecessary or hard to understand," *"the biggest problem right now is the message format"* — wants
> plain language, better grouping (some jargon fine "as long as I can understand most of it"). He
> chose **"draft one sample, then roll out."**

**Decision/state:** Root cause = **no shared house style** (each skill defines its output shape
inline, so reports read differently and internal jargon leaks). A **sample** (the morning briefing,
before→after, + 5 house-style rules) was drafted, **APPROVED 2026-06-17** (the owner compared it
against that morning's live briefing — "much cleaner and easy to read with clear sections," no
changes), then **ROLLED OUT same day**: the 5 rules are now the canonical
[`hermes-skills/_house-style.md`](../operations/hermes-skills/_house-style.md), and the owner-facing
output skills (morning-briefing · repo-health · open-questions · idea-spotlight · review-merge) were
rewritten to cite it (bottom-line-first, plain words, grouped, one screen) + rebuilt
(`scripts/hermes/build_skills.py`). **Owner manual step:** redeploy on the VPS
(`bash scripts/hermes/install-skills.sh`).

**Home:** [`hermes-skills/_house-style.md`](../operations/hermes-skills/_house-style.md) ·
`docs/operations/hermes-skills/*.md` · this Q-block.

### Q-0169 — Owner review inbox / communication website: capture-only now; dashboard board, issue-backed (2026-06-17)

> **DECIDED (capture-only) — owner-in-session (`AskUserQuestion`, 2026-06-17).** Owner wants a channel
> to **post ideas/cog-command reviews** that sessions read and act on, with a visible "is it fixed?"
> status — *"probably a very high-leverage thing"* for reviewability + owner↔agent communication.
> Eventually two sites (product + communication); near-term **integrate into the existing dashboard**.
> He chose **"capture as idea + plan only"** (don't build this session).

**Decision:** Captured as an idea + an executable plan. **Shape:** a dashboard **"Review board"**
backed by the existing labeled-issue / committed-markdown rail (a review = an OPEN item sessions read
like the bug book; resolved = closed/`RESOLVED (#PR)`). Phase 1 is read-only + zero owner setup;
Phase 2 (post-from-dashboard) shares the owner-paced control-API/OAuth write side; Phase 3 = public
submissions + the eventual standalone site. Also feeds the plan backlog (Q-0164).

**Home:** [`owner-review-inbox-2026-06-17.md`](../ideas/owner-review-inbox-2026-06-17.md) +
[`owner-review-inbox-plan-2026-06-17.md`](../planning/owner-review-inbox-plan-2026-06-17.md) ·
this Q-block. Related: Q-0159 (multi-user control panel) · the developer-dashboard idea.

### Q-0170 — Agent tooling: dedicated Claude skills + a UX-consistency linter + a repo-native discovery aid (2026-06-17)

> **DIRECTED (capture + flagship lane) — owner-in-session, 2026-06-17 (+ two follow-up messages).**
> Owner: we made Hermes skills but "never actually made skills for claude … a lot more is possible
> than we currently use … because I've never explicitly asked." Plus two concrete script asks:
> (a) *"something like CI but specifically to find inconsistencies"* — panels missing a back button,
> cogs not following the arch rules, cogs sending ephemeral follow-ups instead of editing in place;
> (b) *"something like codegraph or grimp but specifically built for our needs"* to help agents find
> files/information.

**Decision:** Captured as a **shortlist** an owner picks from — we *do* have `/pre-pr`,
`/session-close`, `/architecture-review`; candidate new skills (`/route-idea`, `/cog-review`,
`/plan-band`, `/fix-drift`) and scripts are listed. **The UX-consistency linter is the flagship
buildable lane** (its own idea + plan — one rule per PR, real backlog-feeding work for Q-0164). The
repo-native discovery aid is captured with a do-not-duplicate gate (must complement `context_map.py` /
`wiring_map.py` / CodeGraph / Grimp, not re-do them) and a prototype-against-real-questions check.

**Home:** [`agent-tooling-automation-shortlist-2026-06-17.md`](../ideas/agent-tooling-automation-shortlist-2026-06-17.md) ·
[`repo-consistency-linter-2026-06-17.md`](../ideas/repo-consistency-linter-2026-06-17.md) +
[its plan](../planning/repo-consistency-linter-plan-2026-06-17.md) · this Q-block.

### Q-0171 — Codex automated PR review: research the mechanism, then decide augment-vs-replace + merge authority (2026-06-17)

> **NOW LIVE — owner enabled it in-session, 2026-06-17** (mentioned: *"a function on ChatGPT that lets
> codex automatically review any PRs"*). The Codex GitHub connector is on and already auto-reacting on
> PRs (validated on **#1026** — a 👍 from `chatgpt-codex-connector[bot]`).

**Decision/state:** **LIVE** — it adds a **second, different-model reviewer** (serves the
anti-monoculture principle behind `needs-hermes-review`, Q-0117). **Observed:** a bare 👍 *reaction*
isn't readable via `get_reviews`/`get_comments` (separate API) — but a substantive Codex *review /
review comment* IS, and the **PR-activity subscription delivers Codex review comments into a watching
session**, so the loop can consume + fix what Codex flags. **Next (no longer "does it exist"):** (1)
check the connector for a "post a full review comment every time" mode (not just react) so its reasoning
is visible to the loop; (2) the **augment-vs-replace + who-holds-merge-authority** question still stands
for the owner (the Q-0082 spend cap + the morning-briefing rate-limit lesson apply).

> **ANSWERED 2026-06-19 (owner, question panel): augment only, NO merge authority.** Codex stays a
> second *advisory* reviewer; routines verify its flags against source and fix the real ones first
> (Q-0174); humans/Hermes keep merge authority. Matches the owner's "accept post-merge review" choice
> (Q-0180) and the anti-monoculture principle (Q-0117). Sub-question (1) — the "full review comment
> every time" mode — is subsumed by Q-0180 (auto-`@codex review` posted on the final head).

**Home:** [`codex-automated-pr-review-2026-06-17.md`](../ideas/codex-automated-pr-review-2026-06-17.md) ·
this Q-block. Related: Q-0117 (Hermes review-merge gate).

### Q-0172 — Open the idea→plan gate: ideas may become plans/builds anytime without approval, flagged for review (2026-06-17)

> **DIRECTED + APPLIED in-session (owner directive, 2026-06-17):** *"we can fix the plan shortage by
> simply removing the 'idea gate' … ideas can just be turned into a plan at any time without my approval,
> but it should be stated in the session log, so hermes or another chat, or me personally in the website,
> can easily see, filter and review those implementations."* Applied directly per the CLAUDE.md
> in-session-directive exception (Q-0106) — the owner is the live reviewer.

**Context:** The owner observed the plan backlog running thin (the Q-0164 case). Root cause wasn't only
the cadence — it was that genuine ideas (canonical example: **fishing**, the owner-ratified ecosystem-#2
verdict) never got promoted to plans, because the old rule ("a new idea is not a new priority" + the
Q-0114 phase gate) kept self-originated work parked behind owner approval. Mining, by contrast, is
*built* with only owner-gated slices left — so the shortage is specifically "ideas that never became
plans," exactly what this opens.

**Decision:** The **approval gate on idea→plan→implementation is removed.** Any agent may promote an idea
to a `docs/planning/` plan and build/ship it **at any time without owner pre-approval** — the work is
reversible, and *ideas exist to be built*. Preserved: (1) the **focus discipline** (a mid-stream idea
doesn't derail the *current* task — capture, finish, then promote); (2) the **classify-into-`docs/ideas/`-first**
habit (keeps the backlog reviewable/filterable); (3) the **safety brakes** (irreversible / external /
production stays ask-first — a *safety* brake, not the idea gate); (4) the **merge gates** (small
self-merges on green; SUBSTANTIAL → `needs-hermes-review`). The phase gate (`check_phase_gate.py`) is
demoted to **advisory-only** — a "bugs-first season" priority readout, never a block (this retires the
Q-0114 approve/deny gate for self-invented features).

**The one requirement — accountability:** every self-initiated promotion is flagged on the new
**`⚑ Self-initiated:`** line of the session-log run report (`.sessions/README.md`); the **dashboard
updates feed badges it** (`scripts/export_dashboard_data.py` → `/updates`) so Hermes, another chat, or
the owner on the website can see, filter, and review unprompted work.

**Surfaces changed:** `.claude/CLAUDE.md` (the idea bullet) · `scripts/check_phase_gate.py` (advisory
banner) · the dispatch routine prompt + skills (`hermes-dispatch-bridge.md`, `hermes-skills/dispatch.md`,
`scripts/hermes/skills/dispatch/SKILL.md`) · `docs/operations/autonomous-routines.md` ·
`hermes-control-plane.md` · `hermes-terminal-cheatsheet.md` · `hermes-skills/README.md` ·
`.sessions/README.md` (the ⚑ line) · `export_dashboard_data.py` + `dashboard/templates/updates.html`
(parse + badge).

**Home:** this Q-block · `.claude/CLAUDE.md` Working agreement. Related: Q-0114 (the retired phase gate),
Q-0164 (PLAN BACKLOG THIN flag), Q-0165 (Run type line — the ⚑ Self-initiated line is its sibling),
Q-0106 (in-session-directive exception).

### Q-0173 — Mining grid world: seed-deterministic (option #1), not literal Minecraft terrain (2026-06-17)

> **DIRECTED — owner-in-session, 2026-06-17:** asked *"is it possible to fetch a seed directly from
> Minecraft and use that as our actual grid?"* After a feasibility breakdown (no API fetches terrain; a
> seed is just a number; the spectrum = seed-as-RNG / Cubiomes biome-replication / full-block-gen), the
> owner picked **#1: "probably the best option."**

**Decision:** The grid Mine (mining-hub-redesign PR3) world model is a **seed-deterministic procedural
grid we generate ourselves** — any number ("seed") feeds our own generator, so `seed 12345` produces
the same world for everyone (deterministic · **shareable** · effectively infinite). This resolves the
plan's open "fixed vs procedural/infinite" question → **procedural, seed-deterministic.** It is *not*
literal Minecraft terrain: that would need either a reverse-engineered gen library (Cubiomes — biomes
+ structures only, a real C dependency; the *later* upgrade path if true Minecraft-shaped worlds are
wanted) or running an actual Minecraft generator (Java server + region files — too heavy for Railway,
rejected). Licensing stays clean — a seed is just a number; we ship no Minecraft code or assets.

**Still open (owner deciding — do NOT resolve unprompted):** ~~one shared grid vs. per-depth-level~~
→ **RESOLVED 2026-06-19 (owner, question panel): ONE shared seed-deterministic grid** (same world for
everyone, shareable — consistent with the Q-0173 intent).
→ **Movement / encounters — RESOLVED 2026-06-19 (owner, question panel):** the v1 grid ships with **free
movement, no encounters** (smallest surface, no new balance system). **Encounters ARE wanted as a later,
own-session layer** — the owner's shape: **depth-gated random encounters** ("after a certain depth you
can get random encounters, but not too many" → sparse, depth-gated, never spammy). A forward design note
for the encounters session; do **not** build it into the grid-navigation PR.
→ **Cell-yield → depth mapping — RESOLVED 2026-06-19 (owner, question panel): the vertical axis maps to
the existing depth bands** (down a row = today's deeper/richer band, so all tuned ore tables/balance +
the 'descend' metaphor carry over unchanged; horizontal = lateral variety within a band; each cell's
exact yield stays seed-determined). `utils/mining/world.py` (currently 1-D) keeps its band economy as
the Y axis.

**Home:** [`planning/mining-hub-redesign-2026-06-15.md`](../planning/mining-hub-redesign-2026-06-15.md)
§ "Mine — 3D grid navigator" · this Q-block. Related: Q-0172 (fishing/open-world is the sibling Explore lane).

### Q-0174 — Codex review integration: routines fix flagged-real issues first; Hermes scans PRs (issue-only) (2026-06-17)

> **DIRECTED — owner-in-session, 2026-06-17:** *"make sure the routines all check the previous PRs for
> any of codex's comments, the first priority of any routine should be to fix anything codex flagged,
> but not blindly… hermes on a 6H timer to check PRs and open an issue if necessary… before we do this
> we should define what a real bug is… for now until hermes has been proven… it just opens an issue and
> only dispatches on command."*

**Context:** Codex (Q-0171) is live and **catching real drift** — verified this session it flagged the
stale `/session-close` cadence, a roadmap "~9 PRs" line, and a mis-named session-card heading
(`Previous-slice` vs the checker-required `Previous-session`) — all real, all fixed. (The owner is
amazed a *code* reviewer spotted *docs* drift — evidence the repo is genuinely navigable.) But Codex
also produces **born-red false positives** (it reviews the card-first commit before the code lands) and
can run "make changes" tasks, so the loop needs a bar + a budget-aware consumer.

**Decision (plan: `planning/codex-review-integration-plan-2026-06-17.md`):**
1. **Routines check Codex first** — every routine's first priority: scan recent PRs for unresolved
   Codex/bot flags, **verify against source**, fix the real ones first; never blindly (Q-0120).
2. **The "real bug" bar** — verified-against-current-source · a genuine defect/contradiction (correctness
   · arch/ownership · docs-vs-code drift · security) · not a nitpick. Explicitly rejects the born-red
   timing class.
3. **Hermes 6H PR-check (spec; issue-only)** — a new `superbot-pr-check` skill (6H) opens a GitHub issue
   per real bug; **does NOT auto-dispatch** — dispatch only on command until Hermes is a proven
   dispatcher. **Why:** only ~15 routine fires/day (~12 dispatch, ~1–2 reconciliation) — too scarce to
   spend on false positives. Auto-dispatch is a later, separate owner decision.

**RESOLVED (owner, 2026-06-17/18):** the comment-only-vs-auto-PR question is **moot — Codex is
structurally comment-only.** It cannot push a branch or open a PR autonomously (a human must press
"create PR" in the Codex UI); its "make changes" output is a *comment* describing a sandbox diff, never
a repo change. **Decision: trial it as-is** (auto-review on). The only safeguard needed: **agents read
Codex's proposed edits in its *comment*, not in a phantom branch/PR** (plan Part A § "Where Codex's edits
live"). Still open — the `@codex review`-on-**final-head** tweak (codex idea doc) to land its *code*
reviews on the complete diff, not the born-red opener.

**Home:** [`planning/codex-review-integration-plan-2026-06-17.md`](../planning/codex-review-integration-plan-2026-06-17.md)
· [`codex-automated-pr-review-2026-06-17.md`](../ideas/codex-automated-pr-review-2026-06-17.md) · this
Q-block. Related: Q-0171 (Codex live), Q-0120 (verify bot output vs source), Q-0117 (Hermes review-merge gate).

### Q-0175 — Fishing v1 + the boat / open-world expansion (the unified-character world) (2026-06-18)

> **DIRECTED (design brain-dump) — owner-in-session, 2026-06-18:** the fishing / open-world vision,
> captured *"before I forget… this should give the planners something to do."* The owner is the designer;
> the plan captures his intent faithfully — build against his answers to the open questions.

**Decision (Phase 1 — buildable):**
- **Fishing v1:** **21 fish ranked by size**, **7 levels, 3 fish/level** — the starting rod/character
  catches the 3 smallest; each level unlocks +3 bigger fish (`3 × 7 = 21`). Scales later; leveling reuses
  the existing tier / `game_xp` systems.
- **Unified character + swappable gear types:** one character; **named loadout presets per activity type**
  (mining/fishing/exploration/…), each a deterministic saved slot ("put on fishing gear" swaps to it).
  **Gear is never required** — any activity works with any gear; matching gear only **increases bonuses**.

**Captured for LATER (Phase 2+, not now):** the **boat** as a second home base (stores rods; also for
exploration); **bounded boat travel** (short timer, locked-in — can fish, not land things, can't leave
till arrival); **real destinations** updating **coordinates + biome** (ties the seed-grid world Q-0173),
each with a **specialty** + bonuses, **some** location-locked eventually.

**Open (owner deciding — do NOT resolve unprompted):** → **RESOLVED 2026-06-19 (owner, question panel):**
catch mechanic = **instant deterministic roll for v1** (an interactive minigame is deferred to its own
later slice) · leveling = **both — a fishing skill (reuses `game_xp`) unlocks the size tier AND rod tier
boosts catch quality** (gear is still never *required*, only a bonus) · fish value/use = **sell + cook**
(a deliberate Phase-1 economy *reconnect* — it re-introduces a coin/consumable path that #1039 removed,
so it needs its own balance plan, **not** a silent revert). *Remaining sub-questions — agent-resolved 2026-06-19 per the owner's "if there's one clean option, just record it" directive (owner may override):*
- **Loadout-preset UI** → **reuse the existing mining Gear-panel pattern** (BaseView/HubView, the #702 gear UI) + a `!loadout` command, with **manual/explicit** preset swap for v1 (no surprise auto-swap; an auto-swap-on-activity toggle can come later). This is the only architecturally-consistent option (helper-policy + discord-views house style); a bespoke new UI would duplicate/violate it.
- **Boat "stuff" while traveling** → **stays Phase-2 deferred** (already the owner's stance); revisit when the boat/open-world lane is planned (ties Q-0173). Nothing to decide now.

**Home:** [`planning/fishing-open-world-expansion-plan-2026-06-18.md`](../planning/fishing-open-world-expansion-plan-2026-06-18.md)
· this Q-block. Related: Q-0172 (fishing = the canonical self-build), Q-0173 (the seed-grid world the boat
travels), the V-13/V-14 ecosystem vision.

### Q-0176 — DISCUSS: should `auto-merge-enabler` skip a PR already labelled `needs-hermes-review`? (2026-06-18)

> **PROPOSED — agent-surfaced (fishing dispatch run, 2026-06-18). Not applied — executable-config
> change (the workflow), so it ships as a proposal per CLAUDE.md.** *(Renumbered from Q-0175 → Q-0176 to
> avoid a collision with the owner's same-day directed Q-0175 above.)*

**Context:** the fishing PR #1033 was opened via the GitHub MCP (`create_pull_request`) and labelled
`needs-hermes-review` (Q-0117 — a substantial new ecosystem subsystem must not self-merge). Per Q-0127
an MCP/app-token PR should NOT trigger the `auto-merge-enabler` workflow — yet auto-merge **was** armed
on it (actor `menno420`, the enabler). The born-red session gate held the merge (the card was
`in-progress`), so nothing leaked, and the routine disarmed auto-merge manually. But the failure mode is
real: a session that flips its card to `complete` *before* noticing/disarming auto-merge on a
review-gated PR would let it merge **unreviewed**.

**Proposal:** the `auto-merge-enabler` workflow already excludes `do-not-automerge` (Q-0114) and
`needs-hermes-review` is meant to be a carve-out (Q-0117) — make that explicit and robust: **skip arming
auto-merge whenever the PR carries `needs-hermes-review` at arm time** (and re-check labels if the enabler
can be re-triggered), so a reviewer-gated PR is never armed in the first place. Defense-in-depth for the
born-red gate, not a replacement.

> **DEFERRED 2026-06-19 (owner, question panel).** Not applied now — the born-red session gate stays the
> single safeguard for the moment (it caught the #1033 case with no leak). Revisit only if the enabler
> actually arms a `needs-hermes-review` PR that then merges unreviewed.

**Home:** this Q-block. Related: Q-0117 (Hermes review-merge gate), Q-0123/Q-0127 (auto-merge-enabler arm
rules), Q-0114 (`do-not-automerge` carve-out), Q-0133 (born-red gate).

---

### Q-0177 — Repo-structure improvement: governance + supply-chain + CI baseline (2026-06-19)

> **DECISION 2026-06-19 (owner-directed in-session, applied directly).** The owner uploaded three
> external repo reviews and asked for a comprehensive plan to improve the repo structure. The agent
> cross-checked every recommendation against live source (the reviews are *input to verify*, not
> orders) and the owner chose, via in-session `AskUserQuestion`: **LICENSE = MIT** and scope = **plan
> + docs + CI config**. Recorded here per CLAUDE.md Q-0106 because part of it touches **executable
> config** (`.github/` workflows + `dependabot.yml`) — applied under the in-session exception (the
> owner is the live reviewer). The rest is docs (free rein), batched here for provenance. Full plan +
> verification table: [`docs/planning/repo-structure-improvement-plan-2026-06-19.md`](../planning/repo-structure-improvement-plan-2026-06-19.md).

**What shipped (this session's PR):**

- **Governance foundation** (root): `LICENSE` (MIT, holder "Menno van Hattum"), `SECURITY.md`,
  `CONTRIBUTING.md`, `CITATION.cff`.
- **Supply-chain / CI** (executable config — the Q-0106 exception): `.github/dependabot.yml` (weekly
  pip for root + `dashboard/` + github-actions), `.github/workflows/codeql.yml` (Python SAST,
  non-blocking), `.github/workflows/dashboard-ci.yml` (runs the previously-`importorskip`-skipped
  `tests/unit/dashboard/` + `mypy dashboard/`), `.github/ISSUE_TEMPLATE/` + `.github/PULL_REQUEST_TEMPLATE.md`.
- **Bug root-fixed while wiring dashboard CI:** a fresh install resolved `httpx 0.28`, which persists
  per-request cookies into the shared `TestClient` and broke 2 dashboard tests; made the fixture
  function-scoped (`tests/unit/dashboard/test_app.py`) → 65 pass. A live demonstration of the
  dependency-pin gap below.

**Routed for the owner (decisions, no rush):**

1. **Dependency-lock strategy** — runtime deps are version *ranges*; fresh installs drift (the
   `httpx 0.28` break is the worked example). Options: (a) `pip-tools` compiled lockfiles for bot +
   dashboard; (b) tighten ranges to known-good ceilings; (c) keep ranges + rely on Dependabot + the
   new dashboard CI. *Agent rec:* (a) for the dashboard first. Ships as its own 2-PR plan once chosen.
   **→ DECIDED 2026-06-19 (owner, question panel): (a) — `pip-tools` compiled lockfiles, dashboard
   first (bot next). Ships as its own 2-PR plan.**
2. **Control-API hardening depth/timing** — request signing (HMAC + timestamp), idempotency keys,
   token rotation. Owner-paced (control-API writes are the "don't rush" zone); sequence behind the
   dashboard live-editor write lane.
   **→ Correctness baseline recorded 2026-06-19 (agent, per the owner's "single clean option / safe
   code" directive):** this is a *security correctness* gate, not a product preference — the
   control-API **write** surface must **not** be publicly exposed until it has authenticated,
   replay-resistant requests (HMAC + timestamp or equivalent) **+** write idempotency keys **+** a
   token-rotation/revocation path. It rushes nothing (public exposure is itself gated); it is folded
   **into** the Q-0179 security-review-gated per-server-panel migration as that migration's entry bar.
   The exact mechanism is a detail for the security-review session.
3. **Pointer README (Q-0151b reprise)** — owner already said "optional, not built now." Offer stands;
   a ready 5-line pointer (→ `docs/AGENT_ORIENTATION.md` + `docs/current-state.md`) can ship the moment
   the owner wants a public landing page.
4. **Roadmap → labeled-issue mirror?** — the reviews push GitHub Issues/Projects for planning; the
   repo deliberately keeps planning in `docs/` + the dashboard. *Agent rec:* do NOT adopt Projects
   wholesale; an optional lightweight roadmap→labeled-issue mirror only if public visibility is wanted.
   **→ DECIDED 2026-06-19 (agent-recorded, single clean option per the owner's directive): do NOT
   adopt.** It would create a *second* planning source of truth (against the repo's binding "one
   source of truth" principle → drift), and its only upside — a public roadmap — is **already**
   delivered by the website two-site split (the dev site is public read-only; community input flows
   `/submit` → moderation → the existing GitHub-issue mirror). Adds drift with no unmet need. Re-open
   only if a concrete public-roadmap-as-issues need appears.

**Owner manual steps (repo Settings / off-repo — cannot be done from a PR):**

- Enable **Dependabot alerts + security updates** (Settings → Code security).
- Enable **private vulnerability reporting** (Settings → Code security) so `SECURITY.md` route 1 works.
- Optionally add **`codeql`** + **`dashboard-ci`** to **branch protection / required checks**.
- Confirm the **MIT copyright holder** name in `LICENSE`.

**Home:** the [plan](../planning/repo-structure-improvement-plan-2026-06-19.md) + this Q-block. Related:
Q-0151 (architecture-atlas review — no reorg; root-README posture), Q-0106 (executable-config exception),
Q-0105 (disposable-tooling discipline), gap-analysis §6 (toolchain-rot watch — closed by Dependabot).

---

### Q-0178 — Website two-site split: bot site vs dev/repo site (2026-06-19)

> **DECISION 2026-06-19 (owner-directed in-session, via the question panel).** After the ultracode run,
> the owner directed splitting the single developer dashboard into **two audience-targeted sites** and
> asked for the required planning output for the next session. The product/privacy/topology choices below
> were made by the owner via `AskUserQuestion`; they are the binding constraints the next planning session
> must honor. Full brief: [`docs/planning/website-two-site-split-planning-brief-2026-06-19.md`](../planning/website-two-site-split-planning-brief-2026-06-19.md).

**Decisions (the four choices):**

1. **Bot site** — **public + dynamic (hybrid:** regenerated content + a few live status widgets). For
   Discord users: command reference, feature showcase, bot changelog, status, and a public submission form.
2. **Public submissions** — **DB intake → owner approves on the dev site → approved ones mirror to GitHub
   issues** (reuse the `.github/ISSUE_TEMPLATE/` shapes). *Not* direct-to-GitHub and *not* a raw public
   feed — moderation gate first.
3. **Dev site** — the current dashboard, repurposed: **all pages public read-only**, owner-gated for
   **edits** (existing Discord-OAuth owner auth). **Hard constraint:** public read-only must never expose
   secret **values/tokens** — names + status only (env-var names are already public; values are the line).
4. **Topology** — **2 Railway services**: repurpose `dashboard/` as the dev site + a **new** lightweight
   public bot site. Preserve the dashboard's existing decoupling (no bot imports; reads generated JSON).

**Still open → now resolved (2026-06-19, via the question panel + plan §7):** domains/branding —
**deferred** (no domain yet; build on Railway URLs, owner sets DNS at cutover); the exact live-widget data
source — **generated build-meta for v1**, the live dev-site aggregator deferred behind the control-API
public-exposure security review (the public site never reads the private control API); the submissions DB
store — **a separate, dashboard-owned Postgres** (INSERT-only role for the public site). The per-server
control-panel placement fork is **Q-0179** (decided: → bot site). Defaults + rationale live in plan §7.

**Home:** the [planning brief](../planning/website-two-site-split-planning-brief-2026-06-19.md) + this
Q-block; idea capture [`website-two-site-split-2026-06-19.md`](../ideas/website-two-site-split-2026-06-19.md).
Related: the developer-dashboard initiative + Q-0155/Q-0156 (dashboard auth/live-editor lane).

---

### Q-0179 — Website split: where does the per-server control panel live? (2026-06-19)

> **DECIDED 2026-06-19 (owner, via the question panel): option (2) — the per-server control panel's home
> is the BOT SITE.** The owner views per-server management as a bot-**user** feature, not a dev/engine-room
> one: server owners manage their server from the bot site rather than the dev dashboard. Surfaced by the
> website two-site-split *plan* (#1100, §7.4), which grounded the fork against the live dashboard; Q-0178's
> "still open" list did not include it. Recorded into plan §1 / §2.4 / §4.4 / §7.4.

**The fork.** Q-0178 (decision 3) says the dev site is "owner-gated for edits (existing Discord-OAuth
owner auth)." But the *existing*, already-shipped, already-audited `/admin` control panel is
**multi-user**: *any* Discord user signs in and edits the servers **they** administer (the bot re-checks
each editor's live authority per guild — the browser is never trusted). So "owner-gated" as written does
not match what is built. Two readings, materially different products:

1. **Keep the existing multi-user per-server control panel on the dev site (v1 — agent recommendation).**
   Zero migration; already built + audited; "owner-gated" reads loosely as "edits require the OAuth gate
   and the bot is the authority." The **new** owner-only surfaces are moderation + env-value mgmt + the
   control board. Lowest-risk, no-downtime.
2. **Treat the per-server control panel as a bot-USER feature → move/mirror it to the public bot site.**
   Cleaner audience separation (a server owner managing their server is a bot user, not a developer), but
   it is migration + re-auth work and re-opens the public-surface security review for the live editors.

*Agent recommendation had been (1) for v1; the owner picked (2).*

**Decision + secure realization (agent judgment on the *how*, per "approving a goal approves the path").**
The owner picked (2). Because (2) places OAuth + a control-API-writing surface on the user-facing side, the
build realizes it as a **gated "manage my server" surface isolated from the secret-free public marketing
pages** (its own service/router under the bot-site domain) — so a compromise of the public marketing
surface cannot reach `CONTROL_API_TOKEN`. The invariant *"the public marketing surface holds exactly one
secret (the INSERT-only submissions DSN)"* is preserved by **isolation** rather than by **site**. The
multi-user, bot-is-the-authority model is unchanged (the panel was never owner-only; the **owner-only**
ring stays on the dev site for submission moderation + env-value mgmt + control board). **Prerequisite:**
this is exactly the scope of the control-API public-exposure security review the owner flagged (Q-0178
still-open #2 / plan §3, §7.2) — that review gates the panel-migration slice. The first additive build wave
(marketing + `/submit` + moderation + GitHub mirror) proceeds with no secrets on the public surface; the
existing dev-site panel keeps serving until its migration slice ships (no gap). *If the owner instead wants
a single merged app, that supersedes the isolation recommendation — say so.*

**Sibling implementation defaults — also decided 2026-06-19 (plan §7):** bot-changelog source = **curated
`docs/bot-changelog.md`** (§7.5; **seed it from the shipped-feature/ledger history so it launches with
real highlights** — owner, question panel, 2026-06-19); public-form spam = **honeypot + rate-limit for
v1**, captcha only if abuse appears (§7.6).

**Additional website-wave decisions — 2026-06-19 (owner, question panel):**
- **v1 launch-wave content (must-haves):** the **command reference** + the public **`/submit` form** +
  the **bot changelog**. The feature showcase + live status widget are *not* v1 — they follow once the
  core lands.
- **Control-API public-exposure security review** (the prerequisite that gates the Q-0179 per-server
  control-panel migration): route it through an **external / Codex security pass** plus a human
  sign-off, after the first additive wave ships. Records into plan §3 / §7.2.

**Home:** the [plan §7](../planning/website-two-site-split-plan-2026-06-19.md) + this Q-block. Related:
Q-0178 (the four decided choices + its own "still open" list), Q-0155/Q-0156 (dashboard auth/live-editor).

### Q-0180 — Codex reviews the final head: auto-post `@codex review` when the session card flips to complete (2026-06-19)

> **DIRECTED + APPLIED in-session (owner, 2026-06-19):** the owner asked whether Codex re-reviews a PR
> after the final commits and whether to "make every final push mention @codex in the PR for a forced
> review." Investigated → confirmed the gap → owner picked **the automated Action** + **accept
> post-merge review**. Applied directly per the CLAUDE.md in-session-directive exception (Q-0106) — the
> owner is the live reviewer. *(This was the long-standing "still open" item from Q-0171/Q-0174 + the
> #1031 session idea — now built.)*

**Context (verified empirically this session on #1097/#1100):** Codex's auto-review fires on exactly
three events — **PR opened · draft marked ready · a `@codex review` comment**; **a plain push is NOT a
trigger.** In the born-red flow (Q-0133) the PR opens on the **card-first commit before the code lands**,
so Codex permanently reviews the *incomplete opener* and **never re-reviews the final head** — and it
re-flags the born-red card itself ("mark the card ready / implementation missing"). Direct proof: on
**#1097** Codex left a **P1 "mark the session card ready before merge"** on the opening commit
`51b0a6e…` (a pure born-red false positive, now `is_outdated`) and never reviewed the final head
`da4df4f…`; same shape on #1100.

**Decision:** A new workflow **`.github/workflows/codex-final-review.yml`** posts **`@codex review`** the
moment a `claude/*` PR's **session card flips to a ready status** — the same born-red signal the merge-gate
keys off (`scripts/check_session_gate.py --require-ready-card`, added this session), i.e. the deliberate
final commit. This makes Codex evaluate the **complete diff** instead of the born-red opener. Idempotent
(a hidden `<!-- codex-final-review -->` marker → posts at most once/PR); carve-outs mirror
`auto-merge-enabler` (never fires on `needs-hermes-review` / `do-not-automerge`).

**The merge race — accepted (owner choice):** the card-flip-to-green is also what lets auto-merge fire, so
the `@codex review` comment often lands as the PR is merging; Codex's review then posts on the
**merged** PR. That is fine by design — **routines already scan recently-merged PRs for Codex comments
and fix the real ones first (Q-0174)**. So this is a *second reviewer that catches things for the next
session*, not a pre-merge gate (the owner explicitly chose "accept post-merge review" over holding the
merge for an external bot's latency).

**Reliability (Q-0105):** UNVERIFIED — watch the first few PRs to confirm it fires exactly once, on the
final head, and that Codex re-reviews the complete diff. Delete the workflow if it misfires or is chatty;
`@codex review` can always be typed by hand.

**Home:** `.github/workflows/codex-final-review.yml` · `scripts/check_session_gate.py` (`--require-ready-card`)
· [`codex-automated-pr-review-2026-06-17.md`](../ideas/codex-automated-pr-review-2026-06-17.md) · this
Q-block. Related: Q-0171 (Codex live), Q-0174 (routines check Codex first; the post-merge consumer),
Q-0133 (born-red card = the trigger signal), Q-0120 (verify bot output vs source).

### Q-0181 — Verify docs/claims against the *code*, not their own badges: the ground-truth audit protocol + plan-code-drift check (2026-06-19)

> **DIRECTED + APPLIED in-session (owner, 2026-06-19):** after the 2026-06-19 review found two plans
> (A3 `games-economy-faucet-sink-diagnostic`, A4 `p0-2-content-free-media-diagnostics`) whose code had
> shipped but were still badged `plan`, the owner asked *why* the earlier docs-cleanup didn't check each
> plan against the code, and for a durable way to force ground-truth verification. Applied directly per the
> CLAUDE.md in-session-directive exception (Q-0106) — the owner is the live reviewer.

**Root cause:** *"make the docs correct / up to date"* was executed as **internal consistency** (routing,
reachability, obvious-stale badges) rather than **truth against the code**. 5 of the task's 6 points are
doc-organisation, so "completed/outdated" inherited the docs-only reading; the rebadge-on-ship convention
relies on a human remembering, and nothing re-derived badge truth from code. Same failure class as the
shallow ultracode-review verification (cheap proxy over ground truth) and the #763 / #1125 ledger checkers.

**Decision — two artifacts:**
- **`docs/operations/ground-truth-audit-protocol.md`** — the reusable contract for any "verify / make
  correct / audit" task: verify against the code at a pinned commit (never a badge / PR-title / self-report),
  read every file in scope (fan out auditors for breadth), cite `file:line`, treat a badge as a claim to
  *disprove*, "done fast = red flag." Template instance: `docs/audits/repo-wide-audit-2026-05-29.md` (the
  22-auditor fan-out the owner pointed at as the depth bar).
- **`scripts/check_plan_code_drift.py`** — automates the badge-drift slice: flags every `plan`-badged doc
  whose named implementation already exists in `disbot/` (`STRONG` = named file + plan-specific symbol).
  Advisory; `--strict` to gate once trusted. Catches A3/A4 automatically; narrows 36 plans → ~7 candidates.

**Reliability (Q-0105):** the check is UNVERIFIED — heuristic; a plan may *extend* existing code, so hits
are review candidates, not proof. Confirm across a few sessions; **delete if noisy.**

**Applied (owner-directed in-session 2026-06-19):** (1) the check now runs in `/session-close` Step 4 (the
quality gate) so every session surfaces its own rebadge candidates — and **A3/A4 were rebadged `historical`
on the spot** (both SHIPPED in #1044, verified present + wired + tested). **Still proposed (owner to
greenlight; executable-config zone, Q-0106):** (2) a diff-aware Stop-hook step mapping a session's touched
`disbot/` files → the plans that name them → "rebadge if you shipped it" (it edits the Stop hook in
`settings.json`, so it waits for an explicit greenlight + a watched first fire).

**Home:** `docs/operations/ground-truth-audit-protocol.md` · `scripts/check_plan_code_drift.py` · this
Q-block. Related: Q-0104 (session-close doc audit), Q-0120 (verify bot output vs source), Q-0107
(reconciliation pass), Q-0166 (fix drift on sight).

---

### Q-0182 — DISCUSS: the federated Explore-hub world model — four open design questions (2026-06-19)

> **PROPOSED — surfaced by the band-#1140 reconciliation pass** from the owner's 2026-06-19
> brainstorm ([`ideas/explore-hub-federated-world-2026-06-19.md`](../ideas/explore-hub-federated-world-2026-06-19.md)).
> Routed for live owner review per the owner's #1140-fire directive ("surface the open questions
> … into the question router (DISCUSS lane)"). The spine those answers do NOT gate is already
> planned ([explore-hub plan](../planning/explore-hub-federated-world-plan-2026-06-19.md), Q-0172).
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → explore-hub plan.** Q1 (what the hub *is*):
> **flat Discord `HubView` router first; the map/biome/location layer stays a deferred layer** (the plan's
> existing sequencing — build the flat router, treat the map as later). Q2–Q4 (survival-overlay attach ·
> subsystem docking · cross-game-identity richness) were **not** put to the panel — they gate only the
> deferred layers and ride on the plan's defaults until that layer is greenlit.

**Context:** the owner wants one world where each subsystem (mining/fishing/pets/survival) is both
part of a shared world *and* its own complete game. The progression model (three XP tracks: message
XP → AI-DM negotiation; global game XP; per-game XP) and the hybrid-gear direction are **decided**
(idea doc § "Progression & gear model"). What remains undecided is the **world's shape**:

1. **What the hub *is*** — a flat Discord `HubView` that routes into each game (Mine · Fish ·
   Explore · …), **or** a richer **map/biome/location** model where destinations gate which game is
   reachable where? (The plan builds the flat router first and treats the map as a deferred layer.)
2. **How the survival/adventure overlay attaches** without forcing it on cozy players — difficulty
   modes (Easy ≡ today, byte-identical, per the rpg-survival plan), opt-in stakes, optional quests?
3. **Where each existing subsystem docks** into the hub (the mining-hub redesign Option A already
   split into Character + Explore sub-hubs — the Explore world hub is the parent of those).
4. **Cross-game identity** — a single profile characterizing a player across games as the world's
   front-end. (The plan builds a read-only cross-game card; the question is how rich it should be.)

**Agent note:** these gate the *deferred* layers only (gear auto-equip, survival overlay, biome
map). The ungated spine — top-level Explore hub + world registry + the global/per-game XP split —
is buildable now and planned. **Home:** the explore-hub plan + this Q-block. Related: Q-0175
(fishing), Q-0040 (AI dungeon master from bounded menus), Q-0080 (stranger-grade identity).

---

### Q-0183 — DISCUSS: the AI correction-report → audience-routed ticket service (plan-the-questions-first) (2026-06-19)

> **PROPOSED — surfaced by the band-#1140 reconciliation pass** from the owner's 2026-06-19
> brainstorm ([`ideas/ai-correction-report-and-ticket-service-2026-06-19.md`](../ideas/ai-correction-report-and-ticket-service-2026-06-19.md)).
> The owner explicitly flagged this as **needing its own extensive session — capture/route only,
> NOT a build plan yet** (#1140-fire directive: "the AI-ticket service stays plan-the-questions-first
> — don't write its build plan yet, just route its questions"). The *board* it writes into is
> planned separately ([feedback-board generalization](../planning/feedback-board-generalization-plan-2026-06-19.md)).

**The vision:** when a user corrects the AI (today it can only deny/acknowledge), let the AI **file
the correction for review**, growing into an **AI ticket service** (users send bug reports · server
problems · moderation issues *through* the AI, which triages and routes each to the right audience).

**The hard part (owner-named) — audience routing, fail-closed:** can the AI correctly classify *who
each report is for* — owner-private · this server's mods · the public bug tracker — with a guard
that **fails closed** so a server-private issue can NEVER leak to the public site? (Unsure →
owner-private, never public — the website-split redaction discipline applied to *outbound* reports.)

**Open questions the dedicated session must answer (do NOT decide unprompted):**
1. The **report schema** (kind: correction/bug/server-problem/moderation · subject · evidence).
2. The **audience classifier** + its **fail-closed default** (unsure → owner-private).
3. **Redaction** — a server's private detail must never cross into a public/GitHub artifact.
4. A mandatory **human approve step** before any report becomes public or a GitHub issue.
5. **Dedup** + **abuse/cost controls** (stranger-grade Q-0080; spend ceiling Q-0082).
6. The **"correct response"** back to the reporting user (acknowledge · "filed" · resolution).
7. **Submission moderation** is a *second* gate that fails **OPEN** (clean-on-suspicion → allow;
   three-way: confident-foul → block · maybe-prank → allow + soft-flag · clean → allow). The two
   gates have **opposite** safe defaults and must NOT be flattened into one "when unsure, block."

**Why gated (correct, not over-caution):** this is the AI's **first real write/external capability**
— per Q-0048 read-only AI ships freely but writes/external need a per-exposure design + lift, so a
dedicated session is the rule. **Home:** the idea doc + this Q-block. Related: Q-0048 (AI write
gate), Q-0121 (Hermes triage write scope), Q-0082 (spend), the website-split redaction contract.

---

### Q-0184 — DISCUSS: bot memory — global (across servers) vs. per-guild scope (2026-06-19)

> **PROPOSED — surfaced by the band-#1140 reconciliation pass** from
> [`ideas/honcho-memory-evaluation-2026-06-16.md`](../ideas/honcho-memory-evaluation-2026-06-16.md).
> Routed for live owner review per the #1140-fire directive.
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → honcho-memory idea doc.** The owner chose
> **user-chosen global-vs-per-guild scope** (each user picks whether memory follows them across servers
> or stays this-server-only) — *not* per-guild-only-by-default, *not* global-by-default. Memory still
> stays light / opt-in / bounded under the Q-0082 spend ceiling; this also fixes the per-user config
> surface the hybrid-gear auto-equip toggle (Q-0182) shares.

**Context:** the memory idea currently proposes **user-chosen scope** — each user picks **global**
(memory follows them across servers) or **per-guild** (this server only), as the *user's* choice,
not a system-wide default. The owner separately wants memory kept **light** (conclusion-style,
opt-in, bounded under the Q-0082 spend ceiling) to control API cost.

**The question for the owner:** is **user-chosen global-vs-per-guild scope** the right model, or
should the bot default to **per-guild only** (simpler, privacy-safest, no cross-server data flow)
with global as a later opt-in — or **global by default**? This also fixes the surface the hybrid-gear
auto-equip toggle (Q-0182) lives on — the idea docs route both per-user preferences to the **same
per-user config surface**. **Home:** the honcho-memory idea doc + this Q-block. Related: Q-0082
(spend ceiling), Q-0080 (stranger-grade), P0-2 (data minimization/retention), Q-0182 (per-user config).

---

### Q-0185 — DISCUSS: the public bot-site's one-line pitch (2026-06-19)

> **PROPOSED — surfaced by the band-#1140 reconciliation pass** per the #1140-fire directive
> ("…and the public bot-site's one-line pitch"). The website split is built/in-flight
> ([website-two-site-split plan](../planning/website-two-site-split-plan-2026-06-19.md), Q-0178/Q-0179);
> the marketing pages need a headline.
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → website-split plan "Layout & UX guidance".**
> The public bot-site one-line pitch is **"Everything your server needs — free, forever."** (leads with
> the free-for-everyone North Star, Q-0190, + all-in-one breadth). Picked over the "actually free" wedge
> and the feature-list variants.

**The question:** what is the **one-line pitch** for the public bot site — the single sentence a
visitor reads first that says what SuperBot *is*? The repo description is *"The best bot ever made"*;
the bot is a multi-feature Discord bot (moderation · server setup/access · economy & games incl.
mining/fishing/blackjack · a BTD6-knowledgeable AI assistant · welcome cards). The owner's voice and
audience should drive the wording — agents should **not** invent the public-facing brand line.
**Home:** this Q-block + the website-split plan's "Layout & UX guidance" section. Related: Q-0042
(staged Someday website), Q-0178 (two-site split), Q-0179 (control-panel placement).

---

### Q-0186 — DISCUSS: Pokétwo-inspired features — which net-new lane to build first + spawn design (2026-06-20)

> **PROPOSED — surfaced while turning the owner's Pokétwo/JMusicBot research report into a plan**
> ([`planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md`](../planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md)).
> The owner steered the report session to **plan only, build nothing yet**; this routes the build
> decisions for when a future session executes. The mapping already settled the gated/rejected
> items (marketplace = its own roadmap gate; premium currency = rejected Q-0039; music = Q-0041
> arch-review pack).
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → the feature-mapping plan.** Build order (Q1):
> **Lane A (Wild Encounters) first** (the agent rec — highest engagement leverage, ungated, feeds B/C/D).
> Q2 (spawn defaults) + Q3 (guardrails) were not separately polled — they ride the plan's documented
> defaults (config-driven threshold/debounce, off by default; earned-only / no-buyable-power per Q-0039;
> per-channel opt-in + rate-limit + no auto-catch; stranger-grade claims per Q-0080), refined when Lane A's
> runtime session builds.

**Context:** most Pokétwo mechanics already have lanes here (catching = fishing/mining/pets;
trading = the economy-marketplace roadmap; "one world" = the federated Explore hub). The mapping
identified **four net-new, ungated, anti-P2W lanes**: **A) Wild Encounters** (activity-based
spawning — the signature mechanic with *no* existing analog), **B) Collection & filtering**
upgrade (extend fishing/inventory), **C) Quest/achievement** foundation (Q-0182-aware), **D)
Shiny/rare-variant** layer (cosmetic prestige, rides on A/fishing).

**The questions (the agent recommends, but the owner-designer decides):**
1. **Build order** — which lane first? *Agent recommendation: **Lane A (Wild Encounters)*** — highest
   engagement leverage, no gate, and it feeds B/C/D. Lane B is the low-risk parallel/warm-up.
2. **Wild-encounter spawn defaults** — threshold/debounce (report's "~24 messages", config-driven,
   off by default); **reward pool** (fishing/mining items vs. coins vs. a dedicated catalogue);
   **claim shape** (first-click vs. "name the catch" guess folding in the hint mechanic).
3. **Confirm the guardrails** — earned-only/no buyable power (Q-0039), per-channel opt-in +
   rate-limit + no auto-catch (the report's own anti-spam rule), stranger-grade claims (Q-0080).

**Agent note:** these gate the *build*, not the plan — the spec is written and ungated; it just
needs the owner's sequence + spawn-design call before a runtime session executes (small focused
PRs, runtime-verified). **Home:** the feature-mapping plan + the
[wild-encounters idea](../ideas/wild-encounters-activity-spawning-2026-06-20.md) + this Q-block.
Related: Q-0041 (music gate), Q-0039 (no P2W), Q-0182 (world model), Q-0040 (AI quests from
bounded menus), Q-0080 (stranger-grade), Q-0071 (atomic workflow).

---

### Q-0187 — DECIDE: creature game — original roster vs Pokémon names · PvP level-normalization · art (2026-06-20)

> **PROPOSED — the owner asked the copyright question directly** (*"how is the copyright with
> Pokémon names — can we use them or do we need to create our own?"*) and greenlit **PvP battles**
> (*"PvP battles with the Pokémon would be great"*). A v1 ruleset + a playability simulator are
> built ([creature-game-design-and-sim](../planning/creature-game-design-and-sim-2026-06-20.md),
> `tools/game_sim/creature_battle_sim.py`). These are the design calls before a build session.
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → the design+sim plan.** (a) Creature IP =
> **original creatures** (no Pokémon names/dex — publish-safe, the agent's strong rec). (b) PvP =
> **normalize to a flat level** (types/team-building/ordering decide; raw levels stay PvE/collection
> prestige — avoids the Q-0039 P2W trap the sim found). (d) Roster = **tiered: sim-core 12 → v1 launch
> ~30–40 → growth in waves**, data-driven JSON catalog, text/emoji-first art. (c) Art bar was not
> separately polled — it rides the agent default (emoji/text v1 → an original sprite pack later, the gear
> paper-doll path).

**(a) Creature IP — original vs Pokémon names.** **Agent answer + strong recommendation: make our
own.** Game *mechanics* (catch/types/turn-based battle/stats) are **not** copyrightable — we can
build the loop freely. Pokémon *names, designs, and the dex* **are** protected (Nintendo /
TPC/Game Freak; aggressively enforced). Using them = the same "fly under the radar until a C&D
hits" risk that killed the music bots (the report's Rythm/Hydra history) — wrong for a bot we want
to **publicly launch**. Original creatures (Temtem/Cassette-Beasts/Coromon precedent) give the
loop with no IP risk and fit our world (we already have original fish/ore). v1 roster is original
(Cindling, Magmaul, …).

**(b) PvP level model.** The simulator found **raw levels decide 1v1s** (a +2 gap wins ~100%) — so
raw-level PvP is a grind/whale-fest = **pay-to-win (Q-0039 forbids)**. **Recommendation: PvP
normalizes to a flat level** (competitive-Pokémon style) so types + team-building + ordering
decide. Raw levels still matter for PvE/collection prestige. Confirm normalized vs raw.

**(c) Art.** Emoji/text v1 → an **original sprite pack** later (same path as the gear paper-doll —
owner drops art into `disbot/assets/`). Confirm the v1 visual bar.

**(d) Roster size.** For scale, **Pokétwo uses ~1,000+** real species (full National Dex + forms +
shinies) — we can't/shouldn't mirror that (each original creature is a design/balance/art cost). Even
art-team originals are small (Temtem ~160, Coromon ~120). **Recommendation: tier it** — **sim-core 12
→ v1 launch ~30–40 → growth in waves**, with a **data-driven JSON catalog** (the `towers.json` /
fish-roster pattern) and **text/emoji-first art**, so a bigger roster is cheap *and* every creature is
sim-validated before it ships. 12 proves balance; ~30–40 gives the collection "dex" feel. See the
design+sim plan §2a.

**Agent note:** none of this blocks the *catch* half (Lane A, Q-0186). The battle subsystem is its
own runtime session once (a)/(b) are confirmed. **Home:** the design+sim plan + this Q-block.
Related: Q-0039 (no P2W), Q-0186 (Pokétwo build sequence), Q-0182 (world model), Q-0041 (the
parallel music legal-lane decision — same publish-safe logic).

---

### Q-0188 — DONE (owner-directed in-session): SessionStart branch-freshness warning (2026-06-20)

> **APPLIED in-session** (the live-owner exception to the "don't self-edit executable config"
> rule — owner directed it, owner is the live reviewer, provenance recorded here). The owner
> *"often has to restart a session multiple times in one chat"* (long reply gaps), so PRs merge
> between restarts and the branch silently goes **behind/divergent** — which then trips the
> post-squash-merge rebase foot-gun (it bit this very chat three times: #1185/#1187/#1188 work).

**What shipped:** `scripts/check_branch_freshness.py` gained a `--event sessionstart` mode (concise
`N behind / M ahead of origin/main` verdict, time-boxed `git fetch`, exit 1 when behind), and
`scripts/claude_session_summary.py` now calls it so the **SessionStart banner** prints a loud
`⚠ STALE BRANCH` block with the safe sync command (`git fetch origin main && git reset --hard
origin/main`, clean-tree-only) when the working branch is behind. The existing Stop / pre-push
freshness hooks are unchanged; this adds the *restart* moment they missed.

**Why a warning, not auto-sync:** auto-`reset --hard` in a hook would discard uncommitted work — the
exact data-loss foot-gun seen earlier this chat. The banner surfaces the state + the `ahead` count
so the agent judges (purely-behind = safe reset; diverged = check whether the local commits are
already merged) and acts. **Q-0105 disposable:** delete the `sessionstart` branch + the summary call
if it proves noisy. **Home:** the two scripts + this Q-block.

---

### Q-0189 — DONE (owner-directed in-session): open the session PR FAST — within ~2 min of start (2026-06-21)

> **APPLIED in-session** (the live-owner exception to the "don't self-edit `.claude/CLAUDE.md`"
> rule — owner directed it, owner is the live reviewer, provenance recorded here). Trigger: this
> chat duplicated reaction-roles **PR 2** (rebuilt as #1221) because the in-flight signal of the
> parallel session's lane wasn't seen early — and the owner observed that session PRs *"sometimes
> take a while to open,"* when *"ideally that should happen within the first 2 minutes of a session
> start."*

**The rule (added to the Q-0133 born-red bullet in `.claude/CLAUDE.md` § Session & plan workflow):**
the born-red session card → first push → PR open is the session's **first action** once scope is
known and the lane is claimed (`active-work.md`) — **target the first ~2 minutes**, *before* the
build work, not deferred until after the bulk is written. Sequence: **orient → decide scope → claim →
open the born-red PR immediately → then build.**

**Why:** the early open's entire value is the **in-flight signal**. A visible PR (+ the claim line) is
how parallel sessions see your lane and avoid duplicating it; a PR that opens late — after substantial
work — is invisible during exactly the window when a collision is most likely (the #1221 lesson). This
is the *timing* half of Q-0052 (open right after first push) / Q-0103 (open ready) / Q-0133 (born-red
first commit): those said *open early*; this pins *how* early. **Home:** the Q-0133 bullet in
`.claude/CLAUDE.md` + this Q-block. No new tooling; if a SessionStart nudge later proves useful it is a
separate, disposable add (route it).

---

### Q-0190 — ANSWERED (owner-directed in-session): the product North Star is "free for everyone, forever" (2026-06-21)

> **APPLIED in-session** (owner directed the new goal; owner is the live reviewer; provenance
> recorded here). The owner set a new top-level project goal — SuperBot becomes a **completely free,
> all-inclusive bot** — and explicitly **rejected** the freemium / "monetize only limited features"
> model he had been considering. The single open fork (does "free" forbid even a voluntary
> zero-benefit support link?) was put to the owner live via the question panel.

**Area:** Product / monetization / distribution posture
**Type:** Founding product principle (North Star) — a binding design filter every new plan inherits
**Status:** Answered (owner-directed in-session, 2026-06-21) — **Routed** → mission doc + roadmap principle + current-state Off-limits

**The decision:** Every SuperBot function is **free for every user, forever** — **no paywalls,
premium tiers, freemium feature-gating, subscriptions, or pay-to-win.** "Free **and** better" is the
competitive wedge against the incumbent bots (pairs with the V-14 feature-mining lane and the Q-0080
public-bot goal).

**The one fork — owner's live pick (question panel, 2026-06-21): "Allow voluntary support."** No
feature-gating monetization ever, but a **voluntary, zero-benefit** donation/sponsor link to offset
hosting + AI cost stays allowed (extends Q-0039's cosmetic-only / no-billing posture). The
alternatives — *truly zero monetization* and *free-now-revisit-if-costs-bite* — were not chosen.

**Relationship to prior decisions:** **generalizes Q-0039** (cosmetic-only donations / no bot-side
billing / no-P2W) from the economy to the **whole product**; subsumes **Q-0108** (paid moderation
tiers declined) as a general rule; is the product posture for **Q-0080** (public bot); shares the
"core stays ungated" principle with **Q-0087**. **Resolves tension T-6** (public scale × ~zero
revenue × fixed Q-0082 AI ceiling): revenue stays ~zero permanently, so the Q-0082 degradation
grammar (AI default-off, tiny per-guild budgets, caching, visible in-world degrade) is now the
*primary* sustainability lever, not a fallback — and the voluntary-support surface (§2 of the mission
doc) is the only money inflow.

**Open (captured, not blocking):** a product-wide anti-paywall-creep lint (Q-0105 disposable; needs an
allowlist); the `/support` surface itself (allowed, not yet designed). **The open-source / self-host
question is now ANSWERED (owner, 2026-06-21):** the repo is already public + MIT-licensed (legally
reusable *now*), but reuse is **not recommended** until the code is reorganized/solid — the gate is
code maturity, not licensing (mission doc §5.1). The owner additionally weighed a **free-use-only**
"keep-it-free" license restriction (so a fork can't be paywalled) and chose to **stay MIT for now**
(2026-06-21) — keeping open-source status + max reusability, accepting that a derivative could in
theory be paid; revisit (PolyForm-Noncommercial-style) only if that actually happens (already-
distributed MIT copies stay MIT).

**Home:** [`docs/ideas/free-for-everyone-mission-2026-06-21.md`](../ideas/free-for-everyone-mission-2026-06-21.md)
(full statement) + `docs/roadmap.md` (product-principle callout) + `docs/current-state.md` ▶ Off-limits
(enforceable form) + this Q-block.

---

### Q-0191 — DONE (owner-directed in-session): owner-directed work is NEVER held for review — merge immediately (2026-06-21)

> **APPLIED in-session** (the live-owner exception to the propose-first rule — the owner directed it,
> the owner is the live reviewer, provenance recorded here). **Verbatim owner instruction:** *"anything
> that I personally direct the agents to do should never be held for review, always merge immediately."*
> *(Drafted in-session as Q-0189; renumbered to **Q-0191** at merge time — a concurrent owner-directed
> session had taken Q-0189 ("open the session PR fast") and Q-0190 ("free for everyone") in parallel. The
> reaction-roles PR #1229 commit messages / body reference the original Q-0189; this Q-0191 block is the
> canonical record.)*

**The decision.** The `needs-hermes-review` gate (Q-0117) exists for *autonomously-initiated* substantial /
risky runtime work — the case where no human chose the task and an independent reviewer should look before it
lands. It must **NOT** be applied to work the **owner personally directed** (a session prompt, an in-chat
instruction, a "build PR N / continue the plan" request). Owner direction *is* the review. So:

- When the owner personally directs a task, the resulting PR(s) are opened **ready, never `needs-hermes-review`
  / never `do-not-automerge`**, and **auto-merge is armed immediately** so GitHub merges the instant **Code
  Quality** is green. No human-merge hold, no waiting for a reviewer.
- This **supersedes** the reflex (seen on reaction-roles PR 2, #1219 / the duplicate #1221) of stamping
  `needs-hermes-review` on owner-directed runtime work. That gating was against the owner's wish.
- The autonomous carve-out is unchanged: a *self-initiated* substantial/risky runtime PR (no owner work order)
  may still choose `needs-hermes-review` (Q-0117) or `do-not-automerge` (Q-0114). The distinction is **who
  chose the task**, not how big it is.

**What "merge immediately" does and does NOT mean (the load-bearing nuance):**

- **Does** mean: arm GitHub-native auto-merge at PR-open (or call `enable_pr_auto_merge` directly when the PR
  was opened via the GitHub MCP, per Q-0127) so it lands the instant CI is green — no deferred / manual merge.
- Does **NOT** mean bypass CI: the PR still **must be green** (Code Quality / the session-card gate). "Merge
  immediately" = "merge the moment it's mergeable," not "merge red."
- Does **NOT** mean deploy: **merge ≠ deploy** stays in force — the production restart / prod-checks remain the
  maintainer's (a merge auto-deploys `main`, but the owner owns prod verification).
- Genuinely **irreversible / external-publish** safety brakes are unchanged — those ask first regardless; this
  directive removes the *review-gating* of owner-directed work, not the *safety* brakes.

**Applied this session:** the owner directed the reaction-roles overhaul PR 3–6 → they open ready and
auto-merge on green (NOT `needs-hermes-review`). The superseded duplicate #1221 (a second build of PR 2, already
shipped via #1219) is closed as superseded, not merged.

**Home:** this Q-block (canonical owner decision) + the `.claude/CLAUDE.md` auto-merge bullet (the binding rule,
edited in-session under the same live-owner exception, citing Q-0191).

### Q-0192 — ANSWERED (owner decision in-session): Project Moon knowledge domain — full parity across all three games (2026-06-21)

**Context.** A community member asked the owner to have the **Project Moon wiki** (Lobotomy Corporation /
Library of Ruina / Limbus Company) available in the bot "in one area," the way BTD6 data is available.
An agent did the feasibility research (verdict: achievable + good fit, but a real build — the bespoke
`btd6_*` knowledge stack and Project Moon's fragmented, prose-heavy sources are the cost) and asked the
owner the **scope fork** via `AskUserQuestion`: (1) lore & Q&A grounding, (2) + structured stat lookups,
(3) full BTD6-grade parity across all games.

**The decision.** The owner picked **(3) — full parity, all games.** The target is the maximal build:
**AI Q&A grounding + browsable structured lookups + calculators** for the whole Project Moon universe,
all three games + shared lore, exact numbers where they exist.

**What this authorises (and its bounds).**

- It is **owner-directed** → resulting PRs open **ready, never `needs-hermes-review`**, auto-merge on
  green (Q-0191). It is **product intent / a north-star scope**, not a licence to one-shot a ~12k-line
  refactor of gated runtime: the work is a **program**, sequenced into value-shipping slices.
- The agent's **engineering call** (not the owner's to make): **generalise the BTD6 knowledge stack into
  a domain-agnostic `KnowledgeDomain` seam** with BTD6 as instance #0 and the Project Moon games as
  instances, rather than a parallel `projmoon_*` copy — built **proof-first** (a minimal standalone
  Limbus domain first, then extract the seam). BTD6 behaviour must stay byte-identical / not regress its
  groundedness guards (ADR-006).
- **Three follow-up design questions** (authoritative source per game · lore depth/spoilers · `/pm` hub
  vs per-game commands) are routed to the owner in the plan; they refine later phases and do **not** block
  the first slice (sensible defaults assumed).

**Applied this session:** promoted the idea → the program plan
`docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md` (owner-directed, auto-merge on green,
docs-only). No runtime code this session — the first build slice (Limbus lore-Q&A vertical) is the next
session's work.

**Home:** this Q-block + `docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md` (the program
plan) + the idea capture `docs/ideas/project-moon-wiki-knowledge-domain-2026-06-21.md` (resolved) +
`docs/planning/README.md` S2 index.

### Q-0193 — ANSWERED (owner directive in-session): "Merge = deploy" — kill the "restart is yours" misinformation (2026-06-21)

**Context.** Closing the role-presets session (#1245), an agent told the owner "the production restart is
still yours." The owner corrected it: **Railway auto-deploys `main` on every merge**, so a merged change is
live on its own — there is no manual restart to perform. He added the meta-point: *the fact that an agent
parroted "restart is your job" means the deploy reality is buried and the docs are too crowded.*

**The decision / correction.** **Merging IS deploying.** A merge to `main` triggers an immediate Railway
auto-redeploy of `worker` (the deploy *is* the container restart); the change is live within minutes with
no manual step. Agents must **never** tell the maintainer to "restart" or "deploy" a merge to apply it.
What genuinely stays the maintainer's is **live verification, rollback, and eval walks**, plus any per-PR
*data* step a change explicitly names (e.g. `!btd6ops seed-data`, or an operator button to clear stale
rows) — **not** the deploy/restart. (This sharpens, not contradicts, the Q-0084 "merge ≠ deploy"
autonomy grant: that grant meant *verification/rollback* stay the owner's, never that a separate manual
deploy is required. The misleading "Merge ≠ deploy — restart stays yours" shorthand was the bug.)

**Applied this session (docs-only):** the canonical `docs/operations/production-deployment.md` § *How code
reaches production* gained an unmissable "Merge = deploy" lead and dropped the "restarts … stay the
maintainer's" phrasing; the `.claude/CLAUDE.md` auto-merge bullet's "**Merge ≠ deploy** — production
restart/prod-checks stay the maintainer's" was rewritten to "**Merging IS deploying** … never tell the
maintainer to restart/deploy a merge" (edited in-session under the Q-0106 live-owner exception, citing this
Q); `.session-journal.md` got a one-line prevention note next to the auto-deploy fact.

**Home:** this Q-block (canonical) + `docs/operations/production-deployment.md` (the operational truth) +
the `.claude/CLAUDE.md` auto-merge bullet (the binding rule).

---

### Q-0194 — ANSWERED (owner directive in-session): make agents self-generate workflow guards; wrong-branch hook (2026-06-22)

**Context.** A session hit a wrong-branch slip: a piped `git checkout` (`… 2>&1 | tail -2 || fallback`)
masked the checkout's failure behind `tail`'s exit code, so a `git merge origin/main` ran on an
already-merged branch (caught + reset, nothing pushed). The owner first asked whether a sync-to-main
rule existed (it does — the orient / SessionStart freshness guard), then asked to turn the prevention
into a hook — and made the **meta-point**: *catching these inconsistencies should not depend on the
owner. The repo is built so agents think for themselves; anytime a session hits something that
interrupts the workflow, it should itself produce a way to prevent it for the next session. Most of
this already works (the session enders / reflection interview), but cases like this still slip by.*

**The decision / directive.**
1. **Build the wrong-branch guard (recommended advisory option).** Extend
   `scripts/check_branch_freshness.py` (the existing Q-0138/Q-0188 PreToolUse(Bash)+Stop+SessionStart
   hook) so PreToolUse also fires on `git commit`/`merge`/`rebase` with a **network-free** branch guard
   (detached-HEAD / on-`main` / behind-`origin/main`) — advisory, never blocking, same Q-0105
   kill-switch. `git push` keeps the authoritative network freshness check. (Built in-session under the
   Q-0106 live-owner exception for executable config; no `.claude/settings.json` change needed — the
   existing `Bash` matcher already routes to the script.)
2. **Standing reflex — "friction → guard" (the systemic half).** Any time something interrupts a
   session's workflow, the session must convert it into the **cheapest *enforcing* prevention** before
   ending — **checker/CI/test → hook → journal Rule**, in that order ("enforce, don't exhort", Q-0132) —
   not merely note it. Ownership split: docs/journal/test/checker guards are **free to ship now**; a
   hook / `.claude/settings.json` / binding-`CLAUDE.md` rule is **owner-gated** (build if owner-directed
   in-session, else propose a router DISCUSS Q).

**Applied this session (in-session authority + free-to-edit):** extended `check_branch_freshness.py`
+ tests (Q-0106 exception; the hook provenance header carries this Q); added reflection-interview
**question 7 (friction → guard)** to `.sessions/README.md`; added END-protocol **step 4b** + two
**Cross-agent & git workflow** Rules (sync-fresh-before-PR-work; never mask a command's `$?` behind a
pipe / confirm `git branch --show-current` after a checkout) to `.session-journal.md`.

**▶ DISCUSS (owner, optional):** elevate the friction→guard reflex from the journal/README into the
`.claude/CLAUDE.md` Working agreement as a one-line binding principle. Left as a proposal because
CLAUDE.md content is propose-first (Q-0035) and the reflex is already operative via the session enders;
the owner can promote it if he wants it binding rather than guidebook-level.

> **ANSWERED 2026-06-28 (owner, question panel) — PROMOTE.** The owner chose to elevate the
> **friction → guard** reflex to a binding one-line principle in the `.claude/CLAUDE.md` Working
> agreement (over keeping it journal/README-level). Applied this session under the Q-0106 live-owner
> exception (the owner directed it via the panel; behaviour is unchanged — the reflex was already
> operative — this raises its authority/visibility). **Home:** `.claude/CLAUDE.md` Working agreement +
> this Q-block.

**Home:** this Q-block (canonical) + `scripts/check_branch_freshness.py` header (the hook) +
`.sessions/README.md` Q7 + `.session-journal.md` END step 4b & Rules (the operative reflex).

### Q-0195 — ANSWERED (owner directive in-session): split the coordination files — per-claim active-work + per-sector current-state (2026-06-22)

**Context.** The owner proposed splitting `current-state.md` per-sector to reduce merge conflicts and
make "what's the current state / next work" easier to find, then asked whether I could *simulate* the
options rather than assert. Two findings: (1) `current-state.md` is **not** the conflict hotspot —
`active-work.md` is (it had ~6× the edit churn); (2) a real-`git merge` simulation
(`tools/sim/claim_layout_sim.py`), replaying concurrent sessions distributed by the **actual** sector
weights (S1 ~55%), measured the single-shared-file claim ledger at a **~98% conflict rate**, a
**per-sector** split at **35–66%** (and *worse* with concurrency, because work clusters in S1), and a
**one-file-per-claim** layout at **0%** (structurally — disjoint file sets cannot conflict), *provided
there is no shared hand-edited index*.

**The decision / directive (owner: "implement both").**
1. **`active-work.md` → one file per claim** under `docs/owner/claims/` (the conflict fix). A session
   creates `docs/owner/claims/<branch>.md` at start and **deletes it** at close; discovery is `ls` /
   `check_lane_overlap.py` (which now reads the directory). **No shared index** — that is the rule that
   preserves the 0%. The old `active-work.md` becomes a pointer to `claims/README.md`.
2. **`current-state.md` → per-sector live-state** files (`docs/current-state/S1..S5.md`) behind the
   existing hub (the discoverability goal — a *different* goal from conflicts). `current-state.md` stays
   the canonical hub (keeps `## Recently shipped` + the ledger marker, so the ledger checker is
   unaffected) and points to each sector file.
3. **GC failsafe (owner: "make it the reconciliation job, so the repo doesn't fill with thousands of
   files").** Primary keep-small mechanism = per-session self-delete; the docs-reconciliation pass
   (Q-0107) GC-sweeps orphans via `scripts/check_stale_claims.py --prune`. We do **not** re-merge claim
   files back into one file (that re-imports the 98% conflict surface).

**Applied this session (owner-directed in-session → Q-0106 live-owner exception for the CLAUDE.md claim
convention).** New `docs/owner/claims/` (README + per-claim files); `active-work.md` → pointer;
`check_lane_overlap.py` reads the directory (+ tests); `check_stale_claims.py` + tests; reconciliation
routine GC step; per-sector `current-state/` files + hub pointer; CLAUDE.md Q-0126/Q-0189 references
updated; `tools/sim/claim_layout_sim.py` kept as the evidence artifact (PR #1283).

**Home:** this Q-block (canonical) + `docs/owner/claims/README.md` (the convention) +
`scripts/check_lane_overlap.py` / `scripts/check_stale_claims.py` headers +
`docs/operations/autonomous-routines.md` (the GC step) + `.claude/CLAUDE.md` § Session & plan workflow.

### Q-0196 — ANSWERED (owner decision, AskUserQuestion): what are caught fish *for*? cook-at-campfire + sellable (2026-06-22)

**Context.** Applying the mining energy rebalance (Q-0195-era, #1284/#1286), the owner asked that energy
also be refillable by "cooking/eating fish or consuming boosters". Fish *use/value* was an explicitly
**open** owner question (Q-0175 — fishing v1 deliberately paid nothing and kept caught fish in a
collection log, not the inventory). Two forks were put to the owner.

**The decision.**
1. **Cooking is gated on a built Campfire structure** (not eat-raw, not free) — a small early coin +
   material sink (`!build campfire`) before fish→energy unlocks. A progression beat, not a wall.
2. **Fish are BOTH an energy source AND sellable for coins** — a caught fish enters the mining
   inventory (sellable via the normal market, modest size-scaled value) and can be `!cook`ed into a
   `cooked fish` food (+30 energy). This resolves the *fish-value* half of Q-0175 (the leveling-ladder /
   minigame tail of Q-0175 stays open).

**Applied this session (owner-directed → merge-immediately, Q-0191).** `fishing_workflow.fish` grants
the caught species to the inventory; fish added to `utils/mining/items.py` as sellable `RESOURCE`s;
`campfire` added to `utils/mining/structures.py`; `mining_workflow.cook` + `!cook`; `cooked fish` in
`energy.RESTORE_VALUES`. **Balance caveat (flagged):** fishing is currently unpaced (no energy/cooldown),
so fish sell value is kept deliberately low — a future fishing-pacing pass is the right place to revisit
it before fish become a meaningful coin faucet. PR #1289.

**Home:** this Q-block (canonical) + `docs/subsystems/games.md` (fishing plan pointer) +
`docs/planning/mining-economy-balance-2026-06-22.md` (Applied section).

### Q-0197 — ANSWERED (owner directive in-session): retire the `needs-hermes-review` label + its merge gate completely (2026-06-22)

**Context.** While merging all open PRs, #1279 sat `needs-hermes-review` / "NOT self-merged" and had to
be hand-merged around its own carve-out. The owner directed, in-session: *"remove the label and the rule
for that completely, it's not being used at all and just gets in the way of clean merges."* This retires
the Q-0117 independent-reviewer merge gate (the Hermes `review-merge` skill) and the executor convention
of labelling substantial self-initiated steps for review.

**The decision.** The `needs-hermes-review` label and its no-self-merge rule are **retired**. No PR is
ever labelled with it again; every PR auto-merges on green CI (Q-0123). The separate **`do-not-automerge`**
generic hold (Q-0114) is **kept** — it is still the way to gate a specific PR by hand. Hermes keeps its
read-only review skills (`review`, `pr-check`) but no longer has a merge action; its remaining sanctioned
write is authoring docs-only skill PRs (Q-0140).

**Applied this session (owner-directed → applied directly per the CLAUDE.md in-session exception).**
Removed the `needs-hermes-review` carve-out from `auto-merge-enabler.yml`, `pr-auto-update.yml`,
`codex-final-review.yml`, and `scripts/check_ci_coverage.py` (`CARVE_OUT_LABELS`); deleted the Hermes
`review-merge` skill (doc + generated `SKILL.md` + `build_skills.py` EXTRAS) and regenerated the skill
set; updated `.claude/CLAUDE.md`, the hermes-skills docs, and `scripts/dispatch_menu.py`. Immutable
history (`.sessions/`, reconciliation passes, idea files) is left as written. **Note for the owner:** the
GitHub *label* itself still exists in repo Settings → Labels — delete it there to finish the cleanup (it
is now unreferenced and harmless). PR for this change: branch `claude/jolly-sagan-dzxeni`.

**Home:** this Q-block (canonical) + `.claude/CLAUDE.md` § Session & plan workflow +
`docs/operations/hermes-skills/README.md`.

### Q-0198 — DISCUSS: mining-grid encounters — depth threshold, content, determinism, resolution UI (2026-06-22)

> **PROPOSED — surfaced by a dispatch grooming pass** (product lanes were gated, so instead of a 7th
> infra guard this routes the *one owner-named* grid follow-up toward buildability). Origin **Q-0173**:
> the owner shipped the grid Mine (`views/mining/grid_mine_view.py`, hub-redesign PR 3) *encounter-free
> by explicit decision* — *"v1 = free movement, NO encounters … encounters ARE wanted, as a separate
> later session."* The [idea](../ideas/mining-grid-encounters-2026-06-22.md) itself says **"route to a
> router Q before building, don't decide unprompted"** — so this poses the decisions, with defaults,
> rather than building. Q-0172 "build freely" yields here to the owner's explicit design reservation.
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → mining-hub-redesign plan + the grid-encounters
> idea.** **Build the encounters, loot/flavour-only first** (Q2 = loot/flavour v1; combat is a fast-follow
> that reuses the creature/deathmatch engine, never a third bespoke combat model). Q1 (depth/chance/
> cooldown), Q3 (live roll — not per-cell-deterministic) and Q4 (extra buttons on the navigator) were not
> separately polled — they ride the agent recommendations in this block, sim-tunable when the runtime
> session builds it.

**Context:** layer **sparse, depth-gated random encounters** onto the shipped grid navigator — a
low-probability event on a `move` / `Mine here` action once deep enough, resolved through the audited
`mining_workflow` seam (RS02/Q-0071), never a direct view write, and **never mandatory-feeling**
(Q-0087). The grid already persists a seed-deterministic `(seed, x, y, z)` world, so encounters can be
deterministic + shareable for free. **Distinct from Q-0186 / the [wild-encounters
idea](../ideas/wild-encounters-activity-spawning-2026-06-20.md):** that one is *chat-activity-triggered*
channel spawns; this is *exploration-triggered* while roaming the grid. They could share **one pure
`encounter` resolution engine** with two triggers — worth building the engine once if both land.

**The questions (the agent recommends; the owner-designer decides):**
1. **Depth threshold + per-action chance + cooldown** (the "not too many" tuning). *Recommendation:*
   no encounters above depth **z ≥ 10** (surface bands stay calm for casual play); **~8 %** per qualifying
   `move`/`mine` action; a **per-player cooldown of ~5 actions** so roaming isn't interrupt-spam. All
   config-driven constants (sim-tunable like the economy constants), off-by-default-safe.
2. **Encounter content — flavour/loot vs. light combat.** *Recommendation:* **start loot/flavour-only**
   for v1 (a small table: ore vein / hazard that costs energy / abandoned cache of coins), routed through
   `economy_service` / `update_mining_item` / `game_xp_service` exactly like `mine_here`. **If combat is
   wanted, reuse the creature/deathmatch engine** — never a third bespoke combat model (the idea's
   anti-pattern). Combat can be a fast-follow once the loot loop proves out.
3. **Determinism — fully seed-deterministic per cell vs. a live roll.** *Recommendation:* **a live roll
   gated by depth/cooldown**, *not* per-cell-deterministic — two players' runs should differ and a cell
   shouldn't farm the same encounter on every revisit (the grid's *terrain* stays deterministic; the
   *events* are live). Keeps it an event, not a map feature.
4. **Resolution UI — extra buttons on the navigator vs. a swapped sub-view.** *Recommendation:* **extra
   buttons on the existing navigator embed** (Fight/Flee/Loot as the content dictates) — stays in the
   one grid surface, no view juggling; matches the calm, in-place UX the grid already uses.

**Agent note:** these gate the *build*, not a plan — the shape is small + additive (the same discipline
grid v1 followed) and ungated apart from this design call; once answered, a runtime session builds it in
small PRs (pure `utils/mining/encounter.py` table + an audited `mining_workflow` op + navigator buttons),
runtime-verified. **Home:** this Q-block (canonical) + the
[mining-grid-encounters idea](../ideas/mining-grid-encounters-2026-06-22.md) +
[`planning/mining-hub-redesign-2026-06-15.md`](../planning/mining-hub-redesign-2026-06-15.md) (PR 3's
"Later — encounters"). Related: **Q-0173** (grid design), **Q-0186** (wild-encounters spawn design —
shared engine), Q-0087 (never mandatory), Q-0071 (atomic workflow).

### Q-0199 — ANSWERED (owner decision, in-session): AI may APPLY setup changes, but only after confirmation — per-suggestion Accept/Deny/Edit (2026-06-23)

**Context.** The generative AI-setup wedge — *"describe your server → AI proposes channels/roles/automod
→ staged ops → apply"* — had its read/propose seams shipped (`/setup-describe` #1355, propose-resource
#1357, Final-Review create-count guard #1361, `views/setup/ai_review/`), but the **apply** (guild-mutating)
step was the one remaining consolidation item, deliberately held under **Q-0048**'s rule (AI *writes* need
a per-exposure design + owner decision before shipping). Asked for the decision, the owner directed,
in-session: *"yes AI should apply them but only after a confirmation, AI should spawn three buttons —
accept, deny, edit."*

**The decision.** AI **may apply** the setup changes it generates (create/bind channels, roles, categories,
automod config from a described plan) — but **never autonomously**. Every applied change is **human-gated**:
each AI suggestion is decided per-item with **Accept · Deny · Edit**, and the accepted set applies **only**
through the existing audited **Final Review** confirmation (`setup_draft` → `FinalReviewView` → the audited
dispatcher, behind the `setup_access.can_apply_setup` permission floor). The AI never writes to a guild
without an operator pressing apply on a reviewed plan. This is the per-exposure **write** lift Q-0048
reserves — granted for *this* exposure (setup provisioning) with the confirmation guardrail above; it does
**not** generalize to other AI write surfaces (each still needs its own lift).

**Applied this session.** The propose→stage→Final-Review→audited-apply path already existed; PR **#1386**
added the missing **Edit** affordance (and renamed Reject→Deny) on the per-recommendation walkthrough
(`views/setup/ai_review/per_recommendation.py`): Edit opens a modal to rename a `create` suggestion before
accepting; a `bind` suggestion can't be renamed (Deny + rebind). The review surface stays **propose-only**
(zero DB/Discord writes there — the module's zero-write contract tests hold); application remains the gated
Final Review. A noted follow-on (not yet built): Edit could re-pick the *target* of a `bind` suggestion via
a channel/role select.

**Home:** this Q-block (canonical) + `.sessions/2026-06-23-ai-setup-edit-button.md` +
`docs/subsystems/settings-bindings-provisioning.md`. Related: **Q-0048** (AI exposure gate / per-exposure
write lift — the parent rule), Q-0123 (auto-merge on green).

### Q-0200 — DISCUSS: add a "grep `def <exact_name>` before defining a new service function" step to the dedup discipline (2026-06-24)

> **PROPOSED — surfaced by a real collision this session** (`.sessions/2026-06-24-btd6-per-round-economy-commands.md`).
> This proposes a rule addition, so it routes here rather than self-editing CLAUDE.md / `helper-policy.md`
> (the binding-rule channel). The owner is the live reviewer when present; otherwise it waits.
>
> **ANSWERED 2026-06-28 (owner, question panel) — Routed → `docs/helper-policy.md` (+ CLAUDE.md helper
> rules mirror).** **Adopt** the one-line dedup guard: before defining a new `services/`-or-`utils/`
> function, grep `def <exact_name>` in the target module + its sibling modules (plus the 1–2 nearest
> concept synonyms). A checklist line, not a CI gate (Q-0105 disposable).

**Context:** building the per-round economy commands (PR #1404), I added a new `round_composition` to
`btd6_data_service` **without noticing one already existed** (the range/AI variant). Python took my later
definition, shadowing the original and breaking its AI-tool + ABR tests — caught only at the full CI
mirror, not pre-implementation. Root cause: the "claim before starting / don't duplicate" scan (CLAUDE.md
§ Session workflow) and `helper-policy.md` both aim at *file/area* overlap, but my dedup grep was keyed on
the **concepts** (`cash`/`income`/`rbe`) and command names — I never grepped the **exact function name** I
was about to define. `round_rbe` (genuinely new) was fine; `round_composition` was a name I should have
checked.

**The proposal:** add one mechanical line to the dedup discipline (in `helper-policy.md`, mirrored in the
CLAUDE.md helper rules): *before defining a new `services/`-or-`utils/` function, grep `def <exact_name>`
in the target module **and** its sibling modules, plus the 1-2 nearest concept synonyms.* Cheap,
deterministic, and it converts a class of "shadowed an existing symbol" bug from a full-mirror catch into
a five-second pre-write check.

**Open question for the owner:** worth codifying as a rule, or leave as session-log lore? It's the kind of
tiny guard the kill-switch convention (Q-0105) covers — adopt it, delete it later if it proves noise.
Recommendation: **adopt** in `helper-policy.md` (not a CI gate — a checklist line), since the failure it
prevents is silent until CI and trivially avoidable.

**Home:** this Q-block (canonical) + the session log. Related: **Q-0014** (claim/dedup before starting),
**helper-policy.md** (the durable home if adopted), Q-0120 (verify-tool-vs-evidence — same "catch it
earlier" instinct).

---

### Q-0201 — ANSWERED (owner decision): the AI may OPEN support tickets in natural language — via a one-click confirm, NOT autonomously (2026-06-24)

**Context.** The owner requested a support-ticket subsystem that works *"by command as well as through the
AI with natural language"* — a user says *"open a ticket, I need help with X"* and the bot opens one. Every
AI tool in `services/ai_tools.py` is **read-only** by a documented + test-pinned invariant (the module
docstring + `tests/unit/services/test_ai_tools.py`); **Q-0048** reserves AI *writes* for a per-exposure
lift. Opening a ticket is a write. Asked how the AI should create it, the owner chose, in-session, the
**one-click confirm** option over having the AI create it directly.

**The decision.** The AI **proposes**, the human **commits**. `open_support_ticket` stays effectively
**read-only**: it validates eligibility (`ticket_service.check_open_eligibility` — per-user open cap +
blacklist + "is the guild set up?") and, when allowed, emits a single advisory `ticket.open_requested`
event; it does **not** create anything. `cogs.ticket_cog` posts a one-click **[Open ticket]/[Cancel]**
confirmation (`views/tickets/confirm.py`, locked to the requesting user) into the channel, and the actual
open runs **only on the user's click**, through the deterministic, audited `ticket_mutation.open_ticket`
seam (one txn + `emit_audit_action` + `ticket.opened`). So the AI never opens a channel on its own, and the
`ai_tools.py` "mutations flow through a deterministic service after explicit confirmation" contract is kept
intact — no write-capable AI tool is introduced.

**Scope / non-generalization.** This is the pattern for *any* AI-initiated mutation: **validate read-only →
emit a request event → human confirms → audited service writes.** A genuinely autonomous (no-click) AI
write still needs its own per-exposure lift (cf. Q-0199, the setup-apply path, which is also click-gated).

**Applied.** PR **#1405** shipped the full `ticket` subsystem (migration 098; `utils/db/tickets.py`;
`ticket_service` read model + eligibility; `ticket_mutation` audited writes; `views/tickets/` launcher /
control / hub; `cogs/ticket_cog.py` commands) — but with the AI tool opening **directly** (the first-pass
design). The follow-up PR **#pending** implements the owner's confirm-button choice: the AI tool now emits
`ticket.open_requested` and the cog posts the confirm view; the actual open is the user's click. Covered by
`tests/unit/services/test_ticket_ai_tool.py` (offering gate + requests-confirmation-without-opening).

**Home:** this Q-block (canonical) + `.sessions/2026-06-24-support-tickets.md` +
`.sessions/2026-06-24-ticket-ai-confirm.md` + the `ai_tools.py` module docstring. Related: **Q-0048** (the
parent AI-exposure gate), **Q-0199** (the setup-apply write lift, also click-gated), Q-0123 (auto-merge).

### Q-0202 — ANSWERED (owner decisions, in-session): Essential Setup "Choose a log channel" scope + naming + the step-0 preset + the Advanced editor (2026-06-24)

**Context.** While building the Essential Setup "Choose a log channel" step (plan
`docs/planning/setup-wizard-restructure-plan-2026-06-24.md`, PR 1; PR **#1429**), four design decisions
needed the owner. Asked as one `AskUserQuestion` batch; answers verbatim below. Two settle *this* step
(scope, name); two settle *later* PRs (step-0 preset = Q-C, the Advanced editor = Q-E) "while you're here".

**The decisions.**
1. **Log scope = moderation log only.** ⚠️ **SUPERSEDED by Q-0203 (2026-06-24, same day).** The step is
   *one* channel: it turns on `logging.enabled` and binds `logging.mod_channel` (the catch-all slot every
   other logging route falls back to) to the picked-or-created channel. **Member-activity (joins/leaves/
   roles) and message-content logging stay OFF** — they are a later follow-on, not this step. *(Reversed
   the same day: the owner clarified "moderation only" was the first slice, not a cap, and asked for a quick
   multi-select of logging types across two channels — see Q-0203. Decisions 2–4 below still stand.)*
2. **Auto-create naming (plan Q-D) = plain-language names.** Auto-created channels/roles use the short §4
   wording — `#mod-log` / `#server-log`, "Level 10", "Regular" — **not** the longer `bot-`-prefixed
   `suggested_name` convention. (The log step creates `#mod-log`.)
3. **Step-0 server-type preset (plan Q-C) = auto-apply safe defaults.** Picking Community/Gaming/Support/
   Creator instantly switches on a curated, **reversible** bundle (nothing irreversible) — *not* recommend-
   and-confirm-each. Not built this PR; settles the future step-0 preset path.
4. **Advanced bulk editor (plan Q-E) = keep but REWORK.** Keep the draft → Final Review editor for power
   users, but the owner sharpened the offered "keep as-is" to **"keep but rework it — currently most of it
   does not do anything."** So PR 3 is not only "demote cog_routing/cleanup under Advanced"; it must audit
   that editor and wire up or strip its dead actions.

**Scope / non-generalization.** (1) and (2) are live in #1429. (3) and (4) are recorded direction for the
step-0 and PR-3 sessions respectively — no code yet.

**Applied.** PR **#1429** ships the moderation-only log-channel step (decisions 1+2): a `LogChannelStep`
on `EssentialFlow` that picks or auto-creates a `#mod-log`, enables logging via `SettingsMutationPipeline`,
and binds `logging.mod_channel` via `BindingMutationPipeline` (lazy-imported per the setup-view invariant)
+ `ChannelLifecycleService.create_channels` for auto-create. Decisions 3+4 are recorded in the plan §10
(Q-C/Q-E ANSWERED) for their future PRs.

**Home:** this Q-block (canonical) + the plan §7 PR-1 note / §5 step 4 / §10 (Q-C/Q-D/Q-E) +
`.sessions/2026-06-24-setup-log-channel-step.md`. Related: **Q-A** (direct-apply per step), the
setup-wizard restructure plan.

### Q-0203 — ANSWERED (owner decision, in-session): the "Choose a log channel" step is a two-channel + multi-select, not moderation-only (2026-06-24)

**Context.** Q-0202(1) scoped the log step to **moderation only** and shipped it that way (#1429). Same
day, the owner clarified that "moderation only" was meant as the **first slice of a multi-step logging
config, not a permanent cap** — and that owners should be able to **choose a few important logging types**
via a **quick multi-select**, kept light ("should not become too much work for server owners, but they
should have the option"). Asked where the chosen logs should go (one channel / two channels / per-type
channels via `AskUserQuestion`), the owner chose **two channels (moderation + activity)**.

**The decision.** The step now offers a **quick multi-select of activity types** — members joining/leaving
(default on) · role changes (default on) · message edits/deletions (⚠️ shows content, default **off**) —
across **two channels**: a **moderation log** (always on → `logging.mod_channel`, the catch-all) and an
**activity log** (→ `logging.events_channel`) for the ticked categories. **Leave a channel empty and the
bot auto-creates it** (`#mod-log` / `#server-log`), so accepting the defaults is one tap. On Save (direct
lane): `logging.enabled=True`; bind `mod_channel`; set the `members_enabled`/`roles_enabled`/
`messages_enabled` flags per the multi-select; bind `events_channel` when any activity type is on. Message
logging stays opt-in because it exposes edited/deleted content (the schema's privacy warning).

**Scope / non-generalization.** This **supersedes Q-0202(1) only** — the naming (Q-0202(2): `#mod-log` /
`#server-log`), the step-0 preset (Q-0202(3)=Q-C), and the Advanced-editor rework (Q-0202(4)=Q-E)
decisions are unaffected. It does **not** promote the full per-category logging surface (the other ~10
channel slots + per-category routing) into the spine — that stays in the existing `!logging` admin UI; the
spine offers a curated few.

**Applied.** PR **#1432** reworks `LogChannelStep` on `EssentialFlow` into the two-channel + multi-select
design above (multi-select + two `_LogChannelPicker`s + auto-create blanks via
`ChannelLifecycleService.create_channels`; bindings via `BindingMutationPipeline`, both lazy-imported per
the setup-view invariant). Reworked tests cover defaults-create-both, picked-channels, activity-off
(moderation only), and create-failure.

**Home:** this Q-block (canonical) + the plan §5 step 4 / §7 PR-1 note + Q-0202(1) (superseded) +
`.sessions/2026-06-24-setup-log-channel-rework.md`. Related: **Q-0202**, **Q-A** (direct-apply per step).

### Q-0204 — ANSWERED (owner decisions, in-session): the "Reward active members" step shape — toggleable rewards + selectable XP rate + an extra role-sourcing screen (2026-06-24)

**Context.** Building the spine's "Reward active members" step (plan §5 step 5; PR **#1434**), the owner
specified the shape over a short exchange: confirmed XP = the per-message earning system, then directed
the step's controls.

**The decisions.**
1. **Role rewards are fully toggleable — both / just one / none.** The owner can switch on level-up roles
   and/or time-in-server roles, or neither.
2. **XP rate is selectable** (the per-message XP range + cooldown) — via a dropdown of presets (Keep
   current / Relaxed / Standard / Active), not free-text.
3. **An extra screen chooses the reward role**, with three sources: **preset** (auto-create a recommended
   `@Regular`) / **create your own** (pick a name) / **reuse an existing role**.
4. **Everything via buttons / dropdowns / multi-selects** — no "type an ID / value" anywhere.
5. **Recommended depth = option 1** (one config screen + the extra role screen; sensible default
   thresholds level 10 / 30 days, tunable later in the role panels) — chosen over cramming threshold
   pickers in or a full multi-screen hub.

**Scope / non-generalization.** Default thresholds (level 10 / 30 days) and the role-name suggestions are
implementation defaults, tunable in the existing `!roles` panels — not owner decisions. **Build note (not
a decision):** the step needed **no new service** — `role_automation.set_xp_threshold` /
`set_time_threshold` are the existing audited direct-apply paths (an earlier "one genuine gap" assumption
was wrong); role auto-create is `RoleLifecycleService.apply(operation="create")`.

**Applied.** PR **#1434** ships `RewardActivityStep` (2-screen) implementing decisions 1–5.

**Home:** this Q-block (canonical) + the plan §5 step 5 / §7 PR-1 note +
`.sessions/2026-06-24-setup-reward-activity.md`. Related: **Q-A** (direct-apply per step), **Q-0202**/
**Q-0203** (the analogous log-channel step decisions).

### Q-0205 — ANSWERED (owner directives, in-session): Essential Setup spine polish + the "optional typing everywhere sensible" principle (2026-06-24)

**Context.** After an agent review of the six live spine steps (navigation / consistent structure / typing),
the owner directed applying every finding and adding optional typing.

**The directives.**
1. **Multi-select is the preferred idiom** for "pick which of these to turn on." Block-spam's four on/off
   toggle buttons were converted to one multi-select, matching the log/reward steps.
2. **Consistent primary-button position + one label voice.** Every step's primary button is **row 3**
   (Back/Skip on row 4) so "Save" is in the same place on every step, and the label is unified to
   **"Save & continue"** (the module-docstring voice), keeping each step's emoji.
3. **Fix the skip-recap bug.** `_StepView.skip()` now records the skipped step (`record_skipped`), so the
   summary's "Skipped (you can do these later)" list actually populates (it was dead code).
4. **Optional typing everywhere it makes sense (DURABLE PRINCIPLE).** Wherever the bot *creates a named
   thing* (a role, a channel), offer an **optional** "✏️ Type a name" path (a `discord.ui.Modal`,
   prefilled with the default). **Typing is always optional, never required** — every default stays
   fully selectable via buttons/dropdowns. Applied to the reward **role name** and the log **channel
   names**. **Future steps must follow this** — e.g. the step-0 server-type preset, and any step that
   auto-creates a named resource, should expose the same optional-type-a-name affordance.

**Scope.** View-layer polish only (no new service / cog / command / artifact). Default thresholds, rate
presets, and suggested names are unchanged.

**Applied.** PR **#1435** (`essential_setup.py` + tests).

**Home:** this Q-block (canonical) + `.sessions/2026-06-24-setup-spine-polish.md` + the plan §7 PR-1 note.
Related: **Q-0202**/**Q-0203**/**Q-0204** (the per-step spine decisions), **Q-A** (direct-apply per step).

### Q-0206 — DISCUSS: automate the claim-GC sweep so a skipped reconciliation step can't leave stale claims (2026-06-25)

> **PROPOSED — surfaced by a dispatch run (2026-06-25).** Captured here, not applied: this is a
> *workflow* change, which CLAUDE.md says an agent **proposes** (router DISCUSS), never self-applies.
>
> **ANSWERED 2026-06-28 (owner, question panel) — option 2.** Make the claim-GC sweep non-skippable via a
> **warn-only `code-quality` step** (`check_stale_claims.py`, advisory — never blocks merges, recursion-free).
> Cheapest safe surfacing; an agent/human still prunes on sight (Q-0166). Chosen over the auto-prune
> workflow (heaviest, #778 recursion class) and the Stop-hook (owner-config, Q-0106). Implemented this
> session.

**The observation.** This dispatch run found a **stale claim file** left on `main`:
`docs/owner/claims/claude-jolly-johnson-rqf8wt.md`, for a branch that merged via **#1407** (band-#1380,
reconciliation pass 23). It survived **two** later reconciliation passes (24 and 25) before this run
deleted it on sight (Q-0166 drift-on-sight).

**Why it's not a tooling bug.** The guard already exists and works: `scripts/check_stale_claims.py`
(built 2026-06-22, with `--prune` + 5 tests) correctly flags exactly this claim (re-verified this run —
it reports the branch as `gone`). The reconciliation routine's saved prompt
(`docs/operations/autonomous-routines.md` L162–163) **already mandates** running it with `--prune`.
The claim lingered because the routine **skipped that step** — a forgettable manual sub-bullet. So the
gap is **execution discipline**, and the durable fix is to make the sweep *not skippable*.

**Options (owner's call — each is a different automation surface):**
1. **A tiny scheduled / merge-triggered workflow** that runs `check_stale_claims.py --prune` and commits
   the deletions. Most automatic; but an auto-commit-to-`main` workflow needs the recursion-guard care
   the #778 class taught us, so it's the heaviest option.
2. **A warn-only `code-quality` step** (`check_stale_claims.py`, advisory) so every PR run surfaces a
   lingering stale claim in its log. Cheap + safe (never blocks merges; an *open* PR's own branch isn't
   merged yet, so it's never falsely flagged), but it only *surfaces* — a human/agent still prunes.
3. **Leave it manual but make the prompt step louder** — promote the GC line from a sub-bullet to a
   first-class numbered step in the reconciliation procedure (lowest effort; relies on discipline,
   which is exactly what failed here).
4. **A Stop-hook advisory** (`scripts/claude_stop_check.py`) that flags a stale-claim count at session
   close — but hooks are executable config an agent does not self-edit (Q-0106), so this is an
   owner-only change.

*Agent recommendation:* **option 2** (warn-only CI surfacing) as the cheap, safe, recursion-free
default, optionally paired with **option 3**. Option 1 only if the owner wants it fully hands-off.

**Home:** this Q-block (canonical) + `.sessions/2026-06-25-stale-claim-detector.md`. Related: **Q-0195**
(one-file-per-claim), **Q-0166** (drift-on-sight), **Q-0105** (disposable-tool posture).

---

### Q-0207 — DISCUSS: make the per-item offline-fit startability tag a standing convention (2026-06-27)

> **PROPOSED — surfaced (and partially built) this session, after a twice-flagged self-audit.** The
> *implementation* (the tags on the sector files + a disposable checker + the map doc) is docs/tooling I
> have free rein on (Q-0105) and shipped this run; **this Q-block is only the rule-level question** —
> should the convention be codified/blessed, or left as a disposable guard? It routes here rather than
> self-editing CLAUDE.md (the binding-rule channel). Owner is the live reviewer when present; else it waits.
>
> **ANSWERED 2026-06-28 (owner, question panel) — options (a)+(c).** **Bless** the per-item offline-fit
> startability tag as a standing convention **and fold it into `dispatch_menu.py`** — the fold already
> shipped in #1482 (`dispatch_menu --unattended` surfaces the per-sector `[offline]` pick). So this is now
> a blessed standing convention (homed in `repo-sector-map.md`); the checker may later graduate to a
> warn-only CI step / Stop-hook advisory (Q-0105 graduate-when-proven). Not left disposable, not dropped.

**Context:** two consecutive empty-fire dispatch runs' Q-0102 reviews (the 2026-06-25 and 2026-06-26
session logs) flagged the same friction: only **S2**'s per-sector live-state file tagged its `▶ Next`
startable items with an offline-fit phrase, and that worked as a fast dispatch signal — but S1/S3/S5
didn't, so each autonomous run burned orient-time rediscovering which startables are offline-verifiable
vs. needs-live-bot vs. owner-gated. The 2026-06-26 review explicitly noted "second occurrence → meets the
router-DISCUSS bar." This run is the third, and confirmed it firsthand (I again spelunked S1's arc bullets
to find the offline lanes).

**What this run already built (reversible docs/tooling, no rule change):** a per-item tag vocabulary —
`[offline]` / `[needs-live-bot]` / `[owner]` — applied to every `▶ Next` item in S1/S2/S3/S5 (S4 exempt:
docs/reconciliation sector); `scripts/check_startability_tags.py` (Q-0105 disposable, **not** CI-wired)
asserting each non-exempt sector's `▶ Next` block carries ≥1 recognized tag; and the convention documented
in `repo-sector-map.md` § "the offline-fit startability tag", next to the existing unattended-fit tag.

**Open question for the owner:** (a) **bless it** as a standing convention (keep the tags + guard, maybe
graduate the checker to a Stop-hook advisory or a warn-only CI step later); (b) **leave it disposable** —
keep it only while it proves useful, delete on the Q-0105 kill-switch if it drifts; or (c) **fold it into
`dispatch_menu.py`** so the empty-fire pick reads the per-item tag directly instead of a human/agent
reading the sector file (the 2026-06-26 review's suggestion). *Agent recommendation:* **(a) + (c)** — the
signal is cheap, already paid for, and directly cuts every future dispatch run's orient cost; wiring it
into `dispatch_menu --unattended` is the natural next slice.

**Home:** this Q-block (canonical) + `.sessions/2026-06-27-startability-offline-fit-tags.md` +
`repo-sector-map.md` (durable home of the convention). Related: **Q-0143** (startability tag), **#1285 /
Q-0172** (unattended-fit tag — the sector-level sibling), **Q-0102** (the self-audit loop that surfaced
it), **Q-0105** (disposable-tool posture).

---

### Q-0208 — DECIDED: three audit-unblock decisions (wire dead stats · build absence-guard Layer B · hold Setup PR 3b) (2026-06-27)

> **ANSWERED (owner, in-session via AskUserQuestion, 2026-06-27).** After an agent reviewed the codex
> unfinished-work audit (PR #1509) and surfaced the genuinely owner-gated items, the owner made three
> decisions in one round. Recorded here so the answers are preserved (Q-0104 "route durable conclusions").

**The three decisions:**

1. **BUG-0026 (`EffectiveStats.light_radius` / `luck` dead stats) → WIRE them into gameplay** (not remove,
   not defer). The gear that grants them should *do* something: `light_radius` → a reveal/visibility effect
   in the mining grid; `luck` → a rare-find/crit chance on dig. *Actioned in its own follow-on PR; the
   BUG-0026 entry is updated there.* The agent brings the specific mechanic + sim-pinned numbers (reversible).

2. **Absence-guard Layer B → BUILD now (offline + unit tests).** Greenlit the design doc's review gate. The
   agent shipped the **grounded-contradiction slice** (§4.2 step 3 — the safe, no-false-floor core) this
   session; the §4.3 unresolved-subject half stays design-only pending a live false-positive-rate check.
   *Home: `btd6-absence-claim-guard-design.md` Update 7 + `.sessions/2026-06-27-btd6-absence-guard-layer-b.md`.*

3. **Advanced Setup PR 3b → HOLD for a live-bot session.** The editor rework ("most of it does nothing")
   genuinely needs a running bot to verify; not done offline. Stays the S1 `▶ Next` `[needs-live-bot]` item.

**Home:** this Q-block (canonical) + the per-decision homes above. Related: **Q-0120** (cross-agent output
is input-to-verify, not an order — the posture used to review the audit), **BUG-0026** (the dead-stats
bug), **Q-0105** (disposable-tool posture).

### Q-0209 — DECIDED: a feature-completion certification layer for S1 bot units (2026-06-27)

> **ANSWERED (owner, in-session via AskUserQuestion, 2026-06-27).** The owner asked for a way to mark
> parts of the bot **complete** — feature- and UX-complete ("all the functions, the right buttons in the
> right places, works as intended, the most convenient version of itself") — and to *prove/show* it,
> noting the bot is close to production-ready and that effort should focus on **finishing existing
> functions before new ideas** (unless an idea deepens an existing one). Recorded per Q-0104.

**Context — why it's a new axis.** This is **orthogonal** to the existing
[`production-readiness`](../planning/production-readiness/README.md) maps, which grade *risk/hardening*
(P0 integrity → P1 correctness → P2 drift). The new axis grades *feature + UX completeness* and ends in
the owner's judgment. A unit is "done-done" only when high on **both**.

**The three decisions (owner picks):**

1. **Unit grain = per feature** — each game and each server function is one certifiable unit, keyed to
   `subsystem_registry.py` (~36 S1 units). (Not per-family, not per-folio.)
2. **Completion-first = soft default** — sessions default to completing/deepening existing units; a
   brand-new unit is captured but **parked** behind a completion gate, greenlightable anytime. (Not a
   hard freeze, not pure case-by-case.)
3. **Certification = evidence + owner sign-off** — a unit reaches `✔ certified` only with a filled
   rubric, green loop/edge tests, a recorded live walkthrough, **and** the owner's ✔. (Not
   agent-self-certified, not owner-only-hands-on.)

**Built this session (PR #1513):** the system + two Definition-of-Complete rubrics (games /
server-functions) + a per-unit certificate model + a generated `completion_scoreboard.py` + a worked
Blackjack pilot, homed at [`docs/planning/feature-completion/`](../planning/feature-completion/README.md).
Wired the soft completion-first gate into [`docs/ideas/README.md`](../ideas/README.md).

**Home:** this Q-block (canonical) + the system README. **Possible future promotion:** if the soft
default proves itself, a one-line binding rule in `.claude/CLAUDE.md` (proposed via a DISCUSS Q, the
graduate-when-proven pattern — Q-0105) would harden it; not done day-one. Related: **Q-0015** (backlog
grooming / secondary task), **Q-0089** (idea generation), **production-readiness** maps (the risk axis).

### Q-0210 — DECIDED: where answers live — router stays the canonical append-only ledger; conclusions route to homes; old blocks archive (never re-home) (2026-06-28)

> **ANSWERED (owner, in-chat, 2026-06-28).** Closing the open-question sweep, the owner asked whether
> some answers should get "a more durable home in the repo," noting the worry that *"a lot of things are
> referred to by question number, so [moving them] might confuse future agents,"* and asked the agent to
> find the best option — leave everything in the router, or slowly start re-routing some answers
> elsewhere. The agent investigated and the decision below records the answer + its evidence.

**Area:** Workflow / docs system · **Type:** Workflow convention · **Status:** Answered — Routed →
`docs/owner/ai-project-workflow.md` §9 + this Q-block.

**The evidence (measured this session).**
- The router is **~491 KB / 7,600+ lines / 215 Q-blocks** and now exceeds the file-read size limit — a
  real, recurring friction (this very session had to read it in slices).
- **9,084 `Q-0XXX` references span 1,307 files.** The Q-number is the repo's stable cross-reference key;
  CLAUDE.md, plans, ideas, session logs, and reconciliation passes all cite decisions *by number*.
- **Exactly ONE anchor-style link exists repo-wide** (`maintainer-question-router.md#q-0017`). Every
  other reference is **plain `Q-0XXX` text** — so a Q-block resolves by `grep`, independent of which file
  it physically lives in.

**The decision (the "best option").** A three-part convention, not the binary the question posed:

1. **The router stays the single canonical, append-only Q-block ledger.** Every decision keeps its
   `Q-0NNN` block here; numbers are **never moved or renumbered** (router §9 / Q-0060). This is what keeps
   the 9,084 references resolvable — the owner's worry is correct, and it is exactly why we do **not**
   physically re-home answers to scattered new docs.
2. **Durable conclusions keep routing to their real homes** via the existing **`Home:` line** (router §7).
   This already happens — the plan / folio / `CLAUDE.md` is where an agent *reads* the decision; the
   Q-block is the *provenance*. So "give answers a more durable home" is already satisfied **by linking,
   not by moving**.
3. **Size is managed by archiving, not re-homing.** When the router grows unwieldy, **old, fully
   answered + routed Q-blocks** move to a new **`docs/owner/maintainer-question-router-archive.md`**
   (newest-kept-here, oldest-archived), with the main file keeping a pointer — exactly mirroring the
   proven **`current-state.md` → `current-state-archive.md`** split. Because references are plain text,
   the archived `Q-0XXX` stays grep-resolvable; the lone `#q-0017` anchor link is the only thing to fix
   if/when Q-0017 is archived. **Archiving is a reconciliation-pass (Q-0107) responsibility**, the same
   pass that already trims `current-state` — so the bulk move happens under an established, careful
   cadence rather than ad hoc.

**Why not the two options as posed.** *"Leave it all in the router"* ignores the real size friction.
*"Slowly re-route answers elsewhere"* (move the canonical record out) would orphan the Q-number anchor
1,307 files depend on — the owner's exact concern. The synthesis keeps provenance stable **and** gives
conclusions durable homes **and** controls size.

**Applied this session (docs-only):** recorded the convention in `ai-project-workflow.md` §9 (the
router-convention home) + added the archive step to the reconciliation routine. The actual first bulk
archive is left to the next reconciliation pass (it is not due — band marker #1500, next at #1530), so
this session changes the *rule*, not 200 blocks of content.

**Home:** this Q-block (canonical) + `docs/owner/ai-project-workflow.md` §9 (the convention) +
`docs/operations/autonomous-routines.md` (the reconciliation archive step). Related: **Q-0060**
(append-only / accept-and-reconcile), **Q-0107** (reconciliation pass owns ledger trimming), **Q-0104**
(route durable conclusions), **Q-0166** (fix drift on sight), the `current-state-archive.md` precedent.

### Q-0211 — DECIDED: `give` retired surface-wide — remove every give command, ban it from ever returning (2026-06-29)

> **Context.** Railway emailed repeated "Deploy Crashed for worker" overnight; the bot was offline.
> Root cause: a top-level **command-name collision**. `mining_cog` carried an admin-only `give` since the
> repo's initial commit (2025-08-10); **PR #1541** then added a second global `give` (economy peer
> coin-transfer `!give`/`!pay`). At boot the second `add_cog` raised `CommandRegistrationError`, so
> `mining_cog` failed to load, its declared entry points (`mine`, `minemenu`) vanished, and the STRICT
> identity-contract check **aborted startup** — a crash loop that never reached the gateway. The owner was
> asked how to resolve it and gave two escalating in-session directives.

**Area:** Bot product / command surface · **Type:** Owner directive (durable policy) · **Status:**
Answered (live, in-session) — Routed → enforcing test + this Q-block.

**The decision (two answers, in order).**
1. *Mining `give`:* **remove it entirely** (not rename) — it was a never-reachable-by-players admin tool
   squatting the most natural global verb; its only caller `mining_workflow.admin_grant` was removed too.
2. *Scope:* **"remove every give command and make sure none of that is ever added again."** → Delete
   **all three** commands named `give`: mining's admin grant, economy's `!give`/`!pay` peer transfer
   (**including the feature** — owner chose "delete it all, incl. feature"), and karma's `!karma give`
   subcommand (kept as **`!karma add`**). `give` is now **banned surface-wide** — no command may use it as
   a primary name *or* alias, at any nesting depth.

**Scope boundary (agent judgment, recorded for review).** The ban is on **commands**, not internal
service methods. Kept: `economy_service.transfer` (the audited balance-move primitive — predates the
feature, referenced as the canonical pattern precedent in 6+ files; no user can invoke it now) and
`karma_service.give` (internal grant logic behind `!karma add` / `!thanks`). `givexp` (xp_cog) is a
distinct command, untouched.

**Enforcement (enforce, don't exhort — Q-0132/Q-0194).** A CI guard in
`tests/unit/invariants/test_extension_integrity.py`:
- `test_no_banned_command_tokens_anywhere` — fails the build if any command/alias named `give` is ever
  re-added (`BANNED_COMMAND_TOKENS = {"give"}`; recurses into group subcommands).
- `test_no_duplicate_top_level_command_tokens` — the broader root-cause guard: catches **any**
  top-level command name/alias claimed by two distinct commands at CI time, **same-cog or cross-cog**
  (broadened + renamed from `…_across_cogs` on 2026-07-01 after the fishing `dock`/`sail` *same-cog*
  collision crash-looped boot — PR #1600 — which the original, de-duplicating claimants by cog, missed).
  The runtime `command_surface_ledger` only sees duplicates *after* every cog loads — which a collision
  prevents — so it could never catch this class; the static check can.

**Home:** this Q-block (canonical) + `tests/unit/invariants/test_extension_integrity.py` (enforcement) +
`.claude/CLAUDE.md` § Helpers "Exact-name guard (Q-0200)" (the sibling same-module guard this extends
cross-cog). Related: **Q-0200** (exact-name collision guard), **Q-0194** (friction → guard), **Q-0132**
(enforce, don't exhort).

### Q-0212 — DECIDED: bot owner has full bot-config authority in any guild they're in (2026-06-30)

> **Context.** Owner request: *"as bot owner I always have full bot permissions in any server that I'm
> in, even if I don't actually have permissions there — not to alter the server, but to make sure the
> bot is properly set up and has the right settings enabled, like the AI and which channels it can do
> certain things in."* Research found the bot already treats the configured owner
> (`config.BOT_OWNER_USER_ID`, the `PermissionTier.PLATFORM_OWNER` allowlist) specially for **AI scope**
> (`_derive_scope` → `AIScope.PLATFORM_OWNER`), **global settings** (owner-only), and a
> **bootstrap-command channel bypass** — but there was **no** override for *per-guild configuration
> authority*: a bot owner who is a plain member of a guild resolved to `tier="user"` and was denied by
> every guild-config seam, so they could *open* `!settings`/`!setup` but not actually apply AI / channel
> / setup changes.

**Area:** Governance / authority · **Type:** Owner directive (durable policy) · **Status:** Answered
(live, in-session) — applied + routed to a single-source helper + tests + `capability-authority.md`.

**The decision.** The configured bot owner holds **full bot-*configuration* authority in any guild they
are a member of**, even without Discord permissions there (set the bot up, AI policy, command channels,
settings, governance writes). This is *configuration* authority, not "moderate/alter the server" — it
exists so the owner can always make the bot work correctly.

**Implementation — one source of truth, wired into every authority seam.** A single helper
`config.is_platform_owner(user_id)` (config is a layer-free leaf importable everywhere) is the only
thing each seam keys on:
- **Governance:** `capability.actor_holds_capability` (step 3, after target-guild membership, before the
  revoke overlay — see `capability-authority.md` §1), `resolver._resolve_member_tier` (elevates to the
  `owner` visibility tier → feeds `resolve_visibility` / `resolve_execution` / `can_execute`),
  `writes._validate_authority` (governance writes = per-channel subsystem visibility).
- **Services:** the five duplicated `_check_admin` gates (`ai_policy` / `ai_instruction` /
  `ai_orchestration` / `btd6_source` / `help_overlay`) + `setup_access` (`is_setup_admin` /
  `can_apply_setup` / `can_apply_setup_by_id`).
- **Views:** the canonical `base.interaction_is_admin` + new `base.member_is_admin`, with the inline raw
  `guild_permissions` config gates (AI panel/behavior/tools, settings command-access, essential_setup)
  routed through them — so the owner can *see & use* the config UI, not just pass the mutation check.
- Consolidated the pre-existing inline `== BOT_OWNER_USER_ID` checks (settings global scope, `ai_tools`,
  `bot_knowledge_service`, `_derive_scope`) onto the same helper.

**Scope boundary / safety (agent judgment, recorded for review).** Purely **additive** — only ever
*grants* the one configured owner id; one-user blast radius; no existing user loses access. The
governance override sits **after** the "actor must be a member of the target guild" check, so it does
**not** weaken the cross-guild invariant ("authority bound to the write target"). It deliberately does
**not** broaden command-access beyond the existing bootstrap bypass, and does **not** touch
feature/game-admin moderation gates (e.g. starboard/tickets/moderation/game panels) — the directive is
*bot configuration*, not "run everything everywhere." If the owner ever wants this off, unset
`BOT_OWNER_USER_ID` (the same switch that governs every other owner power).

**Home:** `disbot/config.py` (`is_platform_owner`, single source) + `docs/capability-authority.md` §1
step 3 (canonical authority contract) + `disbot/governance/permission_tiers.py` PLATFORM_OWNER docstring
+ `tests/unit/test_platform_owner_override.py` (every seam). Related: **Q-0098** (setup-delegate apply
authority — the sibling below-floor grant), **Q-0048** (read-only AI tool posture), **Q-0200** (exact-name
helper guard — `is_platform_owner` is the canonical owner-check that supersedes the inline duplicates).

**Completeness follow-up — #1577 (2026-06-30).** #1573's view sweep was **incomplete** (a grep
truncated at 50 results), so the owner *still* hit "❌ Administrator permission required." on the AI
policy/routing panels (owner-reported, with screenshot). Two whole gate classes were missed and are now
fixed: **(1)** the `views/ai/policy/*` + `views/ai/routing/matrix.py` + `views/{xp,roles}/main_panel.py`
`interaction_check`s (now routed through `views.base.interaction_is_admin` / `member_is_admin`), and
**(2)** the cog command **decorators** — `@commands.has_permissions(administrator=True)` (101) +
`@app_commands.checks.has_permissions(administrator=True)` (28), which gate `!ai`, `/setup`, etc. *before*
the body runs. A new seam, **`core/runtime/permission_checks.py`** (`admin_or_owner` / `app_admin_or_owner`
— administrator OR `is_platform_owner`, raising the same `MissingPermissions` for non-owners), replaced
**every** `administrator=True` decorator bot-wide. The feature-admin **view** gates the #1573 note said it
left alone (starboard / tickets / btd6 event flow / blackjack admin toggle) were **also** made owner-aware
this pass — so the refined scope boundary is: the owner now passes **every `administrator`-tier gate**
(commands + views) and the moderation panel (via `can_execute` → owner tier); still **untouched** are
`manage_roles` gates (server-*role* mutation = "altering the server", outside the directive) and the bot's
own-capability checks (`me.guild_permissions`). **Enforce, don't exhort (Q-0194):** two CI guards now fail
the build on a re-introduction —
`tests/unit/invariants/test_owner_override_guards.py::{test_no_raw_admin_in_view_interaction_check,
test_no_admin_only_command_decorator}` — the exact miss-class #1573 shipped.

**Third extension — #1602 (2026-07-01): owner bypasses ALL permission gates, not just administrator.**
Owner directive *"make sure that I can do everything with this bot as owner"* (screenshot: `/help → Roles
→ Role Menus → New Menu` → "You need the Manage Roles permission to do that"). #1573/#1577 covered only
`administrator`; specific-permission gates (`manage_roles`, `manage_guild`, `manage_channels`,
`manage_messages`, `moderate_members`, `create_instant_invite`) still denied the owner. This **resolves the
original scope tension** (Q-0212 first read as "config, not alter the server"; the owner has now made it
explicit — *everything*). `core.runtime.permission_checks` is generalized to any permission
(`member_has_perms_or_owner(user, **perms)` / `perms_or_owner(**perms)` / `app_perms_or_owner(**perms)`;
`admin_or_owner` etc. become thin wrappers), and **every** `has_permissions(...)` decorator (49 across 18
cogs) + inline `guild_permissions.<perm>` user-gate (18 across ~12 cogs/views — role menus, role hub,
mining, channel, proof-channel, btd6, role-grants) now routes through it. **Untouched by design:** the
bot's own-capability checks (`me.guild_permissions`), informational reads, and the moderation surfaces
(the owner already passes those via the `can_execute` governance path → owner tier). **Enforcement:** the
decorator guard is generalized to *any* `has_permissions(...)` and a new `test_role_surface_gates_are_owner_aware`
pins the role views — completeness is machine-checked, not scoped by judgment (the fix for the three
narrow-scope round-trips #1573→#1577→#1602). Home: `disbot/core/runtime/permission_checks.py` +
`tests/unit/invariants/test_owner_override_guards.py`.

### Q-0213 — DIRECTED: full-access Railway token + credential set is deliberate — the whole project runs fully automated (2026-07-02)

> **Context.** After the Railway audit session (#1638) recommended scoped project tokens + account-token
> rotation, the owner directed in-chat: *"it has been deliberate that this token has full access, claude
> is the only one that has access to it and also the main editor of the repo, I want it this way so you
> don't have to rely on me to enter certain values or create extra workers or any of those things, you
> also have a test bot token and access to API keys … so the whole project can be completely automated."*

**Decision (owner-directed):**

1. **The full-access Railway account token stays in agent containers by design.** Claude is its sole
   holder and the repo's main editor. The #1638 custody recommendation (scoped project tokens + rotate
   the account token) is **DECLINED** — recorded as a conscious, accepted risk, not an oversight.
2. **The credential set exists to remove owner-dependency:** Railway account token, the test-bot Discord
   token (application **"Galaxy Bot"**, id `1298426054636994611` — note the env var is misleadingly named
   `DISCORD_BOT_TOKEN_PRODUCTION` in agent containers), and provider API keys (`OPENAI_API_KEY` verified
   present; Anthropic key lives in the Railway worker vars). Agents should **use** these — entering
   values, creating services/workers, wiring environments — rather than routing such steps to the owner.
3. **Re-scopes the Q-0130 envelope:** agents may now operate the **Railway control plane** directly —
   service/environment configuration, variables, deploy-affecting settings, creating services — with
   read-back verification and a session-log record of every change. The old "deploy/restart/scale/
   rollback stay the maintainer's" line is superseded for *routine* operations.
4. **The standing safety brake is unchanged** (this is the automation grant's boundary, per the working
   agreement's irreversibility rule): destructive or hard-to-reverse operations — `*Delete` mutations,
   backup/volume **restores**, anything that can lose data, plan/billing changes — remain **ask-first**,
   every time. Convention: no automation ever calls a delete/restore mutation.
5. **Recorded operational history (same exchange):** Railway's *wait-for-CI* deploy gating was tried
   before and **"kept failing due to the fast merges"** — R1 of the Railway plan is dropped; do not
   re-enable on the current repo. (Mechanism + the new-repo design condition live in
   `docs/planning/railway-setup-plan-2026-07-02.md` §6.)

**Executed under this grant (2026-07-02, PR #1640, each read-back-verified):** dashboard + botsite
watch-paths; botsite healthcheck `/healthz`; a $15/month **soft** usage alert (email-only, no hard
limit). **Discovered:** Railway-native volume backups (schedules *and* manual) return `Not Authorized`
on the Hobby plan — plan-gated, not token-gated — so the pg_dump workflow gained a monthly 400-day
retention tier as the compensating layer (owner one-time step: raise the repo's artifact-retention
setting to 400 days). Homes: `docs/planning/railway-setup-plan-2026-07-02.md` (plan + statuses),
`docs/operations/production-deployment.md` (envelope + backups), `.github/workflows/backup-db.yml`.

### Q-0214 — DECIDED: the finalised memory system's four structural retention choices (2026-07-02)

> **Decided — owner picked all four live via the in-chat question panel (2026-07-02).**
> Context: the owner-directed retention/context-economy design session (PR #1643,
> [`docs/planning/memory-retention-and-context-economy-plan-2026-07-02.md`](../planning/memory-retention-and-context-economy-plan-2026-07-02.md))
> converged on a sim-tested, adversarially-reviewed policy and surfaced four decisions the evidence
> could not settle — pure owner-values calls (the sim proved each safe either way). Asked live via
> the in-chat question panel; the owner picked the recommended option on all four.

**Area:** AI-memory / docs system / substrate-kit · **Type:** Owner decisions (structural, durable)
· **Status:** Answered (live, in-session, 2026-07-02).

**The four decisions (verbatim options chosen):**

1. **Session-log retention mode = "Delete + tombstones."** The kit's default posture is
   delete-with-tombstones (bounded corpus by construction; one grep-visible index line per pruned
   log; bodies one `git show` away), not archive-everything — the lean-by-construction tiebreak
   applied, exactly as the plan's §6.2 framed it. Harvest-gating (per-file committed evidence) is
   the safety condition that makes this posture acceptable unattended.
2. **Owner inbox = "Website feed."** The `/updates` feed is the canonical surface for ⚑
   owner-facing lines. Implementation consequence (binding on the plan's PR 2):
   `scripts/export_dashboard_data.py` must read **pass-record harvest tables** in addition to raw
   logs, so pruning never blanks the feed; the 14-day log-window floor may be revisited once the
   harvest-fed feed is proven.
3. **Shrink duty = "Checker + routine."** No new per-session shrink ritual: mechanical prunes via
   checker+actuator, judgment prunes via the retention-debt routine issue. This **answers
   orientation-plan Workstream D** (the proposed standing shrink ender): the owner chose the
   mechanical/escalation design over a per-session ritual — the DISCUSS block Workstream D planned
   is superseded by this decision; growth-side enders (Q-0089/Q-0102) are unchanged.
4. **Rebuilt-repo decision-ledger depth = "Verdict + short why."** Each decided question keeps its
   ruling line + 2–3 lines of rationale + provenance link in `decisions.md`; full deliberation
   lives in git/PR history. (This repo's router keeps Q-0210 semantics unchanged — this decision
   shapes the **kit/rebuild** ledger format only.)

**Homes:** the retention plan (policy + PR specs, updated same session) ·
`docs/planning/fresh-rebuild-strategy-2026-07-02.md` §5.2 slot (context-economy engine) ·
orientation-cost-reduction plan Workstream D (superseded by decision 3).

### Q-0215 — DIRECTED: generalize presets-plus-manual-entry from numeric-only to every settings class in the rebuild grammar (2026-07-02)

> **Context.** A daily-review/brainstorm session asked the owner to re-confirm an architectural
> gap before Phase 3 starts: "every text-based function should have presets you can choose from —
> you should never have to write something yourself, but a custom-input option should exist
> wherever useful." Research showed this exact posture was **already decided** as Q-0070
> (2026-06-10) — presets + preset-then-edit + always-available manual entry, for *every* setting
> class including authored text (DM templates, AI instruction bodies) — but the rebuild design
> spec (`rebuild-design-spec-2026-07-02.md` §2.5) had only carried the shipped **numeric**-presets
> mechanism forward verbatim, without generalizing it in the grammar itself. The owner confirmed
> the posture stands and asked for it to be folded into the spec rather than left as a
> settings-audit-only convention.

**Decision:** `SettingSpec` gains a `preset_kind: enum {none, numeric, text} = none` field (§2.5).
`text` extends the shipped numeric-presets UX (pick a preset, edit from it, or write your own) to
any `str`-typed setting. Compile rule: a `str`-typed spec with a non-empty `presets` tuple must
declare `preset_kind="text"`, and manual entry can never be the *only* path removed by a preset
list — the grammar enforces Q-0070's three-requirement posture mechanically instead of relying on
each port remembering it.

**Scope boundary:** this decides the **grammar primitive** only — it does not re-open Q-0070's
deferred "AI-suggested template/preset advisor" idea
(`docs/ideas/settings-presets-and-ai-template-advisor.md`), which stays captured-only behind the
AI per-exposure gates.

**Homes:** `docs/planning/rebuild-design-spec-2026-07-02.md` §2.5 (new field + compile rule) and
top-of-doc addendum; supersedes nothing — extends Q-0070's already-decided posture into the new
repo's grammar.

### Q-0216 — DIRECTED: multi-select promoted from bot-code convention to a rebuild-grammar compile rule (2026-07-02)

> **Context.** Same brainstorm session, second architectural question: "multi-select menus should
> also be the standard wherever possible." Research found this was **already owner-directed** for
> the current bot as Q-0205 (2026-06-24) — "multi-select is the preferred idiom for 'pick which of
> these to turn on'" — and applied in specific PRs (Essential Setup logging-channel step, the
> block-spam toggle row), but never promoted into the rebuild's manifest grammar as a default rule
> new ported/generated selectors would inherit automatically. Current-bot count at the time of
> research: ~125 `Select` menus, only ~20 genuinely multi-select (~5:1 single-select-by-default),
> confirming the gap is real, not just a preference already satisfied everywhere.

**Decision:** `SelectorSpec` (§2.4) gets a compile-time default rule: when a selector's `on_select`
target is a `BindingSpec` with `multiplicity > 1`, or otherwise backs a "pick which of these apply"
choice, `max_values` defaults to that multiplicity (or full option count for unbounded pick-many)
instead of Discord's single-select default. A single-select override requires explicit
justification — the grammar treats "one at a time" as the exception for a naturally multi-valued
choice, not the default. Scalar pickers (channel/role/member selectors backing a true
single-value `SettingSpec` or a `multiplicity=1` binding) are unaffected.

**Homes:** `docs/planning/rebuild-design-spec-2026-07-02.md` §2.4 (new compile rule) and
top-of-doc addendum; extends Q-0205's already-directed idiom from the current codebase into the
new repo's grammar as a mechanical default rather than a per-PR judgment call.

### Q-0217 — EXECUTED: the linchpin-validation's six grammar amendments + five spec corrections folded into the design spec (2026-07-02)

> **Context.** The linchpin-validation spike (#1639, `rebuild-linchpin-validation-2026-07-02.md`)
> already recommended **GO — proceed to Phase 3, with the six grammar amendments folded into the
> design spec first (a half-day docs pass, no re-design)**. This was not a fresh decision — the
> owner asked in this session which plan steps are still left and which must happen before Phase 3
> starts; the answer surfaced that the already-approved fold-in had not actually been executed yet,
> and the owner asked for it to be done now.

**Executed, source-verified against the spike doc's §2.3/§3 tables:**

1. **G-1 — `GatewayListenerSpec`** (§2.8): the load-bearing one — raw Discord gateway listeners
   (server-logging's 8, karma's react-to-thank, blackjack's reaction-join) had no grammar primitive.
2. **G-2 — list-valued settings** (§2.5): `value_type="list[int]"` etc. + kernel add/remove/clear
   workflows, covering the shipped exclusion-list pattern (#1594) and its recurrences.
3. **G-3 — `AnnouncementRouteSpec`** (§2.8): event-class → template → bound-channel as data.
4. **G-4 — `CommandSpec.cooldown`** (§2.2): declares the shipped `@commands.cooldown` rate limit,
   previously silently dropped by the grammar at port time.
5. **G-5 — declarative validator `bounds`** (§2.5): `(lo, hi)`/`max_len` fields replacing trivial
   tier-3 validator refs.
6. **G-6 — command-pool kind-scoping** (§2.2, §3.1): prefix/slash are disjoint Discord namespaces;
   the pool is now partitioned per `CommandSpec.kind`, not one flat pool.
7. **Harness-mechanism naming** (§6): corrected from "testcontainers + dpytest" to what `parity/`
   actually is — fake HTTP over the real discord.py state machine, local Postgres, no new deps.
8. **Evals/harness composition** (§6): evals stay the AI-answer oracle; the golden harness owns the
   deterministic command/panel surface; they compose, they do not merge into one asset.
9. **K10 CI requirement** (§6): `golden-parity` needs a real Postgres service container in the new
   repo's CI — this repo's own `code-quality` runs none, which is why the harness skips there today.
10. **Determinism-pinning budget** (§6): eight nondeterminism classes were pinned for command
    capture; scheduled-loop capture will pay a comparable cost again — budgeted, not assumed free.
11. **Clock + RNG as injectable kernel services** (§1.2): a new kernel requirement the spike
    surfaced — unseeded RNG, real-TTL caches, and `datetime.now()`-derived ids are all
    AST-fenced violations outside `kernel/clock`/`kernel/rng`, making every surface golden-testable.

**Status:** the `rebuild-design-spec-2026-07-02.md` no longer has an outstanding fold-in debt
against the linchpin-validation verdict. Remaining pre-Phase-3 items are unchanged from the
strategy doc's §3: owner sign-off on the design spec, and the Phase 2.5 cold-start proof (not yet
run).

**Homes:** `docs/planning/rebuild-design-spec-2026-07-02.md` §1.2/§2.2/§2.5/§2.8/§3.1/§6 + top-of-doc
addendum; source: `docs/planning/rebuild-linchpin-validation-2026-07-02.md` §2.3/§3.

### Q-0218 — DIRECTED: commit the multi-agent-workflow usage-consent flag so fleet sessions stop re-prompting (2026-07-02)

> **Context.** The owner reported that every remote fleet session (ultracode) prompts him for permission
> before starting a `Workflow`, asked whether that is a recently-added Anthropic requirement, and asked to
> add it to the always-allowed list. Investigated against the *running* CLI binary (`/opt/claude-code/bin/claude`,
> not memory — Q-0120).

**Finding (verified in the binary).** The prompt is the **multi-agent-workflow usage-consent gate**
(`skipWorkflowUsageWarning` / `recordWorkflowUsageConsent` / `workflowNeedsUsageConsentPrompt`; telemetry
`tengu_workflow_usage_warning`), **not** a tool permission. It ships with the newer Workflow/ultracode
feature. On *accept*, the runtime persists `skipWorkflowUsageWarning: true` to `~/.claude/settings.json`
(**user** scope); ephemeral remote containers wipe that each session, so it re-prompts on every boot
(this container started with no `~/.claude/settings.json`). It is a *usage acknowledgement*, so it is **not**
in `permissions.allow` and adding `Workflow`/`Task`/`Agent` there cannot silence it — and `defaultMode` is
already `bypassPermissions`, so those tools are already permission-allowed.

**The scope catch.** The consent reader honors the flag only from **user / local / flag / policy** settings —
**never committed *project* settings** (`.claude/settings.json`). So the flag cannot go in the shared project
settings (it would be silently ignored). The one repo-committable scope it reads is
**`localSettings` = `.claude/settings.local.json`**, previously gitignored.

**Decision (owner-directed in-session; the Q-0106 executable-config exception applies — the maintainer is the
live reviewer, so applied directly with this provenance Q).** Make `.claude/settings.local.json` a **tracked,
shared** file carrying `{ "skipWorkflowUsageWarning": true }`, and un-gitignore it (with an explanatory
comment at `.gitignore`). Every fresh fleet clone now boots pre-consented. Reversible in one commit.

**Cleaner long-term alternative (offered, not applied).** Set the flag once at the code.claude.com
**environment** level (env config / setup script → `flagSettings`/`userSettings` at boot), which keeps
`settings.local.json` personal/gitignored. If the owner adopts that, revert the un-gitignore.

**Homes:** `.claude/settings.local.json` (the flag) · `.gitignore` (the tracked-on-purpose comment) ·
`.sessions/2026-07-02-workflow-consent-fleet-config.md` (session log).

---

### Q-0219 — DECIDED: the engine/declaration/seam standard — how "plug-and-play for any future function" reconciles with centralization (2026-07-03)

> **Context.** Rebuild Phase-A **Stage-1 global review** (owner-live session, PR #1679). The owner
> stated the generalization requirement for the new bot: *"every foundational function becomes a
> plug and play entry for any possible new function that may be added in the future… something
> that defines the base structure, but is steered by the actual function calling it"* — and
> himself flagged the tension: *"the way I'm explaining it it sounds like the methods would live
> in multiple places, which would conflict with the centralization idea."* Discussed live; the
> owner escalated the session to Fable 5 max specifically to review + lock this standard.

**Decision (owner-agreed, escalated-review sharpened):** **what varies per caller is data, not
code.** One engine per domain in exactly one place; callers steer it with **explicit
declarations**; three steering tiers (declarative params → composition → **named registered
handler seam** as the only per-caller code); **handlers are leaves** (compute + return, never
orchestrate — counted under the escape-hatch ratchet); steering is **never by call-site
identity** (user/authority context arrives as explicit request data, not caller inspection);
**second-consumer rule** — build the general engine only when a real second consumer exists now
or clearly imminent, otherwise keep logic specific **behind a clean seam** ("plug-and-play ready"
= the seam discipline, so later generalization refactors the inside without moving callers);
**schema-growth guardrail** — a declaration needing conditionals is the signal for a Tier-3
handler, never for growing the schema into a language; schema fields are added only on ≥2
recurring consumers.

**Binding for:** every Phase-B plan, applied to every foundational function.
**Homes:** `docs/planning/rebuild-stage1-global-review-2026-07-03.md` §2 S-1 (full statement);
design-spec §2.9/§2.10 are the shipped shape it binds to; enforcement idea
`docs/ideas/rebuild-schema-growth-ledger-2026-07-03.md`.

---

### Q-0220 — DECIDED: foundation-before-consumer build ordering; card engine promoted + welcome re-homed as its acceptance test (2026-07-03)

> **Context.** Same Stage-1 session. The review found the frozen BUILD-PLAN's welcome row (L1b)
> depends on both the visual card engine (L1c — a later band) and role (three slots later in the
> same band). Owner ruling on the class: *"the foundation is correct first — that should be the
> standard practice for every function"*; and the card engine specifically *"must not hold only
> one focus — an elaborate system that can create custom cards on the run."*

**Decision:** **S-2 ordering rule** — an **engine-class** dependency (one-to-many foundation
engine) always ports before its first consumer; a **peer-class** dependency (feature consuming
another feature's content) may ship as a **declared-seam deferral** (seam in the manifest day
one, dormant, labeled activation). Applied dispositions: **welcome moves out of the L1b spine to
L1c immediately after the card engine** (fixing both of its inversions; it becomes the engine's
first-consumer acceptance test, mirroring mining-last); **deathmatch-gear and explore-mining stay
put via declared-seam deferrals; mining-last stands.** The card engine is a first-class S-1
engine (CardTemplateSpec declarations; 5+ consumers) with the **image-source seam declared from
day one** (static/asset at L1c; generated images activate with Q-0221's provider at L4). Every
Phase-B layer plan runs an explicit internal-order dependency check against S-2.

**Homes:** decisions log §2 S-2 / §3 (audit table) / §4 D-1; Gate-0 folds the reorder.

---

### Q-0221 — DECIDED: media generation (prompt→image) added to the capability corpus (2026-07-03)

> **Context.** Same Stage-1 session. The owner: *"I was also thinking about using an API key to
> create real looking images based on prompts, which could be used to display the contents of a
> story for the dungeons and dragons story game etc."* Nowhere in the 43-subsystem corpus — a
> genuinely forgotten capability caught by the review.

**Decision:** add a **`MediaGenerationSpec`** capability in the **L4 AI band**: provider call =
egress escape hatch behind a **provider-agnostic adapter**; consumed via the card engine's
image-source seam (Q-0220). **Mandatory cost/abuse posture at declaration time** (free-mission =
owner pays): per-guild quota + global budget cap + cache-by-prompt-hash + owner kill switch +
**default-OFF per guild** (image_moderation precedent); prompt content-safety filter before
egress; no user PII in prompts. Feasibility grounded: `OPENAI_API_KEY` already in agent
containers (Q-0213). **The D&D-style story game itself is NOT scheduled** — recorded on the
known-options menu as a named future consumer only.

**Homes:** decisions log §4 D-2; Gate-0 adds the corpus row + spec section.

---

### Q-0222 — DECIDED: the cutover model — 3-phase, container-first, manifest-driven import (2026-07-03)

> **Context.** Same Stage-1 session. The BUILD-PLAN's cutover story was its thinnest area. Owner:
> *"first only test the new bot directly through the agent's own environment… every session
> should live test what it's built when I'm present, so we can go over every new command one by
> one… installed something that allows us to export the data from the old bot but only the data
> that's actually requested by the new bot… after that we can switch to superbot's token and
> discontinue the old bot entirely."* Verified live: the test-bot token (Galaxy Bot, Q-0213) +
> `DATABASE_URL` are present in agent containers — CUT-1 has zero setup prerequisite.

**Decision:** **CUT-1 container-only live testing** — new bot runs only in the agent container on
the test token in the test server; per-command owner sign-off ("passes when it beats the old
bot"); kernel rails from day one: guild allowlist, single-instance lock, and a **per-command
`verified_live` sign-off registry generated from the manifest** (the live-test checklist is an
artifact). **CUT-2 manifest-driven selective import** — every StoreSpec declares an `import`
mapping (old→new or `fresh-start`+reason); the importer walks the manifest snapshot, copies only
declared needs, and emits a **full-coverage disposition report over every old-DB table** (every
"not copied" is a decision, never an oversight); every Phase-B component plan gains a mandatory
Import-mapping section. **CUT-3 token swap** — telemetry/golden capture before any freeze → short
freeze → final import → real-token swap → old bot retired, kept runnable through a rollback
window (N set at Stage 3). Concretizes design-spec §5.2's "fresh chain + one-time importer";
amends §5.4.

**Homes:** decisions log §4 D-3; Gate-0 replaces the thin cutover text.

---

### Q-0223 — DECIDED: substrate-kit fully completed before new-repo bootstrap (stale figure corrected); 43-subsystem return is not automatic — Stage-2 triage verdicts (2026-07-03)

> **Context.** Same Stage-1 session, two rulings. (1) Owner on the substrate-kit: *"that should
> definitely be fully completed and I was led to believe that it was already complete."* Session
> verification: the strategy doc's ~45–55% figure is **stale** (predates #1649) — the `loop/`
> nervous system + all five hooks + real mode branching are shipped, **422 kit tests green**,
> packaging present; honest state ~90–95% with a named tail. (2) Owner on the corpus: *"some
> features may not need to be reintroduced, or at least not yet until we have those planned to
> completion as well… some features might be outdated or misplaced."*

**Decision:** **(a)** Kit completion is a **named pre-bootstrap gate** (parallel to Stages 2–3,
binding only the new-repo bootstrap), tail = ① re-entrant `transaction` → atomic
`apply_review_verdict` (own PR; the one real correctness bug), ② standalone extraction-proof CI,
③ extraction + owner-named rename. **(b)** Stage 2 assigns **every** BUILD-PLAN §1.1 row a triage
verdict — `bring back` / `defer until planned to completion` / `drop` / `re-place` — with
one-line reasons; `defer`/`drop` rows leave the Phase-B queue and their dependents re-check under
S-2 (Q-0220).

**Homes:** decisions log §4 D-4/D-5 + §5 (corrections);
`docs/ideas/substrate-kit-review-followups-2026-07-02.md` (tail item ①, now scheduled).

---

### Q-0224 — DECIDED: command naming — namespace by shared verb (computed from the corpus), flat otherwise, with safe defaults (2026-07-03)

> **Context.** Rebuild Phase-A conventions freeze (owner-live, PR #1680). Deciding the K1 registry's
> input scheme before the subsystem walk. Owner: a hybrid that *"only uses explicit subcommands for
> commands that need to be reused across multiple instances,"* with *"a proper rule for this to
> prevent this becoming a liability,"* and *"most of those commands work with a standard default if
> there is a clear usecase that gets primarily used by users."*

**Decision:** a command takes the grouped form `/area verb` **only when its verb is shared across
2+ subsystems**; a uniquely-used verb stays a flat top-level command. **The shared-verb set is
computed once at design time from the known 271-command corpus** — so no collision is discovered at
runtime and no flat command is ever force-renamed later (the liability); K1 permanently reserves
each flat name. Commands with an obvious primary use **work with no arguments** (sensible default),
**except** destructive/ambiguous actions, which never default to acting.

**Homes:** `docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md` §1; Stage-2 runs
the corpus computation; Gate-0 folds the rule into the naming grammar.

---

### Q-0225 — DECIDED: the four-rung invocation ladder + additive custom triggers + the fuzzy typo matcher + AI orchestration (2026-07-03)

> **Context.** Same session. The owner specified: both slash and prefix **plus** a Dank-Memer-style
> configurable trigger (`pls <command>`) settable per guild/user/channel and **additive** (*"if one
> word is set for a channel it should not mean that a word set for the whole guild wouldn't work
> there… it just gets an extra option"*); **silent on non-matches** (*"never give error responses
> for wrong commands… does not spam the chat"*); the **fuzzy matcher** that *"decides when a typo is
> a real command"* (the thing he first called "the global parser"); and expanding the AI parser so
> it can *find the right commands* and *"initiate commands gated by a confirm/deny prompt"* — e.g.
> *"create 10 game channels for a D&D tournament for teams of 4"* → AI drafts a template → previews
> the outcome → user presses Accept → it runs.

**Decision:** one invocation engine, four front-ends resolving to the same declared commands:
**(1) exact** (slash + prefix + additive union of global/guild/channel/user custom triggers,
validated when set — min length, common-word blocklist, per-scope cap — and **silently ignored on
no-match**); **(2) fuzzy** typo matcher, deterministic/AI-free, **three tiers** (very-close+safe →
run directly; close → private "did you mean"; far → silent); **(3) NL intent** (language → one
command; the existing central NL stage elevated to mainstream, router **generated from the
manifests**); **(4) NL orchestration** (goal → multi-step **draft** → preview → Accept → atomic
audited apply). Rungs 1–2 need no AI (deterministic-first preserved; the parser is never a
dependency of a core command). Rung 4 **is the already-designed draft lane with the AI as a second
producer** — one pipe, human or AI. **Default posture = hybrid:** answer freely, require a clear
signal (mention/reply/channel) before acting; destructive AI-reached actions always confirm.

**Homes:** conventions log §2; Gate-0 (interaction runtime K8); the D&D example is the
compound-composition canary (FINAL-REVIEW uncertainty).

---

### Q-0226 — DECIDED: moderator actions declared as data (resolves the ModerationActionSpec uncertainty → envelope) (2026-07-03)

> **Context.** Same session. Owner: *"whatever is the best option, I think declaring as data was
> the better option to make it testable."*

**Decision:** a mod action (warn/timeout/kick/ban) is a **declarative envelope** (target,
hierarchy check, DM, cleanup, audit, log route) the engine runs; only the escalation decision stays
a small Tier-3 handler. Chosen for testability (declared = simulable + golden-testable). Resolves
the FINAL-REVIEW `ModerationActionSpec` uncertainty **in favor of the envelope**; grammar-level, so
decided before the Gate-0 freeze, with the plan's ~1-hour spot-check (express one real action
against the grammar) as the pre-freeze confirmation.

**Homes:** conventions log §3; Gate-0 grammar plan.

---

### Q-0227 — DECIDED: one authority layer + a global bot-owner override with a verification test and transparent audit (2026-07-03)

> **Context.** Same session. Owner: one authority layer *"but it should also include the bot owner
> ID, like in the current bot, and it should be verified that every command works for the bot owner
> in every server, so I can help my friends set up commands that may normally only be able to work
> for server owners, like the setup."*

**Decision:** every action carries a **single declared authority label** mapped to roles/Discord
permissions in one place, re-checked at execution time; **on top sits a global bot-owner override**
(by ID, per Q-0212) — the bot owner can run any command in any server, including server-owner-gated
ones. Two clauses added: **(a)** a mechanical parity test — "bot-owner can run everything,
everywhere" walks every command; **(b)** transparency — a bot-owner action in another server is
**loudly audited to that server's log**, never silent. Pins Q-0212 as a rebuild grammar contract.

**Homes:** conventions log §4; Gate-0 authority (K6).

---

### Q-0228 — ENDORSED (owner-confirmed as foundations to document + decide): invocation-stack centralizations (2026-07-03)

> **Context.** Same session, owner asked *"are there any other things related to this we could
> centralize?"* → then confirmed: *"yes all the things you mentioned are good candidates to
> further think about and properly decide upon, your recommendations are good foundations and
> should be documented."* So C-1…C-7 are **endorsed directions** (documented, to be decided in
> detail at Gate-0) — not yet frozen contracts, but no longer merely speculative proposals.

**Proposed (agent-recommended):** **C-1** one command **resolver** all four rungs funnel through
(authority + arg validation + cooldown + audit — the convergence point, strongest recommend);
**C-2** one **preview/confirm/apply draft pipeline** shared by AI drafts, fuzzy-corrected
destructive actions, NL actions, and human setup (one pipe, two producers); **C-3** one **template
primitive** (named reusable draft, human- or AI-instantiated; unifies the scattered setup/role/
channel templates + serves the D&D example); **C-4** one **response/result grammar**
(`WorkflowResult`); **C-5** one **fuzzy/"did-you-mean" engine** (fold the scattered `difflib`
uses); **C-6** one **cooldown/rate-limit engine** (also the abuse-posture home); **C-7** one
**description surface** feeding slash/help/NL-router/fuzzy/suggestions.

**Homes:** conventions log §6. **▶ Next:** each C-item's *detailed* decision (scope, contract
shape) lands in its Gate-0 / Phase-B plan; the owner endorsed all seven as worth building toward
(C-1 the command resolver is the load-bearing one — without it the four invocation rungs
re-implement authority and drift, a safety bug).

---

### Q-0229 — DIRECTED: broaden the `.claude/settings.json` allowlist with whole-MCP-server entries to cut permission prompts (2026-07-03)

> **Context.** Owner reported recurring permission prompts in sessions — including this one, for
> `send_later` "and some other things" — and asked *"how we can improve the always allowlist… I
> really never deny any requests, so isn't there a universal way to allow all actions you can
> do?"* Investigated the actual config (Q-0120: check ground truth, not memory).

**Findings.** `permissions.defaultMode` is **already** `bypassPermissions` and
`skipDangerousModePermissionPrompt` is already true — the file already *requests* universal allow.
The prompts persist because **on the Claude Code web/remote surface a project-file
`bypassPermissions` is not fully honored** (it's treated as advisory for safety); the surface
instead consults the explicit **`allow`** list, and MCP tools from the `Claude_Code_Remote` /
`github` servers weren't on it. `AskUserQuestion` "prompting" is **by design** (it *is* the
question UI, not a permission gate) — not fixable via the allowlist.

**Decision (owner-directed in-session; Q-0106 executable-config exception — owner is the live
reviewer, applied directly with this provenance Q).** Add **whole-MCP-server** allow entries —
`mcp__Claude_Code_Remote`, `mcp__github`, `mcp__codegraph`, `mcp__context7` (bare `mcp__<server>`
matches every tool on that server) — to `.claude/settings.json`. The destructive-ops **`ask`**
brake (rm -r, force-push, railway, sudo, psql, docker, …) is **left intact** — it deliberately
overrides bypass, matching the Q-0213 "destructive/irreversible stays ask-first" boundary.

**The truly universal lever, for the record:** the only switch above the `allow` list is the
**environment-level** permission mode on code.claude.com (or the in-session mode toggle) — the
file can't force it on the web because the surface downgrades project-scope bypass by design. If
the owner wants zero prompts for a class the allowlist can't cover, that's the place to set it.

**Homes:** `.claude/settings.json` (the four entries) · this Q (provenance) ·
`.sessions/2026-07-03-permission-allowlist-and-endorse.md`.

---

### Q-0230 — DECIDED: one unified help hub; admin is a permission-gated node inside it (2026-07-03)

> **Context.** Rebuild Phase-A hub-topology discussion (owner-live, PR #1684). Owner: *"everything
> should function as one help panel, but admin should be locked unless you have the right
> permissions, and admin should ideally be a button that opens a full admin help menu, which
> should also directly open with a `!admin` command."* Broadly agreed with the five working
> top-level buckets (Games/World · You · Community · Knowledge/AI · Admin), wants them refined.

**Decision:** a **single unified help hub** (not two player/operator trees); **admin is a
permission-gated node inside it** — a button locked unless the viewer has the authority (Q-0227
label, **re-checked at click time**, not at open), opening a full admin menu, also directly
openable via `!admin`. Top-level bucket set is a working spine; exact buckets + per-subsystem
placement are Stage-2 work.

**Homes:** `docs/planning/rebuild-hub-navigation-presets-2026-07-03.md` §1; Gate-0 PanelSpec/hub.

---

### Q-0231 — DECIDED: the navigation contract — Back+Home everywhere, persistent restart-safe panels, every node directly openable (2026-07-03)

> **Context.** Same session. Owner: *"every panel everywhere should have a back to help and back
> to parent hub available during all their stages, no matter how many times the panel got updated,
> and we should try to make the panels resistant against timing out too soon."*

**Decision (framework-guaranteed, injected into every rendered state — never per-panel
discipline):** **(1)** two distinct controls on every state at every depth across unlimited
re-renders — **Back** (pop the real navigation stack, contextual) and **Home** (jump to help root,
absolute); **(2)** every hub/sub-hub **directly openable by its own command** (generalizes
`!admin` to all nodes, S-1); **(3)** each panel **declares its semantic parent** so Back has a
target on direct entry; **(4)** panels are **persistent + restart-safe** (no per-instance timeout,
versioned custom_id, generated-from-state) — which *also* solves surviving the merge=deploy
redeploys (Q-0193): "don't time out too soon" and "survive constant redeploys" are the same fix,
free from the generated model.

**Homes:** hub-navigation log §2; Gate-0 NavigationSpec + persistent-view/versioned-custom_id
(design-spec decision 6).

---

### Q-0232 — DECIDED: per-guild interface presets with live preview; the existing (fragmented) surface is improved + centralized (2026-07-03)

> **Context.** Same session. Owner: the interface should be *"very easily customizable… include a
> couple of presets to fit any server"* (e.g. a game server needing btd6 info + moderation + server
> functions + message levels + light games), *"easily adjusted during the setup steps, with clear
> previews and logical presets… either go with a safe default"* — and *"this function already
> exists and works, but it should be improved and centralized."* Verified in source: setup
> `preset_select` (+ `preview_preset`) and the help overlay editor/projection exist and work;
> presets are reimplemented ≥7 times across services/views.

**Decision:** the hub is **customizable per guild**; **presets** (named bundles of per-guild
visibility config) reshape it, chosen at setup with a **live preview** (the preview *is* the
generated hub — no mockup), following the Q-0215/Q-0070 pick→edit→manual pattern with a
safe-default preset. **This is the preset primitive (Q-0215) + template primitive (C-3, Q-0228)
pointed at the hub — improve + centralize the existing working-but-fragmented surface** (setup
preset_select + help editor + ~7 domain preset impls → one primitive, one generated hub; the
existing code is the prior art to port). **Features declare their own preset membership**
(anti-drift). Presets ≠ triage (visibility per guild vs existence in the bot).

**⚠ Open sub-decision (owner):** preset exclusion = **hidden-but-runnable** vs **disabled
entirely**? Agent leaning: hidden = off by default, with a hide-without-disable toggle. Resolve
before §3 freezes.

**Homes:** hub-navigation log §3–4; Gate-0 preset primitive unification + setup wizard.

---

### Q-0233 — DIRECTED: build a critical-review rubric that finds the gap-classes we spot by instinct (2026-07-03)

> **Context.** After a session of reviewing the rebuild plan, the owner: *"do you now understand
> what I meant earlier with the forgotten steps, missing features and proper goals etc? I think it
> would be a good idea to create a rule or system that finds exactly the kind of things that we
> have been spotting today, to make it easier to review the rest of the bot in the same critical
> way."*

**Decision:** extract the session's findings into a reusable **critical-review rubric** — ten
finding-classes (dependency-order inversion · forgotten capability · thin/underspecified step ·
stale un-anchored state claim · fragmentation/reinvention · under-generalization · missing
cross-cutting standard · verification hole · UX/lifecycle-contract gap · naming/visibility/
collision), each a probing question with the day's real example and a mechanization tag
(human-probe / existing checker / build). Run it against **every subsystem in the Stage-2 walk** and
**every plan in Phase B** (it *is* the adversarial-completeness pass's checklist). The common thread:
*an artifact tells you what it does, never whether it's complete, correctly-ordered, non-duplicated,
verifiable, and consistent* — the rubric asks the questions the artifact can't self-report.
**Enforce-don't-exhort:** the mechanizable classes become checkers (extend
`check_plan_staleness.py` for un-anchored `NN%` now; build dep-order / thin-step / fragmentation /
verification-hole / UX-contract checkers against the rebuild's declared manifests); the judgment
classes stay human probes with the rubric as their guard.

**Homes:** `docs/planning/rebuild-critical-review-rubric-2026-07-03.md` (the rubric) ·
`docs/ideas/rebuild-critical-review-checkers-2026-07-03.md` (the mechanization backlog) ·
`.sessions/2026-07-03-critical-review-rubric.md`.

---

### Q-0234 — DECIDED: the new-feature correctness oracle + the plan-verification-fleet gate + the repo-as-artifact migration framing (2026-07-03)

> **Context.** Owner, resolving the rubric's class-8 verification hole and laying out the meta-plan:
> *"the way we prove a function is correct is we compare it against known bots and we personally
> test it together in the test server, so we can find out how it works and if it is logical and
> self explanatory to use. I intend to run this entire plan against multiple verification and
> research agents once it's fully done, to find out the final bits of improvements before moving on
> to the step by step planning and then the migration to the new repo, which is also a big plan of
> its own. My idea is to turn the current repo into an artifact that provides exactly the what the
> why and the how, and our new repo becomes the clean source of truth that makes it all real with a
> proper start that prevents reintroducing old mistakes."*

**Decision (three parts):**
1. **New-feature correctness oracle (resolves rubric class 8).** Two halves: **ported features** →
   parity goldens (match the old bot); **new features** → **competitor-benchmark + live co-test in
   the test server** asserting *works · logical · self-explanatory to use*, reusing the Q-0222
   `verified_live` per-command sign-off. Each feature declares its named competitor + specific
   behaviors + its live-co-test sign-off. "Self-explanatory" is a first-class acceptance criterion
   (only a human driving it live can measure it).
2. **GATE V — the verification-fleet pass.** When the plan is fully done, run it past **multiple
   verification/research agents** for the final improvements **before Phase B**, using the
   ten-class critical-review rubric (Q-0233) as their shared lens. Sits between Phase A and Phase B.
3. **Migration is its own big plan; repo-as-artifact framing.** Current repo → the **artifact**
   (what/why/how — the decision logs + rubric are its "why"); new repo → the clean **source of
   truth** with a proper start that prevents reintroducing old mistakes. The Q-0222 container-first
   cutover is this migration's execution arm.

**Homes:** rubric §class-8 (resolved) · `rebuild-planning-phase-2026-07-03.md` (Gate V + Migration
in the phase sequence) · `.sessions/2026-07-03-oracle-and-verification-strategy.md`.

---

### Q-0235 — DIRECTED: unify the UX-layout sims into one instruction-driven layout-success simulator; it defines settings, live co-test is the final review (2026-07-03)

> **Context.** Extending the hub/arrangement discussion, the owner: *"this is exactly a step where
> the simulations come into play, we could create deterministic or AI driven mockup menus to test
> and see which of the layouts have the biggest success rate when given a simple instruction like
> 'create roles' or 'play the mining game'"* — then, on the fragmentation: *"I even believe this
> exists in multiple places… that's one of the reasons this should become centralized quickly, so
> it can properly define the proper settings for everything, with a final review in the live bot
> testing."* Verified: five bespoke UX-layout sims exist (`claim_layout_sim`,
> `help_menu_grouping_sim`, `role_menu_layout_sim`, `settings_order_sim`, `setup_wizard_sim`).

**Decision:** build **one** layout-success simulator over the manifest that scores any generated
layout by **instruction-driven task success rate** (given only "create roles", does a user model
reach the right node?), with **deterministic** (CI/regression) *and* **AI-driven** (naive-user,
catches label ambiguity) user models — unifying the five existing sims. It **quantifies the
"self-explanatory" half of the Q-0234 oracle** and is the mechanism behind "the sim optimizes
arrangement" (Q-0230). **Pipeline:** the centralized sim **defines the proper settings/layout for
everything** (arrangement, grouping, defaults, order) → the **live bot co-test is the final
review** (the human signs off works·logical·self-explanatory on the sim's winner). The instruction
corpus is reused to test the NL router (invocation rung 3). Extends the simulation-driven-design
standing rule; ties fragmentation-cleanup urgency to the sim being able to tune bot-wide.

**Homes:** `docs/ideas/rebuild-layout-success-simulator-2026-07-03.md` ·
`docs/planning/simulation-driven-design-2026-07-02.md` (the standing rule) ·
`.sessions/2026-07-03-layout-success-simulator.md`.

---

### Q-0236 — DIRECTED: prepare (not run) two parallel ultracode sessions to brainstorm+audit the foundational mechanics against today's decisions (2026-07-03)

> **Context.** After the 2026-07-03 rebuild-decisions session, the owner: *"the correct thing to be
> doing now is sending out 2 ultracode sessions… NOT in this current session, this should be a
> preparation so that I can send out these 2 sessions in parallel to discover and document any
> possible related issues to everything we discovered today. Those 2 sessions should brainstorm
> thoroughly about any foundational mechanic and method we could possibly use and are using now."*
> Asked to research what a dedicated ultracode session can do first (done — official docs).

**Decision:** produce **two paste-ready, parallel-safe ultracode prompts** (this session prepares;
it does NOT launch them). Split by domain to avoid overlap: **Session A = the engine room**
(runtime/logic — grammar, namespace, invocation ladder, resolver, authority, audited-mutation/draft
pipeline, composition, events, lifecycle, persistence, cooldowns, DB/import, settings, substrate-
kit); **Session B = the surface + the proving** (hub/navigation, panel rendering, card+media
engine, presets/templates, help/description projection, response grammar, suggestion surface, the
rubric, the oracle, the layout-success simulator). Each prompt carries an explicit scope boundary,
the shared method (per-mechanic find-now-in-source + research-alternatives + pressure-test →
adversarial-verify vs source → completeness-critic loop → synthesize), the 10-class rubric as its
scoring lens, and a rubric-scored issues-ledger deliverable; each claims its own lane + own PR.
Owner-gated items are surfaced, not decided.

**Homes:** `docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md` (the two
prompts + launch instructions) · `.sessions/2026-07-03-foundational-mechanics-ultracode-brief.md`.

---

### Q-0237 — DECIDED: the 7 Tier-1 rebuild decisions from the Fable-5 final-judgment sitting (2026-07-03)

> **Context.** After the Fable-5 capstone judgment (PR #1701,
> `docs/analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md`) tiered the
> ~58-item owner queue and named **7 Tier-1 decisions** as the ones that block the Stage-2
> subsystem walk or a spec freeze, the owner answered all seven in one sitting via the question
> panel. Provenance for each is this sitting. Six matched the judgment's recommendation; the admin
> one (c) deviated and is recorded as an explicit amendment to Q-0230.

**Decisions (a–g):**

- **(a) Preset exclusion = visibility-only, never execution-off.** When a per-guild interface preset
  excludes a feature/bucket, it is **hidden from the hub/help but still runnable** — preserving the
  shipped, drift-tested **Q-0055/HLP-4** invariant that display-hide is presentation-only. A guild
  may *additionally* opt to disable via an explicit per-preset toggle, but exclusion alone never
  disables. **Resolves the Q-0232 §3 open sub-decision** (the doc's in-line "hidden = off"
  recommendation is rejected). Vocabulary: keep **visibility** (hub surfacing) and **activation**
  (can-run) as distinct axes (Codex-2's split).
- **(b) Back-path = in-session real stack + semantic-parent fallback after restart.** "Back = pop
  the real path you took" holds **within a live session** via the in-memory stack; after a
  merge=deploy redeploy, Back **falls back to each panel's declared semantic parent**. No persisted
  back-trail is required. **Amends the Q-0231 "versioned custom_id" wording** to the two-population
  reality (static hub ids stable/unversioned; dynamic session ids versioned) and pins the medium
  before the NavigationSpec/PanelSpec freeze.
- **(c) Admin = a HIDDEN node INSIDE the one unified hub (amends Q-0230).** The admin/operator area
  stays **inside the single hub** (Q-0230's one-front-door model is kept), but is **hidden from
  those without permission** rather than shown-locked. This **amends Q-0230's "gated *visible*
  node" to "hidden node"** — a viewer sees only the operator surface(s) they hold the tier for
  (moderator slice for mods, full admin for admins), and nothing where they hold nothing. Q-0230's
  "one unified hub, not two separate player/operator trees" headline is preserved.
- **(d) Authority = one `authority_ref` per command.** Stage-2 authors declare a **single authority
  label**; Gate-0 owns the internal mapping to either a governance capability or a domain audience
  tier. **Resolves the design-spec two-lane (`capability_required`/`audience_tier`) vs
  conventions-freeze one-label conflict** (judgment X-8 / L-13) in favor of one public concept;
  the owner override applies once at the C-1 resolver.
- **(e) Slash-cap = slash-common + prefix long-tail.** The common/discoverable set gets slash
  commands; the long tail stays prefix-only. **The K1 shared-verb computation budgets against
  Discord's 100 top-level / 25 sub / 1-nest caps** (feeds Q-0224). D-5 triage shrinks the corpus
  further before the final count.
- **(f) Deep-link names = decided names canonical, shipped names become hidden aliases.**
  `!admin` / `!games` (and one command per hub node) are the **canonical** deep-links; the shipped
  `!adminmenu` / `!modmenu` / `!economymenu` become **hidden aliases** so nothing breaks for current
  users; **K1 reserves both** (feeds Q-0224/Q-0231).
- **(g) Stage-2 contract = adopt Codex review 4's kit as-is.** The Stage-2 subsystem walk uses
  **Codex review 4's per-row template** (command surface / invocation / hub placement / triage
  verdict / oracle / 10-rubric-probes) + the **normalized verdict vocabulary**
  (`keep/improve/merge/redesign/drop/defer/re-place/add`) + a **Lane-0 normalization owner**. It is
  the only artifact that operationalizes D-5 and the rubric per row and already carries
  `prompt-a-issue`/`prompt-b-issue` tags so the judgment's ledger binds to rows.

**Effect.** All 7 Tier-1 blockers from the judgment §6 are cleared; combined with the RPS refund
fix (judgment V-1) and the findings-closure rule (V-3), **the Stage-2 subsystem walk is unblocked**.
Tier-2/Tier-3 queue items (~47) remain for Gate-0 with their recommended defaults.

**Homes:** `docs/analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md` §6
(Tier-1 rows marked RESOLVED) · amendment pointers in
`rebuild-hub-navigation-presets-2026-07-03.md` (a/c), `rebuild-conventions-invocation-authority-2026-07-03.md`
(d/e/f), `rebuild-stage1-global-review-2026-07-03.md` (Stage-2 §6 g) ·
`.sessions/2026-07-03-tier1-owner-decisions.md`.

---

### Q-0238 — DISCUSS: wire code-scanning (CodeQL) status into the born-red merge hold, so an open security alert blocks auto-merge (proposed 2026-07-05)

> **Context.** In the save-fixes session the born-red gate worked as designed — but the merge still
> raced a security alert. #1728 flipped its session card to `complete` (releasing the hold) the
> moment the *local* CI mirror passed; `code-quality` (the one **required** check) went green ~15s
> later and native auto-merge merged the PR **before** the server-side **CodeQL** scan had posted a
> log-injection alert on the same head. CodeQL / code-scanning are **advisory**, not a required
> check, so auto-merge never waits for them. The fix had to land as a separate follow-up PR (#1730).
> The behavioral guard is already banked (journal Rule: don't flip the card to `complete` until the
> pushed head's CodeQL has reported clean) — but that is *exhort*, not *enforce* (Q-0132/Q-0194).

**The proposal (owner decision needed — this touches executable config).** Make an open code-scanning
alert on the PR head hold the merge, one of:
- **(A)** add **`code-scanning` (or the CodeQL check-run) as a required status check** on `claude/*`
  PRs, so native auto-merge simply won't fire while an alert is open (pure branch-protection config,
  no new code); **or**
- **(B)** teach `check_session_gate.py` (the born-red gate that already gates `code-quality`) to
  also fail while the head has an **open, error/warning-severity code-scanning alert** (queried via
  the GitHub API), so the existing required check absorbs it — no separate required context to
  maintain.

**Why it needs the owner.** Both change how *every* future `claude/*` PR merges — (A) is
branch-protection config, (B) is a hook/checker behavior change — both owner-gated per the autonomy
boundary. Trade-off to weigh: (A) is the cleaner "GitHub-native" lever but CodeQL can be slow/flaky
and would occasionally stall an otherwise-green PR; (B) keeps it inside the one gate we control but
adds an API call + a severity threshold to tune. Recommendation: **(A)** if CodeQL runs reliably
fast on this repo; else **(B)** with a warn-first period.

**Homes (on decision):** `.github/` branch-protection or `scripts/check_session_gate.py` +
`.claude/CLAUDE.md` § Session workflow (the born-red-gate rule) · the journal Rule that currently
carries the behavioral half. **Until decided:** the journal Rule stands (wait for CodeQL before the
card flip). Provenance: `.sessions/2026-07-05-next-session-prep.md`.

> **Update (2026-07-05, CI-setup redesign PR #1737 — refined recommendation → option (C)).** The
> 18-agent CI-setup design found a **third option that dominates both (A) and (B)**: a **CodeQL
> code-scanning *merge-protection ruleset*** (branch ruleset, `code_scanning` rule, High-or-higher,
> advanced setup). Unlike a bare *required status check* (option A), a merge-protection ruleset
> **holds** the merge while CodeQL is in-progress and **blocks** when it is unconfigured — it does
> **not** create the "required status that never reports → pending-forever" deadlock a required
> CodeQL check would (the failure mode that makes (A) risky). It is GitHub-native (no `check_session_gate`
> API-call/threshold logic to maintain, so cleaner than (B)). **Prerequisite:** flip `codeql.yml` →
> `cancel-in-progress: false` first (today it is `${{ github.ref != 'refs/heads/main' }}`, i.e. it
> *cancels* CodeQL on PR refs — verified). **Residual hole to bound:** the ruleset does not cover a
> CodeQL run that *starts then errors/hangs*, so pair it with a stuck-scan watchdog leg in
> `ci-rerun-watchdog.yml`. **Corrected fork wording:** rulesets scope by *base* branch, not head
> origin — fork risk is *mitigated* (advanced setup + admin bypass + near-zero fork traffic), not
> *eliminated*. **Tradeoff:** merges now proceed at CodeQL's pace (minutes) not `code-quality`'s (~35s).
> This is **decision G1** in
> [`../planning/ci-setup-redesign-2026-07-05.md`](../planning/ci-setup-redesign-2026-07-05.md) §F.
> **Recommendation: APPROVE (C)** over (A)/(B). Owner-gated (branch-protection config). Provenance:
> `.sessions/2026-07-05-ci-setup-redesign.md`.

### Q-0239 — DISCUSS: ratify the CI-setup target-state migration (one required `ci-gate` context, workflow consolidation, checker promotions) — proposed 2026-07-05

> **Context.** The owner-directed "best-possible CI" session (PR #1737) produced a target-state design
> + phased, reversible migration:
> [`../planning/ci-setup-redesign-2026-07-05.md`](../planning/ci-setup-redesign-2026-07-05.md). Its
> **Phase A** is safe-additive and ships without sign-off (build the new workflows non-required
> *alongside* the old ones; add the guard scripts). Its **Phase B** changes executable config
> (required contexts, workflow deletions, `settings.json` hooks) and needs owner ratification. This
> Q-block carries the Phase-B decisions **G2–G8** (G1 is the Q-0238 update above). Each is item-by-item
> approvable; each only fires **after** the corresponding Phase-A build proves parity across a band of PRs.

**The decisions (recommended defaults in the design doc §F):**
- **G2 — Atomic required-context swap** `code-quality` → **`ci-gate`** (one `if: always()` fan-in job
  that treats a `cancelled`/`failure` leg as a hard block and a path-skipped leg as a pass), reshaping
  `code-quality.yml` → a reusable `_python-quality.yml`. **Must be one atomic change** or PRs stick at
  "Waiting for status to be reported" forever. *(Alt: name the fan-in check `code-quality` to avoid the
  branch-protection edit entirely.)* **Rec: APPROVE the swap once A8 proves parity.**
- **G3 — Delete six folded workflows** (`dashboard-ci`, `botsite-ci`, `tool-pins`, `design-system-ci`,
  `pr-auto-update`, `pr-conflict-guard`) after a full dual-run parity band. **Rec: APPROVE after parity.**
- **G4 — Promote to gating:** `check_workflow_concurrency` (new, shipped as advisory in #1737) A→G, and
  drop `continue-on-error` on `check_audit_seam` once built + proven. Also promotes `check_architecture
  --strict` + `check_tool_pins` + `check_session_slug_unique` into the gate (these are inside G2's build,
  A6). **Rec: APPROVE — low-FP invariants that can silently reach `main` today.**
- **G5 — `settings.json` Stop-hook rewires:** a `check_consistency` Stop mirror (cheap AST); optional
  changed-module fast-pytest on Stop. **Rec: APPROVE the consistency mirror; defer fast-pytest.** (Hook
  wiring is owner-gated, Q-0106.)
- **G6 — "Require branches up to date before merging."** **Rec: LEAVE OFF** — `pr-freshness` +
  `ci-gate`-on-final-head cover it; it serializes merges.
- **G7 — Delete `check_doc_freshness`** (dormant/unwired, no operational caller — Q-0105 disposability);
  **keep `check_plan_staleness`** (unique recon-band + idea-shipped signals). **Rec: APPROVE the single delete.**
- **G8 — the #794-class content-completeness merge race** (close-out docs pushed after the first green
  head already merged): accept it stays *advisory* (badge=G, docs=A), or add a narrow "close-out docs
  present when the badge flips" G check. **Rec: ACCEPT ADVISORY + document it** — a session legitimately
  editing the ledger is common; a presence gate risks false-blocks. Revisit if #794 recurs.

> **RESOLVED 2026-07-06 (owner-delegated, PR #1748 — "finish everything you can; choose decisions
> yourself"):** **G7 EXECUTED** — `check_doc_freshness` deleted (dormant/unwired; `check_plan_staleness`
> kept). **G8 = ACCEPT ADVISORY** (the recommendation; a no-op on enforcement — the content-completeness
> race stays advisory, no presence gate, revisit if #794 recurs). Both are the safe/recommended options
> and neither rewires branch protection or executable config. **Still owner-gated, NOT taken this
> session:** G2 (required-context swap), G3 (6 workflow deletions), G5 (`settings.json` Stop-hook
> rewires) — these change branch protection / executable config and stay for explicit owner sign-off.

**Why it needs the owner.** Every G2–G8 item changes how future PRs merge or deletes/rewires executable
config (workflows / branch protection / `settings.json`) — owner-gated per the autonomy boundary
(Q-0106). **Until decided:** Phase A ships (safe-additive); the current `code-quality` gate stays the
required context; nothing is deleted. **Homes (on decision):** `.github/workflows/` + branch-protection +
`.claude/settings.json` + `.claude/CLAUDE.md` § CI/Session workflow. Provenance:
`.sessions/2026-07-05-ci-setup-redesign.md`.

---

## Q-0240 — Agent decision authority: decide-and-flag over route-up (owner-directed, 2026-07-06)

> **→ Program law: [PL-001]** — this block's durable conclusion is canonicalized as program law **PL-001** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

**Owner directive (in-session):** *"let fable decide … I'm usually going with the recommended decisions
and things are usually too technical for me anyways … redesign the repo so fable will make its own
decisions."* → **Applied directly** (the in-session owner is the live reviewer — the Q-0106 exception —
so the rule change ships now with this provenance Q, not as a proposal).

**Decision.** Agents **decide reversible-until-a-gate calls themselves** (recommendation + one-line
rationale + a flag on the run report) and do **not** route them to the owner. This includes
"too-technical / architectural" *design* calls, because planning/design decisions are reversible by the
owner's single go/no-go veto at the gate. The safety brake is unchanged but **reframed**: irreversible /
production / external work is **decided-and-flagged for veto**, not blocked — the only stop-and-wait is
*executing* something irreversible **before** the gate (creating the new repo, prod write, moving user
data). The owner's control point is **one review pass at the gate**, not per-decision gatekeeping.

**Home:** [`docs/owner/agent-decision-authority.md`](agent-decision-authority.md) (full model + the
decide/flag/veto table); binding pointer in `.claude/CLAUDE.md` § Working agreement (Act vs. ask).
Provenance: `.sessions/2026-07-06-fable-decision-authority-and-foundational-consolidation.md`.

---

## Q-0241 — Remove the owner gates from the rebuild; never-wait autonomy + live-test visibility + silence=consent (owner-directed, 2026-07-07)

> **→ Program law: [PL-002]** — this block's durable conclusion is canonicalized as program law **PL-002** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

**Owner directive (in-session):** *"we should get rid of the owner gates/blockers, especially since we
now also have the option to let all commands be used by an agent in a live bot session, it should just
build everything in logical order and live test it so I can see the results in a server, but it should
never wait for me, if I don't say something about it it should be considered done."* → **Applied
directly** (the in-session owner is the live reviewer — the Q-0106 exception — so the rule change ships
now with this provenance Q, not as a proposal). Extends **Q-0240** (decide-and-flag) into
**decide-and-proceed**.

**Decision.** For the **rebuild program** (the coordinator building `superbot-next` + porting the bot),
the owner's control model changes from *approval-before-execution* to *reaction-after-visibility*:

1. **No owner gates.** The rebuild's **G1 go/no-go sitting**, **G2 "owner accepts the verdict"** on
   Phase-2.5, and every **👤 owner-gated step** (incl. step 6 "create the repo") are **retired as
   blockers.** The coordinator builds everything **in logical order** and does not pause for owner
   sign-off between phases.
2. **Live-test replaces owner verification.** Each piece is **exercised live in a real server** (an
   agent can now drive all commands — slash, prefix, components — in a live bot session), so the owner
   *sees results in a server* instead of reading a verdict and blessing it. Live-test-green is the
   coordinator's own gate; it never routes the "does it work?" question up.
3. **Silence = consent = done.** The coordinator never waits for the owner. **If the owner says nothing
   about a piece, it is considered accepted and done.** The owner's control point is *reacting to what he
   sees* (a message stops or redirects it); absence of a message is approval.

**The one flagged rider (decide-and-flag, vetoable — not a gate).** The owner's model ("if I don't say
something it's done" ⇒ *if I do say something, act on it*) only has teeth while the thing he reacts to is
**still reversible when he reacts.** So for the **destructive tier only** — production data import over
real balances/audit, the CUT-3 token swap, deleting old-bot data — the coordinator **still never waits**,
but executes via the **reversible-equivalent path the plan already specifies**: shadow-first / restored-
snapshot DB, the **N=7d rollback window** (Q-D15), and the declared-loss **reverse-import valve**
(F-1/F-2). This adds **zero pause** — it is not a gate — it just keeps a reaction window open so
"say-something-to-undo" is possible. **Veto available:** if the owner wants zero retained reversibility
(straight destructive execution), he says so and the rider drops.

**Scope (flagged decision).** Q-0241 governs **the rebuild program**. For the **live production bot**
today, the Q-0213 ask-first `*Delete`/`*Restore` brake and prod-data safety **still stand** until the
owner generalizes this — because the rebuild targets a fresh/shadow environment he watches, whereas prod
carries live user data. The owner can extend Q-0241 to all work at any time.

**What stays true.** Merge=deploy still requires **CI green** (never-wait ≠ bypass CI); the born-red
session card / auto-merge machinery is unchanged; decisions are still **recorded + flagged** on the run
report (Q-0240) so the owner's after-the-fact review has a trail to skim.

**Home:** [`docs/owner/agent-decision-authority.md`](agent-decision-authority.md) § "Q-0241 — the
rebuild override"; amendment stamp on
[`../planning/rebuild-canonical-plan-2026-07-06.md`](../planning/rebuild-canonical-plan-2026-07-06.md)
§1/§4/§5 (G1/G2/👤 retired); binding pointer in `.claude/CLAUDE.md` § Working agreement (Act vs. ask).
Provenance: `.sessions/2026-07-07-projects-eap-and-full-autonomy-q0241.md`.

---

### Q-0242 — DIRECTED: Q-0229's "bare `mcp__<server>` = allow every tool" claim is empirically false; exact tool-name entries added for Claude Code Remote (2026-07-07)

> **Context.** Owner reported the *same* recurring permission-prompt problem Q-0229 (2026-07-03) was
> supposed to have fixed: `send_later` and `delete_trigger` (Claude Code Remote's scheduling tools)
> still prompt on the mobile/web client, with screenshots from earlier in this very session as live
> evidence. Owner: *"this is also a recurring problem, which I've tried to fix more times than I can
> count... even with these actions on the allowlist it keeps happening."*

**Findings.** Q-0229 added bare `mcp__<server>` entries (`mcp__Claude_Code_Remote`, `mcp__github`,
`mcp__codegraph`, `mcp__context7`) to `.claude/settings.json`, reasoning "bare `mcp__<server>` matches
every tool on that server." **That claim was never live-verified and this session's evidence refutes
it for at least one server:** `delete_trigger` had no exact-name entry (only the bare wildcard) and
prompted — expected, if the wildcard doesn't actually prefix-match. But `send_later` had **both** the
bare wildcard **and** an exact `mcp__Claude_Code_Remote__send_later` entry (in the tracked
`.claude/settings.local.json`) and **still prompted** — which the bare-wildcard theory alone can't
explain, and which per the repo's own Q-0120 rule ("a green check/claim that contradicts visible
evidence is a bug in the check, not the evidence") means the Q-0229 fix should be treated as
unverified, not working, until proven otherwise.

**Decision (owner-directed in-session; Q-0106 executable-config exception).** Added explicit,
individually-named allow entries for all ten Claude Code Remote tools (`add_repo`, `create_trigger`,
`delete_trigger`, `fire_trigger`, `list_environments`, `list_repos`, `list_triggers`,
`register_repo_root`, `send_later`, `update_trigger`) to `.claude/settings.json` (the shared,
committed project file — not `settings.local.json`, removing any ambiguity about whether a
"local"-scoped file is fully honored on the remote/web client for an ephemeral, freshly-cloned
container). The bare `mcp__Claude_Code_Remote`/`mcp__github`/`mcp__codegraph`/`mcp__context7`
entries were **left in place, not removed** (additive-only change; they may still help for tools not
individually enumerated, and removing them risked losing whatever partial coverage they do provide).

**Honest caveat — this may not fully resolve it.** Given send_later kept prompting even while exactly
allowlisted, there's a real chance Claude Code Remote's *action-scheduling* tools specifically
(`create_trigger`/`update_trigger`/`delete_trigger`/`fire_trigger`/`send_later` — anything that
creates or removes standing autonomous behavior firing later without the owner present) are
deliberately exempted from allowlist auto-approval on the interactive surface, as a safety design that
no `settings.json` entry can override. **The next session to hit this should verify empirically
before re-attempting the same fix a third time**: if these tools still prompt after this change, stop
adding allowlist entries for this specific tool class and instead treat it as confirmed-deliberate
platform behavior (report/ask upstream if a true override is wanted), per Q-0229's own pointer to the
**environment-level permission mode** (code.claude.com / the in-session mode toggle) as the only lever
above the repo's `allow` list — a project file structurally cannot force full bypass on this surface.

**Homes:** `.claude/settings.json` (ten new entries) · this Q (provenance, supersedes Q-0229's
unverified claim) · `.sessions/2026-07-07-rebuild-plan-review-and-automation-idea.md` (continuation).

### Q-0243 — DECIDED: category-B automation pricing is decided by a dedicated SIMULATION, not a judgment call (2026-07-07)

**Context.** Canonical plan §11b A-13 ships the user-self-service automation scheduler with
category B (auto-acting, e.g. auto-collect) structurally reserved but compile-fenced OFF pending a
dedicated pricing session (the owner's explicit earlier instruction — see
`docs/ideas/user-self-service-automation-scheduler-2026-07-07.md`). Asked what should happen next,
the owner ruled on that session's *method*.

**Owner ruling (in-session, 2026-07-07):** "The pricing session should probably be decided by a
dedicated simulation."

**Decision unpacked.** The pricing session's deliverable is a **simulation** in the repo's
established sim-decides-design pattern (layer V-3; precedent: the gear-set numbers, claim-layout,
menu-layout sims): model **automated-vs-manual player expected value over time** for each candidate
pricing shape (flat unlock vs per-use, coins+XP mix, allowance curve), and set the price from the
sim's output — drift-pinnable afterward, never a guessed number. This ratifies the idea doc's own
"needs the same measured/simulated approach the rebuild already uses for layout decisions" as the
*binding mechanism*, not just an aspiration. The unlock still rides Q-0039's earned track;
automation capability is never real-money purchasable (A-13/IC-4).

**Homes:** this Q (provenance) · canonical plan §11b A-13 rider ·
`docs/ideas/user-self-service-automation-scheduler-2026-07-07.md` (pricing section).

### Q-0244 — DECIDED: slash-command verification inherits prefix coverage; owner flags dysfunction reactively; the human lane never blocks (2026-07-07)

**Context.** §11b A-18 budgeted the human `verified_live` lane (~150–250 click-through units,
since agents cannot drive slash/component interactions live — the frozen A-10 constraint) and
flagged two owner-intent questions: may a delegated human sign rows, and should unsigned
human-tier rows hard-block CUT-3 or ride as a published debt list (IC-12)? IC-13 separately
flagged the Q-0241/A-10 capability-claim contradiction.

**Owner ruling (in-session, 2026-07-07):** "if we test the prefix commands then the slash
commands should be considered working as well, I will flag whenever I find any slash commands
dysfunctional, but it shouldn't be a blocker."

**Decision unpacked.** (1) A slash/component surface counts as **verified** when its prefix twin
passes live agent-driven testing AND the slash path passes the in-process pipeline-true replay
(the parity technique — real payload parsing, converters, authority, error handler; only HTTP
faked). No separate human live click-through is required for sign-off. (2) The owner's mechanism
is **reactive flagging**: he reports dysfunctional slash commands as he encounters them in the
server — routed bugs-first, like any live miss. (3) **Nothing in the human lane blocks CUT-3** —
IC-12 resolves to the published coverage-debt-list model, and the human tier shrinks to the
optional Q-0234 "self-explanatory" judgment walks at the owner's leisure (Q-0222's "per-command
owner sign-off one by one" is superseded-in-part by this lighter model). (4) The A-10 capability
fact stands unchanged (agents still *cannot* drive slash/components live); what changed is the
verification *requirement* — which makes the IC-13 wording conflict operationally moot.

**Homes:** this Q (provenance) · canonical plan §11b A-18 rider ·
`rebuild-idea-consolidation-report-2026-07-07.md` §7 addendum.

### Q-0245 — DECIDED: the owner's second account is a declared elevated test actor (env-declared extra owner, never source-hardcoded) (2026-07-07)

**Context.** Companion C's lane B named a "manually operated low-privilege second account" as a
known gap ("no low-privilege second human account exists"). Asked what that meant, the owner
confirmed he **has** one, will use it to drive live tests, and proposed: "it might be a good idea
to hardcode that user ID into the bot so it has free reign to do whatever it needs to to test
moderator functions etc."

**Decision (owner-directed; implemented same day, better-implementation clause).** The intent
(full bot authority for the test account) ships via **configuration, not source-hardcoding**: a
new comma-separated **`EXTRA_OWNER_USER_IDS`** env var. Every id in it clears **both** owner
seams — `config.is_platform_owner()` (the documented single source of truth every governance /
mutation / setup / view admin gate routes through) and `bot.is_owner()` (the command-access
operator bypass, via a small `_SuperBot.is_owner` override that delegates to the same predicate) —
so the account holds full platform-owner authority **in every guild**, exactly like the main
account. Empty default = zero behavior change. The owner sets the variable on Railway (and locally
for the test bot) with his second account's id; rotating/removing it is a config change, no
deploy-time code edit. **Safety note (flagged):** an id in this set is a full-power operator
credential everywhere the bot runs — treat that account's security like the main account's; ids
are deploy-declared, auditable in the deploy config, and never spoofable by message text (identity
is the authoritative Discord user id).

**New-bot landing:** the rebuild inherits this as a K0/K6 concern — a config-declared
`extra_owner_ids`-equivalent recognized by `resolve_authority`'s owner predicate; companion C's
lane-B driver account is its first consumer (test-guild walks of moderator functions without real
Discord roles).

**Homes:** this Q (provenance) · `disbot/config.py` (`EXTRA_OWNER_USER_IDS` + widened
`is_platform_owner`) · `disbot/bot1.py` (`_SuperBot.is_owner`) ·
`tests/unit/test_platform_owner_override.py` (8 new pins) · companion C §4 lane-B note ·
canonical plan §11b A-21.

### Q-0246 — DECIDED: permission-tiered operation — server owners choose Full (administrator) vs Lite (no elevated permissions), features degrade visibly (2026-07-07)

**Context.** The Q-D5 discussion (boot posture on missing intents/permissions) prompted the owner
to state the product rule, not just the failure rule: "currently the bot is a full administrator,
so it either gets permissions or it doesn't … I'd like for it to be possible for server owners to
choose whether they want the full bot with all capabilities, thus needing administrator, or only
games and non admin functions the bot can do without permission, so there always is a failsave in
case people don't want to give permissions to a bot."

**Decision unpacked.** The rebuild ships **two owner-choosable capability tiers**: **Full**
(administrator — everything) and **Lite** (games/community/utility features that need no elevated
Discord permissions — moderation, channel/role management, cleanup etc. stay dark). Mechanism:
every feature's manifest declares the Discord permissions it needs; the compiler derives (a) the
two invite URLs/permission bitmasks presented at setup, and (b) the runtime census — a feature
whose permission is absent degrades **visibly** (help/setup say "needs Manage Roles", never a
silent failure or a crash). This **extends Q-D5's DEGRADE ruling from a failure posture to a
supported product configuration**: running without admin is a first-class mode, not a tolerated
error state. Lite→Full upgrade is just re-inviting/granting and flipping the census — no data or
config loss. (Gateway *intents* keep their separate Q-D5/PG-2 treatment; this Q is about
permissions.)

**Homes:** this Q (provenance) · canonical plan §11b A-22 + §1 F-2 Q-D5 row rider · rider **R-18**
in `rebuild-amendments.yml` (per-feature permission declaration; exact carrier decided at the
owning fold).

### Q-0247 — DECIDED: multi-repo sequencing ratified; kickoff brief directed (2026-07-07)

> **→ Program law: [PL-003]** — this block's durable conclusion is canonicalized as program law **PL-003** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

**Owner ruling (in-session):** "yes I agree, please make sure everything is properly documented
and ready for its own dedicated session." Ratifies the recommended sequencing in
`docs/ideas/multi-repo-program-kit-lab-trading-2026-07-07.md`: **(1)** `superbot-next` now (plan
§5 steps 6–8); **(2)** the substrate-kit extracts to its own repo at the step-7 second-consumer
moment (both repos created in the same kickoff session); **(3)** the trading-research repo third,
on a matured kit; **rail before scale** — each repo's autonomy loop proves its guardrails before
the next launches. Repo-start mechanics stand as captured: fresh-from-kit, old repo attached
read-only as the oracle, never clone-as-base.

**Homes:** this Q · the kickoff brief
(`docs/planning/rebuild-kickoff-steps-6-8-brief-2026-07-07.md`, the directed artifact) · the
capture doc's routing section · current-state ▶ pointers.

### Q-0248 — DECIDED: model-for-task allocation becomes an empirical, rule-based discipline (2026-07-07)

> **→ Program law: [PL-004]** — this block's durable conclusion is canonicalized as program law **PL-004** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

**Owner ruling (in-session):** "we should also find out ways to properly use the right model for
the right task, like everything we do, we should have a way to test this reliably and a proper
rule to define when it is necessary and what decides the result."

**Decision unpacked (the design, decide-and-flag).** Model allocation graduates from the plan's
static §3 table to a measured discipline, in three layers:

1. **Instrument now (passive, cheap):** every session/run logs `model · effort · task-class ·
   outcome` — where outcome is objective first (CI green on first push? checker findings? rework
   or revert within N sessions? tokens per merged PR) — as session-telemetry the kit carries
   (the orientation-budget pattern widened). This runs through the same ~2-month observation
   window as Q-0249, so the budget data and the allocation data are the SAME dataset.
2. **Task-class taxonomy + default ladder:** task classes (docs-only · mechanical refactor ·
   test writing · runtime bugfix · kernel/architecture design · review/verify · research ·
   idea/planning) each get a default tier (Haiku → Sonnet → Opus/Fable ladder) seeded from the
   plan's §3 table; stakes (reversibility, blast radius, frozen-grammar contact) modify upward.
3. **The rule ("when is escalation necessary, what decides the result"):** escalation triggers
   are mechanical — e.g. two red CI rounds on the same task, a review finding ≥N confirmed
   defects, or the task touching frozen grammar/kernel ⇒ auto-escalate one tier; de-escalation
   when a cheaper tier matches the incumbent's outcome quality for M consecutive tasks of that
   class. **What decides:** objective gates first (CI/parity/checkers), judge-scored quality
   second (the Phase-2.5 A/B judge pattern for paired same-task runs), cost as tiebreaker.
   The kit-lab runs the paired A/Bs per class once extraction lands — this is a named lab
   fitness function, not superbot-specific.

**Scope widening (owner clarification, same session):** this discipline covers **both planes**,
not just Claude Code sessions — **(a) the agent plane** (which model/effort runs a work session or
routine — the three layers above), and **(b) the product plane**: which provider/model each
*runtime* API call uses per use case — the bot's NL/knowledge answers, image review/moderation,
future image generation, and any AI integrated into the websites (botsite, the lab's sites, the
trading tracker). The product plane already has the enforcement point designed: the K10 gateway's
task registry + profile resolver (per-task routing as config — the live bot's
`AI_ROUTING_<TASK>` env pattern and the Q-0095 Haiku allocation are its precedent), and its
"what decides the result" is the A-17 eval machinery per use case: deterministic gates + judge-
scored quality **+ per-call cost and latency**, so a routing change is a measured config flip,
never a vibe. Same rule shape on both planes: defaults per task class, mechanical
escalation/de-escalation triggers, objective gates decide, cost/latency as tiebreakers.

**Homes:** this Q · the capture doc part 2 (lab fitness functions) · the kickoff brief (telemetry
from session one) · future kit-repo benchmark suite · K10's task-registry/profile-resolver row
(the product-plane enforcement point).

### Q-0249 — DECIDED: no budget caps yet — a ~2-month observation window with spend telemetry first (2026-07-07)

> **→ Program law: [PL-005]** — this block's durable conclusion is canonicalized as program law **PL-005** in substrate-kit `docs/program/rulings.md` (the canonical home — cite the PL-ID, never copy the body). Canonicalized 2026-07-09, kit-lab band KL-2 (founding plan §8.3(3)); this Q-block stays in place as the origin provenance.

**Owner ruling (in-session):** "budget so far is not really a problem, I'd like to test it for a
while to see the average of a couple of months before deciding on anything."

**Decision unpacked.** The capture doc's recommended budget caps (lab Railway cap, token budgets)
are **deferred, not adopted**: instrument spend per repo/session/routine now (the Q-0248
telemetry carries cost), let ~2 months of real usage accrue, then decide caps from the measured
average — data over guesses, the same instinct as Q-0243. **Unchanged by this ruling:** the
security rails are not budget rails — scoped credentials (a repo/lab never holds another repo's
prod secrets or the live bot token) and the trading repo's real-money brake (per-trade/day/total
caps + kill switch) stand regardless, because they guard irreversibility, not spend.

**Homes:** this Q · the capture doc (open-forks + part-2 rails updated) · the kickoff brief §2
step 8 (no Railway caps; telemetry instead).

### Q-0250 — DECIDED: the trading repo starts stocks-first (US large-cap tech); DEGIRO stays the owner's manual venue; the crypto proving-ground suggestion is withdrawn (2026-07-07)

**Context.** The multi-repo capture left "which market/asset class first" as an open fork; the
outside-the-box sweep suggested crypto as a cheap rigor proving ground (free complete data, 24/7,
trivial paper trading). The owner answered: he trades **stocks only**, on **DEGIRO**, mostly US
large-cap tech (Intel, Nvidia); he has no way — and no desire — to trade crypto, though he'd
accept it if genuinely best "since most of it will not be done by me."

**Decision (owner preference wins; the technical case supports it).** **Stocks-first, US
large-cap tech as the initial scope.** Rationale: for liquid mega-caps the usual data killers are
weak (survivorship bias is a broad-universe problem; large-cap daily/intraday data with
documented splits/dividends is cheap and good; spreads are tight so cost modeling stays honest) —
and the falsification ladder proves out fine there, so crypto's data-cheapness advantage isn't
worth building where the owner's interest and ground truth aren't. Three binding riders:

1. **Point-in-time universe rule — the selection-bias guard.** The backtest universe is defined
   by a dated rule (e.g. "top-N US tech by market cap as of each rebalance date"), **never** "the
   stocks the owner holds/likes today" — NVDA is one of history's best performers, and a universe
   chosen on hindsight makes any long-biased strategy look brilliant. The owner's picks are
   welcome as *watchlist/priority inputs*, not as the universe definition.
2. **The automated lane rides an API broker, not DEGIRO.** DEGIRO has **no official public API**
   (unofficial reverse-engineered clients violate its terms and break routinely — not a
   foundation). Paper trading runs on an API-native broker (IBKR-class, EU-available, real paper
   environments; Alpaca-class for US-stock paper). The eventual capped-live gate (if ever) uses
   the same API broker, under the standing real-money brake.
3. **DEGIRO integrates read-only at the tracker.** DEGIRO supports transaction/portfolio export;
   the tracking website ingests those exports so the owner's *real* portfolio appears next to the
   strategies' paper portfolios — his manual trading becomes a benchmark lane, not an execution
   dependency.

**Homes:** this Q · the capture doc's open-forks + Part 3 (fork closed) · the future trading-repo
founding brief (this Q is its market-scope input).

### Q-0251 — DECIDED: the trading repo's operating model — decision-ledger mock trades, a sniper bucket, and the 3-way hybrid allocator (2026-07-07)

**Owner ruling (in-session, elaborating Q-0250):** trades are **mock trades** that "wouldn't even
need to be actually executed — if we just document our decision and check the results after the
decided time, we know whether or not our trade would have worked"; backtest across multiple
stocks "and even crypto too eventually if it's helpful"; score strategies by "highest % of gain
over a set amount of time or a set amount of trades"; rare-but-precise strategies matter (his
example: a strategy that over many years found only 5 trades but no losers — "not very useful
data, but it does prove that the idea is there") and must not be the only strategy; eventually
run a **3-way hybrid** dividing money across an **active trading** section, a **swing-trade**
section, and a **reserve/save** section "that either remains available for lucky moments or
specifically for entry at a decided level."

**Decision unpacked (strengthened, decide-and-flag):**

1. **The decision ledger IS the v1 product — no broker needed at all.** Every signal is recorded
   *before* its outcome window (instrument, direction, size, thesis, entry, exit rules, horizon)
   and verified against market data after it closes. **Git commits are the tamper-evidence**: a
   decision committed at time T provably predates its outcome — nobody, human or AI, can
   pretend-predict after the fact. Forward testing this way complements backtesting and is the
   strongest antidote to overfit (a strategy can't overfit the future). The Q-0250 API-broker
   paper lane becomes a *later* upgrade (realistic fills/slippage), not a prerequisite.
2. **Scoring:** the leaderboard shows gain % per set time AND per set trade count as the owner
   asked — plus the honesty columns (max drawdown, sample size, exposure time) so a lucky
   3-trade streak never outranks a robust 300-trade record; the promotion ladder (Q-0250 rider
   context) stays the gate.
3. **The sniper bucket (rare-but-precise strategies) is a first-class citizen** with different
   statistics: tiny samples get uncertainty-aware evaluation (a 5-for-5 record proves the
   pattern class exists, not yet the edge — across many candidate strategies, some 5/5 appears
   by pure luck), mandatory forward-test emphasis (tiny-N backtests overfit worst), and
   **notification wiring**: when a sniper setup triggers live, the owner gets pinged (the
   notification/automation primitives from the bot program are the natural transport). Sniper
   signals are also a named *reserve-deployment trigger* (below).
4. **The 3-way hybrid is an ALLOCATOR — itself a strategy, itself backtested.** Buckets: active
   (short-horizon strategies) · swing (longer-horizon) · reserve (cash). The allocator's rules —
   bucket weights, rebalancing, profit routing, reserve refill — are declared and evaluated like
   any strategy, so the *hybrid* has a track record, not just its components. **Reserve
   discipline:** deployment rules are pre-declared (crash/drawdown triggers, pre-decided entry
   levels = standing limit-style entries in the ledger, sniper signals) — "lucky moments" are
   defined in advance, never discretionary hindsight.
5. **Crypto re-scope:** eventually admissible as *backtest robustness data* (does a strategy
   class survive on an unrelated asset class?), never a trading venue — consistent with Q-0250.

**Homes:** this Q · the capture doc Part 3 (operating-model subsection) · the future trading-repo
founding brief (Q-0250 + Q-0251 are its two design inputs).

### Q-0252 — DIRECTED: three dedicated Fable sessions, one per build, each ending in a comprehensive executable plan (2026-07-07)

**Owner directive (in-session):** "prepare the repo for the 3 builds — the goal should be to use
3 dedicated fable sessions to thoroughly research and plan for all these ideas and turn them into
comprehensive ideas/executable plans."

**Executed same day.** The launch package is
[`docs/planning/program-three-sessions-launch-index-2026-07-07.md`](../planning/program-three-sessions-launch-index-2026-07-07.md)
(one page: order, prerequisites, consumes/produces) pointing at three paste-ready briefs:
session 1 = the `superbot-next` kickoff (`rebuild-kickoff-steps-6-8-brief-2026-07-07.md`);
session 2 = the kit-lab founding brief (`kit-lab-repo-founding-brief-2026-07-07.md`);
session 3 = the trading-repo founding brief (`trading-repo-founding-brief-2026-07-07.md`).

**One flagged call (⚑, decide-and-flag):** session 1 is an *execution* session, not a
research-and-plan session — the bot rebuild's comprehensive executable plan already exists (the
canonical plan + §11/§11b, twice-reviewed 2026-07-07); re-planning it would re-litigate settled
work. The genuine research-and-plan sessions are 2 (kit lab) and 3 (trading), whose builds had
only capture-level docs. If the owner *did* want a third planning pass over the bot rebuild, say
so and it becomes a review brief instead — but the recommendation is to spend that session
actually starting the repo.

**Homes:** this Q · the launch index + two new briefs · current-state ▶ pointer.

### Q-0253 — DECIDED: session 1 re-cut to the websites (last Fable day); the kickoff demotes to Opus-class — the first recorded Q-0248 allocation decision (2026-07-07)

**Owner correction (in-session):** "session 1 should probably be different … today is the last
day fable is included in the subscription for a while, it's probably best to properly use it for
a good design and well functioning website etc … use the design of the existing websites as
guidance, specifically the looks of the botsite, but it should come up with its own improved
version … clear and easy to use and feature rich, possibly also decided by simulations."

**Decision unpacked (agreed, with one refinement).** The Fable-availability constraint changes
the allocation: Fable's scarce last-day capacity goes to work where its edge is most visible —
**design quality** (the websites) and, if today's capacity allows more sessions, the two deep
**research-and-plan** sessions (kit-lab, trading). The **kickoff (§5 steps 6–8) needs Fable
least**: it executes an already-complete, twice-reviewed plan — mechanical repo creation, kit
adoption, CI arming — comfortably Opus-class work. So the launch package re-cuts to FOUR
sessions: ① websites (Fable, today — brief:
`docs/planning/website-design-fable-brief-2026-07-07.md`); ②/③ kit-lab + trading founding plans
(Fable today if capacity allows, else Opus `xhigh` — both briefs stand unchanged); ④ the kickoff
(Opus-class, any day — brief unchanged). This is the **first recorded model-reallocation decision
under Q-0248** (task-class: mechanical-execution-of-complete-plan ⇒ tier below frontier; the
Fable-availability window recorded as an allocation constraint). Website scope, priorities, and
the sim-informed UX checks live in the brief; botsite v1's three design-owned files stay
untouched (v2 supersedes, v1 stays the fallback).

**Homes:** this Q · the website brief · the launch index (re-cut) · current-state ▶ pointer.

### Q-0254 — DIRECTED: sessions restate the understood goal back before substantive work — "understand-and-reflect" (2026-07-07)

**Owner directive (in-session, live chat, not a router-routed question — recorded here per the
provenance convention):** after watching a session's sequence of steps on the kit-lab founding
plan, the owner asked whether a general guide already exists for how a session determines the
kind of task it's facing and picks an efficient method for it. He then directed: **lock in a
recurring check** — does the agent understand what the user means, and can it improve the
user's vision and explain it back in a clear, understandable way that includes the broader specs
the user did not state in the original ask.

**What was found (the honest answer to the first half).** No single live ruleset does this
today. Three partial, non-overlapping systems exist: `docs/AGENT_ORIENTATION.md`'s "Reading
order by task" routes a session to *which docs to read* for a known task shape;
`docs/owner/ai-project-workflow.md`'s 5-stage pipeline routes *which AI tool/role* handles a
stage of a larger multi-agent project; and the (not yet adopted into this repo's live workflow)
substrate-kit ships a genuine 5-stance task classifier (question / analysis / debug / review /
plan — each with its own reading-route, tool-scope, and output contract). None of the three
does message-level classification of an incoming ask, and nothing anywhere does a restate-back
step. The question-router pattern (§10, multiple-choice format) is adjacent but exists only for
*genuine product ambiguity* — it does not cover the ordinary case of a clear-enough ask that
still deserves a one-line confirmation before non-trivial work starts.

**Decision unpacked (applied directly — owner-directed-in-session exception, `.claude/CLAUDE.md`
§ Working agreement).** Add a binding rule, not a proposal: before starting substantive
(non-trivial, non-mechanical) work, a session states back — briefly, inline, not as a blocking
question — what it understood the goal to be, **including the broader specs the ask implied but
did not say**, so a misreading surfaces before work happens instead of after. This is explicitly
**not** a return to stop-and-ask-before-acting (Auto Mode / decide-and-flag still govern
execution) — it is a restate woven into the first substantive response, the same posture as
"decide and flag," applied to *understanding* rather than to *technical calls*. For a trivial or
fully-unambiguous ask, a one-line "doing X because Y" suffices instead of a full restate. For a
genuinely ambiguous ask, this escalates to the existing router/question mechanism — it does not
replace it.

**Scope note:** this Q-block is the provenance anchor; the rule text lives in `.claude/CLAUDE.md`
§ Working agreement (binding, auto-loaded every session) with a pointer from
`docs/AGENT_ORIENTATION.md`'s "Read first" mandate. Adopting the kit's dormant stance-classifier
into this repo's live workflow (the deeper version of "how does a session pick its method") is a
separate, larger question — routed to the kit-lab program (`docs/planning/kit-lab-founding-plan-
2026-07-07.md`) rather than decided here; this Q only closes the restate-and-enrich gap.

**Homes:** this Q · `.claude/CLAUDE.md` § Working agreement (the rule text) ·
`docs/AGENT_ORIENTATION.md` § "Read first" mandate (the pointer).

**Addendum — the actual mechanism, in the owner's own words (same day, same conversation):**
"I often have big ideas, and when I explain them it's often in pieces, and I don't have all the
ideas ready at once, so I'm often relying on the agents to come up with the full pictured based
on rough draft ideas, and the agent repeating my intent back to me in a more complete form will
help me find out if the agent understood my intent correctly as well as gives me more ideas to
work with and reason about." This sharpens the rule beyond error-catching: the maintainer builds
ideas **iteratively and in fragments by design**, and relies on the agent to reason forward from
a rough draft to its fuller shape. So the restatement is not just "did I understand" — it is
**"here is the fuller picture I built from your fragment; does it match, and does it also give
you something new to react to?"** Two distinct payoffs from one step: verification (catch a
misread early) and **idea-expansion** (the filled-in picture is itself new material the
maintainer reasons against, the same way he uses ChatGPT/Opus in the Ideas-project pipeline
stage — `docs/owner/ai-project-workflow.md` §2). The CLAUDE.md rule text is written to this
fuller understanding, not the narrower "confirm before acting" framing alone.

**Second addendum — the feasibility-first shape of his idea process (same conversation):** "this
is mainly because sometimes I think of something, and I don't even know for sure if we could do
it, so I lay out the general idea, find out the possibilities, and try to expand from that, to
eventually reach the most advanced functions in the simplest and most efficient ways." The
starting premise is often genuinely uncertain feasibility, not just an incomplete spec — so the
restatement's first job, when that's the shape of the ask, is **surfacing the possibility
space** (what's actually achievable here, and by what approaches) before or alongside proposing
a direction. The stated end-state to build *toward*, once the space is known: **the most
advanced capability reachable by the simplest, most efficient implementation** — not the
fanciest architecture that technically supports it. This is the same "assume he'd want the
better one" instinct already binding in CLAUDE.md (Q-0014, Act-vs-ask), now named as the
*explicit target* the restatement should reason toward whenever the ask starts from "can we
even do this?" rather than a clear spec.

**Third addendum — guiding questions, unattended-session routing, big-idea escalation, and
graduation to kit doctrine (same conversation, following turns).** Four further owner rulings,
each confirmed live:

1. **This rule should live in the substrate-kit** ("yes this is a rule that should live on in
   the substrate kit") — not stay pinned to superbot's local `CLAUDE.md`. **Shipped same day**:
   ported into `substrate-kit/src/engine/templates/CONSTITUTION.md.tmpl` +
   `collaboration-model.md.tmpl` + `question-router.md.tmpl`, dist regenerated, 440/440 kit
   tests green (PR that lands this addendum). Superbot's own CLAUDE.md entry is now the *local
   copy* pending superbot's own upgrade from a real kit release (§4 of the kit-lab founding
   plan) — not removed, since extraction hasn't happened yet.
2. **Unattended sessions map their questions to the repo too**: "unattended sessions or sessions
   in general that have certain questions during their work should just map them to the repo
   wherever applicable." When there is no live owner to ask, the question goes into the router
   (or the kit's portable equivalent) instead of being skipped or silently guessed at.
3. **Confirmed the guiding-questions filter, verbatim**: "it won't ask about small things unless
   it's something that actually matters and is something I can work with, correct? if so this is
   perfect" — confirmed correct. The bar is conjunctive: **matters** (not trivia, not already
   implied) **and actionable** (something concrete he can work with), not either alone.
4. **Big ideas get real research, not memory-only reasoning**: "certain [big] ideas should get
   their own session wherever necessary or should just get a delegated agent researching it
   immediately so it can be reviewed in the same session." Two escalation paths from a single
   restatement, chosen by size: a delegated subagent research pass reviewed inline (same
   session), or — for large enough asks — a dedicated session of its own (the program-session
   pattern already used for the kit-lab/trading/websites founding work).
5. **Threshold calibration deferred, explicitly**: "let it be for now, I can review how well it
   works with a few weeks of testing." The guessed "non-trivial, non-mechanical" trigger in
   CLAUDE.md stays as-is; no further tuning until empirical feedback arrives.

### Q-0255 — DISCUSS: clean the two owner-gated pointers left stale by the in-tree substrate-kit removal (proposed 2026-07-09)

> **Context.** PR #1882 executed the follow-up chore named in the kit-lab founding plan §4.2
> (substrate-kit `docs/planning/kit-lab-founding-plan-2026-07-07.md`): the kit graduated to its
> own repo (menno420/substrate-kit, v1.0.0 released; superbot's pin = `substrate.config.json`,
> #1879), so the historical in-tree copy (`substrate-kit/` + `tests/unit/substrate_kit/`) was
> deleted and the living-doc pointers repointed at the graduated repo. Two references live in
> **owner-gated files** the session may not self-edit (autonomy boundary, `.claude/CLAUDE.md`
> § Working agreement / Q-0194-rider), so they are proposed here instead:

**The proposal (owner decision needed — both touch executable/binding config).**
1. **`.claude/settings.json`** — remove the two now-dead permission-allowlist lines
   `"Bash(python3.10 substrate-kit/src/build_bootstrap.py*)"` and
   `"Bash(python3.10 substrate-kit/dist/bootstrap.py*)"` (lines 47–48). The paths no longer
   exist; the entries are inert but misleading — a later agent could read them as evidence an
   in-tree kit still exists.
2. **`.claude/CLAUDE.md`** — in the Q-0254 working-agreement bullet, the parenthetical
   `(substrate-kit/src/engine/templates/CONSTITUTION.md.tmpl + …)` now names deleted paths;
   reword to point at the graduated repo (menno420/substrate-kit `src/engine/templates/`).
   One-line wording change, no rule-content change.

**Why it needs the owner.** Both files are owner-gated (settings.json is executable config;
CLAUDE.md is read-only to unattended sessions — proposals only). Both edits are trivial and
carry no behavior change beyond removing dead references; recommendation: apply both as-is.

### Q-0256 — DIRECTED: dependabot PRs are reviewed by the first session that sees them, then merged (2026-07-09)

> **Context.** Six dependabot PRs (#1761–#1766, opened 2026-07-06) sat CI-green and
> conflict-free for ~3 days because nothing arms auto-merge for `dependabot/*` branches —
> the `auto-merge-enabler` workflow only arms `claude/*` PRs (by design, per the
> `.github/dependabot.yml` provenance comment: "they wait for review"). The owner was asked
> whether sessions should review-and-merge them.

**Owner's answer (2026-07-09, verbatim):**

> "yes dependabot PRs should always be reviewed by the first session that sees them and then
> properly merged but possibly we need to make some changes on a big version update, so in
> those cases it should either fixit and then merge, or just document that a dedicated
> session sould work on it"

**The rule this sets (durable home: `docs/operations/repo-settings-state.md` § Dependabot
PR policy):**

1. **Review-on-sight:** the *first* session that notices an open dependabot PR reviews it —
   diff + upstream changelog/breaking-changes check + grep of the repo's real usage of the
   package — and **merges it** (squash; CI green on the final head required, as always).
   Don't leave it for "someone else"; an open dependabot PR is unclaimed work for whoever
   sees it.
2. **Major version bumps:** actually assess the breaking changes against real usage. If the
   needed adaptation is contained → **fix it, then merge** (the fix goes through the
   session's own PR, or the green CI on the dependabot head is itself the evidence when no
   code change is needed). If it's too large for the current session → **don't merge**;
   write a dedicated-session work item (`docs/planning/` or `docs/ideas/`) and say so.
3. Merging = deploying (Q-0193) applies as normal; no extra confirmation step.

**Routing.** Recorded in `docs/operations/repo-settings-state.md` (durable rule) +
`docs/current-state.md` pointer. Executed same-session on the backlog: #1762–#1766 merged,
#1761 closed as a strict subset of #1762 (session PR #1886).

### Q-0257 — DISCUSS: should the auto-merge-enabler also arm dependabot PRs? (proposed 2026-07-09)

> **Context.** The root friction behind Q-0256: dependabot PRs sit unmerged because the
> `auto-merge-enabler` workflow arms only non-draft `claude/*` PRs, so a CI-green dependabot
> PR has no merge actor until a session happens to look. Extending the workflow is
> owner-gated (executable config, Q-0194-rider), so it is proposed here, not shipped.

**The proposal (owner decision needed).** Options, with a recommendation:

1. **Status quo + Q-0256 (recommended):** keep dependabot PRs un-armed; sessions
   review-on-sight and merge. The owner's Q-0256 wording ("should always be *reviewed* by
   the first session that sees them") argues *against* blanket auto-arming — auto-merge
   would land bumps with zero review, including majors like psutil 5→7.
2. **Partial arming:** extend `auto-merge-enabler.yml` to arm *only* dependabot PRs whose
   title/metadata marks them minor/patch (the grouped `*-minor-patch` update sets), leaving
   majors for session review. Reduces sit-time for the low-risk class, but a grouped
   "minor" bump can still pull a lockfile change worth eyes; and CI-green-then-merge with
   no review contradicts the plain reading of Q-0256.
3. **Full arming:** arm everything on green CI. Not recommended — directly contradicts
   Q-0256.

**Why it needs the owner.** Workflow files are executable config (owner-gated). If option 1
stands, no change is needed — this Q just records that the alternative was considered and
why it was not shipped.

### Q-0258 — Codex review relay: @codex is the standing reviewer for review-worthy-but-not-owner-only questions (owner directive, 2026-07-10)

> **Context.** Same-day findings converged: the fleet's post-merge review queue had zero
> entries after 116 merged PRs (the "review is post-merge" law had no appenders and no
> drainer — EAP program review §5.2), and sessions were parking review-wants in the
> owner-queue. The owner ruled live, in-session.

**The directive (owner's words, expanded).** Whenever a session feels something needs the
owner's *review* — as opposed to a true owner-only decision (product intent, irreversible,
external/money) — it relays the question to **Codex** instead: post a PR comment
mentioning **@codex** with the specific question/context, so Codex reviews asynchronously.
The owner is working on Codex settings so @codex is available in all valuable repos.
Consequences:

1. **Codex is the named standing drainer** of the post-merge review convention — the
   review-queue/"second eyes" path the merge-on-green law was missing.
2. **The owner-queue narrows to genuinely owner-only items** (Q-0240 decide-and-flag
   unchanged; this adds a *review* lane between "decide it yourself" and "park for owner").
3. **Q-0120 still governs the return path:** Codex's reply is input to verify against
   source, never an order — the receiving session re-verifies before acting.
4. Relay comment convention (template in
   `docs/planning/codex-review-integration-plan-2026-06-17.md`): context in 2–3 lines +
   the *specific* question + "reply with findings; a follow-up session verifies per Q-0120".

**Routing.** This entry (provenance) + the codex-review-integration plan (mechanics) +
round-3 launch pack §1 (fleet propagation via a manager playbook rule). Owner-side
prerequisite: enable the Codex GitHub integration on the valuable repos (owner queue).

### Q-0259 — five round-3 rulings: budget posture · gen-3 scope · rebuild pace · venture mandate · games program (owner, 2026-07-10)

> **Context.** The round-3 launch pack (§4 decision sheet + the five forward questions the
> review session asked) — owner answered all five live. Recorded verbatim-in-substance:

1. **Budget posture:** billing model unknown; if Projects stay within normal session
   limits, the 4 core projects can run **indefinitely — as long as they don't work
   excessively**. Consequence: cadence stands, but "no excessive work" is a design
   principle for routine prompts (bounded slices per wake), and the economics ledger's
   job is to *detect* excess, not to gate.
2. **Gen-3 scope = verify-and-consolidate, not a fresh break:** verify gen-2's results
   and find **the cause of the improvements**; improve the per-repo environments; give
   **every project a clear goal** and a **confirmed method of arming an hourly/2-hourly
   routine**. (The manager's gen-3 report should be structured around exactly these four.)
3. **Rebuild pace:** completion **as fast as reasonably possible** — keep the overnight
   pace; **use more Codex reviews on superbot-next** to catch errors quickly (owner: Codex
   is quite good at PR reviews → standing @codex review on substantive Builder PRs,
   extending Q-0258). Games run in parallel in separate projects and are finetuned for
   bot use later.
4. **Venture mandate:** yes — try to get it profitable to **fund the fleet's expenses**;
   no specific target beyond **durable, sustainable growth**; any methods allowed. Hard
   protocol: if a step needs money, venture-lab produces a plan showing **exactly what the
   owner must do/enable/buy**, plus a **conservative** earnings expectation and
   payback-time estimate — expect bad results, never overstate.
5. **Games program:** the owner will play the builds **after** the EAP, not now. Standing
   instruction: **3 dedicated game projects, each with their own repo**, that continuously
   improve existing games, invent new games, or mod other games — presenting **a few
   options wherever that feels wise** rather than asking. A capability test by design; the
   owner tests everything later and improvement rounds follow.

**Routing.** Round-3 pack §4b (answers) + §1 brief consumers; the manager maps the current
game lanes (superbot-games shared repo · pokemon-mod-lab · gba-homebrew) onto the
3-projects/3-repos shape decide-and-flag.

### Q-0260 — single-writable-repo rule: every Project except the manager attaches exactly ONE repo (owner directive, 2026-07-10)

> **Context.** Live dispatch session, round-3 boot day. Until now Projects often attached
> multiple repos, mainly for read access. Two same-day findings sharpened the question:
> Project-home ≠ repo-lane (a Venture-Lab-homed chat ran the substrate-kit lane overnight
> — the Project boundary does not constrain repo work), and all fleet repos are public and
> therefore raw-readable without attachment.

**The directive (owner's words, expanded).** Each Project, **apart from the fleet manager**,
gets **write access to exactly one repo** — its own lane repo. Cross-repo *reading* uses the
public raw path (`raw.githubusercontent.com`), not attachment. The manager keeps its
multi-repo attachment (its job is cross-repo oversight). Consequences:

1. **Environments compose with the §6b registry rule** (one env per repo, named like the
   repo): a Project selects its lane's single-repo environment; no new multi-repo envs.
2. **The founding-package line "you are an agent of THIS Project (repo X)" plus the
   single-repo attachment together are the lane boundary** — instruction + credential now
   agree, closing the cross-homed-lane class the Venture-Lab screenshot exposed.
3. **Private repos are the carve-out to watch:** raw-read only works on public repos.
   pokemon-mod-lab went private 2026-07-10, so any *other* Project's read of it now fails —
   in particular the manager's staleness sweep needs pokemon-mod-lab attached to the
   manager's environment (or accepts a DARK-by-privacy verdict relayed via the owner).
   Any future private repo inherits the same caveat.

**Routing.** This entry (provenance) + round-3 dispatch runbook §1 (design decisions) +
the founding packages (already single-repo: Idea Engine → superbot; Product Forge →
product-forge) + the manager's environments registry (fleet-manager `environments/`,
owner-relayed) for gen-3 env improvements per Q-0259 ruling 2.

### Q-0261 — core-6 launch order: one Project at a time, finalize-first; substrate-kit is the second Q-0260 exception (write-all for distribution) (owner directive, 2026-07-10)

> **Context.** Live dispatch session, after the gen-3 deployment sim (pipelined vs
> sequential) landed. The owner chose the work order for the system's roots explicitly.

**The directive (owner's words, expanded).**

1. **The standing core is SIX Projects** (revised from the launch-pack-§5 four), launched
   **strictly one at a time**: manager (live) → **substrate-kit** → **superbot-next** →
   **Idea Engine** → **Product Forge** → [sixth seat: owner names it — the five listed
   plus one; hub-superbot or websites are the candidates]. They run indefinitely, at
   least until the EAP ends.
2. **Finalize-first:** a Project does not launch until everything about it is finished —
   if its repo has unanswered questions or open ⚑ OWNER-ACTIONS, those are fixed
   *immediately, before* the boot, not carried as debt into the new generation. (For
   substrate-kit that means the F-5 ruling + its settings clicks land before its boot.)
3. **substrate-kit gets write access to ALL fleet repos** — the second Q-0260 exception
   (manager = read-everywhere oversight; kit = write-everywhere distribution) — so it can
   distribute kit upgrades and regenerate kit-owned conventions fleet-wide (EAP program
   review §6 agenda). **Hard scope guard, owner-stated:** it must not start taking on
   other repos' tasks — its founding instructions restrict lane-repo writes to kit
   distribution only (upgrade PRs, kit-owned convention regeneration, adoption fixes);
   never lane domain work, never another lane's inbox/status; its calibration answer must
   recite this boundary.
4. The deployment-standard's pipelined fast path (sim-backed) stays the method for the
   **post-core** manual/game lanes; the core-6 deliberately takes the sequential
   finalize-first shape — depth over speed for the system's roots.

**Routing.** This entry (provenance) + Q-0260 (amended by 3) + round-3 dispatch runbook §3
(reordered checklist) + `gen3-deployment-standard-2026-07-10.md` §0 note + the
substrate-kit founding package (drafted same session).

### Q-0262 — blanket application of the round-3 recommended answers (owner directive, 2026-07-10)

> **Context.** Live dispatch session. The owner: "apply all your recommended answers to the
> remaining owner questions wherever possible." Scope: the round-3 open decision set
> (launch pack §4 remainder + the session's open questions). Applied wholesale, each item
> flagged-for-veto per Q-0240; lane-inbox lines route via the manager (this session writes
> only superbot).

**The applied rulings:**

1. **Kit F-5 = Reading A** (the stricter reading). Bench runs 2–3 scored under A; family
   headline 1 PASS / 3 FAIL; B-benches unpause. (Launch pack §4.1 recommendation.)
2. **Trading P5 holdout: UNLOCKED** — `docs/p5-holdout-protocol.md` binding for the
   one-shot evaluation; sequencing: trading's own ORDER 007 (significance bar + AAPL
   re-grade) executes FIRST (its status names 007 as gating any holdout use). (§4.2.)
3. **superbot-next flag-13 corpus-red: the lane's own proposed disposition ACCEPTED** —
   proceed; reviewable at the parity gate (Q-0240 class). (§4.5.)
4. **Model-line policy: family-level names ONLY, everywhere** (fable-5, opus-4.8; exact
   IDs never) — un-nulls trading's model rows; matches superbot telemetry vocabulary.
   (§4.6.)
5. **OWNER-ACTION grammar: the kit's field set wins by definition**; venture-lab conforms
   at its next kit upgrade; kit §6.8 (grammar as kit-owned constant) embeds it. (§4.7.)
6. **The 8 undeployed instruction packages STAY undeployed** until re-based on the
   manager's gen-3 blueprint delta. (§4.8.)
7. **Pokemon concept pick = QoL+** (the lane's own recommendation; 12 patches form its
   foundation) — takes effect when the games program boots post-core. (§4.3; GBA
   release-prep was already ruled in Q-0259/§4b.)
8. **Core seat 6 (the Q-0261 open slot) = the superbot hub Project** (games-finishing /
   maintenance seat — the dispatch session's recommendation, applied under this
   delegation; ⚑ most-vetoable item of the set: it names a core roster member).

**Not appliable by delegation (stay owner-only):** the settings sweep (physical clicks —
consolidated by the manager's launch-readiness report), venture-lab ⚑A–D (external/money,
frozen behind the P0 Stripe-path fix), repo creations (product-forge, superbot-plugin-hello,
3 game repos).

**Routing.** This entry (provenance) + manager relay (lane-inbox ORDERs 1–3, policy lines
4–5) + runbook §3 updates + kit founding package §0.1 (F-5 now ruled).

### Q-0263 — never-ask posture: SB_TEST_DB_HOSTS demoted to optional; derivable values never route to the owner (owner directive, 2026-07-10)

> **Context.** The Builder env setup asked the owner to hand-derive a DB hostname for the
> test-plane allowlist. Three chat rounds of safety justification later, the owner ruled:
> this is a hobby project, the friction outweighs the guard, remove it so nothing ever
> asks for it. The deeper miss was already fleet doctrine (kit ORDER 008: asks must be
> paste-ready or not reach the owner) — this entry generalizes it.

**The directives:**

1. **SB_TEST_DB_HOSTS becomes fully optional and silent** (superbot-next ORDER 010):
   absent/empty ⇒ no host restriction on the test plane — the boot proceeds and logs the
   connected host once, loudly. The allowlist logic only engages if someone deliberately
   sets the variable someday (e.g. at a future prod cutover). No boot refusal, no error
   naming it, no ask. `SB_DATA_PLANE` stays required (unquestioned, one word, set once);
   `SB_PROD_ATTEST` and the prod-refusal rail are untouched.
2. **Agents never route derivable values or safety string-work to the owner.** If an
   agent can compute a value (from an env var, a file, an API), it computes it — or the
   booting seat self-reports the finished `NAME=value` line for a one-paste copy. An env
   ask that requires the owner to parse, derive, or transform anything is a drafting
   defect (kit ORDER 008 class), not an owner task.
3. **Safety-posture calibration, owner's words:** "we spend way too much time on safety
   … this is just a hobby project." Scope: friction-costing guards on the owner's own
   surfaces. NOT rescinded: the production-data rails that run silently (plane
   separation, prod attestation), Q-0213's live-bot brake, and the no-secrets-in-repos
   rule — those cost the owner nothing.

**Routing.** This entry (provenance) + superbot-next inbox ORDER 010 (the code change) +
Builder founding package §3 (field removed) + future founding packages inherit rule 2.

### Q-0264 — idea-pipeline redesign: own-repo Idea Engine + a Simulator Project as core seat 6; evidence-gated routing through the manager (owner directive, 2026-07-10)

> **Context.** Live dispatch part-3 session, at the seat-4 boot. The owner stopped the
> original superbot-homed Idea Engine boot: *"we are currently overcomplicating it and
> also missing a step."* The redesign came in his words across the same conversation;
> the sub-forks were settled in two structured-choice rounds (all recommendations
> taken). The owner was the live reviewer — this entry is the provenance record.

**The directives (owner's words, expanded):**

1. **The Idea Engine works from its OWN repo (`idea-engine`)**, not superbot — so
   multiple agents can work in parallel in that Project. The repo is divided into
   **sections, one per main part of the repo system** (derived from the fleet manifest's
   active lanes + one `fleet/` cross-cutting section — never a hardcoded list), plus the
   ideas each section generates *for* that target. Supersedes the v1 package's
   superbot-homed design (env, sole-writer control seeding, in-place promotion).
2. **The missing step: a dedicated SIMULATOR Project (`sim-lab`) — core seat 6**,
   superseding the Q-0262.8 superbot-hub pick (that item was ⚑ flagged most-vetoable;
   the veto arrived). The Idea Engine routes its ideas there; the simulator creates
   **simulation-based results and suggestions — best implementations,
   rejections/approvals — based on facts that it reproduces, as well as its own
   judgement.** Precedents generalized: `tools/sim/claim_layout_sim.py` (settled
   Q-0195) and `tools/sim/gen3_deployment_sim.py` (settled the gen-3 deployment
   method) — decisions settled by reproducible evidence, not vibes.
3. **Validity gate:** each simulator result goes through a fixed question set before
   its verdict counts — are these results comparable to the real live situation? are
   they not corrupted (bugs, seeded luck, parameter cherry-picking)? do they survive
   variation? can someone else re-run them? what do they NOT show?
4. **Codex review before finalization:** every finalized verdict gets an @codex review
   (Q-0258 path; Q-0120 verify-never-obey; the #1945 sandbox-reply caveat applies).
5. **No extra coordinator/builder step.** Finalized evidence packages go to the fleet
   manager — coordination is its job, so **final review is its job too** — and it
   routes them as ORDERs into the proper repos; lanes build their own orders. The
   dedicated hub-executor seat the dispatch copilot had proposed is dissolved; hub
   games-finishing work routes to the games program (Q-0259 r.5) / owner-started
   superbot sessions instead.
6. **Flow mechanics (structured-choice round 2):** sim scope = **all build-worthy ideas,
   cheapest adequate method** (numeric sim / measured prototype / explicitly-labeled
   JUDGMENT-ONLY analysis — the manager always sees the evidence strength); intake =
   **direct pull** (the Idea Engine marks sim-ready ideas in its own outbox; the
   simulator reads it on wake via public raw; the manager touches only the output side).
7. **Reusable simulator templates (owner rider, same conversation):** the simulator's
   product is not just verdicts — it builds **reusable sim templates/harness scripts on
   its public repo** that other Projects can consume (raw/copy), and **other Projects
   that come across substantial simulator work route it to sim-lab** rather than
   building one-off sims inline (trivial inline scripts stay allowed; the routing rule
   is for substantial/reusable work — lanes flag it, the manager routes it). If the
   harness matures into fleet-wide adoption, it graduates to kit distribution (the
   substrate-kit §6 centralization pattern) — start as sim-lab's own public product.
8. **Standing sub-decisions carried from round 1 (still in force where compatible):**
   superbot's existing `docs/ideas/` is **referenced, not migrated** (the engine's
   superbot section indexes by link); the engine works **all three idea classes**
   (product / process-doctrine / venture-revenue) **priority-weighted** per Q-0259
   (games completion wave + rebuild pace first); lane intake = **harvest-on-wake**
   (lanes keep filing ideas locally; the engine sweeps via public raw). The round-1
   "seat-6 hub executor" fork is superseded by directive 5.

**Routing.** This entry (provenance) + the rewritten
`planning/round3-founding-package-idea-engine-2026-07-10.md` (v2, own-repo) + the new
`planning/round3-founding-package-simulator-2026-07-10.md` (seat 6) + runbook §3
reorder (seat-6 swap, new owner clicks) — all this session.

### Q-0265 — continuous mode for ALL six core seats: the routine is a failsafe, not the pacemaker (owner directive, 2026-07-10)

> **Context.** Live dispatch part-3b. The owner asked two freshly-booted seats (Product
> Forge, Ideas Lab) "what caused you to stop working?" — both answered, correctly, that
> they are idle by design between 2-hourly wakes. Owner: *"I thought the instructions
> were supposed to keep you working for as long as possible"* / *"I thought you were
> supposed to keep working on ideas indefinitely, with the routine as a failsafe trigger
> to wake you up in case you stalled"* — and the rationale: *"since nearly all of these
> projects are meant to produce real work that basically has no end, they really don't
> have any reason to stop."* Diagnosis (copilot, confirmed): the founding packages
> carried the gen-2 maintenance-seat pacing doctrine — "ONE bounded pass … no excessive
> work — one real slice per wake" — into open-ended production seats. The seats obeyed
> their instructions; the instructions encoded the wrong operating model.

**The directive (scope chosen by the owner in a structured round: ALL SIX core seats —
manager, substrate-kit, Builder, Idea Engine, Product Forge, Simulator):**

1. **Work continuously.** When a slice finishes and genuinely useful work remains,
   start the next slice immediately, same turn. Each slice still lands as its own
   merged-on-green PR — reviewability is unchanged; the throttle is removed, not the
   ceremony. Near context limits, hand off cleanly (fresh card/branch) instead of
   degrading.
2. **The continuation chain is the pacemaker:** before ending ANY turn, arm a
   `send_later` ~10–15 minutes out ("continue the work loop"). This self-re-arm chain —
   the pattern that shipped 116 PRs overnight on 2026-07-10 — is what keeps a seat
   running.
3. **The standing cron is demoted to dead-man failsafe** (the owner's exact framing):
   same cadence, new prompt — on a cron wake, if the chain is alive, verify liveness in
   one line and end; if the chain stalled, resume the work loop and re-arm it. Live
   seats re-arm their own cron (delete + create, verbatim record in status — the
   proven recipe).
4. **Backpressure replaces the time throttle:** pause the specific activity whose
   downstream queue is saturated (generation pauses when several outbox proposals sit
   unpulled; building pauses at done-when + empty inbox AFTER flagging the manager) —
   grooming, verification, hygiene, and backlog work continue meanwhile.
5. **The honesty guard survives (Q-0089):** genuinely out of useful work → say so in
   status and idle until the failsafe. Forced filler is worse than none — continuous
   mode removes the throttle, never the quality bar.
6. **Cost posture — the copilot's flag INVERTED by the owner (same conversation):**
   *"especially now since the projects are still free, we should make use of them
   excessively."* High usage during the free window (through 2026-07-14) is the point,
   not a risk to minimize — seats lean toward MORE parallel work (child sessions,
   fan-out) within the quality bar, not less.
7. **Produce-then-curate (owner's words):** *"then we can use everything we produced now
   afterwards in a consolidation session to find out what is worth keeping etc, this is
   also a good way for us to produce a lot of test results for anthropic."* Two
   consequences: (a) a **post-window consolidation pass** is planned owner-side — the
   manager preps the fleet-wide inventory of what was produced so the keep/kill session
   has its material; (b) the volume doubles as **EAP evaluation data** — seats keep the
   reporting bar (citations, honest states) precisely so the output stays usable as
   test results, not noise.

**Rollout:** live seats (manager, kit, Builder, Idea Engine) get the owner-pasted
amendment block (part-4 brief §2b); unbooted packages (Product Forge, Simulator)
rewritten so their boots inherit it natively; the manager folds Q-0265 into the gen-3
blueprint delta so every future seat is born continuous.

**Routing.** This entry (provenance) + the amendment block in
`planning/round3-dispatch-part4-brief-2026-07-10.md` + package rewrites/banners (forge,
simulator, idea-engine, builder, runbook §2 manager) — all part 3b (PR #1958).

### Q-0266 — volume-first founding doctrine: maximize output at creation, consolidate later (owner directive, 2026-07-10)

> **Context.** Live dispatch part-4b, minutes after the trading founding package was
> drafted. Owner, verbatim: *"any project should be created with the idea of as much
> output as possible, it should be as correct as possible, but it does not always need
> to be the best, if we get as much production as we can as early as we can, we can
> then consolidate later into only a few dedicated projects that slowly maintain what
> we created, but first the goal should be to really populate all repos with as much
> material as we can."* This is the founding-time generalization of Q-0265.6/.7
> (free-window excess + produce-then-curate), extended in three ways:

1. **Scope: EVERY project, at creation.** Volume-first is a founding-doctrine default
   for all future packages/seats (games program, trading conversion, any later repo) —
   not a property of the six core seats only. Founding packages are written so the seat
   maximizes output from its first turn.
2. **The quality bar, named: CORRECT over BEST.** Output must be as correct as possible
   (honest states, citations, working increments — the Q-0265.5 honesty guard and each
   lane's integrity floor are untouched), but it need not be optimal or polished —
   good-enough implementations ship now; refinement is consolidation-phase work. A
   lane's non-negotiables (e.g. trading's pre-registration/one-shot-holdout contract)
   are part of CORRECT, never tradeable for volume.
3. **The fleet lifecycle, explicit: populate → consolidate → maintain.** Phase 1 (now):
   populate ALL repos with as much material as possible. Phase 2 (later, owner-gated):
   a consolidation pass keeps what is worth keeping and collapses the fleet into a few
   dedicated projects that slowly MAINTAIN what was created. Seats should produce with
   that future triage in mind — committed, discoverable, honestly-labeled artifacts
   (the Q-0265.7 inventory thread is the mechanism).

**Rollout.** Applied at birth to the trading package (same PR); future packages carry a
volume-first clause from drafting; folded into the gen-3 deployment standard §2 next to
the Q-0265 fold (same PR) so every future seat inherits it; live seats need no new
paste — Q-0265 §2b already removed their throttle, and this rider primarily governs how
NEW seats are founded.

**Routing.** This entry (provenance) +
`planning/round3-founding-package-trading-2026-07-10.md` (§1/§2 volume-first clauses) +
`planning/gen3-deployment-standard-2026-07-10.md` §2 rider — part-4b (PR #1963).

### Q-0267 — games mapping owner-shaped: world seat + idle-engine seat, theme-skin architecture, website-first onboarding (owner directive, 2026-07-10)

> **Context.** Live dispatch part-4e, ~40 minutes after the Q-0259 r.5 mapping relay was
> pasted to the manager. The owner gave the shape himself. Verbatim: *"now for the games,
> I already have the superbot-plugin-hello repo, and there is one repo where both
> exploration and mining live, I think we should get one project on that repo working on
> those 2 pieces of the game, also add in the fishing and anything that belongs in the
> exploration/world ecosystem etc, and then there should be another repo and project for
> the egg farm idle game, and that shoud work on shipping some templates, which should
> eventually be choosable before you even invite the bot to your server, my idea is tha
> tyou'll first go on the website to select which features you want, and it would be
> great if we can make th games we have customizable in theme, so the core will be the
> same, but we can ship differed skins over it so every discord server can have an idle
> game that mathces its theme etc, do you understand what I mean? can you expand and
> improve on my ideas"*

1. **The mapping is owner-shaped, superseding the open manager-proposal step as the
   source of the shape.** The manager's Q-0259 r.5 deliverable becomes a *conformed*
   mapping — fill in details (data-API placement, theme-contract home, new repo name,
   first-shippable sequencing), not propose an alternative frame.
2. **Seat A:** ONE Project on `superbot-games` owning the whole world ecosystem —
   exploration + mining + fishing + world-adjacent systems. Gen-2 merges the two
   terminal gen-1 lanes into one seat (their committed succession packages are the boot
   input).
3. **Seat B:** a new repo + Project for the egg-farm idle game, **template-first** —
   the deliverable is themeable templates, eventually choosable before invite.
4. **Website-first onboarding** (product direction): select features/themes on the
   website BEFORE inviting the bot; the bot arrives configured.
5. **Core/skin split:** same game core, data-only theme packs per server — every
   Discord server can run an idle game matching its own theme.

**Expansion (owner-requested "expand and improve"), decided-and-flagged per Q-0240:**
`docs/ideas/games-theme-engine-website-first-2026-07-10.md` — theme packs as validated
data manifests (theme-gate CI; the best Q-0266 populate-phase fit in the program), egg
farm as first theme of an idle ENGINE, setup-code interim provisioning before join-time
manifests, plugin-seam convergence (superbot-next ORDER 002 / `superbot-plugin-hello`),
sim-lab as the idle-economy verdict path.

**Routing.** This entry (provenance) + the idea file above (expanded design) + dispatch
runbook §3.7 re-point + §6.2 conformed-mapping paste block — part-4e (PR #1966).

### Q-0268 — autonomy vs. the money/account line: real-identity setup then keys, never burner-signup (owner directive, 2026-07-11)

> **Context.** Live dispatch part-4h, just after the venture-lab boot prompt was sent.
> The owner asked whether providing a burner email + throwaway credit-card details would
> let the agents create accounts in his name and run the revenue lane fully autonomously.
> The answer is NO — and the reasoning is now doctrine so no future seat (or agent
> advising the owner) re-opens it.

1. **The money/account HARD LINE stays exactly where the money protocol (Q-0259.4) and
   the Q-0268-referenced permissions grant put it:** agents never spend real money,
   create external/payment accounts, or run payment flows on partial identity. This is
   NOT fleet timidity — it is external reality: (a) payment processors require KYC /
   real-identity verification before payout, which an agent cannot complete; (b) a
   burner-email + throwaway-card signup is the exact fraud signature that gets accounts
   FROZEN and funds HELD, defeating the revenue goal; (c) the platform auto-mode
   classifier refuses agent card-entry / account-creation anyway (same wall class as the
   held permission grant). So the burner mechanism does not buy autonomy — it trips three
   independent failures.
2. **Agents do NOT help route around identity verification** — even for the owner's own
   venture. Providing card details to an autonomous agent for signup flows is refused;
   the decision is recorded here so it is not re-litigated.
3. **The path to MAXIMUM durable autonomy (what the owner actually wants):** the
   account-creation + payout step is a ONE-TIME ~30-minute human step (real identity,
   because KYC requires it regardless). Everything on both sides of it is agent-run:
   before it, the seat builds products/listings and validates the full purchase→webhook→
   grant flow in **Stripe TEST mode** (real API shape, zero real money, no freeze risk);
   after it, the owner drops the **API keys** the accounts generate into the env and the
   agent operates the store *through those keys* (create products, update listings, run
   the automated grant flow) — legitimate, ToS-clean, un-freezable because the account is
   properly the owner's. So autonomy is ~95% with one short human gate, durably.
4. **Buildable steer (venture-lab):** the seat emits `docs/owner-setup-checklist.md` —
   the exact, ordered, minimal real-account steps + which env-var NAMES each key fills —
   so the owner's one-time setup is turnkey; and it proves the paid path end-to-end in
   test mode first (the D1 lesson: never claim a payment path works without executing it).

**Routing.** This entry (provenance + the durable line) + the venture-lab relaunch pastes
carry it implicitly via the money protocol / permissions block — part-4h (PR #1971).

### Q-0269 — DIRECTED: live sessions merge finished PRs themselves — never park green PRs on the owner's queue (2026-07-12)

> **Context.** After the overnight fleet review, the hub session (owner live in-chat) left
> two verified-green, complete PRs (websites #158, fleet-manager #92) "parked READY+green
> awaiting the owner's merge click," importing the Project-seat merge wall into a session
> that doesn't have it. Owner, verbatim: *"you just merge everything, only the projects have
> trouble with those things, I expect from a normal session that any mergable PR in finished
> state just gets merged immediatly, we're wasting a lot of time with the fact that agents
> direct me to PRs, it's not my task to do that."*

**Decision (owner-directed in-session).** In any session where the owner is live (hub
sessions, help sessions — anything not running as an autonomous Project seat): **a mergeable
PR in finished state (CI green, card complete, READY) gets merged immediately by the agent.**
Directing the owner to a green PR is a workflow failure, not a courtesy. "Park READY+green
for the owner's click" remains **only** the fallback for Project/auto-mode seats that the
merge classifier actually denies — and even those should first try, then park on a real
denial, not preemptively. Executed under this directive the same minute: websites #158
(squash `b925072`) + fleet-manager #92 (squash `9a8518f`); fleet-vocab guardrail line
updated. What stays genuinely owner-only: infra account actions (Railway service creation,
tokens), personal-content decisions (venture-lab #51), and PRs whose checks the platform
never ran (mineverse #42) until the checks are re-triggered.

### Q-0270 — DIRECTED: the boot triad — every new session establishes model · venue · ability envelope before directing its work (2026-07-12)

> **Context.** Owner, live in-session (same conversation as Q-0269), verbatim: *"another
> addition to the rules, not for just the prjects but in general, when a new session
> initiates, one of it's goals should be to fnd out what model it's running on, and where
> the session is running and what that means for the abilities, that decides how the
> session eventually directs it's work, so project chats avoid anything that stalls,
> normal sessions with me in the chat should always assume no special limitations apply."*

**Decision (owner-directed in-session; applied to CLAUDE.md § "Read first" with this Q as
provenance).** Session start includes a self-orientation triad: **(1) model** (state it,
family-level — feeds the `📊 Model:` card line and the B2 telemetry; also the agent-side
compensation for the platform's config-vs-reality gap documented in the EAP email);
**(2) venue** (owner-live chat / autonomous Project seat / routine-fired wake / subagent;
remote vs local); **(3) ability envelope** (documented walls: merge authority, permission
prompts, cross-session limits). The triad sets the working posture: autonomous sessions
pre-route around known stall classes and park only on a real denial; owner-live sessions
assume no special limitations (Q-0269). **General scope:** this is fleet doctrine, not
superbot-local — relay to the fleet-manager registry (UNIVERSAL / startup templates) via
the owner's paste or the manager's next doctrine pass, and to substrate-kit as template
material so it travels to every future repo.

### Q-0271 — DIRECTED: fleet-wide never-wait — seats never gate work on owner presence; owner-only list is the sole park class (2026-07-12)

> **Context.** Owner, live in-session (the fleet re-arm session, superbot PR #2048), verbatim
> excerpts: *"I've noticed that a lot of projects halucinate what they can or can't do, in the
> sense that they gate a lot of work on my presense what really shouldn't be necessary, the
> goal is that each project just keeps executing and doesn't wait for my reviews … I want to
> prevent this in the next run so we can find out what happens if our system acually runs
> smoothly, and by that I mean that the projects actually work together … anything uncertain
> should be routed to the idea/sim lab … quantity is our power here, if we have 100 finished
> prducts ready tomorrow instead of 10, the changes of earning are 10x bigger, ofcourse
> everything should happen properly and structured, that's why the fleet manager must also
> make sure to properly route all the work and keep track of all the repos and update stale
> docs etc."*

**Decision (owner-directed in-session).** The Q-0241 never-wait / silence=consent posture is
**generalized fleet-wide for Project-seat work** (it was scoped to the rebuild program): a seat
never holds finished work for review, never waits for owner presence to continue, and treats
any "I'll wait for the owner to approve/allow continuation" impulse as a hallucinated gate
unless it names an **OWNER-ONLY class**: repo settings/rulesets · secrets/env/host
provisioning · external publish + spending money · destructive prod-data ops · account/portal
steps. Those park as six-field owner-queue items (citing the probed wall, per the
disconfirming-probe rule) — **queue-and-continue**, never wait-in-place. Uncertainty routes to
Ideas Lab (SIM-REQUEST valve) instead of blocking. The enforcing artifact is the **AUTONOMY
RIDER** in [`fleet-rearm-2026-07-12.md`](./fleet-rearm-2026-07-12.md) §3, embedded in every
seat's 2026-07-12 re-arm prompt and destined verbatim for the v3.4 instruction bodies
(fleet-manager #121/#122 lane) + the substrate-kit templates. **Unchanged:** the live prod
bot's Q-0213 destructive brake; CI-green as the merge floor (never-wait ≠ bypass CI); the
honest-negative bar. **Scope note:** this is fleet doctrine — superbot's own hub sessions
already carry the stronger Q-0269 merge-immediately rule.

### Q-0272 — DIRECTED: standing cross-repo read authorization + the multi-repo reading path in boot orientation (2026-07-12)

> **Context.** Owner, live in-session (the fleet re-arm session, superbot PRs #2048/#2049 →
> this follow-up), correcting the agent's superbot-only reading posture, verbatim: *"doesn't
> the ruperbot repo also tell you that we have more repos, and links to many files in other
> repos"* → *"all repos except the pokemon mod lab are public, so you can view any file just
> as easily as you could view superbot"* → *"first I want you to make sure there is a properly
> suggested multi repo reading path for new sessions, so that we can save 3 turns of
> discovery."*

**Decision (owner-directed in-session; CLAUDE.md pointer applied under the in-session
exception with this Q as provenance).** (1) **Standing authorization:** read-only cross-repo
access to every fleet repo (all public except `pokemon-mod-lab` — DARK, skip) via
`raw.githubusercontent.com` / `git clone` / `git ls-remote` is standing-authorized for every
session in this repo — sessions must not spend turns re-deriving whether they may look.
Boundaries unchanged: GitHub MCP stays scoped to attached repos; writes stay in-repo;
cross-repo work routes via fleet-manager ORDERs; deep/audit work uses `add_repo`+clone.
(2) **The reading path is boot-visible:** canonical route = **`docs/fleet-reading-path.md`**
(repo map · tiers · truth rules) + **`scripts/fleet_status.py`** (one-command per-seat
heartbeat sweep), pointed from `.claude/CLAUDE.md` § Read first, `docs/AGENT_ORIENTATION.md`
(new cross-repo read-only route), and the journal Quick reference. (3) **Kit-graduation
candidate:** the per-repo reading-path pattern should travel via substrate-kit templates so
every repo names its own siblings — routed to the Self Improvement lane.

### Q-0273 — DIRECTED: the hub-venue model, the v2 night goals, and the self-initiative/skills program (2026-07-12, ~23:00Z)

> **Context.** Owner, live in the hub session (same conversation as Q-0271/Q-0272), three
> connected directives. **(1) Venue correction**, verbatim: *"I did not paste it's final
> message here, that was a seperate chat outside the projects like you, and that's currently
> necessary because the projects don't always have the right permissions, or think they don't
> have it, because of mis interpreted harness prompts or too strict harness prompts etc,
> that's why this seperate chat must always exist, to merge or close the stray PRs, execute
> sensetive or destructive actions, sometimes it works from the projects but sometimes it
> does't, and in here it always works, just sometimes prompts me."* The Project Manager's
> mission: *"keep track of everything the fleet does and continue to dispatch orders in their
> repos while I'm away, it also helps me with general project related things or ideas I might
> have."* **(2) Revised night goals per seat** (2.0 max-finalization incl. core/admin/setup
> production-ready + command/button curation; World finalize mining/fishing/idle as games +
> the one minigame/casino section spec; Ideas Lab endless any-domain cycle; Venture both
> lanes — many books incl. multiple versions each, more strategies/stocks/indicators,
> WEBSITE-IDEA markers; websites clarity bar "every page shows immediately what it is, what
> it does, the most important features" + "should not stop until it's all done. And actually,
> well made"; Game Lab mass production beyond GBA/NDS — browser + mobile foundations).
> **(3) The self-initiative program** for substrate-kit, verbatim core: *"an agent should be
> eager to initiate helpfull actions … they could easily lead with the link and the
> copy/paste ready file in chat as a seperate block … should be baked into a method, like a
> skill, that prevents it from taking up too much storage in the claude.md itself, but is
> still always loadable on demand … 'how do I instruct the owner on it's task and prepare
> things for him along the way' … 'I got a reference that haven't found yet, I should find
> out the most logical place where it might be and start looking'. so every agent actually
> self improves in the usefull ways."* Founding incident he cites: this session's own
> opening-message reference miss (the linked brief + named repos not read → the ~3-turn
> Q-0272 discovery).

**Decision (owner-directed in-session).** (1) The **hub venue** (owner-live chat outside the
Projects) is a standing, permanent part of the fleet model — not a seat: it merges/closes
stray PRs and executes sensitive/destructive actions that seat venues can't (or believe they
can't); owner-queue items that are merge/destructive-shaped carry a **`VENUE:hub`** tag.
(2) The revised goals shipped as **NIGHT ORDERS v2**
([`fleet-night-orders-2026-07-12.md`](./fleet-night-orders-2026-07-12.md) §2, superseding v1
in place; v1 in git history). (3) Two **seed skills** shipped in superbot as reference
implementations for the kit to generalize — `.claude/skills/chase-references/` (resolve every
reference in an ask before acting) + `.claude/skills/prep-owner-steps/` (lead with the deep
link + paste-ready blobs; map the owner's steps; batch to one sitting) — and the kit's v2
order carries the full self-initiative program (skill-pack mechanism + the rationalization
layer: sessions ask themselves "does this lesson deserve a permanent home I can ship now?").
