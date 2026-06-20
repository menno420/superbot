# 2026-06-20 — Pin the always-loaded instruction core against pointer rot

> **Status:** `in-progress`

Dispatch run, empty work order. The Explore-hub spine PRs (1 + 3) are merged and the
buildable-`ready` decade queue is consumed, so this run takes a fresh ungated lane from
current-state ▶ Next action: the **small stdlib guards** family + the natural completion
of the procedures→skills thin-pointer work.

**Slice 1 — extend `check_docs.py`'s pinned check to the `.claude/` instruction core.**
`check_docs.py` already pins (`check_pinned`) the concrete backtick repo-paths cited in
the three read-path docs (`AGENT_ORIENTATION` / `current-state` / `repo-navigation-map`),
so a moved/renamed target can't rot those pointers silently. But `.claude/CLAUDE.md` and
`.claude/rules/*.md` — the **always-loaded** instruction core, where the procedures→skills
conversion (#1029, #1028) created many *thin pointers* to the runbooks/docs/skills that
hold the HOW — are **not** pin-checked. A pointer there going stale is exactly the
"stale pointer" drift class the bugs-first/Q-0166 mandate exists to catch, and nothing
guards it today. Extend `check_pinned` to also validate those files (the `_PATH_REF_RE`
regex already supports `.claude/`/`.github/` prefixes; paths resolve relative to repo
root, matching how CLAUDE.md cites them). Green on arrival — all 38 concrete refs across
the `.claude/` files resolve today — so this is a preventive ratchet, not a fix.

Scope fence: docs-checker tooling + its tests only. No `disbot/` runtime code, no
CLAUDE.md *content* edits (this is the autonomy boundary — CLAUDE.md stays read-to-me;
I only add a guard that *protects* its pointers), no deploy.

<!-- This card is born-red (in-progress) per Q-0133: the check_session_gate step in
code-quality holds the auto-merge until the Status flips to a ready token. The close-out
docs (Context delta, idea, previous-session review, run report) land before that flip. -->
