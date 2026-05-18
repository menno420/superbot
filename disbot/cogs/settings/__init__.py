"""Settings subsystem package — S5.

Empty package marker.  The S5 Settings Manager cog does not declare
any ``SettingSpec``/``BindingSpec``/``ResourceRequirement`` of its
own; it is a read-only browser over the *other* subsystems' schemas.
A future PR may add a small ``SubsystemSchema`` here for cog-local
preferences (e.g. ``hub_page_size``), gated on whether that scope is
ever needed.
"""

from __future__ import annotations

__all__: list[str] = []
