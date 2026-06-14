# External systems watchlist — what to learn from, and re-check

> **Status:** `reference`. A living watchlist, not a plan or approval. Capture-and-learn only;
> the binding contracts and source win. **Last reviewed:** 2026-06-14 (created).

## Why this exists

This project's real artifact is the **self-improving agent workflow** — the memory, journal,
hooks, router, and tooling that let any agent work correctly with little steering
(`.claude/CLAUDE.md` Working agreement). That dimension — *curated, version-controlled,
self-governing memory plus a self-audit loop* — is the one most agent projects neglect, and the
one that compounds. To keep compounding, we should periodically look at what the rest of the field
is doing and steal the good parts.

This page lists the systems worth learning from. Each entry is **lesson-first**: what it is in one
line, the single transferable idea, **what we already do vs. the gap**, and where to check for new
output. It is deliberately short — a watchlist, not a survey.

> **Honest framing (so a future agent calibrates correctly):** we are *not* ahead on raw execution
> — the plan→code→PR→CI→merge loop is shared with OpenHands, Devin, Factory, Sweep. We are ahead on
> the **memory + governance discipline** that makes execution compound. So when reading these
> systems, weight ideas that strengthen *that* (retrieval, self-reflection measurement, automatic
> curriculum) over ideas that just re-implement the execution loop we already have.

---

## The watchlist

### 1. Voyager (NVIDIA, 2023) — automatic curriculum + skill library
- **What it is:** an LLM agent in Minecraft that proposes its own next task (automatic curriculum),
  writes skills as reusable executable code, and self-verifies before adding a skill to its library.
- **The lesson for us:** our curriculum is *manual* — the owner drops ideas, agents groom them
  (`docs/ideas/`). Voyager's curriculum is *automatic*: the system proposes the next most-learnable
  task itself. The open question it poses: **can next-task selection be more principled/automatic**
  instead of owner-seeded + heuristic?
- **Our status:** GAP. We have a skill *library* (`scripts/hermes/skills/`, `.claude/` skills) and a
  backlog, but task selection is heuristic (active-work + roadmap + grooming), not a learned curriculum.
- **Where to check:** the Voyager project repo & site (MineDojo / "Voyager" by Guo, Fan et al.);
  follow-up "open-ended agent" work from the same group.

### 2. Reflexion (Shinn, Cassano, Gopinath, Narasimhan, Yao, 2023) — self-reflection as memory
- **What it is:** an agent that writes a *verbal* self-reflection after a failed attempt and stores
  it as episodic memory, measurably improving the next attempt.
- **The lesson for us:** this is **exactly our Q-0102** "review the previous session" ender — but
  ours is *unmeasured*. Reflexion treats the reflection as an input whose value is observable. The
  improvement: **close the loop — did last session's review demonstrably change what this session
  did?** Make the self-audit measurable, not ceremonial.
- **Our status:** PARTIAL. The reflection ritual exists (Q-0102); the *measurement* of whether it
  helps does not. Pairs with the session "context delta" idea (`.sessions/README.md`).
- **Where to check:** the Reflexion paper + citing work on verbal/episodic agent memory.

### 3. Generative Agents (Park et al., Stanford, 2023) — scored memory retrieval
- **What it is:** agents with a memory *stream* retrieved by a score combining **importance ×
  recency × relevance**, plus periodic "reflection" that synthesizes higher-level memories.
- **The lesson for us:** we retrieve memory by a **fixed hand-curated reading order**
  (`AGENT_ORIENTATION.md`). That is great at small scale and is *why* orientation is reliable — but
  as `current-state.md`, the journal, and `docs/` grow, **scored retrieval scales better than a
  static list.** Worth prototyping a relevance/recency-ranked "what should I read for *this* task?"
  layer on top of the fixed route, not replacing it.
- **Our status:** GAP (by design, for now). Fixed reading-order is a deliberate strength; scored
  retrieval is the scaling escape hatch when the read-path gets too big.
- **Where to check:** "Generative Agents: Interactive Simulacra of Human Behavior" + memory-stream
  follow-ups.

### 4. MemGPT / Letta (2023→) — self-managed tiered memory / context paging
- **What it is:** an agent that manages its *own* context window — paging information between
  in-context "main memory" and external storage, deciding what to keep resident.
- **The lesson for us:** we already do a crude version (archives: `.session-journal-archive.md`,
  `docs/archive/`, per-file `.sessions/`). MemGPT formalizes it as the agent **actively paging its
  own memory**. The lesson: as the living ledger grows, make context-paging an explicit discipline
  (what graduates to archive, what stays resident) rather than ad-hoc.
