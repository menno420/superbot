# Voice / Music — architecture-review decision pack (2026-06-20)

> **Status:** `plan` — the **Q-0041-required architecture review**, in decision-pack form.
> **Not implementation approval and not playback code.** Owner steered this session to produce
> *the pack only* (respect the Q-0041 voice gate). Source, binding contracts, and `Q-0041`
> win over this draft. **Subsystem:** media (voice).
>
> **Why this exists:** the research report pitches a full JMusicBot-style player. **Q-0041**
> (2026-06-09) says music is *wanted* but **gated behind a dedicated voice architecture review**,
> itself sequenced **after** the YouTube→Twitch→Spotify alert integrations, with **speech
> recognition last (deferred, not dropped)**. This pack *is* that review — it lays out the
> decisions the owner must make to lift the gate, so a future approved session can build cleanly.
> Companion to [`integrations-media-voice-website-roadmap-2026-06-08.md`](integrations-media-voice-website-roadmap-2026-06-08.md)
> § "Phase 5 — voice concept".

## 1. The decisive constraint, stated first — legal

The report itself documents the history: in **September 2021**, after YouTube enforcement,
**Groovy and Rythm — among the largest Discord bots in existence (Rythm ~560M users / ~20M
servers) — were shut down within weeks**, and **Hydra** survived only by pivoting away from YouTube
music; **Rythm later returned only with official licensing + premium tiers**. The cause was a **ToS**
breach as much as song copyright — YouTube's terms explicitly forbid separating audio from video and
streaming it through unofficial clients, which is exactly what every YouTube-sourced music bot does
(bypassing the ads/Premium that pay rightsholders). The decisive lesson: these bots ran *for years*
while tolerated, and **scale + visibility — not a change in the law — is what triggered enforcement**
(the same publish-safe principle as §1a / the creature-IP decision). Any music feature here lives or
dies on this, so it is the **first** decision, not an afterthought.

**The fork the owner must choose:**

- **(L1) Self-hosted streaming (JMusicBot/Lavaplayer model).** Stream YouTube/SoundCloud/etc.
  directly. *Lowest cost, highest legal exposure* — this is exactly what drew the takedowns. Viable
  only for a private/personal-scale bot the owner accepts the risk for; **not** appropriate for the
  public bot-site launch.
- **(L2) Licensed / API-sanctioned sources only.** Spotify (preview/SDK within ToS), Apple Music
  previews, royalty-free / Creative-Commons catalogues, podcast RSS, direct-upload by server
  owners. *Higher integration effort, defensible legally.* The report's own "make it better"
  recommendation #5 ("partner with services for official API access, use preview APIs to avoid
  DMCA").
- **(L3) Defer indefinitely.** Keep voice out; the bot's identity is community/games/AI, not music.

**Recommendation:** if music ships at all, **L2** for anything public-facing; **L1** only as an
explicitly-private, owner-risk-accepted instance. Decide L1/L2/L3 **before** any infra is built —
it changes every layer below.

### 1a. The L2 compliant-source menu — *how* you stay inside the rules (owner asked directly)

The core principle (shared with the creature-IP decision — **growth/visibility is the enforcement
trigger; publish-safe = a design that does not depend on staying invisible**; see
[creature design+sim](creature-game-design-and-sim-2026-06-20.md) §1): the thing that killed Rythm
wasn't "music," it was **ripping audio from a source whose ToS forbids it** (YouTube). So the whole
game is **sourcing audio from somewhere that actually permits programmatic playback.** The legal
ways:

