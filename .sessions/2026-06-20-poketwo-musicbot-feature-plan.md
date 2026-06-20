# 2026-06-20 — Pokétwo + MusicBot research report → feature mapping plan

> **Status:** `complete`

## Arc

Owner uploaded a research report on **Pokétwo** (Pokémon catching bot) and **JMusicBot**
(music bot) and asked: *"review this … create a plan so we can implement as much of these
features in a proper way."* Owner steered this session (in-session `AskUserQuestion`):
**plan only, build nothing yet**; music half = **architecture-review pack only** (respect the
Q-0041 voice gate, don't build playback). Docs-only; no runtime (`disbot/`) code.

## Shipped (PR #1180, docs-only)

- **`docs/planning/poketwo-musicbot-feature-mapping-plan-2026-06-20.md`** — the report→repo
  mapping. Core finding: **most Pokétwo mechanics already have a lane here** (catching =
  fishing/mining/pets; trading = the economy-marketplace roadmap; "one world" = the federated
  Explore hub), so the job is *extend + dock*, not clone. Every report feature classified
  EXTEND / BUILD / GATED / REJECTED / HAVE. Four net-new ungated anti-P2W lanes spec'd as
  PR-sized work: **A) Wild Encounters** (activity spawning — the one mechanic with *no* analog),
  **B) collection & filtering** (extend fishing/inventory), **C) quest/achievement** foundation
  (Q-0182-aware), **D) shiny/rare-variant** layer (cosmetic, not power). Anti-patterns section
  pins the standing decisions: no premium currency (Q-0039), no standalone marketplace (its own
  gate), no music now (Q-0041).
- **`docs/planning/voice-music-architecture-review-2026-06-20.md`** — the Q-0041-required
  voice/music decision pack: legal lane first (L1 self-host risk / L2 licensed-safe / L3 defer —
  the report's own DMCA history makes this decisive), infra reality (FFmpeg/Opus/±Lavalink, a
  second always-on service the repo has never needed), where a music subsystem lands on existing
  seams (control surface fits cleanly; audio transport is the new costly/risky part), speech-rec
  stays last. Ends with the ordered go/no-go decision that feeds Q-0041.
- **`docs/ideas/wild-encounters-activity-spawning-2026-06-20.md`** + README index entry — capture
  of the signature net-new mechanic.
- **Router Q-0186** — DISCUSS: which net-new lane to build first + wild-encounter spawn design +
  guardrail confirmation. The music pack feeds existing **Q-0041** (no new music Q-block — avoided
  duplicating).
- Homed both plans in `docs/planning/README.md` (S1 + S5); claim in `active-work.md`.

Verification: `check_docs.py --strict` ✓ · `check_plan_homing.py` ✓ (38/38 homed). No `disbot/`
code, so no mypy/pytest scope touched.

## Context delta (Q-0102 self-audit input)

- **Needed and pointed to well:** the `world_registry`/federated-hub plan, the
  economy-marketplace roadmap, and the Q-0039/Q-0041 router entries were all exactly where the
  orientation route said — the mapping wrote itself once those were read.
- **Needed but had to discover:** that **activity-based spawning has no analog anywhere** — only
  confirmed by a broad source sweep (two Explore agents), not by any single doc. Worth a one-line
  "what the bot does NOT have" inventory somewhere durable (see session idea).
- **Pointed to but didn't need:** the giant `current-state.md` ▶ Next-action paragraph — irrelevant
  to a report-mapping task; the *grep-for-the-live-sentence* cost is the same scaling smell the
  previous session flagged.

## Decisions made alone

- **No separate music Q-block** — routed the music decision into the *existing* Q-0041 (the voice
  gate it already owns) via the arch-review pack, rather than minting a duplicate. Reversible.
- **Recommended Lane A first** in Q-0186 (didn't pre-decide it) — engagement leverage + it feeds
  B/C/D; left the call to the owner-designer.

## Flagged for maintainer

- **Q-0186** — which net-new Pokétwo lane to build first + wild-encounter spawn defaults + confirm
  the anti-P2W/anti-spam guardrails. Nothing builds until answered.
- **Q-0041 (music)** — the arch-review pack is ready; owner makes the go/no-go + legal-lane (L1/L2/
  L3) call to lift the voice gate.

## 💡 Session idea (Q-0089)

**A durable "what the bot does NOT have" capabilities-gap inventory.** This session's highest-value
finding — that activity-based spawning, player-to-player trading, and quests have *no* code analog —
took two fan-out Explore agents to establish, because the repo documents what *exists* exhaustively
but never what's *absent*. A short, curated `docs/subsystems/capability-gaps.md` (or a section in the
games folio) listing "deliberately-absent / greenfield" mechanics would let a future feature-mapping
or competitive-analysis task answer "do we already have X?" without a full source sweep. Genuinely
useful, low-maintenance (only changes when a gap is filled); lane = docs/orientation. (Not built this
run — kept the PR single-purpose; clean grooming candidate.)

## ⟲ Previous-session review (Q-0102)

The previous run (`arch-ratchet-cog-layer`, #1163) extended the `baseview_inheritance` arch ratchet
to the cog layer — a genuinely good parity fix (the arch checker now matches the consistency linter's
cog scope) and it correctly *routed* the broader residence-guard decision instead of building it
unilaterally. **What it could've done better:** its own Q-0102 note already nailed the issue — the
`current-state.md` ▶ Next-action paragraph has grown to ~30KB on one logical line and the *live*
sentence is hard to find. I hit the exact same friction this run. **System improvement it surfaces
(and I second):** a future reconciliation pass should *physically truncate* the historical band-tail
out of ▶ Next action into the band pass-record docs it already links — the "trust THIS sentence,
never a lower ▶" convention is holding, but it's compensating for a layout problem that a 5-minute
trim would remove. Two consecutive sessions flagging the same ergonomics smell is the signal to act.

## 📤 Run report

- **Did:** turned the owner's Pokétwo/JMusicBot research report into a feature-mapping plan +
  music architecture-review pack; routed the build decisions · **Outcome:** shipped (docs-only)
- **Shipped:** #1180 — feature-mapping plan · voice/music arch-review pack · wild-encounters idea ·
  Q-0186
- **Run type:** `manual · owner-task`
- **⚑ Owner decisions needed:** Q-0186 (Pokétwo build sequence + spawn design) · Q-0041 (music
  go/no-go + legal lane, now that the arch-review pack exists)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed task; the wild-encounters idea + Q-0186 are *routed*,
  not built — no idea→plan→build promotion this session)
- **↪ Next:** owner answers Q-0186 → a runtime-verified session builds Lane A (Wild Encounters) in
  small PRs; music waits on the Q-0041 decision

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1180, docs-only, auto-merge armed on green) |
| Runtime (`disbot/`) code changed | 0 (plan-only, per owner steer) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| Docs added | 3 (2 plans + 1 idea) · 1 router Q-block · 4 index/claim edits |
| New ideas contributed | 1 (capability-gaps inventory) |
| Ideas groomed | 1 (wild-encounters captured + spec'd into Lane A) |
