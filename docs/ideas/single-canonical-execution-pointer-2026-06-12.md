# Idea: single-canonical-execution-pointer invariant

> **Status:** `ideas`

**Captured:** 2026-06-12 · **Context:** orientation review, agent-memory system follow-up

## Problem
A session can start while two execution-order artifacts coexist: an older plan and a newer superseding plan. The prompt then becomes ambiguous (“execute the multi-lane plan”), and agents may implement the wrong ordering.

## Proposal
Enforce a repo invariant:
- At any time, exactly one doc is canonical for “what do I execute next”
- When a new execution order supersedes an old one, the same commit/PR must update the old doc to point to the new canonical schema
- CI or a freshness lint should detect any doc still claiming canonical status after a known replacement landed

## Value
Removes a class of retroactive ambiguity from parallel/back-to-back sessions, and gives the portable-memory package a clean hook for the same discipline.
