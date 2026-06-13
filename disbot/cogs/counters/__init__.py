"""Counters subsystem package (server counters v1, owner decision Q-0110).

Keeps designated channel names showing a live server stat (total members /
humans / bots) — the "statdock" pattern.  ``schemas`` declares the
operator-editable :class:`~core.runtime.subsystem_schema.SubsystemSchema`; the
periodic rename loop and the ``!counters`` status command live in
:mod:`cogs.counters_cog`, and the count/rename logic in
:mod:`services.counter_service`.
"""
