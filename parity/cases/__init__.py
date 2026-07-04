"""The golden case corpus.

Two populations:

* ``sweep`` — mechanically generated breadth: every enumerable prefix/slash
  command driven with synthesized arguments (or captured refusing them).
  Breadth-first honesty: even a usage-error reply is real behavior.
* ``curated`` — hand-written depth: multi-step flows (panels, games, config
  mutations) for representative subsystems.
"""

from parity.cases.curated import CURATED_CASES

__all__ = ["CURATED_CASES"]
