# 2026-07-02 — Rebuild linchpin validation: golden harness + grammar spike + go/no-go

> **Status:** `complete`
> **PR:** [#1639](https://github.com/menno420/superbot/pull/1639)
> **Branch:** `claude/superbot-linchpin-validation-tcyv25`

## What shipped

The two unproven linchpins gating the Phase-3 rebuild, **built and measured** — the owner-gate
evidence package. Full readout:
[`docs/planning/rebuild-linchpin-validation-2026-07-02.md`](../docs/planning/rebuild-linchpin-validation-2026-07-02.md).

1. **The golden behavioral harness (Phase 0.5)** — [`parity/`](../parity/README.md). The real bot
   (`bot1.bot`, all 58 extensions, real governance guard/error handler/converters/cooldowns/view
   store) driven in-process by synthetic gateway payloads through the real discord.py
   `ConnectionState`, with ONE fake seam (HTTP out). Captures embeds/components/DB row-deltas/bus
   events per case. **Replay-deterministic** (`capture` → `check` byte-identical at full-corpus scale; EIGHT
   nondeterminism classes found and pinned, each by a replay diff: wall-clock `time.time` in
   services, snowflake-encoded cooldown time, spawned-task attribution, `delete_after` timers,
   uuid/auto-custom_id randomness, volatile DB columns, wall-clock view timeouts, and
   position-dependent clock state — the last fixed with per-case hash-derived clock bases so
   `--only` captures equal full-run replays). Corpus: **465 golden cases** (460 gating + 5 named advisory; 11 curated multi-step flows + a
   mechanical sweep over every enumerable command, hidden included). **Final gating replay
   459/459 green.** **Coverage (live denominators): prefix 390/406 = 96% · slash 64/73 = 88% ·
   panel components 60/64 = 94% · panels 9/11 = 82% · events 10/47 = 21% · tables 26/105 = 25% ·
   settings-key mutations 3/120 = 2%** — invocation breadth ~done (every exclusion reasoned),
   deep-state dimensions named as the port bands' curated work (`parity/COVERAGE.md`). Capture-integrity guard: an outbound call the fake doesn't model FAILS
   the case loudly (caught 4 real gaps across the sweep).
2. **The grammar-expressiveness spike** — [`tools/grammar_spike/`](../tools/grammar_spike/__init__.py)
   (explicitly labeled; NOT the kernel; nothing imported by disbot/). Faithful §2 spec prototype
   (S/A/O metadata, §3.2-phase-1 validators) + three complete source-cited real manifests
   (karma / server-logging / blackjack) + a 95-unit judgment-ledger measurement
   (`RESULTS.md`). **Tier-1/2 fit: 73% as-specced → 85% with six proposed amendments; operator
   band 97%; games 44% by design.** Six grammar findings (G-1 GatewayListenerSpec — the
   load-bearing one; G-2 list-valued settings; G-3 AnnouncementRouteSpec; G-4 command cooldowns;
   G-5 declarative bounds; G-6 command-pool kind-scoping) — each exercised in the prototype +
   tests.
3. **The go/no-go synthesis** — verdict **GO with the amendments folded into the design spec
   before K2**. Homed in the planning README rebuild table, S3 sector state, roadmap S3 Now,
   current-state ledger, and back-referenced from the design spec + strategy Phase-0.5.

Tests: `tests/unit/parity/` (machinery, DB-free, in CI) + `tests/unit/tools/test_grammar_spike.py`
(manifests construct; compile rules fire; ledger consistent) + an opt-in full round-trip
integration test (`PARITY_INTEGRATION=1`). Optional manual-dispatch CI workflow
`parity-replay.yml` (Postgres service; never required) proves the Actions shape the rebuild's
`golden-parity` gate uses.

## Rails honored

No `disbot/` behavior changes (verified: diff touches no `disbot/` file). No `sb/` code. §5.3
freezes untouched (the harness + manifests *pin* frozen ids/events/keys, weakening nothing).
Goldens live in this repo — outside the future new repo's write reach.

## Context delta (the reflection interview)

- **Route miss:** none serious — the orientation route (CLAUDE.md → collaboration-model →
  current-state → journal → design spec) was exactly right for this task.
- **Discovered by hand (worth banking):** (1) discord.py's mention regex requires 15–20-digit ids
  — 8-digit fake snowflakes silently break MemberConverter with a misleading "no websocket"
  error; (2) `Message.created_at` (and command cooldowns) derive from the SNOWFLAKE, not the
  payload timestamp — a deterministic driver must encode its clock in its ids; (3)
  `bot._async_setup_hook()` is the one call that makes a gateway-free `commands.Bot` dispatchable;
  (4) `interaction.response.defer` reads `http.proxy` as a plain attribute — a fake HTTP object
  needs data attrs, not just methods; (5) `tree._http` is captured at Bot construction and must be
  swapped separately. All five are encoded in `parity/harness/` comments + README.
- **Decisions made alone:** the driver architecture (fake HTTP over real state vs dpytest — no
  new dep, higher fidelity); measuring grammar fit as a disputable per-unit judgment ledger
  rather than an opaque score; adding the optional non-required parity workflow; extending
  pyproject per-file-ignores for the parity CLI (mirrors the existing tools/ convention).
- **Weak point of what shipped:** sweep coverage is breadth (one synthesized invocation per
  command, admin persona) — subcommand paths behind arg branches and most panel *click* flows
  are uncovered (named in COVERAGE.md); usage-weighted coverage needs the prod telemetry scrape.
- **One change that would have helped:** a documented "how to drive discord.py offline" note —
  now exists as `parity/README.md` § determinism model.
- **🛠 Friction → guard:** the capture-integrity guard (fake-HTTP gaps fail cases loudly) was
  built mid-session after watching a gap get silently swallowed into a golden by the bot's own
  error handling — the exact "checker that lied" class Q-0194 names; it's now enforcing, in-tree,
  and caught 3 further gaps the same day. Also `tests/unit/parity/test_harness_machinery.py::
  test_committed_goldens_are_normalized` — a CI-level guard that dirty (unnormalized) goldens can
  never land silently.

## ⚑ Self-initiated (Q-0172 accountability line)

The session prompt named all three deliverables, so nothing here is an unprompted build lane;
self-initiated *within* it: the `parity-replay.yml` optional workflow, the pyproject parity-CLI
lint convention, the G-1…G-6 grammar amendments as concrete spec proposals, and the doc
back-references into the design spec / strategy / vision idea.

## 💡 Session idea (Q-0089)

**Behavioral-coverage ratchet for the rebuild:** once Phase 4 starts, wire
`parity/COVERAGE.md`'s summary numbers into a tiny checker that fails a port-band PR if any
coverage dimension DROPS vs the merge base (new surfaces may lower the fraction only with an
explicit uncovered-tail entry). This turns the spec's "coverage notes at every flip" from
discipline into a machine gate — the same enforce-don't-exhort move that fixed the docs-drift
class (Q-0132). Filed inline here (small, mechanism-clear); dedup-checked against `docs/ideas/`
(nothing existing covers behavioral-coverage ratcheting).

## ⟲ Previous-session review (Q-0102)

The 2026-07-02 design-spec revision session (#1638) did something genuinely hard well: it folded
two external GPT review rounds into an already-dense spec without breaking its internal
citations, and its **declined-with-reasons list** (footnote-izing citations, splitting the doc)
is exactly the right shape for owner-facing honesty. What it missed — and what this session
existed to fix — is that it left the spec's two scariest claims (harness coverage, grammar fit)
as *assertions* when both were cheaply testable without the gate; the review round even named
them as risks 1 and 5 without proposing the spike. **Workflow improvement:** when a design
review names a risk as "the ceiling on safety" or "asserted, not proven," the review's output
should include the *cheapest experiment that would measure it* — a one-line "provable now by X"
tag per top risk. That single convention would have started this session's work a day earlier.

## Close-out checklist

- [x] current-state ledger entry (#1639) + `Last updated` stamp + S3 sector row/file + roadmap S3 Now
- [x] planning README rebuild table row; design-spec + strategy + vision-idea back-references
- [x] claim file deleted at close
- [x] check_quality --full + check_architecture strict + check_docs --strict green (final head)
- [x] full-corpus replay green (`python3.10 -m parity.run check`)
