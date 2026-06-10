# 2026-06-09 — Platform-surface mapping standard (Codex two-agent campaign prep)

**PR:** #641 (docs-only). **Authoritative doc:**
`docs/planning/platform-surface-mapping-standard-2026-06-09.md`.

## Arc

Standards-setting session for the full command/service/help/panel/settings
consistency audit. Read the orientation route + the two prior Codex audits
(#625 settings, #627 help) + the binding contracts; verified live PR state
(**#638** BTD6 data continuation and **#639** Lane 4/answerability Phase 3 are
open drafts); enumerated the real surface inventories from source (36
extensions / 29 subsystems / 10 hubs + `all_commands` sentinel; 28/29
subsystem cogs expose `build_help_menu_view`; 7 loaded cogs are not
subsystems). Shipped the mapping standard: §2 verified baseline, §3 record
schema + label vocabularies + evidence format, §4 consistency target (T1–T19),
§5 two-agent subsystem split (A: 17 user-facing · B: 12 admin/platform +
setup/bootstrap + composition architecture), §6 copy-paste Codex prompts, §7
merge-session contract.

## Shipped

- The standard doc (above) + roadmap row (Building/interface → Next).
- Drift fixes, all enumeration-verified, none doc-test-pinned:
  help-surface-map prose counts (9→10 hubs, 26→29 subsystems, hook 28/29;
  tables were already right), settings command-map preamble (22/23 → 36 cogs,
  22 → 29 subsystems + cog≠subsystem explanation), repo-navigation cheat-sheet
  rows for `four_twenty`/`games`/`server_management`.
- current-state ▶ line: #638/#639 noted in flight; the mapping campaign staged.

## Key findings (for the next agent)

- **Lane ownership mattered more than expected.** The help-map count drift I
  found in minute one is *already owned by scoreboard Lane 8* (owner-ratified,
  Q-0065) — the right move was to fix only the unpinned prose counts and leave
  the pin tests + characterization tests to the lane. Same pattern: settings
  hub display (Lane 7), Help-consumes-projection (adaptive P1C). The standard
  encodes this as the `blocked-by-gate(<lane>)` verdict.
- **"Loaded cog ≠ subsystem ≠ hub" is the load-bearing distinction** for any
  surface inventory; three docs had drifted by conflating them.
- #638 touches the BTD6 *data* layer, not the command surface; #639 touches
  the AI *tool registry* layer, not the cog/panel surface — so both halves
  stay mappable with narrow `provisional(#nnn)` carve-outs.

## Decisions made alone (ratify if wrong)

- Split shape: `role`/`channel`/`proof_channel` → Agent B (admin-config
  surfaces) even though they're community/moderation hub children; `xp` →
  Agent A. One-subsystem-one-agent, cross-boundary findings as one-liners.
- Mapping agents collect owner questions **in their own doc** (merge session
  routes them to the router) — avoids the documented parallel-append
  renumbering cost.
- Output docs use stable undated filenames
  (`platform-mapping-{a-user,b-admin}-surface.md`) with pre-allocated link
  lines in the standard's §5.5, so reachability never collides.
- T8–T10/T18 of the consistency target are newly-promoted defaults (marked
  *(this standard)*) — deviations are findings, not contract violations,
  until they graduate into the binding standards.

## Flagged for maintainer / known limits

- The Codex prompts assume the Codex env quirks observed in #625/#627 (no
  `gh`/remote in one, no `python3.10` shim in the other) — both prompts carry
  the fallback instructions, but a Codex env with *neither* GitHub access nor
  a usable interpreter would produce a weaker, "unverified-live" report.
- I did not boot the bot — a docs/standards session; counts came from source
  enumeration, not a live walk. The #535 baseline stands; nothing here claims
  fresh live verification.
- If #638/#639 merge before the agents run, §2.4 of the standard goes stale
  in the usual way — both prompts force a live re-verify first.

## Context delta

- **Needed but not pointed to:** the multi-lane scoreboard
  (`planning/multi-lane-execution-plan-2026-06-09.md`) turned out to be the
  *decisive* doc for what this session was allowed to touch (Lanes 7–8 own
  the obvious drift fixes) — the orientation route reaches it only via
  current-state's ▶ line; for any audit/standards session it should be a
  first-class stop. Also `core/runtime/command_surface_ledger.py`'s
  classification vocabulary — the canonical command-classification home — is
  not named in any orientation route (found via the help audit's inventory).
- **Pointed to but didn't need:** `docs/owner/maintainer-question-router.md`
  §25/§27 full blocks (the Q-0055–Q-0059/Q-0063–Q-0064 one-line conclusions in
  the audits' post-merge banners were sufficient); reading
  `settings-customization-roadmap.md`'s S-milestone table (its own banner
  already routes you to the settings audit §11).
- **Discovered by hand:** the `check_docs.py` mechanics that shaped the split
  design — markdown links must point at *existing* files (so future-doc
  references must be backticked paths, not links) and new docs need a badge +
  reachability link; neither is stated where you'd plan a multi-PR doc
  campaign. The doc-pin tests for the help map and command map pin
  headings/keys/labels but **not** the prose counts — which is exactly what
  made the count fixes safe; worth knowing before any inventory-doc edit.

## One change that would have helped

A "Touching the command/help/panel surface" route in `AGENT_ORIENTATION.md`
(help-surface map + the two audits + the scoreboard + the ledger). Not added
this session — my PR already touches two count-stale docs Lane 8/Phase 6 will
edit; filed here so the REVIEW pass can promote it if it recurs.
