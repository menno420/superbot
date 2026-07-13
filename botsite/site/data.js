/* ============================================================================
   SuperBot — SPA data layer (window.SBDATA)
   GENERATED FROM botsite/data/site.json — DO NOT EDIT BY HAND.
   Regenerate: python3.10 scripts/export_dashboard_data.py   (or -m botsite.site_data)
   Served live by the /data.js route; this committed copy is the static fallback.
   ========================================================================== */

const ICONS = {
  "gamepad": "<line x1=\"6\" y1=\"11\" x2=\"10\" y2=\"11\"/><line x1=\"8\" y1=\"9\" x2=\"8\" y2=\"13\"/><line x1=\"15\" y1=\"12\" x2=\"15.01\" y2=\"12\"/><line x1=\"18\" y1=\"10\" x2=\"18.01\" y2=\"10\"/><rect x=\"2\" y=\"6\" width=\"20\" height=\"12\" rx=\"6\"/>",
  "shield": "<path d=\"M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z\"/>",
  "cpu": "<path d=\"M12 3v3M12 18v3M5 12H2M22 12h-3\"/><rect x=\"6\" y=\"6\" width=\"12\" height=\"12\" rx=\"3\"/><circle cx=\"12\" cy=\"12\" r=\"2\"/>",
  "wrench": "<path d=\"M14 4l3 3-8 8H6v-3l8-8z\"/><path d=\"M5 20h14\"/>",
  "star": "<path d=\"M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5L12 3z\"/>",
  "music": "<path d=\"M9 18V5l11-2v13\"/><circle cx=\"6\" cy=\"18\" r=\"3\"/><circle cx=\"17\" cy=\"16\" r=\"3\"/>",
  "search": "<circle cx=\"11\" cy=\"11\" r=\"7\"/><path d=\"M21 21l-4-4\"/>",
  "chevron": "<path d=\"M9 6l6 6-6 6\"/>",
  "arrow": "<path d=\"M5 12h14M13 6l6 6-6 6\"/>",
  "back": "<path d=\"M19 12H5M11 6l-6 6 6 6\"/>",
  "plus": "<path d=\"M12 5v14M5 12h14\"/>",
  "check": "<path d=\"M20 6L9 17l-5-5\"/>",
  "spark": "<path d=\"M12 3v18M3 12h18\" opacity=\".5\"/><path d=\"M12 7l1.5 3.5L17 12l-3.5 1.5L12 17l-1.5-3.5L7 12l3.5-1.5z\"/>",
  "comment": "<path d=\"M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z\"/>",
  "activity": "<path d=\"M22 12h-4l-3 9L9 3l-3 9H2\"/>",
  "clock": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7v5l3 2\"/>",
  "tag": "<path d=\"M3 7v5l8 8 7-7-8-8H3z\"/><circle cx=\"7.5\" cy=\"8.5\" r=\"1.5\"/>",
  "coin": "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M12 7v10M9.5 9.5h3a2 2 0 0 1 0 4H10a2 2 0 0 0 0 4h3.5\"/>",
  "sliders": "<line x1=\"4\" y1=\"8\" x2=\"20\" y2=\"8\"/><line x1=\"4\" y1=\"16\" x2=\"20\" y2=\"16\"/><circle cx=\"9\" cy=\"8\" r=\"2.2\"/><circle cx=\"15\" cy=\"16\" r=\"2.2\"/>"
};

const AREAS = [
  {
    "id": "games",
    "name": "games",
    "icon": "gamepad",
    "color": "var(--g)",
    "title": "Games, ready to play",
    "tagline": "Quick, replayable fun that keeps members coming back.",
    "description": "A suite of games members can play right in chat — cards, dice, fishing, word games and more, with leaderboards and rewards.",
    "points": [
      "BTD6 Assistant",
      "Blackjack",
      "Casino",
      "Chicken Farm",
      "Counting"
    ]
  },
  {
    "id": "moderation",
    "name": "moderation",
    "icon": "shield",
    "color": "var(--sky)",
    "title": "Keep the peace, automatically",
    "tagline": "Keep your community healthy without the busywork.",
    "description": "Automatic and manual moderation with a full audit trail — automod, cleanup, image moderation and server security.",
    "points": [
      "Automod",
      "Cleanup",
      "Image moderation",
      "Moderation",
      "Proof Channel"
    ]
  },
  {
    "id": "economy",
    "name": "economy",
    "icon": "coin",
    "color": "var(--amber)",
    "title": "A living server economy",
    "tagline": "Currency, inventory and mining to keep members engaged.",
    "description": "An in-server economy: earn and spend currency, manage an inventory, and dig for resources with mining.",
    "points": [
      "Economy",
      "Inventory",
      "Mining",
      "Treasury"
    ]
  },
  {
    "id": "admin",
    "name": "admin",
    "icon": "cpu",
    "color": "var(--g-bright)",
    "title": "Run the bot with confidence",
    "tagline": "Diagnostics, settings and control for server owners.",
    "description": "Operator tooling: cog management, server diagnostics, the settings manager and the AI platform readout — the control surface for your bot.",
    "points": [
      "AI Platform",
      "Administration",
      "Diagnostics",
      "Server Logging",
      "Server Management"
    ]
  },
  {
    "id": "community",
    "name": "community",
    "icon": "comment",
    "color": "var(--pink)",
    "title": "Bring members together",
    "tagline": "Welcome, spotlight and celebrate your members.",
    "description": "Community-building tools: welcome flows, member spotlights and live server counters.",
    "points": [
      "Community",
      "Community Spotlight",
      "Server Counters",
      "Support Tickets",
      "Welcome"
    ]
  },
  {
    "id": "progression",
    "name": "progression",
    "icon": "star",
    "color": "var(--indigo)",
    "title": "XP, ranks and leaderboards",
    "tagline": "Turn activity into status with XP and ranks.",
    "description": "Members earn XP for taking part, climb the ranks, and compete on server leaderboards.",
    "points": [
      "Karma",
      "Leaderboard",
      "XP & Levels"
    ]
  },
  {
    "id": "utility",
    "name": "utility",
    "icon": "wrench",
    "color": "var(--g)",
    "title": "The everyday toolkit",
    "tagline": "The little tools a busy server needs every day.",
    "description": "General-purpose quality-of-life commands and helpers, plus the help system that ties everything together.",
    "points": [
      "420",
      "General",
      "Help",
      "Utility"
    ]
  },
  {
    "id": "management",
    "name": "management",
    "icon": "sliders",
    "color": "var(--sky)",
    "title": "Shape your server",
    "tagline": "Channels and roles, managed from chat.",
    "description": "Server-shaping commands for channels and roles — structure your space without leaving Discord.",
    "points": [
      "Channels",
      "Roles",
      "More commands grouped under this area"
    ]
  },
  {
    "id": "other",
    "name": "more",
    "icon": "spark",
    "color": "var(--g-bright)",
    "title": "Everything else",
    "tagline": "Handy extras that round out the bot.",
    "description": "Additional commands that don't fit a single category — odds and ends that are still worth a look.",
    "points": [
      "More commands grouped under this area",
      "Searchable on the Commands page",
      "Each with its own reference page"
    ]
  }
];

