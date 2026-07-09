# 2026-07-09 — substrate-kit v1.0.0 pin file (kit-lab D2, consumer half)

> **Status:** `complete`

## What I did

substrate-kit **v1.0.0** is released
([tag](https://github.com/menno420/substrate-kit/releases/tag/v1.0.0),
`bootstrap.py` sha256
`5e518d4978a01926057bdece04d88bd5f1b7d433bbc19b36790bdeff14149313`). Per the
kit-lab founding plan §4.2 (the named KL-1 companion deliverable), superbot now
records its version pin in a **root `substrate.config.json` next to the
in-tree `substrate-kit/` copy**:

- `kit_version: "1.0.0"` — the pin D2 verifies on ("`substrate.config.json`
  has `kit_version` in both consumers").
- `project_id: "8155d8c4a73f"` — the id the §9.1 friction-report envelope
  needs (plan P9: superbot's `project_id` "comes from the KL-1 pin file").

Minimal hand-authored shape on purpose: superbot is **not an adopted install**
(no `.substrate/`, its own session tooling), so the file carries only the pin
record, not a full kit config. The sha256 above is recorded here for the
session record; per §4.2 it is verified at upgrade time against
`release.json`, not stored in the config. The sibling PR
(superbot-next#42) landed the adopted-consumer half (declared `kit_version`
key + the §3.4 `reconciliation_prs` 20→30 stale-default fix).

**Explicitly out of scope (plan's honest scoping):** deleting the in-tree
`substrate-kit/` source dir — a named follow-up superbot chore. Superbot keeps
participating in B2/friction by hand until it truly adopts.

Docs/config-only; zero `disbot/` runtime. `check_quality.py --check-only`
green.

## Context delta

- **Needed but not pointed to:** nothing repo-side; the authoritative spec
  lives in the kit repo (`docs/planning/kit-lab-founding-plan-2026-07-07.md`
  §4.2/§3.4/§9.1) — cross-repo sessions should fetch kit main first.
- **Pointed to but didn't need:** n/a.
- **Decisions made alone (decide-and-flag, Q-0240):** pin-file shape = minimal
  two-key JSON (not the kit's full `Config` serialisation) because superbot is
  not an adopted install and a full config would imply machinery that isn't
  installed here; `project_id` minted with the kit's own scheme
  (`uuid4().hex[:12]`).

## ⚑ Self-initiated

None — the whole session is the owner-directed D2 consumer deliverable.

## 💡 Session idea

`scripts/check_docs.py` (or a tiny new checker) should learn the pin file:
assert root `substrate.config.json` parses, `kit_version` is valid semver, and
— once superbot truly adopts — matches the vendored dist's stamped version.
Cheap enforce-don't-exhort guard so the pin can't silently rot or get dropped
by a stray edit (the kit's own pre-1.0 `from_dict` round-trip strips unknown
keys — exactly the class of silent loss a one-assert checker catches).

## ⟲ Previous-session review

Previous session (EAP fleet sequencing correction, 2026-07-09) recorded a live
owner correction verbatim, same-day, into the fleet plan doc with an explicit
"Corrected launch scope" section instead of rewriting history — exactly the
right ledger discipline, and its Context-delta section was genuinely
informative. Improvement it surfaces: owner corrections that change an
*already-shipped* plan doc currently rely on the session noticing every
downstream doc that cites the old scope; a grep-for-citations step in
`/session-close` (list docs linking the edited plan) would mechanize that
sweep. This session's own workflow note: the kit-lab task briefs now span
three repos — the claim + born-red-card + auto-merge ritual worked unchanged
cross-repo, no friction to convert.

## Documentation audit

- `python3.10 scripts/check_current_state_ledger.py --strict` — green (my PR
  is unmerged at write time; the next Q-0107 pass records it — benign
  newest-merge lag per Q-0166, marker at #1861).
- `python3.10 scripts/check_docs.py --strict` — green.
- New root file `substrate.config.json` is referenced from this log + PR
  #1879; the kit-side ledger (kit repo `docs/current-state.md`) already
  described D2's consumer half as pending-by-consumer-PR — the kit-lab loop
  reconciles it on merge.
- Backlog grooming (Q-0015): skipped this session — focused cross-repo
  owner-directed deliverable; noted honestly rather than doing token
  grooming.

## Close

Claim file `docs/owner/claims/claude__kit-version-pin.md` deleted at close.
PR #1879 opened ready + auto-merge (squash) armed at open; the session gate
holds it red until this badge flip lands, then it merges on green CI.
