"""Mechanical breadth sweep — one golden per enumerable command.

The denominator comes from the live bot object (``bot.walk_commands()`` /
``bot.tree.walk_commands()``), so the sweep can never quietly diverge from
the real registered surface. For each command we synthesize a plausible
invocation from its signature; commands whose parameters we cannot
synthesize are reported as an explicit uncovered class, never silently
skipped.
"""

from __future__ import annotations

import typing
from typing import Any

import discord
from discord.ext import commands as dpy_commands
from parity.harness.cases import GoldenCase, Step

__all__ = [
    "build_sweep_cases",
    "EXCLUDED_COMMANDS",
    "FLAKY_ADVISORY",
    "SLASH_EXCLUDED_COMMANDS",
    "SweepSkipError",
]

#: process-lifecycle / destructive-to-the-harness commands, with reasons —
#: these appear in the coverage report as excluded-with-reason, not covered.
EXCLUDED_COMMANDS: dict[str, str] = {
    "restart": "process lifecycle — sets a shutdown intent that drains the harness",
    "shutdown": "process lifecycle",
    "die": "process lifecycle",
    "reboot": "process lifecycle",
    "syncslash": "pushes the slash tree — deploy-ops, not guild behavior",
    "seed-data": (
        "bulk data seed — the golden would embed the whole versioned BTD6 "
        "dataset (6.8MB) already pinned by btd6_data_blobs.sha256 provenance "
        "(compat item 9); zero oracle value over the data files themselves"
    ),
    "unloadall": (
        "extension management — unloads every cog IN-PROCESS, so every "
        "later case in the run captures 'command not found' garbage "
        "(observed); deploy-ops, not guild behavior"
    ),
    "loadall": "extension management — same class as unloadall",
    # --- host/process-state diagnostics: their OUTPUT is the machine ------
    # (CPU %, disk GB, uptime, live latency, random snapshot ids). A
    # rebuilt bot on other hardware can never byte-match these; their
    # parity story is the diagnostics REGISTRY, not output bytes. Keys are
    # exact QUALIFIED names — generic short names would over-exclude
    # (e.g. a bare "status" would swallow `!logging status`).
    "system_info": "host-state diagnostics — reports real disk/CPU/host state",
    "diagnostic_bot_status": "process-state diagnostics — live CPU %/uptime",
    "platform health": "process-state diagnostics — random snapshot ids + live stats",
    "platform slow": "process-state diagnostics — real command-latency samples",
    "platform startup": "process-state diagnostics — startup snapshot ids",
    "platform status": "process-state diagnostics — live uptime",
    "force": (
        "admin re-dispatch wrapper — output depends on live dispatch/"
        "process state, not guild behavior"
    ),
    # --- determinism-seam findings (REBUILD DESIGN INPUT, go/no-go §3) ----
    # These commands are nondeterministic BY CONSTRUCTION in the current
    # bot: unseeded private RNG instances or real-TTL in-memory caches that
    # neither per-case seeding nor the pinned clock can reach. The rebuild
    # kernel should make clock+RNG injectable (determinism by design);
    # until then their goldens cannot be stable.
    "catch": "unseeded private RNG in creature spawn selection",
    "treasury grant": "treasury first-touch init rides a real-TTL in-memory cache",
    "platform runtime": "process-state diagnostics — live uptime/loop stats",
}

#: slash-surface-only exclusions (the PREFIX form of the same name replays
#: deterministically and stays covered — only the slash path is excluded).
SLASH_EXCLUDED_COMMANDS: dict[str, str] = {
    "btd6menu": (
        "slash compose path rides a real-TTL in-memory cache (extra edit); "
        "the prefix `!btd6menu` golden covers the surface deterministically"
    ),
    # settle-budget racers: their handlers legitimately take longer than any
    # finite drain budget can distinguish from a stall (provider-health
    # checks with ~10s network timeouts; dataset-scale BTD6 compute on
    # first touch), so response ATTRIBUTION is nondeterministic in a
    # wall-clock process — another face of the injectable-clock design
    # requirement (go/no-go §3 row 6).
    "ai diagnostics": "provider-health checks race the settle budget",
    "ai providers": "provider-health checks race the settle budget",
    "btd6 ct": "dataset-scale compute races the settle budget",
    "btd6 diagnostics": "data-source freshness probes race the settle budget",
    "btd6 rbe": "dataset-scale compute races the settle budget",
    "btd6 relic": "dataset-scale compute races the settle budget",
}


#: The ADVISORY (non-gating) tail — the xfail pattern. These cases capture
#: real behavior worth keeping, but their replay is marginal by
#: construction: in-flow wall-timers or provider/compute latencies sit
#: within ± the settle budget, so attribution flips run-to-run. Their
#: goldens stay (inspectable, still catch gross drift by eye); `check`
#: reports their diffs as advisory instead of failing. Both classes are
#: faces of the injectable-clock/RNG kernel requirement (go/no-go §3 r6).
FLAKY_ADVISORY: dict[str, str] = {
    "sweep.fish": "bite-window sleep (3–6s) sits at the settle-budget edge",
    "sweep.platform_consistency": "live consistency probe (process state)",
    "sweep.slash_ai_readiness": "provider readiness probes race the budget",
    "sweep.slash_btd6_events_latest-data": "data-freshness probe (live age)",
    "sweep.slash_btd6_strat_strategies": (
        "strategy-list compute races the settle budget"
    ),
}


class SweepSkipError(Exception):
    """Raised when an invocation cannot be synthesized for a command."""


