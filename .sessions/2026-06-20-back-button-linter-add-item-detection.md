# 2026-06-20 — back_button linter: catch dynamically-built (add_item) hubs

> **Status:** `complete`
> **Run type:** `manual` — owner greenlit ("Yes go ahead, improvements are always
> welcome") the follow-up idea filed in the #1177 session log.

## Arc

PR #1177 fixed the Explore world-hub dead-end, but it had shipped past the
**graduated (error-level) `back_button` consistency rule** — that rule only saw
`@ui.button`-decorated controls, so registry-driven hubs that build buttons with
`self.add_item(...)` were invisible to it. This run closes that detection gap so
the dead-end class is self-policing, and sweeps the tree for any others.

## Shipped (linter-only; no `disbot/` runtime change)

`scripts/check_consistency.py`:
- **Detect dynamic hubs:** `_class_adds_items_dynamically()` — a HubView that adds
  controls via `add_item(...)` now counts as a navigable panel (was: only decorated
  `@ui.button`/`@ui.select`). This is the gap fix.
- **Smarter back detection** (`_module_has_back_affordance`), so broadening the net
  didn't create false positives — it now also recognizes:
  - `transition_to(...)` — the shared nav helper the UX-lab Home buttons route through;
  - a back-token `label`/`custom_id`/`emoji` on **any** call — covers custom
    back-button *subclasses* (`_BackToHubButton.__init__ → super().__init__(label="Back
    to Hub", custom_id="...back", emoji="↩")`), which the `Button(...)`/`@ui.button`
    checks missed.

Net: the broadened rule first flagged **14**; the two detection improvements cleared
**10** that had real backs (5 settings sub-panels via `_BackToHubButton`, 2 paragon
views, deathmatch select, 2 UX-lab benches via `transition_to`); the remaining **4**
are genuine top-of-stack roots / externally-backed children → allowlisted with reasons
in `consistency_exceptions.yml` (`_CountingHubView`, `ExploreWorldHubView`,
`SettingsHubView`, `UxLabHomeView`). `check_consistency --mode strict` = 0 errors.

Tests: `tests/unit/scripts/test_check_consistency.py` +3 — a dynamic add_item hub
*is* flagged; a custom back-button subclass and a `transition_to` Home button are
clean.

## Verification

- `check_consistency --mode strict`: 0 errors (17 pre-existing `edit_in_place` warns).
- `check_quality --check-only`: all green (black/isort/ruff + consistency).
- `test_check_consistency.py`: 46 passed. Full `--full` suite green.
- No `disbot/` change → `check_architecture` had nothing to check; nothing to deploy.

## Context delta

- **Discovered by hand:** the `back_button` rule had **three** detection blind spots,
  not one — dynamic `add_item`, custom back-button subclasses (`super().__init__`),
  and the `transition_to` nav helper. Fixing only the first (the obvious gap) would
  have turned 8 panels-with-real-backs into false CI errors. Lesson for the next
  linter-broadening: when you widen what a rule *catches*, audit what it *recognizes
  as compliant* in the same pass, or you trade a false negative for false positives.
- **Decisions made alone:** treated `transition_to` as a back/nav affordance (it can
  also do sibling nav, but in practice it's the Home-button helper); allowlisted the 4
  roots rather than adding spurious back buttons to top-of-stack panels.
- **Flagged for maintainer:** none. Pure tooling hardening; behavior of the bot is
  unchanged.

## 💡 Session idea

**A root-claim cross-check for the `back_button` allowlist.** Each allowlist entry
asserts "this is a top-of-stack root (no parent)" — but that's verified by hand and
can rot (a panel later opened from another hub stays allowlisted and silently keeps a
dead-end). A tiny check could confirm each allowlisted class is instantiated by a cog
command path (`send_panel` / a `@commands.command` body) and warn if it's *only* ever
constructed from inside another `views/` module — i.e. it became a child and the
"root" reason is now false. Closes the one soft spot left in this rule (the allowlist
is trust-based). Filed, not built.

## ⟲ Previous-session review

The #1177 session fixed the Explore dead-end at the call site (attached the back
button in `main_panel`) and *filed* the linter gap as an idea rather than fixing it —
the right call under time pressure, but it left a graduated CI rule with a known hole
for a session. Good that it flagged the gap explicitly in the log so this run could
pick it up cleanly. **System note:** the gap existed because the rule graduated to
error (#1094) while still only understanding decorated controls — a rule should
arguably not graduate until its detection covers the dominant construction patterns
in the tree (decorated *and* dynamic). Worth a line in the linter plan's graduation
checklist: "confirm the rule sees both `@ui.button` and `add_item` hubs before
flipping to error."

## 📤 Run report

- **Did:** closed the `back_button` rule's blind spot for dynamically-built (`add_item`)
  hubs + hardened its back-affordance detection (custom subclasses, `transition_to`);
  allowlisted 4 verified roots. · **Outcome:** shipped
- **Shipped:** PR (this run) — linter detection fix; `check_consistency --mode strict`
  clean. No runtime change.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** the idea→build was **owner-greenlit** this run (not unprompted),
  so not self-initiated; the new root-claim cross-check idea above is filed, not built.
- **↪ Next:** optional — build the filed root-claim cross-check, or resume the
  consistency-linter AI-nav lane (rule 1 `edit_in_place`, the 17 remaining `views/ai/`
  warns).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at write time (PR open; auto-merge armed) |
| CI-red rounds | 0 (caught the false-positive class locally before push) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (root-claim cross-check for the allowlist) |
| Ideas groomed | 1 (executed the #1177 filed linter idea, owner-greenlit) |
