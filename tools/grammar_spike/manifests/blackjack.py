"""Blackjack — the STATEFUL-GAME spike subsystem (escape-hatch-heavy).

Source of truth (verified 2026-07-02):
    cogs/blackjack_cog.py       — 4 commands (:431–597), reaction-join
                                  (:410), recovery (:157–297)
    cogs/blackjack/schemas.py   — default_entry_fee SettingSpec
    views/blackjack/solo_view.py — Hit/Stand/Double (auto custom_ids —
                                  exactly what §3.4's g1: scheme replaces),
                                  static `blackjack:solo:replay` (:289)
    services/blackjack_state.py — session state, game_state checkpoints
    utils/… blackjack engine    — pure rules (the shipped engine pattern)

This is the honest stress test: the *session choreography* (escrow, settle
-once, timeouts, recovery, rematch) is exactly `ChallengeSessionSpec` —
kernel-owned. What stays code is the game ENGINE (rules) and the board
RENDERER — both named escape-hatch classes in §2.9. The grammar holds IF
you accept that a game is: declared session + declared money flow +
tier-3 engine + tier-3 renderer. It does NOT try to express game rules,
and must never (that's the "worse programming language" failure mode).
"""

from __future__ import annotations

from tools.grammar_spike.spec import (
    Activation,
    ChallengeSessionSpec,
    CommandKind,
    CommandSpec,
    CostVector,
    GameFacet,
    GatewayListenerSpec,
    HandlerRef,
    HelpEntrySpec,
    LeaderboardSpec,
    PanelActionSpec,
    PanelSpec,
    SettingSpec,
    SubsystemManifest,
)

_ = Activation  # blackjack's one setting is int-typed — no activation choice

