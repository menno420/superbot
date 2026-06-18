# Reconciliation pass — 2026-06-17 · the band-#1020 Q-0107 cadence pass

> **Status:** `historical` — superseded by [the band-#1050 pass](reconciliation-pass-2026-06-18-band1050.md)
> (2026-06-18). The docs-only review + planning pass for the band that crossed **#1020**
> (cadence = every **30th** merged PR per Q-0134; previous cadence pass
> [the band-#990 pass](reconciliation-pass-2026-06-16-band990.md), now `historical`).
> Triggered by the auto-opened `reconcile` issue **#1021**
> (`.github/workflows/reconciliation-trigger.yml`) — the **ninth** consecutive real cadence fire of
> the autonomous issue-trigger, and a live proof the loop self-fires: #1021 was authored by
> **`menno420`** (the `ROUTINE_PAT` owner), not `github-actions[bot]`.
> Sections: §1 verified state + open-PR disposition · §2 band scorecard · §3 priorities restated ·
> §4 the next ~9 PRs · §5 pruned/fixed · §6 the system improvement this pass made.
> Reset target: marker → **#1020** (latest merged at pass time).

---

## 1. Verified state at this pass (against live GitHub + git log)

**Merged since the band-#990 pass (band #995–#1020):** a fast, broad band again. The headline is the
**developer-dashboard / control-API initiative** maturing from read surfaces into a hardened,
live read+write panel — **#996** (Discord-OAuth login + live editors), **#1013** (Phase E control-API
read endpoints + the see-then-change editor), **#1014** (R3 — CSRF + rate-limiting hardening),
**#1015** (Phase C read workspace) — plus the **command/panel manifest spine** (**#1018** typed
`CommandManifest`, **#1019** `PanelManifest`, **#1020** control-API manifest read + cross-manifest
reconciliation + drift guard), the **settings global tier** (**#1017**, per-guild → global → default),
and the **AI deterministic-floor night queue** running fully to completion (**#1008**–**#1012** —
power/relic/hero-ability/MK-category/bloon-modifier/boss-immunity floors, the §7.5/§7.6 lane).

**Ledger reconciled:** at pass start, `check_current_state_ledger --window 60` + a per-PR grep of the
#995–#1020 band found **five genuinely-missing** entries — #1016 + #1014 (the dashboard R3/vision
tail) and #1004 + #1003 + #997 (the loop-hygiene band: union-merge ledger fix, ideas grooming, the
night-queue seed). Entered as **two grouped `Recently shipped` entries**; the **13 oldest live
entries** (#956, #955, #950, the #947 group, #942, #940, #939, #938, #936, #935, #934, #933, the #928
group) trimmed to [`current-state-archive.md`](../current-state-archive.md) to bring the soft ratchet
from 31 back to **20**. `check_current_state_ledger --window 60` green afterward. (#999 — the
band-#990 pass PR itself — is exempt from the guard as a reconciliation PR and is recorded as the
`Last reconciliation pass` marker.)

**Open PRs at pass time (disposition — Q-0125):**

| PR | What | Disposition |
|---|---|---|
| **#941** | `feat(image-moderation): OpenAI omni-moderation image filter (Q-0108)` — `needs-hermes-review` (Q-0117 carve-out: new subsystem **and** a new external-egress path), born-red `complete` | **leave open / Hermes-review carve-out** — auto-merge deliberately disarmed; not in this reconciler's merge authority. Awaiting a human review-merge (last touched 2026-06-16). |
| **#929** | `feat(security): tiers 1+2 — raid detection + account-age filter (Q-0111)` — `needs-hermes-review` carve-out, born-red `complete` | **leave open / Hermes-review carve-out** — same posture; awaiting a human review-merge. |

Both open PRs are the standing `needs-hermes-review` siblings (Q-0117); neither is stale-redundant
nor red-for-a-fixable-reason, so both are correctly left for the owner/Hermes. No PR closed this pass.

## 2. Band scorecard (the band-#990 pass §4 queue, band #995–#1020 → reality)

