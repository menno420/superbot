# Session — Hermes sync hardening (self-healing mirror sync + divergence recovery)

> **Status:** `complete`

## What I did

Live follow-up to #913/#914. Applying the fixes on the VPS surfaced a real bug: the clone had
**diverged** from `origin/main`, so `git pull --ff-only` aborted (`Not possible to fast-forward`)
— which also meant the new `apply_context_fixes.sh` was never downloaded ("No such file"). I gave
the owner a recovery (backup branch + `git reset --hard origin/main`); the apply-script then ran
and landed **all three** `hermes config set` calls cleanly (threshold 0.75, protect_last_n 30,
cache_ttl 1h — incl. the one I was unsure the version would accept). This PR hardens the sync so a
diverged clone can't get stuck again.

## What shipped (PR #915)

- `docs/operations/hermes-operating-prompt.md` — replaced the fragile `git pull --ff-only origin
  main` with the self-healing `git fetch origin main && git checkout -B main origin/main` (always
  lands on fresh main, never aborts on divergence — the dispatch routine's proven pattern). States
  the clone is a read-only mirror; never commit to it. SOUL.md grew only 6478→6560 bytes (still
  <8000 budget; the size guard still infos at >80%).
- `docs/operations/hermes-terminal-cheatsheet.md` — made the deploy-section sync robust + added a
  "clone diverged → recovery" snippet (backup branch + reset --hard).
- **Verified:** `check_docs --strict` ✓; SOUL size re-measured (6560 bytes, under budget).

## Handoff / next

- The fixes are LIVE on the VPS (config applied, SOUL installed). The owner picks up the
  self-healing sync next time they run `install-soul.sh` / `apply_context_fixes.sh` — no urgent
  re-run (the current `--ff-only` SOUL works now that the clone is a clean mirror).
- **Biggest remaining lever:** Hermes' model context window (256K → a 1M-context variant would
  4× the headroom before the 50% compaction line). The owner should check `hermes config` for the
  model; switching is `apply_context_fixes.sh --set-model=<provider/model>` (cost is their call).
- The real test now: a previously-failing ~5-message doc-reading session should hold the thread.

## 💡 Session idea (Q-0089)

**Trim the Hermes operating prompt to leave real headroom.** It's now at 6560/8000 bytes (82%) and
I've bumped it twice this chain — every future rule fights the truncation ceiling. The fix isn't a
bigger budget, it's a leaner SOUL: move *procedural* detail (the skills list, verify-don't-assume
command menu) into the **skills** (which load separately, not in slot #1) and keep SOUL.md to
identity + the 5-6 load-bearing rules. Pairs with the #914 size guard (detect) — this is the
reduce. Dedup-grepped `docs/ideas/` — the only hit is the dispatch-bridge idea (unrelated).

## ⟲ Previous-session review (Q-0102)

Previous: `2026-06-15-hermes-soul-guard.md` (#914). Its "ship a script, not steps" lesson was
**immediately validated** — the owner ran the script and it worked, landing all three config sets
including the uncertain `cache_ttl`. Strong call. **What it missed:** it assumed the clone would
`git pull --ff-only` cleanly to even *get* the script — it didn't (diverged), so delivery failed on
the first attempt. **System improvement (this session):** a VPS operator script's FIRST dependency
is "can the clone update at all?" — so the sync instruction must be self-healing, not abort-prone
(now fixed). Lesson for control-plane work: harden the *delivery path* (git sync) before relying on
the *payload* (the script).

## 📋 Doc audit (Q-0104)

`check_docs --strict` green; both edited docs reachable. SOUL.md re-measured at 6560 bytes (still
under the 8000 budget — the operating-prompt change didn't push it over). No new owner decision to
route (a robustness fix to instructions, not a decision). active-work claim updated; it moves to
Recently-cleared when #915 merges. No chat-only content left undocumented — the recovery is now in
the cheatsheet, the self-healing sync in the operating prompt.
