import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, it, expect } from "vitest";

import {
  SAMPLE_SITE_DATA,
  loadSiteData,
  routeFromHash,
  toLandingProps,
  toFeaturesProps,
  toGamesProps,
  toCommandsProps,
  toChangelogProps,
  toStatusProps,
  type SiteData,
} from "./data";

describe("routeFromHash", () => {
  it("maps the top-level SPA hashes", () => {
    expect(routeFromHash("")).toBe("home");
    expect(routeFromHash("#")).toBe("home");
    expect(routeFromHash("#/")).toBe("home");
    expect(routeFromHash("#/features")).toBe("features");
    expect(routeFromHash("#/commands")).toBe("commands");
    expect(routeFromHash("#/games")).toBe("games");
    expect(routeFromHash("#/changelog")).toBe("changelog");
    expect(routeFromHash("#/status")).toBe("status");
  });

  it("falls a detail hash back to its parent list", () => {
    expect(routeFromHash("#/command/blackjack")).toBe("commands");
    expect(routeFromHash("#/feature/games")).toBe("features");
    expect(routeFromHash("#/game/blackjack")).toBe("games");
  });

  it("falls an unknown hash back to home", () => {
    expect(routeFromHash("#/nonsense")).toBe("home");
  });
});

describe("data adapter — sample → valid page props", () => {
  const data = SAMPLE_SITE_DATA;

  it("threads the real install URL onto every page", () => {
    const url = data.addUrl;
    expect(url).toContain("discord.com/oauth2/authorize");
    expect(toLandingProps(data).addUrl).toBe(url);
    expect(toFeaturesProps(data).addUrl).toBe(url);
    expect(toGamesProps(data).addUrl).toBe(url);
    expect(toCommandsProps(data).addUrl).toBe(url);
    expect(toChangelogProps(data).addUrl).toBe(url);
    expect(toStatusProps(data).addUrl).toBe(url);
  });

  it("maps landing counts + feature categories", () => {
    const p = toLandingProps(data);
    expect(p.counts).toEqual({ commands: 372, features: 37, games: 9 });
    expect(p.features?.map((f) => f.category)).toEqual(["games", "moderation"]);
    expect(p.build?.commit).toBe("abc1234");
  });

  it("groups features by area, marking the game-bearing command", () => {
    const groups = toFeaturesProps(data).groups ?? [];
    const games = groups.find((g) => g.category === "games");
    expect(games?.features.some((f) => f.name === "blackjack" && f.isGame)).toBe(true);
  });

  it("renders the games view from the game catalogue only", () => {
    const groups = toGamesProps(data).groups ?? [];
    expect(groups).toHaveLength(1);
    expect(groups[0].category).toBe("games");
    expect(groups[0].features.every((f) => f.isGame)).toBe(true);
  });

  it("groups commands under their area display name with full records", () => {
    const groups = toCommandsProps(data).groups ?? [];
    const cats = groups.map((g) => g.category).sort();
    expect(cats).toEqual(["games", "moderation"]);
    const warn = groups
      .flatMap((g) => g.commands)
      .find((c) => c.name === "warn");
    expect(warn?.permissions).toBe("Moderator");
    expect(warn?.examples).toContain("!warn @user spamming");
  });

  it("maps changelog change-types onto ChangelogKind", () => {
    const entries = toChangelogProps(data).entries ?? [];
    expect(entries[0]).toMatchObject({
      kind: "feature",
      title: "Fishing minigame",
    });
    expect(entries[0].summary).toContain("rod ladder");
  });

  it("maps the status build + counts", () => {
    const p = toStatusProps(data);
    expect(p.build?.subject).toBe("sample");
    expect(p.counts?.games).toBe(9);
  });
});

// The top-level keys the adapter (data.ts) actually reads off the payload. If you
// teach the adapter to read a new top-level key, add it here AND to the contract —
// the test below fails otherwise, which is the point (the design↔data seam guard).
const ADAPTER_CONSUMED_TOP_LEVEL = [
  "addUrl",
  "build",
  "counts",
  "areas",
  "commands",
  "games",
  "changelog",
] as const;

describe("design↔data contract (shared with the Python producer)", () => {
  // The ONE source of truth — the same file botsite/site_data.validate_site_data_payload
  // checks the producer against. Read across packages on purpose: the contract spans
  // the botsite (producer) ↔ design-system (consumer) seam.
  const contractUrl = new URL(
    "../../../botsite/data/site_data_contract.json",
    import.meta.url,
  );
  const contract = JSON.parse(
    readFileSync(fileURLToPath(contractUrl), "utf-8"),
  ) as { top_level: string[] };

  it("the adapter never reads a top-level key the contract doesn't promise", () => {
    for (const key of ADAPTER_CONSUMED_TOP_LEVEL) {
      expect(contract.top_level).toContain(key);
    }
  });

  it("the bundled sample satisfies the contract's top-level keys", () => {
    // The offline fallback must itself be contract-valid (it stands in for the real
    // payload), so a contract change that the sample misses is caught here too.
    for (const key of ADAPTER_CONSUMED_TOP_LEVEL) {
      expect(SAMPLE_SITE_DATA).toHaveProperty(key);
    }
  });
});

describe("loadSiteData fallback", () => {
  it("falls back to the sample when the fetch fails", async () => {
    const failing: typeof fetch = async () => {
      throw new Error("offline");
    };
    const out = await loadSiteData("/site-data.json", failing);
    expect(out).toBe(SAMPLE_SITE_DATA);
  });

  it("falls back to the sample on a non-ok response", async () => {
    const notOk: typeof fetch = async () =>
      ({ ok: false, status: 404 }) as Response;
    const out = await loadSiteData("/site-data.json", notOk);
    expect(out).toBe(SAMPLE_SITE_DATA);
  });

  it("returns the parsed payload on success", async () => {
    const payload: SiteData = { counts: { commands: 1, features: 2, games: 3 } };
    const ok: typeof fetch = async () =>
      ({ ok: true, status: 200, json: async () => payload }) as Response;
    const out = await loadSiteData("/site-data.json", ok);
    expect(out).toEqual(payload);
  });
});
