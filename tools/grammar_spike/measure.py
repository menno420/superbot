"""Grammar-fit measurement — every real surface unit, classified and counted.

Methodology (the honest part):

* A **unit** is one real, user-observable or contract-bearing surface of the
  subsystem as shipped TODAY — a command, a panel component, a setting, a
  binding, a resource, an event, a listener, a store, a session lifecycle, a
  renderer. Units were enumerated from source (citations in the manifest
  module docstrings), not from the manifest — so the grammar is scored
  against reality, not against what it found convenient to declare.
* Each unit gets TWO classifications:
  - ``tier_spec``      — under the design spec §2 grammar AS WRITTEN;
  - ``tier_proposed``  — with this spike's proposed tier-2 families
    (G-1 GatewayListenerSpec, G-2 list-valued settings + add/remove
    workflows, G-3 AnnouncementRouteSpec, G-4 command cooldowns,
    G-5 declarative validator bounds).
* Tier semantics are §2.9's: 1 = generated/kernel workflow (zero domain
  code) · 2 = declared-parameterized spec family (data, not code) · 3 =
  escape-hatch code (registered handler/renderer with real logic).
* The measurement is a JUDGMENT LEDGER by design — every row carries its
  rationale so a reviewer can dispute any single call. Run
  ``python3.10 -m tools.grammar_spike.measure`` to regenerate RESULTS.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

__all__ = ["UNITS", "Unit", "compute", "main"]


@dataclass(frozen=True)
class Unit:
    subsystem: str
    unit: str
    kind: str
    tier_spec: int
    tier_proposed: int
    rationale: str


UNITS: tuple[Unit, ...] = (
    # ================================================================ karma
    Unit(
        "karma",
        "!thanks (+rep/thank)",
        "command",
        3,
        3,
        "thin domain handler: the audited grant seam; typed errors render "
        "through the §2.7 Result grammar (the cog's try/except dies)",
    ),
    Unit(
        "karma",
        "!karma (card)",
        "command",
        2,
        2,
        "PanelRef route + FieldsBlock over a simple read provider",
    ),
    Unit(
        "karma",
        "!karma add",
        "command",
        3,
        3,
        "same seam as !thanks — declared alias surface",
    ),
    Unit(
        "karma",
        "/karma",
        "command",
        2,
        2,
        "same panel, slash kind — pure declaration",
    ),
    Unit(
        "karma",
        "karma card embed",
        "panel",
        2,
        2,
        "fields provider (record → fields) — no bespoke view class survives",
    ),
    Unit(
        "karma",
        "enabled setting",
        "setting",
        1,
        1,
        "kernel settings workflow + generated panel",
    ),
    Unit(
        "karma",
        "cooldown_seconds setting",
        "setting",
        2,
        1,
        "bounded-int validator is a registered ref as-specced; G-5 makes "
        "bounds declarative data",
    ),
    Unit(
        "karma",
        "daily_cap setting",
        "setting",
        2,
        1,
        "same G-5 class",
    ),
    Unit(
        "karma",
        "reaction_emoji setting",
        "setting",
        1,
        1,
        "plain str setting",
    ),
    Unit(
        "karma",
        "react-to-thank listener",
        "listener",
        3,
        2,
        "NO gateway-listener primitive in §2 (G-1); with it: declared gate + "
        "thin fetch-and-forward handler",
    ),
    Unit(
        "karma",
        "karma.granted event",
        "event",
        1,
        1,
        "EventSpec declaration; emit lives inside the audited seam",
    ),
    Unit(
        "karma",
        "karma table (INV-K)",
        "store",
        1,
        1,
        "StoreSpec → generated sole-writer fence",
    ),
    Unit(
        "karma",
        "karma_audit_log table",
        "store",
        1,
        1,
        "ledger-class StoreSpec",
    ),
    Unit(
        "karma",
        "karma rank / leaderboard read",
        "game",
        2,
        2,
        "LeaderboardSpec over karma.points (decision 10 vocabulary)",
    ),
    Unit(
        "karma",
        "help entry",
        "help",
        1,
        1,
        "help-as-projection",
    ),
    # ============================================================== logging
    Unit(
        "logging",
        "!logging (panel open)",
        "command",
        1,
        1,
        "command → panel route: kernel open-panel workflow",
    ),
    Unit(
        "logging",
        "!logging status",
        "command",
        1,
        1,
        "re-render of the same read-model panel",
    ),
    Unit(
        "logging",
        "!logging set",
        "command",
        1,
        1,
        "the kernel binding-set workflow (channel picker widget)",
    ),
    Unit(
        "logging",
        "!logging create",
        "command",
        1,
        1,
        "the provisioning lane: preview + confirm, never silent",
    ),
    Unit(
        "logging",
        "!logging routes",
        "command",
        2,
        2,
        "routes read-model provider behind a TableBlock",
    ),
    Unit(
        "logging",
        "!logging test",
        "command",
        3,
        3,
        "deliberately exercises the live posting path — real code, thin",
    ),
    Unit(
        "logging",
        "panel: refresh status",
        "panel-action",
        1,
        1,
        "re-render workflow",
    ),
    Unit(
        "logging",
        "panel: set mod channel",
        "panel-action",
        1,
        1,
        "binding-set workflow (custom_id verbatim logging_panel.set_mod)",
    ),
    Unit(
        "logging",
        "panel: set cleanup channel",
        "panel-action",
        1,
        1,
        "binding-set workflow",
    ),
    Unit(
        "logging",
        "panel: create mod channel",
        "panel-action",
        1,
        1,
        "provisioning workflow",
    ),
    Unit(
        "logging",
        "panel: create cleanup channel",
        "panel-action",
        1,
        1,
        "provisioning workflow",
    ),
    Unit(
        "logging",
        "panel: test",
        "panel-action",
        3,
        3,
        "same live-path exercise as !logging test",
    ),
    Unit(
        "logging",
        "panel: routes",
        "panel-action",
        1,
        1,
        "open-panel navigation",
    ),
    Unit(
        "logging",
        "panel: overview",
        "panel-action",
        1,
        1,
        "open-panel navigation",
    ),
    Unit(
        "logging",
        "master enabled toggle",
        "setting",
        1,
        1,
        "bool setting; activation=on_when_bound is the §4.4 showcase",
    ),
    Unit(
        "logging",
        "auto_create_channels",
        "setting",
        1,
        1,
        "bool setting, off_until_opt_in",
    ),
    Unit(
        "logging",
        "7 per-category toggles",
        "setting×7",
        1,
        1,
        "identical bool declarations (counted as 7 units in totals)",
    ),
    Unit(
        "logging",
        "event_routing enum",
        "setting",
        1,
        1,
        "allowed_values enum setting",
    ),
    Unit(
        "logging",
        "ignored_channels list",
        "setting",
        3,
        1,
        "G-2: §2.5 has no list-valued setting shape; with list[type] + "
        "kernel add/remove workflows it is pure declaration",
    ),
    Unit(
        "logging",
        "ignored_users list",
        "setting",
        3,
        1,
        "same G-2 class",
    ),
    Unit(
        "logging",
        "11 channel bindings",
        "binding×11",
        1,
        1,
        "BindingSpec declarations + legacy KV aliases (decision 3)",
    ),
    Unit(
        "logging",
        "11 channel resources",
        "resource×11",
        1,
        1,
        "ResourceRequirement declarations, offer_on_enable",
    ),
    Unit(
        "logging",
        "3 bus subscriptions",
        "subscription×3",
        1,
        1,
        "EventSubscription declarations — the import-invisible wiring made "
        "visible (§1.6); handler classification is the next row",
    ),
    Unit(
        "logging",
        "log-embed rendering handlers",
        "handler",
        3,
        2,
        "as-specced: bespoke embed-format code per event class; G-3 "
        "AnnouncementRouteSpec (event → template → bound destination) makes "
        "the recurring shape data — welcome/counters/spotlight share it",
    ),
    Unit(
        "logging",
        "8 gateway listeners",
        "listener×8",
        3,
        2,
        "G-1: no primitive as-specced (the operator band's biggest gap); "
        "with GatewayListenerSpec: declared gate + payload-extract handlers",
    ),
    Unit(
        "logging",
        "status/routes providers",
        "provider",
        2,
        2,
        "read-model providers behind refs",
    ),
    Unit(
        "logging",
        "help entry",
        "help",
        1,
        1,
        "projection",
    ),
    # ============================================================ blackjack
    Unit(
        "blackjack",
        "!blackjack (+bj)",
        "command",
        3,
        3,
        "session-start handler: bet parse + engine deal (lifecycle is "
        "spec-owned after that)",
    ),
    Unit(
        "blackjack",
        "!bjtournament (+bjtourn)",
        "command",
        3,
        3,
        "lobby orchestration handler",
    ),
    Unit(
        "blackjack",
        "!bjstart",
        "command",
        3,
        3,
        "lobby op",
    ),
    Unit(
        "blackjack",
        "!bjstatus",
        "command",
        2,
        2,
        "status read over session state — provider-shaped",
    ),
    Unit(
        "blackjack",
        "board renderer",
        "renderer",
        3,
        3,
        "renderer_override — §2.9's NAMED escape-hatch class, by design",
    ),
    Unit(
        "blackjack",
        "hit action",
        "panel-action",
        3,
        3,
        "game move handler (declared surface: auth/audit/namespace)",
    ),
    Unit(
        "blackjack",
        "stand action",
        "panel-action",
        3,
        3,
        "game move handler",
    ),
    Unit(
        "blackjack",
        "double action",
        "panel-action",
        3,
        3,
        "game move + second escrow leg",
    ),
    Unit(
        "blackjack",
        "result renderer + replay",
        "renderer",
        3,
        3,
        "outcome card; replay static id declared verbatim",
    ),
    Unit(
        "blackjack",
        "default_entry_fee setting",
        "setting",
        1,
        1,
        "int setting",
    ),
    Unit(
        "blackjack",
        "reaction-join listener",
        "listener",
        3,
        3,
        "G-1 declares the wiring, but the join handler is real lobby logic "
        "— stays tier 3 honestly (contrast logging's extract-and-route)",
    ),
    Unit(
        "blackjack",
        "solo session lifecycle",
        "session",
        2,
        2,
        "ChallengeSessionSpec: escrow/settle-once/timeouts/recovery/rematch "
        "choreography leaves the domain — the facet's biggest win",
    ),
    Unit(
        "blackjack",
        "pvp session lifecycle",
        "session",
        2,
        2,
        "same spec family (accept phase + two-sided escrow)",
    ),
    Unit(
        "blackjack",
        "tournament session lifecycle",
        "session",
        2,
        2,
        "same family; entry fee from setting",
    ),
    Unit(
        "blackjack",
        "game engine (rules)",
        "engine",
        3,
        3,
        "pure-function escape hatch BY DESIGN — the grammar must never "
        "express game rules (§10.1 risk 5)",
    ),
    Unit(
        "blackjack",
        "wins leaderboard",
        "game",
        2,
        2,
        "LeaderboardSpec + declared stat_writes (decision 10)",
    ),
    Unit(
        "blackjack",
        "game_state checkpoints",
        "store",
        2,
        2,
        "persistence=checkpointed on the session spec (019 rule)",
    ),
    Unit(
        "blackjack",
        "help entry",
        "help",
        1,
        1,
        "projection",
    ),
)


#: units whose kind carries a ×N multiplier count as N in totals
def _weight(unit: Unit) -> int:
    if "×" in unit.kind:
        return int(unit.kind.split("×")[1])
    return 1


def compute() -> dict[str, dict[str, float]]:
    """Per-subsystem and overall tier-1/2 fractions, both classifications."""
    out: dict[str, dict[str, float]] = {}
    subsystems = sorted({u.subsystem for u in UNITS})
    for scope in [*subsystems, "OVERALL"]:
        rows = [u for u in UNITS if scope == "OVERALL" or u.subsystem == scope]
        total = sum(_weight(u) for u in rows)
        spec_12 = sum(_weight(u) for u in rows if u.tier_spec <= 2)
        prop_12 = sum(_weight(u) for u in rows if u.tier_proposed <= 2)
        out[scope] = {
            "units": total,
            "spec_fit": spec_12 / total,
            "proposed_fit": prop_12 / total,
        }
    return out


def main() -> None:
    from tools.grammar_spike.manifests import ALL_MANIFESTS
    from tools.grammar_spike.spec import ALL_SPEC_TYPES, untagged_fields

    # sanity: manifests construct (validators ran) + full S/A/O tagging
    if len(ALL_MANIFESTS) != 3:
        raise RuntimeError("expected exactly the three spike manifests")
    for spec_type in ALL_SPEC_TYPES:
        missing = untagged_fields(spec_type)
        if missing:
            raise RuntimeError(f"{spec_type.__name__} untagged fields: {missing}")

    stats = compute()
    lines = [
        "# Grammar-expressiveness spike — RESULTS",
        "",
        "> GENERATED by `python3.10 -m tools.grammar_spike.measure` — edit the",
        "> unit ledger in `measure.py`, not this file. Methodology + tier",
        "> semantics in the module docstring; per-unit rationale below.",
        "",
        "## Tier-1/2 fit (the ~80% hypothesis, design spec §10.1 risk 5)",
        "",
        "| Scope | Surface units | Fit — spec as written | Fit — with proposed families |",
        "|---|---|---|---|",
    ]
    for scope, row in stats.items():
        lines.append(
            f"| {scope} | {row['units']:.0f} | **{row['spec_fit']:.0%}** "
            f"| **{row['proposed_fit']:.0%}** |",
        )
    lines += [
        "",
        "Proposed tier-2 families (detail in the go/no-go doc §2): "
        "**G-1** GatewayListenerSpec · **G-2** list-valued settings + "
        "add/remove workflows · **G-3** AnnouncementRouteSpec · **G-4** "
        "CommandSpec.cooldown · **G-5** declarative validator bounds — "
        "plus **G-6**, a §3.1 namespace correction (command pools are "
        "per-kind: prefix and slash namespaces are disjoint).",
        "",
        "## The unit ledger",
        "",
        "| Subsystem | Unit | Kind | Tier (spec) | Tier (proposed) | Rationale |",
        "|---|---|---|---|---|---|",
    ]
    for u in UNITS:
        lines.append(
            f"| {u.subsystem} | {u.unit} | {u.kind} | {u.tier_spec} "
            f"| {u.tier_proposed} | {u.rationale} |",
        )
    lines.append("")
    out_path = Path(__file__).parent / "RESULTS.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"wrote {out_path}")
    for scope, row in stats.items():
        print(
            f"{scope:12s} units={row['units']:3.0f} "
            f"spec={row['spec_fit']:.0%} proposed={row['proposed_fit']:.0%}",
        )


if __name__ == "__main__":
    main()
