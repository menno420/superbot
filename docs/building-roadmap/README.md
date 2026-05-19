# SuperBot Building Roadmap

Status: Reference only  
Runtime impact: None

This directory contains reference documents for future command, panel, help-menu, Settings Manager, and setup-wizard work.

## Files

- `command-integration-standard.md` — rules for adding commands, panels, help-menu hooks, settings links, and navigation behavior.
- `command-expansion-backlog.md` — near-term command and panel ideas.
- `interface-completion-roadmap.md` — phased roadmap for centralized interface completion (Games hub, Cleanup panel, Access explorer, logging route table, slash front doors, setup wizard).
- `hub-ui-standard.md` — UX standard for SuperBot hubs and panels (hub presets, component thresholds, future visibility metadata, audit of existing views, Phase 8 audit finding).
- `mother-hub-map.md` — canonical mother-hub map: hub assignments, primary-vs-cross-link policy, Help-as-category-index design, navigation/settings/placeholder doctrine, and the S1–S13 PR sequence. Supersedes the candidates section in `hub-ui-standard.md` and the L1–L6 sequence in `../loose-ends-audit-roadmap.md`.

Related reference:

- `docs/operator-settings-presets.md`

## Core principle

SuperBot should feel like a Discord-native application, not a scattered list of commands. Every major feature should be reachable through `!help`, its subsystem panel, relevant Settings Manager pages, and relevant Admin/Platform surfaces where appropriate.
