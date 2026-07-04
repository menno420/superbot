# Strand 1 · Kernel spine · ⑩ The ops kernel — config · DB seam · migrations · metrics · readiness · the data-plane rail

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **Phase-B design spec.** Buildable-depth. Design INTO the frozen design-spec
> (`docs/planning/rebuild-design-spec-2026-07-02.md`) §§4.4, 5.1, 5.2, 6, 10.2, 10.3 and the frozen
> router answers Q-0219…Q-0237. It owns the operational-substrate contracts every other kernel spec
> consumes: the config/secret grammar + boot-preflight, the DB-adapter posture, the migration
> integrity gate, `MetricSpec`, the readiness/drain contract, the **4th data-plane rail**, and the
> **idempotency-key contract** (T2-2 seed).
>
> **Anti-pad note.** The design spec already fixes: metrics relocate to `kernel/observability`
> (decision 7, §8), config is "one typed object validated before connect" (audit A §6.2 R3),
> `off_until_opt_in`/`on_when_keyed` activation grammar (§4.4), fresh chain `0001` + importer (§5.2),
> single-process is a non-goal (T2-13), rulesets/OIDC control plane (§6). This spec does **not**
> restate those — it shapes the eight *undesigned* contracts underneath them and states its seams so
> the seam-consistency pass can verify agreement.
>
> **Closure note (design-closer pass, 2026-07-04).** This revision folds in the adversarial-completeness
> findings: it fixes the Config accessor model to one consistent attribute-per-field shape (§3.2), makes
> `DBUnavailable` a `ConnectionError` subclass so it routes through spec 02 §3.3's *existing* transient
> row with no seam edit (§3.4/§3.9), adds the idempotency `record_outcome`/`read_outcome` write/read
> surfaces and the `db.transaction()` seam that makes `once()` atomic (§3.4/§3.7), shapes `LabelSpec` and
> its cardinality input (§3.3), declares every new operational env var as a `ConfigSpec` incl. a `CSV`
> collection type (§3.1/§3.5), calls out the `/ready` STARTING 200→503 **semantics change** explicitly
> (§3.8/§10), and names the `/metrics` mount point (§3.3/§2/§11). All dispatch/outcome shapes design
> INTO the frozen §2.7 outcome vocab built on the **real** shipped seams — lifecycle
> `contracts.py` (`LifecycleResult`, `StepResult`, outcome constants `SUCCESS/PARTIAL/BLOCKED/DECLINED/
> DISCORD_FAILED` :48-52, reversibility :40-42) and the dispatch analogue `StageResult`
> (`disbot/core/runtime/message_pipeline.py:181`) — **not** any `WorkflowResult`/`disbot/core/contracts.py`
> name (that name is design-spec-only; the shipped seams above are canonical, Q-0120).

---

## 1. Summary + the exact undesigned gap

The design spec names the ops substrate everywhere and shapes it nowhere. Verified today (spot-checked
against shipped source this session):

| Surface | Shipped state (verified) | Cite |
|---|---|---|
| Config/secrets | Flat module of **39 distinct `os.getenv` calls across ~20 modules**; only the token is fail-fast (`ValueError` at import); DSN validated lazily inside `db.init`; **three incompatible boolean grammars** live at once | `config.py` (whole); `pool.py:40-46`; grammar variants below |
| DB pool | `create_pool(min_size=2, max_size=10, init=…)` — **no `command_timeout`, no checkout liveness check** | `pool.py:58-63` |
| Migrations | `schema_migrations(version, applied_at, description)` — **no checksum**; numbering validated only at runtime + a pytest structural test; the "never edit an applied migration" rule is docstring exhortation | `migrations.py:136-143`, `:27-28`; `tests/unit/db/test_migrations_structure.py` |
| Metrics | **46 hand-authored** module-level singletons; no cardinality budget; misfiled in `services/` | `metrics.py` (46 confirmed) |
| Readiness | `/ready` reads gateway + lifecycle phase — **DB-blind**; STARTING⇒200 today (`can_accept_commands()`={STARTING,RUNNING}); nothing declares who probes it | `healthserver.py:92-139`, `lifecycle.py:63` |
| Data plane | `_get_dsn()` opens **whatever `DATABASE_URL` points at** — zero test/prod rail | `pool.py:40-46` |
| Deploy handoff | #1693 stopgap gates the message-pipeline listener only; prefix/interaction/non-message lanes still double-fire on overlap; **no idempotency key anywhere** | FJ L-6, L-9 |

**The gap this spec closes (nothing else designs it):** the *grammar and boot-order* that turns those
seven ad-hoc surfaces into declared, checker-enforced contracts — `ConfigSpec`/`SecretSpec` + a
boot-preflight that runs **before gateway connect**, the DB-down **refuse-with-notice** adapter
posture, `command_timeout` + validate-or-reacquire, the migration **checksum + immutability CI gate**,
`MetricSpec`, the **readiness/drain state table**, the **4th kernel rail** (non-`test` DSN ⇒ refuse
boot), and the **canonical idempotency-key shape** that strand-2's outbox + scheduler consume.

Boolean-grammar evidence (three live grammars — the canonical one below subsumes all three):

```
AI_ENABLED               os.getenv(...).strip().lower() in {"1","true","yes","on"}   # config.py:202
BTD6_INGESTION_ENABLED   os.getenv(...,"false").lower() == "true"                     # ..._supervisor.py:32
BTD6_AUTO_SEED / AUTO_SYNC_COMMANDS   raw "1"/"0" string passed downstream unparsed   # config.py:241,249
```

---

## 2. Files / modules it becomes

New `sb/` paths (K-band in brackets; §11 sequences them):

| New path | Role |
|---|---|
| `sb/spec/config.py` [K2-grammar, importable from K0] | `ConfigSpec`, `SecretSpec`, `ConfigPosture`, `ConfigType` (incl. `CSV`), `IntentSpec`, `DataPlane` frozen dataclasses + the **canonical config registry** (`CONFIG_FIELDS`) — the 39 harvested env vars **+ 8 new operational fields** declared here (47 total) |
| `sb/spec/observability.py` [K0] | `MetricSpec`, `MetricKind`, `LabelSpec` |
| `sb/kernel/config/__init__.py` [K0] | `parse_bool`, `load_config() -> Config`, `preflight() -> Config`, the frozen `Config` accessor object (one typed attribute per field, verbatim env name; redacted fields hidden from repr/diagnostics) |
| `sb/kernel/observability/metrics.py` [K0] | `build_registry(specs) -> MetricRegistry`, the no-op fallback, `render()` (Prometheus exposition) |
| `sb/kernel/db/pool.py` [K3] | pool with `command_timeout` + `checked_acquire()` (validate-or-reacquire) + `transaction()` (the txn seam); `DBUnavailable`; the refuse-with-notice CRUD wrappers |
| `sb/kernel/db/migrations.py` [K3] | fresh-chain runner (`0001+`) with **checksum verify** + `MigrationDrift` |
| `sb/kernel/db/data_plane.py` [K3] | `assert_data_plane()` — the 4th rail |
| `sb/kernel/db/idempotency.py` [K3] | `IdempotencyKey`, `PriorOutcome`, `idempotency_keys` store, `once()` guard + `record_outcome()`/`read_outcome()` (T2-2 seed) |
| `sb/adapters/http/health.py` [K5] | ported health server; `/ready` made DB-aware; **`/metrics` exposition route**; readiness/drain contract |
| `tools/check_migrations.py` [K3, CI gate] | numbering + immutability + checksum-manifest gate |
| `tools/check_config_usage.py` [K0, CI gate] | bans scattered `os.getenv` outside `sb/kernel/config/` |
| `tools/check_metric_cardinality.py` [K0, CI gate] | label-cardinality budget over `MetricSpec` |

