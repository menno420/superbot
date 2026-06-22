# 2026-06-22 — Server treasury (collective coin pool)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (the maintainer picked "treasury" from two offered words and said "build some
> things… do what you want") → built end-to-end (Q-0191 merge-immediately).
> PR #1334 → auto-merge armed; merges on green CI (Q-0123/Q-0127).

## Context (how this session arose)

A reflective conversation about the one-word→feature workflow (idle farm, then "karma"). The
maintainer, going to sleep, gave an open mandate: **document a couple of ideas, capture anything
from the conversation worth keeping, and build something — leaning `treasury`** (a word I'd offered
earlier as "a genuinely-new foundation: the bot's economy is entirely individual; there's no
collective pool"). Three deliverables this session: the treasury build, two idea/insight docs, and
the session-close notes.

## What shipped — the treasury subsystem

The bot's first **server-owned** (collective) coin pool. Every prior balance is individual
(per-user `xp.coins`); the treasury is the seam between the **economy** (where coins come from) and
**governance** (who may spend them). Decomposition mirrors the farm/fishing arc exactly:

- **migration 092** + **`utils/db/treasury.py`** — the `guild_treasury(guild_id, balance, updated_at)`
  row; conn-aware `get_treasury` / `credit_treasury` / `try_debit_treasury` (the conditional
  `balance >= $` debit mirrors `try_debit_coins` — never overdraws, no read-then-write race).
- **`services/treasury_service.py`** — the audited write boundary (RS02/Q-0071): `contribute`
  (member donates own coins → pool) and `disburse` (manager grants pool → member). Each runs the
  pool leg + the user coin leg inside ONE `db.transaction()`; user legs go through
  `economy_service.{debit,credit}_in_txn` so `economy_audit_log` is the money trail (the farm/fishing
  precedent — no separate `emit_audit_action` for the economy domain). EventBus emit after commit.
  Underfunded pool / insufficient funds write nothing and return a typed failure.
- **`views/treasury/`** — `TreasuryView` (HubView): **➕ Contribute** opens a one-field modal
  (button→modal→`edit_message`, the profile-editor idiom) · **🔄 Refresh**. Disburse is deliberately
  **not** a button — only the `manage_guild` command can move coins *out*, so a member's panel can
  only ever move their *own* coins *in*.
- **`cogs/treasury_cog.py`** — `!treasury`/`bank`/`pool` (group → panel), `!treasury contribute
  <amount>`, `!treasury grant @member <amount>` (`@commands.has_permissions(manage_guild=True)`),
  and the Help hook.
- Wiring: `SUBSYSTEMS["treasury"]` (Economy-hub child) · `hub_registry` economy `primary_children`
  · `INITIAL_EXTENSIONS` · `extension_roles.yaml` overlay · the back-button allowlist (root panel,
  parent attaches back externally — the counting/fishing precedent).

**Authority safety:** the service does no permission check by design (so a missing gate can never
silently mint coins); the cog gates `grant` on `manage_guild`. Disburse can never overdraw the pool
(conditional debit). 6 service tests pin transaction membership + the underfunded/insufficient
rollback paths (`tests/unit/services/test_treasury_service.py`).

## Verification

- Full suite: **11795 passed** pre-regen, with 10 generated-artifact freshness failures → all
  resolved by regenerating the pinned artifacts (below); the 4 artifact test files re-run **66
  passed**.
- Regenerated committed artifacts (adding a cog/subsystem shifts their live counts):
  `extension-taxonomy-crosswalk.md`, `dashboard.json`, `site.json` + `data.js`, `env-vars.md`.
- `check_quality.py --check-only` → black/isort/ruff/check_docs/check_consistency/tool-pins ✓ ·
  `mypy disbot/` → 0 errors · `check_architecture.py --mode strict` → 0 errors.
- Doc-audit (Q-0104): surface-map counts (39 subsystems / 52 extensions / 38-of-52 hooks) updated
  to match live registries; help-surface-map + discoverability + roster tests green.
- Not live-verified in Discord (no sandbox bot run); the money paths are unit-covered and the panel
  is CI-asserted discoverable/actionable. Live-verify + the first real `!treasury contribute` is the
  maintainer's (Q-0193: the merge auto-deploys; no manual restart).

## Enders

- **💡 Session idea (Q-0089):** **AI self-curated memory notebook** — give the bot's in-product AI a
  narrow audited write-back seam (correction/AI-judged/daily-cron triggers → a `pending` staging
  table → human-reviewed promotion into instruction / cached layer / **deterministic answer preset**,
  zero-API). The in-product mirror of the agent network's two-part curated memory. *This is the
  maintainer's own idea from the conversation, captured at his request* —
  [`docs/ideas/ai-self-curated-memory-notebook-2026-06-22.md`](../docs/ideas/ai-self-curated-memory-notebook-2026-06-22.md).
- **Conversation insight captured (owner-invited "store what's worth keeping"):** added
  `collaboration-model.md` § "Why the written record *is* the agent's memory (the two-part model)" —
  the extended-mind framing (the journal/`.sessions` artifacts *are* the agent's memory, not a
  substitute) and the maintainer-carries-unfiltered / agent-carries-curated division of labor. It
  reframes session-close curation as the highest-leverage act, grounding why the Q-0089/0102/0104
  enders are mandatory.
- **⟲ Previous-session review (Q-0102):** the idle-farm session (#1328) was exemplary — clean
  fishing-mirror decomposition, and it *proactively* fixed the Games-hub 6th-activity row overflow it
  would have hit. One thing it left for a follow-up that treasury inherits: **neither idle/economy
  subsystem live-verifies in Discord** (both note "not live-verified"). The recurring gap is that
  there's no lightweight headless harness to drive a cog's command path without a real bot+Postgres.
  *System improvement surfaced:* a `tools/sim/`-style **panel/command smoke harness** (instantiate a
  cog with a fake ctx + in-memory db doubles, assert the embed/flow) would let economy/game sessions
  claim more than "unit-covered" without a sandbox — captured as a candidate, not built this session.
- **Context delta:** orientation pointed me straight at the farm subsystem as the template (CLAUDE.md
  "newest complete game" instinct) — that carried 90% of the build. What I had to discover by hand:
  the *full* registration surface a new economy subsystem must touch to stay CI-green — not just
  `SUBSYSTEMS` + `hub_registry`, but the **four pinned generated artifacts** (crosswalk, dashboard,
  site, env-vars), the `extension_roles.yaml` overlay, the help-surface-map **counts** (3 numbers),
  the back-button allowlist, and a hub-children **tuple assertion** in `test_hub_registry`. That
  checklist is scattered; the `new-subsystem` skill / a "new economy child" recipe could enumerate it.
- **⚑ Self-initiated:** none beyond owner latitude — treasury was owner-chosen; the idea capture and
  the collaboration-model insight were owner-requested ("document these ideas", "store what's
  worth keeping"). The *depth* (full subsystem vs. a thinner slice) and the artifact/overlay/doc
  bookkeeping were my judgment within "do what you want… build some things."
