# Per-sector live state

> **Status:** `living-ledger` — per-sector "what's true right now + next ▶" snapshots
> (owner decision **Q-0195**, 2026-06-22). The cross-cutting hub stays at
> [`../current-state.md`](../current-state.md); this directory splits its all-sector
> `▶ Next action` callout into one file per planning sector so a session dispatched to a
> sector reads only its lane.

The 5 planning sectors (Q-0137 · [`../repo-sector-map.md`](../repo-sector-map.md)):

| Sector | File | Scope |
|---|---|---|
| S1 | [`S1-bot.md`](S1-bot.md) | Bot product — the Discord bot users interact with |
| S2 | [`S2-btd6.md`](S2-btd6.md) | BTD6 vertical — runtime + offline data |
| S3 | [`S3-ai-memory.md`](S3-ai-memory.md) | AI-Memory system — the self-improving-agent mechanism |
| S4 | [`S4-docs.md`](S4-docs.md) | Documentation system — the content the engine produces |
| S5 | [`S5-ops.md`](S5-ops.md) | Operations / control-plane — deploy · secrets · loop |

**One-fact-one-home:** these files are *live snapshots* (what just shipped, what's the next
startable item, what's in flight). The authoritative **forward queues** are in
[`../roadmap.md`](../roadmap.md) per sector, and area detail lives in the subsystem folios —
link to them, don't restate them here. Merged-PR history stays in
[`../current-state.md`](../current-state.md) § Recently shipped (the ledger).
