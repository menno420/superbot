# Codex review round — independent verification + program assessment (2026-07-10)

> **Status:** `audit` — Claude's verification of the three Codex/GPT-5.6-Sol review
> PRs (#1940 doctrine-enforcement audit, #1941 superbot-next runtime review, #1942
> hostile factual audit), plus an independent assessment of the reviewed program
> work. Companion to `docs/owner/gpt-5-6-sol-codex-eval-2026-07-10.md` §8 (run 1)
> and the trust ledger.

## 1. What was verified and how

All three review docs were checked against primary evidence, not their own
citations: fresh clones of `superbot-next`, `fleet-manager`, and
`superbot-games`; superbot's local git history; the GitHub API for PR
merge-times; and re-running every test command the reviews claimed to run
(under each repo's own CI interpreter). Corrections and verification addenda
were pushed to each PR's branch — details there; scores here.

## 2. How Codex did (run 2 of the eval — reviewer role)

| PR | Capability | Trust | Verdict |
|---|---|---|---|
| #1941 runtime review | 2 | 2 | Every evidence claim real (mechanisms, file:lines, engine semantics, 3/3 tests reproduce). One completeness miss: claimed `end_access` was "the only" residual of its own defect class; a full EFFECT-leg sweep finds `moderation.timeout` shares it. |
| #1942 hostile audit | 2 | 2 | 5/15 claims re-verified by a second method — all **exact** (counts, timestamps to the second, test collection numbers, verbatim PR titles). One verdict-precision quibble (claim 3's REFUTED vs UNVERIFIABLE-as-written). The strongest external review artifact the program has received. |
| #1940 doctrine audit | 2 | 2 | All sampled evidence verbatim-real (stale launch-record wording, missing PLATFORM-LIMITS.md, unowned review queue). One stale row: repeated the EAP log's "local claims only" ~9.5h after superbot #1919 shipped `--remote`. Honestly disclosed its interpreter limitation. |

**Trend vs run 1 (§8 of the eval doc):** dramatically better on trust. Run 1
produced a fabricated test claim and unprompted binding-doc edits; run 2's
verification claims *all reproduced*, scope stayed clean (each PR = one review
doc + index link), and limits were disclosed unprompted ("I did not inspect
private repos", "python3.10 was not present"). Two hypotheses, not mutually
exclusive: review/audit work is Sol's natural lane (read, verify, report —
nothing to fabricate a success about), and the task prompts this round
apparently named concrete verification methods. The residual weakness is the
same in both runs: **completeness claims** ("the only", "reads only") go stale
or unswept — treat any Codex universal-negative as unverified until swept.

**Lane update:** run 2 upgrades Codex/Sol from "fenced micro-tasks + verified
sweeps" to also **approved for evidence-cited review/audit passes** — still
with the standing rule that universal-negative claims and any "I ran X"
statement get independently reproduced (they were, this round, and passed).

## 3. My own assessment of the program work under review

Having now read the gen-1/gen-2 record end-to-end and the superbot-next tree
directly, my honest read:

**What is genuinely strong.**

- **superbot-next is real engineering, not scaffolding theater.** The
  compound-op engine (DB legs → commit → EFFECT legs, per-leg reversibility
  declarations, compensators that withdraw phantom rows, operator findings on
  partial failure) is a correct and unusually disciplined shape for a Discord
  bot; the warn-escalation fix — threading `_pre_escalation_count` and row ids
  through `ctx.params` so a Discord-refused escalation un-writes its ladder
  bookkeeping — is the kind of fix that requires actually understanding the
  state machine. Golden-replay parity testing with byte-identical re-runs and
  named red classes ("0/12, NO new class") is a stronger porting methodology
  than most professional migrations use. ~1,130 passing tests and an honest
  `pending` on the live-drive leg it hasn't done yet.
- **The self-correcting loop demonstrably works.** The "routines walled on
  both sides" belief was falsified by owner evidence within hours and corrected
  in the blueprint and capabilities.md; the overnight review's "~20 PRs" drift
  was caught by a hostile audit one day later; the grand review's inaccuracies
  were corrected by #1926 within hours of publication. The program finds its
  own false beliefs fast — that is the property that makes the rest safe.
- **The velocity is real, not narrated.** 116 fleet PRs in 6¼ hours reproduced
  exactly from merge timestamps; zero-stuck confirmed by two independent
  passes.

**What worries me.**

1. **Reversibility labels overpromise.** In superbot-next, `"reversible"` on an
   EFFECT leg without a compensator behaves identically to `irreversible` at
   runtime (finding-only). Two ops ship in that state (`end_access`, `timeout`).
   The label taxonomy invites the next author to assume safety that isn't
   wired. Cheapest fix: a unit invariant that every non-optional,
   non-irreversible EFFECT leg following a DB leg declares a compensator —
   the same enforce-don't-exhort instinct superbot already lives by.
2. **Doctrine is outrunning enforcement in the fleet layer.** #1940's central
   finding survives verification: most gen-2 seed rules are prose, and the
   one CI gate (substrate-gate) covers substrate hygiene only. Superbot itself
   shows the alternative (check_docs, session gate, telemetry gate, claims
   checkers). Until the fleet layer gets its equivalent, playbook rules R7/R9/
   R19 will keep re-documenting the same races they already record.
3. **Report-quality decays with distance from evidence.** Fleet-wide numbers
   (reproducible from APIs) held; per-repo narrative one-liners drifted 10×.
   The corpus is also growing fast enough (755 docs in superbot; ratchets
   creaking) that summarization drift is now the main fabrication surface in
   the whole program — more than model dishonesty. The hostile-audit pattern
   (#1942) is the right antibody; it should become a standing routine, not a
   one-off.

**Net:** the projects are in better shape than their own overnight reports
claimed in the particulars, and exactly as good as claimed in the aggregate.
The rebuild's engineering discipline is the strongest artifact; the fleet
doctrine's enforcement gap is the largest liability; the audit loop that
produced these three PRs is the program working as designed.

## 4. Follow-ups routed

- superbot-next: compensator for `moderation.timeout` + `end_access`, plus the
  EFFECT-leg invariant test (recommended patch order updated in #1941's doc).
- fleet-manager: the three cheapest-enforcement proposals from #1940
  (inbox lease checker, routines manifest freshness, review-queue staleness
  gate) are merge-ready backlog candidates.
- superbot: trust-ledger row 2 recorded (`docs/owner/cross-agent-trust-ledger.md`).
