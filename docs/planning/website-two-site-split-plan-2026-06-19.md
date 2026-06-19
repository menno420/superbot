# Website two-site split — implementation plan + ultracode decomposition

> **Status:** `plan` — the implementation plan executing the **brief**
> ([`website-two-site-split-planning-brief-2026-06-19.md`](website-two-site-split-planning-brief-2026-06-19.md))
> and the owner decisions in router **Q-0178**. Owner-directed 2026-06-19. Source code + merged PRs win
> over this document. The next step after this plan is an **ultracode build run** on the disjoint
> back-half units in §5.
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
| `/me`, `/admin/*`, `/auth/*` (control panel) | **dev (v1)** | Per-guild editors; OAuth + bot-authority-gated. *(Open decision §7.4: a per-server control panel is arguably a bot-USER feature — but it is already built + audited on the dev site, so v1 leaves it there with zero migration.)* |

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
| Dev site — `/admin/*` editors | **Discord OAuth + bot-side live authority** | Unchanged. Per-guild edits gated by the bot's live-member capability check; the global-settings + env-value + control-board surfaces are **owner-gated** (the stricter ring) |
| Dev site — `/admin/moderation` | **owner-gated** | New. Same OAuth, restricted to `config.BOT_OWNER_USER_ID` (mirrors the existing global-settings owner gate) |

