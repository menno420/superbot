# 2026-08-13 — adopt substrate-kit v1.21.0 + disposition the 14 false-wall findings

> **Status:** `complete`
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

Landed on PR #2436. Vendored `bootstrap.py` at **v1.21.0**, `substrate.config.json`
pin `1.0.0` → `1.21.0`, and all **14 false-wall findings dispositioned**. Zero
`disbot/` runtime, zero migrations, no dependency change, **no workflow added or
regenerated**.

### One lint-scope change, and why it was unavoidable

Vendoring the dist turned `code-quality` red: `ruff format --check` reported
**"1 file would be reformatted, 1040 files already formatted"** — the new
`bootstrap.py`. The kit's generated dist is not ruff-formatted, and **reformatting
it is the one thing that must never happen**: its sha256 is the adoption proof, and
rewriting a byte forks this adopter from the published asset (the fm #833 doctrine
against patching a vendored dist).

So `bootstrap.py` joins the ruff exclude list. superbot deliberately mirrors that
list in **four** places, and a parity test pins them together:

- `.github/workflows/code-quality.yml` — both the `ruff format` and `ruff check` lines
- `scripts/check_quality.py` — `_RUFF_EXCLUDE`
- `pyproject.toml` — `[tool.ruff] extend-exclude`
- `tests/unit/scripts/test_check_quality_ci_parity.py` — `_EXPECTED_DIRS`, the
  hard-coded canonical set the other three are checked against

All four updated together. `ruff format --check` with the new scope: **1040 files
already formatted, exit 0**. The parity test cannot run in this container
(`ModuleNotFoundError: No module named 'discord'` — pre-existing, identical on
`main`), so its five assertions were re-implemented and run directly against the
three files: **all pass**.

This is a **lint-scope** change, not a behaviour change: `code-quality` remains the
required check, runs on the same events, and gates merges exactly as before. The
only difference is that it no longer tries to reformat a file it must not touch.
mypy needed no change — CI runs it only against `disbot/`.

**sha256:** `8807a00e0e7f14f61f37f2afb48bcb38e4b7247b10741761ff99630bf9cc7356` —
agreeing across the released asset, the `sha256` field in `release.json`, the sidecar,
the kit's committed `dist/bootstrap.py` at the release commit `0021adc`, and
fleet-manager's already-adopted copy. **No rollback is banked and none applies**:
there was no prior vendored dist to bank. The rollback here is `git revert`.

### The 14 wall findings — 3 corrected, 11 allowlisted

**Corrected in place** (the claim was genuinely wrong and rewording preserves intent):

| file | was | now |
|---|---|---|
| `docs/operations/hermes-operating-prompt.md` | an instruction that Hermes does not merge PRs | reframed as a workflow preference, with merging named as a first-class agent path when auto-merge is slow |
| `docs/operations/mcp-servers.md` | one owner-only console generalised into a standing wall on setting environment secrets | scoped to that console, notes GitHub/Railway *are* agent-settable, and says plainly that this console is **untested** rather than blocked |
| `docs/owner/product-catalog.md` | release creation listed as an owner click because agents were said to be refused | repudiated and dated — that generalised a *proxied-route* refusal; release creation works via `workflow_dispatch` and the direct-credential path |

**Allowlisted** — nine reasoned entries in `.substrate/check-exceptions.yml` covering
eleven findings, each with a required non-empty reason (the seam is fail-closed: a
reason-less entry suppresses nothing and reports itself). Every one is the checker
matching a **quoted or recorded** wall rather than a live claim, and in four cases the
sentence's own purpose is to **refute** the wall it quotes:

- `docs/current-state.md` ×2 — the ledger recording PR #2145, the "dewall" that *removed*
  the false merge wall. The quoted phrase is the thing deleted.
- `docs/eap/gen1-wrapup-email-final-candidate.md` · `docs/owner/maintainer-question-router.md:9927`
  — verbatim classifier quotes, one inside an owner-facing email to Anthropic. The quote
  is the evidence.
