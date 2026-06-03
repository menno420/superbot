"""Map the public BTD Mod Helper game-data dump → our BTD6 stats schema.

This is the *third* and most authoritative BTD6 data source (see
``docs/btd6-game-file-extraction-plan.md``). Unlike bloonswiki (lagging,
incomplete — only 6/17 heroes, 2 prose paragons) this reads the game's own
exported model JSON, already decrypted by Mod Helper's "Export Game Data"
button and published at ``github.com/Btd6ModHelper/btd6-game-data``.

The dump is **not vendored** — point ``--dump`` at a local clone:

    git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
    python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --tower dart_monkey --dry-run
    python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --all          # writes every file
    python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --validate-anchors

Source → target field mapping is documented in the extraction plan; the short
version: a tower folder holds the base model (``<Name>.json``, tiers ``000``)
plus one *complete* model file per crosspath state (``<Name>-NNN.json``, all
64). Each file's ``behaviors[]`` carry ``$type``-tagged models; we walk
``AttackModel → weapons[] → projectile → behaviors[DamageModel/Travel…]`` and
flatten to the same cleaned shape ``parse_bloonswiki`` produces from the wiki's
copy of the model, so the runtime (``btd6_stats_service`` et al.) reads it
unchanged. Heroes are one file per level (``<Hero> N.json``); paragons are a
single flat ``<Name>-Paragon.json`` node.

Provenance: every emitted file is stamped ``source: "BTD Mod Helper game data
export"`` and the dump's ``_last_updated``/commit version. We commit only the
derived numeric stats (facts), never the raw dump.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
# Allow ``from utils.btd6...`` when run as a script (pytest already has it).
if str(_REPO_ROOT / "disbot") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "disbot"))

_DATA_ROOT = _REPO_ROOT / "disbot" / "data" / "btd6"
_STATS_DIR = _DATA_ROOT / "stats"
_SOURCE = "BTD Mod Helper game data export"

# towerSet is a bit-flag enum in the model. Verified against the dump:
# DartMonkey/BombShooter=1, Sniper/Sub/Dartling=2, Super/Ninja=4, Village/Farm=8.
_TOWER_SET: dict[int, str] = {1: "primary", 2: "military", 4: "magic", 8: "support"}

# areaTypes entries: 1=Water, 2=Land, 4=Track (verified: land towers carry [2],
# Buccaneer/Sub carry [1]). A tower may list several.
_AREA_WATER, _AREA_LAND, _AREA_TRACK = 1, 2, 4

# Raw ``DamageModifierForTagModel.tag`` → the wiki/runtime field name the
# detail embed renders (``utils.btd6.stats_embed._DAMAGE_MODIFIERS``).
_TAG_TO_DAMAGE_MOD: dict[str, str] = {
    "Lead": "damageModifierForLead",
    "Ceramic": "damageModifierForCeramic",
    "Fortified": "damageModifierForFortified",
    "Moab": "damageModifierForMoab",
    "Moabs": "damageModifierForMoabs",
    "Boss": "damageModifierForBoss",
    "Bad": "damageModifierForBad",
    "Camo": "damageModifierForCamo",
    "Stunned": "damageModifierForStunned",
}


def _short_type(node: Any) -> str:
    """The bare model class name from a ``$type`` string.

    ``"Il2Cpp…Behaviors.AttackModel, Assembly-CSharp"`` → ``"AttackModel"``.
    """
    if not isinstance(node, dict):
        return ""
    raw = node.get("$type")
    if not isinstance(raw, str):
        return ""
    return raw.split(",", 1)[0].rsplit(".", 1)[-1]


def _behaviors(node: dict, *suffixes: str) -> list[dict]:
    """All ``behaviors[]`` entries whose model class ends with one of ``suffixes``."""
    out: list[dict] = []
    for b in node.get("behaviors", []) or []:
        if isinstance(b, dict) and _short_type(b) in suffixes:
            out.append(b)
    return out


def _first(node: dict, *suffixes: str) -> dict | None:
    found = _behaviors(node, *suffixes)
    return found[0] if found else None


def _num(value: Any) -> Any:
    """Spell whole floats as ints (``7.0`` → ``7``) to match the wiki shape; keep
    real fractions and non-numbers verbatim.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _clean_name(raw: Any, fallback: str) -> str:
    """Strip the model-class prefix + trailing junk from a model name.

    ``"AttackModel_Attack_"`` → ``"Attack"``; ``"ProjectileModel_Projectile"``
    → ``"Projectile"``; ``""``/None → fallback.
    """
    if isinstance(raw, str) and raw:
        name = raw.split("_", 1)[-1] if "_" in raw else raw
        name = name.strip("_").strip()
        return name or fallback
    return fallback


# ---------------------------------------------------------------------------
# Projectile / attack / tier walkers (raw behaviors[] → cleaned node)
# ---------------------------------------------------------------------------