**Surfacing a wording mismatch (don't guess — §7.4):** Q-0178 says the dev site is "owner-gated for
edits (existing Discord-OAuth owner auth)", but today's `/admin` is a **multi-user, any-guild-admin**
control panel (the bot re-checks each editor's authority per guild), *not* owner-only. v1 keeps that
existing, audited multi-user panel (the bot is the authority either way); the **new** owner-only gate
applies to **moderation + env-value mgmt + control board**. Whether the per-server panel should instead
become a bot-site *user* feature is §7.4.

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
- **Recommended live-widget source:** the **dev site becomes the trusted status aggregator.** It can
  (optionally, if the owner enables the control token there) poll the bot's `/control/ping` on the
  private network, **redact to a tiny non-sensitive shape** (`{online: bool, build_sha, checked_at}` —
  *no* guild data, *no* counts that reveal private info), cache it, and expose it as a **public,
  rate-limited, read-only** `/status.json`. The bot site fetches *that* (or falls back to its generated
  `meta.build` + a "last generated" label when the aggregator is unavailable).
- **Fallback (no control token anywhere):** the bot site shows the **generated** build/trust band only,
  honestly labelled "as of last deploy" — no live claim. *Exact live source = open decision §7.2,
  gated on the control-API public-exposure security review the brief calls for.*

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

---

## 5. Decomposition into file-disjoint build units  *(deliverable 5)*

Sequenced **serial foundation → parallel back half**. Each unit lists its **exclusive file set** so the
parallel units are ultracode-able with no write conflicts. (The brief's reason for plan-first: the front
half is serial; only after it can the back half fan out.)

### Serial foundation (must land first — everything downstream depends on it)

- **S1 — public data subset + freshness/whitelist guard.**
  Files: `scripts/export_dashboard_data.py` (add the `site.json` subset emitter; add `--targets`),
  `botsite/data/site.json` (generated, committed), `scripts/check_generated_artifacts_fresh.py` (+
  `check_dashboard_data.py`) register `site.json` with a key-whitelist assertion, `tests/unit/scripts/…`.
  *Why serial:* every bot-site page reads `site.json`; the whitelist is the redaction guarantee.
- **S2 — submissions DB schema + access contract.**
  Files: a new `dashboard_db/` (or `botsite/db.py` + `dashboard/db_submissions.py` sharing only the DDL)
  with the `submissions` DDL/migration + a tiny stdlib-ish access layer (INSERT for the bot site, SELECT
  /UPDATE for the dev site), tests. *Why serial:* both the intake (P3) and moderation (P5) units bind to
  this schema. *(DB choice = §7.3; recommend a separate dashboard Postgres.)*

### Parallel back half (file-disjoint — ultracode-able together once S1+S2 land)

- **P1 — bot-site skeleton.** Exclusive: `botsite/__init__.py`, `botsite/app.py`, `botsite/Procfile`,
  `botsite/requirements.txt`, `botsite/templates/base.html`, `botsite/templates/index.html` (landing),
  `botsite/README.md`, `tests/unit/botsite/`. The new service that boots, serves `/` + `/healthz`,
  reads `site.json`. *(Honor the no-`static/` gotcha.)*
- **P2 — bot-site reference pages.** Exclusive: `botsite/templates/commands.html`,
  `botsite/templates/features.html`, the routes for them in `botsite/app.py` *(if P1 lands a thin app
  shell first, P2 adds routes in a disjoint region; otherwise fold P1+P2)*. Read-only command reference +
  feature showcase from `site.json`.
- **P3 — bot-site changelog + status widget.** Exclusive: `botsite/templates/changelog.html`,
  `botsite/templates/status.html`, `docs/bot-changelog.md` (the curated source), the changelog parse in
  `export_dashboard_data.py`'s subset *(coordinate the one shared producer line with S1 — or fold the
  changelog parse into S1)*. The "generated vs live" freshness badges.
- **P4 — bot-site submission form (intake).** Exclusive: `botsite/templates/submit.html`, the `/submit`
  route + intake logic in `botsite/app.py`, `botsite/ratelimit.py` (copy the proven stdlib limiter) or a
  shared import, honeypot + validation, tests. Writes `pending` rows via S2's INSERT path.
- **P5 — dev-site moderation UI.** Exclusive: `dashboard/templates/moderation.html`, the
  `/admin/moderation` route + approve/reject handlers in `dashboard/app.py`, owner-gate helper,
  `tests/unit/dashboard/test_moderation.py`. Lists `pending`, approve/reject, CSRF-protected.
- **P6 — GitHub-mirror mechanism.** Exclusive: `dashboard/github_mirror.py` (the least-privilege
  issue-create client, template-shape mapping) + its test. Called by P5 on approve. *(Disjoint module so
  it can be built/tested against a stub independently of P5's UI.)*
- **P7 — dev-site public-read posture + redaction audit record.** Exclusive: a short
  `docs/operations/dashboard-redaction-audit.md` (the §4.1 matrix as a living checklist) + any small
  route/nav copy tweaks confirming the public-read framing + the freshness badges on the dev read pages.
- **P8 — deploy + env docs.** Exclusive: `botsite/README.md` deploy recipe (2nd-service-style),
  `dashboard/README.md` moderation note, `docs/operations/env-vars.md` (+ the new env names:
  `GITHUB_ISSUE_MIRROR_TOKEN`, the submissions DSN, optional captcha keys), Railway setup notes.

**Dependency graph:** `S1 → {P1, P2, P3}` · `S2 → {P4, P5}` · `P5 → P6` (P6 buildable in isolation
against a stub first) · `{P1…P8}` otherwise parallel. The ultracode run takes S1+S2 serial, then fans
out P1–P8 (P2/P3 sequence behind P1 only if P1 lands a shared app shell; otherwise mergeable as one).

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

## 7. Open decisions — surfaced, not guessed  *(deliverable 7)*

Each carries a **recommendation** so the build run has a default if the owner doesn't weigh in, per the
"approving a goal approves the path" rule — but these are the genuine forks.

1. **Domains / branding.** Bot site (e.g. `superbot.<tld>` / `getsuperbot.<tld>`) vs dev site (keep
   `superbot-dashboard.up.railway.app` or `dev.superbot.<tld>`). *Recommendation:* a clean apex/marketing
   domain for the bot site; keep the existing Railway domain for the dev site v1. **Owner owns the domain
   purchase/DNS.**
2. **Exact live-widget data source** (gated on the control-API public-exposure security review the brief
   requires). *Recommendation:* **dev-site-aggregated, redacted, cached, public `/status.json`** — the
   public bot site **never** touches the private control API. Fallback to generated build-meta when the
   aggregator/token is absent. **Do not expose the control API publicly.**
3. **Submissions DB store** — the bot's Postgres vs a separate one. *Recommendation:* a **separate,
   dashboard-owned Postgres** (submissions aren't bot-domain data; a separate store preserves the
   bot-decoupling rule and lets the public service hold an **INSERT-only** role on one table). Sharing the
   bot's DB would either re-couple the web tier to the bot's DB or force every write through a new bot
   control-API endpoint for non-bot data — both worse.
4. **Per-server control-panel placement** (the Q-0178 "owner-gated" wording vs today's multi-user
   guild-admin panel). *Recommendation:* **leave the existing audited multi-user control panel on the dev
   site for v1** (zero migration, the bot is the authority regardless); make **moderation + env-value +
   control board** the new owner-only surfaces. Revisit moving/mirroring the per-server panel to the bot
   site as a bot-user feature later. **This is the one place the owner's words and the current build
   differ — confirm the intent.**
5. **Bot-changelog source** — a curated `docs/bot-changelog.md` vs auto-derived from session updates via
   the run-type seam. *Recommendation:* **curated file**, seeded from the substantive shipped/`manual`
   items; auto-derivation leaks dev-internal noise into a user surface.
6. **Captcha for `/submit`** — honeypot+rate-limit only (v1) vs add Turnstile/hCaptcha now.
   *Recommendation:* **honeypot + rate-limit for v1** (no third-party JS/secret on the public site);
   add a captcha only if abuse appears. (The moderation gate already prevents spam-as-publication.)

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
- `dashboard/` (the decoupled service), `scripts/export_dashboard_data.py` (the single data producer),
  `disbot/control_api.py` (the private, owner-paced live source), `.github/ISSUE_TEMPLATE/` (the mirror
  shapes, #1064), `docs/operations/env-vars.md` (the env-name surface).