- `docs/eap/screenshots-2026-07-11/index.md` — a caption that must match what the
  screenshot shows.
- `docs/owner/fleet-vocab.md` · `.claude/CLAUDE.md` — the estate's own **anti-wall
  instruction**, telling sessions never to generalise a refusal into a standing wall.
- `docs/owner/maintainer-question-router.md:3383/3399` — a verbatim 2026-06-10 question
  and a durable conclusion that the same file later supersedes (Q-0084, Q-0113).
- `docs/operations/hermes-dispatch-bridge.md` · `router:4343` — the deliberate Q-0114
  feature carve-out, a scope boundary the owner chose, on the very line that *grants*
  self-merge.

Two corrections had to be written twice: quoting the old wording verbatim **re-triggered
the scanner on the correction itself**. The fix was to describe the old phrasing instead
of reproducing it — worth knowing, because the obvious way to write an honest correction
is the way that fails.

### Verify — and the gate is NOT green

`python3 bootstrap.py check --strict`, exit code read directly: **16 findings → 2**.
`GATE_EXIT=1`. The two survivors are both out of scope under the freeze, and are
**flagged rather than suppressed** — an allowlist entry would have bought a green gate
by hiding a true finding, which is the false-green defect (PL-006) this repo's own
checkers exist to catch:

1. **`enforcement-unwired`** — no CI workflow runs `check --strict`. Installing one
   changes how this repo lands PRs. It would also be **red from day one** (finding 2),
   so it would decorate every PR — including the six open dependabot PRs — with a
   permanent failure.
2. **`orientation-budget`** — the boot-read set is **17,664 words against a 7,000-word
   budget** (`docs/current-state.md` 13,603 · `docs/AGENT_ORIENTATION.md` 4,061).
   Fixing it means trimming or demoting a boot doc on the frozen oracle: a real records
   restructure and its own decision, the same call the owner reserved for fleet-manager's
   identical finding.

Also observed, advisory and never exit-affecting: `automerge-branch-drift` — the
installed enabler arms `{claude/*}` while config (which has no `automerge` key at all)
would regenerate `{claim/*, claude/*}`. **This is the advisory the handoff attributed to
`superbot-next`; it is this repo's.** On `superbot-next` the real drift ran the other way
— six prefixes narrowing to one.

## Context delta

- **`upgrade` and `adopt` are the only two documented paths, and this repo fits neither.**
  A v1.0.0 pin with no vendored dist is a shape the kit has no command for: `upgrade`
  refuses outright, `adopt` over-corrects into 21 paths and a workflow regen. The working
  third path — vendor the dist, bump the pin, run `check` — is documented nowhere and had
  to be found by running both documented ones and reading their refusals.
- **A correction that quotes the thing it corrects still trips the scanner.** Two of three
  in-place fixes failed their first attempt for this reason. Any future wall-disposition
  pass should expect it.
- **The allowlist parser accepts flat single-line mappings only** — no folded `>-` or
  block `|` scalars. The first version of `check-exceptions.yml` used `>-`, and every
  continuation line came back as its own `allowlist` finding while the entries themselves
  still applied, so the suppression *worked* while the file *reported as broken*. That
  combination is easy to misread as success.


## 💡 Session idea

`adopt` is written for an empty repo and `upgrade` for an already-adopted one, and
**superbot is neither** — it carries a v1.0.0 config pin with no dist, a shape the
kit has no command for. The minimal path that works (vendor + pin, then `check`)
is not documented anywhere; it was found by trying the two documented ones and
reading what they refused. Worth a kit-side `adopt --dist-only` (or at least a
line in the upgrade guide), because every long-lived repo that adopted early and
then drifted will hit exactly this, and the obvious move — run `adopt` — quietly
rewrites files a frozen repo must not lose.