def _clean_projectile(proj: dict) -> dict:
    """Flatten a raw projectile model + its ``behaviors[]`` into a cleaned node.

    Pulls combat numbers from the projectile itself (pierce/radius), its
    ``DamageModel`` (damage + ``immuneBloonProperties`` → damage type), its
    travel model (speed/lifespan), tag damage modifiers, knockback push, and
    nested ``CreateEffect…`` children. Only the fields the runtime reads are
    emitted (plus a few neighbours), per the extraction plan's contract.
    """
    from utils.btd6.damage_types import decode_damage_type

    out: dict = {"name": _clean_projectile_name(proj)}
    out["pierce"] = _num(proj.get("pierce", 0))
    out["maxPierce"] = _num(proj.get("maxPierce", 0))
    for key in (
        "ignoreBlockers",
        "usePointCollisionWithBloons",
        "canCollisionBeBlockedByMapLos",
    ):
        out[key] = bool(proj.get(key, False))
    out["radius"] = _num(proj.get("radius", 0))
    out["vsBlockerRadius"] = _num(proj.get("vsBlockerRadius", 0))

    dmg = _first(proj, "DamageModel")
    if dmg is not None:
        out["damage"] = _num(dmg.get("damage", 0))
        out["maxDamage"] = _num(dmg.get("maxDamage", 0))
        ibp = dmg.get("immuneBloonProperties")
        if isinstance(ibp, int):
            dt = decode_damage_type(ibp)
            out["damage_type"] = dt.name
            out["cannot_pop"] = dt.cannot_pop
            out["immuneBloonProperties"] = ibp
        out["distributeToChildren"] = bool(dmg.get("distributeToChildren", False))
        out["overrideDistributeBlocker"] = bool(
            dmg.get("overrideDistributeBlocker", False),
        )
        out["ignoreImmunityDestroy"] = bool(dmg.get("ignoreImmunityDestroy", False))

    travel = _first(
        proj,
        "TravelStraitModel",
        "TravelCurvyModel",
        "TravelStraightModel",
    )
    if travel is not None:
        if "speed" in travel:
            out["speed"] = _num(travel["speed"])
        if "lifespan" in travel:
            out["lifespan"] = _num(travel["lifespan"])

    # Tag-based damage modifiers → the flat ``damageModifierFor<Tag>`` the UI
    # reads. The real bonus is an ADDITIVE stored in ``damageAddative`` (sic —
    # the field is misspelled in the model). ``damageMultiplier`` is a *separate*
    # field that is a neutral ``1.0`` in all but 2 cases across the whole roster,
    # so reading it alone (the old bug) missed 2,467 real bonuses and made it
    # look like the mechanic had been removed — it had not (Ultra-Juggernaut
    # Lead +20 / Ceramic +8 are right here in ``damageAddative``, identical to
    # the wiki). Our schema's ``damageModifierFor<Tag>`` holds that additive.
    for mod in _behaviors(proj, "DamageModifierForTagModel"):
        key = _TAG_TO_DAMAGE_MOD.get(str(mod.get("tag")))
        if not key:
            continue
        add = mod.get("damageAddative")
        if isinstance(add, (int, float)) and add != 0:
            out[key] = _num(add)

    knock = _first(proj, "KnockbackModel")
    if knock is not None and "distance" in knock:
        out["pushAmount"] = _num(knock["distance"])

    # filterInvisible: a ProjectileFilterModel with an invisible filter, or the
    # projectile's own filters. The wiki surfaces it as a plain bool.
    out["filterInvisible"] = _projectile_filters_invisible(proj)

    effects = _clean_effects(proj)
    if effects:
        out["effects"] = effects
    return out


def _spawned_projectiles(behavior: dict) -> list[dict]:
    """Child ``ProjectileModel``s a spawn behavior holds, by *structure* not name.

    Spawn models reference their child projectile under many field names —
    ``projectile`` (CreateProjectileOnContact / AlternateProjectile /
    UnstableConcoctionSplash …), ``projectileModel`` (ProjectileOverTime /
    PreEmptiveStrikeLauncher / Submerge …), ``alternateProjectile``
    (PrinceOfDarkness), ``projectileZOMG``/``projectileBFB`` (PhoenixRebirth),
    etc. Matching the *parent type* (the old ``startswith("CreateProjectile")``
    rule) silently dropped ~13 spawn models — and the secondary cluster bombs /
    sub pre-emptive strike / alch splash they fire. So detect a child by its own
    ``$type`` instead, scanning every field value (and one level of list).
    """
    out: list[dict] = []
    for key, value in behavior.items():
        if key == "$type":
            continue
        if isinstance(value, dict) and _short_type(value) == "ProjectileModel":
            out.append(value)
        elif isinstance(value, list):
            out.extend(
                v
                for v in value
                if isinstance(v, dict) and _short_type(v) == "ProjectileModel"
            )
    return out


def _projectile_signature(node: dict) -> tuple:
    """Identity for de-duping projectiles reachable via two spawn paths (an
    explosion can be both an on-contact and on-expire child). Same name + same
    headline stats ⇒ the same projectile; the wiki lists it once, so do we.
    """
    return (
        node.get("name"),
        node.get("damage"),
        node.get("pierce"),
        node.get("radius"),
        node.get("damage_type"),
    )


def _collect_projectiles(proj: dict, _depth: int = 0) -> list[dict]:
    """Flatten a projectile + every projectile it spawns into sibling nodes.

    Many towers deal their damage on a *child* projectile, not the one thrown:
    a bomb's thrown shell carries no ``DamageModel`` — the explosion spawned on
    contact does (the wiki surfaces both as siblings, "Projectile" + "Explosion").
    Cluster/MOAB-shred towers nest further, so we recurse (depth-capped), emit
    each as its own cleaned projectile, and drop exact duplicates.
    """
    out = [_clean_projectile(proj)]
    if _depth < 4:
        for behavior in proj.get("behaviors", []) or []:
            if not isinstance(behavior, dict):
                continue
            for child in _spawned_projectiles(behavior):
                out.extend(_collect_projectiles(child, _depth + 1))
    return out


def _dedupe_projectiles(projectiles: list[dict]) -> list[dict]:
    """Drop projectiles with an identical signature — a child reachable via two
    spawn paths (on-contact *and* on-expire) appears once, as the wiki lists it.
    """
    seen: set[tuple] = set()
    out: list[dict] = []
    for node in projectiles:
        sig = _projectile_signature(node)
        if sig not in seen:
            seen.add(sig)
            out.append(node)
    return out


def _clean_projectile_name(proj: dict) -> str:
    raw_id = proj.get("id")
    if isinstance(raw_id, str) and raw_id:
        return raw_id
    return _clean_name(proj.get("name"), "Projectile")


def _projectile_filters_invisible(proj: dict) -> bool:
    """True if the projectile can hit camo/invisible bloons (a filter allows it)."""
    for filt in proj.get("filters", []) or []:
        if not isinstance(filt, dict):
            continue
        if _short_type(filt) == "FilterInvisibleModel":
            return bool(filt.get("isActive", True))
    return False


