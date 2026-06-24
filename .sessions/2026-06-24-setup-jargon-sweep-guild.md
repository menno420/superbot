# Session — 2026-06-24 · setup plain-language sweep 1 (guild→server)

> **Status:** `in-progress` — born-red. First plain-language sweep on the setup wizard, building on the
> jargon guard (#1420). Reword the 58 operator-facing strings containing "guild" → "server" (mostly the
> uniform *"X requires a guild context."* → *"This can only be used in a server."*), then lower the
> ratchet `_BASELINE_TOTAL`. Pure UI-copy edits — **no behaviour change**; the guard + ratchet test
> verify the count drops. ⚑ Self-initiated (logical next step of the owner-directed plan, Q-A-independent).

## What I'm about to do

1. Replace the ~40 *"… requires a guild context."* error strings with *"This can only be used in a
   server."* (clears guild + any embedded jargon at once).
2. Targeted guild→server edits on the ~15 remaining labels/descriptions (Guild default → Server default,
   Guild ID → Server ID, "this guild" → "this server", resolver-walk "… → guild → default", etc.).
3. Re-run the guard, lower `_BASELINE_TOTAL` to the new measured count, re-run the ratchet test + arch.
