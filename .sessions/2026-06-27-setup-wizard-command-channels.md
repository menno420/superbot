# Session — 2026-06-27 · Setup wizard: "Where can people use commands?" (per-channel command access)

> **Status:** `complete` — ready to merge (Q-0133). Run type: owner-directed (chat).

## What this run did

The owner flagged that the new **Essential Setup** wizard is missing **"allowed commands per channels"**
and asked me to find out whether the wizard covers everything ("a few other things might not be properly
integrated"). I investigated, confirmed it, mapped the surrounding gaps, and shipped the contained,
enforced, high-value half as **PR #1496**.

**Findings (the "find out" half):**
- The Essential spine covers the universal essentials well (server-type · greet · moderators · spam ·
  logging · rewards · help desk) + an Extras menu (7 features, all command-pointers verified live) +
  "Check my setup". The user's flagged gap is real: **"allowed commands per channel" is two distinct
  mechanisms, both absent from the new wizard.**
- **Command Access** (whole-server / chosen-channels / off-except-admins) — *is* enforced + cached today
  (`command_access_service` ← `core.runtime.command_access` gate) but lived only in `!settings`, never in
  setup. The bot's own denial copy even tells admins to fix it "via `!setup`" — with no such step.
- **`cog_routing`** (the literal per-feature per-channel toggle) — advanced-only **and not wired to
  runtime enforcement**: `is_cog_enabled` is read only by the read-only access-projection + the setup
  preview, never by a live command gate (access-projection axis 5 "central availability resolver" was
  never built). Surfacing it as-is would surface a no-op.

**Shipped (PR #1496):** new spine step 8 **`CommandChannelsStep` — "Where can people use commands?"** in
`disbot/views/setup/essential_setup.py`. Plain-language, button/dropdown-only, **direct-apply** through
the audited `command_access_service.set_policy` (lazy-imported per the no-top-level-pipeline-import
invariant; `actor_type="admin"`). Three outcomes → the three stored modes; "only chosen channels"
reveals a channel multi-select and refuses with no pick (won't silently lock the bot to zero channels).
Retroactively makes the existing "enable via `!setup`" denial copy true. No new primitive, no migration.

**Decision note (transparency):** the `AskUserQuestion` to confirm *which* mechanism the owner meant
failed to deliver in this remote env (permission-stream closed). Per the working agreement (act on the
contained/reversible/verifiable; the literal cog_routing reading would surface a no-op), I built the
enforced Command Access half and **deferred** the cog_routing-enforcement half to its own plan-first PR
(it touches the command hot-path; needs a cached read model). Captured as a routed idea so it isn't lost.

## Verification
- `essential_setup.py` step tests: +6 (57 → 64), all green. Full `check_quality.py --full` GREEN after
  the consistency fix below (**12754 passed**, 48 skipped, 2 xfailed).
- One consistency-linter snag fixed: the `_summary` `[:3]` display slice tripped the graduated
  `select_option_truncation` rule (a false positive — it's a summary string, not select options);
  rewrote to a count ("Commands limited to N channels"), no slice. Re-ran the graduated-rule test green.
- `check_architecture --mode strict` exit 0 (pre-existing baseview WARNs only — my step extends
  `_StepView`→`BaseView`, no new violation). Jargon guard: **0 findings** in `essential_setup.py`; the
  no-top-level-pipeline-import fence passes (service lazy-imported). `check_docs --strict` green.
- Mode strings pinned against `utils.db.command_access.KNOWN_MODES` (a test guards that every offered
  mode is a real stored mode — mocked service tests wouldn't otherwise catch a wrong literal).

## 💡 Session idea (Q-0089)
**Wire `cog_routing` to runtime enforcement** — captured as
[`docs/ideas/cog-routing-enforcement-gap-2026-06-27.md`](../docs/ideas/cog-routing-enforcement-gap-2026-06-27.md)
(+ README index). This is the genuine, directly-surfaced follow-up: the per-feature per-channel toggle is
configurable but enforces nothing; doing it right (cached read model in the command gate, default-true
preserved so it's byte-identical for guilds with no rows) is the honest completion of the owner's
"allowed commands per channel" ask. Plan-first (hot-path weight), not promoted unilaterally.

## ⟲ Previous-session review (Q-0102)
The previous run (2026-06-26 BTD6 eval-anchor coverage) did its best work in **guard-the-guard
discipline** — it proved its new coverage/distinctness guards actually fail against the drift they exist
to catch before trusting their green, which is exactly the "a green check that contradicts evidence is a
bug in the check" rule (Q-0120). It also left a sharp Q-0102 note that S1/S3/S5 ▶ items lack the
`(offline, self-mergeable)` tag S2 uses, costing orient-time. **System improvement this run surfaces:**
my investigation burned real time tracing whether `cog_routing`'s policy is *actually enforced at
runtime* (it isn't) — the kind of fact that should be discoverable without a repo-wide trace. A cheap,
durable fix: policy-style subsystems should carry an **"enforced? (which gate reads it)"** note in
`docs/ownership.md` / their folio, so the next agent reads "configurable, not yet enforced" instead of
re-deriving it. I applied the local version (the idea doc + plan both state it explicitly); the
generalizable convention is worth a router DISCUSS block if a third trace-to-confirm-enforcement recurs.

## Doc audit (Q-0104)
Plan `setup-wizard-restructure-plan-2026-06-24.md` ▶ Build progress gained a "Coverage follow-on" note
(new spine step 8 + the deferred cog_routing-enforcement finding). New idea file added + indexed in
`docs/ideas/README.md`. **No `current-state.md` Recently-shipped entry added** — convention is merged PRs
only; #1496 reconciles next pass (recon due at #1500). `check_docs --strict` + `check_consistency` green.
No owner decision recorded this run (owner-directed build; the mechanism-choice was a documented
in-session judgment call, not a new standing rule). Claim file to be deleted at close.

## 📤 Run report
- **Run type:** owner-directed (chat) — "find out if the new setup wizard covers everything; allowed
  commands per channel is missing + would be a great addition."
- **What shipped:** **PR #1496** — new Essential Setup spine step **"Where can people use commands?"**
  (Command Access: whole-server / chosen-channels / off-except-admins), direct-apply via the audited
  `command_access_service`, jargon-clean; +6 tests (57→64). Spine 7→8 steps.
- **⚑ Self-initiated:** the *scoping decision* only — chose to surface the enforced Command Access
  mechanism (not the unenforced `cog_routing`) and defer the latter, after the clarifying
  `AskUserQuestion` couldn't be delivered. The work itself was owner-flagged. Flagged here for review.
- **⚑ Owner-decisions:** none (no new standing rule; the mechanism choice is documented judgment).
- **⚑ Owner-manual-steps:** none — additive UI on the existing command_access tables; no migration, no
  seed/data step. Merge auto-deploys (`worker` redeploys on merge to `main`).
- **Deferred (documented):** `cog_routing` runtime enforcement + its plain-language surface — own
  plan-first PR ([idea](../docs/ideas/cog-routing-enforcement-gap-2026-06-27.md)).
- **Bug-book:** none touched.
