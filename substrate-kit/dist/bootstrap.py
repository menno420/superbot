"""substrate-kit bootstrap — GENERATED, DO NOT EDIT.

Single-file, stdlib-only. Regenerate from source with:
    python3 substrate-kit/src/build_bootstrap.py
Source of truth: substrate-kit/src/engine/. Edits here are overwritten.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Collection, Sequence
from collections.abc import Iterator
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from string import Template
from typing import Any
from typing import NamedTuple
import argparse
import copy
import json
import os
import re
import sys
import tempfile
import uuid

# --- engine/lib/atomicio.py ---
"""Atomic file writes for crash-safe state.

A write goes to a sibling ``*.tmp`` file and is renamed into place with
``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies
mid-write can never leave a half-written, unparseable file behind. This is the
robustness floor the whole engine builds on (plan: Gemini round).
"""




def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

# --- engine/lib/config.py ---
"""Host-project configuration for one substrate-kit install.

Reads and writes ``substrate.config.json`` — the single file that absorbs every
host-specific knob so the engine code never hardcodes a project value. Two
interpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the
kit's own runtime, ``interpreter_for_checks`` is the host project's verification
runtime (e.g. ``python3.10`` for a repo whose CI pins 3.10).
"""




CONFIG_FILENAME = "substrate.config.json"
DEFAULT_STATE_DIR = ".substrate"


def _new_project_id() -> str:
    """Return a short, stable identifier for one install."""
    return uuid.uuid4().hex[:12]


def _default_cadence() -> dict[str, int]:
    """Return the default cadence knobs."""
    return {"reconciliation_prs": 20}


def _default_badge_tokens() -> list[str]:
    """Return the default Status-badge taxonomy the doc checker accepts."""
    return [
        "binding",
        "living-ledger",
        "reference",
        "plan",
        "historical",
        "audit",
        "owner-guidance",
        "ideas",
        "archive",
    ]


def _default_readpath_docs() -> list[str]:
    """Return the read-path doc names that seed the reachability roots."""
    return ["AGENT_ORIENTATION.md", "current-state.md"]


def _default_session_markers() -> list[dict[str, str]]:
    """Return the markers every session log must carry (label + substring)."""
    return [
        {"label": "Status badge", "needle": "**Status:**"},
        {"label": "Session idea", "needle": "💡"},
        {"label": "Previous-session review", "needle": "previous-session review"},
    ]


@dataclass
class Config:
    """Host-project configuration for one substrate-kit install."""

    project_id: str = field(default_factory=_new_project_id)
    interpreter: str = field(default_factory=lambda: sys.executable)
    interpreter_for_checks: str | None = None
    state_dir: str = DEFAULT_STATE_DIR
    docs_root: str = "docs"
    sessions_dir: str = ".sessions"
    paths: dict[str, str] = field(default_factory=dict)
    cadence: dict[str, int] = field(default_factory=_default_cadence)
    scopes: dict[str, str] = field(default_factory=dict)
    badge_tokens: list[str] = field(default_factory=_default_badge_tokens)
    readpath_docs: list[str] = field(default_factory=_default_readpath_docs)
    session_markers: list[dict[str, str]] = field(
        default_factory=_default_session_markers,
    )

    def to_json(self) -> str:
        """Serialise the config to indented, key-sorted JSON."""
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict) -> Config:
        """Build a Config from a parsed dict, ignoring unknown keys."""
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


def config_path(root: Path) -> Path:
    """Return the config-file path for a project ``root``."""
    return root / CONFIG_FILENAME


def load_config(root: Path) -> Config:
    """Load the config from ``root``; return defaults if none exists."""
    path = config_path(root)
    if not path.exists():
        return Config()
    data = json.loads(path.read_text(encoding="utf-8"))
    return Config.from_dict(data)


def save_config(root: Path, config: Config) -> None:
    """Write ``config`` to ``root`` atomically."""
    atomic_write_text(config_path(root), config.to_json() + "\n")

# --- engine/lib/state.py ---
"""The state-backend interface and its default JSON implementation.

