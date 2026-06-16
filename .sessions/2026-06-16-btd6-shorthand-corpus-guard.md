# Session — BTD6 shorthand corpus regression guard

> **Status:** `in-progress`

## About to do

Continuation of the code-expertise-research session (PR #994 merged). Picking up the
standing secondary task — **Q-0015 backlog grooming**: execute the strongest small/safe/
decided-lane idea, `docs/ideas/btd6-shorthand-corpus-eval-2026-06-16.md`.

Ship a single **class-guard regression test** — `tests/unit/services/test_btd6_shorthand_corpus.py`
— holding the canonical BTD6 community-shorthand vocabulary (`despo`/`impop`/round `r53`/
`420 farm`/`d67`/…) and asserting each routes to `AITask.BTD6_ANSWER`, plus the conservatism
negatives (`r2d2`, "67 degrees outside", "a degree in CS", "how do I farm coins") that must
stay general. Guards the recurring "shorthand falls to the unguarded general path → model
freelances" bug class (BUG-0001/0003/0004/0008/0015), which today has only scattered per-bug
tests. Routing-only, no DB. Then re-badge the idea file `historical` ✅.
