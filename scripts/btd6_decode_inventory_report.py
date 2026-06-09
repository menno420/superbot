"""SHA-pinned BTD6 decode inventory / audit report — sizes the v55 cutover.

One re-runnable artifact that packages the three discovery tools already in the
tree into a single ranked report, keyed on the dump's pinned commit SHA:

* ``parse_gamedata.validate_anchors`` — the hard gate (Dart 200, Super 2500);
  if it fails the dump moved and the report aborts.
* ``parse_gamedata.audit`` — per-field fidelity verdict (CLEAN / DELTA /
  SUSPECT) for everything the mapper already extracts.
* ``btd6_gamedata_inventory`` — domain / model-type discovery + textTable
  linkage.

On top of those it adds the two columns the *effect* work needs that no
existing tool emits — **decodable-number?** (does the effect model carry a
stable effect-magnitude field) and **has-curated-name?** (is there a name to
attach the decoded effect to) — and ranks the ``*ZoneModel`` /
``*SupportModel`` / ``*BuffModel`` tail by occurrence so the "49-model-type
wall" becomes a worklist.

Usage (nothing is fetched at runtime; point ``--dump`` at a clone)::

    git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
    python3.10 scripts/btd6_decode_inventory_report.py --dump /tmp/btd6gd
    python3.10 scripts/btd6_decode_inventory_report.py --dump /tmp/btd6gd \
        > docs/btd6/btd6-decode-inventory-v55.md

The report is deterministic for a given dump SHA (no wall-clock in the output),
so re-running on the same clone reproduces the committed doc byte-for-byte; a
diff means the dump moved. Only the derived report is committed — never the raw
dump.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import btd6_gamedata_inventory as inv  # noqa: E402
import parse_gamedata as pg  # noqa: E402

# ---------------------------------------------------------------------------
# Curated per-domain ingest verdict. The dump-derived numbers (file counts,
# audit verdicts, the $type tail) are computed live below; this table carries
# the *judgement* layer — whether a domain is worth ingesting and why —
# reconciled against docs/btd6/btd6-gamedata-decode-status.md (the authoritative
# status doc) and the dictionary. Source + the decode-status doc win when a
# companion doc disagrees. The "extracted" field records whether
# parse_gamedata.py reads the domain into committed stats; "verdict" is one of
# ingest-now / ingest-later / cosmetic-skip.
# ---------------------------------------------------------------------------
_DOMAIN_META: dict[str, dict[str, str]] = {
    "Towers": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "core stats live here; numeric leaves audit CLEAN/DELTA. "
        "The zone/buff/subtower-tail effects are the open decode work (step 5).",
    },
    "Upgrades": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "per-tier cost/xp/name extracted; LocsKey->textTable "
        "descriptions now wired inline into stats (373/375) + grounding.",
    },
    "Bloons": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "children/immune_to/health/speed/fortified-health cut over "
        "to game data (--bloons, game_sourced_fields marker); bosses ingested "
        "from Bloons/<boss>/ via --bosses. rbe stays derived; prose wiki-curated.",
    },
    "Rounds": {
        "extracted": "no",
        "verdict": "ingest-later",
        "reason": "5181 RoundModels (all modes); structure counted, not mapped.",
    },
    "IncomeSets": {
        "extracted": "no",
        "verdict": "ingest-later",
        "reason": "7 IncomeSetModels for economy income; counted, not mapped.",
    },
    "Powers": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--powers builds powers.json (25 of 27; Rogue/seasonal "
        "excluded) with decoded effect factors + filled {0} placeholders.",
    },
    "Mods": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--modes overlays per-mode structured rules blocks "
        "(cash/lives/rounds/cost + restrictions) onto modes.json from "
        "Mods/<mode>.json mutatorMods; taxonomy/prose stay curated.",
    },
    "Achievements": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "achievement metadata; not gameplay stats.",
    },
    "Artifacts": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "Rogue Legends/Frontier artifacts+traits; real gameplay "
        "modifiers but spin-off-mode-only — out of main-game scope (pairs "
        "with rogueData.json; revisit only on a scope expansion).",
    },
    "BloonOverlays": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "bloon sprite overlays; cosmetic.",
    },
    "Bosses": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--bosses builds bosses.json from Bosses/ + Bloons/<boss>/ "
        "(the HP/stats carrier); the folder's own music/sprite files stay "
        "cosmetic.",
    },
    "Buffs": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "BuffIndicatorModel = UI icons, not effects; effects are "
        "inline in tower models. Dictionary marks skip.",
    },
    "GeraldoItems": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--geraldo builds geraldo_items.json (16 items: cash cost, "
        "unlock level, stock/replenish cadence + structured effect factors).",
    },
    "Knowledge": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--knowledge builds monkey_knowledge.json (134 entries, "
        "119 with structured effect factors decoded from mod.mutatorMods).",
    },
    "Maps": {
        "extracted": "yes",
        "verdict": "ingest-now",
        "reason": "--maps rebuilds maps.json from Maps/ folders (86 player "
        "maps, all difficulties, has_water; curated removables preserved).",
    },
    "Skins": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "cosmetic skins; audio/prefab swaps only.",
    },
    "TrophyStoreItems": {
        "extracted": "no",
        "verdict": "cosmetic-skip",
        "reason": "trophy-store cosmetics; not gameplay.",
    },
}

# Effect-magnitude fields: the *strength* of a zone/buff effect (what we want to
# decode). Distinguished from aura-geometry fields (range/lifespan/radius =
# where/how-long the zone applies, not how strong) so a model that only carries
# geometry reads as "geometry-only", not a decodable effect number.
_EFFECT_NUM = {
    "multiplier",
    "additive",
    "pierce",
    "damage",
    "modifier",
    "percentage",
    "slowMultiplier",
    "discount",
    "cash",
    "pushAmount",
    "amount",
    "bonus",
    "distance",
    "maxDamage",
}
_GEOMETRY_NUM = {
    "range",
    "lifespan",
    "radius",
    "duration",
    "rate",
    "tickRate",
    "cooldown",
    "speed",
}
# Dump keys that carry / resolve a display name for an effect node.
_NAME_KEYS = {"buffLocsName", "locsName", "LocsKey", "displayName", "name"}

# --- Step-5 decoder registry (CLASSIFICATION ONLY — writes no buff numbers) --
# How each decodable-number effect `$type` should be handled in the slice-2
# numeric write. This is scaffolding for that work; it does not extract or write
# anything. Classes:
#   SAFE_WRITE       - clear semantics + a committed buff-schema field exists
#                      (verified vs a committed example or an unambiguous field).
#   SCHEMA_FIRST     - real number, but NO field in the committed buff schema
#                      (extend schema + dataclasses + renderers + tests first).
#   DEFER            - ambiguous semantics; needs examples before any write.
#   DESCRIPTION_ONLY - name/flag only; the upgrade description already covers it.
# Everything not listed here is DESCRIPTION_ONLY by default.
_DECODE_CLASS: dict[str, str] = {
    # SAFE_WRITE — additive/multiplier maps cleanly onto _BUFF_FIELDS
    "PierceSupportModel": "SAFE_WRITE",  # pierce -> pierceAdditive
    "RateSupportModel": "SAFE_WRITE",  # multiplier -> rateMultiplier (x-cooldown)
    "PoplustSupportModel": "SAFE_WRITE",  # *PercentIncrease -> *Percentage (verified)
    # 2026-06-09 evidence pass — semantics pinned by committed values, mapped
    # in _BUFF_FIELD_MAP (see each entry's confirmation note there):
    "RangeSupportModel": "SAFE_WRITE",  # additive/multiplier -> rangeAdditive/%
    "StartOfRoundRateBuffModel": "SAFE_WRITE",  # decoded since PR #501 (was stale)
    "ProjectileRadiusSupportModel": "SAFE_WRITE",  # -> radiusMultiplier (Striker)
    "BananaCashIncreaseSupportModel": "SAFE_WRITE",  # -> incomePercentage (Benjamin)
    # SCHEMA_FIRST — real number, no committed buff-schema field yet
    "ProjectileSpeedSupportModel": "SCHEMA_FIRST",  # 0.25 fraction-vs-x unpinned
    "FreezeDurationSupportModel": "SCHEMA_FIRST",  # Silas; no confirming number
    "CentralMarketBuffModel": "SCHEMA_FIRST",  # economy (blocked: Farm has no tiers)
    "BananaCentralBuffModel": "SCHEMA_FIRST",  # economy (no committed number at all)
    "BonusCashZoneModel": "SCHEMA_FIRST",  # Temple zone: sacrifice-conditional
    # DEFER — ambiguous magnitude/semantics until examples prove them
    "BrickellFreezeMinesAbilityBuffModel": "DEFER",  # bare multiplier 0.25 ambiguous
    "BuffBlowbackZoneModel": "DEFER",  # knockback magnitude (hero not committed)
    "ActivateRangeSupportZoneModel": "DEFER",  # inside AbilityModel; value unconfirmed
}


def _dump_sha(dump: Path) -> str:
    """The pinned commit SHA of the dump clone (the report's cache key)."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(dump), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001 - best-effort; report still useful without it
        return "unknown"


def _short_type(node: Any) -> str:
    return inv._short_type(node)


def _scan_effect_tail(dump: Path) -> dict[str, list[tuple[str, int, set, set]]]:
    """Walk every tower model and tally the effect-model ``$type`` tail.

    Returns ``{"zone": rows, "buff": rows}`` where each row is
    ``(short_type, instance_count, numeric_fields, name_keys)`` sorted by count.
    Buffs and supports share a bucket (both are ``buffs[]`` in our schema).
    """
    zone: Counter = Counter()
    buff: Counter = Counter()
    znum: dict[str, set] = {}
    bnum: dict[str, set] = {}
    zname: dict[str, set] = {}
    bname: dict[str, set] = {}

    def record(t: str, counter: Counter, nums: dict, names: dict, node: dict) -> None:
        counter[t] += 1
        nums.setdefault(t, set()).update(
            k
            for k, v in node.items()
            if not k.startswith("$")
            and isinstance(v, (int, float))
            and not isinstance(v, bool)
        )
        names.setdefault(t, set()).update(
            k for k in _NAME_KEYS if node.get(k) not in (None, "", 0)
        )

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            t = _short_type(node)
            if t.endswith("ZoneModel"):
                record(t, zone, znum, zname, node)
            elif t.endswith("SupportModel") or t.endswith("BuffModel"):
                record(t, buff, bnum, bname, node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for fp in sorted((dump / "Towers").rglob("*.json")):
        try:
            walk(json.loads(fp.read_text("utf-8")))
        except (OSError, json.JSONDecodeError):
            continue

    def rows(
        counter: Counter,
        nums: dict,
        names: dict,
    ) -> list[tuple[str, int, set, set]]:
        return [
            (t, n, nums.get(t, set()), names.get(t, set()))
            for t, n in counter.most_common()
        ]

    return {"zone": rows(zone, znum, zname), "buff": rows(buff, bnum, bname)}


def _decodable(numeric: set) -> str:
    if numeric & _EFFECT_NUM:
        return "yes (" + ", ".join(sorted(numeric & _EFFECT_NUM)) + ")"
    if numeric & _GEOMETRY_NUM:
        return "geometry-only"
    return "no (name/flag only)"


def _has_name(name_keys: set) -> str:
    direct = name_keys & {"buffLocsName", "locsName", "displayName"}
    if direct:
        return "yes (" + ", ".join(sorted(direct)) + ")"
    if "name" in name_keys:
        return "yes (model name)"
    # No name on the node itself → resolve via the owning upgrade's LocsKey,
    # which every tower effect has (the documented join key).
    return "via owning upgrade"


def _md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


# Static header preamble, as a module constant so tests can pin it against
# the committed artifact (docs/btd6/btd6-decode-inventory-v55.md). It MUST
# carry the Status badge: scripts/check_docs.py --strict requires one on
# every docs/**/*.md, so a regenerated report without it reddens the
# doc-hygiene gate on the PR that commits it (found 2026-06-09 building the
# btd6-data-refresh workflow — the badge had been hand-added to the artifact
# only, silently breaking byte-for-byte regeneration).
_HEADER_LINES = [
    "# BTD6 v55 decode inventory / audit report",
    "",
    "> **Status:** `reference` — BTD6 v55 decode-inventory reference.",
    "",
    "> **Generated by** `scripts/btd6_decode_inventory_report.py` — ",
    "> re-run it on the same dump clone to reproduce this file. A diff",
    "> means the dump moved; re-validate before trusting old verdicts.",
    "",
]


def build_report(dump: Path) -> str:
    sha = _dump_sha(dump)
    version = pg._dump_version(dump) or "unknown"
    lines: list[str] = list(_HEADER_LINES)
    lines.append(f"- **Dump SHA (pin):** `{sha}`")
    lines.append(f"- **Game version:** {version}")
    lines.append(
        "- **Anchor gate:** Dart Monkey 200, Super Monkey 2500 — **PASS** "
        "(checked first; report aborts on failure).",
    )
    lines.append("")

    # --- 1. Domain coverage ------------------------------------------------
    lines.append("## 1. Domain coverage (present? / extracted? / verdict)")
    lines.append("")
    rows: list[list[str]] = []
    for domain in inv.list_domains(dump):
        files, counter = inv.domain_summary(dump, domain)
        meta = _DOMAIN_META.get(
            domain,
            {"extracted": "no", "verdict": "ingest-later", "reason": "not classified."},
        )
        rows.append(
            [
                f"`{domain}/`",
                str(files),
                meta["extracted"],
                meta["verdict"],
                meta["reason"],
            ],
        )
    lines += _md_table(["Domain", "Files", "Extracted?", "Verdict", "Reason"], rows)
    lines.append("")
    lines.append(inv.text_link_report(dump)[0])
    lines.append("")
    for ln in inv.text_link_report(dump)[1:]:
        lines.append(f"- {ln.strip()}")
    lines.append("")

    # --- 2. Extracted-field fidelity --------------------------------------
    lines.append("## 2. Extracted-field fidelity (`--audit`)")
    lines.append("")
    lines.append(
        "Per-field verdict for everything the mapper already extracts. "
        "`SUSPECT` (>20% divergence) = never overlay; `DELTA` = sparse, "
        "likely a genuine v55 change; `CLEAN` = matches committed data.",
    )
    lines.append("")
    stats = pg.audit(dump)
    order = {"SUSPECT": 0, "DELTA": 1, "CLEAN": 2}
    audit_rows = sorted(
        stats.items(),
        key=lambda kv: (order[kv[1].verdict], -kv[1].diffs),
    )
    counts = Counter(st.verdict for _, st in audit_rows)
    lines.append(
        f"**Totals:** {counts.get('CLEAN', 0)} CLEAN · {counts.get('DELTA', 0)} "
        f"DELTA · {counts.get('SUSPECT', 0)} SUSPECT "
        f"(across {len(audit_rows)} numeric/bool fields).",
    )
    lines.append("")
    table_rows = [
        [f"`{name}`", st.verdict, str(st.diffs), str(st.total), f"{st.rate:.0%}"]
        for name, st in audit_rows
    ]
    lines += _md_table(["Field", "Verdict", "Diffs", "Total", "Rate"], table_rows)
    lines.append("")
    lines.append(
        "> Most DELTAs sit on positionally-indexed `projectiles[1/2/3]` "
        "leaves — phantom diffs from index alignment, not real changes "
        "(named projectiles align cleanly). Numeric overlay (step 3/4) "
        "must align nested lists by name, never index.",
    )
    lines.append("")

    # --- 3. Effect-decode tail --------------------------------------------
    tail = _scan_effect_tail(dump)
    lines.append("## 3. Effect-decode tail — zones & buffs (step 5 worklist)")
    lines.append("")
    lines.append(
        "The 'stat-based effect' half of the goal. These `$type`s are "
        "**inline behaviors in the tower models** (the dump has no "
        "`zones[]`/`buffs[]` arrays — those are our *output* schema). "
        "Ranked by occurrence: decode the headline effect number where one "
        "exists, else fall back to the textTable description (flagged).",
    )
    lines.append("")
    lines.append(
        "**Decode-class** (slice-2 registry, classification only — no numbers "
        "written): `SAFE_WRITE` = clear semantics + a committed buff-schema field; "
        "`SCHEMA_FIRST` = real number but the schema has no field yet (extend "
        "first); `DEFER` = ambiguous semantics; `DESCRIPTION_ONLY` = name/flag "
        "only (already covered by the upgrade description).",
    )
    lines.append("")
    zone_rows = tail["zone"]
    buff_rows = tail["buff"]
    lines.append(f"### 3a. Zone effect models — {len(zone_rows)} distinct `$type`s")
    lines.append("")
    lines.append(
        "> **Doc reconciliation:** `btd6-gamedata-decode-status.md` records "
        f'"0 of 12 zone" — v55 actually has **{len(zone_rows)}** distinct '
        "`*ZoneModel` `$type`s. The doc's 12 is an undercount; this report "
        "is the live ground truth.",
    )
    lines.append("")
    z_rows = [
        [
            f"`{t}`",
            str(n),
            _decodable(nums),
            _has_name(names),
            _DECODE_CLASS.get(t, "DESCRIPTION_ONLY"),
        ]
        for t, n, nums, names in zone_rows
    ]
    lines += _md_table(
        [
            "Zone `$type`",
            "Count",
            "Decodable-number?",
            "Has-curated-name?",
            "Decode-class",
        ],
        z_rows,
    )
    lines.append("")
    lines.append(
        f"### 3b. Buff / support effect models — {len(buff_rows)} distinct `$type`s",
    )
    lines.append("")
    lines.append(
        '> **Doc reconciliation:** decode-status records "0 of 37 buff" — '
        f"v55 has **{len(buff_rows)}** distinct `*SupportModel`/`*BuffModel` "
        "`$type`s (the doc's 37 is close).",
    )
    lines.append("")
    b_rows = [
        [
            f"`{t}`",
            str(n),
            _decodable(nums),
            _has_name(names),
            _DECODE_CLASS.get(t, "DESCRIPTION_ONLY"),
        ]
        for t, n, nums, names in buff_rows
    ]
    lines += _md_table(
        [
            "Buff/Support `$type`",
            "Count",
            "Decodable-number?",
            "Has-curated-name?",
            "Decode-class",
        ],
        b_rows,
    )
    lines.append("")
    n_zone_num = sum(1 for _, _, nums, _ in zone_rows if nums & _EFFECT_NUM)
    n_buff_num = sum(1 for _, _, nums, _ in buff_rows if nums & _EFFECT_NUM)
    lines.append(
        f"**Ranking summary:** {n_zone_num}/{len(zone_rows)} zone and "
        f"{n_buff_num}/{len(buff_rows)} buff `$type`s carry a decodable effect "
        "number; the remainder are name/flag-only and fall back to the textTable "
        "description (partial-but-honest — show the words, never a guessed number).",
    )
    lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump", required=True, type=Path, help="game-data clone path")
    args = ap.parse_args(argv)

    dump: Path = args.dump
    if not dump.is_dir():
        raise SystemExit(f"--dump {dump} is not a directory")

    errors = pg.validate_anchors(dump)
    if errors:
        raise SystemExit(
            "ANCHOR GATE FAILED — the dump moved; re-check before mapping:\n  "
            + "\n  ".join(errors),
        )

    sys.stdout.write(build_report(dump))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
