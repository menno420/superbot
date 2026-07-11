# Screenshot drop — for the second Anthropic email (2026-07-11)

> **Status:** `reference` — a drop folder for Menno's session screenshots so Claude can
> review them and rank which are worth attaching to the second Anthropic email. Linked
> from [`../anthropic-email-2-draft-2026-07-11.md`](../anthropic-email-2-draft-2026-07-11.md)
> § FIGURES.

> ⚠️ **`superbot` is PUBLIC** — anything committed here becomes publicly visible. That's
> consistent with the rest of the EAP record (which is public by design and shared with
> Anthropic), but if a screenshot shows something you'd rather not publish (a private
> project's internals, anything sensitive), push it to a **throwaway private repo** instead
> and tell me the name — I'll `add_repo` + pull it. No secrets/tokens in any frame.

## How to use

1. **Drop your PNGs/JPGs in this folder** and push (any filenames are fine — even
   `IMG_1234.png`). Batch as many as you like; there's no per-commit limit on GitHub.
2. Tell me "screenshots are up" — I'll `git pull`, **view every one**, and give you a
   ranked **SEND / MAYBE / SKIP** verdict, each mapped to a finding in the email + a
   one-line caption ready to paste.
3. You attach only the winners to the actual email (Gmail cap ~25 MB; but aim for ~6–8 —
   curation beats volume).

## What I'm most looking for (maps to the email's Figure list)

Optional — helps if you name or note which is which, but not required; I'll sort them.

| Want | Shows | Priority |
|---|---|---|
| The **Deny/Allow prompt on YOUR screen** for a scheduling tool, when the agent reported success | The two-vantage split — your single best evidence | ⭐ highest (new) |
| A **Routine's edit panel** showing its **model** field (esp. one that differs from what ran) | The model mismatch, visually | ⭐ high (new) |
| A Routine's edit view showing **no repo attached** / where you attach it | The routine-repo bug + your fix | ⭐ high (new) |
| A **stale "Working…" session** in the sidebar, long after it finished | The oversight gap | high (new) |
| The **Projects grid** (all ~15 tiles) + the Routines list | Fleet scale | ✅ have it |
| A session's verbatim **merge denial** (`[Self-Approval]/[Merge Without Review]`) | The permission wall, exact text | ✅ have it |
| Your typed **standing merge-grant** message | The human-authorization workaround | ✅ have it |
| The **PR-#68 "3 walls" / context-sensitivity** investigation | The merge wall is structural + context-driven | ✅ have it |
| Anything else you found striking | (I'll tell you if it earns a spot) | — |

Send me the raw pile — over-send is fine, I'll do the curating.
