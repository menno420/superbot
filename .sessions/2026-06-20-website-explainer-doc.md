# 2026-06-20 — Plain-language website explainer doc (owner-requested)

> **Status:** `complete`

## Arc

Follow-up to the SPA-wiring session (PR #1196, merged). The owner — still learning the web/design
side — asked for a plain-language explanation of "what Jinja and the SPA mean etc., plus other
useful stuff," and how to continue working in Claude Design ("do I just tell it to sync to main?").

## Shipped

- **`docs/owner/website-explained.md`** (`owner-guidance`) — plain-English tour: server-rendered
  (Jinja) vs. SPA, hash routing / `window.SBDATA` / no-build, static vs. dynamic data, the
  `disbot → site.json → data.js → SPA` pipeline, the three web folders (`botsite`/`dashboard`/
  `design-system`), the **Claude Design loop** (GitHub connector = sync of the *library*; porting a
  design onto the live site is a separate Claude-Code step; data is fully automatic), and a
  supporting-cast glossary (FastAPI/route/API/Railway/CI/linter/auto-merge/PR).
- Linked from `docs/AGENT_ORIENTATION.md` (website route, item 0) + `botsite/README.md`; corrected
  the orientation's "production stays Jinja" line to reflect the SPA-as-front-end reality, and
  flagged the design-system README's now-stale "port into Jinja" framing as a reconcile-when-convenient.

Verification: `check_docs --strict` ✓ (doc reachable, badged `owner-guidance`).

## Answer to the owner's Claude Design question (captured in the doc)

"Sync to main" updates what Claude Design *reads* (the `design-system/` component library, via the
GitHub connector) — but it does **not** push a design onto the live site by itself; that still needs
a Claude-Code port step. Data is separate and automatic. The one thing to *set* in Claude Design is
the "Add to Discord" link (still a placeholder).

## ⚑ Self-initiated

None — owner-directed (write the explainer + answer the Claude Design question).

## 💡 Session idea (Q-0089)

**Reconcile the design-system↔front-end story now that the SPA is live.** The `design-system/`
README still says "production stays Jinja; port designs into Jinja." With the SPA shipped, a small
decision + doc update is owed: does the React component library now feed the SPA (retiring the port
step), or do both stay? Capturing it as a router/idea prevents the two docs drifting further. (Noted
here + flagged in AGENT_ORIENTATION; not generalized this run.)

## ⟲ Previous-session review (Q-0102)

The SPA-wiring session (#1196) shipped end-to-end and its sync-guard test caught a real
data.js/site.json drift in CI — good. **What it could have done better:** it left the
design-system↔SPA story inconsistent (README still says "Jinja only"), which this doc had to flag.
**System improvement:** when a session changes *which* front-end is live, it should update the
design-system README in the same PR — a "front-end-of-record" pointer in one place would stop the
two docs disagreeing.

## 📤 Run report

- **Did:** wrote the plain-language website explainer + answered the Claude Design workflow question ·
  **Outcome:** shipped (docs-only)
- **Run type:** `manual · owner-task (docs)`
- **⚑ Owner decisions needed:** design-system↔SPA reconcile (non-urgent; flagged)
- **⚑ Owner manual steps:** set the "Add to Discord" link in Claude Design
- **↪ Next:** on request — reconcile the design-system README to the SPA; wire the install URL
