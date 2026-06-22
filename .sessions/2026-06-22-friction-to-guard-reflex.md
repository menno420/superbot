# 2026-06-22 — Wrong-branch guard hook + the "friction → guard" self-prevention reflex

> **Status:** `complete` — owner-directed. Two halves: (1) build the recommended advisory
> wrong-branch hook; (2) the owner's deeper ask — harden the guides so agents *self-generate*
> these prevention fixes, instead of the owner having to spot inconsistencies. Owner-directed
> (Q-0194, Q-0191) → merge on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## What shipped

**Part A — the wrong-branch guard (the concrete fix).** Extended `scripts/check_branch_freshness.py`
(the existing Q-0138/Q-0188 advisory hook): its PreToolUse(Bash) trigger now also fires on
`git commit`/`merge`/`rebase` with a **network-free** branch guard — warns on **detached HEAD**,
**on `main`**, or **behind `origin/main`** (local refs only, so zero latency on the frequent commit
path; `git push` keeps the authoritative network freshness check). Advisory, never blocking, same
Q-0105 kill-switch. No `.claude/settings.json` change needed (the existing `Bash` matcher already
routes to the script). +4 tests; black/ruff clean; 11/11 green.

This directly catches this session's own slip: a piped `git checkout` (`… | tail -2 || fallback`)
masked the checkout's failed exit behind `tail`'s, so a `git merge origin/main` ran on an
already-merged branch. The guard makes a detached/behind/wrong branch loud at the `commit`/`merge`
moment.

**Part B — the systemic half (so the owner doesn't have to spot these).**
- `.sessions/README.md` — added **reflection-interview question 7: "What interrupted your workflow —
  and did you ship a guard so the next session can't hit it?"** with the preference order
  (checker/CI/test → hook → journal Rule) and the free-vs-owner-gated ownership split → a
  `🛠 Friction → guard` log line.
- `.session-journal.md` — added END-protocol **step 4b (the friction → guard reflex)** and two
  **Cross-agent & git workflow** Rules: *sync to `origin/main` & branch fresh before PR work
  (esp. resumed sessions)* and *never mask a command's `$?` behind a pipe; confirm
  `git branch --show-current` after a checkout*.
- `docs/owner/maintainer-question-router.md` — **Q-0194** records the directive + a DISCUSS item to
  optionally elevate the reflex into binding `CLAUDE.md`.

## Findings / decisions

- **Advisory, not blocking (decided).** A fresh branch also has an empty diff vs `main`, so a hard
  block on "looks merged" would misfire; and squash-merges make "already merged" undetectable from
  git alone. The reliable, low-false-positive signal is the existing behind/detached/on-main check,
  surfaced at the dangerous moment — matching the hook's disposable-advisory philosophy.
- **The real fix is the reflex, not the hook.** The hook prevents *this* footgun; question 7 + step
  4b make the *next* session convert *its* friction into a guard without the owner prompting — which
  was the owner's actual ask. The hook is the dogfooded example of the reflex.
- **Decision made alone — CLAUDE.md elevation left as a proposal.** The reflex is fully operative via
  the journal/README enders (run every session); promoting it into binding CLAUDE.md is propose-first
  (Q-0035), so it's a DISCUSS item, not self-applied.

## 🛠 Friction → guard (Q-0194)

**Friction:** a masked-pipe `git checkout` failure → a `git merge` on the wrong (already-merged)
branch; root-caused to (a) not syncing to `origin/main` first on a resumed session, (b) `cmd | tail
|| fallback` swallowing the real exit code, (c) not verifying the branch after the checkout.
**Guard shipped:** the extended `check_branch_freshness.py` PreToolUse branch guard (Q-0194) + two
journal Rules + the standing reflex itself (so this class self-prevents going forward).

## 💡 Session idea

**A tiny `scripts/check_no_exit_masking.py` lint (Q-0105-disposable).** The root trigger was a shell
anti-pattern — piping a command whose exit code you then branch on (`cmd | tail || fallback`). A
warn-only checker that flags `… | <filter> (&&|\|\|) …` shapes in committed shell/scripts (and could
advise in PreToolUse on Bash) would catch the *class*, not just the git instance. Dedup-checked: no
existing checker inspects shell exit-code handling. (Filed as the forward idea, not built this run —
the branch guard already covers the concrete git case.)

## ⟲ Previous-session review (Q-0102)

The previous turn (un-sticking #1274) was sound — it correctly diagnosed the stuck PR as the dropped
CI run + a real `active-work.md` conflict I had caused, and resolved it cleanly. **Where it (and I)
fell short:** the wrong-branch slip *inside* that work should have triggered a guard immediately,
unprompted — instead it took the owner asking "isn't there a rule?" to surface it. That gap is
exactly what this session's reflex (Q7 + step 4b) institutionalizes. **System improvement
(initiated):** the friction→guard reflex closes the loop so "an agent hit friction" reliably becomes
"the next agent can't" — the internal version of the owner-as-reviewer safety net, but self-served.

## 📤 Run report

- **Did:** built the advisory wrong-branch hook + institutionalized the friction→guard reflex
  (reflection Q7, journal step 4b + Rules, router Q-0194) · **Outcome:** shipped (this PR, auto-merge
  on green)
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** Q-0194 DISCUSS — optionally elevate the friction→guard reflex into
  binding `CLAUDE.md` (it is already operative at journal/README level).
- **⚑ Owner manual steps:** none — docs + a disposable advisory hook; merged = deployed.
- **⚑ Self-initiated:** no — owner-directed (build the hook + improve the guides). The `💡` shell
  exit-masking lint idea is filed, not built.
- **↪ Next:** ungated build lanes (current-state ▶) untouched. If the owner greenlights the DISCUSS
  item, add the one-line CLAUDE.md principle.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` + `check_current_state_ledger --strict` green; hook test 11/11; script
black/ruff clean. Q-0194 recorded in the router with provenance; the hook header carries the Q
(Q-0105 reliability header convention). No current-state ledger entry (no merged PR yet — this
session's PR is recorded next reconciliation, benign lag).
