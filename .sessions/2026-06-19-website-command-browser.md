# 2026-06-19 — Website: interactive command browser (S1.1 + P2)

> **Status:** `complete`

**Run type:** `routine · ultracode`
**⚑ Self-initiated:** none (owner-dispatched ultracode build of plan units S1.1 + P2)

## Arc

The headline user-facing deliverable of the website two-site split
(`docs/planning/website-two-site-split-plan-2026-06-19.md` §5 + the "Site identity &
experience" brief): units **S1.1** (enrich the per-command data) + **P2** (the interactive
command + feature browser). Foundation S1+S2+P1 merged (#1109); owner identity brief merged
(#1110). Built end-to-end on `claude/website-command-browser` → PR **#1112**.

**Exclusive file set only** (9 files): the producer's command projection + the guard's
per-command whitelist + `site.json` + scripts tests (S1.1); three templates + the botsite
test (P2). Did **not** touch `botsite/app.py` (P1 owns routing), other units' files, the
plan doc, or `disbot/`.

## Shipped (PR #1112)

**S1.1 — enrich the public per-command data** (`build_site_subset`). Per command, only
safe/real fields, `null`/`[]` where absent, redaction lens preserved:
- `description` — the command's full first docstring **paragraph** (richer than the one-line
  `usage`), Sphinx roles (``:class:`X```) reduced to their label, markdown stripped; `null`
  when no docstring. Derived in-script (`_command_docstrings` re-parses the cogs tree) since
  the scanner — S1's exclusive file — only exposes the truncated `brief`.
- `examples` — real `!command …` invocations lifted **verbatim** from backtick-wrapped
  docstring snippets; `[]` when none (never fabricated). 33 commands expose examples.
- `use_cases` — reserved `null`: no reliable *structured* per-command source exists; never
  invented.
- `status` — `finished` | `in-progress`: in-progress iff the command's cog/subsystem has a
  linked **open idea or open bug** (188 finished / 118 in-progress on the real repo).
- `linked_ideas` — open ideas mapped to the cog/subsystem, **title + status only** (redaction
  — never the raw idea body).
- `notes` — reserved `null`. The plan's v1 candidate (the help-overlay re-describe text) is
  **per-guild DB data** — unavailable statically *and* unsafe to surface publicly — so v1 is
  `null` (a curated *static* source is a fast-follow, recorded as this session's Q-0089 idea).

  Linking method: the plan's **heuristic name-match fallback** (no explicit subsystem tag
  exists yet), tuned to the **idea filename slug** (curated/topical) rather than the free-text
  title to cut generic-word false matches; open ideas only (`historical`/`reference` excluded),
  open bugs only (`FIXED`/`RESOLVED` excluded). One residual single-word-key cross-match is
  possible (`chain` ~ an agent "self-chaining" idea) — documented honestly in the code; the
  durable fix is this session's idea (an explicit `Subsystem:` idea tag). Safe regardless:
  title+status only.

  `check_dashboard_data.check_site_subset` gains a **fail-closed per-command field whitelist**
  (`SITE_COMMAND_FIELDS`) — a future enrichment can't slip a per-guild value onto the public
  command surface without being vetted in first. `botsite/data/site.json` regenerated
  (regenerable-identical to a fresh build). Scripts tests extended (export + guard).

**P2 — the interactive command + feature browser** (templates only; P1's wired
`/commands` + `/features` routes render them):
- `commands.html` — every command a **clickable card → expanding detail view**. The cards are
  native `<details>` elements, so they are clickable + expandable with **zero JS**
  (progressive enhancement); a small **inline** script (no `static/` dir — the #970 gotcha)
  layers **fast client-side search + category filter** on top (instant `data-search` haystack
  match). Friendly empty state.
- `_command_detail.html` — the detail partial: description · use-cases · aliases · permissions
  · cooldown · examples · notes · **status badge (finished/in-progress)** · **linked-ideas
  "what's planned" teasers**. Every field rendered defensively (null/empty → friendly omission).
- `features.html` — the same catalogue grouped by category (the all-in-one showcase), per-
  feature cards (emoji · name · benefit · tags · game badge) + the same client-side search.
- `tests/unit/botsite/test_commands_page.py` — `importorskip`-guarded; asserts the clickable
  `<details>`, status badges, detail fields, search/filter scaffolding, and no dev-only leak.

## Verification (all green)

- `python3.10 scripts/check_quality.py --full` — **10915 passed, 37 skipped**, `All checks
  passed ✓` (black/isort/ruff + `mypy disbot/` + the full pytest suite).
- `python3.10 scripts/check_architecture.py --mode strict` — exit 0 (no web→`disbot/` import;
  only pre-existing `disbot/views/` warnings).
- `python3.10 scripts/check_dashboard_data.py --site` — OK (top-level + per-command whitelist
  + counts). `check_generated_artifacts_fresh` — `site.json` fresh.
- Targeted: `tests/unit/scripts/test_export_dashboard_data.py` + `test_check_dashboard_data.py`
  (47 passed) · `tests/unit/botsite/` (23 passed) · rendered `/commands` (612 KB, 306 cards) +
  `/features` by hand — cards clickable, badges + examples + linked ideas render correctly.
- `check_docs --strict` + `check_current_state_ledger --strict` exit 0.

## Context delta

- **The plan's `notes` source was unbuildable as written** — "v1 reuse the help-overlay
  re-describe text" — because that text is *per-guild DB data* (`services/help_overlay.py`),
  i.e. neither statically available to the stdlib producer **nor** safe to surface publicly
  (it would breach the redaction lens). Resolved honestly: `notes = null` for v1, with the
  curated-static-source follow-up captured as an idea. This is the kind of source-scope
  mismatch a plan should catch *before* the build (see the previous-session review).
- **The idea↔command link is a heuristic, not a fact.** It is safe (title+status only) and the
  plan explicitly accepted "heuristic name-match as fallback," but it is precision-limited and
  drift-bait. The code says so in its own docstring; the durable fix is this session's Q-0089
  idea (an explicit `Subsystem:` tag on idea front-matter).
- **No `current-state.md` ledger edit from this session.** The `--strict` ledger advisory lists
  #1100–#1109 as unlisted, but those are *newer* than the `Last reconciliation pass` marker
  (#1094) — benign newest-merge lag owned by the parallel website-split sessions' close-outs +
  the next reconciliation pass, and editing `current-state.md` would collide with those
  parallel sessions. My own PR (#1112) is not merged, so nothing of mine is missing.

## 💡 Session idea (Q-0089)

`docs/ideas/idea-subsystem-tag-on-ideas-2026-06-19.md` — add an optional **`Subsystem:`
front-matter tag** on idea files (registry-validated), so the command browser's idea→command
linking (built this session as a filename-slug heuristic) becomes **authoritative** where it
matters. Prefer the tag, keep the heuristic as fallback — the exact "explicit tag, heuristic
fallback" shape S1.1 recommended. Cheap + incremental (no migration; tagging just improves
precision idea-by-idea), reusable (dev `/ideas` grouping, a future "what's planned for X?"
view), and it closes the drift-bait seam the S1.1 code flags in its own caveat. Distinct from
`cog-declares-its-subsystem` (that is *cogs* declaring; this is *ideas* declaring).

## ⟲ Previous-session review (Q-0102)

Reviewing **`2026-06-19-website-identity-and-fanout-enablers.md`** (#1110 — the session that
set up this one).

- **Did well:** it turned the owner's vision into a *buildable contract* with unusual
  precision — it split out S1.1 as a distinct unit, named every per-command field, and flagged
  the ambiguous derivations (`status`, `linked_ideas`, `notes`) as "open decision +
  recommendation" rather than hand-waving them. I implemented those recommendations almost
  verbatim. It also added `botsite-ci.yml` *before* the fan-out, so this PR gets real CI
  instead of `importorskip`-skipping — exactly the right sequencing.
- **Could have been better:** it carried the brief's "`notes` = reuse the help-overlay
  re-describe text" recommendation **without checking that source's scope**. The help overlay
  is *per-guild* (`services/help_overlay.py`), so it is both unavailable to the stdlib producer
  and a redaction-lens breach — a contradiction I only found at build time, costing a detour.
- **Concrete system improvement (initiated):** when a plan recommends a **specific data
  source** for a public/generated surface, it should verify that source's **scope + safety**
  (repo-level vs per-guild; value-free vs value-bearing) *at plan time* — a per-guild or
  value-bearing source silently violates the redaction lens that the whole split rests on.
  Cheap to add as a one-line check in the planning/route-idea routine ("for any data field
  feeding `site.json`, name its source *and* confirm it is repo-level + value-free"); it would
  have caught the `notes` mismatch before the build. (Captured here as the workflow note; not
  promoting to a CLAUDE.md rule — owner-review lane per Q-0106 if it recurs.)

## Grooming (Q-0015)

Primary task fully shipped; the Q-0089 idea above *creates* a new idea and the review *surfaces*
a workflow improvement. The S1.1 heuristic-precision idea is itself the groomed next step for
this lane (small/decided: a future session builds the `Subsystem:` tag). The broader website
back-half (P3 changelog/status, P4 submit, P5/P6 moderation+mirror, P7/P8 docs) remains
fan-out-ready per the plan's dependency graph — unblocked, no grooming change needed.
