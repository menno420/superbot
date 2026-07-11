# superbot · inbox

> ORDERS to this repo. **ONE writer: the fleet manager** — never edit or reorder an
> existing ORDER; **append-only** (new blocks at the end, next free number). superbot is
> the fleet **hub with no standing seat (Q-0264)**: ORDERs landing here are consumed by
> the **next hub-touching session**, not a standing lane seat. Executing sessions report
> progress in their `.sessions/` card + the durable doc the order names — an ORDER's own
> bytes stay untouched once written (status annotations ride later appends or slice
> records). Grammar (kit standard): `## ORDER <nnn> · <ISO8601> · status: <state>` with
> `priority` / `do` / `why` / `done-when` fields.

## ORDER 001 · 2026-07-11T04:31:00Z · status: done (executed by the relaying session itself — superbot PR #1977: `.sessions/README.md` template line added + this session's committed card carries `📊 Model: fable-5`)
priority: P3
from: fleet-manager manager — ORDER 010 per-lane relay (provenance: fm control/inbox.md ORDER 010 + fm docs/findings/model-matrix-2026-07.md; relayed via fm PR #63 → "superbot rides next contact", executed at this next contact via superbot PR #1977)
executor: superbot hub — next hub-touching session (no standing seat, Q-0264)
do: Model-attribution ground truth (fleet standing rule, family-level names only per Q-0262): (1) confirm the session-card template carries a `📊 Model:` line — add it if missing; (2) every fired session records the model family its own harness/environment reports (e.g. fable-5, opus-4.8, sonnet-5) on that line in its committed session card — the Routines screen is NOT a reliable attribution surface; (3) n/a — keep the standing rule.
why: the fleet model matrix (fm docs/findings/model-matrix-2026-07.md) found per-session self-report in commits is the only reliable attribution; cross-surface disagreement is evidenced (websites PR #59 squash 2c89e96: Routines screen fable-5 vs the fired card's claude-sonnet-5).
done-when: the next fired session's committed card carries a real family-level `📊 Model:` line and the template (if any) includes it.
