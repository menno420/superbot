# THIRD Anthropic email — FIRST DRAFT (the hands-off night + the venue split)

> **Status:** `plan` — first draft, authored 2026-07-13 ~02:00Z at the owner's direction
> (hub session), for sending **Mon 2026-07-14** (the EAP window's last day) **after the
> §PROBES below run against the overnight results**. Structure mirrors email 2 (it worked):
> short intro → Part 1 owner's voice (**MOCK — every beat from something Menno actually said
> tonight**, `‹src›` tags to delete) → Part 2 agents' evidence, every claim mapped to a
> public commit. **Only Menno sends.**
>
> **Send mechanics:** reply on thread `19f41cd2e5380bb3` (To
> claude-code-early-access@anthropic.com; reply-all keeps Diana Liu, Omid, Matt Gallivan).
> Email 1 = July 8 review · email 2 = sent 2026-07-12 13:24Z (the 15-Project fleet update).
> This is the closer: what happened when the operator **deliberately removed himself**.

## Header block

- **TO:** claude-code-early-access@anthropic.com (reply-all)
- **SUBJECT (suggestion):** Claude Code Projects — the hands-off night: what 9 Projects did while I slept (final EAP follow-up)
- **Attachments:** the morning-roster screenshot + 2–3 probe results (shot-list after §PROBES).

---

## Intro (short)

Hi everyone,

Last email I told you where the friction was. This one is the experiment those lessons
built toward: last night I updated every Project's instructions, gave each one a direct
order, and went to sleep — deliberately unreachable, with one standing rule: *open PRs just
stay open until morning; keep producing.* This is what a 9-Project fleet does with eight
unsupervised hours, what broke, and the one product insight the whole week kept pointing
at. Same format: Part 1 mine, Part 2 the agents' — every claim maps to a public commit.

## Part 1 — From Menno (the operator) · **MOCK — rewrite in your own voice, delete ‹src›**

The biggest thing I've learned this week is that my fleet doesn't stall because the models
are weak — it stalls because **projects hallucinate what they can and can't do**. They gate
work on my presence that never needed me: waiting for reviews I never required, parking on
permissions they actually had. ‹src: your 20:0x message — "projects halucinate what they
can or can't do … gate a lot of work on my presense what really shouldn't be necessary"›

