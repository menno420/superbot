# Session: install-soul.sh — scripted operating-prompt install + SOUL.md doc fix

> **Status:** `in-progress` — adding the SOUL.md installer + fixing the wiring doc; flip to complete last.

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** tooling + docs fix (owner-driven, in-session)

## What this session did

While wiring the operating prompt onto the Hermes VPS, two things surfaced and were fixed.

1. **Doc was wrong about the home.** `hermes-operating-prompt.md` said to paste the prompt into the
   agent system prompt in `~/.hermes/config.yaml` *or* a base skill. Confirmed against the official
   Nous Hermes docs (`hermes-agent.nousresearch.com`): the durable identity lives in **`~/.hermes/SOUL.md`**
   — slot #1 of the system prompt, plain-text, **loaded fresh each message (no restart)**; `config.yaml`
   is the CLI-managed engine config (`hermes config edit`/`set`), and `agent.personalities` are only
   `/personality` tone overlays, not the base prompt. Corrected the "How to wire it in" section.
2. **No repeatable installer.** Skills had `install-skills.sh`; the operating prompt had to be hand-pasted
   (120 lines — painful on mobile, and a drift risk). Added **`scripts/hermes/install-soul.sh`**
   (mirror of `install-skills.sh`): extracts the operating-prompt block straight from the doc and writes
   it to `~/.hermes/SOUL.md`, timestamp-backing-up any existing file; `--dry-run` previews;
   `HERMES_SOUL` overrides the target. Tested end-to-end here (extract / write / backup / dry-run).
   Cross-linked from `hermes-skills/README.md`.

The owner's live `SOUL.md` was just the default template (heading + comment, no real identity), so
Hermes is running on its built-in default — the installer cleanly replaces it with the SuperBot prompt.

Verification: `bash -n` + functional test (writes 96-line/6.1 KB SOUL.md, creates `.bak` on re-run);
`check_docs --strict` ✓. Tooling + docs only — no runtime bot code.

## 💡 Session idea (Q-0089)

The skill pack has a CI freshness gate (`build_skills.py --check`) but the operating prompt has no
equivalent — nothing verifies the block in `hermes-operating-prompt.md` is still extractable by
`install-soul.sh` (a future doc reformat could silently break the installer). Idea: a tiny CI check (or
a `--check` mode on `install-soul.sh`) that asserts the extraction still yields a non-empty block
starting with "You are Hermes" — so the installer can't rot. Captured pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

The previous run (#869, python3 tooling) correctly de-pinned the *invocation* but left the bigger
deployment story implicit — it didn't notice the operating-prompt doc pointed at the wrong file
(`config.yaml`) entirely. This session caught it only because the owner went to actually do the wiring
and hit the wall. System improvement: agent-facing "how to deploy X" docs should be verified against
the *target tool's own docs* (here, the Nous Hermes docs), not assumed — the same "validate against the
consumer's environment" lesson as #869, now applied to the install destination, and made durable by
shipping a tested installer rather than prose steps.
