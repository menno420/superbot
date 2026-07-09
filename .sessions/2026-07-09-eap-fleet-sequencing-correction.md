# 2026-07-09 — EAP fleet sequencing correction: kit-lab governs real repos, test fleet trimmed to 2

> **Status:** `complete`

## What I did

The previous session's fleet plan (`docs/planning/eap-project-fleet-2026-07-09.md`, PR #1877)
treated kit-lab as one of 11 roughly co-launched Projects. Owner correction, live in this
session: kit-lab is not a peer of the domain-breadth test fleet — it's the long-term manager of
the **real production repos** (superbot, superbot-next, botsite), per the already-decided
founding plan (`kit-lab-founding-plan-2026-07-07.md`, KF-1…KF-11), unchanged. The
domain-breadth fleet (games/bots/research/coding/design/personal/wildcard) is a separate,
throwaway EAP capability-eval exercise that kit-lab does not govern.

Owner's sequencing: launch kit-lab first (per its existing provisioning checklist), then launch
**2** test-fleet projects to run independently alongside it — not all 11 — and revisit tomorrow
whether to add more. Owner picked the coding-tool task run on **Fable 5 and Opus 4.8** (not the
originally-suggested Sonnet 5) as the 2 — i.e. collapse the 3-model comparison to the two
higher-tier models, dropping Sonnet 5 from today's launch.

Updated `docs/planning/eap-project-fleet-2026-07-09.md` with a "Corrected launch scope" section:
kit-lab launches alone first via its existing §7.2 checklist and keeps its original mandate
(manage the real program repos, unchanged); the domain-breadth test fleet is a separate,
throwaway eval that kit-lab does not govern; today's actual launch list is trimmed to kit-lab +
2 coding-tool-lab Projects (`codetool-lab-fable5`, `codetool-lab-opus48` — Sonnet 5 arm dropped
for today), with the remaining 5 domain rows + the Sonnet arm explicitly deferred to a
tomorrow capacity decision rather than pre-committed. No repos were created and no Projects were
launched in this session — those are owner UI/portal actions per the existing checklists; this
was docs-only.

## Context delta

- **Needed but not pointed to:** none beyond what the fleet doc already had — the correction was
  a scope/sequencing clarification from the owner, not a missing-doc gap.
- **Pointed to but didn't need:** n/a.
- **Discovered by hand:** n/a — this was a direct owner correction in-chat, recorded verbatim
  rather than reverse-engineered.
- **Decisions made alone:** picked the coding-tool row (over games/design/wildcard) as the
  "most important" 2-project pick was the owner's explicit call, not mine — I only proposed the
  menu via AskUserQuestion and recorded the answer (Fable 5 + Opus 4.8, dropping Sonnet 5).
- **Flagged for maintainer:** the original fleet doc's 7-row menu and model-comparison section
  are left intact as the reference menu for tomorrow's decision — only the "what launches today"
  framing changed. If tomorrow's session wants a genuinely different subset than "coding twice,"
  it should feel free to deviate; nothing here locks that in.
- **One docs/tooling change that would have most helped:** none identified this session — the
  fix was a two-paragraph doc edit, no tooling gap surfaced.
- **Friction → guard:** none — no workflow friction hit this session (pure planning-doc
  clarification, no code/CI surface touched).

## 💡 Session idea

None new this session — the work was a scope correction on an already-planned fleet, not fresh
ground; forcing a filler idea would violate the "no ceremony" bar (Q-0089).

## ⟲ Previous-session review

The previous session (PR #1877, fleet plan authoring) did good, honest work — it explicitly
flagged "11 is a lot to monitor" as the owner's call rather than silently picking a subset, which
is exactly what let this session's correction land cleanly. What it could have done better: it
conflated kit-lab (a permanent, real-repo-governing Project) with the 7 throwaway domain
evals into one undifferentiated "fleet of 11," which is what needed unwinding today. Concrete
system improvement this surfaces: when a planning doc mixes a **permanent infrastructure
Project** with **throwaway eval Projects** in the same table/count, it should say so explicitly
in the doc's own framing (a one-line "kit-lab is not a fleet peer" caveat in the original doc
would have caught this before it reached chat) — noted here rather than turned into a new
checker, since this is a one-off planning-doc pattern, not a recurring mechanical failure mode.

## Documentation audit

`docs/current-state.md` does not need a new entry — no PR has merged from this session yet and
no runtime/code changed; the fleet plan doc itself is the durable home for this decision, and it
now carries the correction in place rather than needing a pointer elsewhere.