Shipped paths it **retires**: `disbot/config.py` (flat env module → grammar + registry),
`disbot/utils/db/pool.py`, `disbot/utils/db/migrations.py`, `disbot/services/metrics.py`
(→ `kernel/observability`, decision 7), `disbot/healthserver.py` (→ `adapters/http`).

---

## 3. The complete public contract

### 3.1 Config / secret grammar — `sb/spec/config.py`

All fields are **[S]** (config declarations are semantic — hand-authored meaning; no [A]/[O] fields).

```python
class ConfigPosture(StrEnum):        # what happens when a required value is absent/invalid
    FAIL_FAST = "fail_fast"          # refuse boot → FAILED_STARTUP (token, DSN, data-plane)
    DEGRADE   = "degrade"            # feature runs reduced (paragon→local estimate; youtube→key_missing)
    DORMANT   = "dormant"            # feature entirely inert, no error (control-api, AI keys)

class ConfigType(StrEnum):
    STR = "str"; INT = "int"; FLOAT = "float"; BOOL = "bool"
    SECRET = "secret"; DSN = "dsn"
    CSV = "csv"                      # comma-split → tuple[str, ...]; empty/absent ⇒ () (host allowlists)

@dataclass(frozen=True)
class ConfigSpec:
    env_var: str                     # [S] exact env name, verbatim; ALSO the Config attribute name (§3.2)
    type: ConfigType                 # [S]
    required: bool                   # [S] True ⇒ no default; absence triggers `posture`
    default: object | None = None    # [S] present iff required=False; type-consistent (CSV default = ())
    posture: ConfigPosture = ConfigPosture.FAIL_FAST   # [S] only consulted when required & absent/invalid
    owner_subsystem: str | None = None # [S] provenance for generated docs (AI keys→ai, btd6→btd6, ops→ops)
    activation_link: str | None = None # [S] SettingSpec.activation this key drives (§4.4 on_when_keyed)
    choices: tuple[str, ...] = ()    # [S] closed set (SETUP_ADVISOR_PROVIDER ∈ {deterministic,openai,anthropic})
    min: float | None = None         # [S] numeric floor (timeouts, intervals)
    redact: bool = False             # [S] never appears in logs/diagnostics (True for SECRET and DSN)

@dataclass(frozen=True)
class SecretSpec(ConfigSpec):
    # SecretSpec := ConfigSpec with type=SECRET, redact=True enforced by __post_init__;
    # a secret is NEVER logged, NEVER surfaced in /lifecycle or diagnostics, only its
    # presence/absence ("configured": bool) is observable (Config.is_configured, §3.2).
    ...

@dataclass(frozen=True)
class IntentSpec:                    # gateway-intent contract (T2-22 / L-17)
    name: str                        # [S] "message_content" | "members" | "presences" | …
    privileged: bool                 # [S] True for message_content/members/presences
    required: bool                   # [S] the bot cannot function without it
    approval_env: str | None = None  # [S] the BOOL ConfigSpec env asserting Discord approval was granted
                                     #     (parsed via parse_bool, §3.2 — a "truthy" grammar, not presence)

class DataPlane(StrEnum):
    TEST = "test"; PROD = "prod"

# The canonical registry — the ONE place every env var is declared.
# 39 entries harvested from shipped source + 8 new operational fields declared here = 47 total.
CONFIG_FIELDS: tuple[ConfigSpec, ...] = (
    # ---- harvested (39) — verbatim env names, each with type/required/default/posture ----
    SecretSpec("DISCORD_BOT_TOKEN_PRODUCTION", ConfigType.SECRET, required=True,  posture=FAIL_FAST),
    ConfigSpec("DATABASE_URL",                 ConfigType.DSN,    required=True,  posture=FAIL_FAST,
               redact=True),                                       # DSN carries creds ⇒ redact
    ConfigSpec("SB_DATA_PLANE",                ConfigType.STR,    required=True,  posture=FAIL_FAST,
               choices=("test","prod")),                          # NEW — the 4th rail's declaration
    ConfigSpec("BOT_PREFIX",                   ConfigType.STR,    required=False, default="!"),
    ConfigSpec("AI_ENABLED",                   ConfigType.BOOL,   required=False, default=False,
               posture=DORMANT, activation_link="ai.*"),
    SecretSpec("ANTHROPIC_API_KEY",            ConfigType.SECRET, required=False, default=None,
               posture=DORMANT, owner_subsystem="ai", activation_link="ai.on_when_keyed"),
    # … the remaining 33 harvested, each declared with type/required/default/posture, verbatim env names …

    # ---- NEW operational fields (8) declared by THIS spec (NOT among the 39 harvested) ----
    ConfigSpec("DB_COMMAND_TIMEOUT_S",   ConfigType.FLOAT, required=False, default=30.0,  min=1.0,
               owner_subsystem="ops"),   # §3.4 — bounds a wedged query
    ConfigSpec("DB_IDLE_LIFETIME_S",     ConfigType.FLOAT, required=False, default=300.0, min=0.0,
               owner_subsystem="ops"),   # §3.4 — max_inactive_connection_lifetime (recycle stale conns)
    ConfigSpec("SB_TEST_DB_HOSTS",       ConfigType.CSV,   required=False, default=(),
               owner_subsystem="ops"),   # §3.5 — test-plane DSN host allowlist (comma-split)
    SecretSpec("SB_PROD_ATTEST",         ConfigType.SECRET, required=False, default=None,
               owner_subsystem="ops"),   # §3.5 — opaque human-set prod token; PRESENCE ⇒ attested
    ConfigSpec("RAILWAY_SERVICE_NAME",   ConfigType.STR,   required=False, default=None,
               owner_subsystem="ops"),   # §3.5 — Railway-injected service name ('worker' in prod)
    ConfigSpec("SB_INTENT_MSGCONTENT_OK", ConfigType.BOOL, required=False, default=False,
               owner_subsystem="ops"),   # §3.2 — approval_env for message_content (parse_bool grammar)
    ConfigSpec("SB_INTENT_MEMBERS_OK",    ConfigType.BOOL, required=False, default=False,
               owner_subsystem="ops"),   # §3.2 — approval_env for members
)

INTENT_CONTRACT: tuple[IntentSpec, ...] = (
    IntentSpec("message_content", privileged=True, required=True, approval_env="SB_INTENT_MSGCONTENT_OK"),
    IntentSpec("members",         privileged=True, required=True, approval_env="SB_INTENT_MEMBERS_OK"),
)   # the two hardcoded privileged intents in shipped source (bot1.py:77-78, verified this session)
```