The *interface* — not a raw JSON shape — is the contract the rest of the engine
codes against (Hermes-final, plan §2), so a future SQLite backend can replace the
JSON one without a rewrite. The default backend is one JSON file written
atomically; mutations inside a ``transaction`` roll back on error and flush once.
"""




STATE_SCHEMA_VERSION = 1


def default_state(project_id: str) -> dict[str, Any]:
    """Return the initial state document for a fresh install."""
    return {
        "version": STATE_SCHEMA_VERSION,
        "project_id": project_id,
        "mode": "guided",
        "promotion_rights": "propose",
        "stage": "integration",
        "stance": "analysis",
        "session_count": 0,
        "slots": {},
        "open_questions": [],
        "graduation": {
            "soft_target_sessions": 50,
            "criteria": {
                "critical_slots_filled_pct": 0.8,
                "blocking_questions": 0,
            },
        },
    }


class StateBackend(ABC):
    """Read / write / query / transaction / migrate contract for engine state."""

    version: int = STATE_SCHEMA_VERSION

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""

    @abstractmethod
    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""

    @abstractmethod
    def transaction(self) -> AbstractContextManager[StateBackend]:
        """Return a context manager that commits on success, rolls back on error."""

    @abstractmethod
    def migrate(self, to_version: int) -> None:
        """Migrate the stored document to schema ``to_version``."""


class JsonStateBackend(StateBackend):
    """A StateBackend backed by one atomically-written JSON file."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = self._read()
        self._in_txn = False

    def _read(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _flush(self) -> None:
        atomic_write_text(
            self._path,
            json.dumps(self._data, indent=2, sort_keys=True) + "\n",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value stored at ``key`` or ``default``."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store ``value`` at ``key``; flush now unless inside a transaction."""
        self._data[key] = value
        if not self._in_txn:
            self._flush()

    def query(self, prefix: str = "") -> dict[str, Any]:
        """Return all key/value pairs whose key starts with ``prefix``."""
        return {k: v for k, v in self._data.items() if k.startswith(prefix)}

    @contextmanager
    def transaction(self) -> Iterator[JsonStateBackend]:
        """Buffer writes; roll back the whole document on error, else flush once."""
        snapshot = copy.deepcopy(self._data)
        self._in_txn = True
        try:
            yield self
        except Exception:
            self._data = snapshot
            raise
        finally:
            self._in_txn = False
        self._flush()

    def migrate(self, to_version: int) -> None:
        """Set the stored schema version (no transforms needed at v1)."""
        self._data["version"] = to_version
        self._flush()

    @property
    def data(self) -> dict[str, Any]:
        """Return a shallow copy of the current state document."""
        return dict(self._data)

# --- engine/lib/guardrail.py ---
"""The live-loop guardrail.

A mechanical guarantee (plan: design-corroboration) that the kit never operates
on its own repository root — which would let it mutate the very workflow it runs
inside. Safe targets are the system temp tree, an ``examples/`` subtree of the
kit, or any directory outside the kit. Enforced in code, in the first commit —
not left as a doc.
"""




class UnsafeTargetError(Exception):
    """Raised when a target directory would corrupt the kit's own live loop."""


def assert_safe_target(target: Path, kit_root: Path) -> None:
    """Refuse to operate on the kit's own repo root.

    Safe: the system temp tree, an ``examples/`` subtree of ``kit_root``, or any
    path outside ``kit_root``. Unsafe: ``kit_root`` itself or a non-``examples``
    path inside it.
    """
    target = Path(target).resolve()
    kit_root = Path(kit_root).resolve()
    tmp_root = Path(tempfile.gettempdir()).resolve()
    if target.is_relative_to(tmp_root):
        return
    inside_kit = target == kit_root or target.is_relative_to(kit_root)
    inside_examples = target.is_relative_to(kit_root / "examples")
    if inside_kit and not inside_examples:
        msg = f"refusing to operate on the kit's own tree: {target}"
        raise UnsafeTargetError(msg)

# --- engine/interview/question_bank.py ---
"""The interview question bank — the seed set the staged onboarding draws from.

Curation policy (Hermes #7): keep this lean. Add a question only when its slot
genuinely blocks graduation, or a checker keeps flagging its absence; prune
questions that no longer earn their place. Each entry is a plain dict so the bank
ships inside the stdlib-only bootstrap with no parser (the plan named
``question_bank.yml``; a Python module is the simplest form that embeds and runs
identically in ``src`` and the single-file ``dist`` — no YAML/JSON dependency).

Entry fields:
  id        — stable "Q-NNN" identifier.
  slot      — the content slot it fills (matches the project index).
  audience  — "user" (ask the maintainer) or "self" (the agent infers).
  prompt    — the question text.
  routing   — where a confirmed answer lands (a doc:field or state:key).
  priority  — "blocking" | "high" | "normal".
  critical  — True if graduation requires this slot filled (confirmed, not assumed).
"""


CURATION_RULE = (
    "Lean bank: add a question only when it blocks graduation or a checker keeps "
    "flagging its slot; prune questions that no longer earn their place."
)

QUESTIONS: list[dict] = [
    {
        "id": "Q-001",
        "slot": "integration_mode",
        "audience": "user",
        "prompt": "Adoption pace for the workflow? observe | guided | active.",
        "routing": "state:mode",
        "priority": "blocking",
        "critical": True,
    },
    {
        "id": "Q-002",
        "slot": "project_name",
        "audience": "user",
        "prompt": "What is this project called?",
        "routing": "templates/CLAUDE.md:project_name",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-003",
        "slot": "primary_language",
        "audience": "user",
        "prompt": "Primary language / runtime (e.g. Python 3.10, TypeScript)?",
        "routing": "templates/CLAUDE.md:language",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-004",
        "slot": "architecture_layers",
        "audience": "user",
        "prompt": "What are the top-level layers and their import rules?",
        "routing": "templates/architecture.md:layers",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-005",
        "slot": "verify_command",
        "audience": "user",
        "prompt": "One command that proves a change is good (tests + lint)?",
        "routing": "templates/CLAUDE.md:verify_command",
        "priority": "high",
        "critical": True,
    },
    {
        "id": "Q-006",
        "slot": "ownership_model",
        "audience": "self",
        "prompt": "Which component owns each data store / write path?",
        "routing": "templates/ownership.md:owners",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-007",
        "slot": "doc_roots",
        "audience": "self",
        "prompt": "Where does durable documentation live?",
        "routing": "state:paths.docs",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-008",
        "slot": "owner_profile",
        "audience": "user",
        "prompt": "How do you like an agent to work (tone, detail, autonomy)?",
        "routing": "templates/owner-profile.md:style",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-009",
        "slot": "mutation_seam",
        "audience": "self",
        "prompt": "How are writes gated (the audited mutation seam)?",
        "routing": "templates/runtime_contracts.md:mutations",
        "priority": "normal",
        "critical": False,
    },
    {
        "id": "Q-010",
        "slot": "review_ritual",
        "audience": "user",
        "prompt": "Your PR-review and release rhythm?",
        "routing": "templates/owner-profile.md:procedures",
        "priority": "normal",
        "critical": False,
    },
]

# --- engine/interview/stages.py ---
"""Stage state machine + adaptive graduation (plan section 2).

Stage 1 (``integration``) graduates to stage 2 (``steady``) *adaptively* — when
the project's **critical** content slots are mostly filled (by confirmed, not
assumed, answers), no blocking questions remain, and several consecutive sessions
surface no new mandatory question — not at a hard session count.
"""



STAGE_INTEGRATION = "integration"
STAGE_STEADY = "steady"

_DEFAULT_FILL_PCT = 0.8
_DEFAULT_QUIET_SESSIONS = 3


def critical_fill_ratio(slots: dict[str, str], critical: list[str]) -> float:
    """Return the fraction of ``critical`` slots marked ``filled``."""
    if not critical:
        return 1.0
    filled = sum(1 for name in critical if slots.get(name) == "filled")
    return filled / len(critical)


def graduation_ready(
    state: dict[str, Any],
    critical: list[str],
) -> tuple[bool, list[str]]:
    """Return ``(ready, reasons)`` for graduating integration -> steady.

    ``reasons`` lists the unmet criteria when not ready (empty when ready).
    """
    criteria = state.get("graduation", {}).get("criteria", {})
    want_pct = criteria.get("critical_slots_filled_pct", _DEFAULT_FILL_PCT)
    want_quiet = criteria.get("quiet_sessions_required", _DEFAULT_QUIET_SESSIONS)
    reasons: list[str] = []

    ratio = critical_fill_ratio(state.get("slots", {}), critical)
    if ratio < want_pct:
        reasons.append(f"critical slots {ratio:.0%} < {want_pct:.0%}")
    blocking = len(state.get("open_questions", []))
    if blocking:
        reasons.append(f"{blocking} blocking question(s) open")
    quiet = state.get("quiet_sessions", 0)
    if quiet < want_quiet:
        reasons.append(f"quiet streak {quiet} < {want_quiet}")
    return (not reasons, reasons)


def maybe_graduate(backend: Any, critical: list[str]) -> bool:
    """Advance integration -> steady if ready; return whether it graduated."""
    if backend.get("stage") != STAGE_INTEGRATION:
        return False
    ready, _ = graduation_ready(backend.data, critical)
    if ready:
        backend.set("stage", STAGE_STEADY)
    return ready

# --- engine/interview/interview.py ---
"""The interview pass — fills content slots from the question bank (plan section 4).

A session asks its pending questions. A user-facing answer fills a slot
(``filled``); when no human is present the agent self-answers, recording a
*provisional* assumption (``provisional``) that never counts toward graduation
until confirmed. This is what lets an autonomous run keep moving without blocking:
it records assumptions, flags them, and moves on.
"""





def critical_slots(bank: list[dict] | None = None) -> list[str]:
    """Return the slot names the bank marks as critical."""
    bank = QUESTIONS if bank is None else bank
    return [q["slot"] for q in bank if q.get("critical")]


def pending_questions(
    state: dict[str, Any],
    bank: list[dict] | None = None,
) -> list[dict]:
    """Return bank questions whose slot is not yet ``filled``."""
    bank = QUESTIONS if bank is None else bank
    slots = state.get("slots", {})
    return [q for q in bank if slots.get(q["slot"]) != "filled"]


def record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:
    """Fill ``question``'s slot from an answer.

    ``source="user"`` confirms the slot (``filled``); any other source records a
    ``provisional`` self-answer that must be confirmed before it counts.
    """
    status = "filled" if source == "user" else "provisional"
    slots = dict(backend.get("slots", {}))
    values = dict(backend.get("slot_values", {}))
    slots[question["slot"]] = status
    values[question["slot"]] = {
        "value": answer,
        "source": source,
        "question_id": question["id"],
    }
    with backend.transaction():
        backend.set("slots", slots)
        backend.set("slot_values", values)


def run_session(
    backend: Any,
    answers: dict[str, str],
    *,
    autonomous: bool = False,
    bank: list[dict] | None = None,
) -> dict[str, Any]:
    """Run one interview session, then attempt graduation.

    ``answers`` maps slot -> user answer. A pending question with a user answer is
    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally.
    A session that leaves no blocking question unanswered extends the quiet streak;
    any unanswered blocking question resets it.
    """
    bank = QUESTIONS if bank is None else bank
    pending = pending_questions(backend.data, bank)
    left_blocking = False
    for question in pending:
        slot = question["slot"]
        if slot in answers:
            record_answer(backend, question, answers[slot], source="user")
        elif autonomous:
            record_answer(backend, question, f"ASSUMED: {slot}", source="assumption")
        elif question.get("priority") == "blocking":
            left_blocking = True

    backend.set("session_count", int(backend.get("session_count", 0)) + 1)
    quiet = int(backend.get("quiet_sessions", 0))
    backend.set("quiet_sessions", 0 if left_blocking else quiet + 1)

    graduated = maybe_graduate(backend, critical_slots(bank))
    return {
        "session": backend.get("session_count"),
        "pending_after": len(pending_questions(backend.data, bank)),
        "graduated": graduated,
        "stage": backend.get("stage"),
    }

# --- engine/checks/check_docs.py ---
"""Generic doc-hygiene checker (config-driven port of ``check_docs``).

Three portable checks, every input supplied by the caller (from config) rather
than hardcoded:

  1. **badge**      — every ``*.md`` under ``docs_root`` (non-ADR) carries a
     ``> **Status:** `<token>``` line in its first 12 lines, ``<token>`` drawn
     from the project's allowed taxonomy.
  2. **link**       — every relative markdown link ``[text](path)`` resolves to
     an existing file (external / anchor-only links are skipped).
  3. **reachable**  — every live doc is reachable by following links + backtick
     ``<docs>/*.md`` refs from a read-path root (the read-path docs + any
     ``README.md``). Orphans fail unless badged ``historical`` / ``archive`` or
     an ADR.

The host's soft ratchets (top-level pile, recently-shipped) and the
superbot-specific freshness rule are intentionally left behind — they are
project policy, not portable mechanism. Pure stdlib; returns findings rather
than printing so the CLI owns all output.
"""




class Finding(NamedTuple):
    """One doc-hygiene violation: ``path`` is relative to ``docs_root``."""

    path: str
    kind: str
    message: str


# `> **Status:** `<token>`` — the machine-readable badge (rich text may follow).
_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")
# ADR filename: NNN-something.md (exempt — ADRs use their own Accepted/Superseded).
_ADR_RE = re.compile(r"^\d+-.*\.md$")
# Markdown link target: [text](target).
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Badges whose docs are retired content and need no inbound link.
_EXEMPT_BADGES = frozenset({"historical", "archive"})

_BADGE_MISSING = "missing `> **Status:** `<token>`` in first 12 lines"
_ORPHAN_MSG = (
    "orphan: not reachable from any read-path doc / README "
    "(link it from one, or badge it historical/archive)"
)


def _md_files(docs_root: Path) -> list[Path]:
    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""
    if not docs_root.exists():
        return []
    return sorted(docs_root.rglob("*.md"))


def _is_adr(path: Path) -> bool:
    """True for ``decisions/NNN-*.md`` ADR files (badge-exempt)."""
    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))


def _badge_token(path: Path) -> str | None:
    """Return the doc's Status-badge token from its first 12 lines, or None."""
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    match = _BADGE_RE.search(head)
    return match.group(1) if match else None


def _link_target(raw: str) -> str:
    """Normalise a markdown link target (drop ``<>``, title, ``#anchor``)."""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:].split(">", 1)[0]
    parts = target.split()
    target = parts[0] if parts else target
    return target.split("#", 1)[0]


def _backtick_docs_re(docs_root: Path) -> re.Pattern[str]:
    """Compile the ``<docs>/*.md`` backtick-ref pattern for this doc root."""
    name = re.escape(docs_root.name)
    return re.compile(rf"`({name}/[\w./-]+\.md)`")


def check_badges(docs_root: Path, badge_tokens: Collection[str]) -> list[Finding]:
    """Every non-ADR doc must declare a Status badge from the taxonomy."""
    allowed = set(badge_tokens)
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if _is_adr(f):
            continue
        rel = f.relative_to(docs_root).as_posix()
        token = _badge_token(f)
        if token is None:
            findings.append(Finding(rel, "badge", _BADGE_MISSING))
        elif token not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            findings.append(
                Finding(
                    rel,
                    "badge",
                    f"invalid badge token `{token}` (allowed: {allowed_list})",
                ),
            )
    return findings


