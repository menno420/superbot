#!/usr/bin/env python3
"""
Setup-wizard completion simulator.

Models a NON-TECHNICAL server owner walking the setup wizard, to compare the
CURRENT structure against the PROPOSED restructure on the things the owner
actually cares about:

  * does every step complete a real action (no metadata-only / link-only / read-only steps)?
  * how much Discord/bot jargon does the operator hit?
  * does any step dead-end on a resource the operator must create first?
  * how many screens / clicks to finish, and what fraction of operators finish?

It is a DETERMINISTIC expected-value model (no RNG) so results are reproducible
and the comparison is auditable. The drop-off model is intentionally simple and
its knobs are stated up top -- the point is the RELATIVE gap between the two
structures, not a precise abandonment forecast.

Drop-off model (per step, probability the operator continues to the next step):

    continue = BASE
               - DEAD_PENALTY        if the step completes no real configuration
               - JARGON_STEP * hits  (capped) for jargon terms the operator sees
               - BLOCK_PENALTY       if the step needs a role/channel the operator
                                     must create elsewhere first (a hard wall)
               - FATIGUE * index     small per-step fatigue

    completion_rate = product(continue for each step in the main flow)

Run:  python3.10 tools/sim/setup_wizard_sim.py
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- model knobs (stated so the verdict is auditable) ----------------------
BASE = 0.985  # a motivated owner mostly continues
DEAD_PENALTY = 0.10  # a step that configures nothing erodes trust ("why am I here?")
JARGON_STEP = 0.03  # per distinct jargon term the operator reads on the step
JARGON_CAP = 0.12  # max jargon penalty on any one step
BLOCK_PENALTY = 0.15  # step dead-ends on a resource the operator must make first
FATIGUE = 0.004  # per-step fatigue (a long wizard tires people)

# Jargon vocabulary a non-technical owner does NOT understand. Counted per step.
JARGON_TERMS = [
    "draft",
    "operation",
    "stages",
    "bind",
    "binding",
    "final review",
    "cog",
    "subsystem",
    "scope",
    "resolver",
    "precedence",
    "threshold",
    "seam",
    "pipeline",
    "routing",
    "tier",
    "guild",
    "preset",
    "set_setting",
    "set_role_threshold",
    "set_cleanup_policy",
    "set_cog_routing",
    "bind_channel",
]


@dataclass
class Step:
    name: str  # operator-facing label
    completes_action: bool  # does finishing this step actually change config?
    copy: str  # the operator-facing blurb (scored for jargon)
    clicks: int  # interactions to complete
    blocks_on_resource: bool = False  # needs a role/channel made elsewhere first
    in_main_flow: bool = (
        True  # part of the completion path (vs. an optional side panel)
    )

    def jargon_hits(self) -> int:
        text = f"{self.name} {self.copy}".lower()
        return sum(1 for term in JARGON_TERMS if term in text)


@dataclass
class Wizard:
    title: str
    steps: list[Step] = field(default_factory=list)

    def main_flow(self) -> list[Step]:
        return [s for s in self.steps if s.in_main_flow]

    def completion_rate(self) -> float:
        rate = 1.0
        for idx, step in enumerate(self.main_flow()):
            cont = BASE
            if not step.completes_action:
                cont -= DEAD_PENALTY
            cont -= min(JARGON_CAP, JARGON_STEP * step.jargon_hits())
            if step.blocks_on_resource:
                cont -= BLOCK_PENALTY
            cont -= FATIGUE * idx
            rate *= max(0.0, cont)
        return rate

    def report(self) -> dict[str, float]:
        flow = self.main_flow()
        return {
            "screens": len(flow),
            "dead_steps": sum(1 for s in flow if not s.completes_action),
            "blocked_steps": sum(1 for s in flow if s.blocks_on_resource),
            "jargon_hits": sum(s.jargon_hits() for s in flow),
            "clicks": sum(s.clicks for s in flow),
            "completion_rate": self.completion_rate(),
        }


# --- CURRENT wizard, STANDARD depth (the most common path) -----------------
# Copy is paraphrased from the live section embeds (see the research in the plan).
CURRENT = Wizard(
    "CURRENT (standard depth)",
    [
        Step(
            "Server purpose",
            False,
            "Pick what this server is for. Metadata only; nothing is configured.",
            2,
        ),
        Step(
            "Scan server",
            False,
            "Read-only scan of channels, roles and bot permissions.",
            1,
        ),
        Step(
            "Run readiness scan",
            False,
            "Read-only diagnostic; posts a health embed, makes no changes.",
            1,
        ),
        Step(
            "Identity & defaults",
            True,
            "Stage a set_setting operation for the warn threshold default.",
            3,
        ),
        Step(
            "Load preset",
            True,
            "Pick an automation preset; stages every preset operation into the draft.",
            2,
        ),
        Step(
            "Channels & log routing",
            True,
            "Each pick stages a bind_channel operation in the draft; nothing applies until Final review.",
            4,
            blocks_on_resource=True,
        ),
        Step(
            "Auto roles (time & XP)",
            True,
            "Configure thresholds for existing roles. Create roles first in Discord. Stages a set_role_threshold operation.",
            4,
            blocks_on_resource=True,
        ),
        Step(
            "Cleanup inheritance",
            True,
            "Configure cleanup at three scopes. The resolver walks thread to channel to category to guild to default.",
            4,
        ),
        Step(
            "Moderation",
            True,
            "Each pick stages a set_setting operation; Final review applies them through the audited settings pipeline.",
            4,
        ),
        Step(
            "Logging presets",
            True,
            "Pick a logging preset; stages channel-creation operations into the draft.",
            3,
        ),
        Step(
            "Role templates",
            True,
            "Pick a role template; stages create_managed_role operations for missing roles.",
            3,
        ),
        Step(
            "Cog routing",
            True,
            "Enable or disable cogs per scope. The resolver walks channel to category to guild to default-true.",
            4,
        ),
        Step(
            "Diagnose & repair",
            False,
            "Read setup diagnostics; surfaces blockers, warnings and advisories.",
            2,
        ),
        Step(
            "Support Tickets",
            True,
            "Pick a staff role and a transcript channel; applies directly.",
            3,
        ),
        Step(
            "BTD6 Assistant",
            False,
            "Announcement only; shows BTD6 data versions. No per-guild settings yet.",
            1,
        ),
        Step(
            "AI policy",
            False,
            "Link-only step. Opens /aimenu; emits zero draft operations.",
            2,
        ),
        Step(
            "Final review",
            True,
            "Apply every staged operation in the draft through the canonical pipelines.",
            2,
        ),
    ],
)

# --- PROPOSED wizard -------------------------------------------------------
# Plain language; every main-flow step completes a real action immediately
# (direct lane); auto-creates any channel/role it needs; read-only checks moved
# OUT of the completion path into an optional "Check my setup" side panel.
PROPOSED = Wizard(
    "PROPOSED (essentials, direct-apply)",
    [
        Step(
            "What kind of server is this?",
            True,
            "Pick one. We switch on a sensible starter set for you right away.",
            1,
        ),
        Step(
            "Greet new members",
            True,
            "Turn on a welcome message and pick a channel (we can make one for you). Optionally give newcomers a role.",
            3,
        ),
        Step(
            "Who are your moderators?",
            True,
            "Choose the role for people who can warn and remove others. We set safe defaults for the rest.",
            2,
        ),
        Step(
            "Block spam and bad links",
            True,
            "Turn on automatic clean-up of spam, scam links and shouting. Sensible limits are pre-filled.",
            2,
        ),
        Step(
            "Where should activity appear?",
            True,
            "Pick a channel for logs, or let us create a tidy pair for you.",
            2,
        ),
        Step(
            "Reward active members",
            True,
            "Turn on levels, and optionally hand out a role automatically as people stay and chat. We create the roles.",
            3,
        ),
        Step(
            "Set up a help desk",
            True,
            "Let members open a private support request. Pick who answers; we make the rest.",
            3,
        ),
        Step(
            "All done",
            True,
            "Here is everything you switched on. Add more anytime from the extras menu.",
            1,
        ),
        # Optional extras + health check live OUTSIDE the completion path:
        Step(
            "Extras menu",
            True,
            "Hall of Fame, live member counts, raid protection, AI helper, replace another bot.",
            1,
            in_main_flow=False,
        ),
        Step(
            "Check my setup",
            True,
            "Optional health check; tells you anything still worth turning on.",
            1,
            in_main_flow=False,
        ),
    ],
)


def fmt(label: str, rep: dict[str, float]) -> str:
    return (
        f"  {label:38s} screens={rep['screens']:>2.0f}  "
        f"dead={rep['dead_steps']:>2.0f}  blocked={rep['blocked_steps']:>2.0f}  "
        f"jargon={rep['jargon_hits']:>3.0f}  clicks={rep['clicks']:>3.0f}  "
        f"finish={rep['completion_rate'] * 100:5.1f}%"
    )


def main() -> None:
    cur = CURRENT.report()
    new = PROPOSED.report()

    print("=" * 78)
    print("Setup-wizard completion simulation (non-technical owner persona)")
    print("=" * 78)
    print(fmt(CURRENT.title, cur))
    print(fmt(PROPOSED.title, new))
    print("-" * 78)
    print("  Deltas (proposed vs current):")
    print(
        f"    screens   : {new['screens'] - cur['screens']:+.0f}  (shorter is better)",
    )
    print(
        f"    dead steps: {new['dead_steps'] - cur['dead_steps']:+.0f}  (steps that configure nothing)",
    )
    print(
        f"    blocked   : {new['blocked_steps'] - cur['blocked_steps']:+.0f}  (dead-end-on-missing-resource)",
    )
    print(
        f"    jargon    : {new['jargon_hits'] - cur['jargon_hits']:+.0f}  (terms a non-tech owner won't know)",
    )
    print(f"    clicks    : {new['clicks'] - cur['clicks']:+.0f}")
    print(
        f"    finish    : {(new['completion_rate'] - cur['completion_rate']) * 100:+.1f} pts",
    )
    print("=" * 78)

    # Per-step jargon hot-spots in the current flow (where to focus the rewrite).
    print("Current-flow jargon hot-spots (terms seen per step):")
    for s in sorted(CURRENT.main_flow(), key=lambda x: -x.jargon_hits())[:6]:
        hits = [t for t in JARGON_TERMS if t in f"{s.name} {s.copy}".lower()]
        print(f"  {s.name:28s} {s.jargon_hits()} -> {', '.join(hits)}")
    print("=" * 78)

    verdict = (
        "PASS"
        if (
            new["dead_steps"] == 0
            and new["blocked_steps"] == 0
            and new["jargon_hits"] < cur["jargon_hits"] / 3
            and new["completion_rate"] > cur["completion_rate"]
        )
        else "REVIEW"
    )
    print(f"VERDICT: proposed structure is {verdict} on the owner's four goals")
    print("  (zero dead steps, zero dead-ends, jargon cut >3x, higher finish rate)")


if __name__ == "__main__":
    main()
