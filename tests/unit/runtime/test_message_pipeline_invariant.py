"""INV gate: no raw ``on_message`` listeners outside the message pipeline.

Phase §3.2 consolidated five concurrent ``@commands.Cog.listener()
on_message`` handlers (counting / chain / cleanup / xp / rps_tournament)
into one platform-level listener in ``core/runtime/message_pipeline.py``
that dispatches to registered :class:`MessageStage` handlers in
defined order.

Once the migration is complete this test guards the invariant so a
new raw ``on_message`` listener can't sneak back in.  The catch is
strict — it covers every decorator form that registers an
``on_message`` listener with discord.py:

  * ``@commands.Cog.listener()`` over ``async def on_message``
  * ``@bot.event`` over ``async def on_message``
  * ``@bot.listen("on_message")`` over any async function

The lone permitted site is ``core/runtime/message_pipeline.py``,
which intentionally registers the single platform listener via
``@bot.listen("on_message")`` inside :func:`setup`.

If you need to extend message handling, **register a MessageStage**
with the pipeline (see XpStage / CleanupStage / CountingStage /
ChainStage / RpsTournamentStage for examples).  Adding a new raw
listener brings back the ordering bugs §2.2 was created to fix.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_ROOT = REPO_ROOT / "disbot"

ALLOW_LIST = {
    "disbot/core/runtime/message_pipeline.py",
}


def _decorator_targets_on_message(dec: ast.expr) -> bool:
    """Return True if ``dec`` is one of the three on_message-registration forms."""
    # @bot.listen("on_message")  /  @SOMETHING.listen("on_message")
    if isinstance(dec, ast.Call):
        func = dec.func
        # x.listen("on_message")
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "listen"
            and dec.args
            and isinstance(dec.args[0], ast.Constant)
            and dec.args[0].value == "on_message"
        ):
            return True
        # commands.Cog.listener() — caller still checks function name == on_message
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "listener"
            and isinstance(func.value, ast.Attribute)
            and func.value.attr == "Cog"
        ):
            return True
        # bot.event() with no args (rare; @bot.event without parens is the common form)
        if isinstance(func, ast.Attribute) and func.attr == "event":
            return True
    # @bot.event  (attribute, not call)
    if isinstance(dec, ast.Attribute) and dec.attr == "event":
        return True
    return False


def _scan_file(path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, decorator-form)] for every on_message registration."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not _decorator_targets_on_message(dec):
                continue
            # commands.Cog.listener() requires the function NAME to be on_message
            # for it to register as that event.  bot.listen("on_message") and
            # bot.event don't care about the function name — the name is set by
            # the decorator args / event field.  Be conservative and report only
            # when the function name is on_message OR the listen("on_message")
            # form is present.
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                if (
                    dec.func.attr == "listen"
                    and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and dec.args[0].value == "on_message"
                ):
                    out.append((node.lineno, '@x.listen("on_message")'))
                    break
                if dec.func.attr == "listener" and node.name == "on_message":
                    out.append((node.lineno, "@commands.Cog.listener() on_message"))
                    break
                if dec.func.attr == "event" and node.name == "on_message":
                    out.append((node.lineno, "@bot.event on_message"))
                    break
            elif isinstance(dec, ast.Attribute) and dec.attr == "event":
                if node.name == "on_message":
                    out.append((node.lineno, "@bot.event on_message"))
                    break
    return out


def test_no_raw_on_message_listeners_outside_pipeline() -> None:
    violations: list[str] = []
    for path in SCAN_ROOT.rglob("*.py"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOW_LIST:
            continue
        for lineno, form in _scan_file(path):
            violations.append(
                f"{rel}:{lineno}: {form} — register a MessageStage with "
                "core.runtime.message_pipeline instead",
            )
    assert not violations, (
        "raw on_message listeners found outside "
        "core/runtime/message_pipeline.py:\n\n" + "\n".join(violations)
    )
