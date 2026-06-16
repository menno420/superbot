# Session — `!coglist` text command → the "📋 Cog List" button (owner request)

> **Status:** `complete`

## Origin

Owner, after the BUG-0014 loop fix (#949): *"the command `coglist` should be a real command — there
is a button that does exactly that, so link the text command to the button as well."* #949 removed
the orphaned `coglist` *synonym* (the loop cause); this makes `coglist` a **real command** wired to
the existing button's view.

## Change

`disbot/cogs/admin_cog.py` — new prefix command `coglist_command` (method renamed off the
discord.py-reserved `cog_` prefix; command name is `coglist`):

```python
@commands.command(name="coglist", aliases=["cogs", "listcogs", "cogslist"],
                  extras={"alias_classification": "power_user_shortcut"})
@commands.has_permissions(administrator=True)
async def coglist_command(self, ctx):
    view = _CogManagerView(self, ctx.author)
    await send_panel(ctx, embed=view.build_embed(), view=view)
```

- Opens the **same `_CogManagerView`** the admin panel's 📋 Cog List button opens — one surface, no
  duplicated rendering.
- **Exact aliases** `cogs`/`listcogs`/`cogslist` (the tokens users actually type — the BUG-0014 video
  showed both `!cogs` and `!coglist`), so they resolve directly with no fuzzy synonym → #949's
  synonym-orphan invariant stays green (no `coglist` synonym canonical reintroduced).
- **Admin-gated** like `!adminmenu` (which hosts the button); the view keeps its own **owner-gating on
  mutations**. All four names verified collision-free.
- Two discord.py contracts hit + satisfied: method can't start with `cog_` (renamed to
  `coglist_command`); a ≥3-alias command must declare `extras["alias_classification"]` (the
  surface-ledger invariant) — declared `power_user_shortcut` (visible fluency spellings).

## Verification

- `tests/unit/cogs/test_admin_cog_manager.py` — new: command registered with name + aliases + admin
  check; invoking it sends a `_CogManagerView` (mirrors the existing button test). 20/20 pass.
- `python3.10 scripts/check_quality.py --full` → **green (9974 passed, 37 skipped)**.
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0**.

**Merge ≠ deploy-only:** Railway auto-deploys on merge to `main` (per `production-deployment.md`), so
this reaches prod on merge — `!coglist` / `!cogs` will open the cog manager after the deploy completes.

## 💡 Session idea (Q-0089)

[`button-command-surface-parity-2026-06-16.md`](../docs/ideas/button-command-surface-parity-2026-06-16.md)
— this gap (a button with no command front door) was found only because a user hit it. A review-lane
audit pairing distinct action-buttons with command equivalents (not a brittle CI guard — most buttons
are navigation) would surface the rest; a lighter automatable slice mines "command not found" misses
for high-frequency expected names. (Filed + indexed.)

## ⟲ Previous-session review (Q-0102)

Previous session: **BUG-0014 `!coglist` loop fix (#949)**.
- **Did well:** correct root-cause loop-breaker + a CI invariant that fails against the orphan; tight
  and well-tested.
- **What it could have done better (the owner's follow-up proves it):** #949 treated the orphaned
  `coglist` synonym as *purely* bad data and **removed** it — but the owner actually *wanted* `coglist`
  to work (a button already did it). The fuller fix was "make the target exist," not "delete the
  dangling pointer." Genuine lesson: **a dangling reference can signal a *missing feature*, not just
  stale data** — when removing an orphan, ask whether the right fix is to make its target real
  (and flag to the owner if unsure) rather than silently deleting. #949's loop fix was still correct
  and necessary; this PR is the complementary "make it real" half.
- **Workflow improvement:** worth a line in the bug-fix habit — when a fix is "remove a dead
  reference," pause on whether users expected that reference to resolve (the BUG-0014 video literally
  showed the user typing `!coglist` *wanting* an answer).

## Documentation audit (Q-0104)

- `check_docs.py --strict` → green (new idea file reachable + indexed). `check_architecture --mode
  strict` → exit 0.
- Not a bug → no bug-book entry. Session log + active-work claim + idea file/index updated; the fix +
  rationale live in the command docstring + this log. No chat-only durable info outstanding.
- **Operational finding (out of band, reported to owner, not a repo change here):** the Railway
  `RAILWAY_API_KEY` in the agent env is truncated (29 chars, Railway's API rejects it; owner confirmed
  it doesn't match the dashboard token ending `-4c20`). The token *kind* (Account scope) is correct
  for `railway_logs.py`. Live-log verification is blocked until the env value is re-pasted in full —
  a `docs/operations/production-deployment.md` "verify the env value isn't truncated" gotcha is a
  candidate follow-up (not bundled into this feature PR).
- Living-ledger drift (#948/#949 + this) stays the **next reconciliation's** job (not due till #960;
  Q-0124). Backlog grooming (Q-0015): this PR *is* a groomed follow-up to BUG-0014; standing pickups
  (deathmatch timed-view invariant; the two prior idea files) remain named in their logs.
