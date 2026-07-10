# Session — round-3 dispatch, part 4d: games relay pasted + manager prompt registry

> **Status:** `complete`
> **Run type:** owner-directed · same live dispatch chat (parts 4/4b/4c: PRs #1957/#1963/#1964, merged)
> **Model/time:** fable-5 · 2026-07-10 ~21:3xZ → ~21:4xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1964) · PR #1965.

## What is about to happen

Owner reported live: the games-mapping relay (with the read-only-data-API input) is
PASTED to the manager, and the manager is preparing a **centralized prompt registry**
(one home for all Custom Instructions / briefs / wake prompts). Record both in the
runbook (the "relay drafted, pending" rows are now stale), add the registry fact +
one-source-of-truth rule to the gen-3 standard §4 fold-back, and commit the
registry-ingest paste block durably (part-4c's review flagged that gating paste blocks
lived only in chat).

## What happened

- **Runbook §3.7 + §4 de-staled:** games relay is now **PASTED (owner-confirmed,
  ~21:3xZ)** — awaiting the manager's ⚑ mapping proposal, which must additionally
  place the **read-only data API** (superbot dashboard-data-contract, PR #1920) that
  both games-web phase 2 and the websites stats/explorer pages are blocked on (the
  input added to the relay at paste time).
- **Prompt-registry fact recorded two places:** runbook §3.7 (state) + gen-3 standard
  §4 (doctrine: registry copy canonical once it exists; founding-package §1/§2 blocks
  → frozen history with superseded-by pointers; edit-registry-first-then-re-paste;
  `vN · YYYY-MM-DD` version stamps so seats can quote their header and drift is
  detectable).
- **New runbook §6 — durable paste blocks:** the prompt-registry ingest inventory
  (5 canonical prompt locations incl. the trigger-registry-only wake prompts, + the
  three registry rules) committed verbatim, delivered to the owner in-chat for the
  manager. Part-4d convention minted: blocks that gate downstream work get committed,
  not chat-only.

## ⚑ Self-initiated

- The §6 durable-paste-block convention (direct remedy of part-4c's ⟲ review finding;
  contained, docs-only).
- The three registry rules in the ingest block (one-writer / version-stamp /
  superseded-by pointers) — decide-and-flag per Q-0240: the manager and owner see them
  in the paste and can veto before ingest.

## 💡 Session idea

**Prompt version stamps** (shipped inside the §6.1 block, flagged here per Q-0089):
every pasted surface — Custom Instructions, wake prompts — carries `vN · YYYY-MM-DD`
as its first line, mirrored in the registry. Pasted text is the fleet's only
*invisible* state; the stamp makes it queryable ("quote your version header") the same
way `capabilities --probe` (part-4c's idea) makes toolsets queryable. Together they
answer the owner's "ask a project what it is and can do" from both sides.

## ⟲ Previous-session review

Part 4c routed the self-awareness ask well (verbatim words in email + idea file) and
its boot verifications were strictly ground-truth. Its miss, remedied this session:
the games-mapping relay block — which gated the next seeding round — existed only in
chat; a lost chat would have re-drafted it from nothing. Improvement (applied): the
runbook now has a §6 home for downstream-gating paste blocks, and this session's
registry-ingest block is its first entry.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ (no new plan doc — edits to
two already-homed plans) · `check_current_state_ledger --strict` ✓ (benign newest-merge
lag only) · chat-only material swept: relay-pasted state → runbook §3.7/§4; registry
fact + rules → gen-3 §4 + runbook §6.1; ingest paste block → committed verbatim.
Claim file deleted this commit.

## Handoff

Owner: paste the **§6.1 ingest block** into the manager chat (it was also delivered
in-chat this turn). Next sweep verifies: the manager's ⚑ games mapping (now must place
the data API) · the registry location flagged in manager status · trading ORDER 008
report · old trading 4-hourly wake deleted · sim-lab INTAKE 003 verdict + first @codex
reply (OA-002 toggle still the open click) · EAP email send before 07-14.
