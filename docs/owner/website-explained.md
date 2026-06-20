<!-- badge: owner-guidance -->
# The website, explained (plain language)

> **Status:** `owner-guidance` — a learning/orientation doc for the maintainer.
> Plain-English explanation of how SuperBot's public website works and how to
> keep working on it (incl. Claude Design). Source code wins over this doc.

This page exists because the website has a few moving parts that are easy to
confuse. It's written for someone who is comfortable directing the work but is
still learning the web/design vocabulary.

---

## The core idea: two ways to build a web page

A web page is just **HTML** (the content + structure a browser shows). The only
real question is *who assembles that HTML, and when?* There are two answers, and
this repo contains both.

### 1. Server-rendered (the "Jinja" way)

The **server** builds the finished HTML *before* sending it to the browser. The
browser receives a complete, ready-to-show page.

- **Jinja** is a *templating language* — an HTML file with fill-in-the-blanks
  (`Hello {{ name }}`). The server plugs in real values and out comes plain HTML.
- In this repo: `botsite/templates/commands.html` is a Jinja template. Visiting
  `/commands` makes `botsite/app.py` load the data, fill the template, and ship a
  finished page.
- **Analogy:** a restaurant kitchen cooks the whole meal and brings out a plate.
- **Trade-off:** every click is a new request and a full page reload — simple and
  robust, but feels less "appy."

### 2. SPA — Single-Page Application (the Claude-Design site)

The server sends **one mostly-empty HTML shell + JavaScript, once.** After that,
**JavaScript running in the browser** draws each page and swaps content without
reloading.

- "Single-page" = the browser loads one real HTML file (`index.html`); everything
  after is JavaScript redrawing the screen.
- In this repo: `botsite/site/` is the SPA. `index.html` is nearly empty
  (`<main id="app"></main>`); `app.js` fills that `<main>` depending on the page.
- **Analogy:** a food truck hands you a chef once, who re-plates different dishes
  instantly without you walking back to the counter.
- **Trade-off:** snappier and modern; but the first load is "empty until the
  JavaScript runs," and it needs that JavaScript to work.

**Today the SPA is the live public site** (served at `/`). The Jinja pages remain
in the repo as a working fallback.

---

## Vocabulary that comes up around the SPA

- **Hash routing (`/#/commands`).** The part after `#` is **never sent to the
  server** — the server only ever sees `/`, hands over the SPA, and the
  JavaScript reads `#/commands` to decide what to draw. That's how a single-page
  app fakes many "pages" without bothering the server, and why `app.py` only needs
  to serve the SPA at `/`.
- **`window.SBDATA`.** `window` is the browser's global scratchpad. `data.js`
  dumps all the bot's data (commands, games, …) onto `window.SBDATA`, and `app.js`
  reads from it. It's just "the one bucket of data the app reads."
