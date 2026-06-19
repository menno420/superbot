"""Run-order-robust loader for the two web services' apps under test.

Both ``botsite/`` and ``dashboard/`` deploy with Railway *Root Directory* = their own
folder, so each ``app.py`` runs as a **top-level** module and imports its siblings by
**bare name** (``import submissions_db`` / ``import ratelimit`` / ...) after a
``sys.path`` shim. That is correct at runtime — each service is its own process, so only
one set of siblings is ever loaded.

In a single **test** process that loads *both* apps, however, those bare names collide
in ``sys.modules``: whichever service imports first wins, and the second silently gets
the *other* service's namesake. The concrete bite this fixes: ``botsite/submissions_db``
is INSERT-only and has **no** ``set_status`` / ``list_pending``, so when the bot-site
tests run before the dashboard moderation tests, ``dashboard.app.submissions_db``
resolves to the bot-site module and every moderation test errors with
``AttributeError: ... has no attribute 'set_status'``. It was order-dependent — green in
isolation and in the full-suite CI order, red when ``tests/unit/botsite`` ran first.

:func:`load_web_app` makes each load isolated and order-independent. Before executing an
app it puts that service's own directory first on ``sys.path`` and **evicts any cached
bare module that belongs to a *different* web-service directory**, so the app's bare
sibling imports always re-resolve to its own folder. Previously-loaded apps keep working
because they hold direct references to their already-imported sibling module objects —
eviction only clears the ``sys.modules`` *cache entry*, not the live objects. It also
centralises the ``spec_from_file_location`` boilerplate every web app-test fixture used
to duplicate.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

# Web-service source roots whose top-level sibling modules collide by bare name
# (e.g. ``submissions_db`` / ``ratelimit`` exist in both, with different APIs).
_WEB_ROOT_NAMES = frozenset({"botsite", "dashboard"})


def _evict_foreign_web_siblings(service_dir: Path) -> None:
    """Drop cached *bare* modules that ``service_dir`` has its own version of.

    The eviction is deliberately **narrow**: a cached bare module is dropped only when
    (a) it was imported from a *different* web-service dir AND (b) ``service_dir`` ships
    a same-named file — i.e. it is a genuine collision (``submissions_db`` / ``ratelimit``
    exist in both). A module that lives in only one service (e.g. the dashboard's
    ``websession``, which mints a per-import session secret a test may already hold a
    reference to) is **never** evicted — evicting it would re-import a fresh instance and
    silently break cookie/secret continuity. This makes the load order-independent
    without disturbing any single-service module.
    """
    for name, module in list(sys.modules.items()):
        if "." in name:  # only bare top-level names collide
            continue
        file = getattr(module, "__file__", None)
        if not file:
            continue
        parent = Path(file).resolve().parent
        if (
            parent.name in _WEB_ROOT_NAMES
            and parent != service_dir
            and (service_dir / f"{name}.py").exists()
        ):
            del sys.modules[name]


def load_web_app(app_path: str | Path, alias: str) -> ModuleType:
    """Load a web service's ``app.py`` under ``alias`` — isolated + run-order-robust.

    ``app_path`` is the path to the service's ``app.py``; ``alias`` is the private
    ``sys.modules`` name to register it under (kept per-fixture so multiple suites can
    each hold their own load). Returns the executed module.
    """
    app_file = Path(app_path).resolve()
    service_dir = app_file.parent
    _evict_foreign_web_siblings(service_dir)
    # This service's dir must win bare-name resolution over the other web dir.
    dir_str = str(service_dir)
    if dir_str in sys.path:
        sys.path.remove(dir_str)
    sys.path.insert(0, dir_str)
    spec = importlib.util.spec_from_file_location(alias, app_file)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module
