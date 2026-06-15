# Session — 2026-06-15 · Railway log-triage analyzer (deterministic, content-free)

> **Status:** `in-progress`

## What I'm about to do

Dispatch routine. Work order was empty/stale (the named slice, mining Slice D, already
shipped as #891; and mining Slice B/Forge is **in flight as #905** by a parallel session — so
I avoid the mining-structures lane to not duplicate/collide). Taking the next independent,
higher-priority plan slice from the band-#900 decade queue.

**Slice 4 — Railway log-triage skill (Q-0130, reserved autonomous-loop thread).** The skill
doc (`log-triage.md`) + the read-only reader (`railway_logs.py`) already exist, but the skill's
error-scan + crash-loop steps (2–3) rely on the LLM eyeballing raw log text. The gap is a
**deterministic, content-free triage analyzer** that owns those steps mechanically — the
project's "deterministic layer owns the answer" philosophy (same shape as the BUG-0002/0004
mislabel fixes).

- `scripts/hermes/log_triage.py` — stdlib-only, read-only, **content-free**: parses
  `<ts> [SEV] message` lines (from `railway_logs.py` or stdin), groups errors by signature
  (traceback · login/connection · database · command/interaction · generic error), **redacts**
  example lines (snowflakes, tokens, emails, URLs, IPs) so no PII/log bodies leak, detects
  crash-loops (repeated startup banners / repeated fatal signatures), and renders a markdown
  report + `--json`.
- Wire it into `docs/operations/hermes-skills/log-triage.md` (steps 2–3 → run the analyzer) and
  regenerate the `scripts/hermes/skills/log-triage/SKILL.md` artifact (`build_skills.py`).
- Tests: `tests/unit/scripts/test_log_triage.py` (parse · grouping · content-free redaction ·
  crash-loop · json · stdin).

Verify: `check_quality --full` green + `check_architecture --mode strict` 0 + `build_skills --check`.