def _clean_effects(proj: dict) -> list[dict]:
    """Named child effects a projectile creates (``CreateEffect…`` / status models).

    The runtime only reads ``name`` + ``lifespan`` off these (stun detection,
    Pro view), so we keep it lean.
    """
    out: list[dict] = []
    for eff in _behaviors(
        proj,
        "CreateEffectOnExhaustFractionModel",
        "CreateEffectOnExpireModel",
        "AddBehaviorToBloonModel",
        "SlowModel",
        "FreezeModel",
        "StunModel",
    ):
        node: dict = {"name": _clean_name(eff.get("name"), _short_type(eff))}
        if "lifespan" in eff:
            node["lifespan"] = _num(eff["lifespan"])
        out.append(node)
    return out


def _eject(weapon: dict) -> str | None:
    parts = [weapon.get(k) for k in ("ejectX", "ejectY", "ejectZ")]
    if all(p is None for p in parts):
        return None
    return ", ".join(str(_num(p if p is not None else 0)) for p in parts)


def _clean_attack(attack: dict, index: int) -> dict:
    """A raw ``AttackModel`` → cleaned attack node (one entry per weapon's projectile)."""
    out: dict = {"name": _clean_name(attack.get("name"), f"Attack {index + 1}")}
    weapons = attack.get("weapons", []) or []
    if weapons:
        first = weapons[0]
        if "rate" in first:
            out["rate"] = _num(first["rate"])
        ej = _eject(first)
        if ej is not None:
            out["eject"] = ej
        out["fireWithoutTarget"] = bool(first.get("fireWithoutTarget", False))
        out["fireBetweenRounds"] = bool(first.get("fireBetweenRounds", False))
    projectiles: list[dict] = []
    for w in weapons:
        if not isinstance(w, dict):
            continue
        if isinstance(w.get("projectile"), dict):
            projectiles.extend(_collect_projectiles(w["projectile"]))
        # A weapon can also fire projectiles via its own behaviors — e.g. the
        # bomb's secondary cluster comes from an ``AlternateProjectileModel`` on
        # the weapon, not from ``weapon.projectile``.
        for behavior in w.get("behaviors", []) or []:
            if isinstance(behavior, dict):
                for child in _spawned_projectiles(behavior):
                    projectiles.extend(_collect_projectiles(child))
    out["projectiles"] = _dedupe_projectiles(projectiles)
    # ``count`` (projectiles per shot) has no single reliable source in the dump
    # — ``len(weapons)`` and the per-weapon ``emission.count`` each diverge from
    # the trusted wiki value on a third of tiers (see the fidelity audit). Keep
    # the historical ``len(weapons)`` so the mapper output is stable, and let the
    # audit flag ``count`` as SUSPECT so the overlay never refreshes it.
    out["count"] = len(weapons)
    out["targetTypes"] = "Depends on targeting option"
    if "range" in attack:
        out["range"] = _num(attack["range"])
    out["attackThroughWalls"] = bool(attack.get("attackThroughWalls", False))
    out["framesBeforeRetarget"] = _num(attack.get("framesBeforeRetarget", 0))
    out["sharedGridRange"] = _num(attack.get("sharedGridRange", 0))
    # The wiki surfaces an attack-level camo flag = any projectile can see camo.
    out["filterInvisible"] = any(p.get("filterInvisible") for p in out["projectiles"])
    return out


def _clean_ability(ability: dict, index: int) -> dict:
    # Prefer the game's own player-facing name (``displayName`` is already English
    # — "Cocktail of Fire", "Firestorm") over the internal model name.
    display = ability.get("displayName")
    name = display if isinstance(display, str) and display else None
    out: dict = {
        "name": name or _clean_name(ability.get("name"), f"Ability {index + 1}"),
    }
    if "cooldown" in ability:
        out["cooldown"] = _num(ability["cooldown"])
    # An ability fires its own AttackModels; surface their projectiles + bad dmg.
    projectiles: list[dict] = []
    for attack in _behaviors(ability, "AttackModel"):
        for w in attack.get("weapons", []) or []:
            if isinstance(w, dict) and isinstance(w.get("projectile"), dict):
                projectiles.extend(_collect_projectiles(w["projectile"]))
    if projectiles:
        out["projectiles"] = _dedupe_projectiles(projectiles)
    for key in ("damageToBad", "damageToNonBad"):
        # These live on DamageModel children of the ability's attacks.
        for attack in _behaviors(ability, "AttackModel"):
            for w in attack.get("weapons", []) or []:
                proj = w.get("projectile") if isinstance(w, dict) else None
                dm = _first(proj, "DamageModel") if isinstance(proj, dict) else None
                if dm and key in dm:
                    out[key] = _num(dm[key])
    return out


def _income(model: dict) -> dict:
    """Cash-income fields the runtime scans for (banana farm / village / etc.)."""
    out: dict = {}
    per_round = _first(model, "PerRoundCashBonusTowerModel")
    if per_round is not None and "cashPerRound" in per_round:
        out["cashPerRound"] = _num(per_round["cashPerRound"])
    gen = _first(model, "BananaCentralBuffModel", "MoneyPerRoundModel")
    if gen is not None and "minimum" in gen:
        out["cashMinimum"] = _num(gen["minimum"])
    return out


def _placement(model: dict) -> dict:
    area = model.get("areaTypes", []) or []
    return {
        "placeableOnLand": _AREA_LAND in area,
        "placeableOnWater": _AREA_WATER in area,
        "placeableOnTrack": _AREA_TRACK in area,
    }


def _target_types(model: dict) -> dict:
    """The ``targetTypeFirst/Last/Close/Strong`` booleans from ``targetTypes[]``."""
    available = {
        t.get("id") for t in model.get("targetTypes", []) or [] if isinstance(t, dict)
    }
    return {
        "targetTypeFirst": "First" in available,
        "targetTypeLast": "Last" in available,
        "targetTypeClose": "Close" in available,
        "targetTypeStrong": "Strong" in available,
    }


