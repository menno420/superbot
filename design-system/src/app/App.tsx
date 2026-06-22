import * as React from "react";

import { LandingPage } from "../LandingPage";
import { FeaturesPage } from "../FeaturesPage";
import { CommandsPage } from "../CommandsPage";
import { ChangelogPage } from "../ChangelogPage";
import { StatusPage } from "../StatusPage";

import {
  loadSiteData,
  routeFromHash,
  toLandingProps,
  toFeaturesProps,
  toGamesProps,
  toCommandsProps,
  toChangelogProps,
  toStatusProps,
  type Route,
  type SiteData,
} from "./data";

/**
 * The live SuperBot website as a React SPA — the runnable composition of the
 * design-system page components, fed real bot data from `/site-data.json`.
 *
 * This is PR 1 of the React-SPA migration: additive (the live vanilla SPA still
 * serves visitors). It exists so a Claude Design edit to a page component can,
 * once PR 2 cuts over, land on the live site with no hand-written port.
 *
 * Routing is hash-based to match the existing SPA URL scheme (`#/commands`, …) and
 * to keep botsite serving a single static shell (no server route changes).
 */
export function App() {
  const route = useHashRoute();
  const data = useSiteData();
  return renderRoute(route, data);
}

export function renderRoute(route: Route, data: SiteData): React.ReactElement {
  switch (route) {
    case "features":
      return <FeaturesPage {...toFeaturesProps(data)} />;
    case "commands":
      return <CommandsPage {...toCommandsProps(data)} />;
    case "games":
      return <FeaturesPage {...toGamesProps(data)} />;
    case "changelog":
      return <ChangelogPage {...toChangelogProps(data)} />;
    case "status":
      return <StatusPage {...toStatusProps(data)} />;
    case "home":
    default:
      return <LandingPage {...toLandingProps(data)} />;
  }
}

function useHashRoute(): Route {
  const [route, setRoute] = React.useState<Route>(() =>
    routeFromHash(typeof window !== "undefined" ? window.location.hash : ""),
  );
  React.useEffect(() => {
    const onHash = () => setRoute(routeFromHash(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  return route;
}

function useSiteData(): SiteData {
  const [data, setData] = React.useState<SiteData>({});
  React.useEffect(() => {
    let alive = true;
    loadSiteData().then((d) => {
      if (alive) setData(d);
    });
    return () => {
      alive = false;
    };
  }, []);
  return data;
}
