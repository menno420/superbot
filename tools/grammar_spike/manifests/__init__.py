"""Real example manifests for the grammar spike — source-verified 2026-07-02.

Each module declares one shipped subsystem in the §2 grammar, complete: every
command, panel component, setting, binding, resource, event, listener, store,
and behavioral handler that exists in `disbot/` today, with `file:line`
provenance in the module docstring. TIER markers on handler refs record the
honest classification measured by `tools/grammar_spike/measure.py`.
"""

from tools.grammar_spike.manifests.blackjack import BLACKJACK_MANIFEST
from tools.grammar_spike.manifests.karma import KARMA_MANIFEST
from tools.grammar_spike.manifests.server_logging import LOGGING_MANIFEST

ALL_MANIFESTS = (KARMA_MANIFEST, LOGGING_MANIFEST, BLACKJACK_MANIFEST)

__all__ = ["ALL_MANIFESTS", "KARMA_MANIFEST", "LOGGING_MANIFEST", "BLACKJACK_MANIFEST"]
