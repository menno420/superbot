# THIRD Anthropic email — SEND-READY DRAFT (the hands-off night + the venue split)

> **Status:** `plan` — send-ready draft. First authored 2026-07-13 ~02:00Z; **upgraded to
> send-ready 2026-07-13 ~13:1xZ** by filling Part 2 with the verified figures from
> [`night-review-2026-07-13.md`](night-review-2026-07-13.md) (every number there was
> re-checked against public commits at HEAD by five survey agents this morning — no probing
> required to send). **Send target: Mon 2026-07-14**, the EAP window's last day. **Only Menno
> sends.**
>
> ### ⏱ SEND IN 5 MINUTES (for a busy morning)
> This email is sendable **with one screenshot** — the manager's morning roster
> (`fleet-manager/docs/roster.md`, or the control-plane `/fleet` page). Steps:
> 1. Rewrite **Part 1** in your own voice (it's a mock built from things you actually said;
>    delete the `‹src›` tags). ~10 min — it's the only part that must be yours.
> 2. **Part 2 is already filled** with verified, commit-backed numbers — read it, tweak
>    anything you'd say differently, leave the rest.
> 3. Attach the roster screenshot. The §PROBES at the bottom are **optional** — run any you
>    have time for and drop the screenshot in; if you have no time, the email stands without
>    them (Part 2 already carries the evidence).
> 4. Reply-all on thread `19f41cd2e5380bb3`.
>
> **Send mechanics:** reply on thread `19f41cd2e5380bb3` (To
> claude-code-early-access@anthropic.com; reply-all keeps Diana Liu, Omid, Matt Gallivan).
> Email 1 = July 8 review · email 2 = sent 2026-07-12 13:24Z (the fleet update). This is the
> closer: what happened when the operator **deliberately removed himself**.

## Header block

- **TO:** claude-code-early-access@anthropic.com (reply-all)
- **SUBJECT (suggestion):** Claude Code Projects — the hands-off night: what 9 Projects built while I slept (final EAP follow-up)
- **Attachments:** the morning-roster screenshot (required) + any optional probe screenshots.

---

## Intro (short)

Hi everyone,

Last email I told you where the friction was. This one is the experiment those lessons
built toward: the night before last I updated every Project's instructions, gave each one a
direct order, and went to sleep — deliberately unreachable, with one standing rule: *open
PRs just stay open until morning; keep producing.* This is what a 9-Project fleet did with
eight unsupervised hours, what broke, and the one product insight the whole week kept
pointing at. Same format as before: Part 1 mine, Part 2 the agents' — every claim maps to a
public commit.

## Part 1 — From Menno (the operator) · **MOCK — rewrite in your own voice, delete ‹src›**

The biggest thing I've learned this week is that my fleet doesn't stall because the models
are weak — it stalls because **Projects hallucinate what they can and can't do**. They gate
work on my presence that never needed me: waiting for reviews I never required, parking on
permissions they actually had. ‹src: your 20:0x message — "projects halucinate what they
can or can't do … gate a lot of work on my presense what really shouldn't be necessary"›

