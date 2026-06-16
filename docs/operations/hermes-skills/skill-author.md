# Skill: `superbot-skill-author`

> **Status:** `living-ledger` — the **meta-skill**: it teaches Hermes to design a *new* SuperBot
> skill correctly and land its source in the repo, so the skill pack is version-controlled instead
> of living only on the VPS. Update it when the skill format, the build step, or Hermes' write
> scope change. Provenance: owner-directed 2026-06-14 (the self-extension layer); the docs-only-PR
> write it relies on is Q-0140.

**Window:** you've noticed a workflow you repeat, or the owner asks you to "make a skill for X"
**Purpose:** Turn a recurring Hermes workflow into a new, well-formed, version-controlled SuperBot
skill — design it, write it in the repo's skill format, regenerate the installable artifact, and
open a docs-only PR so it is reviewed and committed (not left as a VPS-only scratch file).

**When to use:** when the same multi-step sequence keeps recurring (so it should become one skill),
or to build a **composite** that chains existing atoms (e.g. an overseer `tick` that runs
health → decide → dispatch). The closing of the "Hermes writes its own skills, but they never make
it back into the repo" gap.

**The write it depends on (Q-0140):** authoring a skill is a **docs-only** change, which is one of
Hermes' two sanctioned writes (the other is the `review-merge` gate). Hermes still never edits code,
pushes runtime changes, or touches production.

---

## Prompt

```
You are Hermes, working with the SuperBot repository at /home/hermes/repos/superbot.
GOAL: design a NEW SuperBot skill (or composite) and land its source in the repo via a
docs-only PR. A skill is a reusable prompt; authoring one is a DOCS-ONLY change (Q-0140) —
your sanctioned write. You never edit code or push runtime changes.

STEP 1 — JUSTIFY (read-only). Before writing anything:
  - git -C /home/hermes/repos/superbot fetch origin main
  - Confirm the workflow RECURS (a one-off doesn't earn a skill) and is not already covered:
      ls docs/operations/hermes-skills/ ; grep -ril "<the-job>" docs/operations/hermes-skills/
    If an existing skill already does this, STOP and use it instead.
  - State in one line: the WINDOW (when it's used) and the PURPOSE (what it produces).

STEP 2 — DESIGN. Decide:
  - name: superbot-<kebab-case> (lower-case, hyphens).
  - For an ATOM: the ordered read-only steps + the single output it produces.
  - For a COMPOSITE: keep it THIN — encode the DECISION FLOW that chains existing atoms
    ("run the health check; if X dispatch a fix; else propose a continuation"), and REFERENCE
    the atoms rather than re-implementing them. Do not duplicate another skill's body.
  - Bake in the standing rules so the skill is safe on its own:
      * read-only by default; the only writes are docs-only PRs and the review-merge gate;
      * anything touching code is DISPATCHED to Claude Code, never edited here;
      * verify, don't assume (railway_vars.py / check_* / gh) — say what you verified;
      * never print secrets; reference env vars by name only;
      * MINIMIZE tool round-trips — each call is a model request on a RATE-LIMITED provider, so a
        chatty skill (~12 calls) trips the limit mid-run. Prefer ONE combined shell command per step
        (chain with `&&` / `;`), give exact commands rather than open-ended "scan/search for X" (the
        model fans out into many calls), and lean on what a backing script already extracted. A
        scheduled skill should be only a handful of calls + one compose (the #959/#969 rate-limit
        rework, 2026-06-16);
      * end with one clear verdict or next step (a hint, not an action you take).

STEP 3 — WRITE THE SOURCE. Create docs/operations/hermes-skills/<name>.md in the canonical shape
  (copy an existing skill's structure exactly — e.g. session-brief.md or dispatch.md):
      # Skill: `superbot-<name>`
      > **Status:** `living-ledger` — <one line>.
      **Window:** ...   **Purpose:** <one sentence — the builder lifts this verbatim>
      **When to use:** ...
      ## Prompt
      ```
      <the skill's prompt body — the instructions you will follow when it runs>
      ```
      ## Notes
      <why it exists, gotchas>
  Requirements the builder enforces: the H1 must contain `superbot-<name>` in backticks; there
  must be a **Purpose:** line and a ## Prompt fenced block.

STEP 4 — REGISTER + BUILD. Add a tags entry for the new stem to the EXTRAS dict in
  scripts/hermes/build_skills.py (copy a sibling's line). To make the skill SELF-FIRE on a schedule
  (like superbot-morning-briefing / superbot-idea-spotlight), add schedule=("<cron>", "<one-line
  task>") to its EXTRAS entry — Hermes then runs it on that cron and delivers to the home channel,
  no VPS cron needed, and each scheduled run is a fresh stateless session. Then regenerate the
  installable artifact:
      python3 scripts/hermes/build_skills.py
      python3 scripts/hermes/build_skills.py --check     # must pass
      python3 scripts/check_docs.py --strict             # reachability/pins
  (build_skills.py edits scripts/hermes/build_skills.py only to add the tags line — that is a
  tooling registration, still a docs/tooling change, not a runtime edit. If you are unsure, ask.)

STEP 5 — LAND IT (your docs-only PR). Branch, commit the new doc + its generated SKILL.md +
  the EXTRAS line, push, and open a docs-only PR:
      git checkout -b hermes/skill-<name>
      git add docs/operations/hermes-skills/<name>.md scripts/hermes/skills/<name>/ scripts/hermes/build_skills.py
      git commit -m "docs(hermes): add superbot-<name> skill"
      git push -u origin hermes/skill-<name>
      gh pr create --repo menno420/superbot --title "docs(hermes): add superbot-<name> skill" --body "<what it does + why>"
  Report the PR link and ping me. A Claude Code session or I review/merge it (or you review it via
  superbot-review). Once merged, install on the VPS with scripts/hermes/install-skills.sh.

RULES:
- Docs-only. If the skill would need a code/runtime change to work, STOP — dispatch that part to
  Claude Code instead, and make the skill assume it exists.
- One skill per PR. Don't bundle.
- A new skill must be genuinely new — never duplicate or lightly reword an existing one.
```

---

## Notes

- **Why this is the bootstrap.** "Ask Hermes to make a skill" only produces something *durable* if
  the skill lands in the repo in our format and regenerates its artifact. This skill is the recipe
  that makes that happen — without it, Hermes-authored skills stay as VPS-only scratch
  (`~/.hermes/skills/`) that no one can review.
- **First intended use: composites.** With this in place, ask Hermes to author the overseer `tick`
  (health → decide → act), `triage-and-fix` (log-triage → dispatch), and `watch-and-review`
  composites — each a thin orchestration over the existing atoms. That dogfoods the whole loop:
  Hermes writes a skill → opens a PR → it's reviewed → merged.
- **Keep composites thin.** A composite encodes the *decision flow* and calls the atoms; it must not
  re-implement them. If a composite is mostly copied atom bodies, it's wrong — reference instead.
- **Provenance + reliability (Q-0105).** Added 2026-06-14, owner-directed. UNVERIFIED until Hermes
  has authored at least one accepted skill through it — confirm the first PR is well-formed before
  trusting it unattended. Delete or revise if it produces malformed skills.
