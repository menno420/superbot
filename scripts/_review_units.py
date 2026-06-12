"""Resolve a repo path to its **review unit** per ``docs/repo-review-map.md``.

This is the executable form of the review/refactor partition:

- **Axis A** — the coarse repo domain (A1 bot runtime · A2 BTD6 data pipeline ·
  A3 dev/CI/agent tooling · A4 docs & agent system · A5 tests-as-mirror).
- **Axis B** — inside the bot runtime (A1), the review unit is either a vertical
  **subsystem slice** or a shared **platform** layer.

Shared by ``scripts/review_scope.py`` (file + changeset classification) and
``scripts/context_map.py`` (the one-line "Review unit" header). Pure path logic —
it never touches the filesystem, so it also classifies deleted/renamed paths from a
diff. Heuristic by design: when in doubt it says so and points at the binding docs
(``repo-navigation-map.md`` cheat sheet · ``ownership.md``). The doc wins over this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Offline BTD6 data-pipeline scripts (Axis A2) — everything else in scripts/ is A3.
_BTD6_PIPELINE_SCRIPTS = {
    "parse_gamedata.py",
    "parse_bloonswiki.py",
    "fetch_btd6_wiki_data.py",
    "fetch_bloonswiki.py",
    "explore_gamedata.py",
    "btd6_gamedata_inventory.py",
    "btd6_decode_inventory_report.py",
    "btd6_patch_diff.py",
    "btd6_probe.py",
    "import_btd6_data_from_csv.py",
    "seed_btd6_data.py",
    "upload_btd6_data.py",
    "gen_gear_placeholder_sprites.py",
}

# Root config files (Axis A3).
_ROOT_CONFIG = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    ".pre-commit-config.yaml",
    ".python-version",
    "Procfile",
    ".mcp.json",
    ".gitignore",
    ".gitattributes",
    ".claude.json",
}


@dataclass(frozen=True)
class ReviewUnit:
    """The review unit a single path belongs to."""

    axis: str  # "A1".."A5"
    domain: str  # human label, e.g. "bot runtime"
    kind: str  # slice | platform | data-pipeline | tooling | docs | tests | config | runtime-data | asset | service | unknown
    name: str  # slice name / platform-layer label / ""
    detail: str = ""

    def label(self) -> str:
        """One-line human label, e.g. ``A1 · slice: economy``."""
        head = f"{self.axis} · {self.kind}"
        if self.name:
            head += f": {self.name}"
        return head


def _norm(path: str) -> str:
    p = path.strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def _disbot_unit(rel: str) -> ReviewUnit:
    """Classify a ``disbot/...`` path into an Axis-B slice or platform unit."""
    sub = rel[len("disbot/") :]
    parts = sub.split("/")
    first = parts[0]

    # Entry & lifecycle (platform).
    if (
        sub in {"bot1.py", "config.py", "guild_lifecycle.py", "healthserver.py"}
        or first == "migrations"
    ):
        return ReviewUnit(
            "A1",
            "bot runtime",
            "platform",
            "entry-lifecycle",
            "no subsystem logic here; see repo-navigation-map entry rows",
        )

    # core/ (platform).
    if first == "core":
        layer = (
            "runtime-core"
            if len(parts) > 1 and parts[1] == "runtime"
            else (
                "resources-core"
                if len(parts) > 1 and parts[1] == "resources"
                else "core"
            )
        )
        return ReviewUnit(
            "A1",
            "bot runtime",
            "platform",
            layer,
            "must not import cogs/services; runtime_contracts.md",
        )
    if first == "governance":
        return ReviewUnit(
            "A1",
            "bot runtime",
            "platform",
            "governance",
            "ownership.md INV-E; strict internal layer order",
        )
    if first == "utils":
        return ReviewUnit(
            "A1",
            "bot runtime",
            "platform",
            "utils",
            "helper-policy.md; utils/db may import asyncpg only",
        )

    # views/ — shared primitives are platform; views/<name>/ is a slice.
    if first == "views":
        if len(parts) >= 2 and parts[1] in {"base.py", "navigation.py", "selectors"}:
            return ReviewUnit(
                "A1",
                "bot runtime",
                "platform",
                "view-primitives",
                "no parallel base/navigation module; architecture.md view rules",
            )
        if len(parts) >= 2 and parts[1].endswith(".py"):
            return ReviewUnit(
                "A1",
                "bot runtime",
                "platform",
                "view-primitives",
                "shared top-level view module",
            )
        if len(parts) >= 2:
            return ReviewUnit(
                "A1",
                "bot runtime",
                "slice",
                parts[1],
                "subsystem view package",
            )

    # cogs/ — the subsystem entry points.
    if first == "cogs":
        if len(parts) >= 2 and parts[1].endswith(".py"):
            name = parts[1][: -len(".py")]
            if name.endswith("_cog"):
                name = name[: -len("_cog")]
            if name == "__init__":
                return ReviewUnit(
                    "A1",
                    "bot runtime",
                    "platform",
                    "cogs-init",
                    "package init",
                )
            return ReviewUnit(
                "A1",
                "bot runtime",
                "slice",
                name,
                "subsystem cog entry point",
            )
        if len(parts) >= 2:
            return ReviewUnit(
                "A1",
                "bot runtime",
                "slice",
                parts[1],
                "subsystem private package",
            )

    # services/ — owned by a slice, but not 1:1 by name. Heuristic on the leading token.
    if first == "services":
        if len(parts) >= 2 and parts[1].endswith(".py"):
            token = parts[1][: -len(".py")].split("_")[0]
            return ReviewUnit(
                "A1",
                "bot runtime",
                "service",
                token,
                "owning slice is a guess from the name — confirm in ownership.md",
            )
        return ReviewUnit(
            "A1",
            "bot runtime",
            "service",
            "",
            "confirm owning slice in ownership.md",
        )

    if first == "data":
        return ReviewUnit(
            "A1",
            "bot runtime",
            "runtime-data",
            "",
            "static JSON loaded at runtime; travels with its consuming slice",
        )
    if first == "assets":
        return ReviewUnit(
            "A1",
            "bot runtime",
            "asset",
            "",
            "runtime asset; travels with its consuming slice",
        )

    return ReviewUnit(
        "A1",
        "bot runtime",
        "unknown",
        "",
        "unrecognised disbot/ path — check repo-navigation-map.md",
    )


def classify_path(path: str) -> ReviewUnit:
    """Return the :class:`ReviewUnit` for ``path`` (repo-relative or absolute-ish)."""
    rel = _norm(path)

    if rel.startswith("disbot/"):
        return _disbot_unit(rel)

    if rel.startswith("tests/"):
        return ReviewUnit(
            "A5",
            "tests (mirror)",
            "tests",
            "",
            "reviewed with the slice it mirrors, not as a silo",
        )

    if (
        rel.startswith("docs/")
        or rel.startswith(".claude/")
        or rel.startswith(".sessions/")
        or rel.startswith(".session-journal")
    ):
        return ReviewUnit(
            "A4",
            "docs & agent system",
            "docs",
            "",
            "accuracy + reachability (check_docs)",
        )

    if rel.startswith("data/btd6"):
        return ReviewUnit(
            "A2",
            "BTD6 data pipeline",
            "data-pipeline",
            "",
            "offline data; never serves traffic",
        )

    if rel.startswith("scripts/"):
        base = rel.split("/", 1)[1] if "/" in rel else ""
        if base in _BTD6_PIPELINE_SCRIPTS:
            return ReviewUnit(
                "A2",
                "BTD6 data pipeline",
                "data-pipeline",
                "",
                "offline extraction/seed script",
            )
        return ReviewUnit(
            "A3",
            "dev/CI/agent tooling",
            "tooling",
            "",
            "toolchain — enforce/scaffold/deploy correctness",
        )

    if (
        rel.startswith("tools/")
        or rel.startswith("architecture_rules/")
        or rel.startswith(".github/")
    ):
        return ReviewUnit("A3", "dev/CI/agent tooling", "tooling", "", "toolchain")

    if rel in _ROOT_CONFIG:
        return ReviewUnit("A3", "dev/CI/agent tooling", "config", "", "root config")

    return ReviewUnit(
        "A4",
        "docs & agent system",
        "unknown",
        "",
        "unrecognised top-level path",
    )


@dataclass
class ChangesetVerdict:
    """The review scope of a set of changed paths."""

    verdict: str  # single-slice | multi-slice | platform | non-runtime | mixed | empty
    slices: set[str] = field(default_factory=set)
    platform_layers: set[str] = field(default_factory=set)
    advice: str = ""
    units: list[tuple[str, ReviewUnit]] = field(default_factory=list)


def classify_changeset(paths: list[str]) -> ChangesetVerdict:
    """Classify a changed-file set into a single review-scope verdict."""
    units = [(p, classify_path(p)) for p in paths if _norm(p)]
    if not units:
        return ChangesetVerdict("empty", advice="no paths to classify")

    slices: set[str] = set()
    platform: set[str] = set()
    has_runtime = False
    for _p, u in units:
        if u.axis == "A1":
            if u.kind == "platform":
                platform.add(u.name)
                has_runtime = True
            elif u.kind in {"slice", "service"} and u.name:
                slices.add(u.name)
                has_runtime = True
            elif u.kind in {"runtime-data", "asset", "unknown"}:
                has_runtime = True

    if platform:
        advice = (
            "Platform change — higher review bar. Run `context_map.py` on the touched "
            "layer files for blast radius; review against the layer contract."
        )
        verdict = "platform"
    elif len(slices) >= 2:
        advice = (
            "Touches multiple slices — should the cross-slice effect go through the "
            "EventBus or a shared service instead of a direct dependency? (no cross-cog imports)"
        )
        verdict = "multi-slice"
    elif len(slices) == 1:
        advice = (
            "Self-contained slice review: stay within the slice's cog/views/service/DB + its "
            "mirrored tests; mutations through the audited service seam."
        )
        verdict = "single-slice"
    elif has_runtime:
        advice = "Runtime data/asset only — review with the consuming slice."
        verdict = "mixed"
    else:
        advice = "No bot-runtime files — docs/tooling/data/tests review (Axis A2–A5)."
        verdict = "non-runtime"

    return ChangesetVerdict(verdict, slices, platform, advice, units)