### 3.2 The boot-preflight + loaded object — `sb/kernel/config/__init__.py`

**The one accessor model (was two — now reconciled).** `Config` exposes **one typed, frozen attribute
per `ConfigSpec`, named verbatim by `env_var`** (env names are valid Python identifiers: uppercase,
underscores, no leading digit). The coerced Python type is fixed by `ConfigType`:
`STR→str`, `INT→int`, `FLOAT→float`, `BOOL→bool`, `CSV→tuple[str, ...]`, `DSN→str` (redacted),
`SECRET→str | None` (redacted). So `cfg.DATABASE_URL`, `cfg.DB_COMMAND_TIMEOUT_S`, `cfg.DB_IDLE_LIFETIME_S`,
`cfg.SB_TEST_DB_HOSTS`, `cfg.SB_PROD_ATTEST`, `cfg.RAILWAY_SERVICE_NAME` are all typed attributes — the
usages in §3.4/§3.5 are exactly this model. There is **no `.get(spec)` accessor and no sibling `Secrets`
object**; redaction is a *field property* (`redact=True` for every SECRET and DSN), enforced by `Config`'s
`__repr__`/diagnostic serialization, which omit redacted attribute values and expose only presence via
`is_configured()`. Tooling that must iterate (generated `docs/ownership.md` env section) uses
`iter_fields()`.

```python
_TRUTHY = {"1","true","yes","on","y","t"}
_FALSY  = {"","0","false","no","off","n","f"}

def parse_bool(raw: str, *, env_var: str) -> bool:
    """THE one boolean grammar. Case-insensitive after strip. Unknown token ⇒ ConfigError.
    Subsumes all three shipped grammars: every value they accepted maps identically here."""
    v = raw.strip().lower()
    if v in _TRUTHY: return True
    if v in _FALSY:  return False
    raise ConfigError(env_var, f"not a boolean: {raw!r} (use one of {sorted(_TRUTHY | _FALSY)})")

def parse_dsn(raw: str, *, env_var: str) -> str:
    """DSN SHAPE validation (the preflight DSN coercion). urlsplit(raw) must yield
    scheme ∈ {postgres, postgresql}, a non-empty host, and a non-empty path (db name);
    otherwise ConfigError. Does NOT connect — connection is db.init's job (§3.4).
    Returns the raw DSN string unchanged on success."""

class ConfigError(Exception):
    """One field failed to coerce/validate. Carries env_var + reason; aggregated by preflight."""

class StartupError(Exception):
    """Preflight aggregate — a LIST of ConfigError, raised once. The composition root maps this to
    the lifecycle FAILED_STARTUP phase (12.1-factor: coerce+validate ALL env at boot, never lazily
    deep in a request)."""
    errors: tuple[ConfigError, ...]

@dataclass(frozen=True)
class Config:
    """The one typed, validated, frozen config object. Replaces every `config.X` / scattered getenv.
    ONE attribute per ConfigSpec, named verbatim by env_var (e.g. `cfg.DATABASE_URL`). Redacted fields
    (SECRET, DSN) hold the real value (needed to connect) but never appear in repr/diagnostics."""
    def is_configured(self, env_var: str) -> bool: ...     # presence of a (possibly-redacted) field
    def iter_fields(self) -> Iterable[tuple[ConfigSpec, object]]: ...   # tooling / doc generation
    @property
    def data_plane(self) -> DataPlane: ...                 # derived convenience: DataPlane(cfg.SB_DATA_PLANE)

def preflight(env: Mapping[str, str] = os.environ) -> Config:
    """Runs FIRST in the composition root, BEFORE gateway connect and BEFORE the manifest compiler
    boot_gate legs. For every ConfigSpec in CONFIG_FIELDS:
      1. read env_var; if absent and required → apply posture (FAIL_FAST accrues a ConfigError;
         DEGRADE/DORMANT record 'inactive' and continue); if absent and not required → use default;
      2. coerce by type (parse_bool for BOOL, int()/float() with `min`, choices membership,
         parse_dsn for DSN, comma-split for CSV);
      3. any coercion failure accrues a ConfigError.
    Then: assert_data_plane() (§3.5) and assert_intents() (below).
    On any accrued error → raise StartupError(errors). On success → return frozen Config
    (one attribute per field)."""

def assert_intents(cfg: Config) -> None:
    """For each required IntentSpec: the intent is enabled in code AND, when privileged, its
    approval_env BOOL field is truthy (parse_bool grammar) in non-`test` data planes — a prod bot
    must not silently rely on an unapproved privileged intent (L-17). Reads the approval flag via
    the declared attribute (cfg.SB_INTENT_MSGCONTENT_OK / cfg.SB_INTENT_MEMBERS_OK). Missing approval
    in prod ⇒ ConfigError → StartupError. In `test` plane the check is advisory (logged, non-fatal)."""
```

### 3.3 `MetricSpec` + registry — `sb/spec/observability.py`, `sb/kernel/observability/metrics.py`

```python
class MetricKind(StrEnum): COUNTER="counter"; GAUGE="gauge"; HISTOGRAM="histogram"

@dataclass(frozen=True)
class LabelSpec:
    """A metric label AND its declared value domain — the input check_metric_cardinality needs to
    bound series count. Exactly one of (domain, max_cardinality) must be set."""
    name: str                        # [S] label key, verbatim (e.g. "outcome", "guild_id", "query_name")
    domain: tuple[str, ...] = ()     # [S] CLOSED allowed-value set when finite (outcome ∈ §2.7 vocab,
                                     #     kind ∈ {hit,miss}); |domain| is the label's exact cardinality
    max_cardinality: int = 0         # [S] declared upper bound for an OPEN-but-bounded label
                                     #     (guild_id, query_name); used when `domain` is empty
    # __post_init__: exactly one of (domain non-empty, max_cardinality>0) — else COMPILE_ERROR
    #   (an unbounded label with neither is forbidden — that is the cardinality-explosion class).

@dataclass(frozen=True)
class MetricSpec:
    name: str                        # [S] exposition name, verbatim (governance_cache_hits_total, …)
    kind: MetricKind                 # [S]
    doc: str                         # [S]
    labels: tuple[LabelSpec, ...] = ()  # [S] each label carries its own declared domain (was names-only)
    buckets: tuple[float, ...] = ()  # [S] histogram only; empty ⇒ COMPILE_ERROR for HISTOGRAM
    cardinality_budget: int = 0      # [O] max expected series; 0 ⇒ CI-red unless zero labels
    owner_subsystem: str | None = None  # [S]

METRICS: tuple[MetricSpec, ...] = ( … all 46 families declared, verbatim names/labels(+domains)/buckets … )

class MetricRegistry:
    def counter(self, name: str) -> Counter: ...
    def gauge(self, name: str) -> Gauge: ...
    def histogram(self, name: str) -> Histogram: ...

def build_registry(specs: Iterable[MetricSpec] = METRICS) -> MetricRegistry:
    """Instantiate every declared family once. When prometheus_client is absent, every handle is the
    silent _NoOp (shipped fallback preserved verbatim). Duplicate name ⇒ ValueError at build."""

def render() -> tuple[bytes, str]:
    """(body, content_type) for the /metrics adapter (§3.8). content_type is the Prometheus text
    exposition media type: 'text/plain; version=0.0.4; charset=utf-8'. When prometheus_client is
    absent, returns an empty body with the same content_type (the _NoOp registry has nothing to emit)."""
```

