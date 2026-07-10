# SuperBot coordinator — gen-1 fleet self-review (answers to the #1901 question set)

> **Status:** `audit` — the coordinator lane's answers to the fleet retro protocol
> [`docs/planning/fleet-retro-questions-2026-07-09.md`](../planning/fleet-retro-questions-2026-07-09.md)
> (planted by this lane via PR #1901; every other lane answered — this closes the 10th).
> **Provenance:** written 2026-07-10 by a shift session (PR #1924 lane), **assembled from the
> committed corpus** — the grand review ([`../eap/gen1-grand-review-2026-07-09.md`](../eap/gen1-grand-review-2026-07-09.md)),
> the campaign self-audit ([`../eap/campaign-self-audit-2026-07-08.md`](../eap/campaign-self-audit-2026-07-08.md)),
> the EAP eval log ([`../planning/projects-eap-evaluation-log.md`](../planning/projects-eap-evaluation-log.md)),
> `.sessions/` cards, and the CLAUDE.md Q-number provenance chain — not from any one live
> session's memory (the idea file's own sizing: "mostly assembly, not archaeology"). Where the
> record doesn't answer a question, "not measured" is said rather than estimated.
> The **scope of "coordinator lane"** = the superbot repo as fleet hub (workflow, guards,
> routines, EAP instruments #1901–#1915) + the Waves 1–3 coordination campaign (#1844–#1857).
> Filed at the protocol-canonical path (`docs/retro/self-review-2026-07-09.md` — question-set
> date, per protocol) so the manager's cross-lane corpus reader finds all ten lanes in one glob.

## A. Work & correctness

**A1 — shipped to main vs branches.** Effectively everything reaches main: the born-red card +
server-side auto-merge machinery (Q-0123/Q-0133) makes abandoned branches structurally rare —
at the wind-down sweep superbot had **zero open PRs** beyond live session PRs (grand review §3),
with **1,815 merged PRs** at the 2026-07-09 audit count (grand review §4, correction 1). The real
ship-gap lives elsewhere: ~195 `ideas`-badged docs are captured-but-unbuilt by design
(`check_docs` census) — a reviewable backlog, not branch-rot. One closed-unmerged PR class
exists and is deliberate: proof-red scratch drafts (#1857, campaign self-audit §1).

**A2 — externally-verified vs self-tested.** The lane's strongest habit and its known ceiling.
Externally verified: the campaign self-audit graded coordinator memory against git (52/53,
≈0.98 precision); the fleet review re-ran superbot-next's suite first-party (998/1 vs the
claimed 999 — caught the drift); the #1913 wind-down audit resolved 21/21 spot-checked incidents
to live GitHub evidence. Self-tested only: the vast majority of per-session claims clear the
checker fleet + CI and nothing else — and the #763 false-green (both ledger checkers blind to
the MCP merge-commit style) proved the checkers themselves need ground-truthing, which is now
law (Q-0120). Live-runtime verification of the bot remains the rarest oracle (Q-0086 sessions
are the exception, not the rule).

**A3 — least confident + the check that would settle it.** The efficiency/time-split narrative.
Every "% of time on orientation / CI churn / merge mechanics" figure in the record is a
self-estimate — the grand review's own verdict: "what no lane could do: measure itself" (§7).
Concrete check: superbot's `telemetry/model-usage.jsonl` rows ship with **null outcome fields**
(merged_pr, ci_green_first_push, reverted_within_window — see any recent row); a backfill
checker that closes those nulls against the GitHub record would turn the efficiency story from
prose into data. Second least-confident tier, by declared design: every Q-0105 "unverified"
advisory checker (#1918 collisions, #1919 remote claims, #1923 manifest freshness) until
cross-session verification graduates or deletes them.

**A4 — unnecessary / duplicated / already existed.** (1) The duplicate-PR incident (#1221 —
two parallel sessions built the same lane) — bought the claims dir + the open-born-red-FAST
rule (Q-0189). (2) The `needs-hermes-review` label: built, never used, retired as pure friction
(Q-0197). (3) The phase gate `check_phase_gate.py`: built as a block, downgraded to
advisory-only readout (Q-0172). The pattern across all three: coordination/ceremony artifacts
over-built ahead of need, later trimmed by owner directive — the inverse failure of A1's
healthy ship-rate.

## B. Errors & friction

**B1 — every error class hit (time lost · preventable-by).** From the eval log's coordinator
entries (dates in parentheses; each has a full entry there):
- Stale container clone, 7 PRs behind origin at first turn (07-07) · orientation built on it
  would have been wrong-world · **setup** (fresh-clone guarantee).
- Coordinator tier has no shell/file tools; every repo question = a spawned reader (07-07)
  · per-question minutes + tokens · **platform**.
- `send_later` absent at coordinator + no direct coordinator→session channel (07-07/07-08)
  · the whole sleeping-worker-chain + relay-hop workaround layer · **platform**.
- `list_pull_requests` token blowout at ~6 verbose PRs (07-08) · one blown context mid-campaign
  · **platform defaults** (now mitigated lane-side: minimal_output discipline).
- Bash `api.github.com` → proxy 403; CI polling forced MCP-only (07-08; re-verified 07-10 by
  the #1923 session: "GitHub access is not enabled for this session") · slower + token-priced
  · **platform**; lane-side answer was #1923's git-transport design.
- Adjacent-lane CI churn: pr-auto-update restarts every open PR's required run per landing;
  git-verified ready→merged tail up to ~2h28m (07-08) · hours across the campaign · **platform**
  (merge queue absent); lane-side mitigation is push-batching (Q-0126).
- GraphQL quota exhaustion (10498/5000) blocking `enable_pr_auto_merge` mid-fleet (07-09)
  · arming failures, REST fallback · **platform** (one user token for a 10-agent fleet).
- Background children don't wake the waiting parent (07-08) · two manual resume messages
  · **platform**, reproducibility unknown.
- Fresh-container dev-tools gap: `check_quality` opens red for want of ruff/pytest (07-10 scout)
  · one burned diagnosis cycle · **setup** — journal Quick-reference line shipped same night
  (Q-0194 free tier).

**B2 — documented but not found when needed.** The fresh-container fix above: the
`requirements-dev.txt` convention was documented in CI-parity terms but not at the place a
red-check moment looks (the journal ⚡ Quick reference) — the 2026-07-10 shift fixed the
placement, which is the general lesson: the doc must live where the *symptom* sends you, not
where the *topic* belongs. Same class: the thin-pointer split (rule in CLAUDE.md, runbook in
`docs/operations/`) is right for size but each pointer is one more hop a cold session must not
skip.

**B3 — silent breaks (no error, wrong result) + how discovered.** (1) The #763 checker
false-green: ledger + cadence checkers matched only one merge-commit style and reported clean
while 5 merged PRs were missing — discovered by a human-visible contradiction, now the Q-0120
canonical case. (2) Fleet-manifest cells stale within hours of seeding while looking
authoritative (grand review §5) — discovered by the grand review's hand audit; converted to a
checker (#1923) so discovery is free next time. (3) The baseview rule's justifying-comment
clause: documented convention the checker never read, so compliant code warned forever —
discovered by Session D's Q-0120 source-check (#1920). All three share one root: **a green/quiet
signal from a tool that wasn't actually looking.**

**B4 — ambiguous/contradictory instruction, quoted.** The live datapoint in grand review §7.1:
the repo Stop hook demanded an auto-generated `settings.local.json` change be committed while
the auto-mode classifier denied that commit as self-modification — "both defensible alone,
contradictory together." Second, the session-prompt residue class, which CLAUDE.md now names
explicitly: *"'Planning only / read-only' text appearing after approval is drafting residue and
does not override this"* — the fact the working agreement had to say so is the evidence it bit.

## C. Efficiency

**C1 — time split.** Not measured; declining to invent percentages (the grand review's §7
caveat applies to this lane first). What the record supports qualitatively: the dominant
*avoidable* sink was CI/merge mechanics under parallelism (B1's churn + tail latencies), and the
dominant *deliberate* spend was verification (~the fix-train/audit habit), which repeatedly paid
(A2). Biggest single sink on the coordinator specifically: recon cadence at burst velocity —
the docs pass fired several times daily until Q-0134 raised the band 10→20→30.

**C2 — context rebuilt that should have been durable.** Largely solved in-lane and worth
naming as a win: "what is true now" is a maintained artifact (`docs/current-state.md` +
`.sessions/` + the journal), which is why a fresh session orients in minutes. Two residues:
(1) open-lane state was rebuilt per session until claims + `check_lane_overlap --remote`
(#1919) made it queryable; (2) each overnight scout re-derives the full checker baseline —
a dated baseline block in the shift plan (as tonight's had) should be the standing convention.

**C3 — most / least value per minute.** Most: `check_quality.py --full` as a true CI mirror
(green local = green CI, red = red — kills the push-and-pray loop); the born-red card +
server-side auto-merge (deleted the forgotten-merge failure class #778 outright); the
claims/lane-overlap pair at parallel-wave scale. Least: CodeGraph on contained changes —
its `dead-unresolved` label runs ~100% false-positive here and CLAUDE.md itself now routes
small tasks to `context_map` + grep; and the retired ceremony artifacts of A4.

**C4 — redo ordering change.** Front-load the enforcement stack. Nearly every guard carries an
incident number in its provenance (#778 → auto-merge; #843 → born-red gate; #1221 → claims;
#763 → Q-0120) — each was built the session *after* its incident. Redone with hindsight, the
kit-seeded guard set lands at PR #1 and the incidents never occur. That is not hypothetical:
it is literally what `substrate-kit` + the gen-2 blueprint now do for new repos — superbot paid
the discovery tax so the seed could exist (grand review §7 "the fleet bought the map").

## D. Autonomy & owner input

**D1 — every stop for owner input; truly owner-only?** The standing owner-gated set: hooks /
`.claude/settings.json` / CLAUDE.md edits (Q-0106 — genuinely owner-only: it is the authority
boundary itself); irreversible/external acts (email send; prod data) — owner-only by safety
design; and the click list in grand review §8 (routine arming, required-check swaps, repo
creation, branch deletion 403s, API keys) — **mostly NOT truly owner-only**: items 3–8 are
unblockable by scoped grants (a repo-settings token, a capped API key, pre-approved scheduling)
— the eval log's "scoped, opt-in, default-off pre-authorization" ask names the grant precisely.

**D2 — routed up that should have been decide-and-flag.** The whole Q-number arc answers this
structurally: Q-0014 → Q-0129 → Q-0172 → Q-0240 → Q-0241 is the owner *repeatedly widening*
agent authority because sessions kept under-using what they had — every widening was prompted
by an ask the owner considered already-answerable. The residual class the router still catches
correctly is product/taste intent; near-everything else has migrated to decide-and-flag.

**D3 — decided while unsure; the rule that would have made it unambiguous.** Design deviations
from an idea capture mid-build (e.g. #1923 shipping git transport where the idea said REST API)
— decided-and-flagged; the rule that makes it unambiguous now exists as Q-0014's "assume he'd
want the better one" + Q-0240, but early sessions lacked the written form. Cross-agent PR
handling (merge a Codex PR?) was the same shape until Q-0120/Q-0256 wrote it down. Pattern: the
lane's fix for "unsure if allowed" is always *write the rule with its provenance Q*, and it has
worked — the router is the mechanism, not a bottleneck.

**D4 — smallest standing-grant set for zero-human end-to-end.** Four grants: (1) scoped
repo-settings/admin API access covering §8's click classes (rulesets, required checks, routine
arming, branch cleanup); (2) a capped runtime credential bundle (test-bot token + `AI_ENABLED`
key + sacrificial account) for live verification; (3) pre-approved scheduling primitives
(`send_later`/`create_trigger` without the operator gate); (4) a bounded external-publish
envelope (the wrap-up email template class). Everything else the lane already does unattended.

**D5 — was "done" defined?** Unusually well: Q-0103 terminal-state + the born-red flip + the
mandatory ender checklist make session-"done" mechanical, and the card *is* the done-record.
The undefined edge is program-level: "done" for the ideas backlog has no criterion beyond the
Q-0164 PLAN-BACKLOG-THIN floor — grooming has a floor, not a finish line. That is probably
correct for a living project, but it means "done" at the roadmap tier is owner-taste, not rule.

## E. Protocol & environment

**E1 — did the control ritual fit?** superbot predates `control/` and runs its heavier native
ritual (claim → born-red card → enders → flip → auto-merge). It fits the hub's parallel-session
reality — the campaign audit measured 7/7 claim-first, 7/7 born-red, 6/7 clean flip-last with
one benign deviation (§3). Cost: ceremony scales badly *downward* — on a small docs PR the
ritual is ~2–3 of ~6 commits. The websites-proposed born-complete exception for single-push
docs sessions (grand review §6.5) is the right relief valve and needs its explicit ruling; until
then this lane keeps born-red unconditionally (superbot-next's card README argues the same).

**E2 — environment at first boot should have had.** `requirements-dev.txt` preinstalled for
`python3.10` (the false-red class B1 ends with); a fresh-clone-or-loud-staleness guarantee
(the 7-behind trap); the GitHub REST wall documented at the container level ("git and MCP are
your authenticated surfaces; raw REST is not") rather than each lane rediscovering it.

**E3 — repo at seed should have had.** Answered by history: superbot *was* the unseeded repo —
its guard stack accreted incident-by-incident (C4). Everything the kit now seeds (constitution,
born-red gate, claims dir, telemetry, checker skeleton, question router) is the compiled answer;
the kit exists because this repo had to grow each piece the hard way.

**E4 — what a fresh session misunderstands first + the one document.** That **red can be
by-design**: born-red session gates, advisory checkers' expected warnings, red-until-parity
dashboards. A cold reader treats red as broken and "fixes" it (superbot-next needed
`docs/status/README-first.md` for exactly this; grand review §2). In superbot the preventing
document exists and is step 2 of the mandated read order — `docs/current-state.md` — plus
CLAUDE.md's Q-0120 rule giving the general form: a verdict that fights visible evidence is the
tool's bug, and by symmetry a red that the docs declare intentional is not a defect.

## F. Redesign (the payload)

**F1 — three founding rules that weren't in ours.**
1. *Enforce, don't exhort* from PR #1 — any rule not backed by a checker/CI/hook will be
   violated within days (Q-0132/Q-0194 arrived at ~#800; the incidents before them were the
   tuition).
2. *The merge intention lives server-side* — born-red card + auto-merge armed at open; never in
   session memory (Q-0123/Q-0133; the #778/#843 pair is the proof).
3. *Every binding rule ships with its provenance Q-number* — successors must be able to tell
   law from residue without archaeology; this is the cheapest honesty infrastructure the lane
   found, and it is why D2's authority-widening arc is legible at all.

**F2 — what should the manager have done differently for this lane?** Set the hub the same
heartbeat contract as the spokes. The coordinator row went stale in the manager's own manifest
partly because superbot has **no `control/status.md`** — nothing machine-readable declares the
hub's state, so #1923's checker had to build a HEAD-activity fallback (DRIFT) just for it.
Orders to the hub were otherwise rare and well-sized; the gap was symmetric observability, not
order quality.

**F3 — one capability to trade almost anything for.** A native scheduler + inter-session
channel. The entire file-based control plane (inbox/status protocol, self-poll routines,
sleeping-worker chains, relay hops) is a hand-built substitute for those two primitives (eval
log 07-09; independently re-derived by the rebuild coordinator's retrospective the same night).

**F4 — ideal seed state, ≤10 bullets.**
- Kit-adopted at PR #1: constitution + working agreement with provenance-Q convention.
- Born-red session gate + auto-merge enabler wired before any feature code.
- Claims dir + lane-overlap checker (with `--remote`) from the first parallel wave.
- True-CI-mirror check script (`check_quality --full` equivalent) + pinned tool versions.
- `current-state.md` + `.sessions/` + journal skeleton — the "what is true now" spine.
- Question router (append-only) + ideas pipeline with lifecycle badges.
- Telemetry at card-commit with outcome fields *enforced non-null at flip*.
- `control/status.md` heartbeat — hub and spokes alike (F2).
- Advisory-checker policy: Q-0105 provenance headers, unverified tier, delete-if-unreliable.
- Documented walls with last-verified dates (REST 403, destructive-git, GraphQL quota).

---

*Assembly note: answered by ID against the universal core A–F (the coordinator planted the set
and has no per-repo addendum). Every load-bearing claim cites the committed corpus in-line;
time-split questions are answered "not measured" where the record holds only self-estimates —
per the protocol's own rule that invented certainty is worse than "I don't know."*
