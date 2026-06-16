# Idea — signature-faithful mocks / autospec guard for service+DB facades

> **Status:** `ideas` — brainstorm, not approved. Promotion path: `docs/ideas/README.md`.
> **Captured:** 2026-06-16 (BTD6 live-events session, Q-0089 ender).

## The problem this is born from

The BTD6 event drill-down had been crashing on **every** click in production
(`build_event_detail_view_model` called `btd6_db.search_facts(entity_key=…)`, but
`search_facts` has no `entity_key` parameter → `TypeError`). It shipped green because
its only test mocked the DB facade with a bare `AsyncMock`:

```python
monkeypatch.setattr(btd6_db, "search_facts", AsyncMock(return_value=[...]))
```

A bare `AsyncMock`/`MagicMock` **accepts any args and any kwargs**, so the call-site
kwarg typo passed the test while raising at runtime. The mock was *more permissive
than the real function*, which is exactly how a signature mismatch slips past CI.

This is a recurring, high-cost failure class: a "tested" function that crashes on the
first real call. The user-visible symptom here was "the race event button does
nothing."

## The idea

Make project mocks **signature-faithful** so a call that the real function would
reject also fails the test:

1. **Lint/AST guard (cheap, catches the common case):** flag
   `MagicMock(`/`AsyncMock(` used as a `monkeypatch.setattr(<real_module>, "<attr>", …)`
   replacement for a project callable **without** `spec=`/`autospec=`. Steer toward
   `create_autospec(real_fn)` (or `AsyncMock(spec=real_fn)`), which enforces the real
   signature. Scope to `monkeypatch.setattr`/`patch.object` on `disbot.*` targets so
   third-party mocks aren't touched. Disposable convenience guard (Q-0105 header:
   delete if it proves noisy across a few sessions).
2. **Or a tiny test helper:** `autospec_setattr(monkeypatch, obj, "name", side_effect/return_value=…)`
   that wraps `create_autospec` — one call site, hard to misuse, and the DB-facade
   tests (the densest mock users) adopt it first.

## Why it's worth having

- Directly prevents the class of bug that just cost a fully-broken user-facing feature
  that "had a test."
- Cheap and verifiable: `create_autospec` is stdlib; the guard is pure AST over `tests/`.
- Complements the existing executable-verification push (`docs/ideas/
  executable-verification-over-prose-verified-2026-06-12.md`) — same spirit, applied to
  test doubles.

## Disposition

Promote to a small `docs/planning/` slice when a tooling lane has capacity; start by
autospec-ing the BTD6 view-model + DB-facade tests (highest mock density) and measure how
many latent signature mismatches it surfaces before deciding whether to CI-wire the guard.
