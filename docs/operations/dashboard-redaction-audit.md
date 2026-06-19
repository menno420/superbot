# Dashboard redaction audit — the public read-only dev site

> **Status:** `audit` — a living, dated certification that **every dev-site page renders
> only public-safe content**. It is the standing record behind the website two-site-split's
> non-negotiable #1 (*the public read surface leaks no secret, no per-guild value, no
> dev-internal data*). Source code + the live templates/routes win over this file — re-verify
> on a page/template change and bump the date.

This audit operationalises the per-page redaction matrix in
[`../planning/website-two-site-split-plan-2026-06-19.md`](../planning/website-two-site-split-plan-2026-06-19.md)
§4.1 as a **checklist you re-run**, not a one-time table. The dev site (the current
`dashboard/` service) makes **all read pages public read-only**; this file certifies each page's
posture so the public-read decision stays auditable as the site grows.

It pairs with the *physical* guard on the public **bot** site: `botsite/data/site.json` is a
**redaction-by-construction** whitelist subset (plan §2.2 / §5 — `meta` · `counts` · `catalogue`
· `commands` · `bot_changelog` only), and `scripts/check_dashboard_data.py` fails closed if a new
top-level key escapes that whitelist. **Two complementary mechanisms:** the bot site is redacted
*by construction* (a file that physically cannot hold a private family); the dev site is redacted
*by route auth* (gated surfaces sit behind OAuth / the owner gate). This audit covers the **dev
site by-route-auth** half — the bot-site whitelist guard is the by-construction half and is
CI-enforced, not re-audited here.

## How to use this checklist

- **When:** re-run on any change to a `dashboard/` route, template, or the data producer
  (`scripts/export_dashboard_data.py`), and on the every-30-PR reconciliation pass.
- **What "verify" means per row:** open the route's template + its data slice and confirm the
  *Renders* column is still exhaustive and the *Secret-value risk* is still `none` (for a ✅ row)
  or still gated (for a ⛔ row). A new field that surfaces a stored value or per-guild config
  flips the verdict and is a release blocker until redacted or gated.
- **The crisp boundary (the one rule the whole audit enforces):** *public read-only = the
  repo-level **generated** catalogues (value-free by construction); anything per-guild, any env
  **value**, any raw submission, any control-action stays behind the OAuth / owner gate.*

## Per-page redaction matrix

**Last audited: 2026-06-19** (verified against `dashboard/app.py` routes + the served templates;
the gated `/admin/moderation` row is the new P5 surface, audited against its plan §2.3 / §4.1 spec
as it lands in the fan-out wave).

| Dev page | Route | Auth | Renders | Secret-value risk | Verdict |
|---|---|---|---|---|---|
| `/` | `GET /` | public | landing — catalogue counts + recent updates | none (declared metadata only) | ✅ public-safe |
| `/functions` | `GET /functions` | public | subsystem catalogue metadata | none (declared metadata only) | ✅ public-safe |
| `/games` | `GET /games` | public | game catalogue metadata | none | ✅ public-safe |
| `/status` | `GET /status` | public | inventory counts, build SHA/subject, bug/access health summary | none — build SHA is already public on GitHub | ✅ public-safe |
| `/commands` | `GET /commands` | public | command names/types/aliases, cog-routing **defaults** | none (no per-guild values) | ✅ public-safe |
| `/aliases` | `GET /aliases` | public | command/alias/synonym tokens (suggest tool) | none | ✅ public-safe |
| `/settings` | `GET /settings` | public | setting **keys** + typed `SettingSpec` metadata (type/default/hint/choices) | **names + metadata only, never a stored value** — confirm `default` is the *spec* default, not a live value (it is) | ✅ public-safe |
| `/access` | `GET /access` | public | visibility-tier ladder (which tier sees which subsystem) | none — visibility, **not** execution | ✅ public-safe |
| `/ideas` | `GET /ideas` | public | `docs/ideas/`-derived index | none (already-public docs) | ✅ public-safe |
| `/bugs` | `GET /bugs` | public | bug-book-derived index + "report a bug" CTA | none (already-public docs) | ✅ public-safe |
| `/reviews` | `GET /reviews` | public | owner-review-inbox markdown index | none (already-public docs) | ✅ public-safe |
| `/updates` | `GET /updates` | public | `.sessions/`-derived updates feed | none (already-public docs) | ✅ public-safe |
| `/env` | `GET /env` | public | env-var **names** + code `file:line` + required/optional/layer | **🔒 names + locations only — never a value; never opens `.env`** | ✅ public-safe **by design** (this is the redaction line) |
| `/healthz` | `GET /healthz` | public | liveness JSON | none | ✅ public-safe |
| `/me` | `GET /me` | **OAuth** | the signed-in user's admined guilds | per-user identity | ⛔ **NOT public** — OAuth-gated |
| `/admin/*` | `GET/POST /admin/{guild_id}/…` | **OAuth + bot-side live authority** | one server's **live** settings values, help text, routing | **🔒 per-guild private config** | ⛔ **NOT public** — gated (the "owner-gated for edits" zone) |
| `/auth/*` | `GET /auth/{login,callback,logout}` | OAuth handshake | OAuth redirect/callback/logout | OAuth code exchange | ⛔ **NOT a content page** — handshake only |
| `/admin/moderation` (P5, new) | `GET/POST /admin/moderation` | **owner-gated** | raw public submissions (may contain anything) | **🔒 unmoderated user input** | ⛔ **owner-gated** — never public, rendered escaped |
| env-value mgmt / control board (future owner ring) | — | **owner-only** | secret **values** (via Railway) | **🔒 secrets** | ⛔ **owner-only**, never reachable from the public side |

