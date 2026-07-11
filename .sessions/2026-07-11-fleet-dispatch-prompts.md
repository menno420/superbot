# 2026-07-11 — fleet dispatch prompts (continuation): 8-seat structure → complete paste-and-go startup prompts

> **Status:** `complete`

📊 Model: Opus 4.8 · owner-directed (live dispatch/planning session — turning the 8-seat fleet
restructure into paste-ready startup prompts).

## What this did

Continuation of the 2026-07-11 fleet-management arc (after #2008 landed the superbot-games merges
+ the 8-seat structure doc). This leg turned the structure into **dispatch materials the owner can
paste**:

- **Confirmed the 8-seat structure** with the owner and mapped each of his claude.ai Projects →
  repos + environment + mission (recorded in `docs/owner/fleet-8seat-structure-2026-07-11.md`):
  Project Manager · Venture Lab · SuperBot World · SuperBot 2.0 · Ideas Lab · Game Lab · Self
  Improvement · Websites.
- **Delivered complete, paste-and-go startup prompts** for 5 seats — Project Manager, Self
  Improvement (substrate-kit), SuperBot 2.0 (superbot-next), Venture Lab (merged), SuperBot World
  (merged). Each = the seat's real `coordinator-prompt.md` (loop + pacemaker + failsafe) with the
  gen-3 real-problem fixes **folded in as ONE block**.
- Owner **started Project Manager + Self Improvement**. Remaining to hand over next session:
  **Ideas Lab, Game Lab, Websites**.
- Published/updated the **Fleet Dispatch Pack** artifact (claude.ai) as the owner's copy surface;
  by session end shifted to giving each seat's full prompt + Custom Instructions **inline in chat**
  (owner preference — see learning 1).

## Durable learnings this leg (owner directives — carry these)

1. **ONE complete prompt per seat — never fragmented (owner directive).** Hand over a single
   paste-and-go block, not "base prompt + a rider to bolt on." The real "startup prompt" IS the
   seat's whole `coordinator-prompt.md`; the universal wake prompt is only the pointer version.
   Any real-problem fix is folded INTO the one block, in place.
2. **Use the complete prompts we already had; improve ONLY what caused real problems.** Don't
   re-author mature prompts. The registry's 3-file packages (`instructions.md` + `coordinator-prompt.md`
   + `failsafe-prompt.md` per seat) are the source of truth; start from them verbatim.
3. **The real problems worth fixing = the gen-3 hygiene rider (evidence-based):**
   multi-step trigger-MCP chains in one worker STALL → one trigger call per worker · leaked
   coordinator env into spawned CLIs → `env -u` + smoke gate · warm clone silently drifted 88
   commits → hard-sync `reset --hard` + `git ls-remote` verify · born-red HOLD fires "CI failed"
   webhooks read as real failures → born-red events are NOISE · relayed "owner approved" cleared a
   merge → live-human-only merge auth (already in v2 riders) · companion prompts carried stale
   facts → fact-refresh · the fleet-manager failsafe is bound to an ARCHIVED session → fresh boot
   rebinds-then-deletes.

4. **Routines are AGENT-ARMED — never owner-armed (real failure + a doctrine correction).** Seats
   reported "unable to open/arm them"; my first fix wrongly routed the fallback to an owner-action.
   Corrected against the docs: **agent-armed routines work** (owner-verified 2026-07-10;
   `round3-dispatch-runbook` + the `docs/eap` capability correction retiring the "owner-arms-routines"
   doctrine as *partially invalid*) — the owner CANNOT arm a project's routines. Every coordinator
   prompt gives the exact calls — pacemaker `send_later({message, delay_minutes:15})`, failsafe
   `create_trigger({name,cron_expression,prompt})` + `list_triggers` verify — and, if the
   coordinator's toolset can't arm (seat-inconsistent), **retry from a WORKER** (worker toolsets
   differ; the documented self-arm path) and record the recipe + outcome verbatim. NEVER an
   owner-queue item. Corrected recipe is in the 8-seat structure doc's dispatch guidance.

## Sequencing note for the Project Manager (its first job)
When it canonicalizes the 8-seat registry it must: (a) keep each seat's prompt COMPLETE (one
paste-and-go block); (b) fold the gen-3 rider in place; (c) build the merged seats'
`coordinator-prompt.md` + `failsafe-prompt.md` (Venture Lab, SuperBot World, Ideas Lab, Game Lab)
from the source packages. The complete startup blocks handed to the owner this session are the
paste-now versions; the PM's registry versions become canonical.

## ▶ Next-session brief

**Where we are:** the 8-seat fleet structure is decided + recorded
(`docs/owner/fleet-8seat-structure-2026-07-11.md`). Complete startup prompts delivered for 5 of 8
seats; owner started **Project Manager + Self Improvement**.

**Next actions (in order):**
1. **Hand the owner the last 3 seats' materials — inline, complete, one block each:** Ideas Lab,
   Game Lab, Websites. Each = its Custom Instructions (the merged/existing `instructions.md`) + one
   complete startup `coordinator-prompt.md` with the gen-3 rider folded. Source the real prompts
   from the registry (`fleet-manager/projects/<repo>/`); merged seats (Ideas Lab, Game Lab) are
   composed from their source packages. **Give ONE complete block per seat — do NOT fragment.**
2. **The Project Manager (once running) canonicalizes the 8-seat registry** — its startup order is
   in the 8-seat structure doc; it builds the merged seats' coordinator/failsafe packages.
3. **Owner env-mapping still open:** which repos each of `pinned-research` / `python-lab` /
   `multi-repo` holds — needed to pin the `?` environments in the dispatch pack.

**Open owner items (carried):** venture-lab **#51** (10 accidental personal photos in a public
repo — close or relocate) · mineverse 6 env vars *after* its CSRF fix · project-scoped Railway
tokens (never the account key).

## ⟲ Previous-session review (Q-0102)
The prior leg (#2008, merge continuation) landed the three superbot-games rebases cleanly and
reconciled the handoff — solid. **What it missed:** the dispatch pack it first produced was
*fragmented and re-authored* (condensed my-own-words prompts, a wake-prompt-plus-boot-order split),
which cost **three rounds of owner correction** this leg before landing on "complete prompts from
the registry, only real-problem fixes." **System improvement:** when the owner already has a mature
system (the registry's 3-file prompt packages), the default must be *start from those verbatim and
change only what demonstrably broke* — not compose fresh. That instinct is now written as learnings
1–2 above so the next session doesn't repeat the churn.

## 💡 Session idea (Q-0089)
**A `gen_dispatch_pack.py` in fleet-manager.** A small generator that reads the registry (each
seat's `instructions.md` + `coordinator-prompt.md` + `failsafe-prompt.md`) and emits, per seat, a
single **complete paste-and-go startup block** (coordinator + the gen-3 rider folded) plus its
Custom Instructions — so the owner always gets one canonical, non-fragmented block per seat,
generated from source instead of hand-composed. It directly prevents the fragmentation churn this
session hit, and keeps the pack in sync with the registry automatically. Dedup-checked: the
next-round-kit / dispatch-prompts docs are manual snapshots; this automates them from the canonical
source. (Distinct from `gen_roster.py`, which reports seat *state*, not dispatch prompts.)

## 📊 Model
Opus 4.8 · owner-directed live session · task_class: docs-only (dispatch/planning + close-out).