BLACKJACK_MANIFEST = SubsystemManifest(
    key="blackjack",
    display_name="Blackjack",
    description="Casino blackjack — solo, PvP, and tournaments.",
    emoji="🃏",
    category="games",
    visibility_tier="user",
    dependencies=("economy",),  # escrow flows through the INV-F seam (§1.3)
    parent_hub="games",  # [A]
    commands=(
        # cogs/blackjack_cog.py:431
        CommandSpec(
            name="blackjack",
            aliases=("bj",),
            kind=CommandKind.PREFIX,
            summary="Start a blackjack round (solo, or PvP with a mention).",
            usage="!blackjack <bet> [@opponent]",
            # TIER 3 (thin): session creation binds bet parsing + escrow +
            # engine deal — the session SPEC owns the lifecycle after that.
            route=HandlerRef(
                "blackjack.start",
                justification="bet parse + engine deal; lifecycle is spec-owned",
            ),
        ),
        # :516
        CommandSpec(
            name="bjtournament",
            aliases=("bjtourn",),
            kind=CommandKind.PREFIX,
            summary="Open a blackjack tournament lobby.",
            route=HandlerRef(
                "blackjack.tournament_open",
                justification="multi-player lobby orchestration",
            ),
        ),
        # :577
        CommandSpec(
            name="bjstart",
            kind=CommandKind.PREFIX,
            summary="Force-start the pending tournament.",
            route=HandlerRef("blackjack.tournament_start", justification="lobby op"),
        ),
        # :589
        CommandSpec(
            name="bjstatus",
            kind=CommandKind.PREFIX,
            summary="Show the running tournament's status.",
            route=HandlerRef("blackjack.tournament_status", justification="lobby op"),
        ),
    ),
    panels=(
        # The live game board: renderer_override IS the declared design
        # (§2.9 game-board class). Actions declared so authority + audit +
        # namespace hold; rendering + hand state stay code.
        PanelSpec(
            panel_id="blackjack.board",
            subsystem="blackjack",
            title="🃏 Blackjack",
            audience="invoker",
            renderer_override=HandlerRef(
                "blackjack.render_board",
                justification="stateful game board (cards, totals, reveal flow)",
            ),
            actions=(
                PanelActionSpec(
                    action_id="hit",
                    label="Hit",
                    emoji="👊",
                    style="success",
                    handler=HandlerRef("blackjack.hit", justification="game move"),
                ),
                PanelActionSpec(
                    action_id="stand",
                    label="Stand",
                    emoji="✋",
                    handler=HandlerRef("blackjack.stand", justification="game move"),
                ),
                PanelActionSpec(
                    action_id="double",
                    label="Double Down",
                    handler=HandlerRef(
                        "blackjack.double",
                        justification="game move + second escrow leg",
                    ),
                ),
            ),
        ),
        # views/blackjack/solo_view.py:289 — static persistent id, verbatim
        PanelSpec(
            panel_id="blackjack.result",
            subsystem="blackjack",
            title="Round result",
            renderer_override=HandlerRef(
                "blackjack.render_result",
                justification="outcome card with hand reveal",
            ),
            actions=(
                PanelActionSpec(
                    action_id="replay",
                    custom_id_override="blackjack:solo:replay",
                    label="🔁 Play again",
                    handler=HandlerRef(
                        "blackjack.replay",
                        justification="re-enter start flow with same bet",
                    ),
                ),
            ),
        ),
    ),
    settings=(
        # cogs/blackjack/schemas.py — shipped spec, key verbatim
        SettingSpec(
            name="default_entry_fee",
            value_type="int",
            default=0,
            settings_key="blackjack_default_entry_fee",
            capability_required="blackjack.settings.configure",
            hint="Tournament entry fee when none is given.",
        ),
    ),
    gateway_listeners=(
        # cogs/blackjack_cog.py:410 — reaction-based tournament join
        GatewayListenerSpec(
            gateway_event="on_raw_reaction_add",
            handler=HandlerRef(
                "blackjack.reaction_join",
                justification="lobby join via reaction",
            ),
        ),
    ),
    stores=(),  # session state lives in the shared game_state checkpoints;
    # coins flow through economy (INV-F) — blackjack owns no table (019 rule)
    game=GameFacet(
        sessions=(
            ChallengeSessionSpec(
                game_key="blackjack.solo",
                accept_timeout_s=0,  # solo: no accept phase
                turn_timeout_s=120,
                stale_after_s=900,
                settle_once=True,
                persistence="checkpointed",  # recovery paths :157
                escrow=CostVector(currency="coins", amount_source="arg"),
                custom_id_scheme="g1",
                stat_writes=("blackjack.hands", "blackjack.wins"),  # decision 10
                refund_policy=HandlerRef("blackjack.refund"),
            ),
            ChallengeSessionSpec(
                game_key="blackjack.pvp",
                accept_timeout_s=60,
                turn_timeout_s=120,
                stale_after_s=900,
                settle_once=True,
                persistence="checkpointed",
                escrow=CostVector(currency="coins", amount_source="arg"),
                custom_id_scheme="g1",
                stat_writes=("blackjack.hands", "blackjack.wins"),
                refund_policy=HandlerRef("blackjack.refund"),
            ),
            ChallengeSessionSpec(
                game_key="blackjack.tournament",
                accept_timeout_s=120,
                turn_timeout_s=120,
                stale_after_s=1800,
                settle_once=True,
                persistence="checkpointed",
                escrow=CostVector(
                    currency="coins",
                    amount_source="setting:blackjack_default_entry_fee",
                ),
                custom_id_scheme="g1",
                stat_writes=("blackjack.tournaments",),
                refund_policy=HandlerRef("blackjack.refund"),
            ),
        ),
        leaderboards=(
            # decision 10: honest boards land WITH the port's stat writes
            LeaderboardSpec(
                board_id="blackjack.wins",
                stat_key="blackjack.wins",
                metric="sum",
            ),
        ),
    ),
    help=HelpEntrySpec(
        summary="Blackjack against the house or friends; coins ride on it.",
        examples=("!blackjack 50", "!blackjack 50 @rival", "!bjtournament"),
    ),
)
