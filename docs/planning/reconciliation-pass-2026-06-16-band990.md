# Reconciliation pass — 2026-06-16 · the band-#990 Q-0107 cadence pass

> **Status:** `historical` — superseded by [the band-#1020 pass](reconciliation-pass-2026-06-17-band1020.md),
> which scored this band (#995–#1020) in its §2. The docs-only review + planning pass for the band that crossed
> **#960** (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#930 pass](reconciliation-pass-2026-06-15-band930.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#961**
> (`.github/workflows/reconciliation-trigger.yml`) — the **eighth** consecutive real cadence
> fire of the autonomous issue-trigger, and a live proof the loop self-fires: #961 was authored
> by **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities
> restated · §4 the next ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#994** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#930 pass (band #931–#994):** a fast, broad band. The genuinely-not-yet-
entered PRs at pass start (`check_current_state_ledger --window 60`): the whole **#944–#994 tail**
(27 merges) plus #946/#960 which prior sessions had only *referenced* narratively, never given a
real `Recently shipped` bullet. The headline of the band is the **developer-dashboard / control-API
initiative** (#969/#974/#982/#983/#985/#990/#993 + the Q-0155–Q-0160 owner decisions) — the
"buffer" slot became the band again, the fifth straight time (see the band-#900 §6 promote-the-
recurring-buffer note).

**Ledger reconciled:** the #944–#994 tail entered as **six grouped `Recently shipped` entries**
(docs/architecture maturation · dashboard/control-API · autonomous-loop ops hardening · BTD6 AI
floors+fixes · misc fixes+tooling · routine-hardening); the six oldest live entries
(#912/#917/#918/#920/#924/#926) archived to [`current-state-archive.md`](../current-state-archive.md)
to hold the soft ratchet at 20. `check_current_state_ledger --window 60` green afterward.

**Open PRs at pass time (disposition — Q-0125):**

| PR | What | Disposition |
|---|---|---|
| **#995** | `feat(dashboard): map BTD6/RPS sub-cogs to their parent subsystem` — a `claude/*` session PR opened **today, minutes before this pass**, born-red | **leave open / active parallel session** — in-flight dashboard work, not stale or redundant; auto-merges on green. No action. |
| **#941** | `feat(image-moderation): OpenAI omni-moderation image filter (Q-0108)` — labelled **`needs-hermes-review`** (Q-0117 carve-out: a new subsystem **and** a new external-egress path), born-red `complete` | **leave open / Hermes-review carve-out** — auto-merge deliberately disarmed; not in this reconciler's merge authority. ⚠️ **Now `mergeable_state: dirty` (conflicted)** after the band's churn — flagged for the owner/Hermes to rebase before the review merge, so it does not rot the way #771 did. |

The two `needs-hermes-review` siblings from the prior band — **#929** (security tiers 1+2) and
**#962** (§7.5 paragon) — both **merged** since the band-#930 pass, so the carve-out queue drained
cleanly. The #766/#771 stale/redundant rot class stays clear across the whole #931–#994 band.

**Control-plane state (Q-0135):** `check_loop_health.py` **SKIP** — `gh` unavailable in the
reconciliation sandbox. Fallback read (the documented one): the trigger issue **#961 author is
`menno420`**, the `ROUTINE_PAT` owner → **PAT set, loop self-fires** — consistent with the canonical
[Control-plane state table](../operations/autonomous-routines.md#control-plane-state) (rows 1/2/6 ✅).
No drift; the `current-state.md` Gates bullet is already a **pure pointer** at that table (the
`control-plane-single-source-pointer` idea executed in #943), so there is no second prose home to
drift this pass. Re-confirmed, nothing to re-tick.

## 2. Band scorecard (the band-#930 pass §4 queue, band #931–#994 → reality)

| Slot (from the band-#930 pass §4) | Outcome |
|---|---|
| 1 · the band-#930 pass itself | ✅ (#932) |
| 2 · **Games-economy faucet/sink diagnostic** | ✅ **#937** (`!platform economy` coin-flow read model) |
| 3 · **myprofile PR A** | ✅ **#938** (read-only card) **+ #940** (PR B self-service writes) — lane buildable-complete |
| 4 · **Security tiers 1+2 review + land (#929)** | ✅ **#929 merged** (the Q-0117 review cleared) |
| 5 · **Image moderation (Q-0108)** | 🟡 **in flight #941** (`needs-hermes-review`, now conflicted) |
| 6 · **AI §7 next workflow family** | ✅ **over-delivered** — the entire §7.5 comparison family (#946 tower · #950 difficulty · #955 round-range · #962 paragon) **and** §7.6 roster floors (#975) shipped |
| 7 · **Hermes bug-triage `gh issue create` write (Q-0121)** | 🟡 partial — the `intake` pipeline routed real bugs (BUG-0013/0015), but the sanctioned `gh issue create` write itself is still un-built; carried |
| 8 · **P1-1 absence-guard Layer B** | ❌ → carried (design-for-review + creds) |
| 9 · **BUG-0009 slice 3 — newest-towers ordering** | ❌ → carried (data-gated: `towers.json` has no release-order field) |
| 10 · **Buffer / steered** | the **developer-dashboard / control-API initiative** (#969/#974/#982/#983/#985/#990/#993/#995, Q-0155–Q-0160) + the Hermes/CI ops-hardening band (#952/#959/#965/#966/#968/#971/#976/#978/#981) + the BUG-0013/0014/0015 + deploy-downtime fixes |

**Six of ten planned slots executed (2/3/4/6 fully; 5/7 partial), and slot 6 over-delivered** — the
deterministic BTD6 floor family is now *complete*, closing the whole BUG-0009 "grounded values, wrong
assembly" class for comparisons + rosters. As in the last four bands, the **buffer slot carried the
band's real energy** — this time a wholly new initiative (the developer dashboard). The
`decade-queue-lead-with-the-active-thread` idea (band-#900 §6) is now validated a fifth time; §4
below leads with the dashboard thread accordingly.

## 3. Priorities restated (what the next band is for)

**The AI deterministic-floor family is COMPLETE, the safety-community lane has landed, myprofile is
buildable-complete, and the P0/P1-1-offline/P1-2/P1-3 spine is done.** The buildable-now `ready`
queue is genuinely thin *outside* the dashboard. The next band is therefore weighted toward:

1. **The developer-dashboard / control-API initiative — the active owner thread.** Read-only
   surfaces all shipped (#982/#983/#985 + the #993 control-API write side + #990 export-drift guard);
   the next slices are the **owner-approved live help/panel editor (Q-0156)** and Phase 2/4 (auth ·
   public bug form · control board) — **owner/creds-gated** on the auth method + DB decision in
   [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md) /
   [`developer-dashboard-plan.md`](developer-dashboard-plan.md). #995 (sub-cog→subsystem mapping) is
   in flight.
2. **AI §7 beyond comparison/rosters** — the next orchestration workflow family (plan-first), now
   that the deterministic floors are done.
3. **Hermes bug-triage `gh issue create` write (Q-0121)** — the autonomous-loop maturation slice;
   design the write scope first (the Q-0117 pattern).
4. **The safety/community remainder** — image moderation (#941) lands once Hermes reviews + the
   conflict is resolved; the **moderation-DM config** (Q-0147 sibling, off-by-default per-action
   warn/timeout/kick DMs through the audited `moderation_service` seam) is a clean `ready` slice that
   needs a small plan.
5. **The gated P1 remainder** — absence-guard **Layer B** (design-for-review + creds) and the
   **live-quality eval battery** (prod creds). Both stay `creds`/`plan`.
6. **Owner-led in parallel:** mining V-16 phase-2 PNG pack · BTD6 decode ⭐ item 3 · `!uxlab` walk ·
   the substrate-kit (owner-action since the band-#900 demotion).

## 4. The next ~9 slices (planned after #994)

> Modular but not over-segmented (Q-0107): each slot is a real slice. The `#` column is
> **slot sequence, NOT reserved PR numbers** (GitHub assigns numbers globally across parallel work
> **and issues** — Q-0142; do not read this as a "#995–#1020" schedule). Pick the next slice by its
> **description**, verified against the live ledger. Gate-state tags: `ready` · `creds` · `owner` ·
> `plan-first` · `data`. Owner steers override freely.

| # | PR (one session each) | Gate-state | Scope anchor |
|---|---|---|---|
| 1 | **This pass** — reconcile (#944–#994) + plan + open-PR disposition + the Q-0161 permission fix | — | Q-0107 (issue #961) |
| 2 | **Dashboard — live help/panel editor (Q-0156)** first buildable slice | `owner`/`creds` | [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md) L0–L3; the control-API write side (#993) is the foundation — pick the next slice the auth/DB decision unblocks |
| 3 | **Dashboard — sub-cog→subsystem mapping** (#995 lands) + the next read/grouping slice | `ready` | in-flight #995; continue the dashboard read surfaces |
| 4 | **AI §7 next workflow family** (post-comparison/rosters) | `plan-first` | the AI orchestration §7 families beyond the now-complete deterministic floors; plan-level |
| 5 | **Moderation-DM config (Q-0147 sibling)** | `ready`/`plan-first` | `moderation_dm_enabled` master + per-action map on `!settings` → Moderation, through the audited `moderation_service` seam (off by default, fail-open) — owner-decided policy, needs a small plan |
| 6 | **Image moderation (#941) lands** | `owner`/review | resolve the conflict + finish the Q-0117 Hermes review |
| 7 | **Hermes bug-triage `gh issue create` write (Q-0121)** | `plan-first` | the autonomous-loop maturation slice — let the caretaker open a bug-book-backed issue; design the write scope first |
| 8 | **P1-1 — absence-guard Layer B** (negative-existential gate) | `creds` / design-for-review | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md) §4.3 crux; needs the design review + prod-like creds |
| 9 | **BUG-0009 slice 3 — newest-towers ordering** | `data` | needs sourced release-order data (ADR-006 / `!btd6ops seed-data` provenance lane); then one builder appended to `deterministic_btd6_list_reply` |
| 10 | **Buffer / steered slot** — owner-steered dashboard / product (mining V-16 phase-2 PNG pack / BTD6 decode ⭐ item 3) or autonomous-loop maturation | `owner` | in-flight / owner-led |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler
build (Q-0112 — own AI-cost design first) · P1-4 owner live-walks · the live-quality eval battery
(prod creds) · the substrate-kit (owner-action since the band-#900 demotion) · the Honcho per-user AI
memory evaluation (AI-lane, owner "look into soon").

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** The #944–#994 tail (27 merges + the under-entered #946/#960) added as **six
  grouped `Recently shipped` entries**; the six oldest live entries (#912/#917/#918/#920/#924/#926)
  archived to hold the soft ratchet at 20. `check_current_state_ledger --window 60` green.
- **Permission-brake fix (the headline workflow fix this pass — Q-0161).** This routine **stalled
  twice** on permission prompts mid-run: each was a compound Bash command that did file surgery via a
  temp script and cleaned it up with `rm`, and the blanket `Bash(rm *)` safety brake (Q-0149) forced
  a prompt an unattended routine can't answer. Owner-directed in-session: **narrowed the `rm` brake to
  recursive deletes only** (`rm -rf`-class still prompts; a non-recursive scratch-file cleanup no
  longer does) + added `/tmp` + non-recursive-`rm` allow entries. Provenance: **Q-0161**;
  `.session-journal.md` records the behavioral complement (prefer Edit/Write over a temp
  `python3.10 _scratch.py && rm` dance; scratch scripts go under `/tmp/`). This pass dogfooded it —
  the ledger surgery ran via a **self-deleting** `scripts/_recon_tmp.py` (no `rm`, no stall).
- **[reconciliation-pass-2026-06-15-band930.md](reconciliation-pass-2026-06-15-band930.md) re-badged
  `historical`** — its band (#931–#994) is fully scored in §2 above.
- **`docs/current-state.md` ▶ pointers re-pointed** at *this* doc (by name/date, no PR-number range —
  the band-#800 §6 discipline); the live ▶ NEXT moved to the developer-dashboard / control-API thread
  (the now-active owner initiative).
- **`docs/roadmap.md`** — the live-decade-queue pointer re-pointed from the band-#930 pass to this
  pass; band-#930 marked fully executed, the dashboard initiative flagged the active thread.
- **Open-PR disposition (Q-0125):** #995 (active parallel) + #941 (Hermes-review carve-out, now
  conflicted — flagged) recorded in §1.
- **Marker reset** — `Last reconciliation pass` → **#994**; `check_reconciliation_due.py` next fires
  at #1020.
- **No new runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; **BUG-0009**
  (slice 3 data-gated) / **BUG-0011** (Hermes gateway crash-loop) stay OPEN.

## 6. The system improvement this pass made (the point of the loop)

**This pass hardened the loop against the exact failure that nearly broke it: a routine silently
stalling on a permission prompt with no human to click "Allow."** Q-0149 widened the allow-list but
deliberately kept *all* `rm` on the `ask` brake; this pass found that blanket-`rm` brake guarantees a
stall on the most ordinary routine action — cleaning up a scratch file — and narrowed it to the
genuinely dangerous recursive case (Q-0161). The deeper, durable lesson (recorded in the journal) is
**behavioral**: a docs routine should do file surgery with the Edit/Write tools, not shell out to a
temp-script-plus-`rm` dance — the tools are always allowed and have no Bash brake. The generalized
principle for the next pass: **every command an unattended routine issues should resolve to `allow`,
never `ask`** — the `ask` list is for commands a routine genuinely must not run unattended (prod / DB
/ force-history / external-publish), and anything else on it is a latent stall. A small follow-up idea
(this pass's Q-0089 contribution) proposes a `scripts/check_routine_permission_surface.py` lint that
flags routine-common commands that would hit the `ask` brake, so this class is caught before it
stalls a run rather than after.
