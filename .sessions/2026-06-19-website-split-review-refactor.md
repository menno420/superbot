# 2026-06-19 — Website two-site split: ultracode review-and-refactor pass

> **Status:** `complete`

Owner-directed **ULTRACODE review** of the website two-site-split build (#1109, #1110, #1112,
#1113, #1116, #1117, #1118, #1119) — read+verify every line, refactor what is wrong/fragile/
duplicated, keep everything dormant-by-default and `disbot/`-runtime untouched. Born-red while the
refactor units land; flipped to `complete` as the deliberate final step.

## What I'm about to do (declared up front)

File-disjoint refactor units (each green on `check_quality --full` + `check_architecture --mode
strict` before the card flips):

1. **Test isolation (confirmed CI bug).** `botsite/` and `dashboard/` both deploy with Root
   Directory = their own folder and import siblings by **bare name** (`import submissions_db` /
   `ratelimit`) after a `sys.path` shim. In a single test process that loads *both* apps those bare
   names collide in `sys.modules` — the bot-site INSERT-only `submissions_db` (no `set_status`)
   shadows the dashboard one, so `tests/unit/dashboard/test_moderation.py` blows up when it runs
   after `tests/unit/botsite`. Fix: a shared, run-order-robust `tests/support/web_app_loader.py`
   that isolates each app's bare sibling imports (centralises the duplicated loader boilerplate too).
2. **`botsite/submissions_db._clean` C1 hardening.** It claims to drop "C0/C1 control chars" but
   C1 (e.g. `\x85` NEL, `\x9b` CSI) survive. Make it strip *all* control chars (keep `\n`/`\t`).
3. **Idea→subsystem heuristic mis-mapping.** Build the greenlit explicit-`Subsystem:` tag mechanism
   (parse + prefer-tag + registry-validated warning) and tag the confirmed false-positive (the
   agent-workflow "executor self-chaining" idea cross-matched the **Word Chain** game's `chain`
   subsystem). Regenerate `site.json`.
4. **env-vars.md marker-aware generator.** The hand-maintained "Website tier" section the docs claim
   was added by P8, then deleted by #1119 to unblock main (byte-equality freshness test). Teach
   `scan_env_usage.py` + the two verifiers about an end-marker so a hand tail coexists; restore the
   Website-tier section; fix the now-stale doc claims.

Plus the written **review report** (`docs/operations/website-split-review-2026-06-19.md`) and the
**flag-for-owner** items (web-ci matrix consolidation; moderation double-file race; the broader
80-idea subsystem mapping).

## Shipped (this PR)

Every line of #1109–#1119 was read and **verified against source**; the four hard invariants were
*proven* (decoupling via grep + `check_architecture`; redaction fail-closed via injected-key tests;
security via the mirror/owner-gate/escaping reads; dormancy via the `is_configured` gates), and the
four known weak spots were exercised. Result: the build is sound; four contained defects were fixed.

- **Test isolation (confirmed CI bug)** — `tests/support/web_app_loader.py` + 7 fixtures. Root cause:
  bare-name `sys.modules` collision (`submissions_db`/`ratelimit`) between the two web services; the
  bot-site INSERT-only `submissions_db` shadowed the dashboard's → `test_moderation` broke when it ran
  after `tests/unit/botsite`. Now order-independent (verified both directions, 164 web tests).
- **`botsite/submissions_db._clean` C1 hardening** — the docstring claimed C1 was dropped but
  `\x80–\x9f` (NEL/CSI) survived; now `unicodedata` `Cc` + a regression test.
- **Idea→subsystem `chain` mis-map** — built the greenlit explicit `Subsystem:` tag (header-only parse,
  prefer-over-heuristic, `none` sentinel); tagged the executor-chain idea → the 7 Word-Chain commands
  flip `finished` (verified surgical: exactly those, nothing else). README convention note.
- **`env-vars.md` web-tier marker** — `END_MARKER` lets the generated head + a hand-maintained
  Website-tier tail coexist (the #1119 footgun); both verifiers compare head-only; tail restored.
- **Review report** + **current-state ledger** (#1112–#1119 recorded on sight, Q-0166).

## Verification (green)

- `python3.10 scripts/check_quality.py --full` → **All checks passed ✓** (10972 passed, 37 skipped —
  web tests *ran*, not skipped, since the deps were installed locally; mypy `disbot/` clean).
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0** (no web-tier violations).
- `check_docs --strict`, `check_dashboard_data --site`, `check_generated_artifacts_fresh`,
  `check_current_state_ledger --strict` → all green. Generated artifacts regenerate identically
  (modulo the volatile build-meta/timestamp); the env-vars regen is idempotent.

## ⚑ Self-initiated (Q-0172 accountability)

- Promoted the **explicit `Subsystem:` tag** idea (`idea-subsystem-tag-on-ideas-2026-06-19.md`) →
  implementation this session (greenlit small/decided lane; additive + reversible). No owner approval
  gate (idea-gate per Q-0172); flagged here for review.

## Flag-for-owner (decisions — not guessed; full context in the review report)

1. **Moderation approve double-file race** — two concurrent approves could create two GitHub issues
   (DB guards prevent double-status, not double-issue). Low risk (single owner + CSRF + rate-limit).
   Recommend accept-for-v1; alternatives in the report.
2. **Web-CI matrix consolidation** (`web-ci.yml` + auto-managed-PR predicate de-dup) — a clean win the
   centralization proposal wants as its own *verified* focused PR; left flagged, not bundled here.
3. **Full ~80-idea subsystem mapping** — the mechanism is in; mapping every idea is the owner-paced
   `idea-to-cog-command-mapping` batch effort, not this pass.

## 💡 Session idea (Q-0089)

**Render the command `status` badge from a per-command `Subsystem:`-style override, not only the
subsystem-wide signal.** Today every command in a subsystem shares one `finished`/`in-progress` badge
(derived from the subsystem's open work) — so one open idea marks *all* of a cog's commands in-progress.
A tiny optional per-command override (a curated map, or a `status:` hint where a command's maturity
genuinely differs from its cog's) would make the headline maturity badge honest at the command level,
not just the cog level. Cheap, additive, reuses the redaction lens. Not yet captured — noting here;
dedup-grepped `docs/ideas/` (the existing tag/mapping ideas are about *linking*, not *per-command
status granularity*).

## ⟲ Previous-session review (Q-0102)

The previous session (**P7+P8 docs**, `2026-06-19-website-deploy-redaction-docs.md`) did the redaction
audit + deploy docs well and honestly flagged its env-vars.md "prose not table, on purpose" decision —
but that decision was the *symptom* of an unsolved root cause: the generator clobbers any hand tail, so
"prose" only delayed the collision (#1119 then deleted the section to unblock main). It should have
either (a) built the marker-aware generator then (the real fix, done this session) or (b) *not* claimed
in three docs that a section existed which the very next freshness run would delete. **System
improvement surfaced + acted on:** a generated doc that needs a hand-maintained companion should ship
the *coexistence mechanism* (an end-marker the verifiers respect) in the same PR — never a hand edit
the generator will silently revert. The marker pattern here is reusable for any future
generated+hand-curated doc; worth lifting into the generated-doc convention if a third case appears.

## Documentation audit (Q-0104)

`check_current_state_ledger --strict` green (#1112–#1119 recorded); new docs reachable
(`check_docs --strict` green — the review report linked from the plan §9); owner-relevant decisions
captured as the three flag-for-owner items above (surfaced to the owner via the PR, not silently
decided). Nothing from this session lives only in chat.
