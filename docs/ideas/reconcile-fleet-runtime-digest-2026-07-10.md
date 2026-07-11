# Idea — fleet-runtime digest line in the reconciliation pass record

> **Status:** `ideas` — raised by the band-#1950 (forty-second) Q-0107 reconciliation pass (2026-07-10).
> Lane: S4 (docs system) / S3 (engine tooling). Size: small, `ready`-adjacent — originally framed as
> extending the `check_manifest_freshness.py` git-transport reader shipped in #1923; that checker was
> **retired in #1974 (2026-07-11)** with the fleet-manifest supersession, so an implementation would
> read the fleet-manager generated roster (`menno420/fleet-manager` `docs/roster.md`) or the lane
> heartbeats directly (the same shallow-fetch technique, reimplemented locally).

## The problem

For roughly the last **ten consecutive bands**, the superbot Q-0107 pass has recorded the same
sentence: *"the band is **entirely docs/tooling**, zero `disbot/` runtime logic."* That is **true and
not a failure** — the actual runtime product work has migrated to sibling repos: the rebuild lives in
`superbot-next`, the game work in the games projects, the substrate engine in `substrate-kit`, and the
EAP program spans the whole 10+-Project fleet. The superbot repo has become the fleet's **docs /
coordination substrate**.

But the superbot ledger (`current-state.md` Recently-shipped + the pass records) only reconciles
superbot's *own* merges. Read in isolation it now paints a misleadingly-quiet picture: band after band
of "docs-only, nothing shipped" while the fleet is, in fact, building the whole next-generation bot in
parallel. A reader (owner, a fresh agent, Hermes) who orients from superbot's ledger alone cannot see
that the program is *accelerating* — the runtime progress is invisible because it is in other repos.

## The idea

Have the reconciliation pass emit a one-line **fleet-runtime digest** in the pass record (and optionally
the `current-state.md` narrative), computed from the sibling repos over the same git-transport
technique the retired `#1923` `check_manifest_freshness.py` proved out (shallow fetch + `cat-file`):

> *Fleet this band (2026-07-XX): `superbot-next` +N merges (Phase-B Sxx), `superbot-games` +M,
> `substrate-kit` +K, `venture-lab` +J. superbot itself: docs-only (this pass).*

Mechanically: a small `scripts/fleet_band_digest.py` (or a `--digest` flag on the freshness checker)
that, for each manifest repo, shallow-fetches and counts merges since a timestamp/SHA and reads the
lane's `control/status.md` headline. It reuses the exact transport already proven in agent containers
(REST API is proxy-blocked — the #1923 idea file records this), stays **advisory / warn-only /
Q-0105-disposable**, and is **never a merge gate**.

## Why it is worth having

- **Truthful ledger.** The superbot ledger stops implying "the program stalled" when the program is
  actually shipping hard next-door — the single biggest orientation trap a docs-only substrate repo
  creates.
- **Distinct from the band-archetype classifier** (`band-archetype-classifier-2026-06-24.md`), which
  measures the *intra-superbot* queue-executed-vs-owner-directed ratio. This measures *cross-repo*
  runtime velocity — the two compose (archetype = "is superbot's own queue driving itself?"; digest =
  "where is the fleet's real building happening?").
- **Cheap and already-wired.** The read path exists; this is one small consumer of it, homed in the
  reconciliation routine's runbook where the freshness check already runs.
- **Gen-3 aligned (Q-0259 §2).** Gen-3's mandate is *verify-and-consolidate + give every project a
  clear goal*; a per-band fleet-runtime digest is exactly the consolidation readout that mandate wants.

## Not now / open questions

- The manifest's `Last-seen` timestamps must be trustworthy for the merge-count window (the #1923 first
  run already found 2 stale rows) — the digest should degrade to "n/a (stale manifest)" per repo rather
  than fabricate a count.
- Whether the digest belongs in every pass record or only the `current-state.md` narrative is a
  presentation call for the executor.