## Why each ✅ row is value-free (the standing rationale)

- **The generated catalogues are value-free by construction.** `/`, `/functions`, `/games`,
  `/commands`, `/aliases`, `/status` all render `scripts/export_dashboard_data.py` output — repo
  **structure** (command/subsystem/game names, types, routing *defaults*, counts), never a stored
  per-guild value. The producer reads source + committed docs, never the bot's DB or `.env`.
- **`/settings` renders the spec, not the state.** It surfaces setting **keys** + their
  `SettingSpec` metadata (type, *spec* default, hint, enum choices). The `default` is the
  declared default in code, not a guild's live value — the live value lives only behind
  `/admin/{guild}` (gated). Re-confirm this each audit: a producer change that reads a *stored*
  default would silently flip this row.
- **`/access` is a visibility map, not an execution grant.** It mirrors
  `disbot/utils/visibility_rules.py` — which tier *can see* which subsystem. No token, no
  per-guild override, no execution authority.
- **`/env` is the redaction line, drawn explicitly.** It is static analysis of the bot source:
  variable **names** + the `file:line` that read them + required/optional/layer. It **never**
  reads, stores, or renders a value, and **never** opens an `.env` file. Railway stays the single
  source of truth for values. This is the page most likely to be mistaken for a secret surface —
  it is safe precisely because it surfaces *names + locations only*. See
  [`env-vars.md`](env-vars.md) (the in-repo form of the same map) and
  [`production-deployment.md`](production-deployment.md) (where the values actually live).

## Why each ⛔ row stays gated (the standing rationale)

- **`/me` + `/admin/*`** render one server's **live** configuration — settings values, help text,
  routing. That is per-guild private data, so the route requires Discord OAuth **and** a per-edit
  bot-side authority re-check (the browser's identity claim is re-verified by the bot on every
  write — see `dashboard/README.md` § Control panel). Opening a panel never authorises a later
  callback.
- **`/admin/moderation` (P5)** lists raw public `/submit` submissions, which may contain
  arbitrary user text. It is **owner-gated** (restricted to `BOT_OWNER_USER_ID`, mirroring the
  existing global-settings owner gate) and renders all stored fields **escaped** so a crafted
  payload cannot inject HTML/markdown into the owner's view or a mirrored issue. Nothing a user
  submits is ever shown publicly — submissions land `status='pending'` and the only exposure path
  is explicit owner approval (plan §2.3 / §4.2).
- **The future owner ring** (env-value management, control board) handles secret **values** via
  the Railway API. It is owner-only and must never be reachable from any public-side route.

## What this audit deliberately does NOT cover

- **The public bot site's `site.json`** — redacted *by construction* (the whitelist subset) and
  guarded by `scripts/check_dashboard_data.py` (CI, fail-closed on a new key). That guard is the
  by-construction half; this file is the dev-site by-route-auth half.
- **Secret-holding per service** — which service may hold which secret is the §4.4 matrix; the
  env-name surface is [`env-vars.md`](env-vars.md) and the deploy/secret-scope recipe is
  [`botsite-deploy.md`](botsite-deploy.md).
- **The control-API public-exposure security review** — the prerequisite gating the per-server
  panel's migration to the bot side (plan §3 / §7.4). That review is a separate, owner-paced
  deliverable; until it lands, the panel stays on the dev site (gated, as audited above).
