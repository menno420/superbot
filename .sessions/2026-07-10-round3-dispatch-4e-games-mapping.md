# Session — round-3 dispatch, part 4e: owner shapes the games mapping (theme engine + website-first)

> **Status:** `complete`
> **Run type:** owner-directed · same live dispatch chat (parts 4/4b/4c/4d: PRs #1957/#1963/#1964/#1965, merged)
> **Model/time:** fable-5 · 2026-07-10 ~21:5xZ → ~22:0xZ
> Branch: `claude/sim-lab-repo-setup-ujglev` (restarted from main post-#1965) · PR #1966.

## What is about to happen

Owner gave the games-program shape live (superseding "wait for the manager's proposal"):
ONE Project on `superbot-games` owning the whole world ecosystem (exploration + mining +
fishing + world systems), a SECOND repo+Project for the egg-farm idle game built
template-first, themes choosable on the website BEFORE the bot is invited, and a
core/skin split so the same game core ships different themes per server. Asked me to
expand and improve. Capture: router Q-0267 (verbatim words + decisions), an idea file
with the expanded architecture (theme packs as data, provisioning contract, plugin-seam
convergence), runbook §3.7 update + §6.2 manager paste block.

## What happened

- **Ground truth fetched before designing (Q-0120):** `superbot-games` README + both
  lane heartbeats at HEAD (exploration WIND-DOWN COMPLETE 2026-07-09, mining gen-1
  complete — one gen-2 Project over both is *consistent with* their committed
  succession packages, incl. `docs/gen2-custom-instructions-exploration.md`);
  `superbot-plugin-hello` confirmed as the Builder's OWNER-ACTION 2 / flag-18a
  contract-validation repo (owner-created today, root still empty at main).
- **Q-0267 appended** (owner words verbatim + 5 decisions): mapping owner-shaped —
  manager's Q-0259 r.5 deliverable converts from *propose* to *conform + fill in*.
- **Expanded design shipped**: `docs/ideas/games-theme-engine-website-first-2026-07-10.md`
  (+ README index row) — theme packs as data-only CI-validated manifests (the best
  Q-0266 populate-phase fit: themes are mass-producible at near-zero risk), egg farm as
  first theme of an idle ENGINE, website-first provisioning with a setup-code interim
  path, plugin-seam convergence (superbot-next ORDER 002), sim-lab as the idle-economy
  verdict path, two-seat mapping table with first shippables.
- **Runbook updated**: §3.7 re-pointed (owner-shaped, what's still open), §4 queue row
  rewritten (packages draftable on the conformed mapping OR direct owner go), **§6.2**
  conformed-mapping paste block committed (the §6 durable-block convention's second
  entry, minted in 4d).

## ⚑ Self-initiated

- The four decided-and-flagged design calls in the idea file §7 (plugin-native / no
  old-bot port · setup-code before join-time provisioning · theme contract drafted in
  the idle repo then promoted · `superbot-idle` name suggestion) — veto point is the
  owner's mapping react.
- Converting the manager's deliverable propose→conform in §6.2 (mechanical consequence
  of Q-0267, but it rewrites an instruction already pasted to another seat).

## 💡 Session idea

**Themes as the fleet's first community-contribution surface.** Because theme packs are
data-only and theme-gate CI validates them mechanically, `themes/` is the first place
non-owner humans (server admins) could safely contribute PRs — the gate reviews
mechanics-safety, a human only eyeballs taste. Dedup: not in `docs/ideas/` or the
roadmap; extends Q-0267 in a direction the owner hasn't stated. Kept inline (one line
in the idle founding package's backlog section will carry it when drafted).

## ⟲ Previous-session review

Part 4d minted the §6 durable-paste-block convention and 4e immediately consumed it
(§6.2) — the convention proved itself within the hour. Its gap, visible now: §6 blocks
carry no delivery state, so the section will accumulate blocks whose "did the owner
actually paste this?" status lives only in chat memory. Improvement (applied): both §6
entries now say "pending paste" in their context lines; the next sweep flips them to
"pasted <time>" on owner confirmation, same as any other verified fact.

## Documentation audit (Q-0104)

`check_docs --strict` ✓ · `check_plan_homing --strict` ✓ (no new plan doc; idea file
lives in ideas/ + indexed) · `check_current_state_ledger --strict` ✓ (benign
newest-merge lag only) · chat-only material swept: owner's games shape → Q-0267
verbatim; the expansion → idea file; the manager instruction change → §6.2; repo
ground-truth findings → this card + idea file §4/§5. Claim file deleted this commit.

## Handoff

Owner: react to the expanded design in-chat (the four §7 flags), then paste **§6.2**
into the manager chat. After the conformed mapping (or a direct "go"): the next
dispatch part drafts the **two games founding packages** on the gen-3 standard — the
recipe's next consumers. Unchanged clicks: sim-lab OA-002 Codex toggle · EAP email
before 07-14 · §2.5 batch · orphan-watchdog go.