| Slot (from the band-#990 §4 queue) | Outcome |
|---|---|
| 1 · This-pass recon (band-#990) | ✅ #999 |
| 2 · Dashboard live help/panel editor (owner/creds) | ✅ over-delivered — #996 OAuth login + editors · #1013 Phase E read endpoints + see-then-change editor · #1014 R3 hardening |
| 3 · Dashboard sub-cog→subsystem mapping + read surfaces | ✅ #995 (mapping) · #1015 Phase C read workspace |
| 4 · AI §7 next workflow family (plan-first) | ✅ the night-queue floors #1008–#1012 completed the §7.5/§7.6 deterministic-floor lane |
| 5 · **Moderation-DM config (Q-0147 sibling)** | ❌ not built — **promoted to a complete plan this pass** ([moderation-dm-config-plan](moderation-dm-config-plan-2026-06-17.md)); now the next ungated ▶ slice |
| 6 · Image moderation (#941) lands | ⏳ still open (Hermes-review carve-out) |
| 7 · Hermes bug-triage `gh issue create` write (Q-0121) | ❌ not built (plan-first) |
| 8 · P1-1 absence-guard Layer B | ❌ not built (creds / design-for-review) |
| 9 · BUG-0009 slice 3 newest-towers | ❌ not built (data-gated) |
| 10 · Buffer / steered | ✅ **became the band again** — the command/panel **manifest spine** (#1018/#1019/#1020) + the **settings global tier** (#1017) |

**Four of ten planned slots executed (2/3/4 fully), and the buffer over-delivered into the band's
structural headline** — the manifest spine + settings global tier. **This is the sixth straight band
where the owner-steered buffer slot *became* the band** (dashboard/manifest), confirming the
band-#900 §6 "promote the recurring buffer" note: the dashboard/control-API initiative is the
project's dominant active thread, not a side lane. Slots 5/7/8/9 stayed unbuilt because they are
gated (creds/data/review) or — slot 5 — needed a plan, which this pass wrote.

## 3. Priorities restated (what the next band is for)

**The buildable-now ungated `ready` queue is genuinely thin.** The AI deterministic-floor family is
complete; the dashboard read+write surfaces are live + hardened; myprofile is buildable-complete; the
P0/P1-1-offline/P1-2/P1-3 spine is done. What remains buildable is either owner-paced (the dashboard
manifest-spine PR4 write side), gated (P1-1 Layer B creds, BUG-0009 data, image-mod/security Hermes
review), or needed a plan (moderation-DM config — now written). The next band is therefore weighted
toward:

1. **Moderation-DM config (Q-0147 sibling) — the now-plan-backed ungated `ready` slice.** Per-action
   moderation DMs on the existing `moderation_service` seam, off by default; the
   [moderation-dm-config-plan](moderation-dm-config-plan-2026-06-17.md) is turn-key. **This is the
   next empty-fire ▶ Next action.**
2. **The developer-dashboard / control-API initiative — the dominant owner thread.** The manifest
   spine PR4 (panel-layout editor + declared button→command binding + DB-backed layout overlay) is
   **owner-paced** (a control-API *write* surface needing `CONTROL_API_TOKEN`, and architecturally
   significant); plan it *with* the owner on the write-side pacing.
3. **AI §7 beyond comparison/rosters** — a *new* orchestration workflow family (plan-first), now that
   the deterministic floors are done.
4. **Hermes bug-triage `gh issue create` write (Q-0121)** — the autonomous-loop maturation slice;
   design the write scope first (the Q-0117 pattern).
5. **The gated P1 remainder** — absence-guard **Layer B** (design-for-review + creds) and the
   **live-quality eval battery** (prod creds). Both stay `creds`/`plan`.
6. **Owner-led in parallel:** image-mod #941 + security #929 land once Hermes reviews · mining V-16
   phase-2 PNG pack · BTD6 decode ⭐ item 3 · the substrate-kit (owner-action since band-#900).

## 4. The next ~9 slices (planned after #1020)

> Modular but not over-segmented (Q-0107): each slot is a real slice. The `#` column is **slot
> sequence, NOT reserved PR numbers** (GitHub assigns numbers globally across parallel work **and**
> issues — Q-0142; do not read this as a "#1021–#1050" schedule). Pick the next slice by its
> **description**, verified against the live ledger. Gate-state tags: `ready` · `creds` · `owner` ·
> `plan-first` · `data`. Owner steers override freely.

| # | PR (one session each) | Gate-state | Scope anchor |
|---|---|---|---|
| 1 | **This pass** — reconcile (#995–#1020) + plan + open-PR disposition + the moderation-DM idea→plan promotion + bookkeeping-wall prune | — | Q-0107 (issue #1021) |
| 2 | **Moderation-DM config (Q-0147 sibling)** — per-action moderation DMs | `ready` | [moderation-dm-config-plan](moderation-dm-config-plan-2026-06-17.md) — turn-key, extends `ModerationPolicy.dm_on_action` + `dm_actions`, no migration |
| 3 | **Dashboard — manifest spine PR4** (panel-layout editor) | `owner`/`creds` | [manifest-spine-execution-plan](manifest-spine-execution-plan-2026-06-17.md) PR4; control-API *write* surface — plan with the owner on write-side pacing |
| 4 | **AI §7 next workflow family** (post comparison/rosters) | `plan-first` | the AI orchestration §7 families beyond the now-complete deterministic floors; plan-level |
| 5 | **Image moderation (#941) lands** | `owner`/review | finish the Q-0117 Hermes review (resolve any conflict first) |
| 6 | **Security tiers 1+2 (#929) lands** | `owner`/review | finish the Q-0117 Hermes review |
| 7 | **Hermes bug-triage `gh issue create` write (Q-0121)** | `plan-first` | the autonomous-loop maturation slice — let the caretaker open a bug-book-backed issue; design the write scope first |
| 8 | **P1-1 — absence-guard Layer B** (negative-existential gate) | `creds` / design-for-review | [hardening §P1-1](production-readiness/hardening-roadmap-2026-06-12.md) §4.3 crux; needs the design review + prod-like creds |
| 9 | **BUG-0009 slice 3 — newest-towers ordering** | `data` | needs sourced release-order data (ADR-006 / `!btd6ops seed-data` provenance lane); then one builder appended to `deterministic_btd6_list_reply` |
| 10 | **Buffer / steered slot** — owner-steered dashboard/manifest (PR4 write side) or product (mining V-16 phase-2 PNG pack / BTD6 decode ⭐ item 3) | `owner` | in-flight / owner-led |

**Deliberately *not* in this band** (unchanged unless the owner steers): the NL event scheduler build
(Q-0112 — own AI-cost design first) · P1-4 owner live-walks · the live-quality eval battery (prod
creds) · the substrate-kit (owner-action since band-#900) · the Honcho per-user AI memory evaluation
(AI-lane, owner "look into soon").

## 5. Pruned / fixed by this pass

- **Ledger reconciled.** Added the five missing #995–#1020 entries (#1016+#1014, #1004+#1003+#997 as
  two grouped bullets); trimmed the 13 oldest live entries to the archive to hold the ratchet at 20.
  `check_current_state_ledger --window 60` green; `check_docs --strict` green.
- **Bookkeeping-wall prune (the docs-hygiene improvement this pass made — see §6).** The
  "Older merges" line in `current-state.md` had accreted a ~2,000-word per-session "added X, archived
  Y" running tally that was pure redundant drift surface (the archive file *is* the record of what's
  archived). Replaced it with a two-sentence lean version + this pass's note.
- **[reconciliation-pass-2026-06-16-band990.md](reconciliation-pass-2026-06-16-band990.md) re-badged
  `historical`** — its band (#995–#1020) is fully scored in §2 above.
- **Idea→plan promotion (Q-0144).** With the buildable queue thin, promoted
  [`ideas/server-owner-configurable-moderation-dms-2026-06-16.md`](../ideas/server-owner-configurable-moderation-dms-2026-06-16.md)
  into the complete, turn-key [moderation-dm-config-plan](moderation-dm-config-plan-2026-06-17.md);
  scouted the real seam first (the DM machinery already exists on `moderation_service` /
  `moderation_config` — the plan extends it, not a new subsystem). Indexed in `ideas/README.md` +
  `roadmap.md` so it is the executor's next ▶ Next action.
- **`docs/current-state.md` ▶ pointers re-pointed** at *this* doc (by name/date, no PR-number range —
  the band-#800 §6 discipline); the live ▶ NEXT moved to the moderation-DM `ready` slice (the next
  ungated buildable lane).
- **`docs/roadmap.md`** — the live-decade-queue pointer re-pointed from the band-#990 pass to this
  pass; band-#990 marked fully scored.
- **Control-plane state table (Q-0135).** `gh` was unavailable in this container (`check_loop_health`
  SKIP), so the live read was done via the GitHub MCP: issue **#1021** is authored by **`menno420`**
  (a real-user login), re-confirming `ROUTINE_PAT` is set and the loop self-fires — added as a fresh
  evidence tick on row 1 of the canonical table.
- **Marker reset** — `Last reconciliation pass` → **#1020**; `check_reconciliation_due.py` next fires
  at #1050.
- **No new runtime bugs noticed** (docs-only pass) → nothing appended to the bug book; **BUG-0009**
  (slice 3 data-gated) / **BUG-0011** (Hermes gateway crash-loop) stay OPEN.

## 6. The system improvement this pass made (the point of the loop)

**This pass killed a self-inflicted drift surface: the running bookkeeping tally on the ledger's
"Older merges" line.** Every reconciliation/trim session had been *appending* a sentence describing
what it added and archived, growing an unbounded ~2,000-word parenthetical that (a) duplicated the
archive file's own record, (b) was itself a thing future sessions had to keep correct, and (c) made
the live ledger heavier exactly where it is supposed to stay lean. The archive file is the single
source of truth for what's archived, so the tally was pure redundancy. Pruning it to two sentences
removes a recurring per-session chore *and* a drift surface — a small, durable win for every future
reconciliation pass. (Captured as the idea below so the principle — *don't maintain a running tally of
a thing that has its own authoritative record* — is reusable.)
