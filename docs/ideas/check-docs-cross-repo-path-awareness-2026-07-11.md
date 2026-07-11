# Cross-repo path awareness for `check_docs.py`'s pinned-path check (2026-07-11)

> **Status:** `ideas` — raised 2026-07-11 (forty-fourth Q-0107 reconciliation pass).
> **Subsystem:** tooling / docs-system.
> **Gate:** ready — small, self-contained checker change; disposable per Q-0105.

## The friction this pass hit

`check_docs.py`'s pinned-path check treats any backtick `` `docs/…md` `` token in a doc as a
**claim about a local file** and fails CI (`[pinned]`) when the path doesn't exist on disk.
That is exactly right for an in-repo reference — a stale or mistyped local link is real drift.

But the fleet now routinely references **another repo's** files by their repo-relative path.
This pass hit it: the band-#2010 ledger entry described PR #2006 as pointing to the
fleet-manager repo's `docs/fleet-triage.md`. Written naturally as ``fleet-manager `docs/fleet-triage.md` ``,
the checker read `docs/fleet-triage.md` as a *local* path, found no such file here, and red-failed
`--strict`. The only fix was to reword it to "the fleet-manager repo's `fleet-triage.md`" — dropping
the `docs/` prefix so the token no longer looks local.

Net: every cross-repo file reference that keeps its natural `docs/…` prefix is a false positive,
and the workaround (hand-reword to strip the prefix) is a papercut every future pass referencing
another repo's docs will re-hit — the same "cross-repo reference confuses an in-repo checker"
pattern as the `check_supersede_integrity.py` cross-repo tier
([`supersede-integrity-cross-repo-tier-2026-07-11.md`](supersede-integrity-cross-repo-tier-2026-07-11.md)),
now for the path-pin check.

## The idea

Teach the pinned-path check to recognize a **cross-repo qualifier** immediately preceding the
backtick path and skip the local-existence pin for it. Recognizable patterns:

- a repo name right before the path — ``fleet-manager `docs/…` `` / ``substrate-kit `src/…` `` /
  ``superbot-next `…` `` (match against a known fleet-repo list, or a generic `<word>-<word> \``
  repo-slug shape);
- an explicit "the <repo> repo's" phrase;
- a token already inside a `https://github.com/menno420/<repo>/…` URL (these should already be
  URL-shaped, not bare paths — verify).

When matched, the path is a cross-repo reference → do **not** assert local existence. Bare
`docs/…` tokens with no cross-repo qualifier keep failing exactly as today, so genuine local
drift is still caught.

## Why it's worth having

- Removes a recurring reconciliation-pass papercut at the root (Q-0194 friction→guard) instead
  of relying on each future agent to remember the reword workaround.
- Lets cross-repo references stay in their natural, most-informative form (with the `docs/`
  prefix) rather than a lossy hand-stripped one.
- Pairs cleanly with the supersede-integrity cross-repo tier — both make in-repo checkers
  fleet-aware as the multi-repo fleet grows, which is the direction of travel.

## Scope / cost

One checker, pure-stdlib, a small qualifier regex + a fleet-repo-name list (or reuse whatever
list the fleet-manifest / roster already carries). A few unit tests: a bare `docs/x.md` still
fails, a `fleet-manager \`docs/x.md\`` passes, a real local link still resolves. Q-0105
unverified-tier header; wire into `check_docs` behind the existing pinned-path pass.