1. **Royalty-free / Creative-Commons / public-domain catalogs** — YouTube Audio Library, Pixabay
   Music, Free Music Archive, **Jamendo** (real API), ccMixter, Incompetech, public-domain classical.
   Freely streamable → a 100%-safe lofi / ambient / gaming-radio bot. (Not the commercial Top-40 —
   that's the trade.)
2. **Remote-control the user's *own* licensed player (Spotify-Connect pattern)** — Spotify's API
   **won't** stream full tracks, but its **Connect API** lets the bot control playback on the user's
   own Spotify **Premium** client. Their licensed app plays; the bot is a queue / now-playing /
   vote-skip remote. Legal because the bot never touches the audio stream — **and it needs no audio
   path at all** (no FFmpeg, no Lavalink).
3. **Preview clips** — Spotify / Apple Music / Deezer expose legal **30-second previews**.
4. **User-uploaded / self-owned files (jukebox)** — members upload audio *they* hold rights to; the
   bot just plays the file.
5. **Podcasts / public RSS audio** — most feeds publish freely-distributable audio URLs.

**Permanently off-limits (this *is* the Rythm violation):** `yt-dlp`-ripping YouTube/SoundCloud full
tracks into voice; streaming **full commercial tracks** from any source without a streaming license.
**The honest constraint:** there is **no legal way to offer "type any song → hear the full
commercial track, free"** — that exact capability is *inherently* the infringing one, which is why
every bot offering it was killed or had to license (the report's note: **Rythm only returned with
official licensing + premium tiers**).

**Cost-per-lane (ties to §2 infra):**

| Legal model | What users get | Infra / cost |
|---|---|---|
| Royalty-free radio | Lofi/ambient/gaming, full playback | **Low** — lightweight FFmpeg over a fixed catalog; **no per-request extraction node** |
| Spotify-Connect remote | Control their *own* Premium playback | Medium — OAuth; users need Premium; **no audio path** |
| Preview clips | 30s samples | Low |
| File jukebox | Whatever they upload | Low (FFmpeg play of an uploaded file) |

**Sweet spot (agent recommendation, challengeable):** a **royalty-free "lofi/gaming radio"** lane,
optionally **+ Spotify-Connect remote** for users who want their own music — both fully inside the
rules, both **low-cost** (they dodge the Lavalink/per-request-extraction expense that, alongside
legal risk, was the historical bot-killer), and both a clean fit for a community/gaming bot's
identity. This narrows the §6 decision-#2 "legal lane" from an open L1/L2/L3 fork to **"pick a lane
from the menu above."**

## 2. Infrastructure fit (the part the rest of the bot has never needed)

Music is **architecturally unlike** everything in this repo today. The bot is a `discord.py`
text/command + Postgres + EventBus system with **no audio path**. Voice adds:

- **A voice gateway connection + Opus audio pipeline.** `discord.py[voice]`, native **Opus** libs,
  and **FFmpeg** on the host. None are present; FFmpeg is a non-trivial runtime dependency.
- **An audio source/queue engine.** Either an in-process source (FFmpeg/youtube-dl-style
  extractor) or an external **Lavalink** node (the Java audio server most modern bots use to keep
  audio off the bot process). Lavalink = **a second always-on service to host, monitor, and pay
  for** — relevant given the deployment is Railway and the report flags scaling/cost as the
  historical killer (Pokécord/music shutdowns were cost-driven).
- **Persistent voice sessions** — long-lived per-guild connections with their own lifecycle,
  reconnection, and idle-timeout. This does **not** fit the repo's request/response + audited-DB
  mutation model; it is closer to the `core/runtime/tasks` supervised-loop pattern and needs its
  own lifecycle contract in `docs/runtime_contracts.md`.
- **Hosting reality:** voice + FFmpeg + (optionally) a Lavalink node materially raises the
  process/host footprint vs. today's single worker. The owner must accept this cost or scope L2 to
  preview-clip playback that avoids a streaming node.

## 3. Where a music subsystem would land (if greenlit)

Mapped onto the existing architecture so an executor isn't inventing placement later:

| Concern | Home | Notes |
|---|---|---|
| Cog entry / commands | `cogs/music_cog.py` (+ `cogs/music/`) | `!play`/`!queue`/`!skip`/`!np` + slash variants; the report's command set. |
| Voice session lifecycle | `core/runtime/` (new `voice_session_manager`) | Supervised, idle-timeout, reconnect; **must not** import cogs/services. Needs a `runtime_contracts.md` § entry. |
| Queue / playback engine | `services/music_service.py` (or a Lavalink client wrapper) | Pure-ish queue state + source resolution; provider seam mirrors ADR-007 media ownership. |
| Provider adapters | reuse the **ADR-007 media seam** (`youtube_*_service` prior art) | Q-0041 explicitly wants the alert-integration provider contract proven *first* and reused here. |
| UI control panel | `views/music/` (`BaseView`/`PersistentView`) | The report's Rythm-style `/control` button panel — fits the repo's panel model directly. |
| Permissions (DJ role, vote-skip, requester-only-skip) | `governance/` capability + `role` subsystem | No new auth system — reuse capability re-check at callback time (Q-0080). |
| Settings (per-guild prefix already exists; DJ role, allowed channels, default volume) | `utils/settings_keys/music.py` + `SettingsMutationPipeline` | Mirrors the report's admin controls. |
| State that must persist | minimal (saved playlists / autoplaylist) → a migration + `utils/db/music.py` | Live queue state is in-memory; only saved playlists are durable. |

**Key architectural truth:** the *control surface* (panels, DJ permissions, settings, provider
adapters) maps **cleanly** onto what the repo already does well. The *audio transport* (voice
gateway, FFmpeg/Opus/Lavalink, persistent sessions, legal sourcing) is the genuinely new, costly,
risk-bearing part — and it's entirely a function of the §1 legal choice and §2 infra acceptance.

## 4. Privacy — speech recognition stays last

Q-0041 keeps **speech recognition deferred, not dropped**, with its own consent/retention
decision. This pack **excludes** it: voice *input* (listening to users) is the most
privacy-sensitive surface in the whole product and must not ride in on a music-*output* feature.
If ever pursued, it is a separate review (consent, retention, transcript minimization per P0-2).

## 5. Operational cost, scaling, abuse

- **Cost:** an always-on Lavalink node and/or FFmpeg streaming is the dominant new cost; the
  report names cost as the historical bot-killer. L2 preview-clips minimize this; L1 streaming
  maximizes both cost and legal risk.
- **Abuse:** queue hogging, NSFW/illegal source URLs, voice-channel join spam. Mitigations:
  per-requester queue caps + vote-skip (report's lessons), DJ-role gating, source allow-listing,
  and — for any URL ingestion — the same provenance/moderation discipline as ADR-007 media.
- **Degraded-service:** provider outages must fail quiet (Q-0041's "fail-quiet degradation"),
  matching the existing media-seam behavior.

## 6. The decision the owner must make (this feeds Q-0041)

To lift the Q-0041 voice gate, the owner needs to decide, **in order**:

1. **Go / no-go / later** on music at all (vs. keeping the bot's identity games/AI/community).
2. **Legal lane** — L1 self-host (private only, risk-accepted) vs. L2 licensed/preview-only
   (public-safe) vs. L3 defer. *Everything else depends on this.* **§1a narrows L2 to a concrete
   pickable menu** (royalty-free radio · Spotify-Connect remote · previews · file jukebox), with the
   royalty-free-radio + Spotify-remote sweet spot recommended.
3. **Infra acceptance** — willing to host/pay for an audio path (FFmpeg ± Lavalink) on Railway?
4. **Prerequisite ordering** — Q-0041 wants the YouTube/Twitch **alert** provider contract proven
   first; build that before voice, or run voice as an independent track?

**Agent recommendation (challengeable):** **L2 + preview/licensed sources**, control surface built
on the existing panel/governance/settings seams, audio transport scoped to the cheapest viable
path, speech recognition firmly out. If the owner wants L1 self-host, scope it to an explicitly
private instance, never the public bot-site. If neither legal lane is acceptable, **L3 defer** is
the honest answer — and the control-surface work has near-zero standalone value without audio, so
don't pre-build it.

## 7. What this pack deliberately does NOT do

No voice code, no dependency added, no migration, no provider key. It is the review Q-0041 asks
for. Implementation still needs: this decision pack answered → normal promotion → a runtime-verified
session (or an explicitly-private instance) → its own small-PR build.

→ relates [media/voice/website roadmap](integrations-media-voice-website-roadmap-2026-06-08.md) ·
[feature-mapping plan](poketwo-musicbot-feature-mapping-plan-2026-06-20.md) · ADR-007 (media seam)
· Q-0041 (voice gate + provider order) · Q-0042 (website) · Q-0080 (stranger-grade) · P0-2 (data
minimization, for the deferred speech layer).
