"""Mining subsystem — write orchestration awaiting the RS02 workflow service.

The pure domain modules (items, rewards, world, exploration, recipes, and
the pricing/durability helpers) relocated to ``utils/mining/`` (RS02
stage 1) so views and services import them without layer violations.
What remains here is the *orchestration* half — the multi-write
``apply_*`` operations — which converges into
``services/mining_workflow.py`` (workshop ops this stage; market and the
remaining writers in RS02 stage 2, after which this package is deleted).

Modules:
    market   — sell/buy orchestration (apply_sell / apply_sell_all / apply_buy)
    workshop — durability orchestration (apply_wear / apply_repair / apply_craft)
"""
