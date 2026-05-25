"""AI Platform sibling package — M1 settings/policy host.

The AI cog itself stays at ``disbot/cogs/ai_cog.py`` (the standard
SuperBot single-file cog shape). This package holds the AI cog's
SubsystemSchema and, in later milestones, its policy / instruction
helpers — keeping the cog file small while sharing the existing
auto-dispatched settings UI.

See ``docs/AGENT_ORIENTATION.md`` and the refined-direction plan for
the full milestone breakdown.
"""
