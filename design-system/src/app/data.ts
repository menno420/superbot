// Data adapter — maps the live `/site-data.json` payload onto the design-system
// page props. This is the design↔data contract: the page components own the look;
// this file owns turning the public bot data into the props they take. Kept pure
// (the mappers) + a thin async `loadSiteData()` so the mapping is unit-testable
// without a DOM or a network (the PR-1 smoke test feeds a sample here).
//
// Source of truth stays `disbot/ → site.json` (served by botsite's `/site-data.json`).
// This app reads ONLY that public subset — it never imports the bot.

import type { BuildMeta } from "../SiteFooter";
import type { StatusBuild } from "../StatusCard";
import type { LandingPageProps, FeatureCategory } from "../LandingPage";
import type { FeaturesPageProps, FeatureCategoryGroup } from "../FeaturesPage";
import type { CommandsPageProps, CommandCategoryGroup } from "../CommandsPage";
import type { ChangelogPageProps, ChangelogItem } from "../ChangelogPage";
import type { StatusPageProps, StatusCounts } from "../StatusPage";
import type { ChangelogKind } from "../ChangelogEntry";
import type { CommandRecord, PlannedIdea } from "../CommandDetail";
import type { FeatureShowcaseCardProps } from "../FeatureShowcaseCard";

// ── The `/site-data.json` payload shape (mirrors botsite/site_data.build_prototype_data
//    + the meta/counts/addUrl the route folds in). Only the fields the pages consume
//    are typed; unknown extras are ignored. ───────────────────────────────────────
export interface SiteArea {
  id: string;
  name: string;
  icon?: string;
  color?: string;
  title?: string;
  tagline?: string;
  description?: string;
  points?: string[];
}

export interface SiteCommand {
  name: string;
  area: string;
  status?: "finished" | "in-progress";
  summary?: string;
  description?: string;
  usage?: string;
  aliases?: string[];
  permissions?: string;
  cooldown?: string | null;
  examples?: string[];
  planned?: { status: string; title: string }[];
}

export interface SiteGame {
  id: string;
  name: string;
  command?: string;
  tagline?: string;
  description?: string;
  beta?: boolean;
}

export interface SiteChangelogEntry {
  date: string;
  title: string;
  changes?: { type: string; text: string }[];
}

export interface SiteData {
  /** The real "Add to Discord" OAuth URL (from botsite/chrome.ADD_TO_DISCORD_URL). */
  addUrl?: string;
  /** Deployed-build provenance. */
  build?: { commit?: string; committedAt?: string; subject?: string };
  /** Honest catalogue counts (never server/user totals). */
  counts?: { commands: number; features: number; games: number };
  areas?: SiteArea[];
  commands?: SiteCommand[];
  games?: SiteGame[];
  changelog?: SiteChangelogEntry[];
}

/** The hash routes this app serves (mirrors the vanilla SPA's URL scheme). */
export type Route =
  | "home"
  | "features"
  | "commands"
  | "games"
  | "changelog"
  | "status";

const _ROUTES: Route[] = [
  "home",
  "features",
  "commands",
  "games",
  "changelog",
  "status",
];

/**
 * Map a `window.location.hash` to a top-level route. `#/`, `#`, and `""` are home;
 * `#/commands` → commands; detail hashes (`#/command/foo`, `#/feature/bar`,
 * `#/game/baz`) fall back to their parent list; anything unknown is home.
 */