const COMMANDS = [
  {
    "name": "+prize",
    "area": "moderation",
    "status": "finished",
    "summary": "Grant a winner exclusive access to #proof. Usage: +prize @winner",
    "description": "Grant a winner exclusive access to #proof. Usage: +prize @winner",
    "usage": "!+prize",
    "aliases": [],
    "permissions": "Staff",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "-prize",
    "area": "moderation",
    "status": "finished",
    "summary": "End the prize session and make #proof read-only again. Usage: -prize",
    "description": "End the prize session and make #proof read-only again. Usage: -prize",
    "usage": "!-prize",
    "aliases": [],
    "permissions": "Staff",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "420",
    "area": "utility",
    "status": "finished",
    "summary": "Open the 🍃 420 panel — rotating wisdom and number trivia.",
    "description": "Entry-point command for the 420 subsystem panel.",
    "usage": "!420",
    "aliases": [
      "fourtwenty",
      "fourtwenty420"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "access",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the read-only access-policy explorer.",
    "description": "Open AccessExplorerView for the invoker.",
    "usage": "!access",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!settings"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Settings presets everywhere + AI template advisor — idea capture…"
      }
    ]
  },
  {
    "name": "add",
    "area": "community",
    "status": "finished",
    "summary": "Add a member to this ticket (staff).",
    "description": "Add a member to this ticket (staff).",
    "usage": "!add",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "admin",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the Admin control panel (administrator only).",
    "description": "Slash front door for the Admin hub — ephemeral, admin-only.",
    "usage": "!admin",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "adminmenu",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the interactive admin control panel.",
    "description": "Open the interactive admin control panel.",
    "usage": "!adminmenu",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "ai",
    "area": "admin",
    "status": "in-progress",
    "summary": "AI Platform diagnostics (administrator only).",
    "description": "Open the AI Platform panel.",
    "usage": "!ai",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "aimenu",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the AI Platform panel (alias for ``!ai``).",
    "description": "Open the AI Platform panel (alias for !ai).",
    "usage": "!aimenu",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!ai"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "aireview",
    "area": "other",
    "status": "finished",
    "summary": "Show the AI review-log status (channel + unreviewed backlog).",
    "description": "Show the AI review-log status (channel + unreviewed backlog).",
    "usage": "!aireview",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "anchors",
    "area": "other",
    "status": "finished",
    "summary": "Show last restoration outcome and active anchor counts per subsystem.",
    "description": "Show last restoration outcome and active anchor counts per subsystem.",
    "usage": "!anchors",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "announcechannel",
    "area": "games",
    "status": "in-progress",
    "summary": "Set/clear the BTD6 new-version announcement channel (admin).",
    "description": "Set/clear the BTD6 new-version announcement channel (admin).",
    "usage": "!announcechannel",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "ascend",
    "area": "economy",
    "status": "in-progress",
    "summary": "Climb one mining band back toward the surface.",
    "description": "Climb one mining band back toward the surface.",
    "usage": "!ascend",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "ask",
    "area": "games",
    "status": "in-progress",
    "summary": "Ask a BTD6 question.",
    "description": "Ask a BTD6 question.",
    "usage": "!ask",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "assignroles",
    "area": "management",
    "status": "in-progress",
    "summary": "Manually run time-based role assignment for all members.",
    "description": "Manually run time-based role assignment for all members.",
    "usage": "!assignroles",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "automation",
    "area": "other",
    "status": "finished",
    "summary": "Open the automation management + diagnostics panel.",
    "description": "Open the automation management + diagnostics panel.",
    "usage": "!automation",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "automod",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Show the current automod policy for this server.",
    "description": "Render the effective automod policy (admin/manage-guild only).",
    "usage": "!automod",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "avatar",
    "area": "utility",
    "status": "finished",
    "summary": "Display a user's avatar.",
    "description": "Display a user's avatar.",
    "usage": "!avatar",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "backfill",
    "area": "other",
    "status": "finished",
    "summary": "Dry-run (default) or `apply` the legacy-pointer → binding backfill.",
    "description": "Dry-run (default) or apply the legacy-pointer → binding backfill.",
    "usage": "!backfill",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "bait",
    "area": "games",
    "status": "in-progress",
    "summary": "Load fishing bait — a consumable that pulls catches toward bigger fish.",
    "description": "Load fishing bait — a consumable that pulls catches toward bigger fish.",
    "usage": "!bait",
    "aliases": [
      "baitshop",
      "buybait"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "balance",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show your (or another user's) current coin balance.",
    "description": "Show your (or another user's) current coin balance.",
    "usage": "!balance",
    "aliases": [
      "bal",
      "wallet"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "ban",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Ban a member from the server.",
    "description": "Ban a member from the server.",
    "usage": "!ban",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "bindings",
    "area": "other",
    "status": "finished",
    "summary": "Subsystem bindings (Phase 2b) — taxonomy + per-guild histograms.",
    "description": "Subsystem bindings (Phase 2b) — taxonomy + per-guild histograms.",
    "usage": "!bindings",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "bjstart",
    "area": "games",
    "status": "finished",
    "summary": "Manually start a pending Blackjack tournament early.",
    "description": "Manually start a pending Blackjack tournament early.",
    "usage": "!bjstart",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "bjstatus",
    "area": "games",
    "status": "finished",
    "summary": "Show the current tournament status.",
    "description": "Show the current tournament status.",
    "usage": "!bjstatus",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "bjtournament",
    "area": "games",
    "status": "finished",
    "summary": "Start a Blackjack tournament. !bjtournament [entry_fee] [rounds] [mins]",
    "description": "Start a Blackjack tournament. !bjtournament [entry_fee] [rounds] [mins]",
    "usage": "!bjtournament",
    "aliases": [
      "bjtourn"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "blackjack",
    "area": "games",
    "status": "finished",
    "summary": "Play blackjack. !bj [bet] or !bj @player [bet]",
    "description": "Play blackjack. !bj [bet] or !bj @player [bet]",
    "usage": "!blackjack",
    "aliases": [
      "bj"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "boathouse",
    "area": "games",
    "status": "in-progress",
    "summary": "Build a Boathouse — the coral+wood structure that refills energy faster.",
    "description": "Build a Boathouse — the coral+wood structure that refills energy faster.",
    "usage": "!boathouse",
    "aliases": [
      "moorings",
      "boat"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!tidepool",
      "!dock"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "botinfo",
    "area": "utility",
    "status": "finished",
    "summary": "Show information about the bot — servers, uptime, latency, version.",
    "description": "Show information about the bot — servers, uptime, latency, version.",
    "usage": "!botinfo",
    "aliases": [
      "about"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "browse",
    "area": "games",
    "status": "in-progress",
    "summary": "Browse published BTD6 strategies.",
    "description": "Browse published BTD6 strategies.",
    "usage": "!browse",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 Assistant — lookups, strategy, live events, and ops.",
    "description": "BTD6 Assistant — open the panel, or run a subcommand (income/round/…).",
    "usage": "!btd6",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6events",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 live events — hidden alias of `!btd6 events`.",
    "description": "BTD6 live events — hidden alias of !btd6 events.",
    "usage": "!btd6events",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!btd6 events"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6menu",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the BTD6 panel (alias for ``!btd6``).",
    "description": "Open the BTD6 panel (alias for !btd6).",
    "usage": "!btd6menu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!btd6"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6ops",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 ingestion operations — hidden alias of `!btd6 ops`.",
    "description": "BTD6 ingestion operations — hidden alias of !btd6 ops.",
    "usage": "!btd6ops",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!btd6 ops"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6ref",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 reference lookups — hidden alias of `!btd6` (towers/heroes/rounds/…).",
    "description": "BTD6 reference lookups — hidden alias of !btd6 (towers/heroes/rounds/…).",
    "usage": "!btd6ref",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!btd6"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "btd6strat",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 strategy memory — hidden alias of `!btd6 strat`.",
    "description": "BTD6 strategy memory — hidden alias of !btd6 strat.",
    "usage": "!btd6strat",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!btd6 strat"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "bugreport",
    "area": "other",
    "status": "finished",
    "summary": "Report a bug — Hermes dispatches a Claude Code session to fix it automatically.",
    "description": "Submit a bug report that fires an autonomous fix session.",
    "usage": "!bugreport",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "build",
    "area": "economy",
    "status": "in-progress",
    "summary": "Build / craft an item from recipes (one shared, atomic implementation).",
    "description": "Build / craft an item from recipes (one shared, atomic implementation).",
    "usage": "!build",
    "aliases": [
      "craft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "buildable",
    "area": "economy",
    "status": "in-progress",
    "summary": "Lists only what the user can currently build based on their inventory.",
    "description": "Lists only what the user can currently build based on their inventory.",
    "usage": "!buildable",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "buildlist",
    "area": "economy",
    "status": "in-progress",
    "summary": "Shows all craftable structures from recipes.json.",
    "description": "Shows all craftable structures from recipes.json.",
    "usage": "!buildlist",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "bulkcreate",
    "area": "management",
    "status": "in-progress",
    "summary": "Create multiple channels. Usage: !bulkcreate <ch1> [ch2...] [category]",
    "description": "Create multiple channels. Usage: !bulkcreate <ch1> [ch2...] [category]",
    "usage": "!bulkcreate",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "bulkdelete",
    "area": "management",
    "status": "in-progress",
    "summary": "Delete multiple channels. Usage: !bulkdelete <name|id> [name|id...] or <keyword>",
    "description": "Delete multiple channels. Usage: !bulkdelete <name|id> [name|id...] or <keyword>",
    "usage": "!bulkdelete",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "buy",
    "area": "economy",
    "status": "in-progress",
    "summary": "Buy gear with coins (e.g. `!buy iron sword`).",
    "description": "Buy gear with coins (e.g. !buy iron sword).",
    "usage": "!buy",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!buy iron sword"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "caches",
    "area": "other",
    "status": "finished",
    "summary": "Cache state: F-1 guild_config + governance.cache.",
    "description": "Cache state: F-1 guild_config + governance.cache.",
    "usage": "!caches",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "casino",
    "area": "games",
    "status": "finished",
    "summary": "Open the Casino hub — group card games like poker.",
    "description": "Open the Casino hub — group card games like poker.",
    "usage": "!casino",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "catch",
    "area": "games",
    "status": "in-progress",
    "summary": "Head into the wild to find and catch a creature.",
    "description": "Head into the wild to find and catch a creature.",
    "usage": "!catch",
    "aliases": [
      "hunt"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Creature PvP — rematch button on the outcome embed"
      },
      {
        "status": "idea",
        "title": "Idea — a parity guard tying the creature sim to the runtime battle…"
      }
    ]
  },
  {
    "name": "cbattle",
    "area": "other",
    "status": "finished",
    "summary": "Challenge another member to a level-normalized creature PvP battle.",
    "description": "Challenge another member to a level-normalized creature PvP battle.",
    "usage": "!cbattle",
    "aliases": [
      "creaturebattle"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cbattletop",
    "area": "other",
    "status": "finished",
    "summary": "Show this server's top creature-PvP trainers by wins.",
    "description": "Show this server's top creature-PvP trainers by wins.",
    "usage": "!cbattletop",
    "aliases": [
      "pvptop",
      "battletop"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cbrecord",
    "area": "other",
    "status": "finished",
    "summary": "Show your (or another trainer's) creature PvP win/loss record.",
    "description": "Show your (or another trainer's) creature PvP win/loss record.",
    "usage": "!cbrecord",
    "aliases": [
      "battlerecord"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "chain",
    "area": "games",
    "status": "finished",
    "summary": "Manage message chains and word limits in your server.",
    "description": "Manage message chains and word limits in your server.",
    "usage": "!chain",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "chainmenu",
    "area": "games",
    "status": "finished",
    "summary": "Open the interactive chain management panel.",
    "description": "Open the interactive chain management panel.",
    "usage": "!chainmenu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "channel",
    "area": "other",
    "status": "finished",
    "summary": "Set the review channel: ``!aireview channel #chan``.",
    "description": "Set the review channel: !aireview channel #chan.",
    "usage": "!channel",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!aireview channel #chan"
    ],
    "planned": []
  },
  {
    "name": "channelinfo",
    "area": "management",
    "status": "in-progress",
    "summary": "Channel details. Usage: !channelinfo <name|id>",
    "description": "Channel details. Usage: !channelinfo <name|id>",
    "usage": "!channelinfo",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "channelmenu",
    "area": "management",
    "status": "in-progress",
    "summary": "Open the interactive channel management panel.",
    "description": "Open the interactive channel management panel.",
    "usage": "!channelmenu",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "character",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show your full mining character — the paper-doll, location, stats, wealth.",
    "description": "Show your full mining character — the paper-doll, location, stats, wealth.",
    "usage": "!character",
    "aliases": [
      "profile",
      "char"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "check_database",
    "area": "admin",
    "status": "finished",
    "summary": "Verify that all expected PostgreSQL tables exist.",
    "description": "Verify that all expected PostgreSQL tables exist.",
    "usage": "!check_database",
    "aliases": [
      "checkdb"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "chop",
    "area": "economy",
    "status": "in-progress",
    "summary": "Chop wood. If you have an 'axe', you'll collect double.",
    "description": "Chop wood. If you have an 'axe', you'll collect double.",
    "usage": "!chop",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "claim",
    "area": "community",
    "status": "finished",
    "summary": "Claim the ticket in this channel (staff).",
    "description": "Claim the ticket in this channel (staff).",
    "usage": "!claim",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cleanup",
    "area": "moderation",
    "status": "finished",
    "summary": "Open the Cleanup hub panel — overview + routing to subviews.",
    "description": "Open the Cleanup hub panel — overview + routing to subviews.",
    "usage": "!cleanup",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cleanup-preview",
    "area": "other",
    "status": "finished",
    "summary": "Dry-run preview of the cleanup policy resolved for a location (IL-2).",
    "description": "Dry-run preview of the cleanup policy resolved for a location (IL-2).",
    "usage": "!cleanup-preview",
    "aliases": [
      "cleanuppreview",
      "cleanup-policy"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cleanuphistory",
    "area": "moderation",
    "status": "finished",
    "summary": "Clean channel history by keyword, commands, prohibited words, spam, embeds, links, or attachments.",
    "description": "Clean channel history by keyword, commands, prohibited words, spam, embeds, links, or attachments.",
    "usage": "!cleanuphistory",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "clear",
    "area": "utility",
    "status": "finished",
    "summary": "Purge messages. Max 100.",
    "description": "Purge messages. Max 100.",
    "usage": "!clear",
    "aliases": [
      "purge"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "clearwarnings",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Clear all warnings for a member.",
    "description": "Clear all warnings for a member.",
    "usage": "!clearwarnings",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "clone",
    "area": "management",
    "status": "in-progress",
    "summary": "Clone a channel. Usage: !clone <name|id> <new_name>",
    "description": "Clone a channel. Usage: !clone <name|id> <new_name>",
    "usage": "!clone",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "close",
    "area": "community",
    "status": "finished",
    "summary": "Close the ticket in this channel (staff or the opener).",
    "description": "Close the ticket in this channel (staff or the opener).",
    "usage": "!close",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cog",
    "area": "admin",
    "status": "in-progress",
    "summary": "Load, unload, or reload a cog by name (underscores and _cog suffix optional).",
    "description": "Load, unload, or reload a cog by name (underscores and _cog suffix optional).",
    "usage": "!cog",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "coglist",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the interactive cog manager — the panel's 📋 Cog List button.",
    "description": "Open the interactive cog manager — the panel's 📋 Cog List button.",
    "usage": "!coglist",
    "aliases": [
      "cogs",
      "listcogs",
      "cogslist"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!cog"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "command-access",
    "area": "other",
    "status": "finished",
    "summary": "Show the live command-access decision for a channel.",
    "description": "Show the live command-access decision for a channel.",
    "usage": "!command-access",
    "aliases": [
      "commandaccess"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!bj"
    ],
    "planned": []
  },
  {
    "name": "community",
    "area": "community",
    "status": "in-progress",
    "summary": "Open the Community hub — XP, Roles, and community activities.",
    "description": "Open the Community hub — XP, Roles, and community activities.",
    "usage": "!community",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Giveaway competitive teardown — GiveawayBot vs. SuperBot (2026-06-23)"
      },
      {
        "status": "idea",
        "title": "Community platform features — welcome, feeds, events, counters…"
      }
    ]
  },
  {
    "name": "consistency",
    "area": "other",
    "status": "finished",
    "summary": "Unified platform readiness diagnostic — read-only (Phase 2 PR-10).",
    "description": "Unified platform readiness diagnostic — read-only (Phase 2 PR-10).",
    "usage": "!consistency",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "contribute",
    "area": "economy",
    "status": "finished",
    "summary": "Donate *amount* of your own coins into the server treasury.",
    "description": "Donate *amount* of your own coins into the server treasury.",
    "usage": "!contribute",
    "aliases": [
      "donate",
      "deposit"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "cook",
    "area": "economy",
    "status": "in-progress",
    "summary": "Cook a caught fish into food at your campfire (refills mining energy).",
    "description": "Cook a caught fish into food at your campfire (refills mining energy).",
    "usage": "!cook",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!cook <fish>",
      "!cook <amount> <fish>",
      "!cook 3 minnow"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "count_info",
    "area": "games",
    "status": "finished",
    "summary": "Displays the current count and configuration.",
    "description": "Displays the current count and configuration.",
    "usage": "!count_info",
    "aliases": [
      "ci"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "count_rules",
    "area": "games",
    "status": "finished",
    "summary": "Displays the counting game rules.",
    "description": "Displays the counting game rules.",
    "usage": "!count_rules",
    "aliases": [
      "cr"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "counterpreset",
    "area": "community",
    "status": "in-progress",
    "summary": "Apply a curated counter name-template preset (sets all three templates at once). Run without a name to list the presets.",
    "description": "Apply one of the curated template presets through the audited seam.",
    "usage": "!counterpreset",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!settings"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Community platform features — welcome, feeds, events, counters…"
      }
    ]
  },
  {
    "name": "counters",
    "area": "community",
    "status": "in-progress",
    "summary": "Show the current server-counter channels for this server.",
    "description": "Render the effective counter policy (admin/manage-guild only).",
    "usage": "!counters",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Community platform features — welcome, feeds, events, counters…"
      }
    ]
  },
  {
    "name": "counting-health",
    "area": "other",
    "status": "finished",
    "summary": "Surface counting persistence health from task_outcome_total (IL-3).",
    "description": "Surface counting persistence health from task_outcome_total (IL-3).",
    "usage": "!counting-health",
    "aliases": [
      "countinghealth"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "countingmenu",
    "area": "games",
    "status": "finished",
    "summary": "Open the interactive counting game management panel.",
    "description": "Open the interactive counting game management panel.",
    "usage": "!countingmenu",
    "aliases": [
      "cm"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "counttop",
    "area": "games",
    "status": "finished",
    "summary": "Show the counting leaderboard — who has landed the most correct counts.",
    "description": "Show the counting leaderboard — who has landed the most correct counts.",
    "usage": "!counttop",
    "aliases": [
      "ct",
      "counting_top"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "craftbait",
    "area": "games",
    "status": "in-progress",
    "summary": "Craft bait from small caught fish — closes the catch→bait loop.",
    "description": "Craft bait from small caught fish — closes the catch→bait loop.",
    "usage": "!craftbait",
    "aliases": [
      "baitcraft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!craftbait worm"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "craftcharm",
    "area": "games",
    "status": "in-progress",
    "summary": "Craft a fishing charm from caught fish — the non-coin earn path.",
    "description": "Craft a fishing charm from caught fish — the non-coin earn path.",
    "usage": "!craftcharm",
    "aliases": [
      "charmcraft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!craftcharm fishing charm",
      "!gear"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "craftcurio",
    "area": "games",
    "status": "in-progress",
    "summary": "Carve a cosmetic curio from coral — the deepwater rare-material sink.",
    "description": "Carve a cosmetic curio from coral — the deepwater rare-material sink.",
    "usage": "!craftcurio",
    "aliases": [
      "carve",
      "curiocraft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!craftcurio coral idol",
      "!curios"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "craftpearl",
    "area": "games",
    "status": "in-progress",
    "summary": "Spend pearls to craft the premium bait — the rare-material sink.",
    "description": "Spend pearls to craft the premium bait — the rare-material sink.",
    "usage": "!craftpearl",
    "aliases": [
      "pearlcraft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!craftpearl feast",
      "!bait"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "craftrod",
    "area": "games",
    "status": "in-progress",
    "summary": "Craft the next rod up the ladder from caught fish — the non-coin path.",
    "description": "Craft the next rod up the ladder from caught fish — the non-coin path.",
    "usage": "!craftrod",
    "aliases": [
      "rodcraft"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!craftcharm",
      "!rod"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "create",
    "area": "admin",
    "status": "in-progress",
    "summary": "Preview + create a new log channel for any registered route.",
    "description": "Preview + create a new log channel for any registered route.",
    "usage": "!create",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      }
    ]
  },
  {
    "name": "createrole",
    "area": "management",
    "status": "in-progress",
    "summary": "Create a role (use !roles → Create instead).",
    "description": "Create a role (use !roles → Create instead).",
    "usage": "!createrole",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "creatures",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the interactive Creatures panel — catch, browse your dex, battle.",
    "description": "Open the interactive Creatures panel — catch, browse your dex, battle.",
    "usage": "!creatures",
    "aliases": [
      "creaturemenu",
      "pets"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Creature PvP — rematch button on the outcome embed"
      },
      {
        "status": "idea",
        "title": "Idea — a parity guard tying the creature sim to the runtime battle…"
      }
    ]
  },
  {
    "name": "ct",
    "area": "games",
    "status": "in-progress",
    "summary": "Browse active Contested Territory events and relic tiles.",
    "description": "Browse active Contested Territory events and relic tiles.",
    "usage": "!ct",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "ctteam",
    "area": "games",
    "status": "in-progress",
    "summary": "View or set this server's CT team (paste the bracket group id / URL).",
    "description": "View or set this server's CT team (paste the bracket group id / URL).",
    "usage": "!ctteam",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "curios",
    "area": "games",
    "status": "in-progress",
    "summary": "Show the coral-carving collection + your coral and craft progress.",
    "description": "Show the coral-carving collection + your coral and craft progress.",
    "usage": "!curios",
    "aliases": [
      "curio",
      "carvings"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!craftcurio <name>"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "customization",
    "area": "other",
    "status": "finished",
    "summary": "Customization catalogue across subsystems (S2).",
    "description": "Customization catalogue across subsystems (S2).",
    "usage": "!customization",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "daily",
    "area": "economy",
    "status": "in-progress",
    "summary": "Claim your daily reward. Higher streaks unlock better odds!",
    "description": "Claim your daily reward. Higher streaks unlock better odds!",
    "usage": "!daily",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "damage",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a damage type (Slash / Pierce / Blunt) (or list them all).",
    "description": "Look up a damage type (Slash / Pierce / Blunt) (or list them all).",
    "usage": "!damage",
    "aliases": [
      "damagetype"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "debugroles",
    "area": "management",
    "status": "in-progress",
    "summary": "Print all role names for verification.",
    "description": "Print all role names for verification.",
    "usage": "!debugroles",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "del",
    "area": "management",
    "status": "in-progress",
    "summary": "Delete a specific channel. Usage: !del <name|id>",
    "description": "Delete a specific channel. Usage: !del <name|id>",
    "usage": "!del",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "delete",
    "area": "games",
    "status": "finished",
    "summary": "Delete a chain from a specified channel or the current channel if none is provided.",
    "description": "Delete a chain from a specified channel or the current channel if none is provided.",
    "usage": "!delete",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!chain delete [channel]"
    ],
    "planned": []
  },
  {
    "name": "deleterole",
    "area": "management",
    "status": "in-progress",
    "summary": "Delete a role by name or mention.",
    "description": "Delete a role by name or mention.",
    "usage": "!deleterole",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "descend",
    "area": "economy",
    "status": "in-progress",
    "summary": "Descend one mining band deeper (gated by your equipped light).",
    "description": "Descend one mining band deeper (gated by your equipped light).",
    "usage": "!descend",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "dex",
    "area": "games",
    "status": "in-progress",
    "summary": "Show your creature collection — every creature you've caught.",
    "description": "Show your creature collection — every creature you've caught.",
    "usage": "!dex",
    "aliases": [
      "collection"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Creature PvP — rematch button on the outcome embed"
      },
      {
        "status": "idea",
        "title": "Idea — a parity guard tying the creature sim to the runtime battle…"
      }
    ]
  },
  {
    "name": "dextop",
    "area": "games",
    "status": "in-progress",
    "summary": "Show this server's top collectors by total creatures caught.",
    "description": "Show this server's top collectors by total creatures caught.",
    "usage": "!dextop",
    "aliases": [
      "topcatchers"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Creature PvP — rematch button on the outcome embed"
      },
      {
        "status": "idea",
        "title": "Idea — a parity guard tying the creature sim to the runtime battle…"
      }
    ]
  },
  {
    "name": "diagnostic_bot_status",
    "area": "admin",
    "status": "finished",
    "summary": "Display bot health and performance metrics.",
    "description": "Display bot health and performance metrics.",
    "usage": "!diagnostic_bot_status",
    "aliases": [
      "diag_status"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "diagnostics",
    "area": "admin",
    "status": "in-progress",
    "summary": "The diagnostics command.",
    "description": "The diagnostics command.",
    "usage": "!diagnostics",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "dispatch",
    "area": "other",
    "status": "finished",
    "summary": "Send a raw Hermes work order to the Claude Code Routine (owner only).",
    "description": "Fire an arbitrary work order at the Claude Code Routine.",
    "usage": "!dispatch",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "dm_challenge",
    "area": "games",
    "status": "finished",
    "summary": "Challenge another user to a deathmatch duel.",
    "description": "Challenge another user to a deathmatch duel.",
    "usage": "!dm_challenge",
    "aliases": [
      "deathmatch",
      "challenge",
      "dm"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "dm_help",
    "area": "games",
    "status": "finished",
    "summary": "Display help information for Deathmatch commands.",
    "description": "Display help information for Deathmatch commands.",
    "usage": "!dm_help",
    "aliases": [
      "deathmatch_help"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "dock",
    "area": "games",
    "status": "in-progress",
    "summary": "Build a Dock — the cheap coral+wood structure that makes fish bite faster.",
    "description": "Build a Dock — the cheap coral+wood structure that makes fish bite faster.",
    "usage": "!dock",
    "aliases": [
      "pier",
      "fishingdock"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!tidepool"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "economy",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the Economy hub (daily, work, shop, balance).",
    "description": "Slash front door for the Economy hub — ephemeral.",
    "usage": "!economy",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "economymenu",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the interactive economy control panel.",
    "description": "Open the interactive economy control panel.",
    "usage": "!economymenu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "economytrend",
    "area": "other",
    "status": "finished",
    "summary": "Per-day coin-flow trend (`!platform economytrend [days]`): the daily",
    "description": "Per-day coin-flow trend (!platform economytrend [days]): the daily minted/drained/net series + a net sparkline + a rising/falling read, so you can see whether the economy is inflating *over time*, not just at one snapshot. Window N days or omit for all-time. Read-only, content-free.",
    "usage": "!economytrend",
    "aliases": [
      "coinflowtrend"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!platform economytrend [days]"
    ],
    "planned": []
  },
  {
    "name": "ego",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up an E.G.O grade (ZAYIN…ALEPH) (or list them all).",
    "description": "Look up an E.G.O grade (ZAYIN…ALEPH) (or list them all).",
    "usage": "!ego",
    "aliases": [
      "grade"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "eightball",
    "area": "utility",
    "status": "finished",
    "summary": "Ask the Magic 8-Ball a yes/no question.",
    "description": "Ask the Magic 8-Ball a yes/no question.",
    "usage": "!eightball",
    "aliases": [
      "8ball"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "end_match",
    "area": "games",
    "status": "finished",
    "summary": "Ends the counting match in the specified channel and deletes the channel.",
    "description": "Ends the counting match in the specified channel and deletes the channel.",
    "usage": "!end_match",
    "aliases": [
      "em"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "equip",
    "area": "economy",
    "status": "in-progress",
    "summary": "Equip a tool, light, or charm so its stats apply to your character.",
    "description": "Equip a tool, light, or charm so its stats apply to your character.",
    "usage": "!equip",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "estimate",
    "area": "games",
    "status": "in-progress",
    "summary": "Estimate a boss fight from HP/DPS/cost (tower vs boss, or counters).",
    "description": "Estimate a boss fight from HP/DPS/cost (tower vs boss, or counters).",
    "usage": "!estimate",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "event",
    "area": "games",
    "status": "in-progress",
    "summary": "Show one specific BTD6 event with tower restrictions.",
    "description": "Show one specific BTD6 event with tower restrictions.",
    "usage": "!event",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "events",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 live events, leaderboards, and data sources.",
    "description": "BTD6 live events, leaderboards, and data-source diagnostics.",
    "usage": "!events",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "evt",
    "area": "management",
    "status": "in-progress",
    "summary": "Create or delete an event channel. Usage: !evt <name|id> <create/delete>",
    "description": "Create or delete an event channel. Usage: !evt <name|id> <create/delete>",
    "usage": "!evt",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "explore",
    "area": "economy",
    "status": "in-progress",
    "summary": "Discover random events or items (driven by your gear and depth).",
    "description": "Discover random events or items (driven by your gear and depth).",
    "usage": "!explore",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "export",
    "area": "other",
    "status": "finished",
    "summary": "Dump the backlog as a JSON file for triage.",
    "description": "Dump the backlog as a JSON file for triage.",
    "usage": "!export",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!aireview export",
      "!aireview export unknown",
      "!aireview export all"
    ],
    "planned": []
  },
  {
    "name": "fact",
    "area": "utility",
    "status": "finished",
    "summary": "Sends a random interesting fact.",
    "description": "Sends a random interesting fact.",
    "usage": "!fact",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "farm",
    "area": "games",
    "status": "finished",
    "summary": "Open your idle chicken farm — collect eggs, grow your flock and coop.",
    "description": "Open your idle chicken farm — collect eggs, grow your flock and coop.",
    "usage": "!farm",
    "aliases": [
      "chickenfarm",
      "coop"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "fastmine",
    "area": "economy",
    "status": "in-progress",
    "summary": "One quick mining swing — no buttons (the old !fastmine, reborn).",
    "description": "One quick mining swing — no buttons (the old !fastmine, reborn).",
    "usage": "!fastmine",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "find_command",
    "area": "admin",
    "status": "finished",
    "summary": "Search for commands by keyword in their name or description.",
    "description": "Search for commands by keyword in their name or description.",
    "usage": "!find_command",
    "aliases": [
      "findcmd"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "finding",
    "area": "other",
    "status": "finished",
    "summary": "Transition a persistent finding: `resolve` / `ignore` / `reopen` <fingerprint>.",
    "description": "Transition a persistent finding: resolve / ignore / reopen <fingerprint>.",
    "usage": "!finding",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!platform findings"
    ],
    "planned": []
  },
  {
    "name": "findings",
    "area": "other",
    "status": "finished",
    "summary": "Persistent operational-health findings (open / resolved / ignored / all).",
    "description": "Persistent operational-health findings (open / resolved / ignored / all).",
    "usage": "!findings",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!platform health"
    ],
    "planned": []
  },
  {
    "name": "fish",
    "area": "games",
    "status": "in-progress",
    "summary": "Cast a line — wait for the bite, then reel it in before it gets away.",
    "description": "Cast a line — wait for the bite, then reel it in before it gets away.",
    "usage": "!fish",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "fishery",
    "area": "games",
    "status": "in-progress",
    "summary": "Build a Fishery — the coral+wood structure that lands more double catches.",
    "description": "Build a Fishery — the coral+wood structure that lands more double catches.",
    "usage": "!fishery",
    "aliases": [
      "hatchery",
      "fishfarm"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!tidepool",
      "!dock",
      "!boathouse"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "fishing",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the interactive fishing menu — cast, upgrade your rod, browse the dex.",
    "description": "Open the interactive fishing menu — cast, upgrade your rod, browse the dex.",
    "usage": "!fishing",
    "aliases": [
      "fishmenu"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "fishlog",
    "area": "games",
    "status": "in-progress",
    "summary": "Show your fishing collection — every species you've caught.",
    "description": "Show your fishing collection — every species you've caught.",
    "usage": "!fishlog",
    "aliases": [
      "fishdex"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "fishtop",
    "area": "games",
    "status": "in-progress",
    "summary": "Show this server's top anglers by total fish caught.",
    "description": "Show this server's top anglers by total fish caught.",
    "usage": "!fishtop",
    "aliases": [
      "topfishers"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "flag",
    "area": "other",
    "status": "finished",
    "summary": "Open the editable per-guild flag manager (Phase 6.5a).",
    "description": "Open the editable per-guild flag manager (Phase 6.5a).",
    "usage": "!flag",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "flags",
    "area": "other",
    "status": "finished",
    "summary": "Feature flags: declarations + Phase 2d evaluator state per flag.",
    "description": "Feature flags: declarations + Phase 2d evaluator state per flag.",
    "usage": "!flags",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "force",
    "area": "other",
    "status": "finished",
    "summary": "Overrides channel restrictions and runs a command (admins only).",
    "description": "Overrides channel restrictions and runs a command (admins only).",
    "usage": "!force",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "forecast",
    "area": "games",
    "status": "in-progress",
    "summary": "Show today's fishing forecast — the date-seeded weather everyone shares.",
    "description": "Show today's fishing forecast — the date-seeded weather everyone shares.",
    "usage": "!forecast",
    "aliases": [
      "fishforecast",
      "fishingweather"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "forge",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the Forge — build it to unlock higher-tier gear crafting.",
    "description": "Open the Forge — build it to unlock higher-tier gear crafting.",
    "usage": "!forge",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "forget",
    "area": "admin",
    "status": "in-progress",
    "summary": "Flush the chat-memory cache for THIS channel.",
    "description": "Flush the chat-memory cache for THIS channel.",
    "usage": "!forget",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "from",
    "area": "other",
    "status": "finished",
    "summary": "Author a preset from a logged question: ``!aireview preset from <id> <answer>``.",
    "description": "Author a preset from a logged question: !aireview preset from <id> <answer>.",
    "usage": "!from",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!aireview preset from <id> <answer>"
    ],
    "planned": []
  },
  {
    "name": "games",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the Games hub — competitive games and channel activities.",
    "description": "Open the Games hub — competitive games and channel activities.",
    "usage": "!games",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Games program: theme-engine architecture + website-first provisioning"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "gear",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show your equipped gear, its condition, and the stats it grants.",
    "description": "Show your equipped gear, its condition, and the stats it grants.",
    "usage": "!gear",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "generalmenu",
    "area": "utility",
    "status": "finished",
    "summary": "Open the interactive General panel.",
    "description": "Entry-point command for the General subsystem panel.",
    "usage": "!generalmenu",
    "aliases": [
      "gmenu"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "givexp",
    "area": "progression",
    "status": "finished",
    "summary": "Give XP to a user (admin only).",
    "description": "Give XP to a user (admin only).",
    "usage": "!givexp",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "grant",
    "area": "economy",
    "status": "finished",
    "summary": "Disburse *amount* from the treasury to *member* (managers only).",
    "description": "Disburse *amount* from the treasury to *member* (managers only).",
    "usage": "!grant",
    "aliases": [
      "disburse",
      "payout"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "greet",
    "area": "utility",
    "status": "finished",
    "summary": "Greets you with a random greeting.",
    "description": "Greets you with a random greeting.",
    "usage": "!greet",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "grounding",
    "area": "games",
    "status": "in-progress",
    "summary": "Grounding facts that fed an AI response.",
    "description": "Grounding facts that fed an AI response.",
    "usage": "!grounding",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "health",
    "area": "other",
    "status": "finished",
    "summary": "Deterministic operational health snapshot (admin-gated, redacted).",
    "description": "Deterministic operational health snapshot (admin-gated, redacted).",
    "usage": "!health",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "help",
    "area": "utility",
    "status": "finished",
    "summary": "Shows available commands. Pass a category name for details.",
    "description": "Shows available commands. Pass a category name for details.",
    "usage": "!help",
    "aliases": [
      "hilfe"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "hero",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a hero.",
    "description": "Look up a hero.",
    "usage": "!hero",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "home",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the Home — build it to personalize your Character card.",
    "description": "Open the Home — build it to personalize your Character card.",
    "usage": "!home",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "identity",
    "area": "other",
    "status": "finished",
    "summary": "Run the identity-contract validator and show findings.",
    "description": "Run the identity-contract validator and show findings.",
    "usage": "!identity",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "ignore",
    "area": "other",
    "status": "finished",
    "summary": "Exclude a channel — its messages never enter the board.",
    "description": "Exclude a channel — its messages never enter the board.",
    "usage": "!ignore",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "imagemod",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Show the current image-moderation policy for this server.",
    "description": "Render the effective image-moderation policy (manage-guild only).",
    "usage": "!imagemod",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Meter image moderation under the Q-0082 AI spend ceiling (2026-06-16)"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "income",
    "area": "games",
    "status": "in-progress",
    "summary": "Verified cash earned per round (single round or a range).",
    "description": "Verified cash earned per round (single round or a range).",
    "usage": "!income",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "info",
    "area": "utility",
    "status": "finished",
    "summary": "Show server or user info. !info [server|user] [@mention]",
    "description": "Show server or user info. !info [server|user] [@mention]",
    "usage": "!info",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "inventory",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show your (or another user's) unified inventory hub.",
    "description": "Show your (or another user's) unified inventory hub.",
    "usage": "!inventory",
    "aliases": [
      "inv"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — a `check_subsystem_inventory_homed` guard (close the…"
      }
    ]
  },
  {
    "name": "invite",
    "area": "utility",
    "status": "finished",
    "summary": "Generate a one-use server invite.",
    "description": "Generate a one-use server invite.",
    "usage": "!invite",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "joblist",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show all jobs, requirements, and your mastery for each.",
    "description": "Show all jobs, requirements, and your mastery for each.",
    "usage": "!joblist",
    "aliases": [
      "jobs"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "joke",
    "area": "utility",
    "status": "finished",
    "summary": "Sends a random joke.",
    "description": "Sends a random joke.",
    "usage": "!joke",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "karma",
    "area": "progression",
    "status": "in-progress",
    "summary": "Show a member's karma standing: ``!karma [@user]``.",
    "description": "Show a member's karma standing: !karma [@user].",
    "usage": "!karma",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!karma [@user]"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — Karma (thanks/upvote reputation) system"
      }
    ]
  },
  {
    "name": "kick",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Kick a member from the server.",
    "description": "Kick a member from the server.",
    "usage": "!kick",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "latency",
    "area": "admin",
    "status": "finished",
    "summary": "Report the bot's WebSocket latency (admin detail view).",
    "description": "Report the bot's WebSocket latency (admin detail view).",
    "usage": "!latency",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!ping"
    ],
    "planned": []
  },
  {
    "name": "latest-data",
    "area": "games",
    "status": "in-progress",
    "summary": "Newest fact envelope per entity_kind.",
    "description": "Newest fact envelope per entity_kind.",
    "usage": "!latest-data",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "leaderboard",
    "area": "games",
    "status": "in-progress",
    "summary": "Show race / boss leaderboard.",
    "description": "Show race / boss leaderboard.",
    "usage": "!leaderboard",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "lifecycle",
    "area": "admin",
    "status": "finished",
    "summary": "Lifecycle state (phase, pending request, recent events).",
    "description": "Lifecycle state (phase, pending request, recent events).",
    "usage": "!lifecycle",
    "aliases": [
      "lc"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!platform lifecycle",
      "!diag",
      "!diagnostics"
    ],
    "planned": []
  },
  {
    "name": "list",
    "area": "games",
    "status": "finished",
    "summary": "List all active chains and word limits in the server.",
    "description": "List all active chains and word limits in the server.",
    "usage": "!list",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!chain list"
    ],
    "planned": []
  },
  {
    "name": "list_commands_detailed",
    "area": "admin",
    "status": "finished",
    "summary": "List all registered commands with details, paginated by cog.",
    "description": "List all registered commands with details, paginated by cog.",
    "usage": "!list_commands_detailed",
    "aliases": [
      "listcmds"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "listreactroles",
    "area": "management",
    "status": "in-progress",
    "summary": "List all active reaction roles in this server.",
    "description": "List all active reaction roles in this server.",
    "usage": "!listreactroles",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "live",
    "area": "games",
    "status": "in-progress",
    "summary": "Show recent live events (race/boss/ct/odyssey/event).",
    "description": "Show recent live events (race/boss/ct/odyssey/event).",
    "usage": "!live",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "loadall",
    "area": "admin",
    "status": "in-progress",
    "summary": "Load all unloaded cogs, skipping already-loaded ones.",
    "description": "Load all unloaded cogs, skipping already-loaded ones.",
    "usage": "!loadall",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "loadout",
    "area": "economy",
    "status": "in-progress",
    "summary": "Save / swap named gear loadouts (e.g. mining, combat, fishing).",
    "description": "Save / swap named gear loadouts (e.g. mining, combat, fishing).",
    "usage": "!loadout",
    "aliases": [
      "loadouts"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!loadout save <name>",
      "!loadout <name>",
      "!loadout apply <name>",
      "!loadout list",
      "!loadout delete <name>"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "lock",
    "area": "management",
    "status": "in-progress",
    "summary": "Lock a channel. Usage: !lock <name|id>",
    "description": "Lock a channel. Usage: !lock <name|id>",
    "usage": "!lock",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "locks",
    "area": "other",
    "status": "finished",
    "summary": "scope_locks snapshot; pass a prefix to filter (e.g. `counting`).",
    "description": "scope_locks snapshot; pass a prefix to filter (e.g. counting).",
    "usage": "!locks",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "logging",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the logging admin panel (S7d).",
    "description": "Open the logging admin panel (S7d).",
    "usage": "!logging",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      }
    ]
  },
  {
    "name": "loglevel",
    "area": "admin",
    "status": "in-progress",
    "summary": "Change the bot log level (DEBUG/INFO/WARNING/ERROR/CRITICAL).",
    "description": "Change the bot log level (DEBUG/INFO/WARNING/ERROR/CRITICAL).",
    "usage": "!loglevel",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "lookup",
    "area": "games",
    "status": "in-progress",
    "summary": "Resolve any Limbus name/term across every category.",
    "description": "Resolve any Limbus name/term across every category.",
    "usage": "!lookup",
    "aliases": [
      "search",
      "what"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "market",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show the mining market — sellable resources + the gear shop.",
    "description": "Show the mining market — sellable resources + the gear shop.",
    "usage": "!market",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "mechanic",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a combat mechanic (Clash / Speed / Sanity / …) (or list them all).",
    "description": "Look up a combat mechanic (Clash / Speed / Sanity / …) (or list them all).",
    "usage": "!mechanic",
    "aliases": [
      "mechanics",
      "combat"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "media",
    "area": "other",
    "status": "finished",
    "summary": "Content-free media (YouTube) diagnostics.",
    "description": "Content-free media (YouTube) diagnostics.",
    "usage": "!media",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "membercount",
    "area": "utility",
    "status": "finished",
    "summary": "Show this server's member count — humans, bots, and total.",
    "description": "Show this server's member count — humans, bots, and total.",
    "usage": "!membercount",
    "aliases": [
      "members"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "migrations",
    "area": "other",
    "status": "finished",
    "summary": "Platform migration checkpoints (Phase 2 PR-5) — status + summary.",
    "description": "Platform migration checkpoints (Phase 2 PR-5) — status + summary.",
    "usage": "!migrations",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "mine",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the grid Mine navigator — roam the world and dig.",
    "description": "Open the grid Mine navigator — roam the world and dig.",
    "usage": "!mine",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "mineinv",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show your unified inventory (compatibility alias for !inventory).",
    "description": "Show your unified inventory (compatibility alias for !inventory).",
    "usage": "!mineinv",
    "aliases": [
      "mineinventory"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "minemenu",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the mining hub panel.",
    "description": "Open the mining hub panel.",
    "usage": "!minemenu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "minestats",
    "area": "economy",
    "status": "in-progress",
    "summary": "Shows your total mining items and number of unique items.",
    "description": "Shows your total mining items and number of unique items.",
    "usage": "!minestats",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "mineworld",
    "area": "economy",
    "status": "in-progress",
    "summary": "Show this server's mining world seed; admins reseed (`!mineworld 12345`).",
    "description": "Show this server's mining world seed; admins reseed (!mineworld 12345).",
    "usage": "!mineworld",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!mineworld 12345"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "moderation",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Open the Moderation hub (moderator only).",
    "description": "Slash front door for the Moderation hub — ephemeral, mod-only.",
    "usage": "!moderation",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [
      "!modmenu"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "modlogs",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Show moderation log history for a member.",
    "description": "Show moderation log history for a member.",
    "usage": "!modlogs",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "modmenu",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Show the interactive moderation action panel.",
    "description": "Show the interactive moderation action panel.",
    "usage": "!modmenu",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "motivate",
    "area": "utility",
    "status": "finished",
    "summary": "Sends a motivational message.",
    "description": "Sends a motivational message.",
    "usage": "!motivate",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "move",
    "area": "management",
    "status": "in-progress",
    "summary": "Move a channel to a category. Usage: !move <channel name|id> <category name|id>",
    "description": "Move a channel to a category. Usage: !move <channel name|id> <category name|id>",
    "usage": "!move",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "myprofile",
    "area": "utility",
    "status": "finished",
    "summary": "View your per-server profile card.",
    "description": "View your per-server profile card.",
    "usage": "!myprofile",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "new",
    "area": "community",
    "status": "finished",
    "summary": "Open a ticket directly: ``!ticket new <subject>``.",
    "description": "Open a ticket directly: !ticket new <subject>.",
    "usage": "!new",
    "aliases": [
      "open",
      "create"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!ticket new <subject>"
    ],
    "planned": []
  },
  {
    "name": "off",
    "area": "other",
    "status": "finished",
    "summary": "Clear the review channel (entries are still recorded + queryable).",
    "description": "Clear the review channel (entries are still recorded + queryable).",
    "usage": "!off",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "ops",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 ingestion operations (staff readable; toggles are admin).",
    "description": "BTD6 ingestion operations (staff readable; toggles are admin).",
    "usage": "!ops",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "origins",
    "area": "games",
    "status": "in-progress",
    "summary": "Show every Sinner ↔ the literary work it is drawn from.",
    "description": "Show every Sinner ↔ the literary work it is drawn from.",
    "usage": "!origins",
    "aliases": [
      "origin",
      "literary"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "panel",
    "area": "other",
    "status": "finished",
    "summary": "Open the interactive starboard config panel.",
    "description": "Open the interactive starboard config panel.",
    "usage": "!panel",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "paragon",
    "area": "other",
    "status": "finished",
    "summary": "Open the BTD6 Paragon degree calculator.",
    "description": "Open the BTD6 Paragon degree calculator.",
    "usage": "!paragon",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "participation-schemas",
    "area": "other",
    "status": "finished",
    "summary": "Registered ParticipationSchema instances (Phase 1b).",
    "description": "Registered ParticipationSchema instances (Phase 1b).",
    "usage": "!participation-schemas",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "pay",
    "area": "economy",
    "status": "in-progress",
    "summary": "Send coins to another member. Usage: !pay @user <amount>",
    "description": "Send coins to another member. Usage: !pay @user <amount>",
    "usage": "!pay",
    "aliases": [
      "transfer"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "pending",
    "area": "games",
    "status": "in-progress",
    "summary": "List pending strategy submissions (staff-only).",
    "description": "List pending strategy submissions (staff-only).",
    "usage": "!pending",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "permissions",
    "area": "management",
    "status": "in-progress",
    "summary": "Modify channel permissions. Usage: !permissions <name|id> <@role> <allow/deny>",
    "description": "Modify channel permissions. Usage: !permissions <name|id> <@role> <allow/deny>",
    "usage": "!permissions",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "ping",
    "area": "utility",
    "status": "finished",
    "summary": "Check the bot's responsiveness — gateway + message round-trip.",
    "description": "Check the bot's responsiveness — gateway + message round-trip.",
    "usage": "!ping",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!latency"
    ],
    "planned": []
  },
  {
    "name": "platform",
    "area": "admin",
    "status": "finished",
    "summary": "Open the Platform / Diagnostics hub (administrator only).",
    "description": "Slash front door for the Platform hub — ephemeral, admin-only.",
    "usage": "!platform",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!platform"
    ],
    "planned": []
  },
  {
    "name": "pm",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the Project Moon (Limbus) browse panel.",
    "description": "Open the Project Moon (Limbus) browse panel.",
    "usage": "!pm",
    "aliases": [
      "limbus",
      "projectmoon"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "poker",
    "area": "games",
    "status": "finished",
    "summary": "Open a multiplayer Texas Hold'em table in this channel.",
    "description": "Open a multiplayer Texas Hold'em table in this channel.",
    "usage": "!poker",
    "aliases": [
      "holdem"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "policy",
    "area": "admin",
    "status": "in-progress",
    "summary": "Show the effective AI policy for a channel (dry-run resolver).",
    "description": "Show the effective AI policy for a channel (dry-run resolver).",
    "usage": "!policy",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "poll",
    "area": "utility",
    "status": "finished",
    "summary": "Create a simple reaction poll.",
    "description": "Create a simple reaction poll.",
    "usage": "!poll",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "preset",
    "area": "other",
    "status": "finished",
    "summary": "Manage vetted answer presets (served with zero model call).",
    "description": "Manage vetted answer presets (served with zero model call).",
    "usage": "!preset",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "prizemenu",
    "area": "moderation",
    "status": "finished",
    "summary": "Open the interactive prize channel management panel.",
    "description": "Open the interactive prize channel management panel.",
    "usage": "!prizemenu",
    "aliases": [],
    "permissions": "Staff",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "prizestatus",
    "area": "moderation",
    "status": "finished",
    "summary": "Show current #proof channel permissions.",
    "description": "Show current #proof channel permissions.",
    "usage": "!prizestatus",
    "aliases": [],
    "permissions": "Staff",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "providers",
    "area": "admin",
    "status": "in-progress",
    "summary": "The providers command.",
    "description": "The providers command.",
    "usage": "!providers",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "provisioning",
    "area": "other",
    "status": "finished",
    "summary": "Cross-linked ResourceRequirement × BindingSpec catalogue (S2.5).",
    "description": "Cross-linked ResourceRequirement × BindingSpec catalogue (S2.5).",
    "usage": "!provisioning",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "query_logs",
    "area": "admin",
    "status": "finished",
    "summary": "Query recent logs from the logs table. !query_logs [INFO|ERROR|...] [limit]",
    "description": "Query recent logs from the logs table. !query_logs [INFO|ERROR|...] [limit]",
    "usage": "!query_logs",
    "aliases": [
      "querylogs"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "quickcraft",
    "area": "economy",
    "status": "in-progress",
    "summary": "Re-craft the last gear item that broke and equip it.",
    "description": "Re-craft the last gear item that broke and equip it.",
    "usage": "!quickcraft",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "quote",
    "area": "utility",
    "status": "finished",
    "summary": "Sends a random famous quote.",
    "description": "Sends a random famous quote.",
    "usage": "!quote",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "rank",
    "area": "progression",
    "status": "finished",
    "summary": "Show rank in a category.",
    "description": "Show rank in a category.",
    "usage": "!rank",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!rank",
      "!rank xp|coins|both",
      "!rank @user",
      "!rank @user xp|coins",
      "!rank <category>"
    ],
    "planned": []
  },
  {
    "name": "rbe",
    "area": "games",
    "status": "in-progress",
    "summary": "RBE per round — base + freeplay-scaled (single round or a range).",
    "description": "RBE per round — base + freeplay-scaled (single round or a range).",
    "usage": "!rbe",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "reactroles",
    "area": "management",
    "status": "in-progress",
    "summary": "Attach a reaction role to a message. Usage: !reactroles <message_id> <emoji> <@role>",
    "description": "Attach a reaction role to a message. Usage: !reactroles <message_id> <emoji> <@role>",
    "usage": "!reactroles",
    "aliases": [
      "reaktionsrollen"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "readiness",
    "area": "admin",
    "status": "in-progress",
    "summary": "Run the full AI readiness chain check.",
    "description": "Run the full AI readiness chain check.",
    "usage": "!readiness",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "recent_errors",
    "area": "admin",
    "status": "finished",
    "summary": "Retrieve the most recent ERROR-level log entries.",
    "description": "Retrieve the most recent ERROR-level log entries.",
    "usage": "!recent_errors",
    "aliases": [
      "errors"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "refresh-source",
    "area": "games",
    "status": "in-progress",
    "summary": "Manually refresh one Ninja Kiwi source (staff-only).",
    "description": "Manually refresh one Ninja Kiwi source (staff-only).",
    "usage": "!refresh-source",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "refreshmembers",
    "area": "management",
    "status": "in-progress",
    "summary": "Force-fetch all members from Discord.",
    "description": "Force-fetch all members from Discord.",
    "usage": "!refreshmembers",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "relic",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a Contested Territory relic's effect and tile.",
    "description": "Look up a Contested Territory relic's effect and tile.",
    "usage": "!relic",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "remind",
    "area": "utility",
    "status": "finished",
    "summary": "Set a reminder. !remind <minutes> <message>",
    "description": "Set a reminder. !remind <minutes> <message>",
    "usage": "!remind",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "remove",
    "area": "community",
    "status": "finished",
    "summary": "Remove a member from this ticket (staff).",
    "description": "Remove a member from this ticket (staff).",
    "usage": "!remove",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "removelimit",
    "area": "games",
    "status": "finished",
    "summary": "Remove the word limit from a specified channel or the current channel if none is provided.",
    "description": "Remove the word limit from a specified channel or the current channel if none is provided.",
    "usage": "!removelimit",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!chain removelimit [channel]"
    ],
    "planned": []
  },
  {
    "name": "removereactrole",
    "area": "management",
    "status": "in-progress",
    "summary": "Remove a reaction role binding. Usage: !removereactrole <message_id> <emoji>",
    "description": "Remove a reaction role binding. Usage: !removereactrole <message_id> <emoji>",
    "usage": "!removereactrole",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "rename",
    "area": "management",
    "status": "in-progress",
    "summary": "Rename a channel. Usage: !rename <old name|id> <new_name>",
    "description": "Rename a channel. Usage: !rename <old name|id> <new_name>",
    "usage": "!rename",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "repair",
    "area": "economy",
    "status": "in-progress",
    "summary": "Repair a worn gear item for coins (e.g. `!repair pickaxe`).",
    "description": "Repair a worn gear item for coins (e.g. !repair pickaxe).",
    "usage": "!repair",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!repair pickaxe"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "reset_count",
    "area": "games",
    "status": "finished",
    "summary": "Resets the count to the starting value.",
    "description": "Resets the count to the starting value.",
    "usage": "!reset_count",
    "aliases": [
      "rc"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "reset_inventory",
    "area": "economy",
    "status": "in-progress",
    "summary": "Admin-only: reset a user's inventory in THIS guild (PR M3 — guild-scoped).",
    "description": "Admin-only: reset a user's inventory in THIS guild (PR M3 — guild-scoped).",
    "usage": "!reset_inventory",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "resetxp",
    "area": "progression",
    "status": "finished",
    "summary": "Reset a user's XP to zero (admin only).",
    "description": "Reset a user's XP to zero (admin only).",
    "usage": "!resetxp",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "resolve",
    "area": "other",
    "status": "finished",
    "summary": "Mark one review entry reviewed: ``!aireview resolve <id>``.",
    "description": "Mark one review entry reviewed: !aireview resolve <id>.",
    "usage": "!resolve",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!aireview resolve <id>"
    ],
    "planned": []
  },
  {
    "name": "resource-requirements",
    "area": "other",
    "status": "finished",
    "summary": "Declared ResourceRequirement entries across subsystems (Phase 1c).",
    "description": "Declared ResourceRequirement entries across subsystems (Phase 1c).",
    "usage": "!resource-requirements",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "resources",
    "area": "other",
    "status": "finished",
    "summary": "Resource runtime (Phase 2a) — taxonomy + cached status histogram.",
    "description": "Resource runtime (Phase 2a) — taxonomy + cached status histogram.",
    "usage": "!resources",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "restart",
    "area": "admin",
    "status": "in-progress",
    "summary": "Request a graceful restart through the lifecycle service.",
    "description": "Request a graceful restart through the lifecycle service.",
    "usage": "!restart",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [
      "!restart"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "rod",
    "area": "games",
    "status": "in-progress",
    "summary": "View your fishing rod and upgrade it for coins.",
    "description": "View your fishing rod and upgrade it for coins.",
    "usage": "!rod",
    "aliases": [
      "rodshop",
      "buyrod"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "rodrecipes",
    "area": "games",
    "status": "in-progress",
    "summary": "Browse every fish→rod recipe and your live progress toward each tier.",
    "description": "Browse every fish→rod recipe and your live progress toward each tier.",
    "usage": "!rodrecipes",
    "aliases": [
      "rodrecipe",
      "rrecipes"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "rolecreator",
    "area": "management",
    "status": "in-progress",
    "summary": "Open the role hub (use !roles instead).",
    "description": "Open the role hub (use !roles instead).",
    "usage": "!rolecreator",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "roleinfo",
    "area": "management",
    "status": "in-progress",
    "summary": "Show a role's details. Usage: !roleinfo <@role|name|id>",
    "description": "Read-only role detail card — the role sibling of !channelinfo / !info user.",
    "usage": "!roleinfo",
    "aliases": [
      "ri"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "rolemenu",
    "area": "management",
    "status": "in-progress",
    "summary": "Open the role hub (use !roles instead).",
    "description": "Open the role hub (use !roles instead).",
    "usage": "!rolemenu",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "roles",
    "area": "management",
    "status": "in-progress",
    "summary": "Open the role management hub.",
    "description": "Open the role management hub.",
    "usage": "!roles",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "rolesettings",
    "area": "management",
    "status": "in-progress",
    "summary": "Open the role management hub (alias for !roles).",
    "description": "Open the role management hub (alias for !roles).",
    "usage": "!rolesettings",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "round",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a round, or a values table across a range of rounds.",
    "description": "Look up a round, or a values table across a range of rounds.",
    "usage": "!round",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "routes",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the Phase 9b Routes subpage directly.",
    "description": "Open the Phase 9b Routes subpage directly.",
    "usage": "!routes",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      }
    ]
  },
  {
    "name": "routing",
    "area": "admin",
    "status": "in-progress",
    "summary": "The routing command.",
    "description": "The routing command.",
    "usage": "!routing",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "rps",
    "area": "games",
    "status": "in-progress",
    "summary": "Quick RPS. !rps [bet] or !rps @player [bet]",
    "description": "Quick RPS. !rps [bet] or !rps @player [bet]",
    "usage": "!rps",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpsbot",
    "area": "games",
    "status": "in-progress",
    "summary": "Starts matches against the bot. Delegator — see _bot_matches.",
    "description": "Starts matches against the bot. Delegator — see _bot_matches.",
    "usage": "!rpsbot",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpshelp",
    "area": "games",
    "status": "in-progress",
    "summary": "Displays help information for RPS tournament commands.",
    "description": "Displays help information for RPS tournament commands.",
    "usage": "!rpshelp",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpsmatchup",
    "area": "games",
    "status": "in-progress",
    "summary": "Manually creates a match between two specific members.",
    "description": "Manually creates a match between two specific members.",
    "usage": "!rpsmatchup",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpsregister",
    "area": "games",
    "status": "in-progress",
    "summary": "Starts the registration period with a reaction role message. !rpsregister [@role] [entry_fee]",
    "description": "Starts the registration period with a reaction role message. !rpsregister [@role] [entry_fee]",
    "usage": "!rpsregister",
    "aliases": [
      "rpsreg"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpssettings",
    "area": "games",
    "status": "in-progress",
    "summary": "Updates bot settings.",
    "description": "Updates bot settings.",
    "usage": "!rpssettings",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "rpsstart",
    "area": "games",
    "status": "in-progress",
    "summary": "Starts the RPS tournament. Usage: !rps_start [mode] [best_of]",
    "description": "Starts the RPS tournament. Usage: !rps_start [mode] [best_of]",
    "usage": "!rpsstart",
    "aliases": [
      "rpsbegin"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — refactor RPS tournament orchestration out of the cog"
      }
    ]
  },
  {
    "name": "runs",
    "area": "games",
    "status": "in-progress",
    "summary": "Show recent BTD6 ingestion runs.",
    "description": "Show recent BTD6 ingestion runs.",
    "usage": "!runs",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "runtime",
    "area": "other",
    "status": "finished",
    "summary": "High-level runtime snapshot: every registered diagnostic provider.",
    "description": "High-level runtime snapshot: every registered diagnostic provider.",
    "usage": "!runtime",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "sail",
    "area": "games",
    "status": "in-progress",
    "summary": "Set sail for deepwater (or return to shore) — toggles your fishing venue.",
    "description": "Set sail for deepwater (or return to shore) — toggles your fishing venue.",
    "usage": "!sail",
    "aliases": [
      "setsail"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!fish"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "schemas",
    "area": "other",
    "status": "finished",
    "summary": "Registered SubsystemSchema instances (Phase 1a).",
    "description": "Registered SubsystemSchema instances (Phase 1a).",
    "usage": "!schemas",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "security",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Show the current server-security policy (raid + account-age).",
    "description": "Render the effective security policy (admin/manage-guild only).",
    "usage": "!security",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "seed-data",
    "area": "games",
    "status": "in-progress",
    "summary": "Seed the Postgres data store from the bundled files (admin).",
    "description": "Seed the Postgres data store from the bundled files (admin).",
    "usage": "!seed-data",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "selfstar",
    "area": "other",
    "status": "finished",
    "summary": "Count the author's own ⭐? ``!starboard selfstar on|off`` (default off).",
    "description": "Count the author's own ⭐? !starboard selfstar on|off (default off).",
    "usage": "!selfstar",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!starboard selfstar on|off"
    ],
    "planned": []
  },
  {
    "name": "sell",
    "area": "economy",
    "status": "in-progress",
    "summary": "Sell raw resources for coins (e.g. `!sell diamond 5`).",
    "description": "Sell raw resources for coins (e.g. !sell diamond 5).",
    "usage": "!sell",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sell diamond 5"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "sellall",
    "area": "economy",
    "status": "in-progress",
    "summary": "Sell every raw resource in your inventory for coins.",
    "description": "Sell every raw resource in your inventory for coins.",
    "usage": "!sellall",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "server-management",
    "area": "admin",
    "status": "finished",
    "summary": "Open the Server Management hub (moderation, channels, roles, cleanup, setup).",
    "description": "Ephemeral slash front door for the Server Management hub.",
    "usage": "!server-management",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "serverinfo",
    "area": "utility",
    "status": "finished",
    "summary": "Alias for !info server.",
    "description": "Alias for !info server.",
    "usage": "!serverinfo",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "servermanagement",
    "area": "admin",
    "status": "finished",
    "summary": "Open the unified Server Management hub.",
    "description": "Open the unified Server Management hub.",
    "usage": "!servermanagement",
    "aliases": [
      "servermenu",
      "guildmenu"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "serverstats",
    "area": "admin",
    "status": "in-progress",
    "summary": "Display server statistics.",
    "description": "Display server statistics.",
    "usage": "!serverstats",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "sessions",
    "area": "other",
    "status": "finished",
    "summary": "Active session counts (DB-backed); optionally filtered by subsystem.",
    "description": "Active session counts (DB-backed); optionally filtered by subsystem.",
    "usage": "!sessions",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "set",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the channel-select view for ``mod`` or ``cleanup`` binding.",
    "description": "Open the channel-select view for mod or cleanup binding.",
    "usage": "!set",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      }
    ]
  },
  {
    "name": "set_skip_numbers",
    "area": "games",
    "status": "finished",
    "summary": "Set the skip step N for a 'skip' match (count climbs 1, 1+N, 1+2N, …).",
    "description": "Set the skip step N for a 'skip' match (count climbs 1, 1+N, 1+2N, …).",
    "usage": "!set_skip_numbers",
    "aliases": [
      "ssn"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setlimit",
    "area": "games",
    "status": "finished",
    "summary": "Set a word limit in a specified channel or the current channel if none is provided.",
    "description": "Set a word limit in a specified channel or the current channel if none is provided.",
    "usage": "!setlimit",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!chain setlimit [channel] <number>"
    ],
    "planned": []
  },
  {
    "name": "setlogchannel",
    "area": "economy",
    "status": "in-progress",
    "summary": "Set the economy log channel. Usage: !setlogchannel #channel",
    "description": "Set the economy log channel. Usage: !setlogchannel #channel",
    "usage": "!setlogchannel",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "setrole",
    "area": "management",
    "status": "in-progress",
    "summary": "Add or update a time-based role threshold.",
    "description": "Add or update a time-based role threshold.",
    "usage": "!setrole",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "setting",
    "area": "other",
    "status": "finished",
    "summary": "Explain one scalar setting for this guild.",
    "description": "Explain one scalar setting for this guild.",
    "usage": "!setting",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!platform flag"
    ],
    "planned": []
  },
  {
    "name": "settings",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the AI Platform settings panel directly.",
    "description": "Open the AI Platform settings panel directly.",
    "usage": "!settings",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "settings-registry",
    "area": "other",
    "status": "finished",
    "summary": "Declared SettingSpec catalogue + this guild's current values (S1).",
    "description": "Declared SettingSpec catalogue + this guild's current values (S1).",
    "usage": "!settings-registry",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup",
    "area": "other",
    "status": "finished",
    "summary": "Open Essential Setup — a few simple steps, each saved instantly.",
    "description": "Open Essential Setup — a few simple steps, each saved instantly.",
    "usage": "!setup",
    "aliases": [
      "quicksetup",
      "essentialsetup"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-advanced",
    "area": "other",
    "status": "finished",
    "summary": "Open the advanced setup wizard (power users; /setup is the quick one).",
    "description": "Ephemeral slash front door for the advanced (linear) setup wizard.",
    "usage": "!setup-advanced",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-delegate",
    "area": "other",
    "status": "finished",
    "summary": "Grant a member delegated setup-admin authority (owner only).",
    "description": "Add member to the guild's delegated_admins set.",
    "usage": "!setup-delegate",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-depth",
    "area": "other",
    "status": "finished",
    "summary": "Pick the wizard depth (owner/delegated admin only).",
    "description": "Set the persisted wizard depth without opening the hub.",
    "usage": "!setup-depth",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-describe",
    "area": "other",
    "status": "finished",
    "summary": "Describe your server; the AI proposes a setup plan to review.",
    "description": "Ephemeral natural-language setup proposal (admin-gated).",
    "usage": "!setup-describe",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-hub",
    "area": "other",
    "status": "finished",
    "summary": "Open the legacy section-list hub (compat).",
    "description": "Legacy section-list hub.",
    "usage": "!setup-hub",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-readiness",
    "area": "other",
    "status": "finished",
    "summary": "Per-guild setup-readiness inventory (PR H).",
    "description": "Per-guild setup-readiness inventory (PR H).",
    "usage": "!setup-readiness",
    "aliases": [
      "readiness",
      "ready"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-reset",
    "area": "other",
    "status": "finished",
    "summary": "Clear all staged setup operations (owner/delegated admin only).",
    "description": "Clear the per-guild setup draft without dismissing the session.",
    "usage": "!setup-reset",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-skip",
    "area": "other",
    "status": "finished",
    "summary": "Mark a setup section as skipped (owner/delegated admin only).",
    "description": "Add section to the session's skipped_sections set.",
    "usage": "!setup-skip",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-status",
    "area": "other",
    "status": "finished",
    "summary": "Quick at-a-glance setup state (read-only).",
    "description": "Ephemeral read-only status view.",
    "usage": "!setup-status",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-undelegate",
    "area": "other",
    "status": "finished",
    "summary": "Revoke delegated setup-admin authority (owner only).",
    "description": "Drop member from the guild's delegated_admins set.",
    "usage": "!setup-undelegate",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setup-unskip",
    "area": "other",
    "status": "finished",
    "summary": "Remove a section from the skipped set (owner/delegated admin only).",
    "description": "Drop section from the session's skipped_sections set.",
    "usage": "!setup-unskip",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "setupadvanced",
    "area": "other",
    "status": "finished",
    "summary": "Open or resume the advanced (linear) setup wizard.",
    "description": "Open or resume the advanced (linear) setup wizard.",
    "usage": "!setupadvanced",
    "aliases": [
      "advancedsetup"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!setup"
    ],
    "planned": []
  },
  {
    "name": "setupdescribe",
    "area": "other",
    "status": "finished",
    "summary": "Describe your server in words; propose how to wire it to the bot.",
    "description": "Describe your server in words; propose how to wire it to the bot.",
    "usage": "!setupdescribe",
    "aliases": [
      "describesetup"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "shop",
    "area": "economy",
    "status": "in-progress",
    "summary": "Browse and buy items from the shop.",
    "description": "Browse and buy items from the shop.",
    "usage": "!shop",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "sin",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up one of the 7 Sin affinities (or list them all).",
    "description": "Look up one of the 7 Sin affinities (or list them all).",
    "usage": "!sin",
    "aliases": [
      "sins",
      "affinity"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "sinner",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up one of the 12 Sinners (or list them all).",
    "description": "Look up one of the 12 Sinners (or list them all).",
    "usage": "!sinner",
    "aliases": [
      "sinners"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Project Moon wiki as a bot knowledge domain — feasibility (2026-06-21)"
      }
    ]
  },
  {
    "name": "skill",
    "area": "economy",
    "status": "in-progress",
    "summary": "Spend a skill point into a branch (e.g. `!skill mining`).",
    "description": "Spend a skill point into a branch (e.g. !skill mining).",
    "usage": "!skill",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!skill mining"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "skills",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open your skill tree — spend points to specialize your character.",
    "description": "Open your skill tree — spend points to specialize your character.",
    "usage": "!skills",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "slashes",
    "area": "admin",
    "status": "in-progress",
    "summary": "List currently-registered slash commands (admin only).",
    "description": "List currently-registered slash commands (admin only).",
    "usage": "!slashes",
    "aliases": [
      "slashlist"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "slow",
    "area": "other",
    "status": "finished",
    "summary": "Show the most recent slow-path entries (S3.2 ring buffer).",
    "description": "Show the most recent slow-path entries (S3.2 ring buffer).",
    "usage": "!slow",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "slowmode",
    "area": "management",
    "status": "in-progress",
    "summary": "Set a channel's slowmode. Usage: !slowmode <name|id> <seconds> (0 disables; max 21600 = 6h)",
    "description": "Set a channel's slowmode. Usage: !slowmode <name|id> <seconds> (0 disables; max 21600 = 6h)",
    "usage": "!slowmode",
    "aliases": [
      "slow"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "source-health",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 source registry freshness overview.",
    "description": "BTD6 source registry freshness overview.",
    "usage": "!source-health",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "source_disable",
    "area": "games",
    "status": "in-progress",
    "summary": "Disable a BTD6 ingestion source (administrator only).",
    "description": "Disable a BTD6 ingestion source (administrator only).",
    "usage": "!source_disable",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "source_enable",
    "area": "games",
    "status": "in-progress",
    "summary": "Enable a BTD6 ingestion source (administrator only).",
    "description": "Enable a BTD6 ingestion source (administrator only).",
    "usage": "!source_enable",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "sources",
    "area": "games",
    "status": "in-progress",
    "summary": "List BTD6 source registry rows.",
    "description": "List BTD6 source registry rows.",
    "usage": "!sources",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "spotlight",
    "area": "community",
    "status": "finished",
    "summary": "Show the Community Spotlight — live XP, coins, games, and level-ups.",
    "description": "Show the Community Spotlight — live XP, coins, games, and level-ups.",
    "usage": "!spotlight",
    "aliases": [
      "activity"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "starboard",
    "area": "other",
    "status": "finished",
    "summary": "Show or set the hall-of-fame channel + star threshold.",
    "description": "Show or set the hall-of-fame channel + star threshold.",
    "usage": "!starboard",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!starboard",
      "!starboard #channel [n]",
      "!starboard off"
    ],
    "planned": []
  },
  {
    "name": "start_match",
    "area": "games",
    "status": "finished",
    "summary": "Starts a new counting match with the specified mode.",
    "description": "Starts a new counting match with the specified mode.",
    "usage": "!start_match",
    "aliases": [
      "sm"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "startup",
    "area": "other",
    "status": "finished",
    "summary": "Settled-startup health report (extension load, gateway, DB, …).",
    "description": "Settled-startup health report (extension load, gateway, DB, …).",
    "usage": "!startup",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "stash",
    "area": "economy",
    "status": "in-progress",
    "summary": "Deposit an item into your vault (e.g. `!stash diamond 5`).",
    "description": "Deposit an item into your vault (e.g. !stash diamond 5).",
    "usage": "!stash",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!stash diamond 5"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "status",
    "area": "admin",
    "status": "in-progress",
    "summary": "The status command.",
    "description": "The status command.",
    "usage": "!status",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "strat",
    "area": "games",
    "status": "in-progress",
    "summary": "BTD6 strategy memory — browse, submit, review.",
    "description": "BTD6 strategy memory (browse / submit / review).",
    "usage": "!strat",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "strategies",
    "area": "games",
    "status": "in-progress",
    "summary": "List strategy memory entries available in this guild.",
    "description": "List strategy memory entries available in this guild.",
    "usage": "!strategies",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "strategy",
    "area": "games",
    "status": "in-progress",
    "summary": "Show one strategy in detail.",
    "description": "Show one strategy in detail.",
    "usage": "!strategy",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "strategy-audit",
    "area": "games",
    "status": "in-progress",
    "summary": "Per-strategy audit log.",
    "description": "Per-strategy audit log.",
    "usage": "!strategy-audit",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "submit",
    "area": "games",
    "status": "in-progress",
    "summary": "Submit a BTD6 strategy.",
    "description": "Submit a BTD6 strategy.",
    "usage": "!submit",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "support-report",
    "area": "admin",
    "status": "in-progress",
    "summary": "Render a copy-pasteable support report from recent audit (PR-H).",
    "description": "Render a copy-pasteable support report from recent audit (PR-H).",
    "usage": "!support-report",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "syncslash",
    "area": "admin",
    "status": "in-progress",
    "summary": "Sync the app-command tree for slash commands (owner only).",
    "description": "Sync the app-command tree for slash commands (owner only).",
    "usage": "!syncslash",
    "aliases": [
      "syncs"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "system_info",
    "area": "admin",
    "status": "finished",
    "summary": "Display system-level stats.",
    "description": "Display system-level stats.",
    "usage": "!system_info",
    "aliases": [
      "sysinfo"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "tasks",
    "area": "other",
    "status": "finished",
    "summary": "Managed background-task snapshot (core.runtime.tasks).",
    "description": "Managed background-task snapshot (core.runtime.tasks).",
    "usage": "!tasks",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "temprole",
    "area": "other",
    "status": "finished",
    "summary": "Give a member a role for a limited time. Usage: !temprole @member 2h @role",
    "description": "Give a member a role for a limited time. Usage: !temprole @member 2h @role",
    "usage": "!temprole",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "temproles",
    "area": "other",
    "status": "finished",
    "summary": "List active temporary roles. Usage: !temproles (yours) or !temproles @member (staff).",
    "description": "List active temporary roles. Usage: !temproles (yours) or !temproles @member (staff).",
    "usage": "!temproles",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "test",
    "area": "admin",
    "status": "in-progress",
    "summary": "Send a synthetic warn embed to the configured log channel.",
    "description": "Send a synthetic warn embed to the configured log channel.",
    "usage": "!test",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      }
    ]
  },
  {
    "name": "test-intent",
    "area": "games",
    "status": "in-progress",
    "summary": "Show what the resolver extracted from a message.",
    "description": "Show what the resolver extracted from a message.",
    "usage": "!test-intent",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "test_notification",
    "area": "admin",
    "status": "finished",
    "summary": "Send a test notification via the webhook reporter.",
    "description": "Send a test notification via the webhook reporter.",
    "usage": "!test_notification",
    "aliases": [
      "testnotify"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "thanks",
    "area": "progression",
    "status": "in-progress",
    "summary": "Give a karma point to a helpful member: ``!thanks @user [reason]``.",
    "description": "Give a karma point to a helpful member: !thanks @user [reason].",
    "usage": "!thanks",
    "aliases": [
      "rep",
      "thank"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!thanks @user [reason]"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Idea — Karma (thanks/upvote reputation) system"
      }
    ]
  },
  {
    "name": "ticket",
    "area": "community",
    "status": "finished",
    "summary": "Open the ticket hub — open a ticket or view your open tickets.",
    "description": "Open the ticket hub — open a ticket or view your open tickets.",
    "usage": "!ticket",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "ticketblacklist",
    "area": "community",
    "status": "finished",
    "summary": "Manage who may open tickets: ``!ticketblacklist add|remove @user``.",
    "description": "Manage who may open tickets: !ticketblacklist add|remove @user.",
    "usage": "!ticketblacklist",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!ticketblacklist add|remove @user"
    ],
    "planned": []
  },
  {
    "name": "ticketlimit",
    "area": "community",
    "status": "finished",
    "summary": "Set the max simultaneously-open tickets per member (managers).",
    "description": "Set the max simultaneously-open tickets per member (managers).",
    "usage": "!ticketlimit",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "ticketpanel",
    "area": "community",
    "status": "finished",
    "summary": "Post the public ticket launcher panel in this channel (managers).",
    "description": "Post the public ticket launcher panel in this channel (managers).",
    "usage": "!ticketpanel",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "ticketsetup",
    "area": "community",
    "status": "finished",
    "summary": "Configure tickets — opens a button/dropdown panel (managers).",
    "description": "Configure tickets — opens a button/dropdown panel (managers).",
    "usage": "!ticketsetup",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!ticketsetup @StaffRole [#log-channel]"
    ],
    "planned": []
  },
  {
    "name": "tidepool",
    "area": "games",
    "status": "in-progress",
    "summary": "Build a Tide Pool — the deepwater-coral structure that pulls rarer catches.",
    "description": "Build a Tide Pool — the deepwater-coral structure that pulls rarer catches.",
    "usage": "!tidepool",
    "aliases": [
      "reef",
      "tidepools"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!sail",
      "!curios"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "timedprize",
    "area": "moderation",
    "status": "finished",
    "summary": "Grant timed access to #proof; auto-unlocks after duration minutes. Usage: timedprize @winner <minutes>",
    "description": "Grant timed access to #proof; auto-unlocks after duration minutes. Usage: timedprize @winner <minutes>",
    "usage": "!timedprize",
    "aliases": [],
    "permissions": "Staff",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "timeout",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Timeout a member for a given number of minutes.",
    "description": "Timeout a member for a given number of minutes.",
    "usage": "!timeout",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "titles",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open your titles — equip an earned title on your Character card.",
    "description": "Open your titles — equip an earned title on your Character card.",
    "usage": "!titles",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "toggle_reset_on_wrong_count",
    "area": "games",
    "status": "finished",
    "summary": "Toggles the 'reset on wrong count' feature.",
    "description": "Toggles the 'reset on wrong count' feature.",
    "usage": "!toggle_reset_on_wrong_count",
    "aliases": [
      "trwc"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "toggle_turns",
    "area": "games",
    "status": "finished",
    "summary": "Toggles the 'taking turns' mode.",
    "description": "Toggles the 'taking turns' mode.",
    "usage": "!toggle_turns",
    "aliases": [
      "tt"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "topic",
    "area": "management",
    "status": "in-progress",
    "summary": "Set a channel's topic. Usage: !topic <name|id> <text> (omit text to clear)",
    "description": "Set a channel's topic. Usage: !topic <name|id> <text> (omit text to clear)",
    "usage": "!topic",
    "aliases": [
      "settopic"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "tower",
    "area": "games",
    "status": "in-progress",
    "summary": "Look up a tower.",
    "description": "Look up a tower.",
    "usage": "!tower",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "BTD6 runtime/simulation mechanics — extract straight from the game"
      },
      {
        "status": "idea",
        "title": "Idea — enrich the BTD6 CT event detail with relics + the hex map"
      },
      {
        "status": "idea",
        "title": "BTD6 community-shorthand corpus eval (router-class regression guard)"
      }
    ]
  },
  {
    "name": "treasury",
    "area": "economy",
    "status": "finished",
    "summary": "Open the server treasury — view the pool and contribute coins.",
    "description": "Open the server treasury — view the pool and contribute coins.",
    "usage": "!treasury",
    "aliases": [
      "bank",
      "pool"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "trivia",
    "area": "utility",
    "status": "finished",
    "summary": "Asks a trivia question with a reveal button.",
    "description": "Asks a trivia question with a reveal button.",
    "usage": "!trivia",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "trophies",
    "area": "games",
    "status": "in-progress",
    "summary": "Show this server's heaviest catches — the biggest-fish hall of fame.",
    "description": "Show this server's heaviest catches — the biggest-fish hall of fame.",
    "usage": "!trophies",
    "aliases": [
      "bigfish",
      "fishtrophy"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      }
    ]
  },
  {
    "name": "unban",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Unban a user by their Discord user ID.",
    "description": "Unban a user by their Discord user ID.",
    "usage": "!unban",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "unequip",
    "area": "economy",
    "status": "in-progress",
    "summary": "Clear an equipment slot (tool, light, charm, or a combat piece).",
    "description": "Clear an equipment slot (tool, light, charm, or a combat piece).",
    "usage": "!unequip",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "unignore",
    "area": "other",
    "status": "finished",
    "summary": "Stop ignoring a channel (messages there can enter the board again).",
    "description": "Stop ignoring a channel (messages there can enter the board again).",
    "usage": "!unignore",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "unloadall",
    "area": "admin",
    "status": "in-progress",
    "summary": "Unload all loaded cogs except this one.",
    "description": "Unload all loaded cogs except this one.",
    "usage": "!unloadall",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Central admin guild + central logging guild — the bot's HQ…"
      }
    ]
  },
  {
    "name": "unlock",
    "area": "management",
    "status": "in-progress",
    "summary": "Unlock a channel. Usage: !unlock <name|id>",
    "description": "Unlock a channel. Usage: !unlock <name|id>",
    "usage": "!unlock",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      }
    ]
  },
  {
    "name": "unsetrole",
    "area": "management",
    "status": "in-progress",
    "summary": "Remove a role from time-based assignment.",
    "description": "Remove a role from time-based assignment.",
    "usage": "!unsetrole",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Channel-level, role-scoped access is missing — live bot AND the…"
      },
      {
        "status": "idea",
        "title": "Idea — the off-Discord websites: rebuild disposition, cutover role…"
      },
      {
        "status": "idea",
        "title": "Channel-deployed component-menu primitive (role menus · starboard ·…"
      }
    ]
  },
  {
    "name": "unstash",
    "area": "economy",
    "status": "in-progress",
    "summary": "Withdraw an item from your vault (e.g. `!unstash diamond 5`).",
    "description": "Withdraw an item from your vault (e.g. !unstash diamond 5).",
    "usage": "!unstash",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!unstash diamond 5"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "use",
    "area": "economy",
    "status": "in-progress",
    "summary": "Use a special item from your inventory (e.g., torch, dynamite).",
    "description": "Use a special item from your inventory (e.g., torch, dynamite).",
    "usage": "!use",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "userinfo",
    "area": "utility",
    "status": "finished",
    "summary": "Alias for !info user [@member].",
    "description": "Alias for !info user [@member].",
    "usage": "!userinfo",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "utility",
    "area": "utility",
    "status": "finished",
    "summary": "Open the Utility hub (server info, polls, reminders).",
    "description": "Slash front door for the Utility hub — ephemeral.",
    "usage": "!utility",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "utilitymenu",
    "area": "utility",
    "status": "finished",
    "summary": "Open the interactive utility panel.",
    "description": "Open the interactive utility panel.",
    "usage": "!utilitymenu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "uxlab",
    "area": "admin",
    "status": "in-progress",
    "summary": "Open the UX Lab — the interface gallery + limit probe bench.",
    "description": "Open the UX Lab — the interface gallery + limit probe bench.",
    "usage": "!uxlab",
    "aliases": [
      "interfacelab"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "UX Lab / Interface Gallery — a living Discord-UX sandbox cog"
      }
    ]
  },
  {
    "name": "validate_json_files",
    "area": "admin",
    "status": "finished",
    "summary": "Validate the structure of all JSON files in the data directory.",
    "description": "Validate the structure of all JSON files in the data directory.",
    "usage": "!validate_json_files",
    "aliases": [
      "validatejson"
    ],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "vault",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open your vault — a safe stash separate from your mining pack.",
    "description": "Open your vault — a safe stash separate from your mining pack.",
    "usage": "!vault",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "vaultupgrade",
    "area": "economy",
    "status": "in-progress",
    "summary": "Buy one vault-capacity tier with coins (e.g. more room to stash).",
    "description": "Buy one vault-capacity tier with coins (e.g. more room to stash).",
    "usage": "!vaultupgrade",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "views",
    "area": "other",
    "status": "finished",
    "summary": "Registered PersistentView classes (by subsystem).",
    "description": "Registered PersistentView classes (by subsystem).",
    "usage": "!views",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "warn",
    "area": "moderation",
    "status": "in-progress",
    "summary": "Warn a user. Escalates at the configured threshold (default: timeout).",
    "description": "Warn a user. Escalates at the configured threshold (default: timeout).",
    "usage": "!warn",
    "aliases": [],
    "permissions": "Moderator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Moderation feature gaps versus competitor bots (researched, most…"
      },
      {
        "status": "idea",
        "title": "Idea — server-owner-configurable moderation/warning DMs"
      },
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Server safety, automod, logging, and image moderation (2026-06-12)"
      }
    ]
  },
  {
    "name": "welcome",
    "area": "community",
    "status": "in-progress",
    "summary": "Show the current welcome (greeting) policy for this server.",
    "description": "Render the effective welcome policy (admin/manage-guild only).",
    "usage": "!welcome",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Safety & Community — one operator landing"
      },
      {
        "status": "idea",
        "title": "Community platform features — welcome, feeds, events, counters…"
      }
    ]
  },
  {
    "name": "why-no-response",
    "area": "admin",
    "status": "in-progress",
    "summary": "Show the most recent denials / skips for this guild.",
    "description": "Show the most recent denials / skips for this guild.",
    "usage": "!why-no-response",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "\"Compute, don't refuse\" — a capability sweep over the review log"
      },
      {
        "status": "idea",
        "title": "Frequency-driven preset suggestions from the review log"
      },
      {
        "status": "idea",
        "title": "Session follow-up ideas — visual engine + AI-setup wedge arc…"
      },
      {
        "status": "idea",
        "title": "AI self-curated memory notebook — a write-back learning seam for the…"
      }
    ]
  },
  {
    "name": "word",
    "area": "moderation",
    "status": "finished",
    "summary": "Manage prohibited words. Subcommands: add, remove, list.",
    "description": "Manage prohibited words. Subcommands: add, remove, list.",
    "usage": "!word",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "wordmenu",
    "area": "moderation",
    "status": "finished",
    "summary": "Open the interactive prohibited words management panel.",
    "description": "Open the interactive prohibited words management panel.",
    "usage": "!wordmenu",
    "aliases": [],
    "permissions": "Administrator",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "work",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the job selector and earn coins + XP (1 h cooldown).",
    "description": "Open the job selector and earn coins + XP (1 h cooldown).",
    "usage": "!work",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "workshop",
    "area": "economy",
    "status": "in-progress",
    "summary": "Open the workshop — repair worn gear, craft replacements.",
    "description": "Open the workshop — repair worn gear, craft replacements.",
    "usage": "!workshop",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": [
      {
        "status": "idea",
        "title": "Mining grid encounters — depth-gated sparse events (2026-06-22)"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Mining & Exploration — Brainstorm & Roadmap"
      }
    ]
  },
  {
    "name": "world",
    "area": "games",
    "status": "in-progress",
    "summary": "Open the Explore world hub — the open-world town square (Mine · Fish).",
    "description": "Open the Explore world hub — the open-world town square (Mine · Fish).",
    "usage": "!world",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!explore",
      "!world"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Games program: theme-engine architecture + website-first provisioning"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "worldcard",
    "area": "games",
    "status": "in-progress",
    "summary": "Show your cross-game world card — global level + per-game standing.",
    "description": "Show your cross-game world card — global level + per-game standing.",
    "usage": "!worldcard",
    "aliases": [
      "mystats"
    ],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!world"
    ],
    "planned": [
      {
        "status": "idea",
        "title": "Games program: theme-engine architecture + website-first provisioning"
      },
      {
        "status": "idea",
        "title": "The Explore hub — a federated open world (one world, each subsystem…"
      },
      {
        "status": "idea",
        "title": "Wager / money-flow map — generated trace of game coin paths"
      }
    ]
  },
  {
    "name": "xpconfig",
    "area": "progression",
    "status": "finished",
    "summary": "Open the XP configuration panel (admin only).",
    "description": "Open the XP configuration panel (admin only).",
    "usage": "!xpconfig",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  },
  {
    "name": "xpimport",
    "area": "progression",
    "status": "finished",
    "summary": "Import XP/levels from another bot by reading its level-up channel.",
    "description": "Import XP/levels from another bot by reading its level-up channel.",
    "usage": "!xpimport",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [
      "!xpconfig",
      "!xpimport [source] [#channel] [limit]",
      "!xpimport help"
    ],
    "planned": []
  },
  {
    "name": "xpmenu",
    "area": "progression",
    "status": "finished",
    "summary": "Open the XP panel showing your rank and quick admin actions.",
    "description": "Open the XP panel showing your rank and quick admin actions.",
    "usage": "!xpmenu",
    "aliases": [],
    "permissions": "anyone",
    "cooldown": null,
    "examples": [],
    "planned": []
  }
];

const GAMES = [
  {
    "id": "btd6",
    "name": "BTD6 Assistant",
    "icon": "gamepad",
    "color": "var(--g)",
    "command": "btd6",
    "tagline": "Deterministic Bloons Tower Defense 6 assistant — tower/hero/map lookups, round threat…",
    "description": "Deterministic Bloons Tower Defense 6 assistant — tower/hero/map lookups, round threat summaries, and CHIMPS-mode guidance. Built on validated fixtures; consumes the AI gateway only when explicitly enabled (Module 5).",
    "howTo": [
      "Run !btd6 to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "blackjack",
    "name": "Blackjack",
    "icon": "gamepad",
    "color": "var(--sky)",
    "command": "blackjack",
    "tagline": "Blackjack card game",
    "description": "Blackjack card game",
    "howTo": [
      "Run !blackjack to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  },
  {
    "id": "casino",
    "name": "Casino",
    "icon": "gamepad",
    "color": "var(--g-bright)",
    "command": "casino",
    "tagline": "Group card games like multiplayer poker",
    "description": "Group card games like multiplayer poker",
    "howTo": [
      "Run !casino to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  },
  {
    "id": "farm",
    "name": "Chicken Farm",
    "icon": "gamepad",
    "color": "var(--pink)",
    "command": "farm",
    "tagline": "Idle egg farm — hens lay eggs over time; collect, sell, grow",
    "description": "Idle egg farm — hens lay eggs over time; collect, sell, grow",
    "howTo": [
      "Run !farm to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  },
  {
    "id": "counting",
    "name": "Counting",
    "icon": "gamepad",
    "color": "var(--amber)",
    "command": "count_info",
    "tagline": "Collaborative counting game",
    "description": "Collaborative counting game",
    "howTo": [
      "Run !count_info to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  },
  {
    "id": "creature",
    "name": "Creatures",
    "icon": "gamepad",
    "color": "var(--indigo)",
    "command": "games",
    "tagline": "Catch original creatures and build your collection dex",
    "description": "Catch original creatures and build your collection dex",
    "howTo": [
      "Run !games to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "deathmatch",
    "name": "Deathmatch",
    "icon": "gamepad",
    "color": "var(--g)",
    "command": "dm_challenge",
    "tagline": "1v1 duel battles",
    "description": "1v1 duel battles",
    "howTo": [
      "Run !dm_challenge to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  },
  {
    "id": "fishing",
    "name": "Fishing",
    "icon": "gamepad",
    "color": "var(--sky)",
    "command": "fish",
    "tagline": "Fishing minigame — cast a line, build your collection",
    "description": "Fishing minigame — cast a line, build your collection",
    "howTo": [
      "Run !fish to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "games",
    "name": "Games",
    "icon": "gamepad",
    "color": "var(--g-bright)",
    "command": "games",
    "tagline": "Competitive games and channel activities",
    "description": "Competitive games and channel activities",
    "howTo": [
      "Run !games to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "project_moon",
    "name": "Project Moon",
    "icon": "gamepad",
    "color": "var(--pink)",
    "command": "games",
    "tagline": "Browsable Limbus Company knowledge — the 12 Sinners, the 7 Sins, status keywords, damage…",
    "description": "Browsable Limbus Company knowledge — the 12 Sinners, the 7 Sins, status keywords, damage types, and E.G.O grades. Read-only, deterministic reference built on committed structural facts.",
    "howTo": [
      "Run !games to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "rps_tournament",
    "name": "Rock Paper Scissors",
    "icon": "gamepad",
    "color": "var(--amber)",
    "command": "rps",
    "tagline": "Rock Paper Scissors: quick play, PvP, bot matches, tournaments",
    "description": "Rock Paper Scissors: quick play, PvP, bot matches, tournaments",
    "howTo": [
      "Run !rps to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ],
    "beta": true
  },
  {
    "id": "chain",
    "name": "Word Chain",
    "icon": "gamepad",
    "color": "var(--indigo)",
    "command": "chain",
    "tagline": "Word-chaining game",
    "description": "Word-chaining game",
    "howTo": [
      "Run !chain to get started.",
      "Follow the prompts and buttons in the channel.",
      "Wins and progress feed into XP and the leaderboards."
    ]
  }
];

const CHANGELOG = [
  {
    "version": "2026.06.19",
    "date": "Jun 19, 2026",
    "build": "1cc99af",
    "title": "New public bot website",
    "changes": [
      {
        "type": "improved",
        "text": "A brand-new public website for the bot is taking shape — a marketing + reference site"
      }
    ]
  },
  {
    "version": "2026.06.12",
    "date": "Jun 12, 2026",
    "build": "1cc99af",
    "title": "Owner review inbox on the dashboard",
    "changes": [
      {
        "type": "improved",
        "text": "The developer dashboard now surfaces an owner review inbox, so feedback and review"
      }
    ]
  },
  {
    "version": "2026.06.08",
    "date": "Jun 08, 2026",
    "build": "1cc99af",
    "title": "Command-alias suggestions",
    "changes": [
      {
        "type": "added",
        "text": "You can now suggest a friendly alias for any command from the dashboard's Aliases page,"
      }
    ]
  }
];

const STATUS = {
  "overall": "operational",
  "uptime90": "99.9%",
  "systems": [
    {
      "name": "Core gateway",
      "desc": "Command routing & Discord connection",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "40ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Games",
      "area": "games",
      "desc": "Quick, replayable fun that keeps members coming back.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "35ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Moderation",
      "area": "moderation",
      "desc": "Keep your community healthy without the busywork.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "42ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Economy",
      "area": "economy",
      "desc": "Currency, inventory and mining to keep members engaged.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "49ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Admin",
      "area": "admin",
      "desc": "Diagnostics, settings and control for server owners.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "56ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Community",
      "area": "community",
      "desc": "Welcome, spotlight and celebrate your members.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "63ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Progression",
      "area": "progression",
      "desc": "Turn activity into status with XP and ranks.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "70ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Utility",
      "area": "utility",
      "desc": "The little tools a busy server needs every day.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "77ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Management",
      "area": "management",
      "desc": "Channels and roles, managed from chat.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "84ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "More",
      "area": "other",
      "desc": "Handy extras that round out the bot.",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "91ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    },
    {
      "name": "Database",
      "desc": "Persistence for XP, economy, tags & settings",
      "state": "operational",
      "uptime": "99.9%",
      "latency": "12ms",
      "history": [
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational",
        "operational"
      ]
    }
  ],
  "incidents": []
};

const FEATURES = [
  {
    "key": "ai",
    "name": "AI Platform",
    "emoji": "🤖",
    "area": "admin",
    "description": "Read-only AI gateway diagnostics: provider state, feature flags, task routing, and request/failure counters. Does not own AI provider logic — that lives in core/runtime/ai/.",
    "tags": [
      "ai",
      "platform",
      "diagnostics",
      "providers"
    ],
    "is_game": false
  },
  {
    "key": "admin",
    "name": "Administration",
    "emoji": "⚙️",
    "area": "admin",
    "description": "Cog management, server stats, diagnostics",
    "tags": [
      "admin",
      "cogs",
      "management",
      "diagnostics"
    ],
    "is_game": false
  },
  {
    "key": "diagnostic",
    "name": "Diagnostics",
    "emoji": "🩺",
    "area": "admin",
    "description": "Bot health, latency, and system diagnostics",
    "tags": [
      "diagnostics",
      "health",
      "latency",
      "debug"
    ],
    "is_game": false
  },
  {
    "key": "logging",
    "name": "Server Logging",
    "emoji": "📝",
    "area": "admin",
    "description": "Per-guild moderation/cleanup event logging — channel selection, auto-create, and audit (S7)",
    "tags": [
      "logging",
      "audit",
      "moderation",
      "cleanup"
    ],
    "is_game": false
  },
  {
    "key": "server_management",
    "name": "Server Management",
    "emoji": "🧭",
    "area": "admin",
    "description": "Unified hub for moderation, channels, roles, cleanup, setup",
    "tags": [
      "admin",
      "hub",
      "navigation",
      "operations"
    ],
    "is_game": false
  },
  {
    "key": "settings",
    "name": "Settings Manager",
    "emoji": "⚙️",
    "area": "admin",
    "description": "Read-only browsing of platform settings, bindings, and audit history (S5)",
    "tags": [
      "settings",
      "configuration",
      "audit",
      "platform"
    ],
    "is_game": false
  },
  {
    "key": "ux_lab",
    "name": "UX Lab",
    "emoji": "🧪",
    "area": "admin",
    "description": "Interface gallery — browse UI patterns, all fake & safe",
    "tags": [
      "admin",
      "design",
      "gallery",
      "patterns"
    ],
    "is_game": false
  },
  {
    "key": "community",
    "name": "Community",
    "emoji": "🌱",
    "area": "community",
    "description": "Progression, roles, and community activities",
    "tags": [
      "community",
      "hub",
      "progression"
    ],
    "is_game": false
  },
  {
    "key": "community_spotlight",
    "name": "Community Spotlight",
    "emoji": "🌟",
    "area": "community",
    "description": "Live server activity dashboard — leaders, level-ups, game stats",
    "tags": [
      "spotlight",
      "activity",
      "leaderboard",
      "community"
    ],
    "is_game": false
  },
  {
    "key": "counters",
    "name": "Server Counters",
    "emoji": "📊",
    "area": "community",
    "description": "Live member-count channels (total · humans · bots)",
    "tags": [
      "counters",
      "stats",
      "members",
      "community"
    ],
    "is_game": false
  },
  {
    "key": "ticket",
    "name": "Support Tickets",
    "emoji": "🎫",
    "area": "community",
    "description": "Private support tickets — open by command, panel, or the AI",
    "tags": [
      "tickets",
      "support",
      "help",
      "staff"
    ],
    "is_game": false
  },
  {
    "key": "welcome",
    "name": "Welcome",
    "emoji": "👋",
    "area": "community",
    "description": "Member greetings, farewells, and an optional entry role",
    "tags": [
      "welcome",
      "greeting",
      "onboarding",
      "community"
    ],
    "is_game": false
  },
  {
    "key": "economy",
    "name": "Economy",
    "emoji": "💰",
    "area": "economy",
    "description": "Daily coins, work, shop, balance",
    "tags": [
      "economy",
      "currency",
      "coins",
      "progression"
    ],
    "is_game": false
  },
  {
    "key": "inventory",
    "name": "Inventory",
    "emoji": "🎒",
    "area": "economy",
    "description": "Item management and crafting",
    "tags": [
      "inventory",
      "items",
      "crafting"
    ],
    "is_game": false
  },
  {
    "key": "mining",
    "name": "Mining",
    "emoji": "⛏️",
    "area": "economy",
    "description": "Mining minigame and resource collection",
    "tags": [
      "mining",
      "resources",
      "minigame"
    ],
    "is_game": false
  },
  {
    "key": "treasury",
    "name": "Treasury",
    "emoji": "🏛️",
    "area": "economy",
    "description": "Server-owned coin pool — contribute coins; managers disburse",
    "tags": [
      "treasury",
      "economy",
      "coins",
      "governance"
    ],
    "is_game": false
  },
  {
    "key": "btd6",
    "name": "BTD6 Assistant",
    "emoji": "🐵",
    "area": "games",
    "description": "Deterministic Bloons Tower Defense 6 assistant — tower/hero/map lookups, round threat summaries, and CHIMPS-mode guidance. Built on validated fixtures; consumes the AI gateway only when explicitly enabled (Module 5).",
    "tags": [
      "games",
      "btd6",
      "bloons",
      "tower defense"
    ],
    "is_game": true
  },
  {
    "key": "blackjack",
    "name": "Blackjack",
    "emoji": "🃏",
    "area": "games",
    "description": "Blackjack card game",
    "tags": [
      "games",
      "blackjack",
      "cards"
    ],
    "is_game": true
  },
  {
    "key": "casino",
    "name": "Casino",
    "emoji": "🎰",
    "area": "games",
    "description": "Group card games like multiplayer poker",
    "tags": [
      "games",
      "casino",
      "poker",
      "cards",
      "multiplayer"
    ],
    "is_game": true
  },
  {
    "key": "farm",
    "name": "Chicken Farm",
    "emoji": "🐔",
    "area": "games",
    "description": "Idle egg farm — hens lay eggs over time; collect, sell, grow",
    "tags": [
      "farm",
      "idle",
      "chickens",
      "eggs",
      "activities"
    ],
    "is_game": true
  },
  {
    "key": "counting",
    "name": "Counting",
    "emoji": "🔢",
    "area": "games",
    "description": "Collaborative counting game",
    "tags": [
      "games",
      "counting",
      "community"
    ],
    "is_game": true
  },
  {
    "key": "creature",
    "name": "Creatures",
    "emoji": "🐾",
    "area": "games",
    "description": "Catch original creatures and build your collection dex",
    "tags": [
      "creatures",
      "minigame",
      "activities"
    ],
    "is_game": true
  },
  {
    "key": "deathmatch",
    "name": "Deathmatch",
    "emoji": "⚔️",
    "area": "games",
    "description": "1v1 duel battles",
    "tags": [
      "games",
      "duel",
      "pvp",
      "deathmatch"
    ],
    "is_game": true
  },
  {
    "key": "fishing",
    "name": "Fishing",
    "emoji": "🎣",
    "area": "games",
    "description": "Fishing minigame — cast a line, build your collection",
    "tags": [
      "fishing",
      "minigame",
      "activities"
    ],
    "is_game": true
  },
  {
    "key": "games",
    "name": "Games",
    "emoji": "🎮",
    "area": "games",
    "description": "Competitive games and channel activities",
    "tags": [
      "games",
      "hub",
      "activities"
    ],
    "is_game": true
  },
  {
    "key": "project_moon",
    "name": "Project Moon",
    "emoji": "🌑",
    "area": "games",
    "description": "Browsable Limbus Company knowledge — the 12 Sinners, the 7 Sins, status keywords, damage types, and E.G.O grades. Read-only, deterministic reference built on committed structural facts.",
    "tags": [
      "games",
      "project moon",
      "limbus",
      "reference"
    ],
    "is_game": true
  },
  {
    "key": "rps_tournament",
    "name": "Rock Paper Scissors",
    "emoji": "✂️",
    "area": "games",
    "description": "Rock Paper Scissors: quick play, PvP, bot matches, tournaments",
    "tags": [
      "games",
      "rps",
      "tournament"
    ],
    "is_game": true
  },
  {
    "key": "chain",
    "name": "Word Chain",
    "emoji": "🔗",
    "area": "games",
    "description": "Word-chaining game",
    "tags": [
      "games",
      "words",
      "chain"
    ],
    "is_game": true
  },
  {
    "key": "channel",
    "name": "Channels",
    "emoji": "📐",
    "area": "management",
    "description": "Channel and category creation, deletion, and restrictions",
    "tags": [
      "channels",
      "management",
      "permissions"
    ],
    "is_game": false
  },
  {
    "key": "role",
    "name": "Roles",
    "emoji": "🎭",
    "area": "management",
    "description": "Time-based and XP-based automatic role assignment",
    "tags": [
      "roles",
      "assignment",
      "automation"
    ],
    "is_game": false
  },
  {
    "key": "automod",
    "name": "Automod",
    "emoji": "🛡️",
    "area": "moderation",
    "description": "Spam, invite links, excessive caps, and mass-mention filtering",
    "tags": [
      "automod",
      "moderation",
      "safety",
      "spam",
      "filter"
    ],
    "is_game": false
  },
  {
    "key": "cleanup",
    "name": "Cleanup",
    "emoji": "🧹",
    "area": "moderation",
    "description": "Prohibited words, command deletion, channel hygiene",
    "tags": [
      "cleanup",
      "words",
      "moderation",
      "hygiene"
    ],
    "is_game": false
  },
  {
    "key": "image_moderation",
    "name": "Image moderation",
    "emoji": "🖼️",
    "area": "moderation",
    "description": "Scan uploaded images for sexual, violent, harassment, or hate content",
    "tags": [
      "image",
      "moderation",
      "safety",
      "nsfw",
      "filter"
    ],
    "is_game": false
  },
  {
    "key": "moderation",
    "name": "Moderation",
    "emoji": "🔨",
    "area": "moderation",
    "description": "Warnings, timeouts, bans, mod logs",
    "tags": [
      "moderation",
      "safety",
      "logs",
      "warn",
      "ban"
    ],
    "is_game": false
  },
  {
    "key": "proof_channel",
    "name": "Proof Channel",
    "emoji": "📋",
    "area": "moderation",
    "description": "Proof submission and exclusive access sessions",
    "tags": [
      "proof",
      "events",
      "access"
    ],
    "is_game": false
  },
  {
    "key": "security",
    "name": "Server Security",
    "emoji": "🛡️",
    "area": "moderation",
    "description": "Raid detection + account-age screening on member join",
    "tags": [
      "security",
      "raid",
      "moderation",
      "safety"
    ],
    "is_game": false
  },
  {
    "key": "karma",
    "name": "Karma",
    "emoji": "✨",
    "area": "progression",
    "description": "Peer reputation — thank helpful members with !thanks",
    "tags": [
      "karma",
      "reputation",
      "thanks",
      "progression",
      "leaderboard"
    ],
    "is_game": false
  },
  {
    "key": "leaderboard",
    "name": "Leaderboard",
    "emoji": "🏆",
    "area": "progression",
    "description": "Server leaderboards for XP, coins, and games",
    "tags": [
      "leaderboard",
      "rankings",
      "stats"
    ],
    "is_game": false
  },
  {
    "key": "xp",
    "name": "XP & Levels",
    "emoji": "⭐",
    "area": "progression",
    "description": "Experience points, levels, and leaderboards",
    "tags": [
      "xp",
      "levels",
      "progression",
      "leaderboard"
    ],
    "is_game": false
  },
  {
    "key": "four_twenty",
    "name": "420",
    "emoji": "🍃",
    "area": "utility",
    "description": "A leafy little easter-egg panel — wisdom and number trivia",
    "tags": [
      "fun",
      "easter-egg",
      "420"
    ],
    "is_game": false
  },
  {
    "key": "general",
    "name": "General",
    "emoji": "💬",
    "area": "utility",
    "description": "General bot commands and information",
    "tags": [
      "general",
      "info",
      "community"
    ],
    "is_game": false
  },
  {
    "key": "help",
    "name": "Help",
    "emoji": "📚",
    "area": "utility",
    "description": "Interactive help menu and command discovery",
    "tags": [
      "help",
      "commands",
      "discovery"
    ],
    "is_game": false
  },
  {
    "key": "utility",
    "name": "Utility",
    "emoji": "🔧",
    "area": "utility",
    "description": "General utility commands",
    "tags": [
      "utility",
      "tools",
      "general"
    ],
    "is_game": false
  }
];

const BUILD = {
  "commit": "1cc99af",
  "subject": "Merge remote-tracking branch 'origin/main' into claude/mineverse-flag-2",
  "committed_at": "2026-07-13T04:08:03Z"
};

const COUNTS = {
  "commands": 485,
  "features": 43,
  "games": 12
};

const ADD_URL = "https://discord.com/oauth2/authorize?client_id=1403818430758654132";

function mkHistory(seed, badDays) {
  const out = [];
  for (let i = 0; i < 60; i++) {
    let s = "operational";
    if (badDays && badDays[i]) s = badDays[i];
    out.push(s);
  }
  return out;
}

/* lookup helpers */
const byCommand = (name) => COMMANDS.find((c) => c.name === name);
const byArea = (id) => AREAS.find((a) => a.id === id);
const byGame = (id) => GAMES.find((g) => g.id === id);
const commandsInArea = (id) => COMMANDS.filter((c) => c.area === id);
const byFeature = (key) => FEATURES.find((f) => f.key === key);
const featuresInArea = (id) => FEATURES.filter((f) => f.area === id);

window.SBDATA = { ICONS, AREAS, COMMANDS, GAMES, CHANGELOG, STATUS, byCommand, byArea, byGame, commandsInArea };
/* additive v2 families — v1's frozen app.js ignores these */
Object.assign(window.SBDATA, { FEATURES, BUILD, COUNTS, ADD_URL, byFeature, featuresInArea });
