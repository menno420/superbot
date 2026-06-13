"""Welcome subsystem package (welcome v1, owner decision Q-0110).

Greets members on join, optionally bids farewell on leave, and optionally
grants an entry role on join.  ``schemas`` declares the operator-editable
:class:`~core.runtime.subsystem_schema.SubsystemSchema`; the member listeners
and the ``!welcome`` status command live in :mod:`cogs.welcome_cog`, and the
greeting/farewell logic in :mod:`services.welcome_service`.
"""
