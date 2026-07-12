# /prep-owner-steps — hand the owner finished steps, not directions

> **Owner-directed (Q-0273, 2026-07-12).** His words: agents give him "directions clearly
> mapped out — go to github, actions, settings, rule, etc, and paste this file from this
> github page in this repo — while they could easily lead with the link and the copy/paste
> ready file in chat as a separate block." The method: before handing the owner any step, ask
> *"which steps will he face, and are there any text blobs he might need to enter that I can
> send?"* — then send them. Substrate-kit generalizes this fleet-wide; this is superbot's copy.

## When this runs

Every time work surfaces an **owner-only step** (repo settings, secrets, portal clicks,
external publish, account actions) or any instruction the owner must execute by hand — in
chat replies, owner-queue items, ⚑ blocks, and run reports.

## The method — prepare, don't describe

1. **Lead with the direct link.** Deep-link the exact page (the ruleset editor, the Variables
   tab, the release form) — never a navigation trail when a URL exists. A trail ("Settings →
   Rules → main") is the *fallback annotation under* the link, for when the deep link 404s.
2. **Every blob he must enter ships as its own fenced block.** File contents, variable names,
   one-line replies, commit messages, form fields — each in a separate copy-ready block,
   labeled with exactly where it goes. Never "paste the file from this github page" — fetch
   it and paste it INTO the chat/queue item yourself.
3. **Walk his path once yourself, in your head or via probe.** Enumerate every click/field he
   will actually face (the screen he lands on, the button names, the confirm dialogs) and
   pre-answer each. If a step's outcome feeds a later step (a minted token → a variable),
   say what to carry forward and where it lands.
4. **Batch to one sitting.** If the task needs owner steps at multiple points, restructure so
   they cluster into ONE block at the start or end — never interleave "now go click X" through
   a work narrative he has to babysit.
5. **State the payoff + verification.** One line each: what completing the steps unblocks,
   and how he (or the next agent) verifies it worked (the exact URL/command that should now
   succeed).

## The shape (use it in queue items and chat alike)

```
⚑ OWNER — <what this unblocks, one line>
1. <deep link>  (fallback: Settings → … → …)
   paste ↓ into <exact field>:
   ```<the blob>```
2. …
verify: <command/URL that should now succeed>
```

## The bar

The owner should be able to complete every step with **clicks and pastes only** — zero
composing, zero fetching, zero deciding-what-you-meant. If he has to open another page to
*copy something you could have copied for him*, the preparation failed.
