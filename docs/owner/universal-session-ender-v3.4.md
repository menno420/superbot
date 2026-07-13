# Universal session ender — v3.4 "wind down and land"

> **Status:** `reference` — the fleet's universal session-ender prompt, hub copy.
> **Provenance:** owner-directed in-session rewrite, 2026-07-13 (this repo, PR #2065;
> supersedes **v3.3, 2026-07-12**). The owner's direction, verbatim intent: *finish what
> is in flight to a reasonable stopping point or to done — nothing rushed; then properly
> review the session and document all struggles and all things that went well; no new
> work starts; everything refreshed so no stale docs remain; every lesson baked in for
> the future.*
> **What changed vs v3.3:** the opening move. v3.3 opened with "SHUT DOWN NOW — start no
> new work", which in practice invited rushed merges and abandoned mid-stream work. v3.4
> opens with **LAND** (finish properly first — the no-new-work fence is on *starting*,
> never on *finishing*), and adds three new steps: **REVIEW** (honest retrospective,
> struggles + wins), **REFRESH** (de-stale every doc), **BAKE** (every lesson into a
> future-proof surface). Every v3.3 incident-hardened mechanic is preserved: parked-PR
> landing paths, poll budgets, empty-vehicle merge check, failsafe-stays-armed (F-1),
> business-cron handling, walled-deletion relay, PR-carried heartbeat, neutral-facts
> rule, flip-last, terminal recital.
> **Canonicalization:** the prompt registry in `menno420/fleet-manager`
> (`projects/*/…` + the v3.x generation lane) owns fleet canon — this file is the hub
> copy. Route it to the manager as the next inbox ORDER / dispatch note ("adopt ender
> v3.4 into the next prompt generation"); until the registry carries it, the owner
> pastes the block below directly into session/Project configs.

---

## The paste-ready prompt

```
> **Status:** `reference`

v3.4 · 2026-07-13 · universal session ender — wind down and land

WIND DOWN AND LAND. This message ends your session's chain. From this moment START
NOTHING NEW — no new lane, order, idea, or refactor (queue new arrivals for the
successor: ideas → idea intake, orders → inbox, opportunities → the baton). The fence
is on STARTING, not on finishing: work already in flight gets finished PROPERLY — to
done, or to a clean documented stopping point. The goal of this ender is that nothing
ends rushed, nothing ends stranded, and the session's full experience — struggles and
wins alike — is reviewed, written down, and baked in before the chain terminates.
(Worker/dispatched sessions: run steps 1–3, fold your step-5 review into your report
to your coordinator — who owns steps 4–9 at seat level — then report and end; a worker
never writes control/status.md and never disposes seat routines.)

1. LAND — finish what is in flight, deliberately. FIRST make the honest budget call:
   remaining work vs remaining context/time. Fits → finish it AND verify it (checks
   green, the change demonstrably does what it claims — verification is part of the
   work, not optional polish). Doesn't fit → choose the SEAM NOW instead of sprinting
   past it: bring the lane to its nearest clean boundary (code coherent, tests green on
   what exists, WIP committed + pushed on its branch) and write the resume pointer —
   what remains, the exact pickup point (file / next command / next decision), and why
   you stopped there. A documented seam is a successful landing; a rushed merge or a
   skipped verification to "finish faster" is a failure of this step. Never leave a
   lane in a state only you can decode.
2. PARK — every session PR reaches READY+green or closed-with-reason; nothing left
   draft or red. Checks still PENDING: spend the remaining poll budget (≤3 total);
   still pending → park READY with `pending @ <run-id>` named in the parked-PR list —
   verification passes to the successor/owner, never a poll loop. If anything merged
   this session, diff the merge commit and confirm the payload actually landed (an
   empty-vehicle merge is a known failure class). A seam from step 1 that is not
   mergeable as-is → close its PR with the reason, keep the branch, and record the
   resume pointer in the baton + PR body. Name each parked PR's landing path:
   `owner-click` (default) or `successor non-author review-merge` (only where this
   lane's recorded denials never named relayed authorization).
3. RELEASE — delete your claim files (yours only; a possibly-live parallel claim is
   not yours to sweep).
4. ROUTINE DISPOSITION — you NEVER re-arm here, and you never hand a routine to the
   owner. Delete the pending send_later pacemaker + every session-bound WAKE trigger
   this session created, then VERIFY absent via list_triggers paginated to exhaustion
   (limit 100, next_cursor until has_more is false) — BEFORE the heartbeat, so the
   baton records what really closed. TWO EXCEPTIONS, never closed here: (a) the seat
   FAILSAFE cron — it stays ARMED as the successor's dead-man bridge (F-1); record its
   id + schedule in the heartbeat; the successor's boot cutover rebinds-then-deletes
   it; delete it yourself only on an explicit owner retire-this-seat order, and then
   only AFTER the heartbeat has landed and the card is flipped, as the true final
   call. (b) a BUSINESS cron (a scheduled deliverable — its prompt does real work, not
   a wake): record id + next-fire for the successor to rebind — and a
   FRESH-SESSION-PER-FIRE business cron is recorded but NEVER rebound: it outlives
   every seat session by design. Deletion walled from this toolset → relay the SAME
   delete through a spawned worker (ONE trigger-MCP call per worker), verify;
   genuinely uncloseable → carry the id + why into the heartbeat, for the successor.
5. REVIEW — the honest retrospective, in a durable committed doc (the repo's retro /
   session-log convention), never chat-only. Four sections, no filler — an empty
   section says so and why: (a) SHIPPED & PARKED — what landed, what parked, what was
   attempted and dropped, every claim citing a commit / PR / CI run; (b) STRUGGLES —
   every wall and denial (verbatim quotes go in the PR body, not the heartbeat), every
   time sink, wrong turn, tool that lied, doc that misled; "it went fine" with a real
   struggle omitted is a false record; (c) WENT WELL — what worked and why, and what
   the successor should deliberately repeat (a pattern, a tool, an order of
   operations); (d) SURPRISES & OPEN QUESTIONS the successor should know. This review
   drives steps 6 and 7 — write it before touching the docs.
6. REFRESH — de-stale sweep: after this step, no surviving doc describes the
   pre-session world. True up every doc this session touched or knows to be stale —
   status/tracker rows, current-state entries, README/orientation pointers, prompt
   copies, capability/walls files, anything still saying "in flight" about work now
   done or parked. Correct in place with a dated marker; delete what is now wrong
   rather than leaving it beside the truth; regenerate generated surfaces instead of
   hand-editing them. The test: a fresh successor reading only the refreshed docs
   holds zero false beliefs about this lane.
7. BAKE — every step-5 lesson lands in the surface that changes FUTURE behavior, not
   only in retro prose (enforce, don't exhort): checker / CI / test guard first, else
   a skill or prompt delta (registry-canonical prompts: write the proposed delta into
   your outbox/heartbeat for the manager — never edit another repo's registry
   yourself), else a journal-rule / owner-gated-config proposal, and where the lesson
   generalizes fleet-wide, a kit-graduation proposal. Minimum one system improvement
   per session — or an explicit, honest "nothing to improve, because X".
8. HEARTBEAT — overwrite control/status.md as a COMMIT ON YOUR SESSION PR (main is
   PR-only; a heartbeat outside the PR strands — successors read the newest heartbeat
   across main + open PRs): routine disposition AS VERIFIED in step 4 (ids closed /
   ids uncloseable + why / ids left-for-successor / the failsafe id staying armed as
   the successor's bridge), parked-PR list with landing paths + seam resume pointers,
   ⚑ owner asks paste-ready, next-2-tasks baton, and pointers to the step-5 retro +
   step-6 refreshed docs. NEUTRAL facts + pointers ONLY — no steering lines, no
   verbatim denial quotes (those live in the PR body / owner-queue); durable links
   live in docs/current-state.md, never sole-homed in status.
9. FLIP — flip the born-red session card to complete as the deliberate LAST COMMIT
   (after the heartbeat, so the merged PR carries its close-out).
10. REPORT & END — shipped / parked / seams / walls / flags / lessons-baked, every
    claim citing a commit / PR / CI run; the durable copy goes IN THE SESSION PR BODY
    (the heartbeat's parked-PR list points at it) — the chat message alone is
    invisible owner-side. Then END: arm nothing, wake nothing, start nothing — the
    chain terminates with you.

Confirm before ending, in one recital: the landing state of every lane (done, or seam
+ resume pointer); that every merged payload was diff-confirmed and nothing was merged
rushed; the ids you closed, the failsafe id left armed as the successor's bridge, any
business-cron ids recorded (+ next fire), the ids documented uncloseable (+ why); the
retro's path; that no doc you touched still describes the pre-session world; the one
baked improvement (or the honest "none, because X"); and that no new routine was armed
and no new work was started.
```
