# Idea — extend the pinned-feed-contract pattern to `dashboard.json`

> **Status:** `ideas` — not a plan, not approval. Captured 2026-07-09 (Q-0089 session
> ender, console-feed-contract session / PR #1884).
> **Subsystem:** none (cross-cutting, `scripts/` + `dashboard/data/` tooling)

## The gap

PR #1884 pinned the shape of `botsite/data/console.json` in a committed, versioned
contract (`botsite/data/console_data_contract.json`) because TWO repos render it —
superbot's botsite console and the **websites** repo's dashboard `/console` page —
and a producer-side rename silently blanked the consumer (the BUG-0022 class). The
first consumer-side validation pass immediately caught a live defect: websites'
console page treated the `ideas`/`bugs` families as *lists* when the feed ships
*dicts*, so its stat tiles showed dict-key counts.

But `console.json` is the **small** feed. The websites dashboard renders **~12
pages** off `dashboard/data/dashboard.json` (catalogue, cogs+commands, settings,
access, env-map, ideas, bugs, updates, synonyms…) — a far larger implicit surface
with **no contract at all**. Every one of those pages carries the same silent-break
risk the console just had, multiplied.

## The idea

Apply the now-proven pattern to `dashboard.json`, family by family (not one huge
schema in one go):

- `dashboard/data/dashboard_data_contract.json` — versioned, guaranteed fields per
  family/record, same semantics as the console contract.
- Producer parity + committed-file validation in `check_dashboard_data.py` (the
  checks already exist for counts/required-fields; this adds the contract file as
  the citable source of truth and `meta.schema_version` to the payload).
- websites pins the version + validates at render time (its `data_source.py`
  shaping helpers are exactly the field list to contract).

Start with the families websites actually renders (catalogue / cogs+commands /
settings / env_usage / ideas / bugs / updates / synonyms / access); leave
superbot-only families uncontracted until someone consumes them.

## Why it's worth having

- The cross-repo seam is the least-tested surface in the estate: no shared CI, no
  shared types, raw-URL fetch. A committed contract is the cheapest enforcing pin.
- The console PR proves the mechanism end-to-end (producer parity + fail-closed
  checker + consumer version check) — extending is mostly transcription.
- Kit angle: if this holds up across two feeds, "pinned feed contract" is a
  portable doctrine candidate for substrate-kit (any producer-repo → consumer-repo
  committed-artifact seam).
