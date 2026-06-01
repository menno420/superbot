"""Deterministic BTD6 *upgrade* resolver — upgrades as first-class entities.

The existing :mod:`services.btd6_resolver_service` recognises towers, heroes,
maps, modes, bloons, relics, and live entities — but **not upgrades**. So a
natural-language query like ``"PMFC stats"``, ``"POD cooldown"``, or
``"Prince of Darkness damage"`` resolves to nothing unless the message also
names the tower (``"wizard ..."``). This module fills that gap with a small,
deterministic registry + resolver — no AI, no I/O beyond the committed dataset.

Every upgrade in the game is a ``(tower, path, tier)`` triple with a unique
name; this builds an :class:`UpgradeIdentity` for each from
``btd6_data_service`` (``upgrade_paths`` / ``upgrade_costs``) and resolves a
query to one via, in order:

1. an exact upgrade **name** mentioned in the text (``Prince of Darkness``);
2. a curated **alias / abbreviation / nickname** (``PMFC``, ``POD``,
   ``Phoenix Lord``);
3. **path notation** alongside a tower (``wizard 005`` / ``050 dart``);

returning :class:`UpgradeResolution` with the match type, the resolved upgrade,
or — when a term maps to several upgrades — the ambiguous candidates. Wiring
this into the resolver / AI grounding / panel is a separate step; this layer is
deliberately self-contained and behaviour-neutral on its own.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from services.btd6_data_service import get_dataset

_KEY_BY_PATH = {1: "top", 2: "mid", 3: "bot"}
_PATH_BY_KEY = {"top": 1, "mid": 2, "bot": 3}

# A single-path tier code in text: three digits 0-5, optionally hyphenated,
# bounded so it won't fire inside a longer number (game versions etc.).
_CODE_RE = re.compile(r"(?<![\d-])([0-5])-?([0-5])-?([0-5])(?![\d-])")


@dataclass(frozen=True)
class UpgradeIdentity:
    """One BTD6 upgrade (a tower's path+tier), joined into a stable identity."""

    upgrade_id: str  # "wizard_monkey:005"
    tower_id: str
    tower_name: str
    path: str  # "top" | "mid" | "bot"
    path_index: int  # 1 | 2 | 3
    tier: int  # 1..5
    code: str  # "005"
    crosspath: str  # "0-0-5"
    canonical: str  # "Prince of Darkness"
    cost: int | None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpgradeResolution:
    """Outcome of :func:`resolve_upgrade` — match metadata for callers."""

    query: str
    match_type: str  # exact_name | alias | path_notation | ambiguous | none
    upgrade: UpgradeIdentity | None = None
    candidates: tuple[UpgradeIdentity, ...] = ()

    @property
    def found(self) -> bool:
        return self.upgrade is not None


# Curated alias / abbreviation / nickname -> exact canonical upgrade name. Only
# clearly-correct community terms; anything uncertain is left out so it yields a
# clean no-match rather than a guess. Validated against the live registry by
# tests (every value must name a real upgrade).
_CURATED_ALIASES: dict[str, str] = {
    # Dart Monkey
    "pmfc": "Plasma Monkey Fan Club",
    # Super Monkey
    "smfc": "Super Monkey Fan Club",
    "sun avatar": "Sun Avatar",
    "sav": "Sun Avatar",
    "tsg": "True Sun God",
    "lotn": "Legend of the Night",
    # Wizard Monkey
    "pod": "Prince of Darkness",
    "wlp": "Wizard Lord Phoenix",
    "phoenix lord": "Wizard Lord Phoenix",
    # Dartling Gunner
    "mad": "M.A.D",
    "bez": "Bloon Exclusion Zone",
    "rod": "Ray of Doom",
    # Mortar Monkey
    "paa": "Pop and Awe",
    # Druid
    "aow": "Avatar of Wrath",
    "sotf": "Spirit of the Forest",
    # Alchemist
    "bma": "Bloon Master Alchemist",
    # Mermonkey
    "abyss lord": "Lord of the Abyss",
    # Spike Factory
    "perma spike": "Perma-Spike",
    "permaspike": "Perma-Spike",
    # Glue Gunner
    "bloon solver": "The Bloon Solver",
    # Tack Shooter
    "tack zone": "The Tack Zone",
    # Ninja Monkey
    "gm ninja": "Grandmaster Ninja",
    # Banana Farm
    "monkey wall street": "Monkey Wall Street",
    "mws": "Monkey Wall Street",
}


def _tokens(text: str) -> list[str]:
    """Lowercase alphanumeric word tokens."""
    return [t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t]


def _contains_subsequence(haystack: list[str], needle: list[str]) -> bool:
    """True if ``needle`` appears as a contiguous run inside ``haystack``."""
    if not needle or len(needle) > len(haystack):
        return False
    first = needle[0]
    for i in range(len(haystack) - len(needle) + 1):
        if haystack[i] == first and haystack[i : i + len(needle)] == needle:
            return True
    return False


# ---------------------------------------------------------------------------
# Registry (built once from the dataset, cached)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Registry:
    upgrades: tuple[UpgradeIdentity, ...]
    by_id: dict[str, UpgradeIdentity]
    by_tower: dict[str, dict[str, UpgradeIdentity]]  # tower_id -> code -> identity
    # surface (token tuple) -> identity, for name + alias matching
    name_index: dict[tuple[str, ...], UpgradeIdentity]
    alias_index: dict[tuple[str, ...], UpgradeIdentity]
    tower_surfaces: dict[tuple[str, ...], str]  # tower alias tokens -> tower_id


_REGISTRY: _Registry | None = None


def _build_registry() -> _Registry:
    dataset = get_dataset()
    upgrades: list[UpgradeIdentity] = []
    by_tower: dict[str, dict[str, UpgradeIdentity]] = {}
    name_to_identity: dict[str, UpgradeIdentity] = {}

    for tower in dataset.towers:
        paths = tower.upgrade_paths or {}
        costs = tower.upgrade_costs or {}
        for pkey, names in paths.items():
            path_index = _PATH_BY_KEY.get(pkey)
            if path_index is None:
                continue
            path_costs = costs.get(pkey, ())
            for tier_idx, name in enumerate(names):
                if not name:
                    continue
                tier = tier_idx + 1
                digits = ["0", "0", "0"]
                digits[path_index - 1] = str(tier)
                code = "".join(digits)
                cost = (
                    path_costs[tier_idx]
                    if tier_idx < len(path_costs) and path_costs[tier_idx]
                    else None
                )
                identity = UpgradeIdentity(
                    upgrade_id=f"{tower.id}:{code}",
                    tower_id=tower.id,
                    tower_name=tower.canonical,
                    path=pkey,
                    path_index=path_index,
                    tier=tier,
                    code=code,
                    crosspath="-".join(code),
                    canonical=name,
                    cost=cost,
                )
                upgrades.append(identity)
                by_tower.setdefault(tower.id, {})[code] = identity
                name_to_identity[name.lower()] = identity

    # Attach curated aliases (and a per-identity alias tuple).
    alias_index: dict[tuple[str, ...], UpgradeIdentity] = {}
    aliases_for: dict[str, list[str]] = {}
    for alias, canonical in _CURATED_ALIASES.items():
        identity = name_to_identity.get(canonical.lower())
        if identity is None:
            continue  # a typo'd curated name; tests assert this never happens
        alias_index[tuple(_tokens(alias))] = identity
        aliases_for.setdefault(identity.upgrade_id, []).append(alias)

    # Rebuild identities with their alias tuples filled in.
    final: list[UpgradeIdentity] = []
    by_id: dict[str, UpgradeIdentity] = {}
    name_index: dict[tuple[str, ...], UpgradeIdentity] = {}
    for identity in upgrades:
        al = tuple(aliases_for.get(identity.upgrade_id, ()))
        if al:
            identity = UpgradeIdentity(**{**identity.__dict__, "aliases": al})
        final.append(identity)
        by_id[identity.upgrade_id] = identity
        by_tower[identity.tower_id][identity.code] = identity
        name_index[tuple(_tokens(identity.canonical))] = identity
    # Re-point alias_index at the alias-filled identities.
    alias_index = {toks: by_id[ident.upgrade_id] for toks, ident in alias_index.items()}

    tower_surfaces: dict[tuple[str, ...], str] = {}
    for tower in dataset.towers:
        for surface in (tower.id, tower.canonical, *tower.aliases):
            toks = tuple(_tokens(surface))
            if toks:
                tower_surfaces[toks] = tower.id

    return _Registry(
        upgrades=tuple(final),
        by_id=by_id,
        by_tower=by_tower,
        name_index=name_index,
        alias_index=alias_index,
        tower_surfaces=tower_surfaces,
    )


def _registry() -> _Registry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


def reset_cache() -> None:
    """Test seam: drop the built registry."""
    global _REGISTRY
    _REGISTRY = None


def all_upgrades() -> tuple[UpgradeIdentity, ...]:
    """Every upgrade identity (375: 25 towers x 3 paths x 5 tiers)."""
    return _registry().upgrades


def get_upgrade(upgrade_id: str) -> UpgradeIdentity | None:
    """Look up an upgrade by its ``tower_id:code`` id."""
    return _registry().by_id.get(upgrade_id)


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


def _match_surfaces(
    query_tokens: list[str],
    index: dict[tuple[str, ...], UpgradeIdentity],
) -> set[str]:
    """Upgrade ids whose name/alias surface appears in ``query_tokens``.

    Single-token surfaces match an exact token (so ``mad`` never fires inside
    ``madness``); multi-token surfaces match a contiguous run.
    """
    token_set = set(query_tokens)
    hits: set[str] = set()
    for surface, identity in index.items():
        if len(surface) == 1:
            if surface[0] in token_set:
                hits.add(identity.upgrade_id)
        elif _contains_subsequence(query_tokens, list(surface)):
            hits.add(identity.upgrade_id)
    return hits


def _single_path_code(query: str) -> str | None:
    """The first single-path tier code in ``query`` (e.g. ``005``), or None.

    Crosspath codes (two non-zero digits) are not a single upgrade, so they are
    ignored here — the existing crosspath grounding owns those.
    """
    for match in _CODE_RE.finditer(query or ""):
        digits = match.groups()
        nonzero = [d for d in digits if d != "0"]
        if len(nonzero) == 1:
            return "".join(digits)
    return None


def _tower_in_query(query_tokens: list[str], reg: _Registry) -> str | None:
    token_set = set(query_tokens)
    for surface, tower_id in reg.tower_surfaces.items():
        if len(surface) == 1:
            if surface[0] in token_set:
                return tower_id
        elif _contains_subsequence(query_tokens, list(surface)):
            return tower_id
    return None


def resolve_upgrade(query: str) -> UpgradeResolution:
    """Resolve free-form ``query`` to a single BTD6 upgrade (or ambiguity/none).

    Deterministic and order-stable: an explicit upgrade **name** wins over a
    curated **alias**, which wins over **path notation** (a tower + tier code).
    A term that maps to several distinct upgrades returns ``ambiguous`` with the
    candidates so callers can ask for clarification rather than guess.
    """
    reg = _registry()
    tokens = _tokens(query)
    if not tokens and not (query or "").strip():
        return UpgradeResolution(query=query or "", match_type="none")

    name_hits = _match_surfaces(tokens, reg.name_index)
    if len(name_hits) == 1:
        return UpgradeResolution(query, "exact_name", reg.by_id[next(iter(name_hits))])

    alias_hits = _match_surfaces(tokens, reg.alias_index)
    combined = name_hits | alias_hits
    if len(combined) == 1:
        match_type = "exact_name" if name_hits else "alias"
        return UpgradeResolution(query, match_type, reg.by_id[next(iter(combined))])
    if len(combined) > 1:
        candidates = tuple(
            sorted(
                (reg.by_id[uid] for uid in combined),
                key=lambda u: u.upgrade_id,
            ),
        )
        return UpgradeResolution(query, "ambiguous", None, candidates)

    # Path notation: a tower + a single-path code (e.g. "wizard 005", "050 dart").
    code = _single_path_code(query)
    if code is not None:
        tower_id = _tower_in_query(tokens, reg)
        if tower_id is not None:
            identity = reg.by_tower.get(tower_id, {}).get(code)
            if identity is not None:
                return UpgradeResolution(query, "path_notation", identity)

    return UpgradeResolution(query, "none")


__all__ = [
    "UpgradeIdentity",
    "UpgradeResolution",
    "all_upgrades",
    "get_upgrade",
    "reset_cache",
    "resolve_upgrade",
]
