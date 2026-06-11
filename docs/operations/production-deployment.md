# Production deployment — Railway

> **Status:** `living-ledger` — operational facts about where production runs and how code
> reaches it. Facts verified 2026-06-10 (the build-outage session, PR #685).
> Maintainer owns the Railway dashboard; agents have **no** Railway access — changes
> land repo-side (this doc, `.python-version`, `Procfile`) or via the maintainer.

## Where production runs

- **Platform:** [Railway](https://railway.com) — project `reliable-grace`, environment
  `production`, two services:
  - **`worker`** — the bot, built from this GitHub repo.
  - **`Postgres`** — Railway-native Postgres with a `postgres-volume` for data.
- **Runtime secrets** (Discord token, `DATABASE_URL`, AI provider keys, …) live in
  Railway **service variables**, not in the repo.

## How code reaches production

- The Railway GitHub integration **auto-builds and deploys `worker` on every push to
  `main`** — each merge commit shows up as a deployment ("Merge pull request #NNN …
  via GitHub" in the dashboard).
- **Consequence for Q-0084 merge autonomy:** an agent merging a green session PR
  *is* triggering a production deploy — that has always been true for the
  maintainer's merges too. "Merge ≠ deploy" in the grant means **restarts, prod
  verification, rollbacks, and live eval walks stay the maintainer's**, not that
  merges don't reach prod.
- **Builder:** [railpack](https://railpack.com) (v0.27.x at write time). It detects
  Python + pip, creates `/app/.venv`, runs `pip install -r requirements.txt`, and
  starts the `worker` command from the **`Procfile`**: `python disbot/bot1.py`.

## Python version — pinned, and why

- **The pin: `.python-version` (repo root) = `3.13.13`.** Railpack reads
  mise-compatible version files and installs that exact interpreter from
  precompiled [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
  (pbs) binaries.
- **Why pinned:** with no pin, railpack floats on its default (`3.13` → *latest*
  patch). On 2026-06-10 that resolved to CPython **3.13.14**, released upstream
  *after* pbs's latest binary release (`20260602`) — no precompiled binary for
  `x86_64-unknown-linux-gnu` existed, and every build failed at `mise install`
  (`mise ERROR … no precompiled python found`). A known Railway failure class (the
  same race hit other users on 3.13.11). A floating version re-runs this race on
  every CPython patch release; a pinned one never does.
- **Precedence:** a `RAILPACK_PYTHON_VERSION` service variable would override the
  file — keep it **unset** so the repo stays the single source of truth.
- **Bump procedure** (deliberate, never automatic):
  1. Pick the target patch and verify a pbs binary exists for Railway's platform:
     ```
     curl -s -o /dev/null -w "%{http_code}" -I -L \
       "https://github.com/astral-sh/python-build-standalone/releases/download/<TAG>/cpython-<VER>+<TAG>-x86_64-unknown-linux-gnu-install_only.tar.gz"
     ```
     (`<TAG>` from [latest-release.json](https://raw.githubusercontent.com/astral-sh/python-build-standalone/latest-release/latest-release.json);
     expect `200`.)
  2. Change `.python-version`, merge, and watch the Railway build log: the Packages
     table must read `python │ <VER> │ .python-version` (not `railpack default`).
- **Known drift (open question Q-0085):** CI and local tooling run **Python 3.10**
  (pinned in the workflows and every `python3.10 -m` rule); production runs
  **3.13** and always has (the unpinned default predates this doc). Alignment
  direction is an owner decision —
  [`owner/maintainer-question-router.md`](../owner/maintainer-question-router.md) §36.

## Backups — OPEN

**No automated backup/restore posture exists yet** (as of 2026-06-10). Bot data
lives on the Railway `postgres-volume`. Designing the posture (Railway-side
snapshots vs. offsite `pg_dump`, retention, restore drill) is an open discussion
with the maintainer — when decided, this section becomes its home.

## Incident log

- **2026-06-10 — worker build outage (~21:00–21:45 UTC).** Three consecutive build
  failures (the #681 and #680 merge deploys + a manual retry): railpack default
  resolved to binary-less CPython 3.13.14 (see "Why pinned" above).
  **Impact (owner-corrected 2026-06-11): no user-facing downtime** — Railway
  keeps the active deployment serving until a new build goes live, so the
  previous instance ran throughout; Postgres Online throughout. The real
  impact was a **silent ship-blocker**: no new code could reach production
  until the pin landed. Fix: the `.python-version` pin, PR #685, merged the
  same hour. Diagnosis artifacts: the maintainer's uploaded build log; pbs
  asset probes (3.13.13 → 200, 3.13.14 → 404).
