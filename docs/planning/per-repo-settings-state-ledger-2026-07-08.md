# Plan — Per-repo settings state ledger (so sessions read the state, don't guess)

> **Status:** `plan` · raised by the owner 2026-07-08 (EAP-email thread)
> **Provenance:** owner directive — "create a good plan to see how we have all the settings per
> repo and a way to properly document that so future sessions know the state and don't have to
> guess; maybe add that to the developer website."

## Problem

Sessions repeatedly *guess* at repo configuration and pay for it: which check is the required one,
is auto-merge armed, is "auto-delete head branches" on, what does the ruleset require, which token
fires workflows, is the repo public or private, and — new this session — which git actions the
auto-mode wall blocks. This state is scattered across workflows, journal entries, and tribal
memory. A session should **read** the current state, not reconstruct it.

## Goal

A durable, **current**, per-repo settings ledger, ideally **auto-generated** (so it can't drift),
that sessions read at orientation — covering `superbot`, and `superbot-next` + `substrate-kit`
once they exist. Optionally surfaced on the dev website.

## What it records (per repo)

- Visibility (public/private) + default branch
- Branch protection / **rulesets** (required checks, required reviews, restrict-deletions, etc.)
- Auto-merge config + **which check is the merge gate** (Code Quality)
- "Automatically delete head branches" on/off
- Which token/PAT applies to which automation (`ROUTINE_PAT` and why — the app-token
  workflow-trigger gap)
- **Auto-mode capability facts** — the walled git actions (force-push, remote-branch delete,
  first-publish-to-public) + what clears each (nothing / present-operator / human-with-full-rights),
  cross-linked to `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`

## Phases

**Phase 1 — Capture (docs, ship now).** `docs/operations/repo-settings-state.md` seeded from what
we know + a one-shot GitHub-API read (repo settings, branch list, any reachable ruleset). Manual is
fine for v1; the value is one source of truth existing at all.

**Phase 2 — Auto-generate (dev tool, avoids drift).** `scripts/generate_repo_settings_state.py`
queries the GitHub API and regenerates the doc; wire it into a routine or CI so it stays current.
Known gap to document, not hide: **rulesets / branch-protection / OIDC aren't exposed by the
standard GitHub MCP tools** (coordinator-kickoff §5), so mark which rows are API-fetchable vs.
must-be-hand-confirmed. Ship lazy-imported + `pytest.importorskip` per the dev-dep rule.

**Phase 3 — Surface on the dev website (optional, bigger).** The botsite already has a
`dashboard/data/*.json` → panel pipeline; add a `repo-settings` data source + a read-only panel.
Plan separately once Phases 1–2 prove the data.

## Why this belongs to the workflow, not just the bot

This is orientation infrastructure — the same class as the claim files and the session cards. It
directly reduces the "guess the repo state" friction that has bitten multiple sessions, and it's
the natural home for the auto-mode capability facts so future sessions plan around the walls
instead of re-probing them (extends the coordinator's #1839 "environment capability matrix" idea).

## Next

Phase 1 is shippable immediately (docs). Ping to build it; Phase 2 follows once the row set is
agreed. Phase 3 is a website feature to plan on its own.
