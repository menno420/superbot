# 2026-07-09 — Independent cross-repo review of the Projects-EAP fleet

> **Status:** `complete`

## Arc

Owner-directed (2026-07-09): act as the independent review/management session over the whole
Claude Code Projects (EAP) fleet — now four repos (`superbot`, `superbot-next`, `substrate-kit`,
`websites`) built by a team of Projects. Discover everything, give an honest quality verdict,
compare the new repos' structure/efficiency against the mature `superbot` baseline, review the
open PRs, and capture two forward asks (a manager Project; prep for the parallel test-fleet).

1. Read the EAP corpus in order (`current-state` → coordinator kickoff → evaluation guidebook →
   evaluation log → permission-probe report → today's fleet plan → the sent Anthropic email).
2. Added the 3 new repos to session scope (`add_repo`) and fanned out **three discovery agents**
   (one per new repo) over GitHub-MCP (PRs, diffs, CI, trees).
3. **First-party verification:** cloned `superbot-next` and ran its suite + manifest compiler +
   sampled checkers under CI's Python 3.11 — the coordinator's "999 green" claim holds.
4. Shipped the review + the manager-Project brief + new eval-log entries.

## Shipped

- `docs/eap/fleet-review-2026-07-09.md` (new) — the honest verdict, comparison, open-PR reviews,
  first-party verification, and the render/engage cross-repo finding.
- `docs/planning/eap-manager-project-brief-2026-07-09.md` (new, `plan`) — paste-ready founding
  brief for a cross-repo oversight/direction manager Project (leans on the `websites`
  control-plane board; audits via the rebuild audit checklist).
- `docs/planning/projects-eap-evaluation-log.md` — 3 first-party eval entries.
- `docs/planning/README.md` — homed the manager brief.

## Findings (headline)

- Work is genuinely good and **honestly self-assessed** (self-reviews correct their own numbers
  upward; `websites` commissioned an *independent* audit of itself).
- **The one reproducible weakness:** the substrate-kit's decision half transfers cleanly, but the
  **render/engage half strands in every fresh adoption** (`superbot-next` + `websites` both:
  unrendered `${...}` docs, `session_count` 0, `.claude/` inert; `websites` also has no CI on
  main). Root = `adopt` plants-but-doesn't-render/wire; fix belongs upstream in the kit.
- **Verified:** `superbot-next` @ e8d393f → 998 pass / 1 skip (Py3.11), manifest `sha256:b2e5b64…`
  exact, 466 goldens 0 ported. Counts are real; born-red is truthful.

## Context delta

1. **Needed but not pointed to:** the *cross-repo review* flow — `add_repo` → GitHub-MCP across
   repos → cloning a sibling repo to run its tests — isn't in the orientation route; assembled by
   hand. And a real gotcha: **`superbot-next` runs on Python 3.11** (its `ci.yml`), not superbot's
   pinned 3.10 — running its suite under 3.10 produces **75 phantom failures**; under 3.11 it's
   green. That interpreter-per-repo fact deserves a durable home.
2. **Pointed to but didn't need:** the deep binding docs (architecture/ownership/runtime_contracts)
   — irrelevant to a docs/review session; `current-state` + the EAP corpus carried it.
3. **Discovered by hand:** the Python-3.11-for-`superbot-next` interpreter split (above); the kit's
   `adopt` plants-skip-if-exists + banners-but-doesn't-render mechanism (from the kit source),
   which explains the render/engage gap across both fresh repos.
4. **Decisions made alone (reversible; flagged):** graded the four repos (A/B+/…); designed the
   manager Project as *oversight-not-governor* leaning on the existing board + audit checklist;
   chose first-party verification by clone-and-run over trusting the completion report.
5. **Genuine weak point:** website *visual* quality is judged from source only (no render);
   `superbot-next` verification sampled 2 checkers + tests/compiler, not the full 18-checker fleet
   or `bootstrap check --strict`; the parity-status grep matched one `status:` line (structure may
   differ) though "0 ported" holds via the goldens count.

## 🛠 Friction → guard

- **Friction:** running `superbot-next`'s tests under superbot's pinned Python 3.10 (the Stop
  hook's interpreter) yielded 75 false failures — a cross-repo interpreter trap for any future
  review session. **Guard shipped (docs, free to ship):** recorded the Py3.11-per-repo fact in
  this log's Context delta + the review doc's §5 verification table, so the next reviewer runs the
  target repo's suite under *its* CI interpreter. A stronger guard (a per-repo interpreter note in
  `superbot-next`'s own README/CI banner) is that repo's call — flagged to the coordinator.

## ⟲ Previous-session review

The prior session (`2026-07-08-rebuild-audit-checklist.md`) built the rebuild audit checklist but
flagged that it was *untested against a real window*. This session effectively ran that deep pass:
its core discipline — "read the file / run the code, don't trust the commit message" — paid off
directly (it caught the Py3.11 interpreter issue and the render/engage gap by running/reading, not
by trusting reports). **Concrete sharpening for the checklist:** add a step "run the target repo's
suite under *its* CI interpreter, and record each repo's interpreter version" — the exact trap that
cost recovery time here.

## 💡 Session idea

**Make the kit's `adopt` render-and-engage by default, or plant a born-red post-adopt gate** that
stays red until render + `--wire-enforcement` complete — closing the render/engage last-mile gap at
the root (the kit's own "enforce, don't exhort" pattern). Routed to the **kit-lab / `substrate-kit`
repo**, not superbot's idea backlog (it targets a different repo — same handling the prior session
used for the website idea). Captured in the review doc §4/§8 + eval log.

## 📤 Run report

- **Did:** independent cross-repo EAP fleet review + a manager-Project founding brief · **Outcome:** shipped
- **Shipped:** #1887 — the review (`docs/eap/…`) + manager brief (`docs/planning/…`) + eval-log entries
- **Run type:** `manual`
- **⚑ Owner decisions needed:** bless `substrate-kit` #17 (owner-blessing gate — unblocks B1's first benchmark run); decide whether to stand up the manager Project + launch the model-comparison fleet arms (kit-lab + Fable 5 / Opus 4.8 coding arms)
- **⚑ Owner manual steps:** merge `substrate-kit` #17; create the manager Project + the fleet repos (repo/Project creation is owner-only); finish `websites` #16 (or dispatch a session to)
- **⚑ Self-initiated:** none (owner-directed review; the manager brief was an explicit owner ask)
- **↪ Next:** finish `websites` #16 → generalize the adopt render/engage fix into the kit; land the first `superbot-next` parity flip (turn "instrumented" into "proven")

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (this PR #1887 pending) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (kit adopt render-and-engage-by-default) |
| Ideas groomed | 0 |
