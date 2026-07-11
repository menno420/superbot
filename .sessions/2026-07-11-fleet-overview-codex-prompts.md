# 2026-07-11 — Fleet overview: Codex prompts · PR hygiene · owner queue · product catalog · review-skill generalization

> **Status:** `in-progress`

📊 Model: Fable 5 · owner-directed hub session (fleet management) · day · PR #1990

## What happened (all owner-directed in-chat, 2026-07-11)

1. **4 Codex review prompts shipped** — `docs/owner/codex-review-prompts-2026-07-11.md`:
   superbot-next (5/5), venture-lab (5/5), superbot-mineverse (4/5), substrate-kit (4/5),
   exposure-weighted picks from a 3-agent full-fleet survey; pokemon excluded (private/
   Nintendo), trading (parked program), games (internal-only).
2. **Fleet PR hygiene DONE** — full-fleet open-PR census (16 repos): only superbot-games
   had a backlog (7 green PRs parked behind the classifier wall). **Merged 4** in the
   lane's own order — #34 (`5147a23`), #36 (`325c567`), #46 (`82084aa`), #47 (`201f8dd`) —
   under the owner's live in-chat merge authorization. #38/#32/#27 have real conflicts;
   left for the games lane's queued rebase wake. Everything else: zero open PRs or
   deliberately-live (kit #181 owner-ratification park, kit #207 in-flight born-red,
   fm #47 owner-gated permissions re-land vehicle). Nothing stale to close anywhere.
3. **Owner-queue distilled + stale items caught** — the "only you" list (7 groups,
   priority-ordered) now lives at the tail of `docs/owner/product-catalog.md`; canonical
   queue remains fleet-manager `docs/owner-queue.md`. Stale finds: superbot-next
   OWNER-ACTION 2 asks to *create* `superbot-plugin-hello` (it exists, empty since
   2026-07-10); the prior handoff said pokemon#8 was open awaiting playtest (it merged
   2026-07-10T06:54Z).
4. **Product catalog shipped** — `docs/owner/product-catalog.md`: 18 products in plain
   language (what/who/how-to-use/owner-only steps), from the $49 membership kit to the
   playable GBA game to the fleet-manager itself.
5. **`review` generalized (owner-directed)** — `.claude/skills/fleet-review/SKILL.md`
   rewritten as an object dispatcher (fleet/repo/doc/prompt/PR/diff);
   `docs/owner/fleet-vocab.md` revised to the **verb + object** pattern and grew
   **explain / queue / clean** rows so common operations behave consistently across
   sessions.
6. **Attempted for the owner, classifier-stopped:** seeding `superbot-plugin-hello` from
   superbot-next `examples/` (retires fm owner-queue item 14 residue + idle PLUG-001).
   Auto-mode classifier denied the cross-repo default-branch push pending live owner
   review — respected as terminal; now a one-word owner item ("push the plugin seed").

## ⚑ Self-initiated / decided-and-flagged (Q-0240 — veto anytime)

- Merged games #34/#36/#46/#47 (owner-authorized in-chat; CI green on every head).
- gba Track B concept: adopt the standing recommendation (keep deepening/releasing
  Lumen Drift — already the lane's running default).
- pokemon concept ask is redundant: QoL+ already ruled (Q-0262.7) — lane should retire
  its OWNER-ACTION 2.
- Codex target selection + the exclusion rationale.
- Vocab grew 3 new verbs (explain/queue/clean) beyond the directed review change —
  same pattern, owner may prune.

## 💡 Session idea

**`verify_owner_queue.py` (fleet-manager): an owner-queue auto-verifier.** Parse the
six-field items, probe each WHY/VERIFIED-WHEN condition against live GitHub (repo
exists? PR merged? check required? release published?) each manager wake, and flag
already-satisfied items for retirement. Grounded in today's two catches — a
"create this repo" ask for a repo that exists, and a handoff carrying a
"PR open awaiting playtest" for a PR merged a day earlier. The queue is the owner's
interface; stale asks are the most expensive doc drift the fleet has. (Dedup: distinct
from the roster freshness ladder — that verifies lanes, this verifies *asks*.)

## ⟲ Previous-session review (Q-0102)

The email+handoff session's "NEXT SESSION — START HERE" block worked exactly as
designed — this session oriented in minutes with zero re-derivation; that pattern
should stay. Two misses: it restated pokemon#8 as "deliberately open" without
re-verifying (it had merged the prior morning), and it didn't surface the 7-PR
superbot-games merge backlog even though the parked-green state was a day old.
**Workflow improvement:** handoff briefs must re-verify any "PR is open/blocked" claim
at write time (one `list_pull_requests` per named PR) — and the new fleet-vocab
**clean** verb now gives the owner a one-word way to trigger exactly today's hygiene
pass, so backlogs like games' don't wait for a bespoke session.

## Grooming (Q-0015)

Moved last session's "owner shorthand" idea a full step: from the single-purpose
fleet-review skill to the generalized verb+object dispatcher + 3 new vocab verbs
(owner-directed main task, but it *is* the lifecycle step that idea needed).

## Documentation audit (Q-0104)

`check_docs --strict` ✓ (5 pre-existing soft supersede warnings, untouched by this
session). Ledger in sync at boot; this PR (#1990) enters the ledger at the next
reconciliation pass (benign newest-merge lag). New docs reachable from this card +
each other. Owner-directed vocab/skill change carries its provenance in both files'
headers (owner-guidance zone — no CLAUDE.md edit was needed; the shorthand pointer
there already covers the vocab file). Claim file deleted at close. Nothing chat-only
left un-homed: the games-merge SHAs, the classifier denial, and the stale-ask finds
are all recorded above; the owner overview lives in `docs/owner/product-catalog.md`.
