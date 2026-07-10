# Idea — pin the telemetry `model` short-name vocabulary (enum + validator)

> **Status:** `ideas` — not a plan, not approval. Source + the binding contracts win.
> **Subsystem:** none (agent-workflow / telemetry).

**Session ender (2026-07-10, forty-first Q-0107 reconciliation pass, band-#1920).**

## The gap

The `telemetry/model-usage.jsonl` feed (Q-0248/PL-004 model-allocation record, guard-enforced since
#1894) has a free-text `model` field. Every row so far reads `"fable-5"`, but the moment sessions run on
other tiers each one **guesses the label** — this pass had to decide between `opus-4.8`,
`claude-opus-4-8`, `opus 4.8`, and the exact `claude-opus-4-8[1m]` ID (which the undercover-mode rule
bars from pushed artifacts). Different sessions will resolve that guess differently, so the feed
fragments by inconsistent spelling of the *same* model — which silently defeats the whole point of the
dataset: the console's "Model & spend telemetry" lane and the kit-lab B2 paired-A/B analysis both
**group by `model`**, and `opus-4.8` ≠ `opus 4.8` ≠ `claude-opus-4-8` splits one model into three
buckets.

## The idea

Pin a tiny **canonical short-name vocabulary** for the `model` field — one enum, one home — and make the
`#1894` gate (or a sibling `check_dashboard_data` soft check) reject a telemetry row whose `model` isn't
in it. Concretely: a `telemetry/model-names.json` (or a constant list) mapping allowed short names
(`fable-5`, `sonnet-5`, `opus-4.8`, `haiku-4.5`, …) → optional display label, plus a one-line validator.
This **also resolves the undercover-ID tension explicitly**: the vocabulary is the *family* short name,
never the exact `claude-*[1m]` identifier, so a session records allocation honestly without leaking the
ID the collaboration rule keeps to chat.

## Why it's worth having

- Cheap (stdlib enum + ~5-line check), and the guard that would enforce it already exists (#1894).
- The feed is **brand-new and still tiny** — pinning the vocabulary now, before dozens of rows exist, is
  free; doing it after a fragmented month means a data-cleaning migration.
- It closes a real ambiguity this pass hit live (which is the Q-0089 bar — a genuine friction, not
  invented make-work): the "enforce, don't exhort" (Q-0132) treatment of a rule the README currently
  only describes in prose.

Route: kit-lab B2 dataset owns the canonical schema upstream (`substrate-kit/telemetry/README.md`), so
the superbot-local slice should stay a thin allowed-list that defers to the kit vocabulary when superbot
adopts — pair this with `command-surface-extractor-consolidation` under the warn-first checker kit.
