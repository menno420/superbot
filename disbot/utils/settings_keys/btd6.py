"""Settings keys owned by the BTD6 subsystem (cogs.btd6_cog) — M4.

The strategy-submission channel binding lets admins designate
specific channels as strategy intakes. The central
natural-language stage decides whether the user may talk naturally
at all; this binding decides whether their message is treated as a
strategy submission rather than a question.
"""

BTD6_STRATEGY_SUBMISSION_CHANNEL = "btd6_strategy_submission_channel"
