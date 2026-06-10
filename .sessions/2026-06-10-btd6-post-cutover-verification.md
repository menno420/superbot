# 2026-06-10 — BTD6 post-cutover verification (PR #655)

**Task:** "verify everything that we have now correctly fetched from the data
dump, verify that everything is answerable by the AI as well as through the
btd6 menu" — the verification pass over the merged #649 cutover. (The session
opened on the decode backlog; the maintainer redirected to verification first —
the backlog items stay queued in decode-status ⭐.)
**Shipped:** PR #655 — verification green on all five axes (dump fidelity ·
runtime tests · AI tools · menu renders · live boot) + fixes for the four real
findings: mode-rules dark data (shared `utils/btd6/mode_rules.py`, wired into
`btd6_mode_lookup` + the modes embed), the `!btd6 diagnostics` HTTP-400
(86-map field > 1024), the version-stamp-rot class (overlays re-stamp on
verified runs; towers/heroes/rounds bumped to 55.1 on audit/parity evidence;
`btd6_answerability` now reports 55.1), and the absolute-container-path leak in
`data_source_label()`. Technical detail: decode-status §"Session log —
post-cutover verification (PR #655)"; the new answerability gaps are backlog
items 5–6 there.

## Process learnings (the durable part)

- **"Regenerate everything and demand a clean `git status`" is the strongest
  cheap fidelity check** — it caught the one drift (maps.json's missed 55.1
  stamp) that the value-comparing audit structurally cannot see.
- **Drive every builder, not samples.** 2,022 embeds + 43 tool probes cost
  ~2 minutes of runtime and found a real send-breaking bug (Discord 400s
  oversized fields; it does not truncate). The existing test suite (1,579
  BTD6 tests) was green the whole time — coverage of *limits* and *surface
  wiring* is what was missing, not value correctness.
- **Probe your probes:** 8 of my first battery's 9 "failures" were my own
  wrong tool-argument shapes / comma-formatted expectations. Diff a failing
  probe against the tool spec before believing it; two "missing data" findings
  (BAD health, minion stats) dissolved on inspection.
- **The "0 corrections" overlay trap:** a writer that only rewrites on value
  changes silently lets metadata (the version stamp) rot one game version
  behind. Verified-at-a-version IS information — re-stamp every verified run.

## Context delta (reflection interview)

- **Route miss:** nothing material — CLAUDE.md → current-state → decode-status
  ⭐ led straight to the right starting state; the PR-merge check
  (`list_pull_requests` → `pull_request_read`) confirmed #649 merged before I
  trusted the docs.
- **Route excess:** I read the full carry-forward merge layer (~540 lines)
  before the maintainer redirected to verification — right call for the
  original task, wasted for the redirected one. Cheap lesson: confirm the
  session goal before deep source reading when the prompt says "continue".
- **Discovered by hand:** the tool-handler calling convention (`build_registry`
  → handlers dict → plain async fns on an args dict) — easy once found, but no
  doc states "how to drive AI tools deterministically in a smoke"; it's now
  demonstrated in this PR's body + the decode-status log.
- **Decisions made alone (all contained/reversible):** counts-only Maps
  diagnostics field (roster's one home = build_maps_embed); bumping
  towers/heroes/rounds stamps on audit/parity evidence while leaving `source`
  lineage untouched; routing the deterministic-Ask domain gaps to the backlog
  instead of half-building a second intent router.
- **Weak point of what shipped:** menu "answerability" was verified by
  building the embeds the menu produces, not by clicking the live panels —
  button → builder wiring is pinned by existing view tests, but the
  maintainer's live spot-check (backlog item 4) remains the real-world half.
- **One change that would have helped:** an embed-limits assertion inside the
  existing render tests (now exists for diagnostics; the smoke script pattern
  in the PR body generalizes if another surface grows).

## Grooming pass (Q-0015)

This session closed the decode-status backlog's teed-up mode-rules item and
routed two new precise items (5: deterministic-Ask domain gaps, root-cause
direction included; 6: minion-name resolution + label polish) — the backlog is
groomed in place. No new `docs/ideas/` entries warranted.

**Resume point:** decode-status ⭐ — backlog item 1 (carried-forward mechanism
decodes; the original plan for this session, untouched) or item 5 if the
maintainer wants menu answerability parity first. PR #655 review = the diff.

## Continuation (same session): the carry-forward decode pass

The maintainer said "you can continue" → executed decode-status backlog
item 1 end-to-end in the same PR: **all six carried-forward mechanisms are
now mapper-decoded and `_CUTOVER_CARRYFORWARD` is empty; the audit reads
91 CLEAN · 0 DELTA · 0 SUSPECT** (the mapper reproduces 100% of every
committed file). Per-mechanism evidence + premise corrections + the additive
`*Bonus*`+1 transform live in decode-status' decode-pass session log; new
data shipped along the way (druid-paragon thorn rings, sentry combat +
lifespans, striker L7–17/L18+ hole fills, `cashbackMaxPercent`).

Additional process learnings:
- **Hermetic minimal fixtures catch what real-data regen can't:** the
  blanket name-excluded dedupe looked fine on real data (all real variants
  differ in combat) — the bare test fixtures collapsed and exposed the
  latent class. Scope a dedupe to the structures that need it.
- **The backlog's own notes needed source-verification** (two premise
  corrections above) — "verify cross-agent output" applies to your own
  prior session's backlog notes too.

**Resume point (updated):** decode-status ⭐ item 2 (banana-economy decode)
is the next decode slice; items 5–6 (deterministic-Ask domains; hero-buff /
paragon-subtower surfaces + label polish) are the answerability lane.