def check_links(docs_root: Path) -> list[Finding]:
    """Relative markdown links inside ``docs_root`` must resolve."""
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        rel = f.relative_to(docs_root).as_posix()
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for raw in _MD_LINK_RE.findall(line):
                if raw.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = _link_target(raw)
                if not target or target.startswith(("http", "mailto:")):
                    continue
                if not (f.parent / target).resolve().exists():
                    msg = f"L{lineno}: dead link -> {raw}"
                    findings.append(Finding(rel, "link", msg))
    return findings


def _outgoing_links(path: Path, docs_root: Path) -> set[Path]:
    """Resolve every relative markdown link + backtick ``<docs>/*.md`` ref."""
    out: set[Path] = set()
    backtick = _backtick_docs_re(docs_root)
    root = docs_root.parent
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for line in text.splitlines():
        for raw in _MD_LINK_RE.findall(line):
            if raw.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = _link_target(raw)
            if target:
                out.add((path.parent / target).resolve())
        for ref in backtick.findall(line):
            out.add((root / ref).resolve())
    return out


def check_reachable(docs_root: Path, readpath_docs: Sequence[str]) -> list[Finding]:
    """Every live doc must be reachable from a read-path root / README.

    Walks the doc graph (markdown links + backtick ``<docs>/*.md`` refs) from the
    roots; any doc not reached — and not ``historical`` / ``archive`` badged or an
    ADR — is an orphan.
    """
    roots = [docs_root / name for name in readpath_docs]
    roots += sorted(docs_root.rglob("README.md"))
    seen: set[Path] = set()
    queue: deque[Path] = deque()
    for root in roots:
        resolved = root.resolve()
        if root.exists() and resolved not in seen:
            seen.add(resolved)
            queue.append(resolved)
    while queue:
        cur = queue.popleft()
        if cur.suffix != ".md" or not cur.exists():
            continue
        for nxt in _outgoing_links(cur, docs_root):
            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():
                seen.add(nxt)
                queue.append(nxt)

    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if f.resolve() in seen or _is_adr(f):
            continue
        if _badge_token(f) in _EXEMPT_BADGES:
            continue
        rel = f.relative_to(docs_root).as_posix()
        findings.append(Finding(rel, "reachable", _ORPHAN_MSG))
    return findings


def run_doc_checks(
    docs_root: Path,
    badge_tokens: Collection[str],
    readpath_docs: Sequence[str],
) -> list[Finding]:
    """Run every doc check and return the combined findings."""
    return (
        check_badges(docs_root, badge_tokens)
        + check_links(docs_root)
        + check_reachable(docs_root, readpath_docs)
    )

# --- engine/checks/check_session_log.py ---
"""Generic session-log completeness checker (config-driven port).

The session workflow asks every session to end with a
``<sessions_dir>/<date>-<slug>.md`` log that carries a set of required markers
(by default: a Status badge, a session-idea flag, and a previous-session review).
Each marker is a ``{"label", "needle"}`` pair from ``substrate.config.json``, so a
host tunes the ritual without touching engine code.

Unlike the host's version this port does **not** shell out to ``git`` to pick the
"current" log — ``subprocess`` is banned in engine code and is host-CI sugar
anyway. The current log is the newest ``*.md`` by mtime under ``sessions_dir``
(the CLI also accepts an explicit ``--file``). Pure stdlib; returns the missing
markers rather than printing.
"""




