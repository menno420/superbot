# 2026-07-12 — overnight fleet review (owner "review" word) + trigger-scheduler incident

> **Status:** `complete`

📊 Model: fable-5 · owner-directed (owner asked for the overnight-batch review; suspected cron
problems vs. the 07-10 batch) · `/fleet-review` FLEET mode

## What this did

Full record: **`docs/eap/night-review-2026-07-12.md`** (per-lane digest · incident timeline ·
lessons · fix-first · owner-action queue). Headline findings:

- **The "cron problem" was the platform, not the batch.** Read the full live trigger registry
  (293 records, 4 pages): the CCR scheduler degraded ~02:30–08:00Z — 9 `send_later` one-shots
  silently dropped (stay `enabled` with a past due-time; never back-delivered), 2 crons wedged
  (`next_run_at` frozen: venture-lab failsafe 06:06Z, kit-lab daily 06:08Z "last never"), then a
  partial ~08:0x catch-up revived every seat that had a healthy `*/2` failsafe. The 07-10 batch's
  84/85-fired baseline proves the arming pattern itself is sound — **Q-0265 failsafe doctrine
  validated in production.**
- **Recovery actions:** manually fired the kit-lab loop 08:46Z (fresh-session triggers CAN be
  manually fired) → Self Improvement's daily run started 2.7h late. Cross-session revival of the
  two dark persistent seats (Venture Lab, the failsafe-less SuperBot 2.0 chain) is
  **org-disabled** (`fire/update/create_trigger` on foreign sessions all refused server-side) —
  routed to the owner queue (owner poke / manager `send_message`).
- **Overnight work still shipped:** manager's prompts-v3.2 stateless-artifacts program (fm #108 +
  12 relocation ORDERs merged across 10 repos) · superbot-next band-5 complete · substrate-kit
  ORDER 014 · gba GLOAMLINE slice 5 · first 8-seat staleness sweep. superbot hub itself clean
  (0 open PRs, ledger in sync).
- **Auto-mode prompt question (owner, live):** answered — Auto mode auto-approves built-in tools;
  MCP tools prompt unless allowlisted. Coordinator seats carry per-tool `always_allow` in their
  Routine's `session_context`; plain-started hub sessions don't → unattended hub recovery paths
  can silently stall on a prompt. Allowlist proposal parked in the owner queue (Q-0106 gate).

## Context delta

- **Needed but not pointed to:** fleet-manager keeps a full **`telemetry/triggers-snapshot.json`**
  (783 records) refreshed by a GH-Actions cron — the far cheaper source for trigger forensics
  than paging `list_triggers` through 25k-token MCP overflows. Orientation should route
  trigger/fleet questions there first (and to `docs/roster.md` gen-N).
- **Pointed to but didn't need:** CodeGraph / architecture sections (docs-only review session).
- **Discovered by hand:** the fired-vs-dropped inference rule (`ended_reason=run_once_fired` vs
  `enabled` with past `run_once_at`); the org-policy wall on cross-session trigger ops; the
  born-red code-quality webhook arriving mid-session is indeed pure noise (gen-3 rider held).
- **Decisions made alone:** fired the kit-lab loop 2.7h late rather than losing the day
  (contained; the kit's claim ritual absorbs a rare dupe); did **not** write the trigger-health
  order into fm `control/inbox.md` (inbox is single-writer: the owner) — delivered paste-ready
  text in the owner queue instead.

## 🛠 Friction → guard

Friction: the scheduler drop was discoverable all night (`list_triggers` showed it) but nothing
looks. Guard shipped this session: the detection signature + incident record documented
(`night-review-2026-07-12.md` §4.1), the in-band liveness-sweep idea groomed with the two new
failure classes (build-ready), and a new scheduler-independent watchdog idea filed — the
*enforcing* checker itself belongs in fleet-manager's `gen_roster.py` (cross-repo, manager-owned),
so it ships as the paste-ready fm ORDER in the owner queue rather than a superbot commit.

## Flagged for maintainer (weak points)

- `session_01Xbiuvy…` ↔ SuperBot 2.0 is best-evidence, not confirmed — one session-list glance.
- Venture Lab / kit-lab recovery outcomes unverified at write time; roster gen #14 (~10:40Z) is
  the checkpoint.
- Per-lane PR claims verified via the manager's transport-verified roster + sweep, not by
  re-reading every lane repo.

## 💡 Session idea (Q-0089)

[`scheduler-independent-trigger-watchdog-2026-07-12`](../docs/ideas/scheduler-independent-trigger-watchdog-2026-07-12.md)
— evaluate the trigger snapshot fm's roster-regen Actions cron already fetches (WEDGED / dropped /
dead-chain predicates) from a substrate the CCR scheduler can't take down. Tonight is the direct
evidence: the only oversight that survived the outage was the one riding GitHub's cron. (Filed +
indexed; complement to the groomed in-band sweep idea.)

## ⟲ Previous-session review (Q-0102)

Previous superbot session (44th reconciliation pass, #2014): clean, honest, and its
cross-repo-checker-awareness idea correctly named a recurring class. What it — and every session
so far — lacked: any glance at **trigger health**, despite `list_triggers` being one call away
while the scheduler was already degrading under it (~23:25Z–01:32Z). **System improvement:** make
trigger-health a standing item wherever fleet state is already read (the manager's wake ritual +
the roster generator — the two ideas this session filed/groomed), instead of a thing only a human
suspicion triggers.

## Documentation audit (Q-0104)

Docs-only session. `check_docs --strict` + ledger checker run before push (results in PR CI);
new docs reachable (eap README + ideas README + current-state pointer); owner decisions from this
session: none taken alone that need a router entry (allowlist proposal parked as owner queue item,
not applied — Q-0106). Claim deleted at close.

## 📤 Run report

- **Did:** overnight fleet review — trigger-scheduler incident diagnosed from primary evidence +
  per-seat digest + lessons; kit-lab manually revived · **Outcome:** shipped
- **Shipped:** #2017 — `docs/eap/night-review-2026-07-12.md` + idea file/groom + pointers + card
- **Run type:** `manual` (owner-directed, live)
- **⚑ Owner decisions needed:** allowlist safe CCR MCP subset in hub settings (night-review §6.5,
  Q-0106-gated) — say the word and it ships
- **⚑ Owner manual steps:** poke Venture Lab money-seat session · confirm/poke SuperBot 2.0
  coordinator + arm its failsafe · paste the trigger-health ORDER into Project Manager
  (night-review §6.3) · one-click merges fm #105/#92 · venture-lab #51 photo cleanup (HOT)
- **⚑ Self-initiated:** kit-lab loop manual re-fire (contained recovery, flagged in the
  night-review §1); groomed liveness-sweep idea + filed the watchdog idea
- **↪ Next:** verify recovery at roster gen #14 (~10:40Z); if Venture Lab is still dark, the
  owner poke is the only path (org policy); then normal lanes resume — hub recon next at #2040

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#2017 via auto-merge on green) |
| CI-red rounds | 0 (born-red gate only — by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (scheduler-independent watchdog) |
| Ideas groomed | 1 (trigger-registry liveness sweep → build-ready) |