`tools/check_metric_cardinality.py`: for every `HISTOGRAM` a non-empty `buckets`; for every labelled
family a `cardinality_budget > 0` and **`∏ over labels of L.cardinality ≤ cardinality_budget`**, where
`L.cardinality = len(L.domain)` when a domain is declared else `L.max_cardinality`. A label with
neither a `domain` nor a `max_cardinality` ⇒ CI-red (the unbounded-label class — the shipped
`_TABLE_RE`/`query_name` bounding pattern becomes a declared `max_cardinality`, not a comment). CI-red
on any violation.

### 3.4 DB pool — `sb/kernel/db/pool.py`

```python
class DBUnavailable(ConnectionError):
    """The pool could not serve — down, timed out, or checkout failed. The ONE typed signal the DB
    seam raises for every raw asyncpg connection/pool error. It SUBCLASSES ConnectionError on purpose:
    the resolver's from_exception (spec 02 §3.3) already lists `ConnectionError` in its transient row,
    so DBUnavailable is classified transient/retryable=True/DISCORD_FAILED through that EXISTING row —
    no new row and no seam edit required (§3.9). Layer ownership: the DB seam owns raw asyncpg →
    DBUnavailable; the resolver owns typed exception → ErrorEnvelope."""

async def init(cfg: Config) -> None:
    """create_pool with: dsn=cfg.DATABASE_URL, min_size, max_size,
       command_timeout=cfg.DB_COMMAND_TIMEOUT_S (default 30.0),   # NEW — bounds a wedged query
       max_inactive_connection_lifetime=cfg.DB_IDLE_LIFETIME_S,   # NEW (default 300.0) — recycles stale conns
       init=init_connection.
       Precondition: assert_data_plane(cfg) has already passed inside preflight (§3.5). Then run
       migrations (§3.6)."""

@asynccontextmanager
async def checked_acquire() -> AsyncIterator[Connection]:
    """Acquire + validate-or-reacquire: on checkout, if the connection has been idle past a
    threshold, `SELECT 1`; on failure release-and-reacquire ONCE; a second failure raises
    DBUnavailable. Closes the 'dead connection handed to caller after a DB restart' class."""

@asynccontextmanager
async def transaction() -> AsyncIterator[Connection]:
    """THE sanctioned transaction seam (was missing — §3.7's `once()` atomicity depends on it).
    `async with db.transaction() as conn:` acquires via checked_acquire(), opens `conn.transaction()`,
    yields the txn-bound Connection, and commits on clean exit / rolls back on exception. This is the
    ONLY sanctioned way a domain runs `once()` atomically with its effect: `once(key, conn=conn)` plus
    the action's own `execute(..., conn=conn)` writes share ONE connection and ONE transaction, so the
    guard row and the effect commit-or-roll-back together. Raw `conn.transaction()` / `conn.execute()`
    stay banned outside `sb/kernel/db` (§7); `transaction()` is how a domain gets an explicit txn without
    touching raw asyncpg. asyncpg failures inside the block surface as DBUnavailable (rollback first)."""

async def fetchone/fetchall/execute(query, params=(), *, conn=None):
    """Verbatim shipped signatures + the db_query_seconds/slow_path observation. `conn=` accepts a
    txn-bound connection from transaction() so writes join an open txn; omit it for autocommit. NEW:
    asyncpg connection/pool errors (InterfaceError, pool timeout, ConnectionDoesNotExist) are caught
    and re-raised as DBUnavailable — the refuse-with-notice posture is centralized HERE (T2-14), so no
    domain, cog, or view ever fails-open with empty/stale rows. Query results are never faked."""
```

### 3.5 Data-plane rail — `sb/kernel/db/data_plane.py` (the 4th rail, L-10)

```python
def assert_data_plane(cfg: Config) -> None:
    """The 4th kernel rail — refuse boot on any DSN not provably safe for THIS bot. Runs inside
    preflight(), before init(). Reads only declared Config attributes (no raw getenv — this spec's
    own check_config_usage ban applies to it too). Rules:
      • cfg.data_plane is REQUIRED (SB_DATA_PLANE ∈ {test,prod}; absence already fail_fast in §3.2).
      • data_plane == TEST  ⇒ the DSN host (urlsplit(cfg.DATABASE_URL).hostname) MUST be in the
        declared test allowlist cfg.SB_TEST_DB_HOSTS (a CSV tuple) OR the DSN carries the
        `?sb_plane=test` query marker; else RefuseBoot.
      • data_plane == PROD  ⇒ requires cfg.SB_PROD_ATTEST to be PRESENT (a non-None opaque human-set
        secret token — PRESENCE is the attestation, since it is a SecretSpec its value is never logged)
        AND the running image is the prod worker (cfg.RAILWAY_SERVICE_NAME == 'worker', the
        Railway-injected service name); else RefuseBoot.
        This is the structural exclusion: an agent/dev container carries the prod DSN (Q-0213) but
        NOT SB_PROD_ATTEST, so it cannot open prod even by accident.
    RefuseBoot is a ConfigError accrued into StartupError → FAILED_STARTUP. No data plane, no boot."""
```

> **Prod-attest custody is a labeled deferral, not a blocker (§9).** The *type* is closed here —
> `SB_PROD_ATTEST` is a `SecretSpec` gated by **presence** (present ⇒ attested), so the spec is
> buildable now. The durable *custody mechanism* (plain env token vs sealed secret vs OIDC claim) is
> owner-gated ops-integration work owned by CUT-1 — surfaced as an open decision, not decided here.

### 3.6 Migrations — `sb/kernel/db/migrations.py` + `tools/check_migrations.py`

```python
class MigrationDrift(RuntimeError):
    """A recorded migration's checksum no longer matches its file on disk — an applied migration was
    edited. Correctness hazard (DB ≠ source-of-record). Refuse boot; never auto-repair."""

# schema_migrations gains a `checksum TEXT NOT NULL` column (§5). At boot, AFTER applying pending
# files and BEFORE returning:
async def verify_applied_checksums() -> None:
    """For every recorded version, sha256(file_bytes) == stored checksum; mismatch ⇒ MigrationDrift.
    A version recorded-but-file-absent ⇒ MigrationDrift (a squashed/renamed applied file)."""
```

`tools/check_migrations.py` (CI gate, extends the shipped structural pytest):
1. numbering contiguous + unique (shipped test folds in);
2. **immutability** — every already-committed `NNN_*.sql` byte-matches its entry in a committed
   `migrations/checksums.json` manifest; a changed applied file is CI-red **before** it can reach a
   deploy (today drift is only caught at boot). New files append to the manifest in the same PR;
