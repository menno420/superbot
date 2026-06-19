# 2026-06-19 — Website two-site split: ultracode review-and-refactor pass

> **Status:** `in-progress`

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
