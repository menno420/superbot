# Gen-1 grand review — independent fleet-wide verification + cleanup

> **Status:** `reference` — dated verification snapshot, written 2026-07-09→10 (UTC) by the
> gen-1 grand-review session (PR #1911, model claude-fable-5 · high). Method: multi-agent
> fan-out (7 corpus readers, 9 PR reviewers, 3 diagnostic agents, 5 adversarial refuters —
> ~1.9M subagent tokens) with every factual claim verified against git/GitHub/Gmail primary
> evidence; independent refuters attacked each drafted section before it landed here.
> Companion: [`gen1-wrapup-email-final-candidate.md`](gen1-wrapup-email-final-candidate.md).

## 1. Scope and headline

Reviewed: everything the Claude Code Projects gen-1 fleet did across
`superbot` · `superbot-next` · `superbot-games` · `substrate-kit` · `fleet-manager` ·
`websites` (trading + 3 codetool arms + venture-lab covered second-hand via committed
retros/manifest — out of this session's repo scope). Deliverables: verified old-vs-new gap
map (§2), open-PR sweep driven to terminal (§3), email fact audit (§4), wind-down audit
(§5), gen-2 synthesis (§6), efficiency verdict (§7), owner actions (§8).

**Headline:** the fleet's record is honest — of the many claims audited, the errors found
were small, few, and all in the direction the fleet's own doctrine predicts (stale
snapshots, not inflation). The rebuild is *further along* than its own status docs said.
The open-PR backlog (9 PRs across 6 repos at session start) is now zero except the
session's own PR. The gen-1 wrap-up email is factually sound after three material
corrections (§4).

## 2. Old-bot vs new-bot gap map (verified against both trees)

superbot-next's own `docs/status/old-vs-new-diff-overview-2026-07-09.md` was compiled at
the 49-PR point and is **stale in the good direction**: at PR #97, the composition root
(`sb/app/main.py`), live Discord adapters (gateway/message/component feeds, NL shell), and
a live-boot-tested runtime (CUT-1 smoke PASS on real Postgres) all exist, and port bands
1–4 have been live-driven in a real test guild.

**Ported (verified in source, not from docs):** 41 subsystem manifests compiling to a
hash-pinned snapshot — 276 commands / 121 settings / 14 events / 45 stores / 96 panel
entries (`manifest.snapshot.json`, `stable_hash sha256:40ea3b28…`). Sample family parity
verified name-by-name: mining 37=37, fishing 20=20, counting 10=10, channel 17=17,
blackjack 4=4, moderation 10, xp 6. All seven port bands present in `sb/domain/`; full AI
kernel (K10) + NL shell; out-of-tree plugin host (next#75).

**Missing — whole subsystems (8):** `utility` (15 cmds; medium-small, portable now),
`ticket` (medium, portable now), `starboard` (small-medium — but blocked on a **reaction
adapter that does not exist anywhere** in the new tree), `general` (8 cmds, small),
`four_twenty` (small), `paragon` (small — the math already exists in-tree, wiring only),
`ux_lab` (dev tool, port-worthiness is a product call), `hermes` (Discord→Claude bridge —
product call). Parity rows exist for each in `parity/parity.yml`, i.e. the rebuild plan
already intends them.

**Missing — depth inside ported subsystems (named-successor'd in the decision ledger,
with one exception):** mining 10,276 lines old vs 732 new; fishing 6,113 vs 566;
creature-battle, poker, and tournament engines; full setup-wizard flows; BTD6 ingestion
pipeline; botsite/dashboard. The exception: **Pillow image cards** (rank/profile/welcome)
have *no* explicit successor named — the repo's own diff overview marks them outstanding.

**Verified better in the rebuild:** manifest compiler with drift-red CI; 22-checker fleet
+ 6 required named gates; 465-golden replay system pinned to superbot @`7f7628e1` with
byte-exact corpus manifest; enforced clock/RNG seams (D-0060/D-0061 each caught a real
unseeded leak); event outbox / authority / workflow / due-queue kernels; 24 checksum-pinned
migrations vs 104; ~1,132 unit tests; hash-locked dependency chain (1,015 `--hash` lines);
append-only 62-entry decision ledger; `verified_live` sign-off registry.

**Known reds (all honest, all ledgered):** every parity row `pending`, 0 flips — gated on
the owner's flag-13 corpus-red disposition ruling; bands 1–4 replay 0/91 byte-green with
every red classified; bands 6–7 not live-tested (band 5 landed this session via #95); AI
dormant (no API key in test env); plugin-hello repo creation 403 (owner).

**Improvements applied this session (contained, per Q-0241):**
- **The `golden-parity` report red on main is NOT a bug** — it is the owner's
  red-until-parity dashboard, born red by design, documented in `docs/decisions.md` with an
  explicit "never mark required"; the required `gate` leg is green. Root-caused, reproduced
  locally (byte-matched CI output: `replayable: 465/465, green: 0/465`, exit 1 by design).
  The correct fix was orientation, not greening: **next#97** (merged) ships
  `docs/status/README-first.md` — the retro's own §E4 prevention ("red ≠ broken") — links
  it from the README, un-drifts the README status line (still said "intent-only first
  commit"), and fills the empty `current-state.md` kit template.
- **One genuine bug found inside the report corpus** — the only non-`RefUnresolved` crash
  class: `games.world_card_view` returned a raw dict where the resolver requires the
  `Reply` duck-shape, crashing live `!worldcard`/`!mystats` + both `RESULT_CARD` panel
  actions (`AttributeError: 'dict' object has no attribute 'outcome'`). Fixed in **next#97**
  per the blackjack-handler precedent + a regression test pinning the shape; suite
  1,125→1,126 green, manifest hash unchanged.
- Small-subsystem ports (utility/general/four_twenty/paragon) were **deliberately not
  executed** in this session: each is a full band-style port (manifest + domain + goldens)
  inside a lane the rebuild coordinator owns mid-band-5 — flagged as the next contained
  work items instead (§8).

## 3. Open-PR sweep — all six repos, terminal state reached

9 open PRs at session start (23:14Z). Each independently reviewed on its merits (diff
read fully; CI verified; claims checked against trees; games#5/#11 and kit#26/#49 acted on
under the owner's review-and-merge authorization for this session).

| PR | Verdict | Outcome |
|---|---|---|
| superbot **#1910** (email draft v2, docs) | merge | **MERGED** 23:18:36Z (owner clicked before the sweep reached it; review concurs) |
| superbot **#1911** | — | this session's PR; lands this report + email candidate |
| superbot-next **#95** (band-5 seams, D-0062) | fix-then-merge | fixed by this session (merged main into branch; sole conflict `control/status.md` resolved to main's byte-newer copy — PR-side blob was already landed via #94), suite 1,132 green, auto-merge armed → **MERGED** 23:52:01Z. D-0062 + band-5 0/12 classification now on main |
| superbot-next **#97** (worldcard fix + red-orientation docs) | (this session's fix PR) | **MERGED** ~23:47Z |
| superbot-games **#5** (mining pure-domain port, was draft) | merge | marked ready → **MERGED** (squash `1eea13a`). Diff verified mining-unique-only vs main; 4 modules byte-identical to oracle; 62 tests green locally (⚑ repo CI runs no pytest — see §8) |
| superbot-games **#11** (grid-encounters, was draft stacked on #5) | merge | retargeted to main; squash of #5 broke ancestry → resolved locally (3 add/add conflicts, branch superset kept; 73/73 tests + gate green on exact head) → **MERGED** (`b285df6`) |
| superbot-games **#14** (mining wind-down succession) | merge | merged main cleanly (byte-identical status alignment from #5 did its job), added a dated addendum to `control/status-mining.md` so gen-2 doesn't boot on historical parked-state lines → **MERGED** (`4c9f889`). Mining wind-down now COMPLETE on main |
| substrate-kit **#49** (make_seed `yield` fix, pin path, do-not-automerge) | merge | branch updated (was behind, no file overlap), checks re-run → **merged on green, label kept** (merge = ratification, owner-authorized; unblocks B1 run-3) |
| substrate-kit **#26** (PL-011 program law, do-not-automerge) | merge | branch updated, checks re-run → **merged on green, label kept** (PL-011 ratified; ends the enforcement-precedes-ratification divergence) |
| fleet-manager **#12** (CI-tier standard §2b + sim) | merge (post-merge review) | self-merged by its lane 23:40:31Z; independent post-merge review **concurs** (5 minor sim caveats recorded, none conclusion-changing) |
| fleet-manager **#13** (external-review prompts + wall entry) | merge (post-merge review) | self-merged by its lane 23:37:03Z; review **concurs** (1 wording nit: the messaging wall is org-disabled cross-session targeting, not tool nonexistence) |

**End state (verified 2026-07-10 00:19Z): zero open PRs across all six repos except
#1911 (this session; auto-merges when its born-red card flips) and superbot #1913 — ⚑ a
LIVE parallel session's in-flight docs PR (opened 00:07Z: an independent wind-down audit
whose headline corroborates this report — "all 7 lanes shipped complete succession
packages; 21/21 spot-checked incidents resolved to real GitHub evidence; zero fabricated
content"; left to its own session per lane discipline).** No PR was closed-unsound; every
verdict was merge or fix-then-merge — the parked backlog was authorization debt, not
quality debt. The fleet also kept moving *during* the sweep (fleet-manager #12/#13/#14
and superbot #1913 all self-landed or opened mid-review) — the program is live, not
frozen.

## 4. Email draft v2 — fact audit

~48 claims verified against git/GitHub/Gmail, including all 12 verbatim error quotes
(found verbatim in committed docs), the ping-latency pair (17:54:33Z → 19:54:00Z), the
games#8 timestamp trap (GitHub: `merged_at 2026-07-09T17:06:06Z` — the draft's friction 13
already states it correctly), 67 files / 48 tests / ~35 min / Opus 4.8, the ~1.5 h merge
wait (#3 ready 15:17:13Z after its final commit → owner-merged 16:42:21Z ≈ 1.4 h; open
14:47:26Z → merged is 1.9 h — the retro's "~1.5 h" measures from ready; keep that basis
when quoting), and the kit-collision window (#3 14:47:26Z vs #4 14:54:45Z = 7 m 19 s).

**Material corrections (3):**
1. "~1,900 merged PRs" → **1,815 merged at audit time** (23:45Z; 1,816 after the
   automated #1912 refresh — recount at send) (`search_pull_requests
   repo:menno420/superbot is:merged`, `incomplete_results: false`; PR *numbering* is past
   #1900 — say both).
2. "zero test-count inflation across three **model arms** (63/100/66)" → three **labs**:
   63 = trading-strategy, 100 = codetool-lab-opus4.8, 66 = codetool-lab-fable5; the
   sonnet5 arm had nothing landed to audit.
3. kit "#74, #75 in flight" → **both merged** (20:22:31Z / 20:17:11Z), plus #76 and the
   #77 wind-down-complete marker — kit's gen-1 wind-down is COMPLETE.

**Minor (4):** #1905 is a manifest *row update*, not the manifest; next#89 is ORDER 006
(an order, not a retro artifact — #87/#92 are the retro pair); the §(a)2 "corrected
upward / commissioned audit" sentence cites fleet-quality-review but its evidence lives in
the eval log + websites retrospective + fleet-review; games #8/#12 "two later worker
sessions" share one session ID in their PR footers — possibly one resumed session (retro
counts two; soften to "later Fable 5 session(s)").

**Gmail ground truth:** sent thread `19f41cd2e5380bb3`, one message, 2026-07-08T15:06:39Z,
**no in-thread reply**. Anthropic's only contact since: Diana Liu's broadcast
2026-07-09T22:29:19Z — *"we … will extend the program through next Tuesday, 7/14"* —
which resolves the send-deadline and is folded into the final candidate. The Railway
build-failure claim is verified (2 notify mails 03:46:11Z/03:47:05Z; resolution state
unconfirmed from committed docs).

## 5. Wind-down completeness per lane

| Lane | Package | Marker | Still open |
|---|---|---|---|
| games/exploration | ✅ on main (#13, 20:10:09Z) | ✅ complete | nothing; "zero abandoned PRs" |
| games/mining | 🟡→✅ **landed by this sweep** (#5/#11/#14) | ✅ complete + dated addendum | 0 parity goldens minted (explicit gen-2 debt) |
| substrate-kit | ✅ (#72→#74→#77, addendum #76) | ✅ complete | ⚑ was #26/#49 — **both now ratified-by-merge**; minor: #76 unindexed in retro README |
| websites | ✅ (#46/#47/#48) | ✅ complete | ORDER 005 honestly-unexecuted ("THE #1 TRAP" is documented); liveness unprobed at handover |
| superbot-next | ✅ retro pair on main (#87/#92; + #93/#90/#94/#96) | 🟡 no wind-down marker **by design** — mid-rebuild (Q-0241), band 5 landed via #95 | band-5 status-debt heartbeat; bands 6–7; flag-13 ruling |
| fleet-manager | ✅ (#7/#8/#9/#10/#11; #12/#13 same night) | 🟡 hub keeps working | heartbeat stale (blueprint-DRAFT and EAP-closes-07-10 lines superseded on its own main; the kit-v1.4.0 cell merely outdated vs the kit repo); winddown-prompt "Deployed: not yet" contradicts dispatch-log "7 of 9 DONE"; `current-state.md` empty template |
| superbot (coordinator) | ✅ instruments #1901–#1905/#1909/#1910 | ✅ cards complete | the email send itself; stale fleet-manifest cells (kit row still "v1.0.0, 637 tests"; next row "no wind-down reaction" is **wrong** — #87–#94 exist); no coordinator self-review against its own #1901 question set |
| trading + 3 codetool arms | ✅ ×4 per manifest + retro-synthesis | ✅ | releases/PyPI owner rituals (out of scope) |

**Net:** with this sweep, **9 of 9 gen-1 lanes have their succession packages on main.**
The residual drift is concentrated in the two *hub* files (fleet-manifest cells, manager
heartbeat) — flagged rather than fixed here because both are other lanes' sole-writer
files.

## 6. Gen-2 synthesis — blueprint vs the lanes

The binding blueprint (`fleet-manager/docs/gen2-blueprint.md`) already absorbs the
fleet's convergent asks: seed-state checklist, ten instruction deltas, measured wake
cadences (§2a), CI-tier standard (§2b, added by #12), and the owner's merge-authority
directive (self-merge always; review post-merge; do-not-automerge dead for gen-2 lanes)
which by itself retires gen-1's largest cost class.

**Where the fleet already agrees** (blueprint == lanes; no ruling needed):
READY-never-draft (5+ lanes) · tested exit-0 setup scripts (4 lanes killed by the same
bug) · walls-up-front with verbatim text + "probing a documented wall twice is a bug" ·
walking-skeleton-first (the rebuild's flagship lesson) · Model+time on every card from
card #1 (3 lanes proved it unrecoverable otherwise) · order claim/lease + "orders stay
`new`" (kit's realized double-execution) · boot-time capability audit (opus4.8's biggest
"blocker" was FALSE) · agent-reachable done-whens.

**Genuine inter-lane disagreements (⚑ for the blueprint owner):**
1. *Wake economics* — kit: hourly no-op wakes must ride the ~7 s control fast lane or
   each burns a PR round. Partially absorbed since drafting: fleet-manager #12 added the
   §2b CI-tier standard to the blueprint; the residual ask is only that the control fast
   lane itself become an explicit §1 seed checkbox.
2. *Relaunch cadence* — exploration (backed by the ~2 h pickup datapoint): a relaunched
   lane starts Class A regardless of its gen-1 tail; blueprint's table reads games
   post-mission as Class C. Blueprint rule 2 points the same way; make it explicit.
3. *Claims-dir vs lanes-manifest* — exploration + mining want a machine-checked
   `docs/lanes.yml` linted by CI for shared repos ("enforce, don't exhort"); blueprint
   seeds a claims/ dir (convention only). Note exploration's own caveat: a claims dir
   would NOT have caught the games collision — that was an *order* delegating a
   shared-ground race, so the manifest pairs with "orders touching shared ground name ONE
   executor."
4. *Heartbeat-before-work scope* — websites: claim-first yes, mandatory full status
   commit no; kit: telemetry at card-commit. Reconcile: the born-red card IS the
   heartbeat.
5. *Born-red for tiny docs PRs* — websites: allow born-complete single-push docs
   sessions (precedent: superbot #1910 and kit's single-commit drops; superbot-next's
   card README, by contrast, mandates born-red-flip-last unconditionally — so this
   exception needs an explicit ruling, it isn't yet fleet consensus).
6. *Actions-route releases* — fable5 "never re-route a policy-denied write" vs opus4.8's
   clean release.yml success (retro-synthesis Disagreement #1). Compose: Actions route is
   the sanctioned FIRST path (blueprint delta 3); fable5's rule narrows to "never
   re-route after an in-session denial."
7. *Merge authority* — mining's "must be a direct human turn" predates and is superseded
   by the owner's directive; its durable residue: authority comes from founding text or a
   human turn, never a coordinator relay.

**Amendment candidates asked by ≥1 lane, not yet in the binding text:** orders carry
`blocked-by` (next F2) · machine-checkable done-when fields in status (websites 3.3) ·
session-scope repo lists declared at dispatch (websites 3.5 — the ORDER-005 knot) ·
`add_repo` workaround + limits in PLATFORM-LIMITS seeds (kit 8) · refusal-branch
scripting in the merge-authority clause (exploration §2) · walls carry last-verified
dates + re-probe hints (kit 💡) · walking skeleton extends to the deploy leg per new
service (websites A6) · OWNER-ACTION six-field grammar fleet-wide (kit 7) ·
"land on main first" session-start line + gitignore the kit's guard-fires ledger
(exploration §6) · synthesized Discord component/modal interactions as a platform ask
(next F3 — "the last human-only inch").

## 7. Honest efficiency verdict

Trading-strategy's blunt self-verdict generalizes fleet-wide: **"the model-work was
efficient; the orchestration layer lost the day."** The building was fast everywhere it
was measured (67-file engine in ~35 min; 18-module port in ~23 min; 49 rebuild PRs in
~14 h with a build loop its own retro rates only "15–20% faster on redo"). The day went,
in descending order, to:

1. **Merge-authority + permission friction** — the ~1.5 h merge wait (75% of a phase);
   the ~2 h park-mandated wait; opus4.8's #4/#6 sitting green ~1.5 h on a false
   capability belief; mining's entire output parked to drafts; 3 failed arming attempts
   on one born-red PR. Largely retired for gen-2 by the merge-authority directive + R21.
   *Live datapoint from this very session:* superbot's stop hook demanded an
   auto-generated `settings.local.json` change be committed while the auto-mode
   classifier denied committing it as self-modification — both defensible alone,
   contradictory together; the same inconsistency class the email describes.
2. **Silent session deaths / setup scripts** — 76 min, ~2.8 h, ~40 min, ~30 min, one
   provisioning death; all the same bug, all seed-fixed now.
3. **Coordination without native primitives** — ~60 no-op webhook wakes/14 h; ~2 h order
   pickup without a live session; double executions (kit #50/#51, games kit-adoption,
   ORDER-number races). The committed-file bus worked; every miss cost minutes-to-hours.
4. **Orientation re-assembly** — the rebuild's biggest per-session sink (~25%,
   append-only handoff prose × 18 workers); the wake-up session's ~40% re-verification
   (which paid — it caught the phantom flag).
5. **CI/merge mechanics** — branch-update dance (~15–30 min/incident; it stranded
   #86/#87 for a session tail before an API branch-update un-stuck them, and held #95
   until this session ran the same dance), runner queues, GraphQL quota (10498/5000).

**Deliberate costs that paid:** verification (~30% of rebuild time; the fix train, the
live-boot bug, D-0060/D-0061, and this session's worldcard bug are all verification
catches); the retro/succession corpus (it made this independent review cheap and is the
gen-2 boot capital); honesty infrastructure (four-reviewer audit; self-audits graded
against git).

**What no lane could do: measure itself.** Every time-split above is a self-estimate;
three lanes proved model identity unrecoverable after the fact; kit's telemetry captured
10 of 21+ eligible rows. Gen-2's Model+time-per-card and telemetry-at-card-commit rules
are the fix; the first gen-2 metric worth watching is *minutes from PR-green to merged*.

**Net:** gen-1 paid a one-time ~13-failure-class discovery tax and converted nearly all
of it into enforceable seed state. The correct reading is not "the fleet was slow" —
it's "the fleet bought the map." Gen-2's job is to spend the map, not re-buy it.

## 8. ⚑ Owner actions (exact clicks; everything else is done or agent-doable)

1. **Send the email** — `docs/eap/gen1-wrapup-email-final-candidate.md` is send-ready
   except Part 1 (yours). Window: EAP extended through **2026-07-14** (Diana Liu,
   2026-07-09 22:29Z).
2. **flag-13 corpus-red disposition ruling** (superbot-next `control/status.md`
   OWNER-ACTION 1) — gates the first `ported` flip and every one after.
3. **superbot-next remaining grants** — create `menno420/superbot-plugin-hello` (403 for
   agents); capped `ANTHROPIC_API_KEY` + `AI_ENABLED` for band 7; sacrificial test
   account + privileged intents; remove the old bot's `!` prefix from the test guild.
4. **substrate-kit P10 required-check swap** — Settings → Rules → remove legacy contexts
   "Kit test suite" + "Cold-adoption smoke", add `kit-quality` (root cause of both kit
   incidents; still pending per kit's queue-state).
5. **Branch-deletion housekeeping** — agents 403 on every path; per-repo stale-branch
   lists live in each lane's owner-actions docs (do NOT delete mining's branches until
   confirmed — now moot, all merged).
6. **venture-lab launch clicks** — repo settings/ruleset/Project/environment/hourly
   routine per `fleet-manager/docs/owner-queue.md` item 14.
7. **Arm the standing routines** — every gen-1 lane row in the fleet manifest still says
   "not yet armed"; §2a cadences are measured and ready (routines are "the
   highest-value click": 7/9 lanes never acked the ping for lack of one).
8. **games CI gap** (from the #5 review): `substrate-gate` runs no pytest — one line adds
   `python3 -m pytest tests/` to the gate; agent-doable on your word (it changes a
   workflow file).
9. Optional standing items already queued elsewhere: kit P4 lab-loop cron / P5 Railway /
   P11-or-P13 public-read decision / PL-010 retro-ratification comment; websites custom
   domains + `/submit` Postgres + ORDER-005 GITHUB_TOKEN; codetool PyPI rituals.

---

*Verification note: this report's own drafted sections were attacked by 5 independent
refuter agents before landing; the corrections they produced are incorporated. Where a
claim could not be independently re-verified it is marked in-line (e.g. resolution state
of the Railway failures). The full working evidence (reader/reviewer/refuter outputs) is
session-side; every load-bearing fact cites its committed or API source in-line.*
