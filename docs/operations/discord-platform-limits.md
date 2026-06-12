# Discord platform limits — technical reference

> **Status:** `reference` — distilled from official Discord documentation and community
> testing, as surfaced in the owner-uploaded research (2026-06-12).
> Read this before designing any Discord UI component, image-generation feature,
> or attachment-handling pipeline. Source: Discord developer docs, the
> discord.py library, and verified community testing (cited per fact below).
> **These limits change without notice** — re-verify against the official Discord
> Developer Portal before shipping anything that depends on specific numbers.

---

## 1. Message components (Buttons, Select menus, Action rows)

| Limit | Value | Notes |
|---|---|---|
| Action rows per message | **5** | Legacy (`discord.ui.View`) messages |
| Buttons per action row | **5** | Buttons only; select menus use the full row |
| Select menus per action row | **1** | Each menu occupies an entire row |
| Total components per message | **25** | **Legacy `View` ceiling** (5 rows × 5); Components V2 has its own 40 budget — see below |
| Button label length | **80 characters** | |
| Button custom\_id length | **100 characters** | Used for persistent-view routing |
| String-select options | **2 – 25** | Min 2, max 25 options per menu |
| Select option label length | **100 characters** | |
| Select option value length | **100 characters** | |
| Select option description length | **100 characters** | |
| Select placeholder text | **150 characters** | |

**Components V2** *(corrected 2026-06-12 — this section previously claimed a
25-component budget; verified against the installed discord.py 2.7.1 source)*:
requires the `IS_COMPONENTS_V2` flag on the message (discord.py sets it when sending a
`discord.ui.LayoutView`) and is a different message shape with its own budgets:

| CV2 limit | Value | Source |
|---|---|---|
| Total components (nested count) | **40** | `LayoutView` raises `ValueError('maximum number of children exceeded (40)')` |
| Combined display text across all items | **4 000 characters** | `LayoutView` validation |
| `Section` text displays | ≤3 + one accessory (`Thumbnail` or `Button`) | class docs |
| `MediaGallery` items | ≤10 | class docs |

A CV2 message **replaces** `content`/`embeds` (and disallows polls/stickers); files must
be referenced by a component (`Thumbnail`, `MediaGallery`, `File`). discord.py ≥2.6
exposes the full set: `LayoutView`, `Container` (accent colour, spoiler), `Section`,
`TextDisplay`, `MediaGallery`, `File`, `Separator`. SuperBot's `BaseView`/`HubView`/
`PersistentView` lineage is **legacy-View-based** — CV2 panels need `LayoutView`, a
separate lineage; adopting it for real panels is an ADR-shaped decision (see the
[UX Lab plan](../planning/ux-lab-interface-gallery-plan-2026-06-12.md), whose probe
bench re-verifies this table on demand).

**Modals** *(corrected 2026-06-12)*: since discord.py 2.6, a modal may contain
`discord.ui.Label`-wrapped components — i.e. **selects inside modals are now possible**
(`Label(text=…, component=Select(...))`; label text ≤45 chars, description ≤100).
Older guidance that modals are text-input-only predates the 2.7 pin.

**Pagination implication:** lists longer than 25 items (e.g., a full inventory, a large
role list) require pagination or dynamic loading — a single select menu cannot show them
all.

---

## 2. Embeds and message content

| Limit | Value |
|---|---|
| Embeds per message | **10** |
| Embed title | **256 characters** |
| Embed description | **4 096 characters** |
| Embed fields per embed | **25** |
| Embed field name | **256 characters** |
| Embed field value | **1 024 characters** |
| Embed footer text | **2 048 characters** |
| Embed author name | **256 characters** |
| Embed image/thumbnail URL | **2 048 characters** |
| Total text across all embeds (per message) | **6 000 characters** |
| Message content (outside embeds) | **2 000 characters** (4 000 with Nitro) |

**6 000-character total** is the binding limit when multiple embeds are present —
titles + descriptions + all field names + all field values + footers + author names
combined must not exceed it.

---

## 3. File attachments and image sizes

