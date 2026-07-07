# Fable-5 ultracode brief — fold today's owner ideas into the rebuild plan + re-verify (2026-07-07)

> **Status:** `plan` — the launch brief + paste-ready prompt for a dedicated **Claude Fable 5,
> `/effort ultracode`** session. Owner-directed (2026-07-07), same day as
> [`rebuild-final-review-report-2026-07-07.md`](rebuild-final-review-report-2026-07-07.md) — this is a
> **narrower follow-on**, not a redo: fold four new owner-raised findings into
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md) and re-verify the plan
> at the same rigor as the prior pass, explicitly hunting for further enhancements the new material
> surfaces. Governance: **Q-0241** (never-wait, live-test, silence=consent), **Q-0240**
> (decide-and-flag) — this session decides its own calls and does not wait for the owner.
>
> **Updated same day (post-launch):** a fifth finding (automod's cross-channel-spam evasion + missing
> duplicate-content detection) was **shipped directly on the live bot** (PR #1789, merged) rather than
> left for this session to reason about — see the full reasoning in §4. It needs **zero attention**
> from this session: not folding, not re-verifying, not even reading for context. The mandate below is
> four findings, not five.

---

## 0. Launch (owner: paste §7; the rest is the session's reading route)

- **Model:** Claude **Fable 5** (`claude-fable-5`) — 1M-token context (load the whole corpus at once),
  128k max output, self-validates its own work at high effort.
- **Effort:** `/effort ultracode` (xhigh + automatic workflow orchestration). Verify `/config` →
  Dynamic workflows is on.
- **One Fable-5 caveat:** safety classifiers refuse ~<5% of sessions and reroute to Opus 4.8 — nothing
  here is refusal-prone, but retry on Opus if a sub-task refuses.

## 1. Reading route

1. `.claude/CLAUDE.md` (Working agreement) → `docs/collaboration-model.md` → `docs/current-state.md`
   + `docs/current-state/S3-ai-memory.md` → `.session-journal.md` (Quick reference).
2. **The plan of record, in full:** `rebuild-canonical-plan-2026-07-06.md` (§1 flags, §2 taxonomy, §3
   arc, §4 gates, §5 the 17-step start sequence, §8 decisions, §9 supersessions, §11 amendments) + its
   companions `rebuild-test-guild-design-2026-07-06.md` and `rebuild-phase-2.5-procedure-2026-07-06.md`.
3. **The prior final review** — `rebuild-final-review-report-2026-07-07.md` — so you don't re-derive or
   re-litigate what it already settled (§2 below condenses this).
4. **Today's four remaining captures, all dated 2026-07-07 — all candidates for folding** (see §3):
   - `docs/ideas/channel-role-scoped-authority-gap-2026-07-07.md`
   - `docs/ideas/user-self-service-automation-scheduler-2026-07-07.md`
   - `docs/ideas/moderation-feature-gaps-2026-07-07.md`
   - `docs/ideas/guild-config-backup-and-data-export-gap-2026-07-07.md`
   - (A fifth capture, `docs/ideas/automod-spam-detection-gaps-2026-07-07.md`, is now `historical` —
     shipped live, PR #1789 merged. Skip it entirely; do not read it, fold it, or mention it in your
     output. §4 explains why it was resolved this way instead of through this consolidation.)
5. **This session's own plan critique** (chat-only until now — captured in full in §3.C below since it
   has no other durable home) — treat it as a sixth input with the same weight as the idea docs.

## 2. What is ALREADY settled — spot-check, do NOT re-litigate