- **No build step.** The Claude-Design SPA is *plain* JavaScript — the browser
  runs it directly, no compile needed (that's why "just open `index.html`" works).
  The `design-system/` folder, by contrast, is React and *does* need building.
- **Static vs dynamic data.** *Static* = a frozen file (`botsite/site/data.js`,
  committed). *Dynamic* = generated when requested (the `/data.js` route, built
  fresh from the latest data each time). The live site serves the dynamic version;
  the committed file is a fallback so the prototype still works opened on its own.

---

## The data pipeline (the most important part)

The bot is the **single source of truth**. Data flows one way and is never typed
twice, so the site can't silently drift out of date:

```
disbot/                              ← the bot's actual code (source of truth)
  │  scripts/export_dashboard_data.py reads the bot and writes ↓
  ▼
botsite/data/site.json               ← a clean, PUBLIC, safe summary of the bot
  │  botsite/site_data.py reshapes it into the SPA's shape ↓
  ▼
window.SBDATA  →  served live at /data.js   (+ committed botsite/site/data.js fallback)
  │
  ▼
the SPA (app.js) reads it and draws every page
```

To update the site's content you **do not touch the website** — you change the
bot, re-run the export, and the data flows through automatically.

- **JSON** (`site.json`) is a universal plain-text data format both Python and
  JavaScript read natively — that's why it's the hand-off point between the bot
  (Python) and the site (JavaScript).
- **Safety:** `botsite/` **never imports the bot's code** and only reads the
  *public* `site.json`. Even a fully-compromised public site cannot reach the bot,
  its database, or any secret. That's why `site_data.py` lives inside `botsite/`
  and never touches `disbot/`.

---

## The three web things in the repo (easy to confuse)

| Folder | What it is | Who sees it | Tech |
|---|---|---|---|
| `botsite/` | **Public marketing/reference site** (the main one) | Everyone | FastAPI + the SPA |
| `dashboard/` | **Private developer dashboard** (full internal data) | Owner/admins | FastAPI + Jinja |
| `design-system/` | **Reusable UI building blocks** (React), viewable in Storybook | Designers/devs | React + build step |

---

## Working with Claude Design

There are **two separate things**, and only one of them is automatic:

1. **The component library (`design-system/`)** is what Claude Design *builds
   with*. Claude Design connects to the repo via the **GitHub connector** and
   reads this library directly, so **merging component changes to the connected
   branch (main) is the "sync."** You don't upload anything; at most you hit a
   "refresh/re-read repo" action in Claude Design.

2. **Getting a design onto the live site is NOT automatic.** Claude Design
   *produces* a design composed from your components; turning that into what
   visitors see still needs a **Claude Code step** to port it into `botsite/`.
   Claude Design designs the UI — it does not deploy it.

3. **Data is a third, separate thing** — it comes from the bot via the pipeline
   above. Claude Design never touches data, so you never "arrange" data there.

**So the loop is:**

```
edit on the Claude Design canvas  →  hand the result to Claude Code (or say what changed)
        →  Claude Code ports it into botsite/ and opens a PR  →  data stays automatic
```

The one concrete thing to *set* in Claude Design is the **"Add to Discord"
button**: in the shipped SPA it is still a placeholder (`href="#/"`). The
design-handoff rule is *do not hand-edit `index.html`/`app.js`/`app.css`* — so
fix it in Claude Design (or add an `install_url` field the SPA reads, which keeps
it data-driven).

> **Open decision (worth your call):** the `design-system/` README still describes
> the loop as *"production stays Jinja; port designs back into the Jinja
> templates."* But the live front-end is now the **SPA**. Those two stories
> disagree. Nothing is broken, but at some point decide whether the design-system
> library should feed the **SPA** going forward (and retire the Jinja port step).

---

## Supporting cast (terms you'll keep seeing)

- **FastAPI** — the Python web framework running `botsite`. Each `@app.get("/x")`
  is a **route** / **endpoint**: "when someone visits this URL, run this function."
- **API** — a way for programs (not humans) to talk to each other. `/data.js` and
  `/healthz` are tiny APIs.
- **Railway** — the host that runs `botsite` on the internet; it redeploys
  automatically when code merges to `main`. The bot, dashboard, and public site
  each run as separate Railway services.
- **CI / GitHub Actions** — robots that run the tests + linters on every PR.
  `botsite-tests` and `code-quality` are CI checks; green = safe to merge.
- **Linter / formatter (ruff, black)** — tools that enforce consistent code style.
  "FAILED: black" just means "not formatted the standard way," not "broken."
- **Auto-merge** — once CI is green, GitHub merges the PR by itself (we don't merge
  by hand; we make CI green).
- **PR (Pull Request)** — a proposed bundle of changes, reviewed + tested before
  it joins the main code.

---

## Try it locally (the fastest way to make this concrete)

```bash
pip install -r botsite/requirements.txt
python3.10 scripts/export_dashboard_data.py --targets site   # regenerate site.json + data.js
uvicorn botsite.app:app --reload                             # → http://127.0.0.1:8000 (the SPA)
```

Click around. Seeing the SPA draw pages from `/data.js` makes everything above
click into place.
