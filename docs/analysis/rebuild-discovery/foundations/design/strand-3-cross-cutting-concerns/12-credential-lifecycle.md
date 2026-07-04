# Strand 3 · Cross-cutting concern ⑫ — Credential lifecycle + dependency supply-chain posture

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B **design contract** for one never-surfaced
> foundational concern: Q-0213 deliberately **concentrated** the full-access Railway account token,
> the prod DSN, the Discord + provider tokens, and the GitHub repo-write token in agent containers so
> the project runs owner-independently — but shipped **nothing** for what happens when one of those
> credentials leaks, ages, or must be killed (FJ §4 **#10**). In parallel the runtime carries **12
> `>=` runtime deps (7 with no ceiling), no lockfile, re-resolved on every merge=deploy**, with agents
> licensed to adopt packages under Q-0105 and no review gate (FJ §4 **#12** — the supply-chain leg).
> This dossier designs **the minimum recovery arm that does not reintroduce owner-dependency** (a
> credential registry + tiered rotation cadence + a revocation kill-path + a compromise-recovery
> runbook) and the **deterministic supply-chain posture** (lockfile + hash-verify + advisory scan)
> that composes *with* the Q-0105 adopt-freely grant instead of reversing it. **Precedence:** shipped
> source & merged PRs win (Q-0120); the five strand-1 specs + `shared-vocabulary.md` win for shapes
> they own; this dossier owns only the **credential-lifecycle grammar leaf** (a new sibling leaf — it
> does **not** redefine `SecretSpec`, §2.A) + the two postures. It authors no `disbot/` and no `sb/` code.
>
> **Consumes (does NOT redefine):** the config/secret grammar `SecretSpec` + `CONFIG_FIELDS` +
> `SecretSpec.redact` + the data-plane rail (⑥ / spec 05 §3.1–3.5); the idempotency/​restart pattern
> (shared-vocab §④/§⑤); the security-abuse **class-13** probes N-1 (credential lifecycle) / N-2 (supply
> chain) from concern ⑩ — this dossier is the **fix** that class-13's **lens** asserts exists. It
> **consumes** Q-0213 (the concentration decision — NEVER reversed here), Q-0105 (the adopt-freely
> grant), and Q-0193 (merge/var-change = deploy = restart) as the frozen context it designs *around*.
>
> **Frozen-leaf discipline (why a sibling leaf, not new `SecretSpec` fields).** `SecretSpec`'s shape is
> frozen and **owned by spec 05** (shared-vocab §6.1). Adding lifecycle fields to it would *redefine*
> a leaf this dossier only consumes. So — mirroring sibling concern ⑪, which made `InvariantSpec`
> **a new §2.8 leaf, not a `StoreSpec` field**, precisely to avoid mutating a frozen leaf — the
> lifecycle grammar lands as a **new sibling leaf `CredentialSpec`** keyed to `SecretSpec` by
> `config_ref` (the env-var name), leaving `SecretSpec` and shared-vocab §6.1 **untouched**. No §6.1
> amendment and no reconciliation row is required.

---

## 0. The gap in one paragraph (anti-pad — what is already designed vs what is not)

**Already designed / frozen — this dossier does NOT redesign (one line each):** **`SecretSpec.redact`**
already keeps every secret + DSN out of logs / `/metrics` / diagnostics (05 §3.2/§3.8) — the *log-leak*
prevention leg is closed. The **data-plane rail** already makes a leaked prod DSN structurally unable to
*open* prod from a container (no `SB_PROD_ATTEST` + no `RAILWAY_SERVICE_NAME=="worker"` ⇒ `RefuseBoot`,
05 §3.5) — the *blast-radius cap* on the **internal** DSN is closed. **Redaction + rail = prevention;**
the undesigned gap is **recovery** — a credential that is *already out* (exfiltrated by prompt-injection,
committed, logged upstream) has **no rotation cadence, no revocation path an agent may run, and no
compromise-recovery runbook**, and the one action that would kill it (`apiTokenDelete`) sits **under the
Q-0213 `*Delete` ask-first brake** — so recovery today *requires the owner at the worst moment*, the exact
owner-dependency Q-0213 exists to remove. On the supply side, **Dependabot version-update PRs** already run
on the old repo (`.github/dependabot.yml`, weekly) and CLAUDE.md **already states** "pin a new bot-runtime
dep" — but the rule is exhortation: `requirements.txt` ships open `>=` ranges (`asyncpg>=0.29.0`, no ceiling)
with **no lockfile**, so every merge=deploy re-resolves the transitive set with no diff and no review; and
the Dependabot *security-alert* half is still an unconfirmed owner-Settings toggle (dependabot.yml header).
Depth is spent on those two genuine gaps — the **recovery arm** and the **deterministic install** — not on
the prevention legs.

---

## 1. THREAT / FAILURE MODEL

Concrete scenarios, grounded in shipped source / frozen decisions, bounded by the Q-0213 credential set
+ the known Discord-bot + agent-autonomy threat model (no open-ended speculation). "Blast radius" =
who/what is harmed.

### 1.A Exfiltration — a concentrated credential leaves the container

| # | Scenario (who / how) | Blast radius | Grounding |
|---|---|---|---|
| C-1 | Prompt-injection in untrusted guild/DM text steers an agent session to print / exfiltrate an env var (the **Railway account token** or a provider key) | **Account-wide** — the token = 197 mutations incl. `projectDelete`/`volumeDelete`, reads *all* secret values; or spend-drain on the key | Q-0213 concentrates the full-access token + keys in **every** agent container; railway plan §1 (token caps) |
| C-2 | A secret is committed / logged / lands in a public artifact | Credential disclosure of whatever leaked | `SecretSpec.redact` (05 §3.2) closes the log/metric path; the **commit** path (GitHub push-protection / secret-scanning) is an **owner-toggle detection gate**, not yet confirmed enabled (§2.B Detect) |
| C-3 | A leaked **prod DSN** is used against the DB directly | **Split** — the data-plane rail blocks *opening* prod from a container using the **internal** `DATABASE_URL` (05 §3.5); but the **external** `DATABASE_PUBLIC_URL` proxy the backup workflow uses is **uncapped** — a leaked proxy URL reads prod with no structural containment | `.github/workflows/backup-db.yml:7` (pg_dump against `DATABASE_PUBLIC_URL`, a GitHub repo secret) |
| C-4 | The agent-container `DISCORD_BOT_TOKEN_PRODUCTION` value leaks | **test-only** — a deliberate blast-reducer: the concentrated agent-container value is the **test** bot ("Galaxy Bot" `1298426054636994611`); the **worker's** same-named var holds the real prod token | Q-0213 item 2 (env var "misleadingly named"); `disbot/config.py:19` (`DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN_PRODUCTION")`) |

### 1.B No kill-path — the recovery gap (the core of #10)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| K-1 | A credential is **known-leaked** and no rotation/revocation contract exists — the leaked copy stays valid **indefinitely** | Unbounded exposure window | railway plan §1: account token has **no TTL, no expiry**; "rotation is a human discipline, not a feature" |
| K-2 | The one recovery action — **revoke** the leaked token (`apiTokenDelete`) — sits under the Q-0213 `*Delete` ask-first brake, so compromise-recovery **waits on the owner** | Recovery latency = owner availability; owner-dependency re-introduced at compromise-time | Q-0213 item 4 (`*Delete` ask-first) ∩ railway plan §1 (`apiTokenDelete` in the destructive set) |
| K-3 | Rotating the **root credential** (the account token) can't be fully autonomous — it is the container's own authorization root; who/when is undesigned | The highest-blast credential is the least-rotated | railway plan §1 (account token is the container's provisioning root) |

### 1.C Supply chain — unreviewed code enters prod (#12)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| S-1 | A floating `>=` dep re-resolves to a **new / compromised upstream release on the next unrelated merge=deploy** — no lockfile, no diff, no pin ceiling | Arbitrary third-party code in prod on any redeploy | `requirements.txt` (12 deps; `asyncpg>=0.29.0`, `aiohttp>=3.14.1`, `PyYAML>=6.0`, `python-dotenv`, `psutil`, `python-json-logger`, `prometheus-client` — **7 open `>=`, no ceiling**); merge=deploy (Q-0193) |
| S-2 | An agent **adopts** a package under Q-0105 "adopt freely" with no lock entry and no reviewable artifact | Unreviewed dep in prod with no diff a later reviewer can see | CLAUDE.md Q-0105 (adopt-freely, no-ask); no lockfile to diff against |
| S-3 | A **known-CVE version** is installed because nothing scans the resolved set before deploy | Known-vulnerable code in prod | no `pip-audit`/advisory gate over the *resolved* set (Dependabot PRs the manifest, not the deploy-time resolution) |

---

## 2. DESIGN RESPONSE

Three artifacts: **(A)** the credential registry + the `CredentialSpec` lifecycle grammar **sibling
leaf**, to **buildable depth**; **(B)** the recovery arm — rotation cadence + revocation kill-path +
compromise runbook, to **decision-ready posture depth** with a buildable cadence checker; **(C)** the
supply-chain posture, buildable for the gates + decision-ready for the Q-0105 composition.

### 2.A The credential registry + the `CredentialSpec` sibling leaf (buildable)

The credential *inventory* is already ~90% declared as the `SecretSpec` subset of `CONFIG_FIELDS`
(05 §3.1) — but a `SecretSpec` declares **presence + redaction**, not **lifecycle**, and some
credentials (the account token, the GitHub token, the public DSN) **never enter the worker's env** so
they are not `SecretSpec`s at all. Rather than mutate the frozen `SecretSpec` leaf (owned by spec 05,
§6.1) the way it would be tempting to, this dossier adds a **new sibling leaf `CredentialSpec`** — the
same discipline concern ⑪ used for `InvariantSpec` — and a **single flat registry** so partitioning is
never an open question: every credential is **exactly one** `CredentialSpec` row.

```python
class RotationPosture(StrEnum):
    MANAGED       = "managed"        # platform rotates it; the arm re-reads (Railway-managed DB creds)
    AUTONOMOUS    = "autonomous"     # a routine re-issues + swaps on a cadence with NO owner touch (leaf creds)
    OWNER_PROMPT  = "owner_prompt"   # cadence exists but the swap needs one irreducible platform/owner step (root creds)
    ON_COMPROMISE = "on_compromise"  # no cadence; rotated only on a compromise signal (low-blast)

class RevocationRef(StrEnum):        # CLOSED kill-path vocabulary — one token per kill mechanism (frozen NOW; §CL-6-note)
    RAILWAY_API_TOKEN_DELETE  = "railway.apiTokenDelete"       # revoke a Railway account API token
    RAILWAY_VAR_ROTATE        = "railway.var_rotate"           # rotate a Railway service/worker variable
    RAILWAY_DB_CRED_ROTATE    = "railway.db_credential_rotate" # rotate Railway-managed Postgres creds
    GITHUB_TOKEN_SETTINGS     = "github.token_settings"        # revoke/reissue a GitHub repo-write token
    GITHUB_SECRET_UPDATE      = "github.secret_update"         # rotate a GitHub Actions repo secret
    DISCORD_RESET_TOKEN       = "discord.reset_token"          # reset a Discord bot token in the dev portal
    ANTHROPIC_CONSOLE         = "anthropic.console"            # revoke/reissue an Anthropic API key
    OPENAI_DASHBOARD          = "openai.dashboard"             # revoke/reissue an OpenAI API key

class BlastTier(IntEnum):            # TOTAL ORDER — higher int = higher blast = earlier in the recovery runbook
    TEST_ONLY    = 0                 # test bot / non-prod — no real-world harm
    SPEND        = 1                 # provider spend-drain, capped by billing limits
    BOT_PRESENCE = 2                 # prod bot online/offline — user-visible outage, no data loss
    CONTROL      = 3                 # dashboard / control-plane write access
    PROD_DATA    = 4                 # read/write against prod data
    ACCOUNT      = 5                 # full platform account — provisioning root, reads all secrets

class CredentialStore(StrEnum):      # where the credential PHYSICALLY lives — the disjoint-partition discriminator
    WORKER_ENV            = "worker_env"             # the prod worker process env — IS a CONFIG_FIELDS SecretSpec
    AGENT_CONTAINER_ENV   = "agent_container_env"    # agent/dev container env — NOT worker config
    GITHUB_ACTIONS_SECRET = "github_actions_secret"  # a GitHub repo Actions secret
    RAILWAY_ACCOUNT       = "railway_account"        # a Railway account-level API token
    GITHUB_APP            = "github_app"             # the GitHub repo-write token
    DISCORD_PORTAL        = "discord_portal"         # a token minted in the Discord developer portal

@dataclass(frozen=True)
class CredentialSpec:                 # NEW leaf sb/spec/credentials.py — a SIBLING of SecretSpec, NOT a field on it
    name: str                         # the credential identity (registry key)
    store: CredentialStore            # where it physically lives — the disjoint discriminator
    config_ref: str | None            # the CONFIG_FIELDS SecretSpec.env_var the WORKER reads it from; None if out-of-band
    rotation: RotationPosture
    cadence_days: int | None          # rotation horizon; non-None ⇔ rotation ∈ {AUTONOMOUS, OWNER_PROMPT}; else None
    revocation_ref: RevocationRef     # the CLOSED kill-path token (membership CI-validated, not free-string)
    blast: BlastTier                  # total-ordered severity — orders the recovery runbook (highest first)

CREDENTIAL_REGISTRY: tuple[CredentialSpec, ...]   # the ONE flat, disjoint credential inventory
```

**The partition is closed, not asserted (closes the SecretSpec-vs-ExternalCredential overlap).** There is
**no** `(SecretSpec ⊂ CONFIG_FIELDS) + EXTERNAL_CREDENTIALS` union to keep disjoint. There is one flat
`CREDENTIAL_REGISTRY`; `config_ref` is the discriminator, with the invariant
**`store == WORKER_ENV ⟺ config_ref is not None`**. A credential the worker reads from its own env (Discord
prod token, `DATABASE_URL`, provider keys, `CONTROL_API_TOKEN`, `SB_PROD_ATTEST`) is a `WORKER_ENV` row whose
`config_ref` names its `SecretSpec.env_var`; a credential no worker/bot process reads as config (Railway
account token, GitHub repo-write token, `DATABASE_PUBLIC_URL`, the agent-container **test** Discord value)
is an out-of-band row with `config_ref = None`. The Discord prod/test split is exactly the Q-0213 item-2
"misleadingly named" case: **one env-var name (`DISCORD_BOT_TOKEN_PRODUCTION`), two physical credentials in
two stores** — the worker row (`config_ref` set, prod value) and the agent-container row (`config_ref=None`,
test value) are two disjoint entries, never one.

`tools/check_credential_lifecycle.py` (CI gate, mirrors `check_metric_cardinality` / concern ⑩'s
`check_data_lifecycle`) asserts, for every `CredentialSpec`:

1. **`revocation_ref` is a `RevocationRef` member** — enum-typed, so a kill-path is *structurally* present
   (no free-string, no empty escape hatch). A secret with no declared kill-path can't be constructed.
2. **`cadence_days is not None ⟺ rotation ∈ {AUTONOMOUS, OWNER_PROMPT}`** (the two *our*-scheduled postures)
   and **`cadence_days is None ⟺ rotation ∈ {MANAGED, ON_COMPROMISE}`** (platform-owned or event-driven —
   no our-side horizon). A cadence posture with no interval, or an event-driven posture with a spurious
   interval, is CI-red.
3. **Machine-completeness both directions:** every non-`None` `config_ref` names an existing
   `CONFIG_FIELDS` `SecretSpec.env_var`, **and** every `SecretSpec` in `CONFIG_FIELDS` is named by exactly
   one `WORKER_ENV` row. A new worker secret cannot be added without a lifecycle row, and no lifecycle row
   can dangle a config that doesn't exist.

This makes the inventory *machine-complete*: a new credential cannot be added without stating where it
lives, how it is rotated (posture + horizon), and how it is revoked (a closed kill-path token).

> **Non-credential identity config is deliberately excluded.** `BOT_OWNER_USER_ID` (`config.py:40`,
> `type=INT`, **not** a `SecretSpec` — a public Discord user id, not redacted) is **not** in
> `CREDENTIAL_REGISTRY`. It is neither a `SecretSpec` nor an out-of-band credential; it has no meaningful
> kill-path (it is *not secret* — its integrity comes from being immutable **deploy config** an attacker
> cannot edit, enforced by the config grammar's `FAIL_FAST` posture, ⑥ §6.2, not by rotation). Putting it
> in the registry would force a fake `revocation_ref`/`blast` that either defeats the gate ("n/a" passes)
> or breaks the row. Excluding it keeps the gate's rule uniform: **every registry row has a real kill-path.**

**The concentrated set, as registry rows (grounded; `config_ref` verified against `disbot/config.py`):**

| Credential (`name`) | `store` | `config_ref` | `blast` | root/leaf | `rotation` | `cadence_days` | `revocation_ref` |
|---|---|---|:--:|:--:|:--:|:--:|---|
| Railway account token | `railway_account` | — | `ACCOUNT` | **root** | `OWNER_PROMPT` | 180 | `railway.apiTokenDelete` (brake-adjacent → §2.B CL-2) |
| GitHub repo-write token | `github_app` | — | `CONTROL` | **root** | `OWNER_PROMPT` | 180 | `github.token_settings` |
| `DATABASE_URL` (prod DSN) | `worker_env` | `DATABASE_URL` | `PROD_DATA` (rail-capped) | leaf | `MANAGED` | — | `railway.db_credential_rotate` |
| `DATABASE_PUBLIC_URL` | `github_actions_secret` | — | `PROD_DATA` (**uncapped** proxy) | leaf | `AUTONOMOUS` | 90 | `github.secret_update` |
| Discord **prod** bot token | `worker_env` | `DISCORD_BOT_TOKEN_PRODUCTION` | `BOT_PRESENCE` | leaf | `ON_COMPROMISE` | — | `discord.reset_token` |
| Discord **test** value (agent container) | `agent_container_env` | — | `TEST_ONLY` | leaf | `ON_COMPROMISE` | — | `discord.reset_token` |
| `OPENAI_API_KEY` | `worker_env` | `OPENAI_API_KEY` | `SPEND` | leaf | `AUTONOMOUS` | 90 | `openai.dashboard` |
| `ANTHROPIC_API_KEY` | `worker_env` | `ANTHROPIC_API_KEY` | `SPEND` | leaf | `AUTONOMOUS` | 90 | `anthropic.console` |
| `CONTROL_API_TOKEN` | `worker_env` | `CONTROL_API_TOKEN` | `CONTROL` | leaf | `AUTONOMOUS` | 90 | `railway.var_rotate` |
| `SB_PROD_ATTEST` | `worker_env` | `SB_PROD_ATTEST` | `PROD_DATA` (open-gate) | leaf | `AUTONOMOUS` | 90 | `railway.var_rotate` |

- **`cadence_days` defaults (leaf 90 / root 180) are ops-tunable constants, not a fork** — buildable
  defaults `check_rotation_due` can act on immediately; ops may tune them per row without a design change.
- **`SB_PROD_ATTEST` is now a constructible row** (was prose `rotation='folds into SF-d'`): its *rotation*
  is `AUTONOMOUS` — the value is a presence gate (05 §6.3: presence = attestation, value never checked), so
  refreshing it is a safe worker-var swap that preserves presence. Its **durable custody *source*** (plain
  env vs sealed vs OIDC) remains the **owner-gated SF-d fork** (shared-vocab §⑧) — the fold (CL-5) homes the
  *rotation row* here but **carries that owner call forward unresolved**, it does not decide it.

### 2.B The recovery arm — cadence · revocation · runbook (decision-ready posture)

**The design invariant (how it stays owner-independent):** *leaf* credentials are rotated/revoked **fully
autonomously — the root token authorizes it**; only the *root* credential (the account/GitHub token that
provisions the containers) keeps a **single irreducible owner-touch**, because you cannot autonomously
re-inject the credential that *is* your own authorization root into future container provisioning. Even
that is a **scheduled prompt**, not an operational dependency — routine work never blocks on it.

**(1) Rotation cadence — tiered by root/leaf, restart-aware:**

| Tier | Credentials | Cadence mechanic | Owner touch |
|---|---|---|---|
| **Leaf** | provider keys · `CONTROL_API_TOKEN` · `DATABASE_PUBLIC_URL` · `SB_PROD_ATTEST` (`DATABASE_URL` = `MANAGED`, Railway rotates) | a **scheduled cadence routine** (mirrors the reconciliation routine) that only **detects** due (`check_rotation_due`) and **arms a DURABLE `OneShot` `ManagedTaskSpec` on 09's due-queue** (§2.B(1a)) — it does **not** swap inline. The durable one-shot runs the resumable re-issue → swap store var → **read-back verify the POST-boot instance** → `last_rotated_at`, so a crash mid-swap is boot-reconciled (below) | **none** |
| **Root** | Railway account token · GitHub token | same routine **detects age** (past `cadence_days`) and **prompts** the owner (one platform step: re-provision the container secret) | **one scheduled prompt** (irreducible) |

**Restart-safety — WORKER_ENV rotation is a DURABLE due-queue one-shot, not an inline routine (Q-0193 /
shared-vocab §④ + §⑤.1 item 3; 09 §3.7).** Swapping a **`WORKER_ENV`** credential is a Railway variable
change, which **auto-redeploys the worker** — the same *deploy = restart* semantics as merge=deploy
(Q-0193). A swap therefore **restarts the very process performing the swap**, mid-rotation. A *routine*
fired on a cadence is **not** a durable timer and gets **no** boot-reconcile — that was the sweep gap: the
earlier draft claimed "re-armed by boot-reconcile" for something the due-queue never persists (a routine is
a producer, not a `sb_due_queue` row). So the rotation is split into a detector and a durable executor:

**(1a) The cadence routine DETECTS; a durable one-shot EXECUTES — so boot-reconcile literally applies.**
`check_rotation_due` (the scheduled routine, §2.B(1)) only *detects* a due `WORKER_ENV` credential and
**arms a `TaskDurability.DURABLE` `OneShot` `ManagedTaskSpec` on 09's due-queue** —
`arm_one_shot(rotation_spec, fire_at=now, payload={"name": name, "horizon_epoch": h})` (09 §3.7; the routine
is the *producer*, exactly the producer-arms-one-shot path 09 §3.7 names). Being a **`DURABLE` `sb_due_queue`
row** is what makes **09's `reconcile_on_boot` literally apply** (the correct cite — *not* a routine re-arm):
a one-shot interrupted by the redeploy it triggers is left `pending`/overdue, and 09's boot-reconcile
re-claims + re-fires it **after `/ready` 200 (RUNNING)** (vocab §⑤.1 item 3 — never against a DB the
readiness gate would 503, 05 §3.8). This is the restart-safety the inline routine never actually had.

**(1b) A distinguished externally-effecting one-shot — NOT a pure-DB `_fire_one` fire.** A vanilla due-queue
fire is pure-DB and commits `once()` + effect + `record_outcome` + `mark_fired` in **one** txn (09 §3.4
`atomic_db_only`, §3.7 `_fire_one`). Credential rotation cannot: its effect is **external** (a provider
re-issue + a var-swap that restarts the worker), so it is **exempt** from the pure-DB scheduler-fire fence
and does **not** ride `_fire_one`'s single-shared-txn commit-together guarantee. It rides only the
due-queue's **durable timer + `reconcile_on_boot` + the deterministic `once()` key**, and runs its own
**resumable, multi-txn protocol** over the rotation ledger. Its idempotency key is **horizon-stable, not
timer-instance-stable**: `IdempotencyKey(namespace="credential.rotation", guild_id=0,
dedup_token=f"{name}:{horizon_epoch}")` (**not** 09's default `task_id:fire_epoch`) — so a duplicate arm
(e.g. both instances detect due during a deploy overlap) **and** a boot-reconcile re-fire **both resolve to
the same guard row** and RESUME, never mint a second credential. The fire runs headless as `SYSTEM_ACTOR`
(`actor_type="system"` ⇒ authority scripted-bypass, 09 §3.7 / PIN-3); any fire exception classifies through
`from_exception(exc, surface=Surface.MAINTENANCE, target=None)` (09 §3.8 / PIN-4 — the one background
`Surface`, no interaction target).

**(1c) The intermediate ledger state — the issued-but-unverified recovery (closes the mid-flight `once()`
gap).** Because the effect is external and the swap restarts the process **before** any single txn could
commit `once()`+outcome together, the rotation ledger carries a per-`(name, horizon_epoch)` **`phase`**
column — a small closed state machine committed across three txns:

| `phase` | Committed when | Meaning |
|---|---|---|
| `RESERVED` | txn-1: `once(key)` inserts the guard row (outcome **NULL / pending**) **and** the ledger row, *before* any external call | we own this horizon; nothing issued yet |
| `ISSUED_PENDING_VERIFY` | txn-2: after the provider re-issue succeeds and the store var is swapped — records the new credential's **non-secret identity / fingerprint** + `issued_at` (the secret value goes to the store var, never the ledger) | issued + swapped, not yet verified — the state the swap-redeploy leaves behind |
| `VERIFIED` | txn-3 (post-boot): read-back against the `/ready`-200 instance confirms the new credential serves → sets `last_rotated_at`, `record_outcome(key, DONE)`, then `mark_fired`→DELETE the one-shot | terminal success |
| `FAILED` | any phase, non-retryable | terminal; operator finding (09 §3.8 error routing) |

**Re-run rule (makes the crash-retry well-defined instead of undefined).** When `reconcile_on_boot` / `tick`
re-fires the still-pending one-shot after the swap-redeploy:

- `once(key)` → **False** (the guard row committed at `RESERVED`) ⇒ do **not** re-enter as a fresh rotation.
- `read_outcome(key)` → **outcome is `None` (pending)** — the vocab §④ *"reproduce … may be None if still
  mid-flight"* case, which a pure-DB `_fire_one` never hits but this external fire is the *norm* for. So
  instead of an **undefined** `_reproduce(None)`, the handler LOADS the ledger `phase` and RESUMES:
  - `phase == ISSUED_PENDING_VERIFY` (the expected restart landing): the credential is already issued +
    swapped ⇒ **skip re-issue**, run only the **read-back / verify** against the post-boot instance →
    `VERIFIED` + `record_outcome(DONE)` + `last_rotated_at`. **This is the issued-but-unverified recovery —
    the re-run *completes the verify*; it does not mint a second credential and is no longer undefined.**
  - `phase == RESERVED` (crashed after the guard commit but before an issuance was confirmed): no confirmed
    issuance ⇒ query the provider for an issuance already tagged with this horizon's `dedup_token` and adopt
    it, else issue now → `ISSUED_PENDING_VERIFY` → verify. The Revoke step (§2.B(2)) kills any orphaned
    partial copy, so no horizon ever leaves two live credentials.
  - outcome already set (`phase == VERIFIED`) ⇒ reproduce / no-op → `mark_fired`.

Non-`WORKER_ENV` rotations (GitHub Actions secret, account token, provider console) do **not** restart the
worker; they still arm a durable one-shot for uniform boot-reconcile, but their read-back is a
**synchronous** direct provider-API check inside the same fire, guarded by the same horizon-stable `once()` —
no `ISSUED_PENDING_VERIFY` resume is needed because no self-restart splits the fire.

`scripts/check_rotation_due.py` (mirrors `check_reconciliation_due.py`) joins `CREDENTIAL_REGISTRY`'s static
`cadence_days` against the rotation ledger's `last_rotated_at` (the routine writes it on each rotation —
§2.B(3) Post-mortem; ledger home is the routine's saved state, analogous to the `Last reconciliation pass:
#N` marker, durable-store wiring at CUT-1) and flags any row where `last_rotated_at + cadence_days < now`
(or a never-rotated row older than `cadence_days` since first-seen). Rows with `cadence_days is None`
(`MANAGED`/`ON_COMPROMISE`) are skipped — they have no our-side horizon. On a due leaf the routine **arms a
DURABLE due-queue one-shot** (§2.B(1a), which carries the restart-safe execution + verify); on a due root it
**prompts** the owner.

**(2) Revocation kill-path — the carve-out that makes compromise-recovery autonomous (§4 CL-2):** the
Q-0213 brake forbids `*Delete`/`*Restore` because they **lose data**. A **credential revoke loses no
data** — it is the *opposite* of destructive; it *prevents* loss. The `*Delete` pattern over-captures
`apiTokenDelete`. Recommend narrowing the brake: **credential revocation** (the `RevocationRef` closed set —
`apiTokenDelete`, Discord reset, provider revoke, DB-credential rotate) is a **recovery action,
agent-runnable**; **resource deletion** (`projectDelete`/`serviceDelete`/`volumeDelete`/`environmentDelete`/DB
drop) stays ask-first. Without this carve-out, K-2 stands: leaf revocation stalls on the owner.

**(3) Compromise-recovery runbook — two orderings, both now well-defined (buildable procedure):** the five
**steps** below are the per-credential *procedure* order. When **multiple** credentials are compromised at
once, they are triaged **highest-`blast` first** using the `BlastTier` total order
(`ACCOUNT > PROD_DATA > CONTROL > BOT_PRESENCE > SPEND > TEST_ONLY`) — `sorted(compromised, key=lambda c:
c.blast, reverse=True)`.

| Step | Action | Autonomy |
|---|---|---|
| **Detect** | **live now (grounded):** the Railway **$15 soft usage alert** (verified live 2026-07-02 — anomalous spend) + the **deploy webhook to `#railway-alerts`** (verified live 2026-07-02 — unexpected deploy), both per `railway-setup-plan-2026-07-02.md` §Alerts + planning `README.md` + router Q-0213. **This-doc's addition:** `pip-audit` CI gate (§2.C) — known-CVE dep. **Owner-toggle (repo Settings, arm to complete Detect):** GitHub secret-scanning **push-protection** + Dependabot **security alerts** (both a Settings enable, dependabot.yml header) | live-passive · toggle = one owner action |
| **Contain** | **per-credential — not a blanket claim.** `DATABASE_URL` (internal): the data-plane rail structurally caps it (can't open prod from a non-attested container, 05 §3.5) — *this* leaf is contained. **`DATABASE_PUBLIC_URL` (external proxy): NO structural containment** — C-3's uncapped read path — so recovery is **entirely** Rotate+Revoke, making it a **first-priority rotation target**. Account/control/spend leaves have no structural cap either — Rotate+Revoke is their only containment | structural only for the internal-DSN leaf; all others = Rotate+Revoke |
| **Rotate** | `WORKER_ENV`: the **durable due-queue one-shot** (§2.B(1a–1c)) re-issues (leaf: provider API; root: platform step) → swaps the store var → on the swap-triggered redeploy, 09's `reconcile_on_boot` resumes at `ISSUED_PENDING_VERIFY` and **read-back verifies the post-boot instance** (`/ready` 200); the horizon-stable `once()` prevents double-issue. Non-`WORKER_ENV`: synchronous provider re-issue + read-back in-fire | leaf: auto · root: prompt |
| **Revoke** | kill the leaked copy via `revocation_ref` (needs CL-2 carve-out for leaves) | leaf: auto (post-CL-2) |
| **Post-mortem** | confirm prod healthy on new creds; write `last_rotated_at` + an entry to the credential-incident ledger (feeds `check_rotation_due`); if a supply-chain dep, remove/pin it + regenerate the lock (§2.C) | auto |

### 2.C The supply-chain posture — deterministic install (buildable) + the Q-0105 composition

**The single highest-leverage fix is a hash-pinned lockfile:** convert merge=deploy from "re-resolve
latest" (S-1) to "install the exact reviewed set."

| Mechanic | Shape | Closes |
|---|---|---|
| **Lockfile + hashes** | `requirements.lock` from `pip-compile --generate-hashes` (or `uv pip compile`); the container installs `pip install --require-hashes -r requirements.lock`. `requirements.txt` becomes the **human-edited input** (constraints); the lock is the **resolved, hash-verified output** checked in | **S-1** (deploy-time re-resolution) |
| **`check_lockfile_fresh`** CI gate | regenerating the lock from `requirements.txt` yields **no diff**, and every entry is hash-pinned; a drifted lock is CI-red | S-1 · S-2 (forces the lock diff to exist) |
| **`pip-audit`** CI gate | scan the **resolved lock** against the CVE advisory DB; a known-vuln version is a finding | **S-3** |
| **Dependabot/Renovate** | advisory PRs for updates — version-update half **already exists old-repo** (`.github/dependabot.yml`); carry to the new repo; the *security-alert* half is the owner-Settings toggle above | pin-rot downside of pinning |
| **`>=`-ceiling hygiene** | add `<next-major` ceilings to the **7** open `>=` runtime deps (matches the shipped discord.py/openai/anthropic/youtube-transcript-api/Pillow pattern) — a cheap fix-on-sight | S-1 (immediate, pre-lock) |

**Q-0105 composition (the owner-gated DISCUSS, §4 CL-3):** the lockfile does **not** reverse "adopt
freely." Q-0105 already *states* "pin a new bot-runtime dep" — the lockfile is that rule's **enforcement**
("enforce, don't exhort", Q-0132). Adopt-freely = the *decision* to add (still no-ask); the lock = the
*mechanics* of how it lands. An agent adopts → **regenerates the lock in the same PR** → CI verifies fresh
→ **the lock diff IS the reviewable artifact** a later reviewer / another chat / the owner can see. That is
#12's "human review" satisfied as a **deferred, visible** review (the parallel-agent norm), **not** a
blocking live gate — a blocking gate would reintroduce the owner-dependency Q-0213 forbids.

---

## 3. LANDING SITE (so no response can evaporate — V-3)

| Response | Lands exactly at | Cannot evaporate because |
|---|---|---|
| `CredentialSpec` sibling leaf + `RotationPosture`/`RevocationRef`/`BlastTier`/`CredentialStore` + `CREDENTIAL_REGISTRY` | **new leaf `sb/spec/credentials.py`** (a §2.8-style sibling of `SecretSpec`; `SecretSpec`/§6.1 untouched) — Gate-0 grammar | a secret with no declared kill-path/horizon is unconstructible + CI-red |
| `check_credential_lifecycle.py` (kill-path + cadence-consistency + config_ref completeness) | `tools/` CI gate (mirrors `check_metric_cardinality`, `check_data_lifecycle`) | required-check set; a registry entry missing/mismatched a field fails CI |
| Rotation cadence (detect) + `check_rotation_due.py` + the **durable one-shot executor** + the rotation ledger (`last_rotated_at` + `phase`) | detect = a **scheduled routine** in `docs/operations/autonomous-routines.md` + the checker (mirrors the reconciliation routine); execute = a **`DURABLE` `OneShot` `ManagedTaskSpec` on 09's due-queue** (§2.B(1a–1c)); ledger (incl. the `RESERVED`/`ISSUED_PENDING_VERIFY`/`VERIFIED` `phase`) = routine saved state, durable-store at CUT-1 | the checker joins `cadence_days`×`last_rotated_at`, flags overdue, and **arms the one-shot**; 09's `reconcile_on_boot` re-fires a crash-interrupted swap; the `phase` column makes the outcome-pending re-run resume the verify, never double-issue |
| Revocation carve-out (narrows the Q-0213 `*Delete` brake) | a **router DISCUSS Q** → once decided, the runbook + the routine's saved prompt | Q-0213 is a binding owner decision; the narrowing ships with its provenance Q |
| Compromise-recovery runbook (blast-ordered triage + 5-step procedure) | **new ops doc `docs/operations/credential-lifecycle.md`** + cross-ref from `production-deployment.md` §Backups (which already homes the DR runbook) | it is the routine's saved procedure; the routine can't run without it |
| Lockfile + `check_lockfile_fresh` + `pip-audit` | the new repo's `requirements.lock` + `.github/workflows` gate + `tools/check_lockfile_fresh.py` — Gate-0 | a non-fresh / vuln lock is CI-red before deploy |
| Q-0105 composition (lock diff = deferred review) | a **router DISCUSS Q** + a proposed **CLAUDE.md rider** (proposed, not self-applied) | rule changes are router-proposed per CLAUDE.md; the rider ships with its Q |
| `SB_PROD_ATTEST` rotation-row fold-in (SF-d custody source carried forward as an open call) | consolidated INTO this registry's `SB_PROD_ATTEST` row; the **custody-source** stays SF-d owner-gated | one home for "how is each secret rotated"; the owner custody call is not silently absorbed |

---

## 4. OWNER-GATED?

Per response: decide-able by design (recommended default, flagged) vs a genuine owner-only call (options +
recommendation only). Q-0213 + Q-0105 are **binding owner decisions** → anything that touches them is
**proposed, not self-applied** (router DISCUSS).

| ID | Decision | 🔒? | Options | Recommendation |
|---|---|:--:|---|---|
| **CL-1** | A credential-lifecycle **recovery arm** at all? (touches the Q-0213 concentration) | 🔒 owner | (a) full arm: registry + tiered cadence + revocation carve-out + runbook · (b) runbook only, no cadence · (c) none (accept the no-kill-path risk) | **(a)** — a recovery arm is **orthogonal** to Q-0213: Q-0213 declined *scoping/custody* (keep creds concentrated), it did not decline *recovery*. This **removes** owner-dependency at compromise-time (K-2), the opposite of what Q-0213 guards against |
| **CL-2** | **Revocation carve-out** — narrow the Q-0213 `*Delete` brake to exclude credential revoke? | 🔒 owner | (a) credential revoke (the `RevocationRef` closed set) = agent-runnable recovery; **resource** delete stays ask-first · (b) keep all `*Delete` ask-first (recovery waits on owner) | **(a)** — a token revoke **loses no data**; the brake's intent (Q-0213 item 4) is *data-loss*, and its `*Delete` pattern over-captures `apiTokenDelete`. Route as DISCUSS (narrows a Q-0213 brake) |
| **CL-3** | **Supply-chain**: lockfile + hash-verify + `pip-audit` CI gate vs the Q-0105 adopt-freely grant | 🔒 owner | (a) lockfile + CI gate; adopt-freely (no-ask) **unchanged**, the lock diff is the deferred-review artifact · (b) blocking human-review on every dep add (reintroduces owner-dependency — rejected vs Q-0213) · (c) status quo (floating `>=`, no lock) | **(a)** — it **enforces the runtime-pin rule Q-0105 already states**; composes with adopt-freely (adopt → regenerate lock → CI verifies). Route as DISCUSS (touches Q-0105 binding) |
| **CL-5b** | **`SB_PROD_ATTEST` durable custody *source*** (folded here from SF-d): plain env `SecretSpec` vs sealed/managed secret vs short-lived OIDC claim | 🔒 owner | (a) presence-gated env `SecretSpec` (built default, the 4th rail is correct today) · (b) sealed/managed secret · (c) short-lived OIDC claim | **defer to owner** — this is shared-vocab §⑧ **SF-d**, genuinely owner-gated. The fold (CL-5) homes the *rotation row* in this registry; it does **not** decide the custody source. Carried forward unresolved |
| **CL-4** | `CredentialSpec` sibling leaf + `check_credential_lifecycle` gate | arch (design) | — | **Adopt** — mirrors concern ⑪'s sibling-leaf discipline (`InvariantSpec`, not a `StoreSpec` field) + concern ⑩'s `check_data_lifecycle` gate; leaves `SecretSpec`/§6.1 frozen; a secret with no kill-path is a completeness bug. *Decided by design (flagged).* |
| **CL-5** | Fold **SF-d**'s `SB_PROD_ATTEST` **rotation row** into this contract as one credential-lifecycle home (custody source → CL-5b) | arch (design) | — | **Fold** — the rotation posture/kill-path belong in one registry; the owner-gated *custody source* is split out to **CL-5b** and carried forward, not decided here. *Decided by design (flagged).* |
| **CL-6** | `>=`-ceiling hygiene on the 7 open runtime deps + freeze the `RevocationRef` closed vocab now | arch (design) | — | **Adopt** — ceilings match the shipped discord.py/openai/anthropic/youtube-transcript-api/Pillow pattern (old-repo fix-on-sight, noted); the closed `RevocationRef` set is frozen now so the CI gate validates *membership* even though token→API dispatch is deferred to CUT-1. *Decided by design (flagged).* |

---

## 5. RETIREMENT MAP (FJ L-rows / §4 gaps / owner-queue closed or advanced)

| Item | What it was | How this dossier closes / advances it |
|---|---|---|
| **FJ §4 #10** (Gate-0-bound) | "Credential lifecycle — no rotation/revocation/compromise-recovery contract for the token/DSN/Railway creds Q-0213 concentrates in agent containers" | **RETIRED (design):** the recovery arm (§2.B — tiered cadence + `check_rotation_due` + revocation carve-out + blast-ordered compromise runbook) + the `CredentialSpec` sibling leaf + `check_credential_lifecycle` (§2.A). The owner-independence invariant (leaves auto, root = one irreducible prompt) is the design's spine. Owner legs **CL-1/CL-2** flagged |
| **FJ §4 #12** (Gate-0-bound) | "Dependency supply chain — 12 floating `>=` deps, no lockfile, re-resolved every merge=deploy, agents licensed to adopt, **no human review**; carried into the new repo with zero disposition" | **RETIRED (design):** the deterministic posture (§2.C — lockfile + hashes + `check_lockfile_fresh` + `pip-audit` + Dependabot carry-forward + `>=`-ceilings). The Q-0105 composition (**lock diff = deferred review**) is the "human review" leg — **wholly #12's**, no double-count with L-21. Owner leg **CL-3** flagged |
| **L-21** (⑂ owner, §2) | **Real two legs:** (a) no CI guard write-protects the frozen capstone/decision logs against always-on autonomous agents; (b) no policy governs old-bot feature drift away from the 271-command corpus/goldens/import-mappings | **NOT this dossier's — owned elsewhere, noted for the reviewer.** The frozen-path CI guard is a Gate-0 item (FJ §3.5); the old-bot corpus policy is a Stage-3 consolidation line (FJ §3 "what can wait"). **L-21 has *no* supply-chain / dependency / human-review leg** — that concern is entirely #12's (row above). (An earlier draft of this dossier mis-booked a fabricated "L-21 supply-chain-review leg"; corrected — the row is removed and the supply-chain retirement is credited only to #12.) |
| **New owner-queue rows CL-1 / CL-2 / CL-3 / CL-5b** | §4 gaps #10/#12 had **no** owner-queue row in FJ §6 (they were §4 completeness misses); SF-d custody is an existing §⑧ fork | **GRADUATED** into owner-decidable rows with options+recommendation — the same §4-gap → owner-decision move concern ⑩ made for L-19→T-1; CL-5b carries the SF-d custody fork forward |
| **SF-d** (vocab §⑧ / 05 §9) | `SB_PROD_ATTEST` durable-custody, owner-gated | **CONSOLIDATED (CL-5) + CARRIED FORWARD (CL-5b):** the rotation row folds into the registry; the owner-gated custody *source* is split out to CL-5b and left for the owner, not absorbed as design-decided |

**Cross-reference (composition, not double-claim):** concern ⑩'s **class-13 probes N-1 (credential
lifecycle) / N-2 (supply chain)** are the **standing lens** that catches a *regression* forward (43× in
Stage-2, once in the Phase-B pass); **this dossier is the mechanic that lens asserts exists.** ⑩ explicitly
deferred the *fix* to a Gate-0 item — this is it. The `check_credential_lifecycle` gate is the sibling of
⑩'s `check_data_lifecycle` (⑩ built the retention/erasure leaf-fields + gate on `StoreSpec`; this builds the
credential lifecycle as a **sibling leaf**, the ⑪ discipline).

---

## 6. DEFERRALS (labeled with reason)

| Deferral | Reason | Bound |
|---|---|---|
| The rotation **execution wiring** (concrete Railway/provider/Discord API calls + read-back) + the durable **rotation-ledger table** (`last_rotated_at` + `phase`) | The *grammar* + *cadence posture* + *runbook* + the **durable-one-shot arming on 09's due-queue**, the **`RESERVED`/`ISSUED_PENDING_VERIFY`/`VERIFIED` phase state machine**, and the **horizon-stable `once()` + outcome-pending resume rule** are all designed here (§2.B(1a–1c)); only the concrete provider/Railway API bindings + the physical ledger table are ops build, same tier as SF-d custody | **CUT-1** ops setup |
| `RevocationRef` **token → concrete API dispatch** map | The closed *vocabulary* is frozen now (so the gate validates membership); binding each token to its provider call is ops wiring | CUT-1 (with the rotation wiring) |
| The compromise **detection anomaly-model** beyond the live/toggle signals (usage alert + deploy webhook live; secret-scanning + Dependabot alerts = owner-toggle) | A richer anomaly model (e.g. per-key spend baselining) is ops observability, not a foundational rail | ops observability (bounded) |
| **FJ §4 #11** — prod-data copies in agent containers (restored snapshots, LLM-judge replays) retention/erasure | Distinct concern (data-subject erasure, not credential rotation); it is concern ⑩'s **class-12 R-2** probe + a Gate-0/CUT fix. *Note:* #10 and #11 share the same Q-0213 container, so the recovery arm's detection **helps**, but erasure is #11's home | Gate-0 / CUT-2 (concern ⑩ / ⑪) |
| The **old-repo** `requirements.txt` `>=`-ceiling fix (CL-6) | This is a docs-only design pass; ceilings on the shipped file are a cheap fix-on-sight the owner/next session can take | fix-on-sight (noted) |

No open-ended speculation — every threat is grounded in a shipped credential, a frozen decision (Q-0213 /
Q-0105 / Q-0193), or a verified file/doc (`requirements.txt`, `backup-db.yml`, `config.py:19/40`,
`dependabot.yml`, `railway-setup-plan-2026-07-02.md` §Alerts). Every "already live" Detect signal names its
grounding doc; every owner-toggle signal is labeled as such (not "already wired"); and every deferral names
its owning phase within the corpus.

---

*Authored 2026-07-04 for the strand-3 cross-cutting concerns; revised same day to close the design-critic
findings (sibling-leaf grammar, disjoint registry, closed `RevocationRef`/`BlastTier`, `cadence_days`
horizon + `check_rotation_due` join, per-credential Contain, L-21
mis-cite removed, Detect signals grounded/toggle-split, `BOT_OWNER_USER_ID` excluded, SF-d custody carried
forward as CL-5b); reconciled same day against the strand seam-pass — WORKER_ENV rotation re-based from an
inline routine onto a **DURABLE `OneShot` `ManagedTaskSpec` on 09's due-queue** so 09's `reconcile_on_boot`
(vocab §⑤.1 item 3) *literally* applies, with a `RESERVED`/`ISSUED_PENDING_VERIFY`/`VERIFIED` ledger `phase`
+ horizon-stable `once()` giving the issued-but-unverified re-run a defined resume (was the mid-flight
`once()`-pending gap), and the `§⑤.3` boot-reconcile mis-cite corrected. Consumes `shared-vocabulary.md` (⑥ config/secret grammar; §④/§⑤ idempotency+restart) +
spec 05 (§3.1/§3.2/§3.5/§6.3) + concern ⑩ (class-13 N-1/N-2, `check_data_lifecycle`) + concern ⑪
(sibling-leaf discipline). Spot-verified this session against shipped source / frozen decisions:
`requirements.txt` (12 deps, 7 open `>=`, no lockfile), `.github/workflows/backup-db.yml:7`
(`DATABASE_PUBLIC_URL` GitHub repo secret), `.github/dependabot.yml` (version-updates only; alert half an
owner toggle), `disbot/config.py:19` (`DISCORD_BOT_TOKEN_PRODUCTION`), `:40` (`BOT_OWNER_USER_ID`),
`:185-186` (`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`), router Q-0213 (concentration + `*Delete` brake),
`railway-setup-plan-2026-07-02.md` §Alerts (soft $15 usage alert + `#railway-alerts` deploy webhook, verified
live 2026-07-02), FJ L-21 (frozen-doc + corpus-drift legs, no supply-chain leg). `sb/` re-confirmed
design-only (no files). **NOT SOURCE OF TRUTH for runtime** — a design contract; source wins (Q-0120).*
</content>
</invoke>