Everything the 2026-07-06 canonical plan and the 2026-07-07 final review already settled: Gate V
complete (Sequence C adopted), the capability audit (85%+ fit), the Phase-2.5 A/B verdict (adopt-render
fix shipped, cold-start *benefit* claim still unproven — carry the caveat, don't rerun the whole A/B),
the sim dispositions (D-17), the sequencing/K7-urgency question, the K9=durability/K10=AI-kernel
numbering (Gate-0 wins, not the old design-spec numbering). Full detail in the final-review report's
§A/§2 — don't reopen any of it here.

**Also settled, same day, after this brief was first written:** the automod cross-channel-spam +
duplicate-content gap is **fixed and merged** (PR #1789) — `SpamTracker.record_and_count_any_channel`
+ a new `DuplicateTracker`, both through the existing audited `moderation_service` seam, both
defaulting OFF, fully tested. This is not a rebuild-plan matter at all (see §4) — it's listed here
only so you don't go looking for it.

## 3. The mandate — what this session must produce

Decide-and-proceed (Q-0241). Produce **one short consolidation report**
(`docs/planning/rebuild-idea-consolidation-report-<date>.md`) plus **direct amendments to the canonical
plan** (extend §11 with new lettered entries, same pattern as A-1…A-11) for whatever you decide to fold.

### A. Fold the two foundational, time-sensitive findings — both land before their kernel band is built

1. **Channel-role-scoped-authority-gap.** Confirmed (with `path:line` citations already in the idea doc)
   at both the live governance stack and the frozen K6 design: neither can express "only role X in
   channel Y" — `resolve_authority`'s `Lane{CAPABILITY,TIER}` and `ChannelAccessDecision`/`AccessMode`
   are both guild-wide/ordinal, never role-specific. K6 has **not been built** (§5 step 9, not started)
   and sits upstream of K7/K8 in the build chain, so this is the one item in today's batch where timing
   actually matters — decide the shape (the idea doc sketches a `Lane.ROLE_SET` addition) and land it as
   a canonical-plan amendment *before* whoever writes K6's Phase-B per-step plan needs it, not after.
2. **User-self-service automation scheduler.** Owner-proposed foundational primitive: guardrailed,
   unlockable, per-user recurring "cron jobs" (a daily rank ping; a periodic game-state check), ridden on
   K9's not-yet-built `ManagedTaskSpec`/due-queue machinery rather than bolted on per-feature later. The
   owner has already ruled on the hard part: category-B (auto-*acting* automation, e.g. auto-collect) is
   allowed to exist, but only gated behind an unlock cost (coins + XP or similar) plus a free daily
   allowance that can itself be increased — **and the owner explicitly wants the pricing mechanism
   designed in its own dedicated session, not decided here.** Your job: land the **kernel primitive**
   (category A notify-only, plus category B *structurally reserved but switched off* pending pricing) as
   a K9 amendment now, and confirm the split is real — the K9 build should not stall waiting on
   economics, and the future pricing session shouldn't have to rush ahead of the kernel.

### B. Judgment calls — decide whether these two also warrant elevation now, or stay backlog

3. **Moderation feature gaps** (join verification/CAPTCHA gate; a dedicated ban-appeal/modmail flow
   distinct from the general ticket system; custom trigger→response commands). These are feature-level,
   not architectural — the idea doc's own recommendation is "whoever ports the moderation/security
   subsystem in Sequence C decides whether these port forward as new manifest-declared features." Your
   call whether any deserves an explicit landing in the plan now (e.g. named in a Phase-B walk row) or
   should genuinely wait — don't force an elevation just because it's on the list.
4. **Guild-config backup/restore + GDPR data-export gap.** Two adjacent misses: self-service per-guild
   settings backup/restore (distinct from the whole-DB disaster recovery S14 already covers), and the
   "export" half of GDPR-style data requests (erasure is thoroughly mechanized in the privacy rubric
   landing at S11; export quietly never made it back in after the original idea capture). The idea doc
   flags these as cheap to add *because* they ride infrastructure S11/S14 are already building for other
   reasons — assess whether that's true and, if so, whether to fold them into S11/S14's scope now rather
   than as a separate later initiative.

### C. Re-verify the plan against this session's own critique — hunt for enhancements

Earlier today (before the idea captures), this session gave the owner an independent critique of the
canonical plan, agreeing with the plan's own self-identified #1 risk and adding several of its own. None
of this is written down anywhere else — treat every point below as a real input requiring a real
verdict (fold, refine, or explicitly reject with reasoning), not a rhetorical aside:

- **Layer V thinness at exactly the moment human gates were retired** (the plan's own named #1 risk,
  final-review report §A). This session's addition: "widen parity depth per band as we go" is a
  discipline commitment, not an enforced one under never-wait — consider hardening step 11 into a
  **numeric, CI-enforced per-band coverage floor** (a band can't merge below X% event/table/settings
  depth for the subsystems it touches) rather than leaving it as a norm.
- **AI/knowledge-domain verification is a different kind of problem than golden parity, and it's ported
  last.** Golden replay works for deterministic commands; it doesn't make sense for generative BTD6/
  Limbus answers. The live bot already has a separate semantic-grading eval harness for this reason.
  The verification-review doc says to "preserve" it as advisory; this session's ask: should it become a
  **required**, not advisory, gate specifically for port band 7 (knowledge domains onto K10), given it's
  arguably the bot's most differentiated feature and is built last, after review attention has likely
  waned?
- **The human `verified_live` bottleneck may not be budgeted into the timeline.** Discord's ToS forces
  slash/component/panel verification through an actual human clicking the test guild (companion C) —
  the "~2-week floor" estimate is stated as being about agent merge velocity. Does the plan's timeline
  implicitly assume unlimited owner (or delegated alt-account) click-through capacity across ~55
  features? If so, name it explicitly as the real pacing risk rather than leaving it implicit.
- **Post-cutover ratchet permanence.** The manifest-fit escape-hatch ratchet (the ~15% of surface that
  stays hand-written code) is specified as a build-time discipline. Confirm whether it's wired as a
  **permanent** post-cutover CI metric (so year-two feature work can't silently erode back toward the
  smeared-file pattern the whole rebuild exists to kill) or only enforced during the port itself — and
  fix it if the latter.
- **Rollback window (N=7d) vs. actual game/economy event cadence.** Sanity-check whether any live game
  system has a weekly-or-longer cycle (events, resets, ladders) that could hide a cadence-dependent bug
  past the 7-day window, where only the narrower reverse-import valve (money/audit only) would remain as
  a safety net. Not necessarily wrong — just verify it against real cadences rather than leaving it an
  unchecked assumption.

## 4. What NOT to do

- **Do not fold, re-read, or re-verify the automod cross-channel-spam/duplicate-content finding at
  all — it's fully resolved, not merely out of scope.** The owner initially asked whether this should
  go into the rebuild plan instead of staying a live-bot punch-list item; the answer was no *and* it
  no longer even needs a plan mention, because it was fixed directly on the live bot the same day
  (PR #1789, merged) rather than deferred. The reasoning, in case a future reader wonders why a
  live-bot bug fix happened mid-rebuild-planning-session: the rebuild ports subsystems by replaying
  **goldens captured from the live bot's current behavior** and requires byte-for-byte parity before
  merging (`red until parity`) — leaving the bug unfixed would mean whatever golden gets captured for
  automod encodes the *buggy* behavior, and the new bot would then be obligated to reproduce that exact
  bug to pass its own parity gate. A plan footnote doesn't reliably prevent that; golden-replay porting
  carries forward whatever it's given by default. Fixing it live instead means the correction flows
  into the rebuild automatically via the project's own existing rule (L-21: any PR that changes
  golden-captured behavior re-captures the affected goldens in the same PR) — no special-casing, no
  amendment, no re-verification needed. Treat this as closed; spend zero budget on it.
- Don't re-open Gate V / Sequence C / the K7-urgency question, the Phase-2.5 A/B, or the K9/K10 numbering
  — all settled, per §2.
- Don't treat this as license to re-review the whole plan from scratch the way the 2026-07-07 final
  review did — that pass is done and its findings stand; this session's job is the four new inputs plus
  the five specific re-verify points in §3.C, not a fresh A–H sweep.
- Don't wait for the owner on anything reversible — decide, live-test if applicable, flag on the report.
  The only genuine owner call buried in today's material is the automation-scheduler's pricing mechanism
  (§3.A.2) — and even that is explicitly deferred to its *own* future session, not answered here.

## 5. Owner decisions to FLAG (not block on)

- The channel-role-authority lane's exact shape (`Lane.ROLE_SET` vs. an alternative) — recommend one,
  flag it, proceed.
- Whether AI/knowledge verification becomes a required (not advisory) gate for port band 7 — recommend,
  flag, proceed.
- Anything from §3.B's judgment calls that you decide to elevate rather than backlog — flag the reasoning
  either way.

## 6. Output artifacts

1. `docs/planning/rebuild-idea-consolidation-report-<date>.md` — what got folded, what got left as
   backlog and why, the re-verify verdicts on §3.C, and a decisions log (same style as the final-review
   report's).
2. Direct amendments to `rebuild-canonical-plan-2026-07-06.md` §11 (new lettered entries continuing from
   A-11) for whatever is folded, each with a one-line rationale, mirroring the existing amendment style.
3. Update each folded idea doc's "Recommended routing" section to point at where it landed, so a future
   reader doesn't find an idea doc that looks unresolved when it's actually been folded in.

## 7. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`** on the SuperBot repo. Read
> `docs/planning/rebuild-idea-consolidation-fable5-ultracode-brief-2026-07-07.md` first — it is your
> full brief, reading route, and the "already-settled, don't-redo" baseline.
>
> Fold today's four remaining owner-raised findings into the rebuild plan of record
> (`rebuild-canonical-plan-2026-07-06.md`): the **channel-role-scoped authority gap** (K6, time-sensitive
> — K6 isn't built yet) and the **user-self-service automation scheduler** (K9, with category-B
> auto-acting automation structurally reserved but gated off pending its own dedicated pricing session)
> should both land as canonical-plan amendments. Use your own judgment on whether the **moderation
> feature gaps** and the **guild-config backup/GDPR-export gaps** also deserve elevation now versus
> staying backlog — don't force it either way.
>
> Then re-verify the plan against everything else we discussed today, not just the two big ones — the
> brief's §3.C lists five specific points (the layer-V depth risk, whether AI/knowledge verification
> should be a required gate for its port band, whether the human verified_live bottleneck is honestly
> budgeted into the timeline, whether the manifest-fit ratchet is permanent post-cutover, and the
> rollback-window-vs-game-cadence sanity check) — but don't treat that list as exhaustive. Reason freely
> over the whole corpus and today's discussion and surface anything else worth enhancing.
>
> A fifth finding from today (automod duplicate-message/cross-channel-spam evasion) is **already fully
> resolved — shipped directly on the live bot (PR #1789, merged), not through this plan.** It needs zero
> attention from you: don't read the idea doc, don't fold it, don't mention it in your report.
>
> You operate under **Q-0241**: decide reversible calls yourself, flag every decision on your
> consolidation report, and never wait for me — if I say nothing, it's approved. Ship the report and the
> canonical-plan amendments; route only genuine product/intent forks to the question router.
