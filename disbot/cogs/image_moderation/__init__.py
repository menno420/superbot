"""Image-moderation cog package (Q-0108).

The cog glue lives in ``cogs.image_moderation_cog``; this package holds the
unit-testable pieces kept out of the cog (the F-3 thin-cog convention):

* ``schemas`` — the :class:`SettingSpec` declarations + ``register_schemas``.
* ``listener`` — ``process_message`` (the pipeline-stage body: scan → act).
"""
