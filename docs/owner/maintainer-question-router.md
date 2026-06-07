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
