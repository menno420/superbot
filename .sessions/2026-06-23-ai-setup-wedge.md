# 2026-06-23 — AI natural-language setup wedge (`/setup-describe`)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Owner-directed (chat: "continue from where you left off" → the AI-setup wedge I teed up after the
> positioning doc named it the highest-leverage next build). PR #1355 auto-merges on green (Q-0123).

## Arc

The positioning north-star (#1352) named the **AI-setup wedge** — *"describe your server, it
configures itself"* — as the one capability that's both a genuine "whoa" demo and structurally hard
for incumbents to retrofit. Orientation found the infrastructure **already largely exists**:
`services/setup_ai_advisor.OpenAISetupAdvisor` turns a `GuildSnapshot` into a schema-validated
`SetupPlanDraft`, and `views/setup/ai_review/AIReviewPanelView` renders that draft → accept →
`operations_from_recommendations` → the audited Final Review apply path. The **only missing piece**
is a *natural-language input* path — folding the operator's free-form description into that prompt.

This PR adds exactly that, reusing everything else.

## Plan (this PR)

- `OpenAISetupAdvisor.suggest_with_description(snapshot, description)` (+ a shared private `_run`) —
  folds the operator's description into the prompt/payload; reuses the existing JSON schema,
  `_validate_ai_payload`, gateway, and degraded handling unchanged.
- `services/setup_natural_language_advisor.suggest_from_description(...)` — thin entry: builds the
  configured advisor, uses the description only when the AI advisor is available, else falls back to
  the deterministic snapshot-only plan (description simply unused, never an error).
- `cogs/setup/_describe_entry.py` — snapshot → advisor → open the existing `AIReviewPanelView`
  ephemerally (admin-gated; apply stays gated by `can_apply_setup` inside Final Review).
- `/setup-describe <description>` + `!setupdescribe` commands in `setup_cog` (thin delegators).
- Tests for the advisor + the NL entry.

**Contained + reversible:** no new mutation code — the proposal flows into the existing audited
apply seam, applied only on explicit operator confirmation. Resource *creation* (vs binding existing
channels/roles) stays a follow-up (the recommendation schema is binding-only today).

## Shipped (PR #1355)

- **`services/setup_ai_advisor.py`** — `OpenAISetupAdvisor` gained `suggest_with_description` and a
  shared private `_run(snapshot, *, description)`; `suggest` now delegates to `_run(description=None)`
  (existing callers `setup_advisor_review` / `launcher` unchanged). When a description is present it
  appends `_DESCRIPTION_DIRECTIVE` to the system prompt and adds `operator_description` to the
  payload; everything else (schema, `_validate_ai_payload`, gateway, degraded handling) is reused.
- **`services/setup_natural_language_advisor.py`** (new) — `suggest_from_description(snapshot,
  description, *, advisor=None, provider=None)`: folds the description only when the resolved advisor
  is the OpenAI adapter and the text is non-empty; otherwise plain snapshot-only `suggest` (the
  deterministic fallback can't use free text → description dropped, never faked). `draft.source`
  reports which path ran.
- **`cogs/setup/_describe_entry.py`** (new) — slash + prefix entry points: snapshot → advisor → open
  the existing `AIReviewPanelView` (accept → `operations_from_recommendations` → audited Final Review
  apply). Fail-safe (`collect`/advisor errors → friendly note), bounded description (600 chars),
  `safe_defer` for the LLM round-trip, and a "AI not configured, names used instead" note when the
  plan came from the deterministic fallback.
- **`cogs/setup_cog.py`** — `/setup-describe <description>` + `!setupdescribe` (alias `describesetup`),
  admin-gated, thin delegators.
- **Tests:** `tests/unit/services/test_setup_natural_language_advisor.py` (4 — fold / blank-skip /
  deterministic-ignores / CI default) + 2 in `test_setup_ai_advisor.py` (folds & still validates ·
  plain suggest omits the field).
- **Regenerated:** `dashboard/data/dashboard.json`, `botsite/data/site.json`, `botsite/site/data.js`
  (commands 386 → 388), `docs/operations/env-vars.md` (line-number citations shifted by the advisor
  edit). Pinned the new `/setup-describe` slash route in `test_command_surface_ledger`.

## Why it's contained + reversible

No new mutation code: proposals flow into the **existing audited apply seam** and only on explicit
operator confirmation (`can_apply_setup` still gates Final Review). The advisor stays read-only
(its no-DB / no-`guild.create_*` invariants still hold). Resource **creation** (vs. binding existing
resources) is a clean follow-up — the recommendation schema is binding-only today.

## Verification

- `python3.10 -m mypy disbot/` → no issues (821 files); formatters/lint via
  `check_quality.py --check-only` → all checks passed.
- `check_architecture --mode strict` → 0 errors (49 pre-existing warnings).
- Targeted: 111 advisor/NL/setup-cog tests + the 145 surface/freshness/defer tests that the new
  command touched.

## Session enders

- **♻ Grooming (Q-0015):** advanced the AI-setup wedge from the positioning north-star
  (`competitive-positioning-north-star-2026-06-23.md`, pillar 2) into a shipped first slice; the
  doc's "AI-as-operator, not chatbot" framing directly shaped scoping (reused the existing audited
  apply path rather than building a new one).
- **💡 Session idea (Q-0089):** *Extend the wedge to propose resource **creation** from a
  description* — today it only binds *existing* channels/roles. Letting the advisor emit
  `create_channel`/`create_role` recommendations (the `SetupOperation` kinds already exist; only the
  recommendation JSON schema + a creation adapter are missing) turns "describe your server" into
  genuinely building it from a sentence — the full "whoa". Contained follow-up; dedup-checked
  `docs/ideas/`, not yet captured.
- **⟲ Previous-session review (Q-0102):** the positioning-doc session did well to flag its own
  honesty caveats (vendor-blog bias; the AI-setup lane is contested) — and this session benefited
  directly: I scoped to *AI-as-operator over the audited seam*, not a bolted-on chatbot. *Workflow
  note it surfaced:* the deep research fan-out's nested-agent tangle (flagged last session) recurred
  conceptually — orientation here used **one** Explore agent (flat), which was clean and fast. Keep
  research/orientation flat.
- **📋 Doc audit (Q-0104):** ledger unaffected (PR not merged yet — recorded on merge); generated
  artifacts regenerated + freshness green; no chat-only conclusions left undocumented (the design
  + follow-up live in this log).
