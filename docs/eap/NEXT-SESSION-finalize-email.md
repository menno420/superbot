# ▶ NEXT SESSION — finalize the second Anthropic email (owner's top priority)

> **Status:** `reference` — ✅ **STAGED 2026-07-12** — clean draft is in Gmail, ready for the owner to send.
> The finalization session ran with the owner live. Outcome: the send-ready email is now a
> **clean Gmail draft** (id `r9217428483600498478`) — a **reply on the July 8 thread**
> `19f41cd2e5380bb3` (so the original email is quoted below as reference), **To**
> `claude-code-early-access@anthropic.com`, **cc** `dliu@` / `omid@` / `mattg@`. The owner's
> Part 1 is kept **verbatim** from his own Gmail edit; all scaffolding (status header, `*****`
> markers, "Working notes") stripped; Part 2 de-markdowned; figures reduced to a plain key.
> **Left to the owner only:** (1) attach screenshots by hand (Gmail draft API can't attach —
> recommend Figs 1/5/7/9/10 + 15a–c); (2) delete the OLD standalone draft
> `r-7695257510039698568` (thread `19f513094d66637d`) so the uncleaned version isn't sent;
> (3) optional final glance at two Part-1 spots he was offered ("What I most want out of it
> manage…" missing verb; empty "My idea:" line) — left untouched per his "keep my sections
> unchanged". Optional non-blocker: refresh the review-site data (still a 07-11 snapshot) to
> today. **The section below is the original handoff, kept for provenance.**
>
> **Origin:** next-session handoff, written 2026-07-12 at session close (owner-directed: *"prepare the
> repo for the next session to continue finalizing the email with me as the next most
> important step"*). This was the **one thing that matters next**; it is now STAGED (see banner above).

## The state in one paragraph

The send candidate is **`anthropic-email-2-draft-2026-07-11.md`** (same folder). It is
**fully send-ready** — facts verified, all figures committed, the live review-site URL
filled in, findings 6 & 7 sharpened with the owner's own recording. The **only** remaining
work is Part 1 (the owner's voice): he wants to rewrite the **➕ NEW mock addition**
(2026-07-12 section) the way he rewrote the original Part 1 mock — in his own words. Once he
does, stage the Gmail draft and he presses send. Window closes **Tue 2026-07-14**.

## What the next session does — exact steps

1. **Read the draft** end to end (`anthropic-email-2-draft-2026-07-11.md`). Note the two
   owner-region blocks (original Part 1 + the "➕ NEW mock addition") are **owner-edits-only**
   — never rewrite his voice; you only fix typos and assemble.
2. **Ask the owner for his Part-1 rewrite** of the ➕ NEW mock addition (the 4 beats:
   self-wake proposal · model-fix confirmation *replacing* his old model paragraph · sidebar
   correction *replacing* his old sidebar paragraph · website closer). He may paste it rough
   — light typo pass only, keep his style (`tho`/`aswell` stay).
3. **When he's happy with Part 1**, assemble the **final send text**: strip the `‹src›` tags,
   the two `***OWNER EDITS ONLY***` marker lines, the `[Fig N]` markers (or convert to a
   figure appendix), and the mock/handoff scaffolding — leaving a clean Intro → Part 1 →
   Part 2 → figure list.
4. **Stage it as a Gmail draft** (Gmail MCP is available: `create_draft`) as a **reply on
   thread `19f41cd2e5380bb3`**, to `claude-code-early-access@anthropic.com` (reply-all keeps
   Diana/Omid/Matt). Attach the send-set figures from `screenshots-2026-07-11/` +
   `screenshots-2026-07-12/` (the index files name the send set). **Draft only — the owner
   sends.** Verify with him before creating the draft (external-publish confirm).

## Verified facts to trust (don't re-derive)

- **Nothing has been sent yet** — Gmail thread `19f41cd2e5380bb3` holds only the owner's
  July 8 email (verified 2026-07-12). This is the first follow-up.
- **Review site is LIVE:** https://review-production-f027.up.railway.app (created via Railway
  API under owner authorization; `/healthz` + all routes 200 as of 11:34Z). URL is already in
  the draft (both slots).
- **All figures are committed** — `docs/eap/screenshots-2026-07-11/index.md` (send set +
  the recovered 15a/b/c/17) and `docs/eap/screenshots-2026-07-12/index.md` (figs 20–35,
  send-set marked). No more "attach from phone" gaps.
- **The findings are current** through the owner's 13:41 recording (findings 6 & 7 updated).

## NOT part of finalizing the email (owner's separate track — don't block on these)

- **GitHub PAT** for the control-plane service — owner-only (no API mints a PAT). In the
  websites owner-queue.
- **Websites review-site data refresh** — one ORDER to the Websites Project to bake today's
  data (scheduler incident + v3.3 story) into the review site. Nice-to-have before send, not
  a blocker; the site is live and honest now.
- **`postgres-botsite` + `DATABASE_URL`** — already provisioned this session (submission-queue
  feature now agent-buildable).
- **Doc drift to flag, not fix mid-flight:** websites docs say services live in a
  "superbot-websites" Railway project; they actually live in **`reliable-grace`** (alongside
  `worker`/`botsite`/`dashboard`/`review`). Tell the websites lane; don't edit their repo from
  hub.
