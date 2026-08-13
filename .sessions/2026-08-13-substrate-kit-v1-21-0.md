# 2026-08-13 — adopt substrate-kit v1.21.0 + disposition the 14 false-wall findings

> **Status:** `in-progress`
> **Run type:** kit adoption · docs-only
> Born-red: this card is the sole FIRST commit on the branch; the adoption and the
> wall dispositions land in the following commits; the `in-progress` → `complete`
> flip is the deliberate LAST commit.

## Order

Phase 2 of the substrate-kit v1.21.0 rollout wave. The owner named **both superbot
repos** as the first batch, live 2026-08-13. `superbot-next` landed first as the
one-version hop (its PR #606, merged and tree-verified); this repo is the larger,
adopt-shaped half and gets its own run — the two were deliberately never batched.

## Scope — and the freeze

**superbot is FROZEN as the behavioural oracle for the `superbot-next` rebuild**
(its own `docs/current-state.md` banner, OD-1). The owner's instruction settles what
that permits here: **kit method and records work is in scope; the repo's BEHAVIOUR is
not.**

So this session is **docs + the vendored kit distribution only**. Zero `disbot/`
runtime, zero migrations, zero tests, no dependency change, and — the part that took
a measurement to get right — **no CI workflow is installed or regenerated**, because
that would change how this repo lands PRs.

## Shape — `adopt` or `upgrade`? Measured, not assumed

The handoff left this open: with no vendored dist, does `bootstrap.py.new upgrade`
run at all, or is the flow `adopt`? Both were run against the real tree:

- `python3 bootstrap.py.new upgrade` → **exit 1**, `no state at /home/user/superbot
  (run init first)`, **tree untouched**. The upgrade path does not apply here.
- `python3 bootstrap.py.new adopt` → **exit 0**, and it is far too big for this repo.
  It touched **21 paths**: planted ~14 template docs (including a `docs/decisions.md`
  **beside superbot's existing `docs/decisions/` directory**), rewrote
  `.sessions/README.md` and `.gitattributes`, and **regenerated
  `.github/workflows/auto-merge-enabler.yml`**, dropping a host step (`Enable native
  auto-merge (merge commit)`). It then reported `NOT ENGAGED` — the gate stays red
  until three planted docs have their interview slots answered and a CI gate is
  wired.

**So neither documented path is what this repo needs, and that is the finding.**
A third, minimal path was measured and works: **vendor the dist and bump the pin,
nothing else.** `check --strict` then runs in full — every checker, all findings —
with no `.substrate/` state, no planted docs and no workflow change. That is what
this PR does. The `adopt` run was reverted in full (`git checkout -- . && git clean`),
verified clean before any of it was committed.

## Result

_(filled at close)_

## 💡 Session idea

`adopt` is written for an empty repo and `upgrade` for an already-adopted one, and
**superbot is neither** — it carries a v1.0.0 config pin with no dist, a shape the
kit has no command for. The minimal path that works (vendor + pin, then `check`)
is not documented anywhere; it was found by trying the two documented ones and
reading what they refused. Worth a kit-side `adopt --dist-only` (or at least a
line in the upgrade guide), because every long-lived repo that adopted early and
then drifted will hit exactly this, and the obvious move — run `adopt` — quietly
rewrites files a frozen repo must not lose.