def _synthesize_argument(param: dpy_commands.Parameter) -> str:
    """Best-effort literal for one command parameter."""
    annotation = param.annotation
    origin = typing.get_origin(annotation)
    if origin is typing.Union:  # Optional[X] → X
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        annotation = args[0] if args else str

    if annotation in (param.empty, str):
        return "test"
    if annotation is int:
        return "3"
    if annotation is float:
        return "1.5"
    if annotation is bool:
        return "true"
    if annotation is discord.Member or annotation is discord.User:
        return "<@900000000000000103>"  # second_member persona
    if annotation is discord.TextChannel or annotation is discord.abc.GuildChannel:
        return "<#{commands}>"  # placeholder replaced by the runner-side id
    if annotation is discord.Role:
        return "<@&800000000000000201>"  # the Admin role
    if isinstance(annotation, type) and issubclass(annotation, dpy_commands.Converter):
        raise SweepSkipError(f"custom converter {annotation.__name__}")
    raise SweepSkipError(f"unsupported annotation {annotation!r}")


def _invocation_for(command: dpy_commands.Command[Any, Any, Any]) -> str:
    parts = [f"!{command.qualified_name}"]
    for _name, param in command.clean_params.items():
        kind_var = param.kind in (
            param.VAR_POSITIONAL,
            param.KEYWORD_ONLY,
        )
        if not param.required:
            continue  # optional args: capture the no-arg shape
        literal = _synthesize_argument(param)
        if literal == "<#{commands}>":
            literal = "__CHANNEL_COMMANDS__"
        parts.append(literal)
        if kind_var:
            break
    return " ".join(parts)


def build_sweep_cases(bot: Any) -> tuple[list[GoldenCase], dict[str, str]]:
    """(cases, skipped{qualified_name: reason}) from the live bot surface."""
    cases: list[GoldenCase] = []
    skipped: dict[str, str] = {}

    for command in sorted(bot.walk_commands(), key=lambda c: c.qualified_name):
        qname = command.qualified_name
        # hidden commands are still dispatchable behavior (hidden only skips
        # help listings — `!warn`, `!ban`, the mining family are all hidden);
        # they are swept like any other surface.
        if qname in EXCLUDED_COMMANDS or command.name in EXCLUDED_COMMANDS:
            skipped[qname] = EXCLUDED_COMMANDS.get(
                qname,
                EXCLUDED_COMMANDS.get(command.name, "excluded"),
            )
            continue
        try:
            invocation = _invocation_for(command)
        except SweepSkipError as exc:
            skipped[qname] = str(exc)
            continue
        mentions = ("second_member",) if "<@900000000000000103>" in invocation else ()
        subsystem = _subsystem_for(command)
        cases.append(
            GoldenCase(
                id=f"sweep.{qname.replace(' ', '_')}",
                subsystem=subsystem,
                steps=(
                    Step(
                        kind="command",
                        content=invocation,
                        persona="admin",
                        mentions=mentions,
                    ),
                ),
                tags=("sweep",),
                notes="mechanical breadth sweep (admin persona)",
            ),
        )

    for app_command in sorted(
        bot.tree.walk_commands(),
        key=lambda c: c.qualified_name,
    ):
        if not isinstance(app_command, discord.app_commands.Command):
            continue
        qname = app_command.qualified_name
        slash_excluded = {**EXCLUDED_COMMANDS, **SLASH_EXCLUDED_COMMANDS}
        if qname in slash_excluded or app_command.name in slash_excluded:
            skipped[f"/{qname}"] = slash_excluded.get(
                qname,
                slash_excluded.get(app_command.name, "excluded"),
            )
            continue
        options, skip_reason = _slash_options_for(app_command)
        if skip_reason is not None:
            skipped[f"/{qname}"] = skip_reason
            continue
        cases.append(
            GoldenCase(
                id=f"sweep.slash_{qname.replace(' ', '_')}",
                subsystem=_subsystem_for_slash(app_command),
                steps=(
                    Step(
                        kind="slash",
                        name=qname,
                        options=tuple(options),
                        persona="admin",
                    ),
                ),
                tags=("sweep", "slash"),
                notes="mechanical slash sweep (admin persona)",
            ),
        )

    return cases, skipped


def _subsystem_for(command: dpy_commands.Command[Any, Any, Any]) -> str:
    try:
        from utils.subsystem_registry import COMMAND_TO_SUBSYSTEM

        root = command.qualified_name.split(" ")[0]
        return COMMAND_TO_SUBSYSTEM.get(root, "_unmapped")
    except Exception:  # noqa: BLE001 - registry import is env-dependent
        return "_unmapped"


def _subsystem_for_slash(command: Any) -> str:
    binding = getattr(command, "binding", None)
    if binding is not None:
        return type(binding).__name__.replace("Cog", "").lower() or "_unmapped"
    return "_unmapped"


def _slash_options_for(command: Any) -> tuple[list[dict[str, Any]], str | None]:
    """Synthesize interaction options; None reason = drivable."""
    options: list[dict[str, Any]] = []
    for param in command.parameters:
        if not param.required:
            continue
        if param.type is discord.AppCommandOptionType.string:
            options.append({"name": param.name, "type": 3, "value": "test"})
        elif param.type is discord.AppCommandOptionType.integer:
            options.append({"name": param.name, "type": 4, "value": 3})
        elif param.type is discord.AppCommandOptionType.boolean:
            options.append({"name": param.name, "type": 5, "value": True})
        elif param.type is discord.AppCommandOptionType.number:
            options.append({"name": param.name, "type": 10, "value": 1.5})
        else:
            return [], f"unsupported required option type {param.type.name}"
    return options, None