| Limit | Value | Notes |
|---|---|---|
| Attachments per message | **10** | |
| Max file size — free users | 10 MB | |
| Max file size — Nitro Basic | 50 MB | |
| Max file size — Nitro | 500 MB | |
| Max file size — **bots and webhooks** | **~8 MiB** | The 25 MB user limit does NOT apply; bots receive `413 Payload Too Large` above ~8 MiB |
| Combined attachment size (user API) | 25 MB | Not relevant to bots — use 8 MiB cap |
| Image inline-preview area limit | ~90 million pixels | Community-tested; larger images require download |
| Image inline-preview max dimension | ~64 000 px (either side) | Community-tested |

**The 8 MiB bot limit is the binding constraint** for all image-generation features
(PIL-generated cards, PIL inventory displays, gear paper-doll compositors, etc.).
Use JPEG or WebP export at medium compression — a 1920×1080 JPEG at medium quality
is typically under 1 MB, leaving ample headroom. Avoid raw PNG for large canvases.

**Alt text:** Discord supports alt-text on image attachments. When generating images
programmatically (PIL), supply a concise description string as alt-text metadata to
improve accessibility.

---

## 4. PIL image generation — bot design guide

Derived from the 8 MiB constraint and the standard Pillow workflow.

- **Export format:** JPEG or WebP for photographic/composite images; PNG only for
  pixel-art or images requiring transparency at small sizes.
- **Compression:** `image.save(buf, format='JPEG', quality=85)` typically yields
  <500 KB at 1920×1080. Tune `quality` downward if the image consistently exceeds
  2–3 MB.
- **Canvas sizing:** stay within 3000×3000 px for inline previews. Higher is rarely
  needed and risks hitting the 90 Mp area limit.
- **Font rendering:** Pillow's `ImageDraw.text()` with a TTF font — keep font files
  in `disbot/assets/fonts/`; load once at module import and cache.
- **Avatar compositing (welcome cards):** download the user's avatar URL, open it
  with `Image.open(BytesIO(data))`, resize/crop to a circle with an alpha mask, paste
  onto the template. Handle network failures with a fallback silhouette.
- **Concurrency:** PIL operations are CPU-bound; run inside `asyncio.to_thread()` to
  avoid blocking the event loop.
- **Caching:** leaderboard and profile images that don't change frequently can be
  cached in-memory (keyed by a hash of the data) to avoid redundant re-renders.

---

## 5. YouTube transcript and summarization constraints

When implementing YouTube video summarization (the feed-service extension):

| Constraint | Detail |
|---|---|
| Transcript availability | Not all videos have transcripts; auto-generated ones may be inaccurate |
| Transcript access | YouTube Data API (requires API key) or third-party transcript APIs |
| LLM context window | Long transcripts exceed a single context window → chunk and summarize iteratively |
| API quotas | YouTube Data API has daily quota units; transcript requests count against them |
| AI cost | Each summarization call = tokens → count under the Q-0082 spend ceiling |
| Language | Auto-generated transcripts are often in the video's primary language; verify before sending to an LLM |

**Recommended pipeline:** fetch transcript → split into ≤N-token chunks → summarize each
chunk → merge summaries with a final consolidation call → post to Discord as an embed.
The owner confirmed YouTube-first posture (Q-0041); implement and meter before expanding.

---

## 6. Image moderation — provider comparison

For the proposed image moderation service (`docs/ideas/server-safety-and-automod-2026-06-12.md` §3):

| Provider | Cost | Image size limit | Categories | Notes |
|---|---|---|---|---|
| OpenAI omni-moderation-latest | **Free** | 20 MB | Sexual, harassment, violence, hate, self-harm | Accepts text + images in the same request; returns per-category confidence scores |
| API4AI NSFW Recognition | Affordable paid | Not published | SFW / NSFW (binary + confidence) | Demo endpoint available; production requires a token |
| Hive Moderation | Higher cost, no free tier | Not published | **50+ categories** (nudity, violence, drugs, weapons, hate symbols, …) | Enterprise-grade; per-category threshold tuning; no self-hosted option |

**Recommendation for SuperBot:** start with OpenAI (free, already integrated in the AI cog,
20 MB covers the 8 MiB bot attachment limit). Gate Hive behind a premium-server option
if a richer category set is wanted later.