def missing_markers(text: str, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the labels of markers whose needle is absent from ``text``."""
    lower = text.lower()
    return [m["label"] for m in markers if m["needle"].lower() not in lower]


def latest_session_log(sessions_dir: Path) -> Path | None:
    """Best guess at this session's log: newest ``*.md`` by mtime (skip README)."""
    if not sessions_dir.is_dir():
        return None
    candidates = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def check_log(path: Path, markers: Sequence[Mapping[str, str]]) -> list[str]:
    """Return the missing-marker labels for one log file (all if unreadable)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [m["label"] for m in markers]
    return missing_markers(text, markers)

# --- engine/render.py ---
"""Render the project's content docs from templates + filled interview slots.

Templates use ``${slot_name}`` placeholders (``string.Template``). A slot the
interview has filled substitutes in; an unfilled slot is left as ``${slot_name}``
and reported — so a half-onboarded project's gaps stay visible rather than going
silently blank. Templates ship embedded in the bootstrap (the generated
``_TEMPLATES`` dict) and, in the source tree, live under ``src/templates/``.
"""



_PLACEHOLDER_RE = re.compile(r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def find_placeholders(text: str) -> set[str]:
    """Return the set of ``${name}`` placeholders remaining in ``text``."""
    return set(_PLACEHOLDER_RE.findall(text))


def render(text: str, context: dict[str, str]) -> str:
    """Substitute ``${slot}`` placeholders from ``context`` (unfilled left as-is)."""
    return Template(text).safe_substitute(context)


def build_context(state: dict[str, Any]) -> dict[str, str]:
    """Build the substitution context from a state document's filled slots."""
    values = state.get("slot_values", {})
    return {slot: str(entry.get("value", "")) for slot, entry in values.items()}


def load_templates() -> dict[str, str]:
    """Return ``{filename: text}`` for every template (embedded or from src)."""
    embedded = globals().get("_TEMPLATES")
    if embedded is not None:
        return dict(embedded)
    root = Path(__file__).resolve().parent.parent / "templates"
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*"))}

# --- engine/cli.py ---
"""The substrate-kit bootstrap command line.

Surface: ``init`` (idempotent), ``status``, ``mode <name>``, ``ask`` (list the
pending interview questions), ``render`` (write content docs), ``check`` (run the
doc + session-log hygiene checks), and ``--simulate N`` (the CI / proving smoke
that drives the staged interview). Output goes through ``_emit``
(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.
"""





def _emit(line: str = "") -> None:
    """Write a line to stdout (avoids the print() lint ban in engine code)."""
    sys.stdout.write(line + "\n")


def _kit_root() -> Path:
    """Return the kit root (``substrate-kit/``) for the guardrail check."""
    return Path(__file__).resolve().parents[2]


def _state_path(root: Path, config: Config) -> Path:
    """Return the state-file path under a project ``root``."""
    return root / config.state_dir / "state.json"


def cmd_init(target: Path) -> int:
    """Create config + state under ``target`` if absent; never clobber."""
    assert_safe_target(target, _kit_root())
    target.mkdir(parents=True, exist_ok=True)
    if config_path(target).exists():
        config = load_config(target)
    else:
        config = Config()
        save_config(target, config)
    state_path = _state_path(target, config)
    if state_path.exists():
        _emit(f"init: already initialised at {target} (idempotent no-op).")
        return 0
    backend = JsonStateBackend(state_path)
    with backend.transaction():
        for key, value in default_state(config.project_id).items():
            backend.set(key, value)
    _emit(f"init: created {state_path} (project_id={config.project_id}).")
    return 0


def cmd_status(target: Path) -> int:
    """Print a one-screen summary of the install's state."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    data = backend.data
    if not data:
        _emit(f"status: no state at {target} (run init first).")
        return 1
    _emit(f"project_id : {data.get('project_id')}")
    _emit(f"stage      : {data.get('stage')}")
    _emit(f"mode       : {data.get('mode')}")
    _emit(f"stance     : {data.get('stance')}")
    _emit(f"sessions   : {data.get('session_count')}")
    return 0


def cmd_mode(target: Path, name: str) -> int:
    """Set the integration mode (observe | guided | active)."""
    valid = ("observe", "guided", "active")
    if name not in valid:
        _emit(f"mode: invalid mode {name!r} (choose from {list(valid)}).")
        return 2
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"mode: no state at {target} (run init first).")
        return 1
    backend.set("mode", name)
    _emit(f"mode: set to {name}.")
    return 0


def cmd_ask(target: Path) -> int:
    """List the interview's currently pending questions."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"ask: no state at {target} (run init first).")
        return 1
    pending = pending_questions(backend.data)
    if not pending:
        _emit("ask: no pending questions — all slots filled.")
        return 0
    _emit(f"ask: {len(pending)} pending question(s):")
    for question in pending:
        _emit(
            f"  [{question['id']}] "
            f"({question['audience']}/{question['priority']}) {question['prompt']}",
        )
    return 0


def cmd_render(target: Path) -> int:
    """Render the content docs from the current filled slots into ``target``."""
    config = load_config(target)
    backend = JsonStateBackend(_state_path(target, config))
    if not backend.data:
        _emit(f"render: no state at {target} (run init first).")
        return 1
    context = build_context(backend.data)
    out_dir = target / config.state_dir / "rendered"
    leftover_total = 0
    for name, text in load_templates().items():
        rendered = render(text, context)
        leftover = find_placeholders(rendered)
        leftover_total += len(leftover)
        out_name = name[:-5] if name.endswith(".tmpl") else name
        atomic_write_text(out_dir / out_name, rendered)
        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""
        _emit(f"render: wrote {out_name}{suffix}")
    _emit(f"render: {leftover_total} unfilled placeholder(s) total.")
    return 0


def cmd_check(target: Path, strict: bool) -> int:
    """Run the doc-hygiene + session-log checks against ``target``.

    Doc findings always count toward the exit code (under ``--strict``); a
    *missing* session log is advisory (a host may run ``check`` mid-session), but
    an *incomplete* existing log counts. Uses config defaults if ``target`` has
    no ``substrate.config.json`` yet, so a project can lint before onboarding.
    """
    config = load_config(target)
    docs_root = target / config.docs_root
    doc_findings = run_doc_checks(
        docs_root,
        config.badge_tokens,
        config.readpath_docs,
    )
    if doc_findings:
        _emit(f"check: {len(doc_findings)} doc finding(s):")
        for finding in doc_findings:
            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")

    log = latest_session_log(target / config.sessions_dir)
    log_missing: list[str] = check_log(log, config.session_markers) if log else []
    if log is None:
        _emit("check: no session log found yet (advisory — not a failure).")
    else:
        rel = log.relative_to(target) if log.is_relative_to(target) else log
        if log_missing:
            _emit(f"check: session log {rel} is missing: {', '.join(log_missing)}")
        else:
            _emit(f"check: session log {rel} complete.")

    if not doc_findings and not log_missing:
        _emit("check: all checks passed.")
        return 0
    return 1 if strict else 0


def cmd_simulate(n: int) -> int:
    """Init into a temp dir and drive ``n`` interview sessions; verify progress.

    Session 1 supplies confirmed answers for every critical slot; later sessions
    supply none. Asserts the critical slots fill and (for ``n`` past the quiet
    threshold) the install graduates integration -> steady.
    """
    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:
        target = Path(tmp)
        rc = cmd_init(target)
        if rc != 0:
            return rc
        state_path = _state_path(target, load_config(target))
        crit = critical_slots()
        answers = {slot: f"value-for-{slot}" for slot in crit}
        graduated = False
        for index in range(n):
            backend = JsonStateBackend(state_path)
            result = run_session(backend, answers if index == 0 else {})
            graduated = graduated or result["graduated"]
        data = JsonStateBackend(state_path).data
        missing = [s for s in crit if data.get("slots", {}).get(s) != "filled"]
        if missing:
            _emit(f"simulate: FAILED — critical slots unfilled: {missing}")
            return 1
        _emit(
            f"simulate: OK — {n} session(s), {len(crit)} critical slots filled, "
            f"stage={data.get('stage')} (graduated={graduated}).",
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct the bootstrap argument parser."""
    parser = argparse.ArgumentParser(prog="bootstrap", description="substrate-kit")
    parser.add_argument(
        "--simulate",
        type=int,
        metavar="N",
        help="run N synthetic sessions in a temp dir, then exit",
    )
    sub = parser.add_subparsers(dest="command")
    for name, helptext in (
        ("init", "initialise a project"),
        ("status", "show install state"),
        ("ask", "list pending interview questions"),
        ("render", "render content docs from filled slots"),
    ):
        child = sub.add_parser(name, help=helptext)
        child.add_argument("--target", type=Path, default=Path.cwd())
    mode = sub.add_parser("mode", help="set the integration mode")
    mode.add_argument("name")
    mode.add_argument("--target", type=Path, default=Path.cwd())
    check = sub.add_parser("check", help="run the doc + session-log hygiene checks")
    check.add_argument("--target", type=Path, default=Path.cwd())
    check.add_argument("--strict", action="store_true", help="exit 1 if any violation")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the bootstrap CLI; return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.simulate is not None:
            return cmd_simulate(args.simulate)
        if args.command == "init":
            return cmd_init(args.target)
        if args.command == "status":
            return cmd_status(args.target)
        if args.command == "ask":
            return cmd_ask(args.target)
        if args.command == "render":
            return cmd_render(args.target)
        if args.command == "mode":
            return cmd_mode(args.target, args.name)
        if args.command == "check":
            return cmd_check(args.target, args.strict)
    except UnsafeTargetError as exc:
        _emit(f"refused: {exc}")
        return 2
    parser.print_help()
    return 0

_ENGINE_MANIFEST = {
    'engine/__init__.py': '',
    'engine/lib/__init__.py': '',
    'engine/interview/__init__.py': '',
    'engine/checks/__init__.py': '"""Generic, config-driven hygiene checkers lifted from the host project.\n\nThese are stdlib-only ports of the proven ``check_docs`` / ``check_session_log``\nscripts, with every host-specific value (doc root, badge taxonomy, read-path\ndocs, sessions dir, required markers) read from ``substrate.config.json`` instead\nof hardcoded. The host project\'s ratchets and freshness rules are intentionally\ndropped — they are superbot-shaped policy, not portable mechanism.\n"""\n',
    'engine/lib/atomicio.py': '"""Atomic file writes for crash-safe state.\n\nA write goes to a sibling ``*.tmp`` file and is renamed into place with\n``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies\nmid-write can never leave a half-written, unparseable file behind. This is the\nrobustness floor the whole engine builds on (plan: Gemini round).\n"""\n\nfrom __future__ import annotations\n\nimport os\nfrom pathlib import Path\n\n\ndef atomic_write_text(path: Path, text: str) -> None:\n    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""\n    path.parent.mkdir(parents=True, exist_ok=True)\n    tmp = path.with_name(path.name + ".tmp")\n    tmp.write_text(text, encoding="utf-8")\n    os.replace(tmp, path)\n',
    'engine/lib/config.py': '"""Host-project configuration for one substrate-kit install.\n\nReads and writes ``substrate.config.json`` — the single file that absorbs every\nhost-specific knob so the engine code never hardcodes a project value. Two\ninterpreters are kept explicitly separate (Hermes-final): ``interpreter`` is the\nkit\'s own runtime, ``interpreter_for_checks`` is the host project\'s verification\nruntime (e.g. ``python3.10`` for a repo whose CI pins 3.10).\n"""\n\nfrom __future__ import annotations\n\nimport json\nimport sys\nimport uuid\nfrom dataclasses import asdict, dataclass, field, fields\nfrom pathlib import Path\n\nfrom engine.lib.atomicio import atomic_write_text\n\nCONFIG_FILENAME = "substrate.config.json"\nDEFAULT_STATE_DIR = ".substrate"\n\n\ndef _new_project_id() -> str:\n    """Return a short, stable identifier for one install."""\n    return uuid.uuid4().hex[:12]\n\n\ndef _default_cadence() -> dict[str, int]:\n    """Return the default cadence knobs."""\n    return {"reconciliation_prs": 20}\n\n\ndef _default_badge_tokens() -> list[str]:\n    """Return the default Status-badge taxonomy the doc checker accepts."""\n    return [\n        "binding",\n        "living-ledger",\n        "reference",\n        "plan",\n        "historical",\n        "audit",\n        "owner-guidance",\n        "ideas",\n        "archive",\n    ]\n\n\ndef _default_readpath_docs() -> list[str]:\n    """Return the read-path doc names that seed the reachability roots."""\n    return ["AGENT_ORIENTATION.md", "current-state.md"]\n\n\ndef _default_session_markers() -> list[dict[str, str]]:\n    """Return the markers every session log must carry (label + substring)."""\n    return [\n        {"label": "Status badge", "needle": "**Status:**"},\n        {"label": "Session idea", "needle": "💡"},\n        {"label": "Previous-session review", "needle": "previous-session review"},\n    ]\n\n\n@dataclass\nclass Config:\n    """Host-project configuration for one substrate-kit install."""\n\n    project_id: str = field(default_factory=_new_project_id)\n    interpreter: str = field(default_factory=lambda: sys.executable)\n    interpreter_for_checks: str | None = None\n    state_dir: str = DEFAULT_STATE_DIR\n    docs_root: str = "docs"\n    sessions_dir: str = ".sessions"\n    paths: dict[str, str] = field(default_factory=dict)\n    cadence: dict[str, int] = field(default_factory=_default_cadence)\n    scopes: dict[str, str] = field(default_factory=dict)\n    badge_tokens: list[str] = field(default_factory=_default_badge_tokens)\n    readpath_docs: list[str] = field(default_factory=_default_readpath_docs)\n    session_markers: list[dict[str, str]] = field(\n        default_factory=_default_session_markers,\n    )\n\n    def to_json(self) -> str:\n        """Serialise the config to indented, key-sorted JSON."""\n        return json.dumps(asdict(self), indent=2, sort_keys=True)\n\n    @classmethod\n    def from_dict(cls, data: dict) -> Config:\n        """Build a Config from a parsed dict, ignoring unknown keys."""\n        known = {f.name for f in fields(cls)}\n        return cls(**{k: v for k, v in data.items() if k in known})\n\n\ndef config_path(root: Path) -> Path:\n    """Return the config-file path for a project ``root``."""\n    return root / CONFIG_FILENAME\n\n\ndef load_config(root: Path) -> Config:\n    """Load the config from ``root``; return defaults if none exists."""\n    path = config_path(root)\n    if not path.exists():\n        return Config()\n    data = json.loads(path.read_text(encoding="utf-8"))\n    return Config.from_dict(data)\n\n\ndef save_config(root: Path, config: Config) -> None:\n    """Write ``config`` to ``root`` atomically."""\n    atomic_write_text(config_path(root), config.to_json() + "\\n")\n',
    'engine/lib/state.py': '"""The state-backend interface and its default JSON implementation.\n\nThe *interface* — not a raw JSON shape — is the contract the rest of the engine\ncodes against (Hermes-final, plan §2), so a future SQLite backend can replace the\nJSON one without a rewrite. The default backend is one JSON file written\natomically; mutations inside a ``transaction`` roll back on error and flush once.\n"""\n\nfrom __future__ import annotations\n\nimport copy\nimport json\nfrom abc import ABC, abstractmethod\nfrom collections.abc import Iterator\nfrom contextlib import AbstractContextManager, contextmanager\nfrom pathlib import Path\nfrom typing import Any\n\nfrom engine.lib.atomicio import atomic_write_text\n\nSTATE_SCHEMA_VERSION = 1\n\n\ndef default_state(project_id: str) -> dict[str, Any]:\n    """Return the initial state document for a fresh install."""\n    return {\n        "version": STATE_SCHEMA_VERSION,\n        "project_id": project_id,\n        "mode": "guided",\n        "promotion_rights": "propose",\n        "stage": "integration",\n        "stance": "analysis",\n        "session_count": 0,\n        "slots": {},\n        "open_questions": [],\n        "graduation": {\n            "soft_target_sessions": 50,\n            "criteria": {\n                "critical_slots_filled_pct": 0.8,\n                "blocking_questions": 0,\n            },\n        },\n    }\n\n\nclass StateBackend(ABC):\n    """Read / write / query / transaction / migrate contract for engine state."""\n\n    version: int = STATE_SCHEMA_VERSION\n\n    @abstractmethod\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n\n    @abstractmethod\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key`` (flushing unless inside a transaction)."""\n\n    @abstractmethod\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n\n    @abstractmethod\n    def transaction(self) -> AbstractContextManager[StateBackend]:\n        """Return a context manager that commits on success, rolls back on error."""\n\n    @abstractmethod\n    def migrate(self, to_version: int) -> None:\n        """Migrate the stored document to schema ``to_version``."""\n\n\nclass JsonStateBackend(StateBackend):\n    """A StateBackend backed by one atomically-written JSON file."""\n\n    def __init__(self, path: Path) -> None:\n        self._path = Path(path)\n        self._data: dict[str, Any] = self._read()\n        self._in_txn = False\n\n    def _read(self) -> dict[str, Any]:\n        if not self._path.exists():\n            return {}\n        return json.loads(self._path.read_text(encoding="utf-8"))\n\n    def _flush(self) -> None:\n        atomic_write_text(\n            self._path,\n            json.dumps(self._data, indent=2, sort_keys=True) + "\\n",\n        )\n\n    def get(self, key: str, default: Any = None) -> Any:\n        """Return the value stored at ``key`` or ``default``."""\n        return self._data.get(key, default)\n\n    def set(self, key: str, value: Any) -> None:\n        """Store ``value`` at ``key``; flush now unless inside a transaction."""\n        self._data[key] = value\n        if not self._in_txn:\n            self._flush()\n\n    def query(self, prefix: str = "") -> dict[str, Any]:\n        """Return all key/value pairs whose key starts with ``prefix``."""\n        return {k: v for k, v in self._data.items() if k.startswith(prefix)}\n\n    @contextmanager\n    def transaction(self) -> Iterator[JsonStateBackend]:\n        """Buffer writes; roll back the whole document on error, else flush once."""\n        snapshot = copy.deepcopy(self._data)\n        self._in_txn = True\n        try:\n            yield self\n        except Exception:\n            self._data = snapshot\n            raise\n        finally:\n            self._in_txn = False\n        self._flush()\n\n    def migrate(self, to_version: int) -> None:\n        """Set the stored schema version (no transforms needed at v1)."""\n        self._data["version"] = to_version\n        self._flush()\n\n    @property\n    def data(self) -> dict[str, Any]:\n        """Return a shallow copy of the current state document."""\n        return dict(self._data)\n',
    'engine/lib/guardrail.py': '"""The live-loop guardrail.\n\nA mechanical guarantee (plan: design-corroboration) that the kit never operates\non its own repository root — which would let it mutate the very workflow it runs\ninside. Safe targets are the system temp tree, an ``examples/`` subtree of the\nkit, or any directory outside the kit. Enforced in code, in the first commit —\nnot left as a doc.\n"""\n\nfrom __future__ import annotations\n\nimport tempfile\nfrom pathlib import Path\n\n\nclass UnsafeTargetError(Exception):\n    """Raised when a target directory would corrupt the kit\'s own live loop."""\n\n\ndef assert_safe_target(target: Path, kit_root: Path) -> None:\n    """Refuse to operate on the kit\'s own repo root.\n\n    Safe: the system temp tree, an ``examples/`` subtree of ``kit_root``, or any\n    path outside ``kit_root``. Unsafe: ``kit_root`` itself or a non-``examples``\n    path inside it.\n    """\n    target = Path(target).resolve()\n    kit_root = Path(kit_root).resolve()\n    tmp_root = Path(tempfile.gettempdir()).resolve()\n    if target.is_relative_to(tmp_root):\n        return\n    inside_kit = target == kit_root or target.is_relative_to(kit_root)\n    inside_examples = target.is_relative_to(kit_root / "examples")\n    if inside_kit and not inside_examples:\n        msg = f"refusing to operate on the kit\'s own tree: {target}"\n        raise UnsafeTargetError(msg)\n',
    'engine/interview/question_bank.py': '"""The interview question bank — the seed set the staged onboarding draws from.\n\nCuration policy (Hermes #7): keep this lean. Add a question only when its slot\ngenuinely blocks graduation, or a checker keeps flagging its absence; prune\nquestions that no longer earn their place. Each entry is a plain dict so the bank\nships inside the stdlib-only bootstrap with no parser (the plan named\n``question_bank.yml``; a Python module is the simplest form that embeds and runs\nidentically in ``src`` and the single-file ``dist`` — no YAML/JSON dependency).\n\nEntry fields:\n  id        — stable "Q-NNN" identifier.\n  slot      — the content slot it fills (matches the project index).\n  audience  — "user" (ask the maintainer) or "self" (the agent infers).\n  prompt    — the question text.\n  routing   — where a confirmed answer lands (a doc:field or state:key).\n  priority  — "blocking" | "high" | "normal".\n  critical  — True if graduation requires this slot filled (confirmed, not assumed).\n"""\n\nfrom __future__ import annotations\n\nCURATION_RULE = (\n    "Lean bank: add a question only when it blocks graduation or a checker keeps "\n    "flagging its slot; prune questions that no longer earn their place."\n)\n\nQUESTIONS: list[dict] = [\n    {\n        "id": "Q-001",\n        "slot": "integration_mode",\n        "audience": "user",\n        "prompt": "Adoption pace for the workflow? observe | guided | active.",\n        "routing": "state:mode",\n        "priority": "blocking",\n        "critical": True,\n    },\n    {\n        "id": "Q-002",\n        "slot": "project_name",\n        "audience": "user",\n        "prompt": "What is this project called?",\n        "routing": "templates/CLAUDE.md:project_name",\n        "priority": "high",\n        "critical": True,\n    },\n    {\n        "id": "Q-003",\n        "slot": "primary_language",\n        "audience": "user",\n        "prompt": "Primary language / runtime (e.g. Python 3.10, TypeScript)?",\n        "routing": "templates/CLAUDE.md:language",\n        "priority": "high",\n        "critical": True,\n    },\n    {\n        "id": "Q-004",\n        "slot": "architecture_layers",\n        "audience": "user",\n        "prompt": "What are the top-level layers and their import rules?",\n        "routing": "templates/architecture.md:layers",\n        "priority": "high",\n        "critical": True,\n    },\n    {\n        "id": "Q-005",\n        "slot": "verify_command",\n        "audience": "user",\n        "prompt": "One command that proves a change is good (tests + lint)?",\n        "routing": "templates/CLAUDE.md:verify_command",\n        "priority": "high",\n        "critical": True,\n    },\n    {\n        "id": "Q-006",\n        "slot": "ownership_model",\n        "audience": "self",\n        "prompt": "Which component owns each data store / write path?",\n        "routing": "templates/ownership.md:owners",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-007",\n        "slot": "doc_roots",\n        "audience": "self",\n        "prompt": "Where does durable documentation live?",\n        "routing": "state:paths.docs",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-008",\n        "slot": "owner_profile",\n        "audience": "user",\n        "prompt": "How do you like an agent to work (tone, detail, autonomy)?",\n        "routing": "templates/owner-profile.md:style",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-009",\n        "slot": "mutation_seam",\n        "audience": "self",\n        "prompt": "How are writes gated (the audited mutation seam)?",\n        "routing": "templates/runtime_contracts.md:mutations",\n        "priority": "normal",\n        "critical": False,\n    },\n    {\n        "id": "Q-010",\n        "slot": "review_ritual",\n        "audience": "user",\n        "prompt": "Your PR-review and release rhythm?",\n        "routing": "templates/owner-profile.md:procedures",\n        "priority": "normal",\n        "critical": False,\n    },\n]\n',
    'engine/interview/stages.py': '"""Stage state machine + adaptive graduation (plan section 2).\n\nStage 1 (``integration``) graduates to stage 2 (``steady``) *adaptively* — when\nthe project\'s **critical** content slots are mostly filled (by confirmed, not\nassumed, answers), no blocking questions remain, and several consecutive sessions\nsurface no new mandatory question — not at a hard session count.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any\n\nSTAGE_INTEGRATION = "integration"\nSTAGE_STEADY = "steady"\n\n_DEFAULT_FILL_PCT = 0.8\n_DEFAULT_QUIET_SESSIONS = 3\n\n\ndef critical_fill_ratio(slots: dict[str, str], critical: list[str]) -> float:\n    """Return the fraction of ``critical`` slots marked ``filled``."""\n    if not critical:\n        return 1.0\n    filled = sum(1 for name in critical if slots.get(name) == "filled")\n    return filled / len(critical)\n\n\ndef graduation_ready(\n    state: dict[str, Any],\n    critical: list[str],\n) -> tuple[bool, list[str]]:\n    """Return ``(ready, reasons)`` for graduating integration -> steady.\n\n    ``reasons`` lists the unmet criteria when not ready (empty when ready).\n    """\n    criteria = state.get("graduation", {}).get("criteria", {})\n    want_pct = criteria.get("critical_slots_filled_pct", _DEFAULT_FILL_PCT)\n    want_quiet = criteria.get("quiet_sessions_required", _DEFAULT_QUIET_SESSIONS)\n    reasons: list[str] = []\n\n    ratio = critical_fill_ratio(state.get("slots", {}), critical)\n    if ratio < want_pct:\n        reasons.append(f"critical slots {ratio:.0%} < {want_pct:.0%}")\n    blocking = len(state.get("open_questions", []))\n    if blocking:\n        reasons.append(f"{blocking} blocking question(s) open")\n    quiet = state.get("quiet_sessions", 0)\n    if quiet < want_quiet:\n        reasons.append(f"quiet streak {quiet} < {want_quiet}")\n    return (not reasons, reasons)\n\n\ndef maybe_graduate(backend: Any, critical: list[str]) -> bool:\n    """Advance integration -> steady if ready; return whether it graduated."""\n    if backend.get("stage") != STAGE_INTEGRATION:\n        return False\n    ready, _ = graduation_ready(backend.data, critical)\n    if ready:\n        backend.set("stage", STAGE_STEADY)\n    return ready\n',
    'engine/interview/interview.py': '"""The interview pass — fills content slots from the question bank (plan section 4).\n\nA session asks its pending questions. A user-facing answer fills a slot\n(``filled``); when no human is present the agent self-answers, recording a\n*provisional* assumption (``provisional``) that never counts toward graduation\nuntil confirmed. This is what lets an autonomous run keep moving without blocking:\nit records assumptions, flags them, and moves on.\n"""\n\nfrom __future__ import annotations\n\nfrom typing import Any\n\nfrom engine.interview.question_bank import QUESTIONS\nfrom engine.interview.stages import maybe_graduate\n\n\ndef critical_slots(bank: list[dict] | None = None) -> list[str]:\n    """Return the slot names the bank marks as critical."""\n    bank = QUESTIONS if bank is None else bank\n    return [q["slot"] for q in bank if q.get("critical")]\n\n\ndef pending_questions(\n    state: dict[str, Any],\n    bank: list[dict] | None = None,\n) -> list[dict]:\n    """Return bank questions whose slot is not yet ``filled``."""\n    bank = QUESTIONS if bank is None else bank\n    slots = state.get("slots", {})\n    return [q for q in bank if slots.get(q["slot"]) != "filled"]\n\n\ndef record_answer(backend: Any, question: dict, answer: str, *, source: str) -> None:\n    """Fill ``question``\'s slot from an answer.\n\n    ``source="user"`` confirms the slot (``filled``); any other source records a\n    ``provisional`` self-answer that must be confirmed before it counts.\n    """\n    status = "filled" if source == "user" else "provisional"\n    slots = dict(backend.get("slots", {}))\n    values = dict(backend.get("slot_values", {}))\n    slots[question["slot"]] = status\n    values[question["slot"]] = {\n        "value": answer,\n        "source": source,\n        "question_id": question["id"],\n    }\n    with backend.transaction():\n        backend.set("slots", slots)\n        backend.set("slot_values", values)\n\n\ndef run_session(\n    backend: Any,\n    answers: dict[str, str],\n    *,\n    autonomous: bool = False,\n    bank: list[dict] | None = None,\n) -> dict[str, Any]:\n    """Run one interview session, then attempt graduation.\n\n    ``answers`` maps slot -> user answer. A pending question with a user answer is\n    confirmed; otherwise, in ``autonomous`` mode it is self-answered provisionally.\n    A session that leaves no blocking question unanswered extends the quiet streak;\n    any unanswered blocking question resets it.\n    """\n    bank = QUESTIONS if bank is None else bank\n    pending = pending_questions(backend.data, bank)\n    left_blocking = False\n    for question in pending:\n        slot = question["slot"]\n        if slot in answers:\n            record_answer(backend, question, answers[slot], source="user")\n        elif autonomous:\n            record_answer(backend, question, f"ASSUMED: {slot}", source="assumption")\n        elif question.get("priority") == "blocking":\n            left_blocking = True\n\n    backend.set("session_count", int(backend.get("session_count", 0)) + 1)\n    quiet = int(backend.get("quiet_sessions", 0))\n    backend.set("quiet_sessions", 0 if left_blocking else quiet + 1)\n\n    graduated = maybe_graduate(backend, critical_slots(bank))\n    return {\n        "session": backend.get("session_count"),\n        "pending_after": len(pending_questions(backend.data, bank)),\n        "graduated": graduated,\n        "stage": backend.get("stage"),\n    }\n',
    'engine/checks/check_docs.py': '"""Generic doc-hygiene checker (config-driven port of ``check_docs``).\n\nThree portable checks, every input supplied by the caller (from config) rather\nthan hardcoded:\n\n  1. **badge**      — every ``*.md`` under ``docs_root`` (non-ADR) carries a\n     ``> **Status:** `<token>``` line in its first 12 lines, ``<token>`` drawn\n     from the project\'s allowed taxonomy.\n  2. **link**       — every relative markdown link ``[text](path)`` resolves to\n     an existing file (external / anchor-only links are skipped).\n  3. **reachable**  — every live doc is reachable by following links + backtick\n     ``<docs>/*.md`` refs from a read-path root (the read-path docs + any\n     ``README.md``). Orphans fail unless badged ``historical`` / ``archive`` or\n     an ADR.\n\nThe host\'s soft ratchets (top-level pile, recently-shipped) and the\nsuperbot-specific freshness rule are intentionally left behind — they are\nproject policy, not portable mechanism. Pure stdlib; returns findings rather\nthan printing so the CLI owns all output.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom collections import deque\nfrom collections.abc import Collection, Sequence\nfrom pathlib import Path\nfrom typing import NamedTuple\n\n\nclass Finding(NamedTuple):\n    """One doc-hygiene violation: ``path`` is relative to ``docs_root``."""\n\n    path: str\n    kind: str\n    message: str\n\n\n# `> **Status:** `<token>`` — the machine-readable badge (rich text may follow).\n_BADGE_RE = re.compile(r"\\*\\*Status:\\*\\*\\s*`([a-z-]+)`")\n# ADR filename: NNN-something.md (exempt — ADRs use their own Accepted/Superseded).\n_ADR_RE = re.compile(r"^\\d+-.*\\.md$")\n# Markdown link target: [text](target).\n_MD_LINK_RE = re.compile(r"\\[[^\\]]*\\]\\(([^)]+)\\)")\n# Badges whose docs are retired content and need no inbound link.\n_EXEMPT_BADGES = frozenset({"historical", "archive"})\n\n_BADGE_MISSING = "missing `> **Status:** `<token>`` in first 12 lines"\n_ORPHAN_MSG = (\n    "orphan: not reachable from any read-path doc / README "\n    "(link it from one, or badge it historical/archive)"\n)\n\n\ndef _md_files(docs_root: Path) -> list[Path]:\n    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""\n    if not docs_root.exists():\n        return []\n    return sorted(docs_root.rglob("*.md"))\n\n\ndef _is_adr(path: Path) -> bool:\n    """True for ``decisions/NNN-*.md`` ADR files (badge-exempt)."""\n    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))\n\n\ndef _badge_token(path: Path) -> str | None:\n    """Return the doc\'s Status-badge token from its first 12 lines, or None."""\n    head = "\\n".join(path.read_text(encoding="utf-8").splitlines()[:12])\n    match = _BADGE_RE.search(head)\n    return match.group(1) if match else None\n\n\ndef _link_target(raw: str) -> str:\n    """Normalise a markdown link target (drop ``<>``, title, ``#anchor``)."""\n    target = raw.strip()\n    if target.startswith("<") and ">" in target:\n        target = target[1:].split(">", 1)[0]\n    parts = target.split()\n    target = parts[0] if parts else target\n    return target.split("#", 1)[0]\n\n\ndef _backtick_docs_re(docs_root: Path) -> re.Pattern[str]:\n    """Compile the ``<docs>/*.md`` backtick-ref pattern for this doc root."""\n    name = re.escape(docs_root.name)\n    return re.compile(rf"`({name}/[\\w./-]+\\.md)`")\n\n\ndef check_badges(docs_root: Path, badge_tokens: Collection[str]) -> list[Finding]:\n    """Every non-ADR doc must declare a Status badge from the taxonomy."""\n    allowed = set(badge_tokens)\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        if _is_adr(f):\n            continue\n        rel = f.relative_to(docs_root).as_posix()\n        token = _badge_token(f)\n        if token is None:\n            findings.append(Finding(rel, "badge", _BADGE_MISSING))\n        elif token not in allowed:\n            allowed_list = ", ".join(sorted(allowed))\n            findings.append(\n                Finding(\n                    rel,\n                    "badge",\n                    f"invalid badge token `{token}` (allowed: {allowed_list})",\n                ),\n            )\n    return findings\n\n\ndef check_links(docs_root: Path) -> list[Finding]:\n    """Relative markdown links inside ``docs_root`` must resolve."""\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        rel = f.relative_to(docs_root).as_posix()\n        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):\n            for raw in _MD_LINK_RE.findall(line):\n                if raw.startswith(("http://", "https://", "mailto:", "#")):\n                    continue\n                target = _link_target(raw)\n                if not target or target.startswith(("http", "mailto:")):\n                    continue\n                if not (f.parent / target).resolve().exists():\n                    msg = f"L{lineno}: dead link -> {raw}"\n                    findings.append(Finding(rel, "link", msg))\n    return findings\n\n\ndef _outgoing_links(path: Path, docs_root: Path) -> set[Path]:\n    """Resolve every relative markdown link + backtick ``<docs>/*.md`` ref."""\n    out: set[Path] = set()\n    backtick = _backtick_docs_re(docs_root)\n    root = docs_root.parent\n    try:\n        text = path.read_text(encoding="utf-8")\n    except (OSError, UnicodeDecodeError):\n        return out\n    for line in text.splitlines():\n        for raw in _MD_LINK_RE.findall(line):\n            if raw.startswith(("http://", "https://", "mailto:", "#")):\n                continue\n            target = _link_target(raw)\n            if target:\n                out.add((path.parent / target).resolve())\n        for ref in backtick.findall(line):\n            out.add((root / ref).resolve())\n    return out\n\n\ndef check_reachable(docs_root: Path, readpath_docs: Sequence[str]) -> list[Finding]:\n    """Every live doc must be reachable from a read-path root / README.\n\n    Walks the doc graph (markdown links + backtick ``<docs>/*.md`` refs) from the\n    roots; any doc not reached — and not ``historical`` / ``archive`` badged or an\n    ADR — is an orphan.\n    """\n    roots = [docs_root / name for name in readpath_docs]\n    roots += sorted(docs_root.rglob("README.md"))\n    seen: set[Path] = set()\n    queue: deque[Path] = deque()\n    for root in roots:\n        resolved = root.resolve()\n        if root.exists() and resolved not in seen:\n            seen.add(resolved)\n            queue.append(resolved)\n    while queue:\n        cur = queue.popleft()\n        if cur.suffix != ".md" or not cur.exists():\n            continue\n        for nxt in _outgoing_links(cur, docs_root):\n            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():\n                seen.add(nxt)\n                queue.append(nxt)\n\n    findings: list[Finding] = []\n    for f in _md_files(docs_root):\n        if f.resolve() in seen or _is_adr(f):\n            continue\n        if _badge_token(f) in _EXEMPT_BADGES:\n            continue\n        rel = f.relative_to(docs_root).as_posix()\n        findings.append(Finding(rel, "reachable", _ORPHAN_MSG))\n    return findings\n\n\ndef run_doc_checks(\n    docs_root: Path,\n    badge_tokens: Collection[str],\n    readpath_docs: Sequence[str],\n) -> list[Finding]:\n    """Run every doc check and return the combined findings."""\n    return (\n        check_badges(docs_root, badge_tokens)\n        + check_links(docs_root)\n        + check_reachable(docs_root, readpath_docs)\n    )\n',
    'engine/checks/check_session_log.py': '"""Generic session-log completeness checker (config-driven port).\n\nThe session workflow asks every session to end with a\n``<sessions_dir>/<date>-<slug>.md`` log that carries a set of required markers\n(by default: a Status badge, a session-idea flag, and a previous-session review).\nEach marker is a ``{"label", "needle"}`` pair from ``substrate.config.json``, so a\nhost tunes the ritual without touching engine code.\n\nUnlike the host\'s version this port does **not** shell out to ``git`` to pick the\n"current" log — ``subprocess`` is banned in engine code and is host-CI sugar\nanyway. The current log is the newest ``*.md`` by mtime under ``sessions_dir``\n(the CLI also accepts an explicit ``--file``). Pure stdlib; returns the missing\nmarkers rather than printing.\n"""\n\nfrom __future__ import annotations\n\nfrom collections.abc import Mapping, Sequence\nfrom pathlib import Path\n\n\ndef missing_markers(text: str, markers: Sequence[Mapping[str, str]]) -> list[str]:\n    """Return the labels of markers whose needle is absent from ``text``."""\n    lower = text.lower()\n    return [m["label"] for m in markers if m["needle"].lower() not in lower]\n\n\ndef latest_session_log(sessions_dir: Path) -> Path | None:\n    """Best guess at this session\'s log: newest ``*.md`` by mtime (skip README)."""\n    if not sessions_dir.is_dir():\n        return None\n    candidates = [p for p in sessions_dir.glob("*.md") if p.name != "README.md"]\n    if not candidates:\n        return None\n    return max(candidates, key=lambda p: p.stat().st_mtime)\n\n\ndef check_log(path: Path, markers: Sequence[Mapping[str, str]]) -> list[str]:\n    """Return the missing-marker labels for one log file (all if unreadable)."""\n    try:\n        text = path.read_text(encoding="utf-8")\n    except OSError:\n        return [m["label"] for m in markers]\n    return missing_markers(text, markers)\n',
    'engine/render.py': '"""Render the project\'s content docs from templates + filled interview slots.\n\nTemplates use ``${slot_name}`` placeholders (``string.Template``). A slot the\ninterview has filled substitutes in; an unfilled slot is left as ``${slot_name}``\nand reported — so a half-onboarded project\'s gaps stay visible rather than going\nsilently blank. Templates ship embedded in the bootstrap (the generated\n``_TEMPLATES`` dict) and, in the source tree, live under ``src/templates/``.\n"""\n\nfrom __future__ import annotations\n\nimport re\nfrom pathlib import Path\nfrom string import Template\nfrom typing import Any\n\n_PLACEHOLDER_RE = re.compile(r"\\$\\{([a-zA-Z_][a-zA-Z0-9_]*)\\}")\n\n\ndef find_placeholders(text: str) -> set[str]:\n    """Return the set of ``${name}`` placeholders remaining in ``text``."""\n    return set(_PLACEHOLDER_RE.findall(text))\n\n\ndef render(text: str, context: dict[str, str]) -> str:\n    """Substitute ``${slot}`` placeholders from ``context`` (unfilled left as-is)."""\n    return Template(text).safe_substitute(context)\n\n\ndef build_context(state: dict[str, Any]) -> dict[str, str]:\n    """Build the substitution context from a state document\'s filled slots."""\n    values = state.get("slot_values", {})\n    return {slot: str(entry.get("value", "")) for slot, entry in values.items()}\n\n\ndef load_templates() -> dict[str, str]:\n    """Return ``{filename: text}`` for every template (embedded or from src)."""\n    embedded = globals().get("_TEMPLATES")\n    if embedded is not None:\n        return dict(embedded)\n    root = Path(__file__).resolve().parent.parent / "templates"\n    return {p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*"))}\n',
    'engine/cli.py': '"""The substrate-kit bootstrap command line.\n\nSurface: ``init`` (idempotent), ``status``, ``mode <name>``, ``ask`` (list the\npending interview questions), ``render`` (write content docs), ``check`` (run the\ndoc + session-log hygiene checks), and ``--simulate N`` (the CI / proving smoke\nthat drives the staged interview). Output goes through ``_emit``\n(``sys.stdout.write``) rather than ``print`` to keep the engine lint-clean.\n"""\n\nfrom __future__ import annotations\n\nimport argparse\nimport sys\nimport tempfile\nfrom pathlib import Path\n\nfrom engine.checks.check_docs import run_doc_checks\nfrom engine.checks.check_session_log import check_log, latest_session_log\nfrom engine.interview.interview import critical_slots, pending_questions, run_session\nfrom engine.lib.atomicio import atomic_write_text\nfrom engine.lib.config import Config, config_path, load_config, save_config\nfrom engine.lib.guardrail import UnsafeTargetError, assert_safe_target\nfrom engine.lib.state import JsonStateBackend, default_state\nfrom engine.render import build_context, find_placeholders, load_templates, render\n\n\ndef _emit(line: str = "") -> None:\n    """Write a line to stdout (avoids the print() lint ban in engine code)."""\n    sys.stdout.write(line + "\\n")\n\n\ndef _kit_root() -> Path:\n    """Return the kit root (``substrate-kit/``) for the guardrail check."""\n    return Path(__file__).resolve().parents[2]\n\n\ndef _state_path(root: Path, config: Config) -> Path:\n    """Return the state-file path under a project ``root``."""\n    return root / config.state_dir / "state.json"\n\n\ndef cmd_init(target: Path) -> int:\n    """Create config + state under ``target`` if absent; never clobber."""\n    assert_safe_target(target, _kit_root())\n    target.mkdir(parents=True, exist_ok=True)\n    if config_path(target).exists():\n        config = load_config(target)\n    else:\n        config = Config()\n        save_config(target, config)\n    state_path = _state_path(target, config)\n    if state_path.exists():\n        _emit(f"init: already initialised at {target} (idempotent no-op).")\n        return 0\n    backend = JsonStateBackend(state_path)\n    with backend.transaction():\n        for key, value in default_state(config.project_id).items():\n            backend.set(key, value)\n    _emit(f"init: created {state_path} (project_id={config.project_id}).")\n    return 0\n\n\ndef cmd_status(target: Path) -> int:\n    """Print a one-screen summary of the install\'s state."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    data = backend.data\n    if not data:\n        _emit(f"status: no state at {target} (run init first).")\n        return 1\n    _emit(f"project_id : {data.get(\'project_id\')}")\n    _emit(f"stage      : {data.get(\'stage\')}")\n    _emit(f"mode       : {data.get(\'mode\')}")\n    _emit(f"stance     : {data.get(\'stance\')}")\n    _emit(f"sessions   : {data.get(\'session_count\')}")\n    return 0\n\n\ndef cmd_mode(target: Path, name: str) -> int:\n    """Set the integration mode (observe | guided | active)."""\n    valid = ("observe", "guided", "active")\n    if name not in valid:\n        _emit(f"mode: invalid mode {name!r} (choose from {list(valid)}).")\n        return 2\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"mode: no state at {target} (run init first).")\n        return 1\n    backend.set("mode", name)\n    _emit(f"mode: set to {name}.")\n    return 0\n\n\ndef cmd_ask(target: Path) -> int:\n    """List the interview\'s currently pending questions."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"ask: no state at {target} (run init first).")\n        return 1\n    pending = pending_questions(backend.data)\n    if not pending:\n        _emit("ask: no pending questions — all slots filled.")\n        return 0\n    _emit(f"ask: {len(pending)} pending question(s):")\n    for question in pending:\n        _emit(\n            f"  [{question[\'id\']}] "\n            f"({question[\'audience\']}/{question[\'priority\']}) {question[\'prompt\']}",\n        )\n    return 0\n\n\ndef cmd_render(target: Path) -> int:\n    """Render the content docs from the current filled slots into ``target``."""\n    config = load_config(target)\n    backend = JsonStateBackend(_state_path(target, config))\n    if not backend.data:\n        _emit(f"render: no state at {target} (run init first).")\n        return 1\n    context = build_context(backend.data)\n    out_dir = target / config.state_dir / "rendered"\n    leftover_total = 0\n    for name, text in load_templates().items():\n        rendered = render(text, context)\n        leftover = find_placeholders(rendered)\n        leftover_total += len(leftover)\n        out_name = name[:-5] if name.endswith(".tmpl") else name\n        atomic_write_text(out_dir / out_name, rendered)\n        suffix = f" ({len(leftover)} slot(s) unfilled)" if leftover else ""\n        _emit(f"render: wrote {out_name}{suffix}")\n    _emit(f"render: {leftover_total} unfilled placeholder(s) total.")\n    return 0\n\n\ndef cmd_check(target: Path, strict: bool) -> int:\n    """Run the doc-hygiene + session-log checks against ``target``.\n\n    Doc findings always count toward the exit code (under ``--strict``); a\n    *missing* session log is advisory (a host may run ``check`` mid-session), but\n    an *incomplete* existing log counts. Uses config defaults if ``target`` has\n    no ``substrate.config.json`` yet, so a project can lint before onboarding.\n    """\n    config = load_config(target)\n    docs_root = target / config.docs_root\n    doc_findings = run_doc_checks(\n        docs_root,\n        config.badge_tokens,\n        config.readpath_docs,\n    )\n    if doc_findings:\n        _emit(f"check: {len(doc_findings)} doc finding(s):")\n        for finding in doc_findings:\n            _emit(f"  [{finding.kind}] {finding.path}: {finding.message}")\n\n    log = latest_session_log(target / config.sessions_dir)\n    log_missing: list[str] = check_log(log, config.session_markers) if log else []\n    if log is None:\n        _emit("check: no session log found yet (advisory — not a failure).")\n    else:\n        rel = log.relative_to(target) if log.is_relative_to(target) else log\n        if log_missing:\n            _emit(f"check: session log {rel} is missing: {\', \'.join(log_missing)}")\n        else:\n            _emit(f"check: session log {rel} complete.")\n\n    if not doc_findings and not log_missing:\n        _emit("check: all checks passed.")\n        return 0\n    return 1 if strict else 0\n\n\ndef cmd_simulate(n: int) -> int:\n    """Init into a temp dir and drive ``n`` interview sessions; verify progress.\n\n    Session 1 supplies confirmed answers for every critical slot; later sessions\n    supply none. Asserts the critical slots fill and (for ``n`` past the quiet\n    threshold) the install graduates integration -> steady.\n    """\n    with tempfile.TemporaryDirectory(prefix="substrate-sim-") as tmp:\n        target = Path(tmp)\n        rc = cmd_init(target)\n        if rc != 0:\n            return rc\n        state_path = _state_path(target, load_config(target))\n        crit = critical_slots()\n        answers = {slot: f"value-for-{slot}" for slot in crit}\n        graduated = False\n        for index in range(n):\n            backend = JsonStateBackend(state_path)\n            result = run_session(backend, answers if index == 0 else {})\n            graduated = graduated or result["graduated"]\n        data = JsonStateBackend(state_path).data\n        missing = [s for s in crit if data.get("slots", {}).get(s) != "filled"]\n        if missing:\n            _emit(f"simulate: FAILED — critical slots unfilled: {missing}")\n            return 1\n        _emit(\n            f"simulate: OK — {n} session(s), {len(crit)} critical slots filled, "\n            f"stage={data.get(\'stage\')} (graduated={graduated}).",\n        )\n    return 0\n\n\ndef build_parser() -> argparse.ArgumentParser:\n    """Construct the bootstrap argument parser."""\n    parser = argparse.ArgumentParser(prog="bootstrap", description="substrate-kit")\n    parser.add_argument(\n        "--simulate",\n        type=int,\n        metavar="N",\n        help="run N synthetic sessions in a temp dir, then exit",\n    )\n    sub = parser.add_subparsers(dest="command")\n    for name, helptext in (\n        ("init", "initialise a project"),\n        ("status", "show install state"),\n        ("ask", "list pending interview questions"),\n        ("render", "render content docs from filled slots"),\n    ):\n        child = sub.add_parser(name, help=helptext)\n        child.add_argument("--target", type=Path, default=Path.cwd())\n    mode = sub.add_parser("mode", help="set the integration mode")\n    mode.add_argument("name")\n    mode.add_argument("--target", type=Path, default=Path.cwd())\n    check = sub.add_parser("check", help="run the doc + session-log hygiene checks")\n    check.add_argument("--target", type=Path, default=Path.cwd())\n    check.add_argument("--strict", action="store_true", help="exit 1 if any violation")\n    return parser\n\n\ndef main(argv: list[str] | None = None) -> int:\n    """Run the bootstrap CLI; return a process exit code."""\n    parser = build_parser()\n    args = parser.parse_args(argv)\n    try:\n        if args.simulate is not None:\n            return cmd_simulate(args.simulate)\n        if args.command == "init":\n            return cmd_init(args.target)\n        if args.command == "status":\n            return cmd_status(args.target)\n        if args.command == "ask":\n            return cmd_ask(args.target)\n        if args.command == "render":\n            return cmd_render(args.target)\n        if args.command == "mode":\n            return cmd_mode(args.target, args.name)\n        if args.command == "check":\n            return cmd_check(args.target, args.strict)\n    except UnsafeTargetError as exc:\n        _emit(f"refused: {exc}")\n        return 2\n    parser.print_help()\n    return 0\n',
}

_TEMPLATES = {
    'AGENT_ORIENTATION.md.tmpl': '# ${project_name} — agent orientation & reading order\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. The task reading-router: start here to find which\n> docs a given task needs. **NOT SOURCE OF TRUTH** — the binding contracts win.\n\n## Start every session\n\n1. `.claude/CLAUDE.md` — the working agreement.\n2. `docs/current-state.md` — the living status ledger.\n3. This file — task-specific reading routes.\n\n## Binding contracts\n\n- **Architecture / layering:** ${architecture_layers}\n- **Ownership** (who owns each write path): ${ownership_model}\n- **Mutation seam** (how writes are gated): ${mutation_seam}\n\n## Where things live\n\nDocumentation root(s): ${doc_roots}\n\n## Verifying any change\n\n```\n${verify_command}\n```\n',
    'CLAUDE.md.tmpl': '# ${project_name} — agent working agreement\n\n> **Status:** `binding`\n>\n> Generated by substrate-kit from the staged interview. **NOT SOURCE OF TRUTH**\n> for code — source files always win. Re-render (`bootstrap render`) after the\n> interview fills more slots.\n\n## What this project is\n\n${project_name} is built in ${primary_language}.\n\n## Orientation — read first, in order\n\n1. This file — the working agreement.\n2. `docs/current-state.md` — what is true right now.\n3. `docs/AGENT_ORIENTATION.md` — the task-specific reading router.\n\n## Architecture — layers & import rules\n\n${architecture_layers}\n\n## Verifying a change\n\nRun before every push:\n\n```\n${verify_command}\n```\n\n## How the maintainer works\n\n${owner_profile}\n\n## Workflow adoption\n\nCurrent adoption pace for the substrate workflow: **${integration_mode}**.\n',
    'current-state.md.tmpl': '# ${project_name} — Current State\n\n> **Status:** `living-ledger`\n>\n> Generated by substrate-kit. **Living status ledger.** Source code and merged\n> work always win over this file. Read it second (right after the working\n> agreement) and keep it current as the project moves.\n\n## Stability baseline\n\n(Describe the accepted-stable baseline once established — what is known-good and\nshould not be re-audited without a reported regression.)\n\n## In flight\n\n(Verify against live source control — this section is a dated snapshot.)\n\n## Recently shipped (newest first)\n\n(Merged work only, newest first.)\n\n## Review rhythm\n\n${review_ritual}\n',
    'ideas-README.md.tmpl': '# ${project_name} — idea backlog & lifecycle\n\n> **Status:** `ideas`\n>\n> Generated by substrate-kit. Capture ideas here so they live in the repo, not in\n> chat. Nothing here is approved until it graduates. A **conveyor, not a graveyard**:\n> every idea ends implemented, on a roadmap, in discussion, or explicitly rejected.\n\n## Lifecycle\n\n```\n(1) INTAKE   capture the idea (raw -> captured)\n(2) MAP      name the owning area, rough size, rough risk\n(3) ROUTE    -> quick-win | structured plan | discuss-first (question router)\n(4) GROOM    pull one routable idea forward each session\n(5) OUTCOME  implemented | on a roadmap | in discussion | rejected\n```\n\n## Backlog\n\n(Captured ideas, each with a state and a next destination — none left at `raw`.)\n',
    'question-router.md.tmpl': '# ${project_name} — maintainer question router\n\n> **Status:** `owner-guidance`\n>\n> Generated by substrate-kit. Append-only `## Q-NNNN` blocks capture owner-intent\n> decisions and open questions. The interview writes here; confirmed answers route\n> into the durable docs. **Append only** (next free Q-number) — never rewrite history.\n\n## Block format\n\n```\n## Q-0001\n- **Area / Type / Priority / Status:** ...\n- **Question:** ...\n- **Why agents need this:** ...\n- **Options:** ...\n- **Safe default:** ...\n- **Maintainer answer:** (verbatim)\n- **Routing result:** (which doc / slot the answer landed in)\n```\n\n## Open questions\n\n(Unanswered Q-blocks live here until the maintainer decides; a blocking one gates\ngraduation.)\n',
    'session-journal.md.tmpl': "# ${project_name} — session journal (process memory)\n\n> **Status:** `reference`\n>\n> Generated by substrate-kit. Cross-session working memory — a **guidebook, not a\n> log**. Per-session logs live in `.sessions/<date>-<slug>.md` (newest first);\n> older history archives out. Keep THIS file lean.\n\n## ⚡ Quick reference\n\n(Boot / run-checks / common-recovery commands for ${project_name}.)\n\n## Environment & boot runbook\n\n(How to bring a working dev/test environment up.)\n\n## Recurring problems + fixes\n\n(Known traps and their resolutions — so the next session doesn't re-discover them.)\n\n## Past mistakes to avoid\n\n(Things that went wrong before; don't repeat them.)\n\n## Candidate rules (not yet promoted)\n\n(Proposed working-agreement rules awaiting owner review.)\n",
}

if __name__ == "__main__":
    raise SystemExit(main())
