"""Automod subsystem package (cogs.automod_cog).

automod v1 (owner decision Q-0108): the automated message-filter layer beneath
manual moderation.  The detection engine lives in ``services.automod_service``
(pure, testable); this package holds the Discord-facing glue:

    schemas   — the SubsystemSchema (operator config via the !settings widget)
    listener  — the message-pipeline stage body (delete + warn orchestration)
"""