export function routeFromHash(hash: string): Route {
  const path = (hash || "").replace(/^#\/?/, "").split("/")[0].toLowerCase();
  if (!path) return "home";
  if (path === "feature") return "features";
  if (path === "command") return "commands";
  if (path === "game") return "games";
  return (_ROUTES.find((r) => r === path) ?? "home") as Route;
}

// ── Build metadata ────────────────────────────────────────────────────────────
export function toBuildMeta(data: SiteData): BuildMeta | undefined {
  const b = data.build;
  if (!b || !b.commit) return undefined;
  return { commit: b.commit, committedAt: b.committedAt };
}

export function toStatusBuild(data: SiteData): StatusBuild | undefined {
  const b = data.build;
  if (!b || !b.commit) return undefined;
  return { commit: b.commit, committedAt: b.committedAt, subject: b.subject };
}

function counts(data: SiteData): StatusCounts | undefined {
  return data.counts;
}

// ── Per-page mappers (pure) ─────────────────────────────────────────────────────
export function toLandingProps(data: SiteData): LandingPageProps {
  const features: FeatureCategory[] = (data.areas ?? []).map((a) => ({
    category: a.name || a.id,
    items: pickAreaFeatureItems(a, data.commands ?? []),
  }));
  return {
    addUrl: data.addUrl,
    counts: data.counts,
    features: features.length ? features : undefined,
    build: toBuildMeta(data),
  };
}

// The landing "What it does" grid shows a few representative items per area. We use
// the area's `points` (its curated subsystem display names) as the item labels — the
// same data the vanilla SPA's feature cards surface — capped to keep the grid tidy.
function pickAreaFeatureItems(area: SiteArea, _commands: SiteCommand[]) {
  return (area.points ?? []).slice(0, 4).map((name) => ({ name }));
}

export function toFeaturesProps(data: SiteData): FeaturesPageProps {
  return {
    addUrl: data.addUrl,
    groups: buildFeatureGroups(data),
    build: toBuildMeta(data),
  };
}

// The /games view reuses FeaturesPage with only the game-bearing entries — a faithful
// "just the games" slice until a dedicated GamesPage component lands (PR 2+).
export function toGamesProps(data: SiteData): FeaturesPageProps {
  const games: FeatureShowcaseCardProps[] = (data.games ?? []).map((g) => ({
    name: g.name,
    description: g.tagline || g.description,
    isGame: true,
    tags: g.beta ? ["beta"] : undefined,
    commandsHref: g.command ? `#/commands` : undefined,
  }));
  const groups: FeatureCategoryGroup[] = games.length
    ? [{ category: "games", features: games }]
    : [];
  return {
    addUrl: data.addUrl,
    groups: groups.length ? groups : undefined,
    build: toBuildMeta(data),
  };
}

function buildFeatureGroups(data: SiteData): FeatureCategoryGroup[] | undefined {
  const areas = data.areas ?? [];
  const commands = data.commands ?? [];
  const games = new Set((data.games ?? []).map((g) => g.command));
  const groups: FeatureCategoryGroup[] = [];
  for (const area of areas) {
    const inArea = commands.filter((c) => c.area === area.id);
    if (!inArea.length) continue;
    const features: FeatureShowcaseCardProps[] = inArea.map((c) => ({
      name: c.name,
      description: c.summary || c.description,
      tags: c.aliases?.length ? c.aliases.slice(0, 3) : undefined,
      isGame: games.has(c.name),
      commandsHref: `#/command/${c.name}`,
    }));
    groups.push({ category: area.name || area.id, features });
  }
  return groups.length ? groups : undefined;
}

export function toCommandsProps(data: SiteData): CommandsPageProps {
  const areaName = new Map((data.areas ?? []).map((a) => [a.id, a.name || a.id]));
  const byCategory = new Map<string, CommandRecord[]>();
  for (const c of data.commands ?? []) {
    const cat = areaName.get(c.area) || c.area || "other";
    const rec: CommandRecord = {
      name: c.name,
      usage: c.usage || c.summary,
      status: c.status,
      description: c.description || c.summary,
      aliases: c.aliases?.length ? c.aliases : undefined,
      permissions: c.permissions,
      cooldown: c.cooldown ?? undefined,
      examples: c.examples?.length ? c.examples : undefined,
      plannedIdeas: c.planned?.length ? (c.planned as PlannedIdea[]) : undefined,
    };
    const list = byCategory.get(cat) ?? [];
    list.push(rec);
    byCategory.set(cat, list);
  }
  const groups: CommandCategoryGroup[] = [...byCategory.entries()].map(
    ([category, commands]) => ({ category, commands }),
  );
  return {
    addUrl: data.addUrl,
    groups: groups.length ? groups : undefined,
    build: toBuildMeta(data),
  };
}

const _CHANGE_KIND: Record<string, ChangelogKind> = {
  added: "feature",
  improved: "improvement",
  fixed: "fix",
  removed: "update",
};

export function toChangelogProps(data: SiteData): ChangelogPageProps {
  const entries: ChangelogItem[] = (data.changelog ?? []).map((e) => {
    const first = e.changes?.[0];
    const kind: ChangelogKind = first
      ? (_CHANGE_KIND[first.type] ?? "update")
      : "update";
    const summary = (e.changes ?? []).map((c) => c.text).filter(Boolean).join(" ");
    return { date: e.date, kind, title: e.title, summary: summary || undefined };
  });
  return {
    addUrl: data.addUrl,
    entries: entries.length ? entries : undefined,
    build: toBuildMeta(data),
  };
}

export function toStatusProps(data: SiteData): StatusPageProps {
  return {
    addUrl: data.addUrl,
    build: toStatusBuild(data),
    counts: counts(data),
  };
}

// ── Loader ──────────────────────────────────────────────────────────────────────
// Fetches the live public data; on any failure (offline canvas, missing route) it
// falls back to the bundled sample so the app still renders — the pages also carry
// their own sample defaults, so a partial payload degrades gracefully too.
export async function loadSiteData(
  url = "/site-data.json",
  fetchImpl: typeof fetch = fetch,
): Promise<SiteData> {
  try {
    const res = await fetchImpl(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`site-data ${res.status}`);
    return (await res.json()) as SiteData;
  } catch {
    return SAMPLE_SITE_DATA;
  }
}

// A minimal, self-contained sample used as the offline fallback and in the smoke test.
// Mirrors the `/site-data.json` shape; the real payload is far larger.
export const SAMPLE_SITE_DATA: SiteData = {
  addUrl: "https://discord.com/oauth2/authorize?client_id=1403818430758654132",
  build: { commit: "abc1234", committedAt: "2026-06-22T00:00:00Z", subject: "sample" },
  counts: { commands: 372, features: 37, games: 9 },
  areas: [
    {
      id: "games",
      name: "games",
      icon: "gamepad",
      color: "var(--g)",
      title: "Games, ready to play",
      tagline: "Quick, replayable fun.",
      description: "A suite of games members can play right in chat.",
      points: ["Blackjack", "Fishing", "Mining"],
    },
    {
      id: "moderation",
      name: "moderation",
      icon: "shield",
      color: "var(--sky)",
      title: "Keep the peace",
      tagline: "Healthy community without the busywork.",
      description: "Automatic and manual moderation with a full audit trail.",
      points: ["Automod", "Warnings", "Timeouts"],
    },
  ],
  commands: [
    {
      name: "blackjack",
      area: "games",
      status: "finished",
      summary: "Play blackjack against the bot.",
      description: "Start a game of blackjack against the bot.",
      usage: "!blackjack",
      aliases: ["bj"],
      permissions: "anyone",
      cooldown: null,
      examples: ["!blackjack 100"],
      planned: [],
    },
    {
      name: "warn",
      area: "moderation",
      status: "finished",
      summary: "Issue a warning to a member.",
      description: "Issue a warning to a member.",
      usage: "!warn",
      aliases: [],
      permissions: "Moderator",
      cooldown: null,
      examples: ["!warn @user spamming"],
      planned: [],
    },
  ],
  games: [
    {
      id: "blackjack",
      name: "Blackjack",
      command: "blackjack",
      tagline: "Beat the dealer.",
      description: "Card game against the bot.",
    },
  ],
  changelog: [
    {
      date: "Jun 22, 2026",
      title: "Fishing minigame",
      changes: [{ type: "added", text: "A new fishing minigame with a rod ladder." }],
    },
  ],
};
