# 2026-07-08 — Rebuild-direction: owner router answers + audit checklist

> **Status:** `complete`

## Arc

Continuation of the rebuild-direction management-layer session
([handoff](../docs/planning/rebuild-direction-handoff-2026-07-08.md)). This slice:

1. Pulled the rebuild Project's live state directly from GitHub (`superbot-next` +
   `substrate-kit`, added to session scope) rather than waiting for a pasted status
   report — 29 PRs merged in `superbot-next` (kernel K0–K9, layer V, K10, port bands 1
   into 2), 2 in `substrate-kit` (kit populated, now dormant). Spot-checked
   `tools/manifest_compile.py` against its commit-message claims — held up.
2. Ran all six pending `docs/question-router.md` blocks in `superbot-next` through the
   owner via `AskUserQuestion` (S11 rubric-v2, S13 credential lifecycle, S14 backup/DR,
   S15 platform governance, V-5 verified_live, K10 AI kernel) and pushed the answers
   back (`superbot-next` PR #30, merged).
3. Added `.github/CODEOWNERS` to both `superbot-next` and `substrate-kit` (PR #31, #3 —
   merged) so the owner's pending branch-protection pass has something to enforce.
4. Wrote a repeatable audit checklist
   (`docs/planning/rebuild-project-audit-checklist-2026-07-08.md`) for confirming the
   Project's work is directing correctly *and* spec-correct, not just trusting commit
   messages — grew directly out of two things caught by reading source instead of
   prose: `superbot-next/docs/current-state.md` is still the unfilled kit template, and
   the V-5 router block re-asked a question `superbot`'s own router (Q-0244) already
   ruled.
5. Fixed a pre-existing `docs/planning/README.md` homing gap: the handoff doc
   (`rebuild-direction-handoff-2026-07-08.md`) was never indexed — fixed on sight per
   Q-0166, alongside adding the new checklist doc.

## Shipped (this repo)

- `docs/planning/rebuild-project-audit-checklist-2026-07-08.md` (new).
- `docs/planning/README.md` — added missing handoff-doc row + the new checklist row.

## Shipped (other repos, via this directing session)

- `superbot-next` #30 — router answers.
- `superbot-next` #31 — CODEOWNERS.
- `substrate-kit` #3 — CODEOWNERS.

## Findings flagged back to the coordinator (not this repo's job to fix)

- `superbot-next/docs/current-state.md` unmaintained (still template) — flagged, not
  fixed directly (out of this session's write scope by convention; the coordinator
  owns that repo's docs).
- V-5(a) router-hygiene gap — a block re-asked an already-ruled question. Recorded in
  the routing-result text of `superbot-next` PR #30 itself.
- `superbot-next` has no `auto-merge-enabler` workflow (unlike `superbot`) — PRs there
  merge via direct API call, not native auto-merge. Flagged to the owner in-chat, not
  built here (coordinator's repo, coordinator's call).

## Mistake caught mid-session (kept in the checklist as a live lesson)

A `create_or_update_file` call to push the router answers was first issued with a
placeholder string (`*** see file content above ***`) instead of the real ~13 KB body
— the API accepted it silently (30-byte file, no error). Caught immediately by
checking the returned `size` field and fixed with a follow-up commit before the PR was
opened. This is now checklist item B: "no file a commit message describes at length
turns out to be a stub — file size after push is a real signal."

## Context delta

1. **Needed but not pointed to:** nothing genuinely missing this slice — the two prior
   docs (handoff + kickoff) fully oriented the work; the gap was in the *target*
   repos' docs, not this repo's orientation.
2. **Pointed to but didn't need:** n/a.
3. **Discovered by hand:** the `golden-parity.yml` workflow file's own inline comment
   (`👤 OWNER: designate THIS job as the required status check ... report job must NOT
   be required`) is the single most load-bearing piece of operational knowledge for
   the owner's pending repo-settings pass, and it lives only in a code comment in
   `superbot-next`, not in any doc a director would think to read first. Worth a
   pointer from this repo's handoff doc next time it's touched.
4. **Decisions made alone:** none beyond what the owner explicitly ratified via the
   question panel this session; the CODEOWNERS blanket-ownership choice (`* @menno420`)
   was a low-stakes default, not flagged separately.
5. **Genuine weak point:** the audit checklist itself is untested — it hasn't yet been
   run as a "deep pass" against a real 10-PR window. Next session directing this
   Project should do that pass and report whether the checklist actually catches
   anything, or needs sharpening.

## ⟲ Previous-session review

The prior session (`7f7628e`, handoff creation) correctly scoped a management-only
role and captured live state accurately — the coordinator's actual PR history matched
the handoff's description closely. One thing it could have done better: it didn't
anticipate that the *next* session would need to independently verify the target
repos' GitHub state rather than wait for a pasted report, so it didn't pre-stage repo
access or note that `add_repo` would be needed. Improvement shipped this session: the
audit checklist itself, so future directing sessions don't have to reconstruct
"how do I know it's actually correct" from scratch each time.

## 💡 Session idea

A **status dashboard website** for the rebuild — see the separate website-Project
planning conversation this session; not filed as a `docs/ideas/` entry here because
it targets a different repo/Project entirely (its own planning artifact lives with
that Project, not `superbot`'s idea backlog).

## Flagged for maintainer

- Do the repo-settings pass on `superbot-next` + `substrate-kit` (runbook given
  in-chat: required checks are `ci / *` + `golden-parity / gate` only — never
  `golden-parity / report`).
- Decide on the new website-Project scope (separate planning doc/conversation).
