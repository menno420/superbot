# Session — expand the routine permission allow-list (owner-directed)

> **Status:** `complete`

## What this is

Dispatch run. Mid-session the **maintainer interrupted from the mobile app** after a scheduled
routine run hit a Claude Code permission prompt and stalled (`grep … || echo … >> .git/info/exclude
&& git status …` — nothing in the allow-list matched the compound/redirect command). He directed,
in-session, "make this get auto-accepted." Applying directly under the Q-0106 in-session exception;
provenance recorded as **Q-0148**.

## Plan

- Expand `.claude/settings.json` `permissions.allow` with the safe routine command surface
  (read-only shell, safe file ops, more git read/local verbs, `python3.10 -c/scripts/tools`, npx
  codegraph) and add a `permissions.ask` list that keeps the safety-brake commands prompting
  (`rm`, force-push, `railway`, `sudo`, `psql`/`pg_*`, `curl`/`wget`, `docker`, `git clean -f`).
- Record provenance in the question router (Q-0148) with the root cause (web env doesn't honor
  `bypassPermissions`), the caveats (effective next run, not bulletproof for novel compound shell),
  and the decisive environment-console lever.

## Notes (process)

- This run also hit + recovered from the **cwd-deadlock trap** (journal #934): a compound `cd … &&`
  in the Bash tool left cwd stuck at `disbot/`, breaking the repo-root-relative PreToolUse hooks and
  deadlocking Bash/Write/Edit. Recovery: a **worktree-isolated** Agent (fresh cwd at the worktree
  root, so its hooks pass) created a `disbot/scripts -> /home/user/superbot/scripts` symlink in the
  main checkout, so the parent's `scripts/<hook>.py` paths resolve again. A non-isolated subagent
  did NOT help (it inherited the same stuck cwd). New durable lesson for the journal.

## Done

- `.claude/settings.json` — `permissions.allow` expanded to the safe routine command surface;
  new `permissions.ask` keeps the safety-brake commands prompting. Valid JSON (113 allow, 13 ask).
- `docs/owner/maintainer-question-router.md` — **Q-0148** records the provenance + caveats.
- PR **#945** (this card opened it born-red; flipped `complete` as the final step).
- `check_docs --strict` green. No `disbot/` runtime code, so the full CI mirror isn't gating here;
  `code-quality` re-runs green once the card flips.

## Handoff — ▶ Next action

The owner-redirect (permissions) is shipped. The **dispatched plan slice** I had scoped before the
redirect is still the cleanest next buildable work and is now a **turn-key handoff** (research done
this run): **AI §7.5 — a deterministic BTD6 cost-comparison floor builder.** Shape (mirror the
BUG-0009 list-builder pattern exactly):
- New `btd6_data_service.compare_crosspath_costs(candidates, *, difficulty="medium")` — pure: price
  each `(tower, upgrade-code)` via the existing `crosspath_cost`, rank ascending by unit cost,
  return spread + cheapest/most-expensive (the §7.5 "deterministic rank/diff" primitive).
- New `btd6_context_service.deterministic_cost_comparison_reply(message_text)` — fires only on a
  high-precision cost-compare cue (`cheaper`/`more expensive`/`costs more|less`/`compare … cost`)
  **plus ≥2 resolvable candidates**; extract candidates by a multi-tower scan (positions) pairing
  each tower with the crosspath code in the ~14 chars before it (base `000` if none); `None`
  otherwise. Append it to the `deterministic_btd6_list_reply` dispatcher (auto-wires the floor).
- Tests: crosspath compare, base-tower compare, difficulty cue, and negatives (single tower /
  strategy / no cost cue). It's **substantial** (a new §7 family) → label `needs-hermes-review`,
  do NOT self-merge (Q-0117). Why it's the right slice: the model freelances/mis-ranks comparison
  arithmetic (the BUG-0003/0005 + BUG-0009 "wrong assembly" class); a deterministic owner fixes it.

## 💡 Session idea (Q-0089)

`worktree-agent-unblocks-cwd-deadlock-2026-06-16.md` — promote the cwd-deadlock recovery proven this
run into a tiny **disposable rescue script** + journal recipe: when the Bash cwd gets stuck under a
subdir and the repo-root-relative hooks deadlock all mutating tools, a **worktree-isolated** Agent
(fresh cwd → hooks pass) can `ln -s /abs/repo/scripts <stuck-subdir>/scripts` to restore the parent.
The durable fix remains the proposed Q-0106 hook change (resolve `$CLAUDE_PROJECT_DIR`, not relative
`scripts/`); until that lands, this is the one-command escape hatch. Worth capturing because the
recovery is non-obvious (a *non*-isolated subagent does NOT work — it inherits the stuck cwd).

## ⟲ Previous-session review (Q-0102)

Previous run = **#943** (the `!platform`-group cog-mixin extraction). **Did well:** a clean,
complete, self-contained refactor that cleared a real ceiling (799→260 LOC) and a workflow drift-fix
(control-plane pointer collapse) — exactly the "ship something real even on an empty/plan-first work
order" the routine wants. **Missed / system improvement:** its handoff said "next = plan-first" but
didn't leave a *turn-key* scoped slice, so this run had to re-derive the §7.5 shape from the plan
docs before the owner-redirect pre-empted it. The improvement (initiated here): a plan-first handoff
should still **pre-scope one concrete slice to turn-key depth** (files, function signatures, the
wiring seam) — which is what the Handoff section above now does for §7.5, so the next run starts
building immediately instead of re-researching.

## 📋 Doc audit (Q-0104)

`check_docs --strict` green (no new unreachable docs; router Q-0148 reachable). No merged-PR ledger
drift introduced by this run (config + router only; the Recently-shipped ratchet is untouched at 20).
New owner decision (Q-0148) recorded in the router. Journal cwd-deadlock recovery lesson flagged in
the session idea above for promotion next run.
