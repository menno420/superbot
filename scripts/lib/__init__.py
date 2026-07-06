"""scripts/lib — shared helpers reused across the standalone scripts in ``scripts/``.

``scripts/`` is not a package (each script is run directly, e.g. ``python3 scripts/foo.py``), so a
consumer adds ``scripts/`` to ``sys.path`` and imports ``lib.<mod>`` (see check_ci_coverage.py /
check_codeql_coverage.py). Keep modules here dependency-light and side-effect-free at import time.
"""
