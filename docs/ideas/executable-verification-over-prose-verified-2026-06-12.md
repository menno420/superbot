# Idea: executable invariants replace prose "verified" status claims

> **Status:** `ideas`

**Captured:** 2026-06-12 · **Context:** orientation review, agent-memory system follow-up

## Problem
Docs and plans still use prose “verified” checklist items that drift over time. That directly caused a missed touch-point during the 2026-06-09/lane merges: an execution plan list was marked verified but omitted a real registration surface, and only a doc-pin test caught it later.

## Proposal
Make evidence status machine-checkable wherever possible:
- Turn prose “verified” lists into executable checks or CI tests
- Where automation is impractical, label items explicitly as manual with a stable trace ID and expected runner
- Treat any checklist item without a verification rule or trace ID as implicitly unverified

## Value
Prevents rot-by-narrative, catches omissions before merge, improves portable-package extraction because verification becomes a declared contract instead of a convention buried in prose.
