# Soft ratchet on the supersede-banner warning count (2026-07-17)

> **Status:** `ideas` — raised 2026-07-17 (forty-eighth Q-0107 reconciliation pass).
> **Subsystem:** tooling / docs-system.
> **Gate:** ready — small, self-contained checker change; disposable per Q-0105.

## The friction this pass hit

`check_docs.py`'s supersede-banner integrity check is **warn-only** — it lists every doc whose
`SUPERSEDED` banner names no resolvable successor and never fails CI. That is deliberate and
correct: most are honest cross-repo supersessions (successors live in fleet-manager, registry
PR #39) the in-repo checker can't model, and two open ideas already propose teaching it to
resolve those paths ([`check-docs-cross-repo-path-awareness-2026-07-11.md`](check-docs-cross-repo-path-awareness-2026-07-11.md),
[`supersede-integrity-cross-repo-tier-2026-07-11.md`](supersede-integrity-cross-repo-tier-2026-07-11.md)).

But "warn-only" also means the count **drifts silently**. This pass the warning set grew **5 → 9**:
a band added four new phantom cross-repo successor links (the fleet-centralization / fleet-review /
trigger-health docs) and **no check flagged the regression at the moment it was introduced** — the
+4 only surfaced 30 PRs later, at reconcile, when a human eyeballed the census. A genuinely *broken*
in-repo banner (a real drift, not a cross-repo false positive) would ride the same silent channel:
it would land warn-only and go unnoticed until the next pass.

## The idea

Add a **soft ratchet on the supersede-banner warning *set*** — the same *spirit* as the ratchets
`check_docs.py` already applies to Recently-shipped (20) and top-level docs (22), but keyed on
**banner identity, not a bare count**. Persist the *accepted* warning set (the doc-path + successor-link
identity of each known warning) as the floor; warn (do not fail) when a run surfaces a banner **not in
the accepted set**, naming exactly the net-new ones:

```
⚠ supersede-banner: 1 banner not in the accepted set (accepted: 9) — net-new this change:
    docs/owner/trigger-health-order-2026-07-12.md → <phantom successor>
  If this is an honest cross-repo supersession, add it to the accepted set; otherwise fix the banner.
```

**Why identity, not just a count** (Codex P2 on the introducing PR, #2132): a count-only floor is
defeated by a resolve-one/add-one edit — if a known cross-repo warning is fixed in the same change
that introduces a broken in-repo banner, the total is unchanged (or below the floor) and a count check
stays silent despite a real regression. Comparing the *finding set* against the accepted baseline (or
against the base revision's findings) is what actually guarantees introduction-time detection. The
accepted set lives beside the existing ratchets (a small `.ratchets` / sidecar list of banner
identities); adding an entry is a one-line, deliberate act — exactly like trimming Recently-shipped
past its ratchet — so a session that *adds* a legitimate cross-repo banner records that intent, and a
session that accidentally breaks an in-repo banner gets told **at the diff**, not a month later.

## Why it's worth having

- Catches net-new banner drift **at introduction**, closing the same "warn-only channel hides
  regressions" gap the Rule-6 graduation (#2000) closed for `check_consistency`.
- Complementary to the two cross-repo-awareness ideas, not a duplicate: those *suppress* the
  false positives; this *pins the accepted set* so a real regression can't hide among them even
  before cross-repo awareness lands.
- Cheap and disposable (Q-0105): one ratchet constant + one comparison; delete it if it proves
  noisy across a few passes.

## Route in

`scripts/check_docs.py` (census block, beside the Recently-shipped / top-level ratchets) +
`scripts/check_supersede_integrity.py` (the source of the count). A reconciliation pass is the
natural place to bump the floor, since it already narrates the count each time.
