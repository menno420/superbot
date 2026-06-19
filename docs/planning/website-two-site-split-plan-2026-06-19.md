# Website two-site split — implementation plan + ultracode decomposition

> **Status:** `plan` — the implementation plan executing the **brief**
> ([`website-two-site-split-planning-brief-2026-06-19.md`](website-two-site-split-planning-brief-2026-06-19.md))
> and the owner decisions in router **Q-0178** + **Q-0179**. Owner-directed 2026-06-19. Source code +
> merged PRs win over this document. The next step after this plan is an **ultracode build run** on the
> disjoint back-half units in §5.
>
> **▶ Open decisions LOCKED 2026-06-19** (owner, via the question panel — full record in §7): control
> panel → **bot site** (Q-0179, realized as a gated surface isolated from the secret-free public marketing
> pages, gated on the control-API security review) · domains **deferred** to cutover (build on Railway
> URLs) · live-widget source = **generated build-meta v1** (live aggregator deferred behind the security
> review) · submissions DB = **separate dashboard-owned Postgres** · changelog = **curated** · `/submit`
> spam = **honeypot + rate-limit v1**. The build run is now decision-unblocked. A short **Layout & UX
> guidance** section (folded from the owner's 2026-06-19 external research) gives the build run concrete
> page specs.
>
> **North-star alignment:** this split is the IA realisation of the four-zone model in
> [`dashboard-vision-finalized-state.md`](dashboard-vision-finalized-state.md) — the **Public** zone
> becomes the bot site; the **Personal / Server-admin / Owner-developer** zones stay the dev site. The
> two binding principles never bend: *(1)* the bot is the source of truth, *(2)* front-end the bot's
> audited seams — never a parallel system.

---

## 0. Orientation — what exists today (grounded, so the plan is accurate not aspirational)

The single dashboard service already does **most** of what the dev site needs. The split is therefore
**95% audience-presentation + one new intake flow over a shared data backbone**, not a feature
migration. Establishing this up front keeps the decomposition small and the rollout low-risk.

**The current `dashboard/` service** (one Railway service, root dir `dashboard/`, auto-redeploys on
merge to `main`):

| Concern | Reality today (verified in source) |
|---|---|
| Stack | FastAPI + Jinja2 + Tailwind-CDN, Python 3.10; **no JS build, no `static/` dir** (`.gitignore` ignores `static/` — the #970 deploy-crash gotcha) |
| Decoupling | `dashboard/` **never imports `disbot/`**. It reads the committed `dashboard/data/dashboard.json` |
| Data producer | `scripts/export_dashboard_data.py` (pure stdlib) → `dashboard.json`. Composes sibling scanners (`scan_commands`, `scan_settings`, `scan_setting_specs`, `scan_access`, `scan_synonyms`, `scan_env_usage`) + markdown parsers (ideas, bugs, reviews, updates) + the subsystem-registry AST |
| Read pages (no auth) | `/` `/status` `/functions` `/games` `/commands` `/aliases` `/settings` `/access` `/ideas` `/bugs` `/reviews` `/updates` `/env` `/healthz` |
| Control zone (Discord OAuth, **dormant** unless configured) | `/auth/*`, `/me`, `/admin`, `/admin/{guild}`, `/admin/{guild}/overview`, and POST editors `/admin/{guild}/{settings,help/overlay,help/home,routing}` |
| Web→bot writes | `dashboard/control_client.py` → the bot's **private** `control_api.py` (aiohttp on the health server, `worker.railway.internal`, bearer `CONTROL_API_TOKEN`, **dormant** until the token is set). Every write re-resolves the live `discord.Member` and goes through the bot's **audited seam** |
| Hardening already shipped | stdlib HMAC-signed session cookie (`websession.py`), CSRF tokens on editor forms, sliding-window rate limiters (`ratelimit.py`) on login + edit POSTs; the bot also per-(guild,user) rate-limits control-API writes |

**Two facts that shape the whole plan:**

1. **The read pages are already public + read-only + value-free.** `/env` renders env-var *names +
   code locations only* (never a value); `/settings` renders keys + typed `SettingSpec` metadata
   (never a stored value); `/access` is a *visibility* map; `control_client.py` never echoes the
   token. So "all dev pages public read-only" (Q-0178) is **largely already true** — the work is to make
   it *explicit and audited*, not to rebuild it.
2. **The only genuinely private surfaces are the per-guild control panel and the (future) owner zone.**
   `/admin/*` renders one server's *live* config (settings values, help text) and is already
   OAuth + bot-authority-gated. Those stay gated; they are the "owner-gated for edits" half of Q-0178.

---

## 1. Page / audience allocation matrix  *(deliverable 1)*

Every current page mapped to **bot** (public bot site) / **dev** (repurposed dashboard) / **both**
(same generated data, *different framing/chrome per site*). "Both" never means shared templates — it
means both sites render the **same `dashboard.json` family**, each with its own audience-appropriate page.

| Current page | bot / dev / both | Rationale |
|---|---|---|
| `/` (landing) | **both** | Each site owns its own `/`: bot = marketing router-landing (hero, feature bands, "Add the bot" CTA, trust band); dev = the engine-room index it is today |
| `/status` | **both** | bot = a slim user-facing **trust band** (online + build + uptime); dev = full inventory + bug/access health |
| `/functions` | **both** | The subsystem catalogue *is* the "feature showcase" the bot site wants; dev keeps the developer framing |
| `/games` | **both** | Player-facing by nature → prime bot-site material; also a dev catalogue |
| `/commands` | **both (split by capability)** | bot = read-only **command reference** (search/filter, no Manage); dev keeps the **management surface** (per-cog routing + alias suggest panels) |
| `/aliases` | **dev** | A contributor/dev suggest-→-PR tool, not user marketing (optionally surfaced read-only on the bot site later) |
| `/settings` | **dev** | Admin/dev settings *reference* (keys + specs). Not user-marketing; stays dev |
| `/access` | **dev** | Visibility/authority map — dev/admin education |
| `/ideas` | **dev** | Idea backlog — repo/dev content |
| `/bugs` | **dev** | The **bug book** (existing issues) is dev/repo. The bot site gets a *new submission form*, **not** the bug book |
| `/reviews` | **dev** | Owner review inbox — owner/agent channel |
| `/updates` | **both (split by run-type)** | dev keeps the full `.sessions/` **repo/session updates** feed; bot gets a curated **bot changelog** (see below) |
| `/env` | **dev** | Env-usage map (names only) — dev/owner; never user-facing |
| `/healthz` | **both** | Each Railway service needs its own liveness probe |
| `/me`, `/admin/*`, `/auth/*` (control panel) | **bot (gated zone)** | Per-guild editors; OAuth + bot-authority-gated. **Decided (Q-0179, 2026-06-19): the control panel's home is the bot site** — per-server management is a bot-USER feature. Realized as a gated "manage my server" surface **isolated** from the secret-free public marketing pages (§2.4 / §4.4); the migration slice is gated on the control-API public-exposure security review (§3), and the existing dev-site panel keeps serving until it ships (no gap). |

**New bot-site pages** (none exist yet; all read the public data subset + the new sources):

| New page | What | Source |
|---|---|---|
| `/` | Marketing router-landing: hero, feature bands per category, "Add the bot" CTA, live trust band | `site.json` (subset) + live status widget (§3) |
| `/commands` | Read-only command reference (search + filters), the user's "what can it do?" | `site.json.commands` |
| `/features` | Feature showcase (the `/functions` + `/games` catalogues, user-framed) | `site.json.catalogue` |
| `/changelog` | **Bot changelog** — user-facing "what's new in the bot" | curated source (§3) |
| `/status` | User trust band (online · build · uptime) | live status widget (§3) |
| `/submit` (a.k.a. `/feedback`) | **Public bug/suggestion form** → DB intake (moderation-gated, never auto-shown) | writes the submissions DB (§2.3) |
| `/healthz` | Liveness probe | app constant |

**The "bot updates vs repo updates" split (brief deliverable 1 explicit ask).** The brief points at the
**Run-type seam** — `export_dashboard_data.py` already tags each `/updates` entry with `run_type`
(`routine`/`manual`) and `self_initiated` (Q-0165/Q-0172). But that seam classifies *how a session ran*,
not *whether a change is user-relevant* — every `.sessions/` log is dev/repo content. So:

- **Repo/session updates** (dev `/updates`): the existing `.sessions/` feed stays as-is on the dev site.
- **Bot changelog** (bot `/changelog`): a **new curated, user-facing source** — recommended
  `docs/bot-changelog.md` (one entry per user-visible bot change: new command, new game, a fix users
  feel). The export script parses it into `site.json.bot_changelog`. The run-type seam is a useful
  *seed/filter* (a user changelog should never surface a routine docs-reconciliation pass), but a
  curated source is the honest answer — auto-deriving a user changelog from session logs would leak
  dev-internal noise. *(Exact source = open decision §7.5; recommendation: curated file, seeded from the
  substantive `manual` + shipped items.)*

---

## Site identity & experience — the owner's vision (2026-06-19, binding brief)

> Owner-directed; this is the **binding product brief** for the bot site's pages — the fan-out (S1.1, P2,
> P3, …) builds to it. The tone/branding *wording* is the owner's to refine; the **positioning + behaviour
> below are the build spec.**

**Positioning — all-in-one, stated boldly.** SuperBot's pitch is that it *replaces the stack*: the goal is
that **every function any Discord bot offers is present here, and better.** The hero one-liner is the
owner's: **"Add SuperBot and you can remove every other bot from your server."**

**Feel.** Fun **but** professional. Simple, self-explanatory, **easily browsable** — a visitor finds what
they need in seconds, never hunts. Clear explanations over cleverness.

**Interactive command reference (the core UX ask).** Every command on `/commands` (and surfaced through
`/features`) is **clickable → a detail view**, not a static table row. The detail shows:
- what it does + **use-cases**, its **aliases**, cooldown, required **permissions**, examples;
- **notes/comments** left on it (ours or the community's);
- a **status badge — `finished` vs `in-progress`** — so users instantly see how mature a feature is;
- **linked ideas/plans** for that command/cog — so "what's coming" is discoverable right where the command
  lives.

**Discoverability through the repo's own data.** Same source-of-truth principle the whole split rests on:
the site doesn't invent a parallel catalogue — it **projects the repo's real commands ↔ aliases ↔ ideas ↔
status, linked by cog/command**, into a safe, user-facing, *navigable* shape. An idea that matches a
subsystem surfaces on that subsystem's commands; an open idea/bug on a command flips its status to
`in-progress`. Users browse the bot the way we see it — minus anything dev-internal or unsafe (the
redaction lens still applies, §4; the data-contract extension that feeds this is unit **S1.1** in §5).

**Proof, honestly.** Lead with real breadth — the honest catalogue counts (N commands · M features ·
K games), never fabricated server/user totals (§3).

## 2. Architecture  *(deliverable 2)*

### 2.1 Topology — 2 Railway services (Q-0178)

```
                      ┌─────────────────────────────────────────────┐
   Public internet ──▶│  BOT SITE  (new Railway service, root botsite/) │  public, no secrets except
                      │  FastAPI+Jinja2+Tailwind · marketing/reference  │  the INSERT-only submissions DSN
                      │  reads botsite/data/site.json (public subset)   │
                      │  /submit → INSERT pending row ──────────────┐   │
                      └─────────────────────────────────────────────┼───┘
                                                                     ▼
                                              ┌──────────────────────────────┐
                                              │  SUBMISSIONS DB (dashboard-   │  separate from the bot's
                                              │  owned Postgres; NOT the bot's)│  Postgres → preserves decoupling
                                              └──────────────────────────────┘
                                                                     ▲ read + moderate
                      ┌─────────────────────────────────────────────┼───┐
   Public internet ──▶│  DEV SITE  (current Railway service dashboard/)  │
                      │  all read pages PUBLIC read-only                 │
   Discord OAuth   ──▶│  /admin/* editors OWNER/admin-gated (unchanged)  │
                      │  /admin/moderation → approve → GitHub issue ─────┼──▶ GitHub issues
                      │  control panel ──(private net, CONTROL_API_TOKEN)┼──▶ bot worker control API
                      └─────────────────────────────────────────────────┘
```

> **Q-0179 update (decided 2026-06-19): the per-server control panel moves to the bot-site side** as a
> gated surface **isolated** from the public marketing pages (see §2.4, §4.4, §7.4). The diagram above
> shows the *pre-decision* placement (panel on the dev site); the secret-isolation invariant and the
> security-review prerequisite are in §4.4 / §7.4. The dev site retains submission moderation + the GitHub
> mirror + the owner-only ring (env-value mgmt, control board).

- **Dev site = the *current* `dashboard/` service, untouched in its deploy shape** (root dir
  `dashboard/`, same Procfile, same auto-redeploy). We only **add** (moderation page, public-subset
  emission). This is what makes rollout no-downtime (§6).
- **Bot site = a *new* lightweight service**, new root dir **`botsite/`** (its own
  `requirements.txt` + `Procfile`, mirroring the proven `dashboard/` deploy recipe — incl. the
  **no-`static/`-dir** gotcha). Separate Railway service, separate domain.

### 2.2 Shared factoring — one producer, independent presentation, a lint guard

The brief asks how shared templates/assets/data are factored "without re-coupling." Decision, with the
trade-off stated:

**Chosen: a shared *data artifact* (single producer) + *independent* presentation per site + a CI
guard.** Rejected: a shared Python package imported by both services.

*Why not a shared package?* Railway scopes each service's build to its **root directory** (that is
exactly what installs `dashboard/requirements.txt` and not the bot's — README/#970). A package outside
both roots is not on either service's runtime path without abandoning the simple, proven root-directory
deploy (and risking the bot-deps trap). The two sites also *should* look different (marketing vs
engine-room), so "shared templates" is mostly a non-problem — the real shared thing is the **data**.

**The factoring, concretely:**

1. **One data producer stays canonical.** `scripts/export_dashboard_data.py` remains the *only* generator.
   Extend it to emit **two** artifacts from the same in-memory build:
   - `dashboard/data/dashboard.json` — the **full** payload (unchanged; dev site).
   - `botsite/data/site.json` — a **minimized public subset**: an explicit *whitelist* of user-safe
     families only (`meta.build`, a slim `catalogue`, `commands` reference fields, `bot_changelog`,
     public `counts`). It **omits** `env_usage`, `settings`, `access`, `reviews`, `ideas`, raw `bugs`,
     and any internal field. This is **redaction by construction** — a file that *physically cannot*
     contain a secret or a dev-only family is the strongest guarantee for non-negotiable #1.
2. **A CI guard enforces the subset is safe + fresh.** Extend the existing
   `scripts/check_generated_artifacts_fresh.py` / `check_dashboard_data.py` family with a
   `site.json` entry: assert it is regenerable-identical (freshness) **and** that its top-level keys are
   a subset of the allowed whitelist (a new key in the producer can't silently leak a private family).
3. **Independent presentation, no shared import.** Each site owns its `templates/` and a ~25-line
   `base.html`. If visual parity is wanted, a tiny **template-parity lint** can assert the two
   `base.html` chrome blocks stay in sync — but the recommendation is **independent by design** (they
   serve different audiences). The data subset is the only required coupling.

### 2.3 Submission flow — end-to-end (Q-0178 decision 2)

> **DB intake → owner approves on the dev site → approved ones mirror to GitHub issues.** Moderation
> gate *before* anything is publicly shown or mirrored (non-negotiable #3). Submissions are **never**
> shown publicly on the bot site — they go straight to a `pending` queue only the owner sees.

**DB schema** (a `submissions` table in the **dashboard-owned** Postgres — *not* the bot's DB; §7.3):

| column | type | note |
|---|---|---|
| `id` | bigserial PK | |
| `kind` | text | `bug` \| `suggestion` (maps to the `.github/ISSUE_TEMPLATE/` shape) |
| `title` | text | length-capped, server-trimmed |
| `body` | text | length-capped; stored as plain text, rendered escaped |
| `surface` | text | from the bug template dropdown (bot / dashboard / CI / other) |
| `contact` | text null | optional, never required, never published |
| `status` | text | `pending` (default) → `approved` \| `rejected` |
| `submitted_at` | timestamptz | `now()` |
| `source_ip_hash` | text | salted hash for rate-limit/abuse forensics — **never the raw IP** |
| `moderated_by` | text null | owner Discord id at decision time |
| `github_issue_url` | text null | set when mirrored |

**Flow:**
1. **Bot site `/submit`** (public, no login): validated form → on success `INSERT … status='pending'`.
   Rate-limited + validated + honeypot-gated (§4.2). The user sees a "thanks, queued for review"
   confirmation — **no public listing**.
2. **Dev site `/admin/moderation`** (owner-gated): lists `pending` rows; the owner **approves** or
   **rejects** each. CSRF + rate-limit reuse the existing `dashboard/` machinery.
3. **On approve**, the dev site calls the **GitHub mirror** (§4.3): create one issue in
   `menno420/superbot` using the matching `.github/ISSUE_TEMPLATE/` body shape (labels `bug` /
   `enhancement`), store `github_issue_url`, flip `status='approved'`. Reject just flips status.

**Why this division is safe:** the **public** service only ever *writes* `pending` rows (least-privilege
DB role, §4.4) and never holds the GitHub token. The **GitHub token + the mirror action live only on
the owner-gated dev site**, behind the moderation gate. Nothing the public submits reaches GitHub or any
public page without an explicit owner approval.

### 2.4 Auth boundaries

| Surface | Auth | Notes |
|---|---|---|
| Bot site — all pages | **none (public)** | Read-only marketing/reference; the only write is `/submit` → `pending` intake (no login, abuse-gated §4.2) |
| Dev site — read pages | **none (public read-only)** | The existing value-free catalogues; the redaction audit (§4.1) certifies each |
| `/admin/*` editors (→ bot-site gated manager) | **Discord OAuth + bot-side live authority** | Per-guild edits gated by the bot's live-member capability check. **Q-0179: relocating to the bot-site gated manager** (§7.4), isolated from the public marketing pages; unchanged until that slice ships. The **owner-only** ring (global-settings + env-value + control-board) stays on the dev site (the stricter ring) |
| Dev site — `/admin/moderation` | **owner-gated** | New. Same OAuth, restricted to `config.BOT_OWNER_USER_ID` (mirrors the existing global-settings owner gate) |

**Resolved wording mismatch (Q-0179, decided 2026-06-19):** Q-0178 said the dev site is "owner-gated for
edits (existing Discord-OAuth owner auth)", but today's `/admin` is a **multi-user, any-guild-admin**
control panel (the bot re-checks each editor's authority per guild), *not* owner-only. The owner resolved
the fork: **the per-server panel is a bot-USER feature → its home is the bot site** (§7.4). It moves as a
gated surface **isolated** from the public marketing pages, keeping the multi-user, bot-is-the-authority
model; the migration is gated on the control-API public-exposure security review and the existing dev-site
panel serves until it ships (no gap). The **owner-only** gate (the stricter ring) applies to **submission
moderation + env-value mgmt + control board**, which stay on the dev site.

---

## 3. Data / freshness design  *(deliverable 3)*

The bot site is **hybrid**: mostly regenerated, a few live widgets — exactly the vision's freshness model.

**Regenerated (committed generated artifacts, the fast/simple path):**

| Family | Source | Cadence / trigger |
|---|---|---|
| `site.json` catalogue + command reference | repo via `export_dashboard_data.py` (same scanners as today) | regenerated + committed on source change; auto-redeploys on merge to `main`; the docs-reconciliation routine re-runs it (existing) |
| `site.json.bot_changelog` | curated `docs/bot-changelog.md` (§1) | same export run |
| `meta.build` (deployed commit/subject/date) | `git` meta in the export (`_git_meta`) | each export |

**The "few live widgets" (the dynamic half):** a **status/trust band** (is the bot online · uptime ·
deployed build). The only *live* truth source is the bot — and that is exactly where the security gate
bites:

- **Hard rule:** the **public** bot site must **never** read the bot's **private control API** directly.
  The control API is private-network-only, token-gated, the owner's "don't rush" zone — exposing it to a
  public service (or copying its token there) violates the whole security model.
- **v1 source (DECIDED §7.2 — generated build-meta):** the status/trust band renders the **generated**
  `meta.build` (online-as-of-last-deploy · build SHA/date), honestly labelled "as of last deploy" — **no
  live claim**. This is the v1 path: zero new secrets, zero control-API exposure, ships in the first wave.
- **Post-review follow-up (NOT v1 — the live aggregator):** *later, and only after the control-API
  public-exposure security review (§7.2)*, the **dev site** may become the trusted status aggregator — poll
  the bot's `/control/ping` on the private network (iff the owner enables the control token there),
  **redact to a tiny non-sensitive shape** (`{online: bool, build_sha, checked_at}` — *no* guild data, *no*
  counts that reveal private info), cache it, and expose it as a **public, rate-limited, read-only**
  `/status.json` that the bot site fetches. The public bot site still **never** touches the private control
  API — it reads the dev site's redacted `/status.json`. This is a deferred slice, not a v1 dependency.

**Freshness labelling (vision's freshness contract — applied to the public site too):** every widget
declares its lineage with one of two honest badges — **"generated"** (commit/export-time) or
**"live"** (runtime-backed, with the aggregator's `checked_at`). No widget ever silently implies
real-time when it is generated. Optional `ETag`/`stale-while-revalidate` on the read responses improves
perf without faking realtime.

---

## 4. Security review  *(deliverable 4)*

### 4.1 Per-page redaction matrix — the public read-only dev site

The brief makes a **redaction audit of every dev-site page** a required deliverable. Result (verified
against the current templates + routes):

| Dev page | Renders | Secret-value risk | Verdict |
|---|---|---|---|
| `/` `/functions` `/games` | counts, subsystem catalogue metadata | none (declared metadata only) | ✅ public-safe |
| `/status` | inventory counts, build SHA/subject, bug/access health summary | none | ✅ public-safe (build SHA is already public on GitHub) |
| `/commands` | command names/types/aliases, cog-routing *defaults* | none (no per-guild values) | ✅ public-safe |
| `/aliases` | command/alias/synonym tokens | none | ✅ public-safe |
| `/settings` | setting **keys** + typed `SettingSpec` metadata (type/default/hint/choices) | **names + metadata only, never a stored value** | ✅ public-safe (confirm `default` is the *spec* default, not a live value — it is) |
| `/access` | visibility-tier ladder | none (visibility, not execution) | ✅ public-safe |
| `/ideas` `/bugs` `/reviews` `/updates` | markdown-derived docs indexes | none (already-public docs) | ✅ public-safe |
| `/env` | env-var **names** + code file:line + required/optional/layer | **🔒 names + locations only — never a value; never opens `.env`** | ✅ public-safe *by design* (this is the redaction line) |
| `/me`, `/admin/*` | one server's **live** settings values, help text, routing | **per-guild private config** | ⛔ **NOT public** — stays OAuth + bot-authority-gated (this is the "owner-gated for edits" zone) |
| `/admin/moderation` (new) | raw public submissions (may contain anything) | **unmoderated user input** | ⛔ **owner-gated** — never public |
| env-value mgmt / control board (future owner zone) | secret **values** (via Railway) | **🔒 secrets** | ⛔ **owner-only**, never reachable from public side |

**The crisp redaction boundary:** *public read-only = the repo-level **generated** catalogues
(value-free by construction); anything per-guild, any env **value**, any submission, any control-action
stays behind the OAuth/owner gate.* The §2.2 `site.json` whitelist enforces this *physically* for the
bot site; the dev site enforces it *by route auth* for the gated surfaces. A CI assertion that the public
`site.json` keys ⊆ the whitelist is the standing guard against future leakage.

### 4.2 Public-submission abuse plan (non-negotiable #3)

The `/submit` form is public + no-login → an abuse vector. Layered defenses, all **before** anything is
stored-visibly or mirrored:

1. **Nothing is auto-public.** Submissions land `status='pending'`; the bot site never lists them. The
   *only* exposure path is owner approval (§2.3) — this alone defeats spam-as-publication.
2. **Rate-limit** (reuse `ratelimit.py`'s stdlib sliding window): per-IP cap on `/submit` (e.g. a few
   per minute, a couple dozen per hour). Store a **salted IP hash** only, for forensic dedup — never the
   raw IP.
3. **Validation + sanitation:** required `kind`/`title`/`body`; server-side length caps; reject empty /
   control-character payloads; store as plain text and render **escaped** in moderation (no HTML/markdown
   injection into the owner's view or the mirrored issue).
4. **Honeypot field** (a hidden input real users never fill) → silently drop bots. Cheap, no dependency.
5. **Optional captcha** (Cloudflare Turnstile / hCaptcha) as a fast-follow **iff** honeypot+rate-limit
   prove insufficient — kept an open lever (§7.6), not a v1 dependency (avoids a third-party JS/secret on
   the public site until needed).
6. **Mirror is owner-gated + idempotent:** only an approved row creates an issue; the moderation action
   is CSRF-protected and writes `github_issue_url` so a double-click can't double-file.

### 4.3 GitHub-mirror token scope (least privilege)

- A **fine-grained Personal Access Token**, scoped to **only** `menno420/superbot`, with the **single**
  permission **Issues: Read & write** — nothing else (no code, no actions, no metadata-write).
- Stored **only** in the **dev site's** Railway env (e.g. `GITHUB_ISSUE_MIRROR_TOKEN`); **never** on the
  public bot site, never in the repo, never in `site.json`. Surfaced by **name** on `/env` once it exists.
- The mirror call runs **server-side on approval** (owner-gated route) — the token never reaches a
  browser or the public service.
- Issues are created with the existing `.github/ISSUE_TEMPLATE/` body shapes + labels (`bug` /
  `enhancement`), so triage/automation downstream is unchanged.

### 4.4 Per-service secret-holding matrix (defense-in-depth: minimize what each service can leak)

| Secret | Bot site (public) | Dev site (gated) | Bot worker |
|---|---|---|---|
| `CONTROL_API_TOKEN` | ❌ never | ✅ (control panel + optional status aggregator) | ✅ |
| `GITHUB_ISSUE_MIRROR_TOKEN` | ❌ never | ✅ (mirror on approve) | ❌ |
| `DISCORD_OAUTH_*` / `DASHBOARD_SESSION_SECRET` | ❌ (no login) | ✅ | ❌ |
| Submissions DB DSN | ✅ **INSERT-only role** | ✅ full (read/moderate) | ❌ |
| Bot's Postgres DSN | ❌ never | ❌ never (decoupling) | ✅ |

The public service holds exactly **one** secret — an **INSERT-only** DB role on **one** table. A full
compromise of the bot site cannot read submissions, cannot reach GitHub, cannot reach the bot, cannot
touch the bot's DB. That is the security payoff of the split done this way.

**Q-0179 redistribution (decided 2026-06-19 — control panel → bot site).** Moving the per-server panel to
the bot side does **not** dissolve this payoff — it relocates it. The bot-site *domain* now fronts **two
surfaces that must be isolated at the process + secret-scope level**: the **public marketing pages** (still
holding only the INSERT-only submissions DSN — the table column above is unchanged for them) and a
**gated "manage my server" manager** that holds `DISCORD_OAUTH_*` / session-secret + `CONTROL_API_TOKEN`.

**The isolation boundary must be a *separate service*, not a same-process router (explicit decision).** A
router mounted inside the public marketing app would share that app's runtime process and environment —
so a marketing-surface compromise *would* reach `CONTROL_API_TOKEN`, **defeating the invariant**. Therefore
the gated manager is its **own Railway service** (own process, own env/secret scope, own deploy), reachable
under the bot-site domain (e.g. a `manage.` host or a path routed to that service at the edge) but **never
sharing a process with the marketing pages**. The invariant holds verbatim — *the **public marketing
surface** holds exactly one secret (the INSERT-only DSN)* — because the only thing holding the OAuth/control
secrets is the separate manager service.

**Topology consequence (updates Q-0178's "2 Railway services").** This slice makes it **3 services**:
(1) the public marketing bot site, (2) the gated manager service, (3) the dev site. That growth is the
cost of the owner's "move the panel to the bot site" choice done securely. *Two alternatives if 3 services
is unwanted:* keep the per-server panel on the **dev site** (the original agent recommendation — strictly 2
services, the audience split is slightly less clean), or accept a **same-process router** on the bot site
(2 services, but the marketing surface and the control token then share a process — the weaker boundary
above). The **secure default recorded here is the separate manager service**; owner can pick an alternative.

The **dev site** keeps `GITHUB_ISSUE_MIRROR_TOKEN` + the moderation gate + the owner-only ring. This whole
migration is **gated on the control-API public-exposure security review** (§3, §7.2 / §7.4) — exposing a
control-API-writing editor on a user-facing surface is precisely what that review covers — so it lands as a
security-reviewed slice *after* the first additive build wave (which stays 2 services, secret-free public).

---

## 5. Decomposition into file-disjoint build units  *(deliverable 5)*

Sequenced **serial foundation → parallel back half**. Each unit lists its **exclusive file set**; the
parallel units share **no** file, so a fleet builds them with no write conflicts. **Tightened
2026-06-19 pre-ultracode** to make that literally true: the earlier draft let three "parallel" units edit
`botsite/app.py` (P1/P2/P4) and two edit `export_dashboard_data.py` (S1/P3), with "decide at build / or
fold" hedges a parallel fleet can't resolve. Those overlaps are folded into single owners below, and the
remaining either/ors (S2's module shape, the rate-limiter, the whitelist keys) are pinned.

**Build-without-live-infra (so no unit blocks on provisioning).** Every unit builds **code + tests only**,
against a **test DB** (S2's schema on a throwaway/test Postgres or SQLite) and a **mocked GitHub** (P6) —
exactly the `importorskip`/mock pattern the existing `dashboard/` suite uses. No unit needs the real
Railway service, the real Postgres, or any token; the owner provisions those at **rollout** (§6).

> **▶ Status (2026-06-19): the serial foundation S1 + S2 + P1 is MERGED (#1109).** The remaining work is
> the back half — now **reshaped by the Site identity & experience brief above**: a new unit **S1.1**
> enriches the per-command data the interactive browser needs, and **P2** becomes that browser (not a
> static table). The rest (P3–P8) is unchanged. New dependency: **S1.1 → P2**.

### Serial foundation (✅ MERGED #1109) — original spec retained for reference

- **S1 — the data producer, end to end (sole owner of `export_dashboard_data.py`).**
  Files: `scripts/export_dashboard_data.py` (the `site.json` subset emitter + `--targets` **+ the
  `bot_changelog` parse**, folded in here so no other unit touches the producer), `docs/bot-changelog.md`
  (seed the curated source), `botsite/data/site.json` (generated + committed),
  `scripts/check_generated_artifacts_fresh.py` (+ `check_dashboard_data.py`) registering `site.json` with
  the **key-whitelist** assertion, `tests/unit/scripts/test_export_dashboard_data.py`.
  **Whitelist — the exact allowed top-level `site.json` keys (the redaction guarantee, fails closed on a
  new key):** `meta` (build sha/subject/date only), `counts` (catalogue counts only —
  commands/features/games; **never** server/user totals), `catalogue` (subsystem + game
  name/description/category/badges), `commands` (name/aliases/category/cooldown/permissions/usage — no
  per-guild values), `bot_changelog`. **Omits** `env_usage`, `settings`, `access`, `reviews`, `ideas`, raw
  `bugs`, and anything not listed.
- **S2 — submissions store: one schema, two independent access helpers (no shared package — §2.2).**
  Files: one committed **DDL/migration** for the `submissions` table (§2.3); `botsite/submissions_db.py`
  (a single `insert_pending(...)`, **INSERT-only**); `dashboard/submissions_db.py`
  (`list_pending()` / `set_status()` / `attach_issue_url()`, SELECT+UPDATE); tests for each. The two
  helpers **share only the table contract (the DDL), not code** — that is what keeps the services
  decoupled. *(Store = separate dashboard Postgres, §7.3.)*
- **P1 — bot-site app + ALL routes (sole owner of `botsite/app.py`).**
  Files: `botsite/__init__.py`, `botsite/app.py`, `botsite/Procfile`, `botsite/requirements.txt`,
  `botsite/data_loader.py` (load/validate `site.json`), `botsite/templates/base.html`,
  `botsite/templates/index.html`, `botsite/submit.py` (an **empty stub `APIRouter`** so the app boots —
  P4 owns its real content), `botsite/README.md`, `tests/unit/botsite/test_app.py`. **`app.py` wires every
  route up front** — `/`, `/commands`, `/features`, `/changelog`, `/status`, `/healthz` (each renders its
  template *by filename*; the templates land in P2/P3) and `/submit` (via
  `app.include_router(submit_router)`). This single-owner `app.py` is what makes the back half disjoint —
  **no other unit edits `app.py`.** *(Honor the no-`static/` gotcha.)*

### Parallel back half (truly file-disjoint — fan out once S1 + S2 + P1 land)

- **S1.1 — enrich the public command data (extends the merged S1 producer + whitelist; P2 depends on it).**
  Exclusive: `scripts/export_dashboard_data.py` (the `build_site_subset` command projection),
  `scripts/check_dashboard_data.py` (extend `check_site_subset`'s per-command whitelist — still
  **fail-closed**), `botsite/data/site.json` (regenerate), `tests/unit/scripts/` (extend). Adds, **per
  command, only safe/curated fields** — never fabricated, redaction lens still applies:
  - `description` / `use_cases` / `examples` — from the help catalogue + command docstrings (already
    scanned); emit `null`, not invented prose, where absent.
  - `status` — **`finished` | `in-progress`**, an honest maturity signal. *Recommended derivation:* a
    command is `in-progress` if its cog/subsystem has a **linked open idea or open bug**, else `finished`;
    a curated override can come later. *(Source = open decision — recommend this; flag for owner.)*
  - `linked_ideas` — ideas mapped to the command's **cog/subsystem** (the subsystem registry already maps
    cog→subsystem), surfaced as user-facing "what's planned" teasers — **title + status only, never raw
    internal idea text** (redaction). *(Linking method = open decision — recommend explicit subsystem tag,
    heuristic name-match as fallback.)*
  - `notes` — curated per-command notes (ours/community). *(Source = open decision — recommend v1 reuse the
    help-overlay re-describe text; a dedicated community-notes source is a fast-follow, not invented.)*
- **P2 — interactive command + feature browser (the owner-vision core; depends on S1.1).** Exclusive:
  `botsite/templates/commands.html`, `botsite/templates/features.html`, `botsite/templates/_command_detail.html`
  (the detail partial). Renders the **enriched** `site.json` as **clickable command cards → a detail view**
  (use-cases · aliases · permissions · examples · **notes** · **status badge** · **linked ideas**), with
  fast client-side search/filter so nothing takes long to find; progressive-enhancement JS inline (honor
  the no-`static/` gotcha). `/features` groups the same data by category — the all-in-one showcase. Reads
  `site.json`; rendered by P1's already-wired routes; **no `app.py` edit.**
- **P3 — changelog + status templates.** Exclusive: `botsite/templates/changelog.html`,
  `botsite/templates/status.html` + the "generated vs live" freshness badges. Reads `site.json.bot_changelog`
  + `meta.build` (both produced by S1). Templates only — no `app.py`, no producer edit.
- **P4 — submission intake module.** Exclusive: `botsite/submit.py` (the `/submit` `APIRouter` + honeypot +
  validation + INSERT via S2's `botsite/submissions_db.py` — fills in P1's stub), `botsite/ratelimit.py`
  (**copy** the proven stdlib limiter — no shared import, §2.2), `botsite/templates/submit.html`,
  `tests/unit/botsite/test_submit.py`.
- **P5 — dev-site moderation UI.** Exclusive: `dashboard/templates/moderation.html`, the
  `/admin/moderation` route + approve/reject handlers in `dashboard/app.py`, owner-gate helper,
  `tests/unit/dashboard/test_moderation.py`. Lists `pending`, approve/reject, CSRF-protected; uses S2's
  `dashboard/submissions_db.py` + P6's mirror.
- **P6 — GitHub-mirror mechanism.** Exclusive: `dashboard/github_mirror.py` (least-privilege issue-create
  client + template-shape mapping) + its test. Called by P5 on approve; built/tested against a stub first.
- **P7 — redaction audit record.** Exclusive: `docs/operations/dashboard-redaction-audit.md` (the §4.1
  matrix as a living checklist). Docs only — no `dashboard/app.py` or shared-template edits (those belong
  to P5), so it can't collide.
- **P8 — deploy + env docs.** Exclusive: `docs/operations/botsite-deploy.md` (new — the 2nd-service deploy
  recipe + Railway setup), `docs/operations/env-vars.md` (+ the new env names: `GITHUB_ISSUE_MIRROR_TOKEN`,
  the submissions DSN, optional captcha keys), `dashboard/README.md` (moderation note). *(P1 owns
  `botsite/README.md`; P8 does not touch it.)*

**Dependency graph (updated 2026-06-19):** the foundation `S1 → {S2, P1}` is **merged (#1109)**. Remaining:
`S1.1 → P2` (the browser needs the enriched data) runs as its own short serial pair; `{P3, P4, P6, P7, P8}`
fan out fully in parallel alongside it; P4 fills P1's `submit.py` stub + uses S2's INSERT helper, P5 uses
S2's read helper + P6 (P6 stub-buildable first). S1.1 is the only producer-touching unit, so it never
collides with the template/module units. No two concurrently-running units share a file.

---

## 6. Migration / rollout — no downtime + rollback  *(deliverable 6)*

The split is **additive**, which is what makes it safe:

1. **The dev site never stops serving.** It *is* the current live dashboard. S1 (subset emission), P5/P6
   (moderation+mirror), P7/P8 (docs) only **add** to it — no existing route changes behaviour. Each lands
   green on `main` and auto-redeploys as today.
2. **Stand the bot site up alongside, dark.** Provision the **new** Railway service (root dir `botsite/`)
   once P1 lands. It serves on its Railway-generated URL first — **no public domain, no announcement** —
   so it's verifiable in production without being "the website" yet.
3. **Provision the submissions DB** (S2) and wire env vars per the §4.4 matrix (owner step). Intake (P4)
   and moderation (P5) light up only when their env is set — same **dormant-by-default** discipline the
   control API already uses.
4. **Cut over deliberately:** when the bot site is complete + reviewed, point the **marketing domain** at
   it and link it from the dev site / Discord. The dev site keeps its existing domain (e.g.
   `superbot-dashboard.up.railway.app`) for the owner+agents.
5. **Rollback** at every step: the bot site is a separate service → if it misbehaves, **delete/pause the
   service or revert DNS**; the dev site is wholly unaffected. The submissions DB is additive → drop the
   table to fully unwind intake. Each dev-site PR is independently revertible (no coupled migrations on
   the bot's DB — decoupling guarantees this).

---

## 7. Decisions — resolved 2026-06-19  *(deliverable 7)*

All six were resolved by the owner on **2026-06-19** (via the question panel, against the recommendations
each carried). They are cross-checked against the owner-provided external research (ChatGPT, 2026-06-19),
which independently reached the same recommendation on five of six and endorsed this whole approach as its
recommended "strong audience split with separate domains" (rejecting a unified single-site and an
API-first/heavy-JS rebuild). The build run executes the **Decided** lines below, not the recommendations.

1. **Domains / branding — DECIDED: deferred.** No domain yet; the build stands both services up on their
   **Railway-generated URLs**, and the owner sets DNS/branding at cutover (non-blocking — §6 already
   dark-launches the bot site on its Railway URL). When chosen, the sites get **separate** domains
   (subdomain `bot.`/`dev.` *or* apex-for-bot + `dev.` subdomain — owner's call; the research leans
   subdomains). **Owner owns the domain purchase/DNS.**
2. **Exact live-widget data source — DECIDED: generated build-meta for v1.** The status/trust band renders
   the **generated** build/uptime meta, honestly labelled "as of last deploy." The **live** dev-site
   aggregator (redacted, cached, public `/status.json`) is a **fast-follow deferred behind the control-API
   public-exposure security review** — the public bot site **never** touches the private control API. (This
   is the §3 fallback chosen as the v1 default; it matches the research's "generated snapshot first.")
3. **Submissions DB store — DECIDED: a separate, dashboard-owned Postgres.** Submissions aren't bot-domain
   data; a separate store preserves the bot-decoupling rule and lets the public service hold an
   **INSERT-only** role on one table. (Owner provisions it on Railway at build time.)
4. **Per-server control-panel placement — DECIDED: → the bot site (Q-0179, option 2).** Per-server
   management is a bot-**USER** feature, so the control panel's home is the bot site (not the dev
   engine-room). Realized as a **gated "manage my server" surface isolated from the secret-free public
   marketing pages** (§2.4 / §4.4), keeping the multi-user, bot-is-the-authority model. **Gated on the
   control-API public-exposure security review** (§3) → it lands as a security-reviewed slice *after* the
   first additive build wave; the existing dev-site panel keeps serving until then (no gap). *(The agent
   recommendation had been "leave on dev for v1"; the owner picked the audience-clean move. If the owner
   instead wants a single merged app rather than an isolated manager, that supersedes the isolation
   realization.)*
5. **Bot-changelog source — DECIDED: a curated `docs/bot-changelog.md`**, seeded from the substantive
   shipped/`manual` items. Auto-deriving from session updates via the run-type seam leaks dev-internal
   noise into a user surface (the seam classifies *how a session ran*, not user-relevance — §1).
6. **Captcha for `/submit` — DECIDED: honeypot + rate-limit for v1** (no third-party JS/secret on the
   public site); add a captcha (Turnstile/hCaptcha) only if abuse appears. The moderation gate already
   prevents spam-as-publication, and the research notes honeypot+rate-limit blocks ~99.5% of automated
   spam.

## Layout & UX guidance — folded from the owner's external research (2026-06-19)

Concrete page-level defaults for the build run, from the owner-provided research (ChatGPT, 2026-06-19),
treated as **input verified against this plan** (Q-0120), not as orders. They fill the layout detail the
architecture sections deliberately left open; the build run may refine them.

- **Bot-site navigation.** Top bar: logo left, primary links right (*Features · Commands · Games ·
  Changelog · Status · Submit*) + a **persistent "Add to Discord" CTA** styled distinctively. Mobile:
  collapse to a hamburger + a fixed "Add" button; a small status dot (green/amber/red) in the header links
  to `/status`. **Dev site keeps its existing sidebar** (engine-room framing).
- **Homepage structure.** Hero (headline + one-line benefit + "Add to Discord") → **3–5 feature cards**
  (icon · benefit · deep link, grouped by category: Games · Moderation · AI · BTD6 tools) → a **capability
  band** built from the **honest catalogue counts** `site.json` actually exposes (e.g. "N commands across
  M features / K games") → a 3-step "how it works" (Invite → Configure → Enjoy) → a repeat CTA.
  Marketing-first (the research's pick; matches the plan's "marketing router-landing"). **Note (do not
  fake social proof):** `site.json` holds repo/catalogue counts, **not** live server/user totals — those
  would need the deferred live source (§3, post-security-review), so v1 must **not** render
  server/user numbers; use the catalogue counts or omit the band until a reviewed live source exists.
- **Command reference (`/commands`).** A **filterable table** (command · description · cooldown ·
  permissions · category) with a search box, category accordions, and a sticky header; on mobile, stacked
  cards. Anchor links per command.
- **Feature showcase (`/features`).** Category tabs/accordion over the `/functions` + `/games` catalogues,
  user-framed; per-feature card (icon · name · short benefit · optional badge like *beta* · deep link).
  *(This already merges the dev `/functions` + `/games` into one user-facing page — the research's
  "important improvement #1", which the plan adopted in §1.)*
- **Changelog (`/changelog`).** A timeline grouped by date; each entry tagged feature/fix/improvement;
  link out to the GitHub release/PR — but **don't surface raw internal PR numbers as user-facing
  identifiers**.
- **Submission form (`/submit`).** Fields: *category* (bug/suggestion) · *title* · *description* (rendered
  escaped) · ***surface*** (the §2.3 schema field — bot / dashboard / CI / other — that maps to the
  issue-template dropdown; shown for bugs, stored nullable for suggestions) · optional *contact*; a hidden
  **honeypot** + server-side validation (§4.2); friendly copy that submissions are reviewed and not all
  suggestions ship, plus a one-line privacy note; redirect to a thank-you page on success. *(The form's
  fields must cover every non-defaulted `submissions` column in §2.3 so the GitHub mirror can populate the
  template — `surface` is the one the earlier draft omitted.)*
- **Cross-cutting.** Friendly **empty/error states** (no internal error text leaked); **freshness badges**
  ("generated" vs "live", §3) on every data widget; an **accurate privacy note** — the public site reads no
  Discord/guild personal data, and the **only** data it collects is what you submit on `/submit`: your
  optional *contact* (never published) and a **salted IP hash** kept for abuse prevention (§4.2). Do **not**
  claim "no personal data is collected" (the contact + IP-hash flow is pseudonymous personal data); state
  the retention/abuse purpose plainly instead.

---

## 8. Verification / acceptance

- `python3.10 scripts/export_dashboard_data.py` regenerates **both** artifacts; the freshness+whitelist
  guard is green; `python3.10 -m pytest tests/unit/scripts/test_export_dashboard_data.py` passes.
- Bot site smoke (local, `importorskip`-guarded like the dashboard suite):
  `pip install -r botsite/requirements.txt && python3.10 -m pytest tests/unit/botsite/`.
- The redaction CI assertion: `site.json` top-level keys ⊆ the whitelist (fails closed on a new private
  family).
- Submission round-trip (local, against a test DB): `/submit` writes `pending`; `/admin/moderation`
  approve creates a stub issue (mocked GitHub) + stores the URL; reject flips status; no public listing
  exists.
- `check_architecture --mode strict` + `check_quality --check-only` green; **neither web service imports
  `disbot/`** (preserve decoupling).

## 9. Builds on / references (don't duplicate)

- [`website-two-site-split-planning-brief-2026-06-19.md`](website-two-site-split-planning-brief-2026-06-19.md)
  — the brief this plan executes; router **Q-0178** — the owner decisions.
- [`developer-dashboard-plan.md`](developer-dashboard-plan.md) — the current dashboard's design + the
  already-envisioned public bug form + GitHub-issue mirror (Phase 2).
- [`dashboard-live-editor-plan.md`](dashboard-live-editor-plan.md) — owner-auth + control-API write design.
- [`dashboard-vision-finalized-state.md`](dashboard-vision-finalized-state.md) — the four-zone north star
  this split realises (Public → bot site; Personal/Server/Owner → dev site).
- [`web-tier-centralization-proposal-2026-06-19.md`](web-tier-centralization-proposal-2026-06-19.md) — the
  `web-ci.yml` matrix (dashboard + botsite) + PR-machinery de-duplication (owner centralization mandate).
- `dashboard/` (the decoupled service), `scripts/export_dashboard_data.py` (the single data producer),
  `disbot/control_api.py` (the private, owner-paced live source), `.github/ISSUE_TEMPLATE/` (the mirror
  shapes, #1064), `docs/operations/env-vars.md` (the env-name surface).