def _map_tier(model: dict) -> dict:
    """A full tower-state model file → one cleaned tier node."""
    tier: dict = {}
    tier.update(_placement(model))
    if "range" in model:
        tier["range"] = _num(model["range"])
    theme = model.get("towerSelectionMenuThemeId")
    if isinstance(theme, str) and theme:
        tier["towerSelectionMenuThemeId"] = theme
    # The footprint is a top-level model (not in behaviors[]).
    foot = model.get("footprint")
    if isinstance(foot, dict):
        if "radius" in foot:
            tier["footprintRadius"] = _num(foot["radius"])
        tier["doesntBlockTowerPlacement"] = bool(
            foot.get("doesntBlockTowerPlacement", False),
        )
    attacks = _behaviors(model, "AttackModel")
    tier["attacks"] = [_clean_attack(a, i) for i, a in enumerate(attacks)]
    abilities = _behaviors(model, "AbilityModel")
    if abilities:
        tier["abilities"] = [_clean_ability(a, i) for i, a in enumerate(abilities)]
    tier.update(_target_types(model))
    income = _income(model)
    if income:
        # Income is surfaced via the runtime's recursive special-scan
        # (_iter_dicts), which walks the whole tier — top-level keys are found.
        tier.update(income)
    return tier


# ---------------------------------------------------------------------------
# Name allowlist (catalog ids → dump folder), built + asserted at run time
# ---------------------------------------------------------------------------


def _pascal(canonical: str) -> str:
    """``"Captain Churchill"`` → ``"CaptainChurchill"`` (dump folder convention)."""
    return "".join(part for part in canonical.replace("-", " ").split(" ") if part)


def _load_catalog(name: str, id_key: str) -> dict[str, str]:
    raw = json.loads((_DATA_ROOT / name).read_text(encoding="utf-8"))
    if isinstance(raw, list):
        rows: list = raw
    else:
        # Catalogs wrap their rows under a list value (e.g. {"towers": [...]});
        # the metadata keys (data_version, …) are scalars/strings.
        rows = next((v for v in raw.values() if isinstance(v, list)), [])
    out: dict[str, str] = {}
    for row in rows:
        if isinstance(row, dict) and row.get(id_key) and row.get("canonical"):
            out[row[id_key]] = row["canonical"]
    return out


