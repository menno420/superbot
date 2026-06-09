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
**Status:** Open
**Question:** Is a player guild/clan scoped independently inside each Discord server, or may one player guild span multiple Discord servers? If cross-server identity is wanted, what consent, discoverability, moderation, ownership-transfer, retention, deletion/export, and main-server behavior should apply?

**Why agents need this:** The answer determines the canonical keys and owner for membership, treasury, battles, profiles, and leaderboards. Guessing would create either a duplicate per-server system or an unapproved cross-server identity system.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** Treat the social roadmap as planning-only. Do not create a guild/clan schema or expose cross-server profiles. Preserve existing Discord-guild scoping.

**Suggested destination after answer:** `docs/planning/social-community-progression-roadmap-2026-06-08.md` and a dedicated ownership/ADR decision if a new social domain is approved.

### Q-0039 — Which VIP/donation benefits are acceptable under the no-pay-to-win rule?

**Area:** Economy / rewards
**Type:** Product, monetization, and fairness boundary
**Priority:** High (blocks VIP planning)
**Status:** Open
**Question:** Should VIP/donation tiers be limited to cosmetic identity and supporter recognition, or may they include convenience benefits? Which exact benefits are explicitly allowed or forbidden, and should donation status ever be stored or processed by SuperBot itself?

**Why agents need this:** “No pay-to-win” is binding owner intent, but convenience, lottery entries, marketplace privileges, and economy-adjacent perks can still create gameplay advantage or external billing/privacy obligations.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No paid/donation benefit affects XP, coins, drops, odds, cooldowns, market access/fees, guild power, or game outcomes. Do not add billing/provider integration.

**Suggested destination after answer:** `docs/planning/economy-marketplace-rewards-roadmap-2026-06-08.md` and, if external payment data is approved, the integrations/privacy decision set.

### Q-0040 — What operational posture should an AI dungeon master use?

**Area:** AI / games / social
**Type:** Product, cost, moderation, and retention boundary
**Priority:** High (blocks AI dungeon-master and player-prompted event planning)
**Status:** Open
**Question:** For thread, persistent-channel, and DM modes, what should persist; who may start/join/control a session; what content/moderation limits apply; what cost/rate limits are acceptable; and may AI ever propose mechanics/rewards beyond narrative wrapping of deterministic game-owned outcomes?

**Why agents need this:** The answer governs state ownership, privacy, content safety, provider spend, and whether the feature remains explanation/narrative-only or requires a future action-authority decision.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No implementation. AI may not own rewards, difficulty, quests, or state mutations; all current AI expansion/action gates remain binding.

**Suggested destination after answer:** `docs/ai/ai-product-extension-routing-2026-06-08.md` and the authoritative `docs/planning/ai-roadmap-2026-06-07.md`.

### Q-0041 — What privacy and provider posture should integrations and voice use?

**Area:** Integrations / media / voice
**Type:** Privacy, credentials, moderation, retention, and degraded-provider policy
**Priority:** High (blocks Twitch, YouTube alerts, Spotify/Last.fm, Steam, music, SFX, and speech commands)
**Status:** Open
**Question:** Which provider integrations should be considered first, who supplies/owns credentials, what user/server consent is required, what data/content may be cached and for how long, what moderation rules apply, and how should alerts/voice features behave when providers fail or rate-limit the bot?

**Why agents need this:** These ideas share secrets, personal activity, third-party terms, moderation, retention/deletion, rate-limit, and outage behavior. Implementing one ad hoc would create a parallel provider or delivery path.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** No new provider or voice implementation; retain only the existing ADR-007-owned media seams and require opt-in, bounded retention, and safe degraded behavior in future plans.

**Suggested destination after answer:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md` and the media folio/ADR if the shared platform boundary changes.

### Q-0042 — Should a full web dashboard become a future product surface?

**Area:** Website / cross-cutting UI
**Type:** Product investment + architecture boundary
**Priority:** Medium (future-only; blocks website planning)
**Status:** Open
**Question:** Is the intended website a read-only companion, a full management surface, or not a priority? If management is wanted, what authentication/authorization model, hosting/operations budget, privacy posture, and limit on website-specific behavior should apply?

**Why agents need this:** A website can easily become a second control plane, duplicate Discord-native panels, or bypass domain mutation/audit/permission paths.

**Handling (Q-0051, 2026-06-09):** a draft-answer session is queued — the agent drafts a concrete proposed answer for the maintainer to mark up; safe default holds until then.

**Safe default until answered:** Keep the website at Someday. Mature Discord-native panels and canonical read/mutation services first; do not create website-specific authority or mutations.

**Suggested destination after answer:** `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md` and a dedicated architecture decision if promoted.

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
**Status:** Open

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
**Status:** Open

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
**Status:** Open

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
**Status:** Open

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
**Status:** Open

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
**Status:** Open

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
**Status:** Open

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
