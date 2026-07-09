# 2026-07-09 — substrate-kit v1.0.0 pin file (kit-lab D2, consumer half)

> **Status:** `in-progress`

## What I'm about to do

substrate-kit **v1.0.0** is released
([tag](https://github.com/menno420/substrate-kit/releases/tag/v1.0.0),
`bootstrap.py` sha256
`5e518d4978a01926057bdece04d88bd5f1b7d433bbc19b36790bdeff14149313`). Per the
kit-lab founding plan §4.2 (a named KL-1 companion deliverable), superbot
records its version pin in a **root `substrate.config.json` next to the
in-tree `substrate-kit/` copy**: `kit_version: "1.0.0"` + a `project_id`
(which the §9.1 friction-report envelope needs). Docs/config-only; the
in-tree `substrate-kit/` source dir deletion stays a separate follow-up chore
(explicitly out of this session's scope, per the plan's honest scoping).
