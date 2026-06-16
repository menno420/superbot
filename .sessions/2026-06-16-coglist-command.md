# Session — `!coglist` text command → the "📋 Cog List" button (owner request)

> **Status:** `in-progress`

## What I'm about to do

Owner: "the command coglist should be a real command — there is a button that does exactly that, so
link the text command to the button as well." The admin panel's **📋 Cog List** button
(`_AdminPanelView.coglist_btn`) opens the interactive `_CogManagerView` (loaded/unloaded/syntax
status for every cog; mutations owner-gated). After BUG-0014 (#949) I removed the orphaned `coglist`
synonym; now I make `coglist` a **real command** that opens that same view, with `cogs`/`listcogs`/
`cogslist` as exact aliases (no fuzzy synonym needed → #949's synonym-orphan invariant stays green).
Admin-gated like `!adminmenu` (the panel that hosts the button); the view keeps mutation owner-gating.

(Filled in as the deliberate final step — born-red per Q-0133.)
