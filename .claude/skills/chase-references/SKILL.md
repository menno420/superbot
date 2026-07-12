# /chase-references — resolve every reference in the ask before acting

> **Owner-directed (Q-0273, 2026-07-12).** Founding incident: the owner opened a session
> with a comprehensive message containing a direct link to the previous session's brief and
> multiple sibling repos by name — and the session still oriented superbot-only, costing ~3
> turns of re-discovery. The lesson graduates here as an on-demand method (his words: "baked
> into a method, like a skill, that prevents it from taking up too much storage in the
> claude.md itself, but is still always loadable on demand"). Substrate-kit generalizes this
> for every repo; this is superbot's copy.

## When this runs

At the start of ANY substantive ask — an opening message, an ORDER, a brief — and again
whenever a mid-task message introduces new references. Trigger especially on: URLs · file
paths · doc titles · repo names · PR/issue numbers · Q-numbers · "as discussed in / the plan
says / the brief covers" phrasings.

## The method

1. **Inventory first.** Before any substantive work, list every reference the ask contains
   or implies (explicit links, named files, named repos, named plans, "the X doc"). The ask's
   references ARE its context spec — the author included them because reading them is cheaper
   than re-deriving them.
2. **Resolve each one, in this order:**
   - a local path → Read it;
   - a superbot doc name → open it (`Glob`/`Grep` if the path is fuzzy);
   - a **sibling repo or its file** → raw-fetch it (standing-authorized, Q-0272 — see
     `docs/fleet-reading-path.md`; `python3.10 scripts/fleet_status.py --repo X` for
     heartbeats);
   - a PR/issue number → pull it via MCP (own repo) or the heartbeat/raw pointer (sibling);
   - a Q-number → grep the question router.
3. **An unfound reference is a search task, never a skip.** Guess the most-logical homes and
   look there before proceeding: `docs/owner/` (owner guidance/dispatch) → `docs/planning/`
   (plans) → `.sessions/` (recent session records) → `docs/ideas/` → the named sibling repo's
   `control/status.md` + `docs/` + `ideas/` via raw. If it is genuinely absent after that,
   SAY so explicitly ("the brief references X; I could not find it in A/B/C") — silent
   omission is how wrong pictures get built.
4. **State the assembled picture back** (Q-0254): one short paragraph of what the references
   collectively establish, before the work starts. A wrong assumption corrected here costs
   one line; discovered later it costs the session.

## The bar

You are done chasing when every reference is either **read**, **fetched**, or **explicitly
reported unfindable with the places you looked**. "I'll read it if it becomes relevant" fails
the bar for anything the owner linked or named directly — he already decided it was relevant.
