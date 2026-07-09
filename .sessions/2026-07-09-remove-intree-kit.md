# 2026-07-09 — Remove the in-tree substrate-kit copy (named follow-up chore)

> **Status:** `in-progress`

## What I did

Executed the follow-up chore named in the kit-lab founding plan §4.2
(substrate-kit `docs/planning/kit-lab-founding-plan-2026-07-07.md`: "the
in-tree `substrate-kit/` source dir deletion stays a follow-up superbot
chore"). The kit graduated to **menno420/substrate-kit** (v1.0.0 released;
KL-1 + KL-2 merged there — the graduated repo has evolved past this
snapshot); superbot's pin is `substrate.config.json` (`kit_version: 1.0.0`,
`project_id`, PR #1879).

**⚑ Deletion flag (prominent, per the working agreement):** this PR deletes
**`substrate-kit/`** (in-tree source snapshot: src + dist + pyproject +
README) and **`tests/unit/substrate_kit/`** (the kit's test suite) — 101
files total. Reversible via git history (`git checkout f0f6414 --
substrate-kit/`); the graduated repo supersedes the snapshot. This is the
*named* §4.2 follow-up chore, coordinator-directed, not self-initiated
scope.

**Redundancy verified before deleting:**
- Nothing in superbot imports or runs from `substrate-kit/` or
  `tests/unit/substrate_kit/`: no CI workflow, no `scripts/`, no `tools/`,
  no `.claude/` hook references those paths (grepped py/yml/json/sh/toml
  repo-wide).
- pytest collection after deletion: **13857 tests collected, 0 errors**.
- Remaining textual mentions are historical (planning docs, `.sessions/`,
  router provenance, `current-state.md` narrative) — left as history.

**Living-doc pointers repointed at the graduated repo** (+ pin file):
`docs/AGENT_ORIENTATION.md` (Q-0254 kit-doctrine path),
`docs/current-state/S4-docs.md` (economy-engine path),
`docs/roadmap.md` (OSS-arc entry: graduation note),
`docs/ideas/adopt-kit-stance-classifier-2026-07-07.md`,
`docs/ideas/substrate-kit-auto-drafted-handoff-2026-07-07.md`.

**Owner-gated stale pointers → proposed, not self-edited (Q-0194-rider):**
`.claude/settings.json` lines 47–48 (dead allowlist entries for the deleted
in-tree build/bootstrap paths) and the `.claude/CLAUDE.md` Q-0254 bullet's
`substrate-kit/src/engine/templates/…` parenthetical — both routed as
**router Q-0255 (DISCUSS)** with an apply-as-is recommendation.

**Checks:** `check_quality.py --check-only` ✓ · `check_quality.py --full`
(mypy + full pytest) ✓ · `check_docs.py --strict` ✓ ·
`check_architecture.py --mode strict` ✓ (2 pre-existing WARNs only) ·
`check_current_state_ledger.py --strict` ✓ (benign newest-merge lag only) ·
`check_session_log.py` ✓.

**PR:** #1882 (`claude/remove-intree-kit`), auto-merge armed at open.

## Session enders

💡 **Session idea — `check_kit_pin.py`: make the §9.2 outbound protocol
consumable superbot-side.** Now that the in-tree copy is gone, superbot's
only kit tie is the `substrate.config.json` pin — and nothing ever looks at
it again. A tiny disposable checker (Q-0105 provenance header) that reads
the pin and the graduated repo's `release.json` (the machine end of the
kit's outbound protocol, founding plan §9.2) and prints "newer kit release
vN.N.N exists — upgrade_steps: …" as an advisory would turn the pin from a
dead record into an upgrade signal, and is the natural superbot half of the
#1881 session's "cross-repo pins need drift checks" observation.
Dedup-grepped `docs/ideas/` for `release.json` / `kit_version` /
`check_kit_pin` — no hits.

⟲ **Previous-session review (#1881, kl2-provenance-riders).** Clean,
plan-faithful execution: the eight PL riders landed exactly as §8.3(3)
prescribed, cite-never-copy honored, and the explicit "nothing else is
prescribed superbot-side for KL-2" scoping note is the kind of
negative-space statement that saves the next session a verification pass —
today's session leaned on its sibling note (the §4.2 chore pointer) to
start fast. One improvable: its 💡 idea (PL-rider drift check) named the
**in-tree** `substrate-kit/` copy as the register source "for now" — one
session later that path is gone. Workflow improvement this surfaces:
ideas that reference repo *paths* should prefer the durable home (the
graduated repo / a release URL) over the transient one even when the
transient one is momentarily more convenient — the in-tree copy was already
a named deletion target when that idea was written.

**Documentation audit (Q-0104).** `check_current_state_ledger.py --strict`
green (only benign newest-merge lag past marker #1861 — the next
reconciliation pass records #1882 as a routine merge; no pre-merge ledger
entry needed, same call as #1881). `check_docs.py --strict` green — no
orphaned docs created; the two doc pointers this session touched now
resolve to the graduated repo. Nothing captured only in chat: the deletion
rationale lives in this card + PR #1882's description, the owner-facing
proposal lives in router Q-0255, and the plan-side provenance is
substrate-kit's founding plan §4.2 (unchanged, kit-side).

⚑ Self-initiated: none — coordinator-directed §4.2 follow-up chore. The
deletion itself is flagged above.
