# Next-session brief — 2026-07-14 morning: read the night, probe, send email 3

> **Status:** `owner-guidance` — written at the close of the 2026-07-12/13 hub session
> (the doctrine night). The fleet ran unsupervised from ~01:00Z under NIGHT ORDERS v2 +
> the owner's direct orders (fm ORDERs 030–040), with the manager's backup ladder armed
> (R27) and the hub's midnight sweep already landed (6 gba PRs). **Today is the EAP
> window's last day — email 3 goes out today.**

## 1 · The morning read (~10 minutes, in order)

1. **The manager's morning roster** (fleet-manager, ~06:00Z per ORDER 040): per-seat
   tallies, dropped-tick report, backup-ladder record, the **round-trip flag**, v3.5 state,
   the Websites ORDER-041 number. This is the night's one-page verdict.
2. `python3.10 scripts/fleet_status.py` — live heartbeats vs the roster (trust-but-verify).
3. **The open-PR morning sweep** (hub venue, your rule): everything green+READY lands;
   superbot-next's stacked WP lane merges oldest-first once its seat's night stack settles;
   websites' by-design-open pair closes out with its seat.

## 2 · The probe pass → email 3 (before anything else eats the day)

Run **§PROBES** in [`../eap/anthropic-email-3-draft-2026-07-13.md`](../eap/anthropic-email-3-draft-2026-07-13.md)
(7 probes, ~30 min, screenshots marked 📸), fill the draft's brackets from the roster,
rewrite Part 1 in your voice, **send on thread `19f41cd2e5380bb3`**. Optional but
high-value: book Matt Gallivan's 10–15 min interview — the email is the evidence half,
the interview is the concept-fit half.

## 3 · The standing owner surface (unchanged, one sitting)

The ≤07-13 bundle rolled to today: Lumen Drift itch.io go/no-go · pokemon playtest
verdicts · gba concept pick · post-EAP routine posture (rec: Option A) · websites cutover
(rec: Option A) · venture "go with defaults" (releases 3 products) · superbot-next
ruleset/merge-queue click · **makerbench→curious-research follow-ups**: the blueprint's
five workshop projects (a–e) still route as build slices when you want them — say the
word to the manager. Canonical queue: fleet-manager `docs/owner-queue.md`.

## 4 · Curious Research day-one (when you're with your friend)

The repo is live and seeded. His path: README § Start here → the animated PR guide →
the 3-minute first-PR exercise → first question to his Claude. Your prompt pair for the
ninth seat is in [`curious-research-project-prompts-2026-07-13.md`](curious-research-project-prompts-2026-07-13.md)
(paste 1 = instructions, paste 2 = startup) if you want the seat researching before he
arrives.

## 5 · The hub's honest review — projects and struggles so far (Q-0102-grade, from the seat that read everything)

**What's genuinely strong.** (1) *The memory architecture works.* Every lesson tonight
became an artifact (Q-0271…Q-0274, the grounding file, the reading path, two skills) and
the manager folded them into the next prompt generation within hours — the system now
learns faster than it forgets, which is the whole premise paying off. (2) *The seats are
genuinely productive when the posture is right* — the same fleet that stalled on imagined
review gates two nights ago shipped three new games, a curation report, parity write-
goldens, and a seeded ninth repo in one unsupervised night. The bottleneck moved from
"agents waiting" to "owner click bandwidth," which is the correct bottleneck for this
design — and the VENUE:hub + morning-sweep pattern prices it at minutes per day.
(3) *Truth discipline held under pressure*: the manager's pre-commit review caught my five
stale Position lines; sim-lab caught three fabricated external reviews and answered with a
gate, not a ban. The system audits itself, including me.

**Where the struggles genuinely are.** (1) *The platform capability fog is the tax on
everything* — the venue split (seat-denied vs hub-works), allowlists that don't hold,
routines that drop repos or models: none of it is fatal, all of it costs turns and bred
exactly the presence-gating you spent tonight killing. It's a product problem we can only
route around, document, and report (email 3 does). (2) *Records rot in hours at this
velocity* — my grounding-file Positions were stale before commit; the fix (one-sentence
dated Positions + live sweeps) is right, but every doc that duplicates live state is a
future lie; keep pushing state into generated surfaces (roster, fleet_status) and intent
into durable ones. (3) *Quantity needs its quality counterweights watched*: open-PRs-stay-
open + mass production is the right growth posture, but stacked PRs, byte-frozen goldens,
and validity gates are what keep 100 products from being 100 liabilities — the morning
sweep and the authenticity gate are now load-bearing; treat any pressure to skip them as
the first smell of drift. (4) *The human is still the single point of failure for exactly
five click classes* (settings, secrets, publish, spend, portals) — the owner-queue makes
that visible and batchable, but the EAP asks (pre-auth envelope, queryable capabilities)
are the real fix and worth pushing hard while Anthropic is listening.

**One prediction to check in a week:** if the round-trip flag (idea→verdict→routed→built→
merged→surfaced, hands-free) fires regularly, the system is compounding; if it stays rare,
the interlock is still theater and the manager's routing needs teeth. Watch that number
over any single seat's output.

## 6 · Carry-overs and fences

EAP window closes **today** · Railway project consolidation stays FROZEN until after
today (OQ-RAILWAY-PROJECT-SPLIT) · websites review-site URLs unmoved until after today ·
trading grading Friday · T+7/T+14 checkpoints 07-19/07-26 · next superbot recon pass at
PR #2070.
