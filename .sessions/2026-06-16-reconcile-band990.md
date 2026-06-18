# Session — 2026-06-16 · tenth Q-0107 docs reconciliation (band-#990)

> **Status:** `complete`
> Routine: **superbot docs reconciliation** · trigger: `reconcile` issue **#961** · branch
> `claude/reconcile-960-gkryzh` · docs-only.

## What this session did

A Q-0107 docs-only reconciliation + planning pass for the band that crossed #960 — **plus a
mid-run workflow fix the maintainer directed live.**

**The live interruption (the headline).** The routine **stalled twice** on Claude Code permission
prompts: each was a compound Bash command doing ledger surgery via a temp script and cleaning it up
with `rm`, and the blanket `Bash(rm *)` safety brake (Q-0149) forced a prompt an unattended routine
can't answer. The maintainer asked me to resync, start over, and **fix this for good in the
allow-list**. Done:
- **`.claude/settings.json`** — narrowed the `rm` `ask` brake to **recursive deletes only**
  (`rm -r*` / `rm -R*` / `rm -fr*` / `rm -fR*`); added `allow` for non-recursive `rm -f*`, `rm /tmp/*`,
  `rm _*`, `python3.10 *`, `python3 /tmp/*`. So a routine's scratch-file cleanup never stalls, while
  `rm -rf <dir>` still prompts. **(owner-directed in-session → applied directly, Q-0106 exception.)**
- **Q-0161** recorded in the question router (full provenance + the behavioral complement).
- **`.session-journal.md`** (Boot & environment) — the recurring-problem note: prefer Edit/Write over
  a temp `python3.10 _scratch.py && rm` dance; scratch scripts go under `/tmp/`.
- Dogfooded it: this pass's ledger surgery ran via a **self-deleting** `scripts/_recon_tmp.py`
  (no `rm`, no stall).

**The reconciliation itself:**
- **Ledger** — added the #944–#994 tail (27 merges + the under-entered #946/#960) as **six grouped
  `Recently shipped` entries**; archived the six oldest (#912/#917/#918/#920/#924/#926) to hold the
  ratchet at 20. `check_current_state_ledger --window 60` green.
- **Open-PR disposition (Q-0125):** #995 (active parallel dashboard PR — leave) · #941 (image-mod,
  `needs-hermes-review`, **now conflicted** — flagged for the owner/Hermes, not my merge authority).
  The two prior carve-outs (#929 security, #962 paragon) both merged — the queue drained.
- **Control-plane (Q-0135):** `check_loop_health` SKIP (no `gh`); fallback read — #961 authored by
  `menno420` = PAT set, loop self-fires; canonical table already correct (Gates bullet is a pure
  pointer since #943). No drift.
- **Planning** — wrote [`reconciliation-pass-2026-06-16-band990.md`](../docs/planning/reconciliation-pass-2026-06-16-band990.md)
  (scorecard: 6/10 slots, slot 6 over-delivered — the deterministic BTD6 floor family is complete;
  the **developer-dashboard / control-API initiative** was the buffer-that-became-the-band, a 5th
  time). Planned the next ~9 (dashboard live editor · AI §7 next family · moderation-DM config ·
  Hermes `gh issue` write · gated P1 remainder). Re-pointed current-state ▶ + roadmap Now; re-badged
  the band-#930 pass `historical`; marker #930→**#994** (next at #1020).

## 💡 Session idea (Q-0089)

[`routine-permission-surface-lint-2026-06-16.md`](../docs/ideas/routine-permission-surface-lint-2026-06-16.md)
— a stdlib `check_routine_permission_surface.py` that flags any routine-common command which would
resolve to the `permissions.ask` brake (i.e. would stall an unattended run), turning the Q-0161
lesson ("every routine command must be `allow`, never `ask`") into a pre-flight CI guard instead of a
reactive fix-after-stall. Genuinely worth having — this is now the **second** time a permission brake
silently cost a scheduled run.

## ⟲ Previous-session review (Q-0102)

The band-#930 pass (#932) did its core job well — clean scorecard, idea→plan promotion, control-plane
drift caught via the fallback read. **What it missed:** it left the giant `▶ Next action` / `▶ NEXT`
callouts in `current-state.md` as ever-growing append-only blobs, so by this pass the lead sentences
still implied security tiers / BUG-0009 were in flight when they had all shipped — a reader trusting
the "read THIS line" lead got stale state. **System improvement surfaced:** those two callouts are the
single worst drift surface in the repo (each is ~3 000 words of dated narrative the convention says to
"trust the first sentence" of). A future pass should either hard-cap them (lead sentence + a link to
the band doc, the rest archived like the `Last updated:` stamp wall was in #925) or add a
`check_docs` length/staleness guard on them. The deeper pattern — *a pointer that's allowed to grow
unboundedly becomes a liar* — is the same one the stamp-wall archive and the control-plane
single-source-pointer (#943) already fixed elsewhere; the ▶ callouts are the last un-fixed instance.
