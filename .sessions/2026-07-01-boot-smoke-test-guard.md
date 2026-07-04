# 2026-07-01 — Boot smoke-test guard (never ship a cog that won't load)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1601](https://github.com/menno420/superbot/pull/1601) — dynamic boot smoke test + BUG-0030.
**Branch:** `claude/funny-franklin-4n38rf` (restarted from origin/main after #1600 merged).
**Run type:** `routine · dispatch` (owner-directed hardening after my own outage)

## What this run did — and why

**My own PR #1599 (fishing Dock) took production offline.** I named a command `!dock` that collided
with `!sail`'s existing `dock` alias *inside the same cog* → `CommandRegistrationError` at `add_cog`
→ `fishing` cog failed to load → STRICT identity-contract aborted boot → **crash loop**. #1600 (a
separate session) fixed the code (dropped the alias) and broadened the static token guard; the bot
recovered on its auto-deploy.

The owner's directive: *shipping features is fine, shipping broken features is fine — but shipping
code that breaks the bot's **startup** must never happen.* This is the **second** such outage (the
first was the `give` collision, #1541/#1544). Per the Friction→guard rule (Q-0194), I converted it
into the strongest **enforcing** prevention at the exact layer both outages slipped through.

## Shipped (PR #1601)

- **`tests/unit/invariants/test_cog_load_smoke.py`** — a **dynamic boot smoke test**: it constructs a
  bot mirroring `bot1` (`help_command=None`, `case_insensitive=True`) and **loads every
  `config.INITIAL_EXTENSIONS` cog in a fresh subprocess**, failing CI if any raises at `add_cog`. This
  is the "did the bot actually boot?" check nothing in CI performed. It catches the whole boot-break
  class — token collisions (both prior outages) **and** a raising `cog_load`, a bad import, a
  duplicate app-command — not just the token subclass #1600's static guard covers.
  - Regression-proven both ways: fails naming `cogs.fishing_cog … CommandRegistrationError: The
    command dock is already an existing command or alias` on the pre-fix tree; passes 58/58 on fixed
    `main`.
  - **Runs in a subprocess deliberately** — an earlier in-process version loaded all cogs into the
    pytest process and polluted global state (EventBus subscriptions / singletons), failing unrelated
    xp/mining view tests by run-order. I caught that in the full mirror *before* shipping and rewrote
    it as a subprocess (true isolation + a more faithful fresh-boot check). 13,434 tests green, no
    order dependence.
- **`docs/health/bug-book.md` — BUG-0030** recording the outage (symptom, root cause incl. the
  review miss, #1600's fix, and both stays-fixed guards) — the durable prod-bug entry that was missing.

Full CI mirror green (13,434 passed); `check_architecture --mode strict` 0 errors.

## The honest miss (accountability)

I had every input to prevent this and used none of them: I had **read** the `!sail` command with its
`dock` alias minutes before naming my command `dock`; the repo had *just* had this exact bug class
(`give`, which I read in orientation); and a binding rule for the same instinct exists (Q-0200's
grep-before-you-name, scoped to `def`s). I treated "pick a command name" as a naming decision instead
of a namespace check, and skipped the one `grep '"dock"'` that would have caught it. My green CI gave
false confidence because no check loaded the cogs. **Behavior change:** before adding any command/alias,
grep the target cog + repo for the exact token across `name=` and `aliases=`. #1601 now enforces the
outcome at CI regardless of whether I remember.

## Context delta

- **Discovered by hand:** `add_cog` command registration is fully offline (no DB/creds) — 56–58/58
  cogs load on a bare bot — so a boot smoke test *is* CI-runnable. The two gotchas: mirror `bot1`'s
  `help_command=None`/`case_insensitive=True` (else the default `help` command false-positives), and
  neutralise `tasks.Loop.start` + `core.runtime.tasks.spawn` (gateway-dependent background tasks).
- **Needed but not pointed to:** the "boot caught it, CI didn't" gap was a *known* idea
  (`test_extension_integrity`'s docstring cites it) but only ever addressed statically; nothing routed
  a session toward the dynamic complement until an outage forced it.

## 🛠 Friction → guard

- **Friction:** a command-token collision boot-loops the bot and green CI doesn't catch it (twice).
  **Guard shipped (this PR, free-to-ship test):** `test_cog_load_smoke.py` — CI now fails if any cog
  won't load, closing the whole boot-break class dynamically (complements #1600's static token guard).
  This is the enforcing prevention, not a prose reminder.

## 💡 Session idea

**Extend the boot smoke test to also register the app-command tree** (`await bot.tree.sync` is
network, but building/`copy_global_to`-style validation is offline) — a duplicate *slash*-command name
across cogs is the same boot-break class the prefix check now covers, and it's the one gap the current
subprocess load doesn't assert on. Small, offline, self-mergeable follow-up. Left as a note here (not
built — kept this PR to the prefix-command boot guard + the incident record).

## ⟲ Previous-session review

The previous run in this chain was **me** — the two-slice fishing structures run (#1598/#1599). It
shipped fast and clean-looking, but slice 2 (#1599) is precisely what caused the outage: I optimised
for "2–3 slices" throughput and skipped the collision check on a command name I'd literally just read.
The lesson for the **system**, not just me: the completion-bias in the dispatch prompt ("aim for 2–3
slices, never just one") has no counterweight for *boot-safety* on the runtime surface — it rewards
volume without a hard gate on "does it still start?". #1601 adds that missing hard gate at CI. The
honest verdict on the prior run: good velocity, but velocity without the boot check is exactly how you
ship an outage — the guard now makes the check non-optional.

## 📤 Run report

- **Did:** shipped the enforcing boot-safety guard (a dynamic cog-load smoke test) + recorded the
  outage as BUG-0030, after my #1599 boot-looped production · **Outcome:** shipped
- **Shipped:** #1601 — `test_cog_load_smoke.py` (CI fails if any cog won't load) + BUG-0030.
  *(Related: #1600, separate session, was the code hotfix + static-guard broadening — already merged
  + deployed; the bot is back up.)*
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (the bot already recovered via #1600's auto-deploy; this PR is a
  test-only guard)
- **⚑ Self-initiated:** the guard + BUG-0030 were self-initiated hardening in direct response to the
  owner's in-chat directive ("boot-breaking must never happen") — not a separate dispatched order, but
  owner-directed, so flagged here for visibility rather than as unprompted scope.
- **↪ Next:** optional follow-up — extend the boot smoke test to catch duplicate *slash*-command names
  (the one boot-break subclass it doesn't yet assert). Otherwise S1 fishing structures work continues
  per `docs/current-state/S1-bot.md`.
