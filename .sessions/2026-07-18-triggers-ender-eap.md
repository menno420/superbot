# 2026-07-18 · hub session — routine cleanup, session-ender v3.8, EAP evidence

> **Status:** `complete`

- **📊 Model:** opus-4.8 · high · docs + cross-repo doctrine
- **Venue:** owner-live hub chat (rooted `/home/user`, multi-repo sources; writes via direct-PAT).

Owner-directed working session. Most of the effort was undoing hallucinated /
agent-created problems (false walls already handled prior; this session: uncleaned
routine tombstones, an orphaned claim blocking CI, a stale-doctrine wake chain).

## What shipped / landed

- **Session-ender v3.8 — full seat-local routine wipe (fleet-manager #330, owner-merged).**
  Step 3 rewritten: at the owner-attended session close each seat deletes **only its
  own** triggers (id-attributed: armed-this-session + predecessor heartbeat + telemetry
  snapshot) — pacemaker `send_later`s, wake triggers, the failsafe cron, reminders, and
  **business crons** (no carve-out) — leaving zero for that seat; the startup prompt
  re-arms the single fresh failsafe. Never account-sweeps, never pattern-matches, never
  touches a sibling's live routines. BOOT-4 "cutover" reconciled to match; re-spliced
  into all 9 startups via `regen_b_files.py` (D-10 + registry checks green).
  **Verified live in Venture Lab:** *"Ender complete — seat closed to zero. Ids closed
  (14/14) … verified by a full account sweep (1,901 triggers) … nothing outside the 14
  attributed ids was touched."*
- **Universal Continue discoverability + version stamp (websites #424 + fleet-manager
  #331, merged, live).** The `/prompts` intro summary + quick-link row now generate from
  `FLEET_WIDE` (Universal Continue announced, not just its card); `v1.0 · 2026-07-18`
  stamp added. Also cleared a pre-existing orphaned claim (`nav-reachability-guard.md`)
  that was reding CI for *every* websites PR.
- **EAP follow-up email + evidence doc updated (this PR)** with the session's key finding.

## Key finding (for the EAP email)

The trigger/routine MCP tools force an interactive approval on **every call**, and
**no owner setting suppresses it** — verified with `bypassPermissions` + explicit
allow-list + the `mcp__Claude_Code_Remote` wildcard all set; the calls still prompt
because the approval sits above the settings layer. Downstream cost: **~1,900 orphaned
trigger tombstones** clearable only by a human tapping approve per delete; autonomous
cleanup is impossible. The v3.8 ender is the agent-side mitigation but works only
because the owner is present clicking at the attended ender/startup. Sharpens the
standing ask: an owner-accountability grant — for this class there isn't even a setting
to toggle.

## Owner decisions (provenance)

- Ender wipes **everything** for the seat, **seat-local only** (never account-wide) —
  owner directed in-session (2026-07-18); business crons included ("useless — a mortal
  seat can't own a future-dated cron; a 24/7 project does recurring work in its loop").
- Lifecycle: **startup arms** the single failsafe, **ender destroys** all — no carry
  across a clean ender (crash still leaves the startup-armed failsafe as the bridge).
- **Janitor routine + ~1,900 historical orphans: left as-is** (owner: "leave it") — the
  attended self-cleanup replaces the janitor going forward; orphans are a one-time clear.

## Owner workflow preference (apply next sessions)

When asking the owner to review something, **paste the actual contents in chat** — not a
PR/diff link. The owner does not read diffs; he reviews the **finished product** or the
**live result** (e.g. the new prompts rendered on the control-plane site). Candidate for
`docs/owner/maintainer-working-profile.md` on a future superbot-rooted session.

## 💡 Session idea

**Per-seat trigger-attribution ledger** (`telemetry/triggers-owned.json`, append-on-arm):
seat-local cleanup is only as good as attribution, and a fired `send_later` loses its
seat label in `list_triggers`, so the ender currently *reconstructs* ownership from
names + heartbeat. If each seat appended every trigger id it arms to a small owned-ids
file, the ender (and its successor) would have a deterministic per-seat id list — making
"delete only my own" exact and shrinking the orphan class at its source rather than after
the fact.

## ⟲ Previous-session review

The sessions that built the failsafe/pacemaker wake chain optimized hard for
*never going silent* but never closed the loop on *cleanup* — every armed routine
assumed a successor "cutover" that mostly failed, so tombstones compounded to ~2,000.
The workflow was missing a "what did I arm, and did it actually get cleaned?" invariant
to pair with the "did I re-arm?" one. System improvement: the highest-leverage guardrails
this fleet has are the ones that stop agents creating *durable* mess — `check_no_false_walls`
is the model for docs; the trigger-attribution ledger (idea above) + the v3.8 self-wipe are
the analog for routines. Enforce the invariant, don't exhort it.
