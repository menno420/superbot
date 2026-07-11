# 2026-07-11 — Email #2: owner's Part 1 landed + agents' Part 2 fact-refresh

> **Status:** `complete`

📊 Model: Fable 5 · owner-directed hub session (EAP email) · afternoon · PR #1992

## What happened

The owner rewrote Part 1 of the second Anthropic email in his own voice (in chat) and
asked for a full review including the agents' Part 2. This session:

1. **Committed his Part 1 verbatim** into `docs/eap/anthropic-email-2-draft-2026-07-11.md`
   (the owner-edits-only marker is respected byte-for-byte — typo list returned in chat
   for HIM to apply, or on his one-word grant).
2. **Part 2 fact-refresh + strengthening** (full log in the draft's Working notes):
   superbot-next 30→33/49 parity subsystems (212/212 goldens); kit v1.10.1→v1.11.0
   (six releases in ~48h); finding b1 gained the positive-side classifier confirmation
   (games #34/#36/#46/#47 merged first-try under live in-chat authorization) and the
   content-provenance denial (plugin-hello seed push) — the "live human context IS the
   permission" line is now evidenced from both sides; (c) gained the owner-vocabulary
   bullet (Part 1's "one word = full job" built by hand); (e) enriched with
   idle/trading/sim/idea-engine concrete numbers.
3. **Friction → guard:** `/session-close` SKILL.md now names the telemetry-row
   requirement (the Q-0194 gate that held PR #1990 red at its flip).

## ⚑ Self-initiated

- The session-close skill telemetry line (checker existed; the skill's checklist was
  the gap — docs-tier guard, free to ship).
- Part 2 edits beyond pure fact-refresh (the b1 both-sides paragraph, the (c) vocab
  bullet) — flagged; owner may cut when tightening.

## 💡 Session idea

**Owner-text block guard (`check_owner_blocks.py`):** a convention + checker pair —
text between `OWNER-TEXT START/END` markers in any doc fails CI if modified by an
agent-authored commit (committer != owner). Today's email drama worked on trust ("edits
only above this line"); a marker the gate enforces makes owner-voice text structurally
safe to co-edit around, exactly like the session-card gate made partial merges
structurally impossible. (Dedup-checked `docs/ideas/`: nothing covers owner-provenance
text protection.)

## ⟲ Previous-session review (Q-0102)

The fleet-overview session (same day, earlier) delivered a lot in one arc — but it
tripped the telemetry gate at its flip (CI red on what should have been the clean final
push) and, notably, its own close-out narrative said "everything's committed and green"
*before* the gate result came back. Improvement applied this session: the skill now
names the requirement (see above). Honest residue: the improvement is a checklist line,
not an enforcing guard — the enforcing guard already exists (the gate itself); what was
missing was only discoverability, which is the right tier.

## Grooming (Q-0015)

Groomed by execution: the "generalize the review verb" idea shipped this morning got its
first real exercise — this session ran as DOC-mode review (claims verified against the
committed file + today's survey data before editing). No separate `docs/ideas/` item
moved; capacity went to the owner-directed email work.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · ledger in sync (this PR is benign newest-merge lag) · the
Part 1 typo list intentionally lives in chat only (it is feedback ON owner text, not
durable doctrine; the Working notes point at it) · telemetry row appended this PR ·
claim file deleted at close.
