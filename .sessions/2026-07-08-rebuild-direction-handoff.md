# Session — Close-out: rebuild-direction handoff + email marked sent

> **Status:** `complete`

## What this session did (close-out of a long EAP → production chat)
The owner moved from *evaluating* Claude Code Projects to *using* one for the real rebuild build, and
is switching the directing role to a fresh Sonnet-5 session (limit-watching + a model-comparison
bonus). This session swept the chat into durable homes and handed off:

- **Created the directing handoff** `docs/planning/rebuild-direction-handoff-2026-07-08.md` — live
  state (the rebuild Project is running: 3 repos, canonical §5 steps 7–13, build-first/test-later,
  forward-only), the **two axes to score each coordinator report** (owner-directing quality;
  self-correctness / spec-drift), the owner-only checklist, next-email material, and the banked
  findings. Linked from the kickoff doc.
- **Marked the Anthropic email SENT** (2026-07-08, `claude-code-early-access@anthropic.com`, no reply
  yet) in `projects-eap-anthropic-email-2026-07-08.md`.
- Left a **small starting prompt** for the next session (below + in chat).

`check_docs --strict` green.

## Chat sweep — everything captured, nothing left only in chat
- Email finalized + **sent**; both authors signed (Menno / Claude). ✓ (email doc marked sent)
- Permission model fully mapped incl. the **live accept-edits probe** (scheduling tools gate in every
  mode; GitHub MCP write silent; two-vantage split). ✓ (eval log 2026-07-08 entries)
- **Empty-repo correction** (repos already seeded → normal git; access was never the constraint). ✓
  (kickoff doc)
- **Rebuild Project kickoff** (Custom Instructions + startup prompt). ✓ (`rebuild-project-kickoff`)
- The **two axes to watch** during the run. ✓ (handoff doc)
- Anthropic contacts + free-window-ends-7/10 + Max-renew-direct. ✓ (handoff doc)
- Session-close **footgun** (reset-to-main while own PR open). ✓ (handoff working-discipline + below)

## Small starting prompt for the next (Sonnet-5) session
> You're directing the SuperBot rebuild Project, which is now running. Start by reading
> `docs/planning/rebuild-direction-handoff-2026-07-08.md` (live state, your job, the two axes to
> score), then `docs/planning/rebuild-project-kickoff-2026-07-08.md` and the canonical plan §5. I'll
> paste the coordinator's status reports as they come; for each, help me (1) act on any owner-only step
> it flags, and (2) note how well it directed me and whether its build looks spec-correct. The
> Anthropic feedback email is already sent — just flag any reply.

## 💡 Session idea (Q-0089)
**Allocate the management/directing layer to a cheaper model than the execution fleet.** This session
proved the two-layer split (directing chat vs. building Project); the directing layer mostly *reads
reports + routes owner-only steps + scores axes* — cheap cognitive work — while the build fleet needs
top-tier. Running the director on Sonnet 5 while the Project fleet runs Opus is a deliberate
cost-shape, not just a limit workaround. Worth a doc note in the collaboration model: name the
management layer as the place to spend a cheaper model. (Distinct from the earlier PROJECT_KICKOFF
template + memory-audit-routine ideas.)

## ⟲ Previous-session review (Q-0102)
Previous session (rebuild-project-kickoff, #1867) shipped the kickoff but its first push hit **two
avoidable reddenings**: (a) the plan-homing orphan — the new `plan` doc wasn't added to
`docs/planning/README.md` (the #1855 guard caught it — as designed, but it should've been in the first
commit), and (b) an **over-cautious constraint written from stale state** (told the coordinator to use
the Contents API to "populate" repos that were already seeded — the owner corrected it). **System
lesson:** for a new `plan` doc, home it in the planning README in the *same* commit; and **verify
current-state facts** (are the repos empty?) before baking constraints into instructions — a wrong
assumption in a coordinator brief propagates to a whole autonomous run. Both are now in the handoff's
working-discipline note.

## 📋 Doc audit (Q-0104)
`check_docs --strict` green. Handoff doc badged `reference` (not `plan`, so no plan-homing burden) and
linked from the kickoff doc; email doc marked sent; all cross-links resolve. No new binding rule → no
router Q. Nothing from this long session lives only in chat.