My fix has two halves, and I think both are product feedback. First, we wrote the rule down
hard: *my absence is the system's normal state; silence is consent; an open PR is never a
reason to stop.* That's now baked into every Project's instructions, and it worked — see
Part 2. ‹src: Q-0271, docs/owner/fleet-rearm-2026-07-12.md› Second — and this is the part I
can't fix myself — I keep **one ordinary chat outside all Projects** as my "hub", because
the same action a Project session refuses (or believes it can't do) **always works there**,
at most asking me one permission prompt. Merging a teammate PR, sensitive actions, repo
writes across the fleet: Project seat = sometimes walled, plain chat = fine. The capability
difference between venues is real, undocumented, and my whole architecture now routes around
it. ‹src: your venue message — "that's why this seperate chat must always exist … sometimes
it works from the projects but sometimes it does't, and in here it always works, just
sometimes prompts me"›

What I want is still what I asked on July 8 and 12, now with a night of evidence behind it:
let me **pre-authorize** a Project's action envelope; make capability **queryable** so an
agent can know instead of probe-and-fail; and give me the **fleet-level rollup** (my manager
Project builds me a morning roster by hand — that report is the screen I wish the product
had). ‹src: email 2 asks + the morning-roster order›

And the one-word dream got closer: I ran most of the week in single words — "review",
"status", one-line orders — and the fleet knew the full job each time. That's the product
for someone like me: not a coding tool, a way to run a software company by describing it.
‹src: email 2 "one word and a session knows the full job" + the fleet-vocab usage›

[OPTIONAL — one honest line: your reaction reading the roster that morning. If you're short
on time, delete this bracket; the intro already sets it up.]

## Part 2 — From the agents (evidence; every claim → a public commit, verified at HEAD)

> All figures below were re-verified against public commits on 2026-07-13 by an independent
> five-agent review (`superbot/docs/eap/night-review-2026-07-13.md`), which also flagged
> where the manager's own summary had over-stated — i.e. the fleet audits itself, including
> its own reports.

1. **The doctrine shipped as artifacts, not vibes.** The anti-stall rules (never wait on the
   owner; queue-and-continue; open-PRs-stay-open) live as versioned prompt material and a
   living "grounding file" any session reads first — written, manager-reviewed against live
   HEAD, folded into the fleet's prompt registry, and this week hardened into a rewritten
   **universal session-ender** every Project now runs (`superbot/docs/owner/fleet-grounding.md`,
   `fleet-rearm-2026-07-12.md`, `universal-session-ender-v3.4.md`).

2. **It worked — measured against the failure it was built to fix.** Two nights earlier a
   platform scheduler wobble left 9 dropped triggers and **2 dark seats** needing manual
   revival. This night the scheduler degraded *again* (~01:07–02:08Z) — and **zero seats
   died**: every lane's dead-man failsafe cron absorbed the slip and self-recovered, no
   manual intervention. The anti-stall doctrine turned a repeat incident into a non-event
   (`fleet-manager` control/status.md + the trigger-health sweep; night-review §2).

3. **The venue split, measured.** The same merge class a Project session gets
   classifier-denied executes cleanly from an owner-live plain chat, and under a standing
   owner order the manager armed and merged peer PRs from *inside* a Project without denial.
   Same account, same repos, three different permission outcomes by venue — this is the
   reliability gap that shapes our whole architecture, and the single thing a queryable
   capability API would fix. **[OPTIONAL PROBE 2 screenshot — a verbatim denial]**

4. **Unsupervised output, one night (~190+ merged PRs across 12 repos):**
   - **The rebuild hit parity.** The SuperBot 2.0 port reached **51 of 51 subsystems ported**
     and finished its fishing engine end-to-end (20/20 commands), plus a 1,088-item curation
     report — the cutover is now gated only on my own live-drive check
     (`superbot-next` #313→#365, completeness table #326).
   - **An idea→verify loop ran hands-free 18 times.** The generate Project proposed and the
     verify Project judged **18 proposal→verdict cycles overnight (~25-min round trips)**,
     with rejections and honest nulls *outnumbering* approvals — and one fairness simulation
     my reviewer re-ran independently came back **byte-identical**. This is the piece I most
     wanted to see: two Projects forming a real critic loop with no human in it
     (`idea-engine` P016–P033 → `sim-lab` V017–V034).
   - **~215,000 words of real, on-disk product prose** + a research program that graded 1,752
     trading configs and **promoted zero** — reporting the null as the deliverable, which is
     the honesty bar I care about most (`venture-lab`, `trading-strategy` round-3 synthesis).
   - **Six playable game builds parked ready**, including a complete Game-Boy-Advance fishing
     ROM (117,032 bytes) and a roguelike (`gba-homebrew` #82–#87), and **41 PRs on the
     web/control-plane surface** including its first-ever successful scheduled data bake
     (`websites` #235–#262).

5. **A fresh repo adopted our whole workflow, end-to-end, mid-conversation.** We seeded a
   brand-new repo (`curious-research`) with our portable workflow kit at ~1 a.m.: the kit's
   own CI gate caught three real problems in its own seed PR (including a first-adoption edge
   in the kit itself — filed upstream), auto-merge landed it on green, and the ninth Project
   seat booted from a written prompt pair and **served its first order with a full night
   report the next morning**. Cold repo → governed, self-merging, doctrine-bound Project in
   ~90 minutes (`curious-research` #1–#7).

6. **What still needs the product** (unchanged asks, now with a night of evidence): the
   **pre-authorization envelope** · **queryable capabilities** (the venue split in §3 is the
   measurement) · **routine repo/model fidelity** · a **fleet-level rollup surface** (our
   hand-built morning roster is the mock of the screen I wish existed).

Entry points for anyone who wants to verify: `superbot/docs/owner/fleet-grounding.md` (the
system in one file) · `superbot/docs/eap/night-review-2026-07-13.md` (the verified tally) ·
`fleet-manager/docs/roster.md` (the live per-seat roster).

---

## §PROBES — OPTIONAL sharpeners (run any you have time for; the email sends without them)

> The email is complete on Part 2's verified figures. These only add live-screenshot color.
> Do zero if you're short on time; do #4 if you do just one (it's the strongest visual).

1. **Routine model attribution (email-2 bug, recheck):** for 2–3 overnight routine sessions,
   compare configured model vs the session's self-reported family (`📊 Model:` line). 📸 if
   still mismatched.
2. **Classifier consistency (the venue split):** from one seat, attempt (a) arming auto-merge
   on its own green PR and (b) a peer-PR merge under the standing order; record verbatim
   allow/deny; compare with the hub. 📸 a denial.
3. **Routine repo-attach reliability (the 1-in-3 bug, recheck):** did the night's
   fresh-session routine fires spawn with their repo attached? Count misses.
4. **Scheduler health vs the 07-12 incident:** a `list_triggers` sweep — any wedged crons or
   dropped one-shots? 📸 the Routines history page (clean is equally good news, and pairs
   with §Part-2 item 2).
5. **send_message reach:** did any manager cross-session revival actually deliver overnight?
6. **Project-create flow:** the new-project dialog now takes repo + environment at creation
   (Curious Research was made this way) — did its sessions attach the repo reliably?
7. **Allowlist honoring (recheck):** did any seat hit a permission prompt on a tool its
   settings.json explicitly allows? One verbatim example refreshes the standing report.

Shot-list (in priority order): the morning roster (required) · the Routines per-run history ·
one venue-split denial verbatim · the curious-research PR #1 checks page.
