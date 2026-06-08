# Idea-to-roadmap mapping session — 2026-06-08

## Goal and result

Consolidated the current idea backlog into one lifecycle inventory and eight roadmap-shaped routing/planning drafts without implementing runtime features. The pass preserves current authorities, keeps server management as the active lane, aligns AI extensions under the authoritative AI roadmap, preserves ADR-002/ADR-006/ADR-007 boundaries, and routes product-sensitive decisions to Q-0038–Q-0042.

## Live PR verification

Attempted before trusting in-repo snapshots. `gh` is unavailable and this checkout has no configured Git remote, so live GitHub open PRs could not be verified from this environment. No live-PR claim was inferred. Future promotion sessions must verify live PRs in a connected checkout.

## Docs created

- `docs/planning/idea-roadmap-inventory-2026-06-08.md`
- `docs/planning/social-community-progression-roadmap-2026-06-08.md`
- `docs/planning/economy-marketplace-rewards-roadmap-2026-06-08.md`
- `docs/planning/games-mining-idle-roadmap-2026-06-08.md`
- `docs/planning/server-management-extension-routing-2026-06-08.md`
- `docs/planning/integrations-media-voice-website-roadmap-2026-06-08.md`
- `docs/planning/ux-discoverability-mobile-roadmap-2026-06-08.md`
- `docs/ai/ai-product-extension-routing-2026-06-08.md`
- `docs/btd6/btd6-product-extension-routing-2026-06-08.md`

## Lifecycle outcomes

- New roadmap drafts: social/community/progression; economy/marketplace/rewards; games/mining/idle; integrations/media/voice/website; UX/discoverability/mobile; BTD6 product extensions.
- Routing addenda, not competing plans: AI product extensions; server-management/setup/access/routine extensions.
- Existing plans retained: mining wire, adaptive setup/access/routine, authoritative AI roadmap/tool/orchestration plans, server-management trackers, interface/mother-hub/command backlogs, games deferred actionability.
- Blocked/rejected boundaries retained: no AI action tools now, no BTD6 extraction bypass, no Redis/restart-safe games, no duplicate simulators/panels/helpers/dashboards, no arbitrary automation, no unreviewed provider/media/voice work.
- Open questions: Q-0038 guild tenancy/identity; Q-0039 VIP/donation fairness; Q-0040 AI DM posture; Q-0041 integrations/voice privacy/provider posture; Q-0042 website product/control-plane posture.

## Source verification notes

Manual source-tree verification confirmed the existing economy, game-state, blackjack, mining, AI, BTD6, access/setup/moderation, and YouTube/media seams named in the drafts. No `disbot/*.py` file was opened or modified, so no source context map was required. CodeGraph tooling was not available as a configured command/resource in this environment; manual `find`/`rg` and the generated context index were used instead.

## Context delta

### needed-not-pointed

- A connected-checkout fallback recipe for mandatory live PR verification when `gh` or a Git remote is absent.
- A dedicated social/economy subsystem folio only if those domains are later approved; creating one now would prematurely invent ownership.
- A canonical release-manifest owner for changelog/balance notices.

### pointed-not-needed

- Generated context packs beyond `docs/agent/index.yml`; the index and folios were sufficient, and generated packs were not edited.
- Most 2026-06-07/08 session journals; current plans/folios and the owner-vision capture already explained the current routing.
- CodeGraph commands; no usable CodeGraph interface was exposed in this environment.

### discovered-by-hand

- The source tree already contains canonical economy, game-state, mining, AI, BTD6, access, setup, moderation, and shared YouTube/media seams that future plans must extend.
- There is no approved social/guild or voice owner, which makes owner/architecture decisions mandatory before schema planning.
- The owner-selected “quick-win” labels do not clear lifecycle promotion gates; most ideas still need balance, privacy, authority, or product decisions.

## Validation

Run after edits:

- `python3.10 scripts/check_docs.py`
- `python3.10 tools/agent_context/validate_pack.py`
- `python3.10 scripts/check_architecture.py --mode strict`

## Recommended handoff

First Opus product revision: social/community/progression after Q-0038. First safe executable candidate remains the separately approved mining-wire plan; UX mobile audit/read-only Help routing are possible bounded Sonnet planning/execution candidates only when selected by the authoritative interface lane. AI actions/events/DM, BTD6 extensions, integrations/voice/web, analytics, poker concurrency, and cross-server social identity remain mapping-only or gated.