def build_allowlist(dump: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return ``(towers, heroes)`` mapping catalog id → dump folder name.

    Asserts every catalog id resolves to exactly one existing folder; fails
    loudly otherwise (the plan's explicit anti-"blind PascalCase" guard).
    """
    towers_cat = _load_catalog("towers.json", "id")
    heroes_cat = _load_catalog("heroes.json", "id")
    towers_dir = dump / "Towers"

    def resolve(catalog: dict[str, str], label: str) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for tid, canonical in catalog.items():
            folder = _pascal(canonical)
            if not (towers_dir / folder).is_dir():
                raise SystemExit(
                    f"allowlist: {label} id {tid!r} ({canonical!r}) → folder "
                    f"{folder!r} not found under {towers_dir}",
                )
            resolved[tid] = folder
        return resolved

    return resolve(towers_cat, "tower"), resolve(heroes_cat, "hero")


# ---------------------------------------------------------------------------
# Tower / hero / paragon mappers
# ---------------------------------------------------------------------------


@dataclass
class MapResult:
    payload: dict
    warnings: list[str] = field(default_factory=list)


def _dump_version(dump: Path) -> str:
    """The game version the dump was taken at — the dump's commit message
    (Mod Helper stamps it e.g. ``55.0``).
    """
    import subprocess

    try:
        msg = subprocess.check_output(
            ["git", "-C", str(dump), "log", "-1", "--format=%s"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        # Take the leading version-looking token (e.g. "55.0" from "55.0 fixes").
        token = msg.split()[0] if msg else ""
        if token and token[0].isdigit():
            return token
    except Exception:  # noqa: BLE001 - best-effort version stamp
        pass
    return ""


def _upgrades_for(tdir: Path, dump: Path) -> list[dict]:
    """Per-upgrade name/cost/xp from ``Upgrades/*.json``, our schema's path/tier.

    Each tower-state file's ``upgrades`` is a flat list of ``UpgradePathModel``
    ``{tower, upgrade}`` entries, but a single state only lists the upgrades
    *reachable from it* (the base file holds just the 3 tier-1 steps). The full
    15 are the **union** across every crosspath file. The canonical path/tier +
    cost/xp live in ``Upgrades/<name>.json`` (``path``/``tier`` 0-indexed → +1).
    """
    names: list[str] = []
    seen: set[str] = set()
    for fp in sorted(tdir.glob("*.json")):
        if fp.stem.endswith("-Paragon"):
            continue
        try:
            data = json.loads(fp.read_text("utf-8"))
        except Exception:  # noqa: BLE001, S112
            continue
        for entry in data.get("upgrades", []) or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("upgrade")
            if isinstance(name, str) and name and name not in seen:
                seen.add(name)
                names.append(name)
    tt = _text_table(dump)
    out: list[dict] = []
    for name in names:
        up = _read_upgrade(dump, name)
        if up is None:
            continue
        path = up.get("path")
        tier = up.get("tier")
        if not isinstance(path, int) or not isinstance(tier, int):
            continue
        entry = {
            "path": path + 1,
            "tier": tier + 1,
            "name": up.get("name", name),
            "cost": _num(up.get("cost", 0)),
            "xp": _num(up.get("xpCost", 0)),
        }
        # Game-authored description ("what this upgrade grants"), resolved through
        # the upgrade's localization key — the bot's most reliable upgrade prose.
        locs = up.get("LocsKey")
        if isinstance(locs, str) and locs:
            description = tt.get(f"{locs} Description")
            if isinstance(description, str) and description:
                entry["description"] = description
        out.append(entry)
    out.sort(key=lambda u: (u["path"], u["tier"]))
    return out


_TEXT_TABLE_CACHE: dict[str, dict[str, str]] = {}


def _text_table(dump: Path) -> dict[str, str]:
    """The dump's ``textTable.json`` (game display strings + descriptions), cached
    per dump path. Empty dict if absent — name/description lookups then no-op.
    """
    key = str(dump)
    if key not in _TEXT_TABLE_CACHE:
        fp = dump / "textTable.json"
        try:
            raw = json.loads(fp.read_text("utf-8")) if fp.exists() else {}
        except (OSError, json.JSONDecodeError):
            raw = {}
        _TEXT_TABLE_CACHE[key] = {k: v for k, v in raw.items() if isinstance(v, str)}
    return _TEXT_TABLE_CACHE[key]


def _read_upgrade(dump: Path, upgrade_id: Any) -> dict | None:
    if not isinstance(upgrade_id, str) or not upgrade_id:
        return None
    path = dump / "Upgrades" / f"{upgrade_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def map_tower(dump: Path, tower_id: str, canonical: str, version: str) -> MapResult:
    folder = _pascal(canonical)
    tdir = dump / "Towers" / folder
    base = json.loads((tdir / f"{folder}.json").read_text("utf-8"))
    warnings: list[str] = []

    tower_set = base.get("towerSet")
    category = _TOWER_SET.get(int(tower_set)) if isinstance(tower_set, int) else None
    if category is None:
        warnings.append(f"unknown towerSet {tower_set!r}")

    tiers: dict[str, dict] = {}
    for fp in sorted(tdir.glob(f"{folder}-*.json")):
        code = fp.stem.rsplit("-", 1)[-1]
        if len(code) != 3 or not code.isdigit():
            continue  # skip -Paragon and any non-tier file
        model = json.loads(fp.read_text("utf-8"))
        node = _map_tier(model)
        node["code"] = code
        node["crosspath"] = "-".join(code)
        tiers[code] = node
    # base file is the 000 tier
    base_node = _map_tier(base)
    base_node["code"] = "000"
    base_node["crosspath"] = "0-0-0"
    tiers["000"] = base_node

    payload = {
        "tower_id": tower_id,
        "canonical": canonical,
        "game_version": version,
        "source": _SOURCE,
        "base_cost": _num(base.get("cost", 0)),
        "category": category,
        "upgrades": _upgrades_for(tdir, dump),
        "tiers": dict(sorted(tiers.items())),
    }
    if not tiers:
        warnings.append("no tiers parsed")
    return MapResult(payload=payload, warnings=warnings)


def map_hero(dump: Path, hero_id: str, canonical: str, version: str) -> MapResult:
    folder = _pascal(canonical)
    hdir = dump / "Towers" / folder
    base_fp = hdir / f"{folder}.json"
    warnings: list[str] = []
    base = json.loads(base_fp.read_text("utf-8"))

    levels: dict[str, dict] = {}
    for level in range(1, 21):
        # Heroes: one file per level, named "<Folder> N.json" (level 1 is base).
        fp = hdir / f"{folder} {level}.json"
        model = base if level == 1 and not fp.exists() else None
        if fp.exists():
            model = json.loads(fp.read_text("utf-8"))
        if model is None:
            continue
        node = _map_tier(model)
        node["level"] = level
        levels[str(level)] = node
    if not levels:
        warnings.append("no level files found")

    payload = {
        "hero_id": hero_id,
        "canonical": canonical,
        "game_version": version,
        "source": _SOURCE,
        "base_cost": _num(base.get("cost", 0)),
        "cost_chimps": _num(base.get("cost", 0)),
        "levels": levels,
    }
    return MapResult(payload=payload, warnings=warnings)


def _existing_paragons() -> dict[str, tuple[str, dict]]:
    """Index committed paragon files by ``tower_id`` → (file stem, payload).

    Paragon *cost / canonical name / XP* are not cleanly exposed in the dump
    (its ``<Name>-Paragon.json`` ``cost`` is the base monkey's placement cost,
    not the paragon's price), so we preserve that metadata from the existing
    bloonswiki-sourced file and replace only the combat ``base`` node.
    """
    out: dict[str, tuple[str, dict]] = {}
    pdir = _STATS_DIR / "paragons"
    if not pdir.is_dir():
        return out
    for fp in pdir.glob("*.json"):
        try:
            data = json.loads(fp.read_text("utf-8"))
        except Exception:  # noqa: BLE001, S112
            continue
        tid = data.get("tower_id")
        if isinstance(tid, str) and tid:
            out[tid] = (fp.stem, data)
    return out


def map_paragon(
    dump: Path,
    tower_id: str,
    tower_canonical: str,
    version: str,
    existing: dict[str, tuple[str, dict]],
) -> tuple[str, MapResult] | None:
    folder = _pascal(tower_canonical)
    fp = dump / "Towers" / folder / f"{folder}-Paragon.json"
    if not fp.exists():
        return None
    model = json.loads(fp.read_text("utf-8"))
    warnings: list[str] = []
    base_node = _map_tier(model)

    prior = existing.get(tower_id)
    if prior is None:
        # No committed file to inherit metadata from — emit what we can and warn,
        # naming the file after the tower id so it is obvious it needs curation.
        stem = tower_id
        payload = {
            "tower_id": tower_id,
            "tower_canonical": tower_canonical,
            "game_version": version,
            "source": _SOURCE,
            "base": base_node,
        }
        warnings.append("no existing paragon file — cost/name metadata missing")
    else:
        stem, prior_payload = prior
        payload = dict(prior_payload)  # preserve canonical/cost/cost_chimps/xp/etc.
        payload["game_version"] = version
        payload["source"] = _SOURCE
        payload["base"] = base_node
        payload.pop("is_prose_sourced", None)  # now module-exact, not prose
    if not base_node.get("attacks") and not base_node.get("abilities"):
        warnings.append("paragon node has no attacks or abilities")
    return stem, MapResult(payload=payload, warnings=warnings)


# ---------------------------------------------------------------------------
# Fidelity audit — mapper output vs the committed (wiki-sourced) ground truth
# ---------------------------------------------------------------------------
#
# A v55 cutover that blindly wrote the mapper's numbers over the committed files
# would *corrupt* correct data: the dump represents several mechanics
# differently from the wiki (verified — e.g. ``DamageModifierForTagModel`` is a
# uniform ``1.0`` in the dump while the wiki carries the real Lead/Ceramic
# bonus). Before any overlay we must know, field by field, where the mapper
# agrees with the trusted data (safe to refresh), where it differs rarely
# (likely a genuine v55 delta), and where it differs systematically (a mapper /
# representation gap — must NOT be overlaid). This audit produces exactly that
# verdict so the overlay (next step) only touches fields it can trust.

# A field is SUSPECT (a systematic mapper gap, never overlay it) above this
# divergence rate; at-or-below it the diffs are sparse enough to be real v55
# deltas worth reviewing (DELTA); zero diffs is CLEAN (safe to overlay).
_AUDIT_SUSPECT_RATE = 0.20


@dataclass
class _FieldStat:
    total: int = 0
    diffs: int = 0
    examples: list[tuple[str, Any, Any]] = field(default_factory=list)

    @property
    def rate(self) -> float:
        return self.diffs / self.total if self.total else 0.0

    @property
    def verdict(self) -> str:
        if self.diffs == 0:
            return "CLEAN"
        return "SUSPECT" if self.rate > _AUDIT_SUSPECT_RATE else "DELTA"


def _is_audit_scalar(value: Any) -> bool:
    """Numbers and bools — the leaves an overlay could refresh. (Names/strings
    are curated and never overlaid, so they are out of scope here.)
    """
    return isinstance(value, (int, float, bool))


def _audit_equal(committed: Any, mapped: Any) -> bool:
    """Equal *for fidelity purposes* — bools compared identity, numbers compared
    rounded to 4 decimals so the wiki's rounded values (``0.3616``) don't read as
    a diff against the dump's full precision (``0.36160713``). That float-
    precision noise is a representation difference, not a data change.
    """
    if isinstance(committed, bool) or isinstance(mapped, bool):
        return committed is mapped
    if isinstance(committed, (int, float)) and isinstance(mapped, (int, float)):
        return round(float(committed), 4) == round(float(mapped), 4)
    return committed == mapped


def _align_named(
    committed: list,
    mapped: list,
) -> list[tuple[str, dict, dict]] | None:
    """Pair two lists of dicts by their ``name`` — or ``None`` to fall back to
    positional alignment.

    Attacks, projectiles and abilities are emitted in a different order by the
    two sources (the mapper flattens sub-projectiles depth-first; the wiki
    orders them its own way), so an index diff reports every field as a phantom
    swap. When both sides are dicts with **unique** names, pairing by name is
    the true alignment. Anything else (scalars, missing/duplicate names) keeps
    positional comparison.
    """

    def names(rows: list) -> list[str] | None:
        if not rows or not all(isinstance(r, dict) and "name" in r for r in rows):
            return None
        ns = [str(r["name"]) for r in rows]
        return ns if len(set(ns)) == len(ns) else None

    cn, mn = names(committed), names(mapped)
    if cn is None or mn is None:
        return None
    mmap = {str(r["name"]): r for r in mapped}
    return [(n, c, mmap[n]) for n, c in zip(cn, committed, strict=True) if n in mmap]


def _walk_audit(
    committed: Any,
    mapped: Any,
    key: str,
    stats: dict[str, _FieldStat],
    ctx: str,
) -> None:
    """Compare matching leaves of the two trees, tallying per-field-name stats.

    Walks only keys/indices present in both: a key the mapper omits (e.g. a
    curated description, or a ``1.0`` modifier we deliberately drop) is not a
    diff — the overlay simply keeps the curated value there.
    """
    if isinstance(committed, dict) and isinstance(mapped, dict):
        for k in committed:
            if k in mapped:
                _walk_audit(committed[k], mapped[k], k, stats, f"{ctx}.{k}")
    elif isinstance(committed, list) and isinstance(mapped, list):
        pairs = _align_named(committed, mapped)
        if pairs is not None:  # dict-lists with unique names — align by name
            for name, citem, mitem in pairs:
                _walk_audit(citem, mitem, key, stats, f"{ctx}[{name}]")
        else:  # positional fallback (scalars / unnamed / duplicate names)
            for i in range(min(len(committed), len(mapped))):
                _walk_audit(committed[i], mapped[i], key, stats, f"{ctx}[{i}]")
    elif _is_audit_scalar(committed) and _is_audit_scalar(mapped):
        # bool and 1/1.0 compare equal in Python; keep them in separate buckets
        # so a numeric field and a same-named flag never pool.
        bucket = f"bool:{key}" if isinstance(committed, bool) else key
        st = stats.setdefault(bucket, _FieldStat())
        st.total += 1
        if not _audit_equal(committed, mapped):
            st.diffs += 1
            if len(st.examples) < 5:
                st.examples.append((ctx, committed, mapped))


def _audit_upgrades(
    committed: list,
    mapped: list,
    stats: dict[str, _FieldStat],
    ctx: str,
) -> None:
    """Upgrades aligned by ``(path, tier)`` — index alignment produces phantom
    diffs because the two sources order the 15 upgrades differently.
    """

    def keyed(rows: list) -> dict[tuple, dict]:
        out: dict[tuple, dict] = {}
        for row in rows:
            if isinstance(row, dict) and "path" in row and "tier" in row:
                out[(row["path"], row["tier"])] = row
        return out

    cmap, mmap = keyed(committed), keyed(mapped)
    for k in cmap:
        if k in mmap:
            _walk_audit(cmap[k], mmap[k], "upgrade", stats, f"{ctx}[{k[0]}-{k[1]}]")


def _map_for_audit(
    dump: Path,
    towers: dict[str, str],
    heroes: dict[str, str],
    version: str,
) -> dict[str, dict]:
    """``committed-relative-path -> mapped payload`` for every entity that has a
    committed file to compare against.
    """
    existing = _existing_paragons()
    out: dict[str, dict] = {}
    for tid, canonical in towers.items():
        out[f"stats/{tid}.json"] = map_tower(dump, tid, canonical, version).payload
        par = map_paragon(dump, tid, canonical, version, existing)
        if par is not None:
            stem, res = par
            out[f"stats/paragons/{stem}.json"] = res.payload
    for hid, canonical in heroes.items():
        out[f"stats/heroes/{hid}.json"] = map_hero(
            dump,
            hid,
            canonical,
            version,
        ).payload
    return out


def audit(dump: Path) -> dict[str, _FieldStat]:
    """Per-field fidelity stats across every entity with a committed file."""
    towers, heroes = build_allowlist(dump)
    version = _dump_version(dump)
    stats: dict[str, _FieldStat] = {}
    for rel, mapped in _map_for_audit(dump, towers, heroes, version).items():
        committed_fp = _DATA_ROOT / rel
        if not committed_fp.exists():
            continue
        committed = json.loads(committed_fp.read_text("utf-8"))
        for key in committed:
            if key == "upgrades" and isinstance(committed.get("upgrades"), list):
                _audit_upgrades(
                    committed["upgrades"],
                    mapped.get("upgrades", []),
                    stats,
                    rel,
                )
            elif key in mapped:
                _walk_audit(committed[key], mapped[key], key, stats, f"{rel}.{key}")
    return stats


def render_audit(stats: dict[str, _FieldStat]) -> str:
    """A human-readable trust report, SUSPECT first then DELTA then CLEAN."""
    order = {"SUSPECT": 0, "DELTA": 1, "CLEAN": 2}
    rows = sorted(
        stats.items(),
        key=lambda kv: (order[kv[1].verdict], -kv[1].diffs),
    )
    lines = [
        "BTD6 game-data mapper fidelity audit (mapped v55 vs committed wiki data)",
        f"  SUSPECT = systematic gap, never overlay (>{_AUDIT_SUSPECT_RATE:.0%} diff)",
        "  DELTA   = sparse diffs, review as genuine v55 changes",
        "  CLEAN   = mapper matches the trusted data, safe to overlay",
        "",
        f"  {'field':36}{'verdict':9}{'diffs':>7}{'total':>8}{'rate':>7}",
    ]
    for name, st in rows:
        lines.append(
            f"  {name:36}{st.verdict:9}{st.diffs:>7}{st.total:>8}{st.rate:>6.0%}",
        )
        if st.verdict != "CLEAN":
            for ctx, cv, mv in st.examples[:3]:
                where = ctx.split("/")[-1]
                lines.append(f"        {where}: {cv!r} → {mv!r}")
    safe = sorted(n for n, s in stats.items() if s.verdict in ("CLEAN", "DELTA"))
    lines += ["", f"  overlay-eligible (CLEAN+DELTA): {', '.join(safe)}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Safe numeric overlay — refresh trusted v55 numbers onto the curated files
# ---------------------------------------------------------------------------
#
# The committed tower/hero files are bloonswiki-sourced (v53) with curated names,
# descriptions and structure. The overlay refreshes ONLY the audit-trusted
# numeric / immunity leaves to their v55 values, in place, aligning lists by
# name (and upgrades by (path, tier)) — it never adds or removes a projectile /
# attack / upgrade, so the curated structure + names survive intact. Fields the
# audit can't trust (``count``, the camo/blocker bools tangled in flatten order)
# and all names/descriptions are left untouched.

# Tier-/level-level scalar fields that are SAFE to overlay: each occurs once per
# tier dict, so there is no alignment ambiguity. We deliberately do NOT overlay
# per-projectile / per-attack / per-ability stats — projectile and ability names
# are not reliable keys across the two sources (the wiki calls a projectile
# "Projectile" where the dump calls it "BaseProjectile"; "Ability" is reused for
# distinct abilities), so matching by name writes values onto the WRONG node
# (verified: it would put the Superstorm's 100 dmg on Druid's base dart, and
# Legend-of-the-Night's 180s cooldown on Dark Knight's other ability). Those
# stats stay curated; the audit shows them mostly CLEAN anyway.
_OVERLAY_FIELDS: frozenset[str] = frozenset({"range", "footprintRadius"})


def _overlay_node(committed: Any, mapped: Any, changes: list[str], ctx: str) -> None:
    """Refresh ``_OVERLAY_FIELDS`` scalar leaves of ``committed`` from ``mapped``.

    Recurses **dicts only** — never lists. Lists (attacks/projectiles/abilities)
    can't be aligned safely across the two sources (see ``_OVERLAY_FIELDS``), so
    they are left entirely curated rather than risk a mis-keyed write.
    """
    if not (isinstance(committed, dict) and isinstance(mapped, dict)):
        return
    for key, cval in committed.items():
        if key not in mapped:
            continue
        mval = mapped[key]
        if key in _OVERLAY_FIELDS and _is_audit_scalar(cval) and _is_audit_scalar(mval):
            if not _audit_equal(cval, mval) and type(cval) is not bool:
                committed[key] = mval
                changes.append(f"{ctx}.{key}: {cval!r} → {mval!r}")
        elif isinstance(cval, dict):
            _overlay_node(cval, mval, changes, f"{ctx}.{key}")


def _overlay_upgrades(committed: dict, mapped: dict, changes: list[str]) -> None:
    """Refresh upgrade ``cost`` / ``xp`` aligned by ``(path, tier)`` (keep names)."""
    mmap = {
        (u.get("path"), u.get("tier")): u
        for u in mapped.get("upgrades", [])
        if isinstance(u, dict)
    }
    for up in committed.get("upgrades", []) or []:
        if not isinstance(up, dict):
            continue
        m = mmap.get((up.get("path"), up.get("tier")))
        if not m:
            continue
        for field_name in ("cost", "xp"):
            if field_name in up and field_name in m and up[field_name] != m[field_name]:
                changes.append(
                    f"upgrade[{up.get('path')}-{up.get('tier')}].{field_name}: "
                    f"{up[field_name]!r} → {m[field_name]!r}",
                )
                up[field_name] = m[field_name]


def overlay_payload(committed: dict, mapped: dict, version: str) -> list[str]:
    """Overlay ``mapped`` v55 numbers onto a committed tower/hero ``dict`` in
    place; return the list of changes made.
    """
    changes: list[str] = []
    for key in ("base_cost", "category"):
        if key in committed and key in mapped and committed[key] != mapped[key]:
            changes.append(f"{key}: {committed[key]!r} → {mapped[key]!r}")
            committed[key] = mapped[key]
    if committed.get("upgrades") and mapped.get("upgrades"):
        _overlay_upgrades(committed, mapped, changes)
    for container in ("tiers", "levels"):
        if container in committed and container in mapped:
            _overlay_node(
                committed[container],
                mapped[container],
                changes,
                container,
            )
    if changes:
        committed["game_version"] = version
        prior = str(committed.get("source", ""))
        stamp = f"BTD Mod Helper game data v{version} (numeric overlay)"
        if "Mod Helper" not in prior:
            committed["source"] = f"{prior}; {stamp}" if prior else stamp
    return changes


# ---------------------------------------------------------------------------
# Anchors + CLI
# ---------------------------------------------------------------------------

_ANCHORS = {"DartMonkey": 200.0, "SuperMonkey": 2500.0}


def validate_anchors(dump: Path) -> list[str]:
    errors: list[str] = []
    for folder, expected in _ANCHORS.items():
        fp = dump / "Towers" / folder / f"{folder}.json"
        if not fp.exists():
            errors.append(f"{folder}: base file missing")
            continue
        cost = json.loads(fp.read_text("utf-8")).get("cost")
        if cost != expected:
            errors.append(f"{folder}: cost {cost!r} != expected {expected}")
    return errors


def overlay_all(dump: Path, *, dry_run: bool) -> dict[str, list[str]]:
    """Overlay v55 numbers onto every curated tower + hero file. Returns
    ``{relative_path: [change, …]}`` for files that changed (generated heroes are
    already v55, so they no-op). Paragons are intentionally out of scope.
    """
    towers, heroes = build_allowlist(dump)
    version = _dump_version(dump)
    report: dict[str, list[str]] = {}

    def apply(fp: Path, rel: str, mapped: dict) -> None:
        if not fp.exists():
            return
        committed = json.loads(fp.read_text("utf-8"))
        changes = overlay_payload(committed, mapped, version)
        if changes:
            report[rel] = changes
            if not dry_run:
                _write(fp, committed)

    for tid, canonical in towers.items():
        apply(
            _STATS_DIR / f"{tid}.json",
            f"stats/{tid}.json",
            map_tower(dump, tid, canonical, version).payload,
        )
    for hid, canonical in heroes.items():
        apply(
            _STATS_DIR / "heroes" / f"{hid}.json",
            f"stats/heroes/{hid}.json",
            map_hero(dump, hid, canonical, version).payload,
        )
    return report


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dump",
        required=True,
        type=Path,
        help="path to a btd6-game-data clone",
    )
    ap.add_argument("--tower", help="map a single tower by catalog id")
    ap.add_argument("--hero", help="map a single hero by catalog id")
    ap.add_argument(
        "--all",
        action="store_true",
        help="map every tower + hero + paragon",
    )
    ap.add_argument("--validate-anchors", action="store_true")
    ap.add_argument(
        "--audit",
        action="store_true",
        help="report per-field fidelity vs the committed wiki data (no writes)",
    )
    ap.add_argument(
        "--overlay",
        action="store_true",
        help="refresh trusted v55 numbers onto curated tower/hero files",
    )
    ap.add_argument("--dry-run", action="store_true", help="print, do not write")
    args = ap.parse_args(argv)

    dump: Path = args.dump
    if not (dump / "Towers").is_dir():
        raise SystemExit(f"--dump {dump} has no Towers/ — not a game-data clone")

    if args.validate_anchors:
        errs = validate_anchors(dump)
        if errs:
            print("ANCHORS FAILED:")
            for e in errs:
                print(f"  - {e}")
            return 1
        print("anchors OK (Dart 200, Super 2500)")
        return 0

    if args.audit:
        print(render_audit(audit(dump)))
        return 0

    if args.overlay:
        report = overlay_all(dump, dry_run=args.dry_run)
        verb = "would change" if args.dry_run else "changed"
        total = sum(len(v) for v in report.values())
        print(f"overlay: {verb} {len(report)} file(s), {total} leaf value(s)\n")
        for rel in sorted(report):
            print(f"  {rel}  ({len(report[rel])} change(s))")
            for change in report[rel]:
                print(f"      {change}")
        return 0

    towers, heroes = build_allowlist(dump)
    version = _dump_version(dump)
    existing_paragons = _existing_paragons()
    print(
        f"dump version: {version or '?'}  ({len(towers)} towers, {len(heroes)} heroes)",
    )

    all_warnings: list[str] = []

    def emit(payload: dict, dest: Path) -> None:
        if args.dry_run:
            print(f"--- {dest.relative_to(_REPO_ROOT)} ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False)[:1200])
        else:
            _write(dest, payload)
            print(f"wrote {dest.relative_to(_REPO_ROOT)}")

    targets_towers: list[str]
    targets_heroes: list[str]
    if args.tower:
        targets_towers, targets_heroes = [args.tower], []
    elif args.hero:
        targets_towers, targets_heroes = [], [args.hero]
    elif args.all:
        targets_towers, targets_heroes = list(towers), list(heroes)
    else:
        raise SystemExit(
            "nothing to do: pass --tower / --hero / --all / --validate-anchors",
        )

    for tid in targets_towers:
        if tid not in towers:
            raise SystemExit(f"unknown tower id {tid!r} (not in towers.json)")
        res = map_tower(dump, tid, towers[tid], version)
        all_warnings += [f"{tid}: {w}" for w in res.warnings]
        emit(res.payload, _STATS_DIR / f"{tid}.json")
        par = map_paragon(dump, tid, towers[tid], version, existing_paragons)
        if par is not None:
            stem, par_res = par
            all_warnings += [f"{tid} paragon: {w}" for w in par_res.warnings]
            emit(par_res.payload, _STATS_DIR / "paragons" / f"{stem}.json")

    for hid in targets_heroes:
        if hid not in heroes:
            raise SystemExit(f"unknown hero id {hid!r} (not in heroes.json)")
        res = map_hero(dump, hid, heroes[hid], version)
        all_warnings += [f"{hid}: {w}" for w in res.warnings]
        emit(res.payload, _STATS_DIR / "heroes" / f"{hid}.json")

    if all_warnings:
        print(f"\n{len(all_warnings)} warning(s):")
        for w in all_warnings:
            print(f"  - {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
