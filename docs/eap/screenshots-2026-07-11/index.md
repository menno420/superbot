# Screenshot figures — second Anthropic email (2026-07-11)

> Curated from 64 uploaded screenshots (PRs #1987/#1988/#1989, recordings excluded),
> triaged by 3 review agents. These 16 are the keepers; the other ~48 were routine session
> views with no evidentiary value (SKIP). Clean `fig-NN` names map to the email's figure
> slots; the original filename is kept here for provenance. **Tier 1 = definitely send;
> Tier 2 = strong extras if you want more.** The model-mismatch shot (F4) is the one weak
> slot — see the note at the bottom.

## Tier 1 — the core set (send these)

| Fig | File | Original | Shows | Caption for the email |
|---|---|---|---|---|
| **1** | `fig-01-scale-grid-routines.jpg` | 0711 01:46 | Projects grid (14+ tiles) + failsafe-wake Routines list | The fleet at scale — ~15 Projects, each its own repo, plus their Routines. |
| **2** | `fig-02-merge-denial-verbatim.jpg` | 0711 03:30 | Verbatim "[Merge Without Review] … also implicates [Self-Approval]" | The merge wall, in the classifier's own words. |
| **3** | `fig-03-standing-grant.jpg` | 0711 03:36 | Operator's standing grant: "don't keep waiting, keep creating PRs" | The workaround: I hand-type a permission slip so work doesn't stall. |
| **4** | `fig-04-denial-beside-grant.jpg` | 0710 23:08 | `enable_pr_auto_merge` denied as self-merge, beside the operator granting it | The problem and my fix in one frame. |
| **5** | `fig-05-wall-tracks-session-not-pr.jpg` | 0711 14:01 | "the wall tracked the sessions, not the PR" | The key finding: the classifier judged the *session's context*, not the PR. |
| **6** | `fig-06-three-stacked-walls.jpg` | 0711 13:42 | Three stacked walls incl. "Can not approve your own pull request" | Why a green PR can't self-land — three independent walls, all verbatim. |
| **7** | `fig-07-twovantage-predict-then-modal.jpg` | 0708 15:58 | Operator predicts "try delete trigger, that'll prompt me" → the Deny/Allow modal fires | The two-vantage split: the gate I see that the agent is blind to. |
| **8** | `fig-08-twovantage-modal-listrepos.jpg` | 0711 01:27 | Deny/Allow modal: "Allow Claude to use list repos" | A second permission prompt on my screen the session reported as a clean success. |
| **9** | `fig-09-oversight-stuck-6h54m.jpg` | 0708 11:21 | Session runtime 6h 54m, stuck on an unavailable tool | The oversight gap: a session burned ~7h and nothing surfaced it. |
| **10** | `fig-10-routine-no-push-credential.jpg` | 0710 21:13 | Routine fired but "no push credential" for its repo | A routine session woke with no way to land its own work. |
| **11** | `fig-11-repos-attach-panel.jpg` | 0707 22:40 | Project Settings → Repositories (attach / Add) | Where repos attach to a Project — the fix surface for the routine-repo bug. |

## Tier 2 — strong extras (send if you want more depth)

| Fig | File | Original | Shows | Caption |
|---|---|---|---|---|
| **12** | `fig-12-4096-byte-cap.jpg` | 0708 02:10 | "start_project_session: instructions must be at most 4096 bytes" | The verbatim child-brief size cap that forced us to compress every lane brief. |
| **13** | `fig-13-skip-all-approvals-toggle.jpg` | 0708 14:05 | "Skip all approvals?" beta modal ("can put your data at risk") | The blunt toggle that exists today — I want a scoped, safer version of this. |
| **14** | `fig-14-setup-script-failure.jpg` | 0709 15:37 | Setup script failed (not-a-git-repo / missing requirements.txt) | A non-zero setup script left a session dead ~30 min with no signal. |
| **15** | `fig-15-model-labels-opus-fable.jpg` | 0710 16:53 | Session labels Opus 4.8 / Fable 5 + auto-merge re-arm bug | Weak F4 — closest shot to the model-mismatch (better told in words; see note). |
| **16** | `fig-16-owner-projects-not-self-aware.jpg` | 0710 23:00 | Operator note: "projects aren't aware how they work themselves yet" | My own words behind the capability-self-awareness ask. |

## F4 (model mismatch) — NOW FILLED (your phone shots, 2026-07-11)

These 4 are on your phone, not in this repo folder — **attach them to the email directly**
(or drop them into a GitHub upload and I'll add them here). The first three are a **complete
model-mismatch proof and the single best evidence in the whole set — send all three as a
sequence:**

| Fig | Shows | Caption |
|---|---|---|
| **15a** | pokemon-mod-lab routine Edit panel: model **Opus 4.8**, repo attached, env `gba-lab` | A routine configured as Opus 4.8. |
| **15b** | gba-homebrew routine Edit panel: model **Opus 4.8**, *two* repos attached | Same — configured Opus 4.8, driving two repos. |
| **15c** | The gba-homebrew session it woke: agent states "I'm running as **Sonnet 5**, not Opus 4.8 … given to me as fact" | …but the session actually ran Sonnet 5. Config and reality silently diverge. |
| **17** | Fable 5 session: explicit in-session grant clears the classifier, but `git push --delete` still 403s | Even with permission granted, the git credential layer 403s server-side — two walls, one action. |

15a → 15b → 15c is a three-shot narrative (config says Opus 4.8 → session ran Sonnet 5);
it **supersedes** the weak Fig 15 `model-labels` shot above. Fig 17 corroborates the 403
branch-delete wall from the July 8 email (grant clears the classifier; the credential still
403s).

## Provenance
Sources: worktrees of PRs #1987 (`menno420-patch-2`), #1988 (`menno420-patch-3`), #1989
(`menno420-patch-3-1`). The ~48 SKIP images (routine session views, GitHub config, ChatGPT
UI, dashboards) are not copied here; the bulk upload PRs can be closed unmerged so main
stays clean.