3. forward-only (no version below the current max may be *added* in a PR that isn't a signed rebase).

### 3.7 Idempotency-key contract — `sb/kernel/db/idempotency.py` (T2-2 seed — the shape strand-2 completes)

```python
@dataclass(frozen=True)
class IdempotencyKey:
    """THE canonical key shape. Deterministic string: exactly-once over an at-least-once substrate.
    Every mutating action that can double-fire on deploy-overlap (L-6) guards on one of these."""
    namespace: str      # the action family, namespace-reserved (e.g. "economy.daily", "rps.forfeit")
    guild_id: int
    dedup_token: str    # the action's NATURAL key — the Discord event/entity id that makes a
                        #   retry identical: message_id | interaction_id | (tournament_id,round) | …
    def render(self) -> str:  # f"{namespace}:{guild_id}:{dedup_token}" — the stored PK
        ...

@dataclass(frozen=True)
class PriorOutcome:
    """What a prior first-run committed for a key — the False-branch read result."""
    outcome: str            # §2.7 frozen vocab ONLY (SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED)
    result_ref: str | None  # optional pointer to the durable result (audit id / mutation id)
    first_seen_at: int

async def once(key: IdempotencyKey, *, conn: Connection) -> bool:
    """INSERT ... ON CONFLICT DO NOTHING RETURNING. True ⇒ first sighting, caller proceeds inside
    the SAME txn. False ⇒ already applied, caller no-ops (and reads the prior outcome via
    read_outcome). MUST be called with a txn-bound `conn` from `db.transaction()` (§3.4) so the guard
    row and the action's effect commit atomically — the fast-release deploy handoff (T2-2) relies on
    this: two instances briefly both handling the same event both attempt `once`, exactly one wins,
    no drain required. `conn` must be the SAME connection the action writes its effect through."""

async def record_outcome(key: IdempotencyKey, outcome: str, *, result_ref: str | None = None,
                         conn: Connection) -> None:
    """Write-back — fills the guard row's outcome/result_ref AFTER the effect is written, INSIDE the
    same txn/`conn` as `once()` and the effect, BEFORE commit. `UPDATE idempotency_keys SET outcome=?,
    result_ref=? WHERE key=?`. So the recorded outcome commits atomically with the effect it describes;
    a crash before commit rolls back BOTH the effect and its outcome, and the key row too (nothing
    half-recorded). `outcome` MUST be one of the §2.7 constants — any other value ⇒ ValueError."""

async def read_outcome(key: IdempotencyKey, *, conn: Connection) -> PriorOutcome | None:
    """The False-branch read path: returns the prior committed PriorOutcome for an already-applied key,
    or None when the row exists but outcome is not yet recorded (a concurrent first-run still mid-flight
    before its record_outcome commit). Callers that must reproduce the first run's user reply read this;
    callers that only need 'already done, no-op' ignore it. Read-only — safe with or without an open txn."""
```

**Canonical usage (the atomic pattern):**

```python
async with db.transaction() as conn:            # §3.4 — one connection, one txn
    if await once(key, conn=conn):              # first sighting
        result = await apply_effect(conn=conn)  # the action's own writes join THIS txn
        await record_outcome(key, result.outcome, result_ref=result.audit_id, conn=conn)
    else:                                        # already applied on the other instance
        prior = await read_outcome(key, conn=conn)   # may be None if still mid-flight
        return prior                             # reproduce / no-op
# commit here — guard row + effect + outcome all land together, or none do
```

**Ownership boundary (V-3):** this spec owns the *shape* (`IdempotencyKey`, `PriorOutcome`, `once`,
`record_outcome`, `read_outcome`, the table). **Strand-2 completes** the per-action `dedup_token`
definitions (which natural key each action uses) and the in-txn **outbox** that emits events under the
same key + `conn` (L-9). Both consume this contract.

### 3.8 Readiness / drain contract — `sb/adapters/http/health.py`

`/health` (liveness) and `/lifecycle` (diag dump) port verbatim. `/ready` becomes **DB-aware** and
gains a declared consumer. `/metrics` is mounted here too (below). The full readiness state table
(the contract):

| gateway `is_ready()` | lifecycle phase | DB pool | `/ready` | `reason` |
|---|---|---|---|---|
| False | any | any | 503 | `gateway_not_ready` |
| True | RUNNING | up | **200** | — |
| True | RUNNING | **down** | **503** | `db_unavailable` ← **NEW, closes the DB-blind gap** |
| True | STARTING | any | **503** | `still_starting` ← **SEMANTICS CHANGE, see note** |
| True | DRAINING / SHUTTING_DOWN / RESTARTING / STOPPED | any | 503 | `draining` |
| True | FAILED_STARTUP | any | 503 | `failed_startup` |

> **⚠ STARTING readiness is a deliberate SEMANTICS change (not a verbatim port).** Shipped
> `_ready_handler` returns **200** when `can_accept_commands()` is true, and shipped `can_accept_commands()`
> = `{STARTING, RUNNING}` (`lifecycle.py:63`) — so **today STARTING ⇒ 200**. This table replaces that
> gate with a **RUNNING-only 200** rule: STARTING ⇒ **503 `still_starting`**. Rationale: a replica that
> is still booting (pool not up, migrations mid-apply, on_ready not fired) cannot serve commands, so an
> orchestrator must **not** route traffic to it — exactly the case the readiness probe exists to exclude.
> The shipped `can_accept_commands()`/`{STARTING,RUNNING}` gate is intentionally **not** ported into
> `/ready`; it remains valid for its own callers (command_access). This is a behavior change, not a
> docstring/DB-awareness-only change — §10 A#23 is corrected accordingly.

DB probe = a bounded `SELECT 1` via `checked_acquire()` with a short timeout, cached ~1s so probe
storms don't hammer the pool. **The consumer (was missing):** the orchestrator healthcheck path
points at `/ready`; the **fast-release deploy handoff** (T2-2) reads `/ready==503-while-DRAINING` as
the stop-routing signal — the old replica flips to DRAINING, `/ready` goes 503, the router drains it,
the new replica takes the runtime lock immediately (no drain-then-release wait), and idempotency keys
(§3.7) cover the brief both-live overlap.

**`/metrics` mount (was unowned):** `sb/adapters/http/health.py` mounts a fourth route,
`GET /metrics`, on the SAME aiohttp health server, returning `render()` (§3.3) — body +
`content_type='text/plain; version=0.0.4; charset=utf-8'` (Prometheus text exposition). No auth/gating
(it is scrape-only, no secrets — redacted config never enters a metric). It is independent of lifecycle
phase (a draining replica still exposes metrics).

### 3.9 Consumed-seam adapters (stated so the seam pass can verify)

- **`DBUnavailable` (§3.4) routes through the resolver's EXISTING transient row.** Because
  `DBUnavailable` subclasses **`ConnectionError`**, and spec 02 §3.3's `from_exception` table already
  lists `ConnectionError` (and `asyncpg pool-timeout`) in its **`transient`** row
  (`transient / retryable=True / DISCORD_FAILED`, user copy "Discord/the service is busy — try again
  shortly."), `from_exception(DBUnavailable(...), …)` classifies it transient with **no new row and no
  edit to spec 02**. The DB seam (§3.4) is the sole producer of `DBUnavailable`; the resolver is the sole
  classifier. *(Seam nicety for spec 02, non-blocking: its `ConnectionError`/`asyncpg pool-timeout`
  transient row MAY be annotated "(incl. `DBUnavailable`, the typed form the DB seam raises)" for
  readers — but buildability does not depend on that annotation, since subtype matching already fires.)*
- `StartupError`/`RefuseBoot`/`MigrationDrift` map to the lifecycle **`FAILED_STARTUP`** phase via
  the composition root's `fail_startup` seam (compiler spec 01 §3.4, lifecycle K5).

---

## 4. Provides / Consumes

### 4.1 Provides (canonical shapes this spec OWNS)

| Contract | Shape | Consumers |
|---|---|---|
| Config/secret grammar | `ConfigSpec`/`SecretSpec`/`ConfigPosture`/`ConfigType`(+CSV)/`IntentSpec` + `CONFIG_FIELDS` (47) | boot-preflight; generated `docs/ownership.md` env section; §4.4 activation (`on_when_keyed` ← DORMANT secrets) |
| Config accessor | frozen `Config`, one typed attribute per field (verbatim env name), redacted fields hidden | every consumer via `cfg.<ENV_VAR>`; `iter_fields()`/`is_configured()` for tooling |
| Boolean grammar | `parse_bool` (`{1,true,yes,on,y,t}` / else `ConfigError`) | every config coercion; approval_env intents; bans all three shipped variants |
| Boot-preflight | `preflight() -> Config` raising `StartupError` | composition root `sb/app`, runs before compiler boot_gate + before connect |
| DB-adapter posture | `DBUnavailable(ConnectionError)` + refuse-with-notice CRUD (T2-14) | every domain via the seam; the resolver `from_exception` (via ConnectionError row) |
| Pool robustness | `command_timeout` + `checked_acquire()` + `transaction()` (the txn seam) | all DB access; `once()` atomicity |
| Migration integrity | `checksum` column + `verify_applied_checksums` + `check_migrations` gate | K3 runner; CI |
| `MetricSpec` + registry | `MetricSpec`/`LabelSpec` + `build_registry` + `render()` + cardinality gate | `kernel/observability`; every metric emitter; `/metrics` route |
| Readiness/drain contract | the §3.8 state table (RUNNING-only 200) + DB-aware `/ready` + `/metrics` | orchestrator healthcheck; the fast-release handoff |
| Data-plane rail | `assert_data_plane` (non-`test` DSN ⇒ refuse) | boot; CUT-1 |
| **Idempotency-key contract** | `IdempotencyKey`/`PriorOutcome` + `once()`/`record_outcome()`/`read_outcome()` + `idempotency_keys` table | **strand-2 outbox + scheduler**; every double-fireable action |

### 4.2 Consumes (assumed shapes — exact so the seam pass can check)

| Assumed contract | Precise assumption | Source spec |
|---|---|---|
| Compiler boot-gate | `sb/app/boot_gate.py` runs boot legs in the composition root; **preflight() is invoked as leg-0, before P1..P9 and before gateway connect** | 01 §3.4 (`boot_gate.py`, `compile_manifests`) |
| `fail_startup` seam | A composition-root call that drives the lifecycle to `FAILED_STARTUP`; accepts an exception aggregate | 01 §3.5; lifecycle K5 |
| Error envelope | `from_exception(exc, surface)` classifies `DBUnavailable` **via its existing `ConnectionError` transient row** → `transient`/`retryable=True`/`DISCORD_FAILED`; unknown→`bug` | 02 §3.3 (line 179, `ConnectionError` row) |
| Outcome vocab | `outcome` values written by `record_outcome`/stored in `idempotency_keys.outcome` are the §2.7 frozen constants (`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED`) — built on the shipped lifecycle vocab (`contracts.py:48-52`) and the dispatch analogue `StageResult` (`message_pipeline.py:181`), never a new type | §2.7; lifecycle `contracts.py` |
| Restart-safety | The scheduler's **boot-reconcile** re-arms durable timers **after** `/ready` reports 200 (RUNNING) — reconcile must not run against a DB the readiness gate would 503 | strand-2 scheduler |
| Outbox + scheduler | Both derive their dedup token from `IdempotencyKey.dedup_token`; the outbox writes its row inside the same `db.transaction()` conn as `once()` | strand-2 |
| Namespace | `ConfigSpec.env_var`, `MetricSpec.name`, `IdempotencyKey.namespace` are namespace-reserved `(kind,value)` claims | K1 (spec 03) |

---

## 5. Data model + migration/index shape

Two kernel tables (fresh chain `0001+`, §5.2). Both are **aggregates** by the checkpoint test (§5.1) —
their loss costs an operator an audit answer / a correctness guarantee, so both are first-class tables.

**`schema_migrations`** (extends the shipped three-column shape — the ONE change to the ledger):

| column | type | note |
|---|---|---|
| `version` | `INTEGER PRIMARY KEY` | verbatim |
| `applied_at` | `BIGINT NOT NULL` | verbatim |
| `description` | `TEXT NOT NULL` | verbatim |
| `checksum` | `TEXT NOT NULL` | **NEW** — `sha256(file_bytes)`; verified every boot (§3.6) |

**`idempotency_keys`** (new, T2-2):

| column | type | note |
|---|---|---|
| `key` | `TEXT PRIMARY KEY` | `IdempotencyKey.render()` — `{namespace}:{guild_id}:{dedup_token}`; the `ON CONFLICT` target for `once()` |
| `namespace` | `TEXT NOT NULL` | for retention scoping + metrics label (bounded) |
| `first_seen_at` | `BIGINT NOT NULL` | insertion epoch (set by `once()`) |
| `outcome` | `TEXT` | the §2.7 outcome the first run committed; **nullable until `record_outcome()` fills it** in the same txn after the effect writes (§3.7) |
| `result_ref` | `TEXT` | optional pointer to the durable result (audit/mutation id); written by `record_outcome()` |

Write paths: `once()` INSERTs `key/namespace/first_seen_at` (outcome/result_ref NULL);
`record_outcome()` UPDATEs `outcome/result_ref` for that key in the same txn; `read_outcome()` SELECTs
them for the False branch (§3.7). Index: PK on `key` is the dedup guard. Secondary
`(namespace, first_seen_at)` for the retention sweep. `StoreSpec.retention` declared per namespace
(§10.3 item 4) — short-lived families (message dedup) prune fast; money/audit families
(`economy.daily`, `rps.forfeit`) retain to the audit horizon.

No other schema is owned here — the 43 domain stores are `StoreSpec`-derived by their own manifests.

---

## 6. Restart & merge=deploy behavior

- **Boot order (composition root, `sb/app`):** `preflight()` (which itself runs `assert_data_plane()` +
  `assert_intents()`) → compiler boot_gate legs (01) → `db.init` (pool + migrations +
  `verify_applied_checksums`) → EventBus → lifecycle (STARTING) → gateway connect → on_ready
  (STARTING→RUNNING) → `/ready` 200. Any step 1-4 failure ⇒ `FAILED_STARTUP`, gateway never connects
  (the "validate before connect" invariant, audit A §6.2 R3). Note `/ready` is **503 throughout
  STARTING** (§3.8) and flips to 200 only at RUNNING — the orchestrator holds traffic until the replica
  can actually serve.
- **merge=deploy (Railway auto-redeploy):** the **fast-release** handoff (T2-2, decided). Old worker
  → SIGTERM → lifecycle DRAINING → `/ready` 503 (router stops routing) → old worker **releases the
  runtime lock immediately** rather than draining to zero first. New worker acquires the lock at boot
  and serves. During the sub-second both-live window, `once()` (§3.7) makes any duplicate
  event-handling a no-op — this is why fast-release is *correct* where the #1693 listener-only gate
  (L-6) was not: it covers prefix, interaction, and non-message lanes uniformly through the shared
  idempotency guard (`db.transaction()` + `once()`), not per-listener.
- **Dual-instance migrations:** the shipped `pg_advisory_lock` serialization is preserved verbatim —
  only one instance applies a pending migration; the other waits, then `verify_applied_checksums`
  sees a consistent ledger.
- **Single-process (ADR-001):** carried forward as a **named non-goal** (T2-13, §9) — the runtime
  lock guarantees exactly one writer; nothing here assumes horizontal sharding.

---

## 7. Architecture rules honored

- **Layer boundaries** (`docs/architecture.md`): `sb/kernel/observability` is the cross-cutting leaf
  every layer may import (design-spec §1.1; fixes the shipped `pool.py`→`services.metrics` up-import
  that made metrics misfiled, decision 7). `sb/kernel/config` and `sb/kernel/db` sit at/below the DB
  seam — they import `sb/spec` (dataclasses) and stdlib/asyncpg only; **no upward import** to
  services/views/cogs. `data_plane`/`idempotency` live under `sb/kernel/db` (asyncpg-only, mirroring
  the shipped `utils/db/` "asyncpg only" rule).
- **All DB access via the seam:** `once()`/`record_outcome()`/`read_outcome()`, migrations, the pool
  wrappers, and **`transaction()`** are the *only* callers of raw `conn.execute`/`conn.transaction()` —
  every domain routes through `fetchone/fetchall/execute` (autocommit) or `db.transaction()` (explicit
  txn), preserving the "never `pool.execute()` / raw `conn.transaction()` outside `utils/db/`" rule (now
  `sb/kernel/db`). `db.transaction()` is the sanctioned way a domain gets an explicit multi-write txn.
- **Config via the accessor, never raw getenv:** `check_config_usage` bans `os.getenv`/`os.environ`
  outside `sb/kernel/config/`; every consumer (incl. `assert_data_plane`, which reads
  `cfg.RAILWAY_SERVICE_NAME`/`cfg.SB_PROD_ATTEST`/`cfg.SB_TEST_DB_HOSTS` as declared attributes) goes
  through `Config`.
- **Settings via constants, mutations audited:** config is env (boot-time), **explicitly not** the
  per-guild settings resolver (audit A §6.2: "config never conflated with settings"). The
  idempotency guard is infrastructure, not an auditable mutation — the *action* it guards still calls
  `emit_audit_action()` on its own mutation seam.
- **INV cites honored:** the runtime-lock single-writer invariant (LP-4 lineage) is the substrate the
  fast-release handoff + idempotency keys build on; `FAILED_STARTUP` is the frozen terminal phase
  (lifecycle) these rails drive.

---

## 8. Options → Decision → Why (forks CLOSED)

| # | Fork | Options | Decision | Why |
|---|---|---|---|---|
| 1 | Where `ConfigSpec` lives | per-subsystem manifest facet vs kernel-global registry | **Kernel-global `CONFIG_FIELDS`** (with `owner_subsystem` for provenance) | Preflight must see the whole set at boot, *before* any subsystem/manifest loads — a per-subsystem facet is a chicken-and-egg |
| 1b | Config accessor model | generic `.get(spec)` vs one attribute per field | **One typed attribute per field, named verbatim by `env_var`** (`.get`/sibling-Secrets dropped) | The whole codebase reads `cfg.DATABASE_URL`-style; redaction is a field property (`redact`) enforced at repr, not a separate object — one consistent surface, no name-mapping to invent |
| 2 | Boolean grammar | keep per-call variants vs one canonical set | **`{1,true,yes,on,y,t}` truthy / else `ConfigError`** | Superset of all three shipped grammars (no shipped value changes meaning); strict-error kills silent misconfig |
| 3 | Migration integrity | checksum-verify vs auto-repair vs numbering-only | **Checksum column + verify-or-`FAILED_STARTUP`, never repair** | An edited applied migration means DB ≠ source-of-record; guessing which is right is the corruption path |
| 4 | Migration gate home | runtime-only vs CI + runtime | **Both** — `check_migrations` (CI, pre-deploy) + boot verify | Today drift is caught only at boot (after merge=deploy is live); a CI gate catches the edit in the PR |
| 5 | DB-down posture | degrade-with-stale vs refuse-with-notice | **Refuse-with-notice uniformly, centralized at the adapter** (T2-14) | Fail-open with empty/0 rows can authorize a bad spend/grant; one central posture beats N per-cog guesses |
| 5b | DBUnavailable→resolver seam | new `DBUnavailable` row in spec 02 vs subclass an already-matched type | **`DBUnavailable(ConnectionError)`** — routes through spec 02's existing `ConnectionError` transient row | Zero-edit seam: subtype matching fires the correct transient/DISCORD_FAILED classification; DB seam owns raw→typed, resolver owns typed→envelope |
| 6 | `command_timeout` value | none vs fixed vs configurable | **30s default, `DB_COMMAND_TIMEOUT_S` override** | Bounds a wedged query well above p99, below the orchestrator kill deadline |
| 7 | Stale-connection handling | trust asyncpg vs explicit checkout ping | **`checked_acquire()` — ping + reacquire once** | Closes the "dead conn after DB restart handed to caller" class the shipped pool has no guard for |
| 7b | Idempotency atomicity seam | autocommit `once()` vs explicit txn manager | **`db.transaction()` context manager** shared by `once()`+effect+`record_outcome()` | Fast-release correctness needs the guard, effect, and outcome to commit-or-roll-back together on ONE conn — no raw asyncpg in domains |
| 7c | Idempotency outcome surface | `once()`→bool only vs add record/read | **Add `record_outcome()` + `read_outcome()` + `PriorOutcome`** | The False branch must reproduce the first run's reply and the `outcome` column must be filled — bool alone left both unbuildable |
| 8 | `MetricSpec` / labels | names-only labels vs `LabelSpec` with domain | **`LabelSpec` (domain or `max_cardinality`) + budget gate** | The cardinality checker needs each label's declared value domain to compute `∏|domain| ≤ budget`; names alone give it no input |
| 9 | Readiness DB probe + STARTING | keep DB-blind {STARTING,RUNNING}⇒200 vs DB-aware RUNNING-only | **DB-aware `/ready`, RUNNING-only 200, ~1s cached (STARTING⇒503)** | The gate exists to route traffic away from a replica that can't serve — a DB-down OR still-booting replica can't; STARTING⇒503 is a deliberate semantics change (§3.8 note) |
| 10 | Idempotency key shape | UUID token vs natural-key derived | **Natural-key `{namespace}:{guild_id}:{dedup_token}`** | A retry of the *same Discord event* must produce the *same* key or dedup fails; a random UUID defeats it |
| 11 | Deploy handoff | drain-then-release vs fast-release + keys | **Fast-release + idempotency keys** (T2-2) | Covers every double-fire lane (prefix/interaction/non-message) at once, where the #1693 listener gate reaches only one |
| 12 | `SB_PROD_ATTEST` type | BOOL-truthy vs SECRET-presence | **`SecretSpec`, gated by PRESENCE** (present ⇒ attested) | It is an opaque human-set token, not a flag — presence is the attestation and its value stays redacted; the custody *mechanism* stays owner-gated (§9, open decision) |

---

## 9. Labeled deferrals (bounded)

| Deferral | Reason | Bound |
|---|---|---|
| **`CacheSpec` storage grammar** (A#22) | Caches (guild_config, scope_locks, governance — the 6× fragmentation, L-15) are a **cross-cutting** collapse, not an ops-substrate rail; their *observability* (hit/miss families) is declared here via `MetricSpec` | Strand-3 (cross-cutting concerns); the cache-metric families ship now |
| **Per-action `dedup_token` definitions** | Each of the ~dozen double-fireable actions names its own natural key — that is per-subsystem work | Strand-2 completes them against this key shape (V-3) |
| **The in-txn outbox** (L-9) | At-least-once delivery is strand-2's durability rail; it *consumes* `once()` + `db.transaction()` but is not this spec | Strand-2 (T2-3) |
| **Slash-first survivability posture** (L-17 product leg) | The `IntentSpec` contract + approval-env preflight is designed here; the *product* decision (verification-application milestone, intent-denial fallback ladder) is a roadmap call | Build-plan / owner, not a kernel rail |
| **Exact prod-attest *custody* mechanism** | `SB_PROD_ATTEST` as a presence-gated SecretSpec is designed (type CLOSED, §3.5/§8-12); whether custody becomes an OIDC claim, a sealed secret, or a plain env token is an ops-integration + credential-custody call | **Owner-gated** (see open decision below); K3/CUT-1 ops setup |
| **Retention windows per idempotency namespace** | The `StoreSpec.retention` field exists; the filled-in per-namespace inventory is the §10.3 pre-cutover deliverable | Phase-4 retention inventory |

**Open decision surfaced to the owner (credential-custody — NOT decided here):** the durable
`SB_PROD_ATTEST` custody mechanism. The spec is **buildable now** with a presence-gated env `SecretSpec`;
the owner call is whether to keep the plain env token or upgrade to a sealed secret / OIDC claim at
CUT-1. Recorded as an open decision in this pass's structured output (owner-gated, ops tier); route
durable resolution to `docs/owner/maintainer-question-router.md`.

No open-ended speculation — every deferral names its owning strand/phase within the 43-subsystem +
named-amendment corpus.

---

## 10. Retirement map (FJ L-rows + owner-queue items this RETIRES)

| Item | What it was | How this retires it |
|---|---|---|
| **L-10** (⚑ new, high) | CUT-1 data plane undefined; ambient prod DSN in agent containers | §3.5 the **4th rail** — `assert_data_plane()` refuses boot on a non-`test` DSN without `SB_PROD_ATTEST` + prod-worker identity; `SB_DATA_PLANE` is a required fail_fast field. **RETIRED** (persistent test Postgres provisioning is the CUT-1 ops step, not a kernel rail — noted §9) |
| **T2-2 / L-6** (⚑) | Fast-release + durable per-action idempotency keys | §3.7 `IdempotencyKey`/`PriorOutcome` + `once()`/`record_outcome()`/`read_outcome()` + `idempotency_keys` table + `db.transaction()` atomicity; §6 fast-release handoff. **RETIRED (shape)** — per-action tokens are strand-2's completion (V-3) |
| **T2-14 / L-? (DB posture)** | DB-down refuse-with-notice, centralized at the adapter | §3.4 `DBUnavailable(ConnectionError)` + refuse-with-notice CRUD wrappers; §3.8 readiness 503; §3.9 routes through spec 02's existing ConnectionError transient row. **RETIRED** |
| **T2-13** | Single-process ADR-001 as a named non-goal | §6 + §9 — carried forward explicitly as a non-goal with the runtime-lock single-writer guarantee. **RETIRED (named)** |
| **T2-22 / A#31 A#32** (⚠ UNVERIFIED→verified) | ConfigSpec/SecretSpec + gateway-intent — verify then design | Intent claim **verified this session against shipped source**: `message_content`/`members` are the two hardcoded privileged intents (`bot1.py:77-78` — `intents.message_content = True`, `intents.members = True`). §3.1-3.2 grammar + preflight, §3.2 `assert_intents`. **RETIRED** |
| **T3 A#21** | MetricSpec — "yes" | §3.3 `MetricSpec` + `LabelSpec` + registry + cardinality gate. **RETIRED** |
| **T3 A#23** | `/ready` DB-awareness + lock as restart seam | §3.8 readiness state table + DB-aware `/ready`; §6 runtime-lock-as-restart-seam. **Correction:** this is **not** a docstring-only rewrite — `/ready` STARTING flips **200→503** (a semantics change from shipped `{STARTING,RUNNING}⇒200`, §3.8 note). **RETIRED (with semantics change flagged)** |
| **T3 A#22** | CacheSpec — "yes" | **PARTIAL** — cache-observability families declared via `MetricSpec` now; the storage grammar deferred to strand-3 (§9) |
| **L-17** (⚑, intent leg) | Privileged-intent growth gate never a design constraint | **PARTIAL** — `IntentSpec` + `assert_intents` approval-env preflight designed (§3.1-3.2); the product survivability posture stays a build-plan item (§9) |

---

## 11. Build order (design-spec §9, K0-K10)

| Component | Lands at | Blocks |
|---|---|---|
| `sb/spec/config.py`, `sb/kernel/config` (preflight + `parse_bool` + `parse_dsn`), `check_config_usage` | **K0** (substrate; runs before all else at boot) | everything — the composition root cannot boot without it |
| `sb/spec/observability.py` (incl. `LabelSpec`), `sb/kernel/observability/metrics.py` (+`render()`), `check_metric_cardinality` | **K0** (the cross-cutting leaf, §9.1 "observability lands with the substrate") | every metric emitter below it; the `/metrics` route |
| `IntentSpec` + `assert_intents` | **K0** (part of preflight) | gateway connect |
| `sb/kernel/db/{pool(+transaction),data_plane,migrations,idempotency}` + `check_migrations` | **K3** (db seam + fresh runner) | K5 lifecycle, K7 workflow (audit spine writes via the seam), strand-2 outbox/scheduler |
| `sb/adapters/http/health.py` (readiness/drain + `/metrics` route) | **K5** (lifecycle + the phases `/ready` reads) | the deploy handoff; CUT-1 |

**What this spec blocks:** K3 cannot land without the config object (K0) — `db.init(cfg)` takes it.
K7's audit spine and strand-2's outbox both write through the K3 seam (`db.transaction()`) and guard on
`once()`. The readiness contract (K5) gates CUT-1 (the fast-release handoff is the cutover deploy
mechanism), and mounts the `/metrics` route. Per §9.1, each component lands **with its checker**, so
`check_config_usage` / `check_migrations` / `check_metric_cardinality` arm the required-check set
incrementally.
