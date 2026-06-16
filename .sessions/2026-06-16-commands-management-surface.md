# 2026-06-16 — `/commands` management surface (READ side)

> **Status:** `complete` — dashboard-only (no `disbot/` runtime). One PR (#988).

## Arc

Continued the bot's main website (`dashboard/`). Built the **`/commands` management surface —
READ side** (Q-0158 owner ask): turned the read-only explorer into a management surface — a
**Manage** button on every command *and* every cog, each opening a slide-over panel. Decoupled +
read-only (no `disbot/` import, no auth, no bot change); the bot stays the source of truth and the
site front-ends its existing audited seams (`command_routing` + the synonym layer).

Confirmed the one open architectural fork with the owner first (the handoff + the predecessor
session both flagged it), then built the whole read side — which ships identically either way.

## Owner decision (AskUserQuestion → Q-0160)

Q-0158 literally asked to "enable/disable **each command** from the website," but the bot routes
only at **cog (subsystem)** level today. Per-command would be a new finer bot routing layer.
**Owner chose: cog-level now, per-command later.** So the panels show **cog-level** routing state;
the per-command write affordance this session is the **alias suggest box**. Recorded as router
**Q-0160** (explicit sign-off on the Q-0158 interpretation, so it isn't reopened).

## Shipped (PR #988)

- **`dashboard/templates/commands.html`** — Manage button on every command + cog; a slide-over
  drawer (vanilla JS, no framework, same style as the existing `/aliases` + `/commands` scripts)
  populated from `data-*` attrs + three embedded JSON blobs (collision map, synonyms, routable set):
  - **Command panel:** identity (type / parent / cog / brief / button-backed) · current aliases
    (code aliases vs soft synonyms, distinguished) · cog-level routing state · a **per-command alias
    suggest box** — the `/aliases` collision check + prefilled GitHub issue + paste-ready
    `synonyms.py` snippet, scoped to that one command.
  - **Cog panel:** identity (class / file / loaded-vs-mixin) · routing state · its command list.
- **`dashboard/app.py`** — factored `_command_names` / `_build_taken_map` (shared by `/aliases` +
  `/commands`, DRY) + `_routable_subsystems`; `/commands` now feeds `routable` / `taken` /
  `synonyms_by_canonical`. `/aliases` refactored onto the shared helpers (unchanged behaviour).
- **Drive-by fix** — acronym-aware `_cog_to_subsystem` (`scripts/scan_commands.py`): `BTD6Cog`→
  `btd6`, `AICog`→`ai`, `XPCog`→`xp` (were `b_t_d6`/`a_i`/`x_p`, matching no registry key). Fixes the
  cog→registry join for those cogs' header emoji/name *and* their routing-key display. Added
  `visibility_mode` to the exported catalogue so routability is computed precisely (non-internal).
- Regenerated `dashboard/data/dashboard.json`; updated the plan doc (read side marked shipped).

## Status checklist

- [x] acronym-aware `_cog_to_subsystem` + test
- [x] `/commands` Manage buttons (command + cog) + slide-over panel
- [x] per-command alias suggest box (collision check + prefilled issue + snippet)
- [x] cog routing-state display (cog-level model, audited seam)
- [x] export enrich (`visibility_mode`) + regenerate `dashboard.json`
- [x] smoke test (web deps) + `check_quality --check-only`
- [x] Q-0160 router record + plan-doc update
- [x] session enders + flip card `complete`

## Verification

- `pip install -r dashboard/requirements.txt httpx` (under `python3.10 -m pip` — bare `pip` hit a
  different interpreter and silently skipped the suite) → `python3.10 -m pytest tests/unit/dashboard/`
  → **20 passed** (incl. the new `test_commands_page_has_manage_surface`).
- `python3.10 -m pytest tests/unit/scripts/test_scan_commands.py` → **8 passed** (incl. the new
  acronym test); export/scanner script tests **54 passed**.
- `python3.10 scripts/check_quality.py --check-only` → green; `check_docs --strict` → green.
- End-to-end render: 301 command + 42 cog Manage buttons, drawer + embedded data present,
  `data-subsystem="btd6"`×9 / `ai`×14 (acronym join works), `/aliases` still renders.

## 💡 Session idea (Q-0089)

**Dashboard cog↔registry coverage check** — `docs/ideas/dashboard-registry-coverage-check-2026-06-16.md`
(+ README index). A stdlib self-check (a `--check` mode on the exporter or a unit test) that flags
scanned cogs whose `subsystem` doesn't resolve to a registered subsystem (split *expected* allow-list
vs *unexpected* drift) — so a cog rename / new acronym cog / registry-key change that breaks the
dashboard's cog→registry join **fails a check** instead of silently degrading that cog's card. I hit
exactly this class this session (the acronym cogs were silently degraded); fixing one class by hand
proved the failure is invisible. Decided-lane, small.

## ♻️ Backlog grooming (Q-0015)

Advanced the predecessor session's "**your authority preview (pre-auth)**" idea — it was buried in
the `2026-06-16-multiuser-control-panel-design` session log — into the plan's **Ready read-only
slices** list (`dashboard-live-editor-plan.md`). It's now a tracked, no-auth, no-bot-change next slice
and a natural extension of the `/commands` + `/access` read surfaces I just shipped (moved one step
down its lifecycle: log-note → tracked plannable slice).

## ⟲ Previous-session review (Q-0102)

Reviewed **`2026-06-16-multiuser-control-panel-design.md`** (the design session that handed off to
me; router Q-0159). **Did well:** it correctly resisted the urge to build — owner said "don't rush,
bot first" — and instead nailed the *finding* that both config layers already exist, so the real gap
is just the control API + identity→authority bridge. That framing made my session trivial to scope.
It also explicitly listed its open questions ("cog-vs-command enable/disable; `/commands` go-ahead")
at the bottom — and I resolved exactly those, which is the handoff loop working as designed.
**Could've gone further:** its own 💡 idea (the authority preview) was a *read-only, no-auth* slice it
could have started building in that same session instead of leaving the whole read side to me — the
"don't rush" applied to the *runtime* (control API / OAuth), not to read-only website work, so there
was idle read-only capacity. **System improvement it surfaces:** a session's 💡 idea, when it's
itself a small same-lane read-only slice, tends to get stranded in the log (the predecessor's did;
I had to go dig it out to groom it). The grooming ender *catches* this, but late. A lighter fix:
when a session's own 💡 idea is small + decided-lane + same-lane, it should either be executed in
that session or filed as a proper idea file then (not only in the log) — i.e. close the Q-0089→Q-0015
gap at *creation* time, not one session later. (Captured here as the workflow note, not a rule change
— CLAUDE.md is propose-only.)

## Documentation audit (Q-0104)

- Owner decision recorded (Q-0160, router + plan); new idea filed + README-indexed; plan doc updated
  (read side shipped + the groomed slice). `check_docs --strict` green; `check_quality --check-only`
  green.
- **Ledger backlog deliberately untouched (Q-0124):** the SessionStart banner flagged 8 merged PRs
  not yet in `current-state.md` (#979/#978/#976/#974/…). That's the **automated reconciliation**
  routine's job, not a manual build session's — and the Recently-shipped ratchet is already at 20, so
  adding them needs an archive pass (reconciliation). My own PR (#988) isn't merged yet, so it's
  correctly absent. Nothing from *this* session is missing a durable home.

## Context delta

- The bot's **command routing is cog-level only** and keys on the **subsystem key** (snake_case,
  e.g. `games`/`economy`), *not* the cog class name — verified in `services/access_projection.py`
  (axis 3) + `views/setup/sections/cog_routing.py` (operator picker = non-internal SUBSYSTEMS keys).
  Default is **enabled** (channel→category→guild→default-true); routing only *restricts*.
- The dashboard cog→registry join was silently broken for **acronym cogs** (naive CamelCase split);
  fixed here for the whole class. ~10/42 cog entries still don't resolve (module/mixins + genuinely
  unregistered cogs) — captured as the Q-0089 coverage-check idea.
- Per-guild routing state is **runtime DB** — the static dashboard shows the *model* (default +
  scope + the audited seam), never a fabricated live value; live state + toggling needs the control
  API (Phase 2, OAuth not yet set up by the owner → read-only side is the lane to grow).