- **Our status:** PARTIAL. Archive discipline exists; agent-driven paging policy is informal.
- **Where to check:** the Letta project (formerly MemGPT) repo + docs.

### 5. SWE-agent / SWE-bench (Princeton, 2024) — the agent–computer interface matters
- **What it is:** SWE-bench is the real-GitHub-issue benchmark; SWE-agent's key finding is that the
  **interface** the agent acts *through* (its custom commands/tools) drives success as much as the
  base model does.
- **The lesson for us:** this **validates** our bespoke tooling — `context_map.py`, `wiring_map.py`,
  `check_architecture.py`, the `check_*` guards, CodeGraph. Investing in agent-facing tooling is not
  overhead; it is the lever. Keep building purpose-built tools; treat a recurring manual step as a
  missing tool.
- **Our status:** STRONG (this is a confirmation, not a gap). Our tooling layer *is* an
  agent–computer interface.
- **Where to check:** the SWE-bench leaderboard (track which interface/scaffold ideas win) +
  SWE-agent releases.

### 6. Production autonomous-SWE loops — OpenHands, Devin (Cognition), Factory
- **What they are:** production systems running plan → code → test → PR → (often) merge-on-green,
  with planning and verification-before-done as first-class stages.
- **The lesson for us:** we **share this loop** — it is not where we are differentiated. Track them
  for the *verification* and *long-horizon planning* patterns specifically (how they confirm a
  change works before declaring done — our `/verify` & `/run` skills are the seam to mature), and
  for merge-gating ideas. Do **not** copy their orchestration wholesale; our memory discipline is
  the part they tend to lack.
- **Our status:** PARITY on the loop; our edge is upstream of it (memory/governance).
- **Where to check:** the OpenHands repo (most open), Cognition (Devin) and Factory engineering
  blogs / changelogs.

### 7. Human engineering-org practice — ADRs, RFCs, DORA, blameless postmortems
- **What it is:** decades of well-run-team process: architecture decision records, RFCs, the DORA
  delivery metrics, blameless postmortems, runbooks.
- **The lesson for us:** our **closest kin is not an AI framework** — it is a disciplined eng org.
  Our `docs/decisions/` (ADRs), the Q-router (decision provenance), `current-state.md` (runbook),
  and the session self-audit are direct analogues. This literature is far deeper than the agent
  field; keep mining it for the *next* governance primitive (e.g. DORA-style metrics on the
  autonomous loop's own delivery — lead time, change-fail rate of routine PRs).
- **Our status:** STRONG and ongoing; the richest vein for new governance ideas.
- **Where to check:** the ADR community (adr.github.io), the DORA / "Accelerate" body of work,
  Google SRE postmortem culture.

---

## Adjacent areas worth a lighter watch

- **LLM-as-judge / evaluator-optimizer patterns** — directly relevant to the **Hermes
  independent-reviewer** seam (`docs/ideas/autonomous-improvement-loop-vision-2026-06-12.md`). Track
  how the field calibrates a "different mind" critic so Hermes's verdicts stay trustworthy.
- **Multi-agent orchestration frameworks** (AutoGen, CrewAI, LangGraph) — mostly *re-implement*
  coordination we already have bespoke; watch for *memory-sharing* and *handoff* primitives only,
  not the orchestration.

---

## How to keep this alive (the re-check loop)

This watchlist is only useful if it is revisited. The cadence is **grooming-driven, not a new
routine** (a new routine would be executable-config the agent must not self-add):

1. **Re-check trigger:** during the end-of-session **grooming sweep** (the standing secondary task,
   `docs/ideas/README.md`), if no idea is more pressing, an agent may pick **one** entry here, check
   its "where to check" source for genuinely new output, and either (a) capture a concrete new idea
   into `docs/ideas/` with a back-link, or (b) note "checked, nothing new" by bumping the entry.
2. **Update the header `Last reviewed:` date** whenever any entry is re-checked.
3. **Keep it lesson-first.** If an entry stops teaching us anything actionable, cut it — a watchlist
   that only grows becomes a survey nobody reads.

> **Proposed (not self-applied):** wiring a periodic watchlist re-check into the **reconciliation
> pass** would make the cadence reliable, but that changes a routine's scope (executable config) —
> so it belongs in the question router as an owner decision, not a self-edit. Captured here as a
> candidate; route it as a Q-block if an agent wants to formalize it.