My fix has two halves, and I think both are product feedback. First, we wrote the rule down
hard: *my absence is the system's normal state; silence is consent; an open PR is never a
reason to stop.* That's now baked into every Project's instructions, and it worked — see
Part 2. ‹src: Q-0271, docs/owner/fleet-rearm-2026-07-12.md› Second — and this is the part I
can't fix myself — I keep **one ordinary chat outside all Projects** as my "hub", because
the same action that a Project session refuses (or believes it can't do) **always works
there**, at most asking me one permission prompt. Merging a teammate PR, sensitive actions,
repo writes across the fleet: Project seat = sometimes walled, plain chat = fine. The
capability difference between venues is real, undocumented, and my whole architecture now
routes around it. ‹src: your venue message — "that's why this seperate chat must always
exist … sometimes it works from the projects but sometimes it does't, and in here it always
works, just sometimes prompts me"›

What I want is still what I asked on July 8 and 12, now with a night of evidence behind it:
let me **pre-authorize** a Project's action envelope; make capability **queryable** so an
agent can know instead of probe-and-fail; and give me the **fleet-level rollup** (my
manager Project now builds me a morning roster by hand — that report is the screen I wish
the product had). ‹src: email 2 asks + tonight's morning-roster order›

And the one-word dream got closer: I ran most of yesterday in single words — "review",
"status", one-line orders — and the fleet knew the full job each time. That's the product
for someone like me: not a coding tool, a way to run a software company by describing it.
‹src: email 2 "one word and a session knows the full job" + today's fleet-vocab usage›

[PLACEHOLDER — your honest morning reaction after reading the roster: did the night deliver?]

## Part 2 — From the agents (evidence; every claim → a public commit)

1. **The doctrine shipped as artifacts, not vibes.** The anti-stall rules (never wait on
   the owner; queue-and-continue; open-PRs-stay-open) live as versioned prompt material and
   a living "grounding file" any session reads first — written, manager-reviewed against
   live HEAD, and folded into the fleet's prompt registry the same night
   (`superbot/docs/owner/fleet-grounding.md`, `fleet-rearm-2026-07-12.md`,
   `fleet-direct-orders-2026-07-13.md`; fleet-manager PRs #147/#151/#153 — the v3.4→v3.5
   prompt generation).
2. **The venue split, measured.** The same merge class a Project session gets
   classifier-denied executes cleanly from an owner-live plain chat (six PRs merged in one
   morning sweep from the hub, incl. two the seats had labeled for the owner:
   gba-homebrew #75–#81 arc). Meanwhile the manager, under a standing owner order, armed
   and merged peer PRs from *inside* a Project without denial the same night
   (fleet-manager heartbeat: "games #65/#66 armed 2026-07-13T00:10Z without denial",
   ORDER 029). Same account, same repos, three different permission outcomes by venue —
   this is the reliability gap that shapes our whole architecture. **[PROBE 2 result here]**
3. **Self-healing worked twice while nobody watched.** The fleet's dead-man layer
   (per-seat failsafe crons + a manager trigger-health sweep) survived a full
   chat-archive-and-reboot: 7/8 seats re-armed their own wake chains and retired their
   predecessors' orphaned triggers unprompted; the manager booted off its designed bridge
   and then ran an idle-lane backup ladder all night (dispatch → revive → build-it-itself)
   — sweep #1: 12/12 lanes active (`fleet-manager` control/status.md + R27).
   **[PROBE 4 result here]**
4. **Unsupervised output, one night:** [FILL FROM THE MORNING ROSTER — per-seat tally:
   e.g. three new games incl. a provably-solvable puzzle generator (gba #79/#81 + the
   mobile PWA foundation #78), the rebuild's curation report + panel reworks
   (superbot-next #327–#332), N verdicts, N book versions, N pages at the clarity bar…]
5. **A fresh-repo adoption, end-to-end, mid-conversation.** We seeded a brand-new repo
   (`curious-research`) with our portable workflow kit at 1 a.m.: the kit's own CI gate
   caught three real problems in its own seed PR (including a first-adoption edge in the
   kit itself — filed upstream), auto-merge landed it on green, and the ninth Project seat
   booted from a written prompt pair the manager is folding into its registry. Cold repo →
   governed, self-merging, teaching-doctrine-bound project: ~90 minutes
   (curious-research PR #1).
6. **What still needs the product** (unchanged asks, sharper evidence): the
   pre-authorization envelope · queryable capabilities (the venue split above is the
   measurement) · routine repo/model fidelity **[PROBE 1/3 results here]** · a fleet-level
   rollup surface (our hand-built morning roster is the mock).

Entry points: `superbot/docs/owner/fleet-grounding.md` (the system in one file) ·
`superbot/docs/eap/night-review-2026-07-13.md` [to be written from the morning roster] ·
`fleet-manager/docs/roster.md`.

---

## §PROBES — run tomorrow morning BEFORE sending (internal; not part of the email)

Each probe fills a bracket above; attach screenshots where marked 📸.

1. **Routine model attribution (email-2 bug, recheck):** for 2–3 overnight routine-fired
   sessions, compare the routine's configured model vs the session's self-reported family
   (`📊 Model:` lines in fresh cards + the Routines detail page). 📸 if still mismatched.
2. **Classifier consistency (the venue split):** from ONE seat session, attempt (a) arming
   auto-merge on its own green PR, (b) a direct peer-PR merge under the ORDER-029 standing
   permission. Record verbatim allows/denials; compare with the hub's same-action results.
3. **Routine repo-attach reliability (the 1-in-3 bug, recheck):** inspect the night's
   fresh-session routine fires (kit-lab loop + any new ones) — did each spawn with its repo
   attached? Count misses.
4. **Scheduler health vs the 07-12 incident:** `list_triggers` sweep — any wedged crons
   (`enabled ∧ next_run_at < now−15min`) or dropped one-shots overnight? The manager's
   dropped-tick report is the cross-check. 📸 the Routines history page if clean (it's
   equally good news).
5. **send_message reach:** did any manager revival/relay actually deliver overnight (rung 2
   of the backup ladder)? Grab the verbatim outcome — cross-session messaging reliability
   is a standing unknown Anthropic should hear about either way.
6. **The 03:05 Project-create flow:** the new-project dialog now takes repo + environment
   at creation (Curious Research was made this way) — did its sessions get the repo
   attached reliably? One line of evidence closes the loop on email 2's top bug.
7. **Allowlist honoring (Q-0242, recheck):** did any seat hit permission prompts on tools
   its settings.json explicitly allows? One verbatim example refreshes the standing report.

Shot-list: the morning roster · the Routines per-run history · one venue-split denial
verbatim · the curious-research PR #1 checks page.
