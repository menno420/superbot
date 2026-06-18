"""Security subsystem package (security tiers 1+2, owner decision Q-0111).

Screens joining members through raid detection (join-rate lockdown + staff
alert) and an account-age filter (alert/kick on too-young accounts).
``schemas`` declares the operator-editable
:class:`~core.runtime.subsystem_schema.SubsystemSchema`; the ``on_member_join``
listener and the ``!security`` status command live in :mod:`cogs.security_cog`,
and the detection/orchestration logic in :mod:`services.security_service`.

The two DECLINED tiers (alt-detection / VPN blocking, Q-0111) are deliberately
absent — this subsystem makes no external calls and stores no PII.
"""
