# Strand 3 · Cross-cutting concern ⑫ — Credential lifecycle + dependency supply-chain posture

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B **design contract** for one never-surfaced
> foundational concern: Q-0213 deliberately **concentrated** the full-access Railway account token,
> the prod DSN, the Discord + provider tokens, and the GitHub repo-write token in agent containers so
> the project runs owner-independently — but shipped **nothing** for what happens when one of those
> credentials leaks, ages, or must be killed (FJ §4 **#10**). In parallel the runtime carries **12
> floating `>=` runtime deps, no lockfile, re-resolved on every merge=deploy**, with agents licensed
> to adopt packages under Q-0105 and no review gate (FJ §4 **#12** / **L-21** supply-chain leg). This
> dossier designs **the minimum recovery arm that does not reintroduce owner-dependency** (a credential
> registry + tiered rotation cadence + a revocation kill-path + a compromise-recovery runbook) and the
> **deterministic supply-chain posture** (lockfile + hash-verify + advisory scan) that composes *with*
> the Q-0105 adopt-freely grant instead of reversing it. **Precedence:** shipped source & merged PRs
> win (Q-0120); the five strand-1 specs + `shared-vocabulary.md` win for shapes they own; this dossier
> owns only the lifecycle grammar leg + the two postures. It authors no `disbot/` and no `sb/` code.
>
> **Consumes (does NOT redefine):** the config/secret grammar `SecretSpec` + `CONFIG_FIELDS` +
> `SecretSpec.redact` + the data-plane rail (⑥ / spec 05 §3.1–3.5); the security-abuse **class-13**
> probes N-1 (credential lifecycle) / N-2 (supply chain) from concern ⑩ — this dossier is the **fix**
> that class-13's **lens** asserts exists. It **consumes** Q-0213 (the concentration decision — NEVER
> reversed here) and Q-0105 (the adopt-freely grant) as the frozen context it designs *around*.

---

## 0. The gap in one paragraph (anti-pad — what is already designed vs what is not)

**Already designed / frozen — this dossier does NOT redesign (one line each):** **`SecretSpec.redact`**
already keeps every secret + DSN out of logs / `/metrics` / diagnostics (05 §3.2/§3.8) — the *log-leak*
prevention leg is closed. The **data-plane rail** already makes a leaked prod DSN structurally unable to
*open* prod from a container (no `SB_PROD_ATTEST` + no `RAILWAY_SERVICE_NAME=="worker"` ⇒ `RefuseBoot`,
05 §3.5) — the *blast-radius cap* on the DSN is closed. **Redaction + rail = prevention;** the
undesigned gap is **recovery** — a credential that is *already out* (exfiltrated by prompt-injection,
committed, logged upstream) has **no rotation cadence, no revocation path an agent may run, and no
compromise-recovery runbook**, and the one action that would kill it (`apiTokenDelete`) sits **under the
Q-0213 `*Delete` ask-first brake** — so recovery today *requires the owner at the worst moment*, the exact
owner-dependency Q-0213 exists to remove. On the supply side, **Dependabot** already runs on the old repo
(advisory PRs) and CLAUDE.md **already states** "pin a new bot-runtime dep" — but the rule is exhortation:
`requirements.txt` ships open `>=` ranges (`asyncpg>=0.29.0`, no ceiling) with **no lockfile**, so every
merge=deploy re-resolves the transitive set with no diff and no review. Depth is spent on those two
genuine gaps — the **recovery arm** and the **deterministic install** — not on the prevention legs.

---

## 1. THREAT / FAILURE MODEL

Concrete scenarios, grounded in shipped source / frozen decisions, bounded by the Q-0213 credential set
+ the known Discord-bot + agent-autonomy threat model (no open-ended speculation). "Blast radius" =
who/what is harmed.

### 1.A Exfiltration — a concentrated credential leaves the container

| # | Scenario (who / how) | Blast radius | Grounding |
|---|---|---|---|
| C-1 | Prompt-injection in untrusted guild/DM text steers an agent session to print / exfiltrate an env var (the **Railway account token** or `OPENAI_API_KEY`) | **Account-wide** — the token = 197 mutations incl. `projectDelete`/`volumeDelete`, reads *all* secret values; or spend-drain on the key | Q-0213 concentrates the full-access token + keys in **every** agent container; railway plan §1 (token caps) |
| C-2 | A secret is committed / logged / lands in a public artifact | Credential disclosure of whatever leaked | `SecretSpec.redact` (05 §3.2) closes the log/metric path; the **commit** path (GitHub push-protection / secret-scanning) is an **undesigned detection gate** |
| C-3 | A leaked **prod DSN** is used against the DB directly | **Capped** — the data-plane rail blocks *opening* prod from a container (05 §3.5); but the DSN still grants read via the **`DATABASE_PUBLIC_URL` external proxy** the backup workflow already uses | `.github/workflows/backup-db.yml:7` (pg_dump against `DATABASE_PUBLIC_URL`, a GitHub repo secret) |
| C-4 | The agent-container `DISCORD_BOT_TOKEN_PRODUCTION` leaks | **test-only** — a deliberate blast-reducer: the concentrated Discord token is the **test** bot ("Galaxy Bot" `1298426054636994611`); the real prod token lives in **worker vars, not agent containers** | Q-0213 item 2 (verbatim: env var "misleadingly named") |

### 1.B No kill-path — the recovery gap (the core of #10)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| K-1 | A credential is **known-leaked** and no rotation/revocation contract exists — the leaked copy stays valid **indefinitely** | Unbounded exposure window | railway plan §1: account token has **no TTL, no expiry**; "rotation is a human discipline, not a feature" |
| K-2 | The one recovery action — **revoke** the leaked token (`apiTokenDelete`) — sits under the Q-0213 `*Delete` ask-first brake, so compromise-recovery **waits on the owner** | Recovery latency = owner availability; owner-dependency re-introduced at compromise-time | Q-0213 item 4 (`*Delete` ask-first) ∩ railway plan §1 (`apiTokenDelete` in the destructive set) |
| K-3 | Rotating the **root credential** (the account token) can't be fully autonomous — it is the container's own authorization root; who/when is undesigned | The highest-blast credential is the least-rotated | railway plan §1 (account token is the container's provisioning root) |

### 1.C Supply chain — unreviewed code enters prod (#12 / L-21 leg)

| # | Scenario | Blast radius | Grounding |
|---|---|---|---|
| S-1 | A floating `>=` dep re-resolves to a **new / compromised upstream release on the next unrelated merge=deploy** — no lockfile, no diff, no pin ceiling | Arbitrary third-party code in prod on any redeploy | `requirements.txt` (12 deps; `asyncpg>=0.29.0`, `aiohttp>=3.14.1`, `PyYAML>=6.0`, `python-dotenv`, `psutil`, `python-json-logger`, `prometheus-client` all **open `>=`, no ceiling**); merge=deploy (Q-0193) |
| S-2 | An agent **adopts** a package under Q-0105 "adopt freely" with no lock entry and no reviewable artifact | Unreviewed dep in prod with no diff a later reviewer can see | CLAUDE.md Q-0105 (adopt-freely, no-ask); no lockfile to diff against |
| S-3 | A **known-CVE version** is installed because nothing scans the resolved set before deploy | Known-vulnerable code in prod | no `pip-audit`/advisory gate over the *resolved* set (Dependabot PRs the manifest, not the deploy-time resolution) |

---

## 2. DESIGN RESPONSE

Three artifacts: **(A)** the credential registry + the `SecretSpec` lifecycle grammar leg, to **buildable
depth** (mirrors `StoreSpec.retention` / `SecretSpec.redact`); **(B)** the recovery arm — rotation cadence
+ revocation kill-path + compromise runbook, to **decision-ready posture depth**; **(C)** the supply-chain
posture, buildable for the gates + decision-ready for the Q-0105 composition.

### 2.A The credential registry + `SecretSpec` lifecycle grammar leg (buildable)

The credential *inventory* is already 90% declared: it is the `SecretSpec` subset of `CONFIG_FIELDS`
(05 §3.1). The gap is that a `SecretSpec` declares **presence + redaction** but **not its lifecycle**.
Extend it with three [S] fields — the same move concern ⑩ made adding `retention` to `StoreSpec`:

```python
class RotationPosture(StrEnum):
    MANAGED     = "managed"        # platform rotates it; the arm re-reads (Railway-managed DB creds)
    AUTONOMOUS  = "autonomous"     # a routine re-issues + swaps on a cadence with NO owner touch (leaf creds)
    OWNER_PROMPT= "owner_prompt"   # cadence exists but the swap needs one irreducible platform/owner step (root creds)
    ON_COMPROMISE = "on_compromise"# no cadence; rotated only on a compromise signal (low-blast)
    STATIC      = "static"         # deliberately never rotated (owner id; not a rotatable secret)

@dataclass(frozen=True)
class SecretSpec(ConfigSpec):      # already type=SECRET, redact=True (05 §3.2) — gains the lifecycle triple
    rotation: RotationPosture = RotationPosture.ON_COMPROMISE   # [S]
    revocation_ref: str = ""       # [S] the kill-path token: "railway.apiTokenDelete" | "discord.reset_token"
                                   #     | "openai.dashboard" | "railway.db_credential_rotate" | "github.secret_update"
    blast: str = ""                # [S] "account" | "prod-data" | "bot-presence" | "spend" | "control" | "test-only"
                                   #     — orders the recovery runbook (highest blast first)

# Credentials that never enter the worker's env (account token, GitHub token, Discord tokens, public DSN)
# are NOT in CONFIG_FIELDS. They are declared out-of-band so the registry is the COMPLETE inventory:
@dataclass(frozen=True)
class ExternalCredential:          # same three lifecycle fields; store = where it actually lives
    name: str; store: str          # "railway_account" | "github_secret" | "discord_portal" | "railway_worker_var"
    rotation: RotationPosture; revocation_ref: str; blast: str

CREDENTIAL_REGISTRY = tuple(f for f in CONFIG_FIELDS if isinstance(f, SecretSpec)) + EXTERNAL_CREDENTIALS
```

`tools/check_credential_lifecycle.py` (CI gate, mirrors `check_metric_cardinality` / `check_data_lifecycle`):
**every entry in `CREDENTIAL_REGISTRY` declares a non-empty `rotation` + `revocation_ref` + `blast`** —
a secret with no declared kill-path is CI-red. This makes the inventory *machine-complete*: a new secret
cannot be added without stating how it is rotated and revoked.

**The concentrated set, mapped (the registry's v1 rows — grounded):**

| Credential | Lives in | `blast` | root/leaf | `rotation` | `revocation_ref` |
|---|---|---|---|:--:|---|
| Railway account token | agent containers (Q-0213) | `account` | **root** | `OWNER_PROMPT` | `railway.apiTokenDelete` (brake-adjacent → §2.B carve-out) |
| GitHub repo-write token | agent containers | `control` | **root** | `OWNER_PROMPT` | `github.token_settings` |
| `DATABASE_URL` (prod DSN) | worker vars + agent containers | `prod-data` (capped by rail) | leaf | `MANAGED` | `railway.db_credential_rotate` |
| `DATABASE_PUBLIC_URL` | GitHub Actions repo secret | `prod-data` (read) | leaf | `AUTONOMOUS` | `github.secret_update` |
| Discord **prod** bot token | worker vars (not containers) | `bot-presence` | leaf | `ON_COMPROMISE` | `discord.reset_token` |
| Discord **test** token (`DISCORD_BOT_TOKEN_PRODUCTION`) | agent containers | `test-only` | leaf | `ON_COMPROMISE` | `discord.reset_token` |
| `OPENAI_API_KEY` | agent containers | `spend` | leaf | `AUTONOMOUS` | `openai.dashboard` |
| `ANTHROPIC_API_KEY` | worker vars | `spend` | leaf | `AUTONOMOUS` | `anthropic.console` |
| `CONTROL_API_TOKEN` | dashboard + worker | `control` | leaf | `AUTONOMOUS` | `railway.var_rotate` |
| `SB_PROD_ATTEST` | worker vars (SF-d custody) | `prod-data` (open-gate) | leaf | folds into **SF-d** custody call | `railway.var_rotate` |
| `BOT_OWNER_USER_ID` | deploy config (`config.py:40`) | — | — | `STATIC` | n/a (identity, not a secret) |

### 2.B The recovery arm — cadence · revocation · runbook (decision-ready posture)

**The design invariant (how it stays owner-independent):** *leaf* credentials are rotated/revoked **fully
autonomously — the root token authorizes it**; only the *root* credential (the account/GitHub token that
provisions the containers) keeps a **single irreducible owner-touch**, because you cannot autonomously
re-inject the credential that *is* your own authorization root into future container provisioning. Even
that is a **scheduled prompt**, not an operational dependency — routine work never blocks on it.

**(1) Rotation cadence — tiered by root/leaf:**

| Tier | Credentials | Cadence mechanic | Owner touch |
|---|---|---|---|
| **Leaf** | provider keys · `CONTROL_API_TOKEN` · public DSN · (DSN = `MANAGED`, Railway rotates) | a **scheduled routine** (mirrors the reconciliation routine): re-issue via provider API → swap the worker/secret var → read-back verify → record | **none** |
| **Root** | Railway account token · GitHub token | same routine **detects age** and **prompts** the owner (one platform step: re-provision the container secret) | **one scheduled prompt** (irreducible) |

`scripts/check_rotation_due.py` (mirrors `check_reconciliation_due.py`) flags any registry entry past its
cadence horizon; the routine acts on leaves and prompts on roots.

**(2) Revocation kill-path — the carve-out that makes compromise-recovery autonomous (§4 CL-2):** the
Q-0213 brake forbids `*Delete`/`*Restore` because they **lose data**. A **credential revoke loses no
data** — it is the *opposite* of destructive; it *prevents* loss. The `*Delete` pattern over-captures
`apiTokenDelete`. Recommend narrowing the brake: **credential revocation** (`apiTokenDelete`, Discord
reset, provider revoke, DB-credential rotate) is a **recovery action, agent-runnable**; **resource
deletion** (`projectDelete`/`serviceDelete`/`volumeDelete`/`environmentDelete`/DB drop) stays ask-first.
Without this carve-out, K-2 stands: leaf revocation stalls on the owner.

**(3) Compromise-recovery runbook — ordered by `blast` (buildable procedure):**

| Step | Action | Autonomy |
|---|---|---|
| **Detect** | signals: GitHub secret-scanning push-protection · `pip-audit`/Dependabot (dep compromise) · Railway **usage alert** ($15 soft, already live) = anomalous spend · the deploy webhook to `#railway-alerts` (already live) = unexpected deploy | passive (already wired) |
| **Contain** | the data-plane rail already caps a leaked DSN (can't open prod, 05 §3.5) — recorded as the standing containment for `prod-data` blast | structural (frozen) |
| **Rotate** | re-issue the new credential (leaf: provider API; root: platform step) → swap into the store → **read-back verify** the new one serves | leaf: auto · root: prompt |
| **Revoke** | kill the leaked copy via `revocation_ref` (needs CL-2 carve-out for leaves) | leaf: auto (post-CL-2) |
| **Post-mortem** | confirm prod healthy on new creds; append an entry to the credential-incident ledger; if a supply-chain dep, remove/pin it + regenerate the lock (§2.C) | auto |

### 2.C The supply-chain posture — deterministic install (buildable) + the Q-0105 composition

**The single highest-leverage fix is a hash-pinned lockfile:** convert merge=deploy from "re-resolve
latest" (S-1) to "install the exact reviewed set."

| Mechanic | Shape | Closes |
|---|---|---|
| **Lockfile + hashes** | `requirements.lock` from `pip-compile --generate-hashes` (or `uv pip compile`); the container installs `pip install --require-hashes -r requirements.lock`. `requirements.txt` becomes the **human-edited input** (constraints); the lock is the **resolved, hash-verified output** checked in | **S-1** (deploy-time re-resolution) |
| **`check_lockfile_fresh`** CI gate | regenerating the lock from `requirements.txt` yields **no diff**, and every entry is hash-pinned; a drifted lock is CI-red | S-1 · S-2 (forces the lock diff to exist) |
| **`pip-audit`** CI gate | scan the **resolved lock** against the CVE advisory DB; a known-vuln version is a finding | **S-3** |
| **Dependabot/Renovate** | advisory PRs for updates — **already exists old-repo**; carry to the new repo (bounds pinned-dep rot) | pin-rot downside of pinning |
| **`>=`-ceiling hygiene** | add `<next-major` ceilings to the open `>=` runtime deps (matches the shipped discord.py/openai/anthropic/Pillow pattern) — a cheap fix-on-sight | S-1 (immediate, pre-lock) |

**Q-0105 composition (the owner-gated DISCUSS, §4 CL-3):** the lockfile does **not** reverse "adopt
freely." Q-0105 already *states* "pin a new bot-runtime dep" — the lockfile is that rule's **enforcement**
("enforce, don't exhort", Q-0132). Adopt-freely = the *decision* to add (still no-ask); the lock = the
*mechanics* of how it lands. An agent adopts → **regenerates the lock in the same PR** → CI verifies fresh
→ **the lock diff IS the reviewable artifact** a later reviewer / Hermes / the owner can see. That is #12's
"human review" satisfied as a **deferred, visible** review (the parallel-agent norm), **not** a blocking
live gate — a blocking gate would reintroduce the owner-dependency Q-0213 forbids.

---

## 3. LANDING SITE (so no response can evaporate — V-3)

| Response | Lands exactly at | Cannot evaporate because |
|---|---|---|
| `SecretSpec` lifecycle triple (`rotation`/`revocation_ref`/`blast`) + `ExternalCredential` + `CREDENTIAL_REGISTRY` | **spec 05 `sb/spec/config.py`** (alongside `CONFIG_FIELDS`) — Gate-0 grammar | a secret with no declared kill-path is CI-red |
| `check_credential_lifecycle.py` | `tools/` CI gate (mirrors `check_metric_cardinality`, 05 §11) | required-check set; a registry entry missing a field fails CI |
| Rotation cadence + `check_rotation_due.py` | a **scheduled routine** in `docs/operations/autonomous-routines.md` + the checker (mirrors the reconciliation routine) | the routine fires on cadence; the checker flags overdue |
| Revocation carve-out (narrows the Q-0213 `*Delete` brake) | a **router DISCUSS Q** → once decided, the runbook + the routine's saved prompt | Q-0213 is a binding owner decision; the narrowing ships with its provenance Q |
| Compromise-recovery runbook | **new ops doc `docs/operations/credential-lifecycle.md`** + cross-ref from `production-deployment.md` §Backups (which already homes the DR runbook) | it is the routine's saved procedure; the routine can't run without it |
| Lockfile + `check_lockfile_fresh` + `pip-audit` | the new repo's `requirements.lock` + `.github/workflows` gate + `tools/check_lockfile_fresh.py` — Gate-0 | a non-fresh / vuln lock is CI-red before deploy |
| Q-0105 composition (lock diff = deferred review) | a **router DISCUSS Q** + a proposed **CLAUDE.md rider** (proposed, not self-applied) | rule changes are router-proposed per CLAUDE.md; the rider ships with its Q |
| SF-d (`SB_PROD_ATTEST` custody) fold-in | consolidated INTO this contract's registry (its `rotation`/`revocation_ref` row) | one home for "how is each secret custodied + rotated" instead of two |

---

## 4. OWNER-GATED?

Per response: decide-able by design (recommended default, flagged) vs a genuine owner-only call (options +
recommendation only). Q-0213 + Q-0105 are **binding owner decisions** → anything that touches them is
**proposed, not self-applied** (router DISCUSS).

| ID | Decision | 🔒? | Options | Recommendation |
|---|---|:--:|---|---|
| **CL-1** | A credential-lifecycle **recovery arm** at all? (touches the Q-0213 concentration) | 🔒 owner | (a) full arm: registry + tiered cadence + revocation carve-out + runbook · (b) runbook only, no cadence · (c) none (accept the no-kill-path risk) | **(a)** — a recovery arm is **orthogonal** to Q-0213: Q-0213 declined *scoping/custody* (keep creds concentrated), it did not decline *recovery*. This **removes** owner-dependency at compromise-time (K-2), the opposite of what Q-0213 guards against |
| **CL-2** | **Revocation carve-out** — narrow the Q-0213 `*Delete` brake to exclude credential revoke? | 🔒 owner | (a) credential revoke (`apiTokenDelete`/reset/provider) = agent-runnable recovery; **resource** delete stays ask-first · (b) keep all `*Delete` ask-first (recovery waits on owner) | **(a)** — a token revoke **loses no data**; the brake's intent (Q-0213 item 4) is *data-loss*, and its `*Delete` pattern over-captures `apiTokenDelete`. Route as DISCUSS (narrows a Q-0213 brake) |
| **CL-3** | **Supply-chain**: lockfile + hash-verify + `pip-audit` CI gate vs the Q-0105 adopt-freely grant | 🔒 owner | (a) lockfile + CI gate; adopt-freely (no-ask) **unchanged**, the lock diff is the deferred-review artifact · (b) blocking human-review on every dep add (reintroduces owner-dependency — rejected vs Q-0213) · (c) status quo (floating `>=`, no lock) | **(a)** — it **enforces the runtime-pin rule Q-0105 already states**; composes with adopt-freely (adopt → regenerate lock → CI verifies). Route as DISCUSS (touches Q-0105 binding) |
| **CL-4** | `SecretSpec` lifecycle fields + `check_credential_lifecycle` gate | arch (design) | — | **Adopt** — mirrors `StoreSpec.retention` (⑩) + `SecretSpec.redact` (05); a secret with no kill-path is a completeness bug. *Decided by design (flagged).* |
| **CL-5** | Fold **SF-d** (`SB_PROD_ATTEST` custody) into this contract as one credential-lifecycle home | arch (design) | — | **Fold** — SF-d's "plain env vs sealed vs OIDC" IS a rotation/custody question; one registry home beats two. *Decided by design (flagged).* |
| **CL-6** | `>=`-ceiling hygiene on the open runtime deps | arch (design) | — | **Adopt** — matches the shipped discord.py/openai/anthropic/Pillow ceiling pattern; the **old-repo** `requirements.txt` ceiling is a cheap fix-on-sight (noted; not done in this docs-only pass). *Decided by design (flagged).* |

---

## 5. RETIREMENT MAP (FJ L-rows / §4 gaps / owner-queue closed or advanced)

| Item | What it was | How this dossier closes / advances it |
|---|---|---|
| **FJ §4 #10** (Gate-0-bound) | "Credential lifecycle — no rotation/revocation/compromise-recovery contract for the token/DSN/Railway creds Q-0213 concentrates in agent containers" | **RETIRED (design):** the recovery arm (§2.B — tiered cadence + revocation carve-out + compromise runbook) + the `SecretSpec` lifecycle grammar leg + `check_credential_lifecycle` (§2.A). The owner-independence invariant (leaves auto, root = one irreducible prompt) is the design's spine. Owner legs **CL-1/CL-2** flagged |
| **FJ §4 #12** (Gate-0-bound) | "Dependency supply chain — 12 floating `>=` deps, no lockfile, re-resolved every merge=deploy, agents licensed to adopt, no human review; carried into the new repo with zero disposition" | **RETIRED (design):** the deterministic posture (§2.C — lockfile + hashes + `check_lockfile_fresh` + `pip-audit` + Dependabot carry-forward + `>=`-ceilings). The Q-0105 composition (lock diff = deferred review) is the "human review" leg. Owner leg **CL-3** flagged |
| **L-21** (⑂ owner, §2) — **supply-chain-human-review leg** | "…always-on autonomous agents [adopt] with no human review…" | **RETIRED (design) for the supply-chain-review leg:** the lock diff + `check_lockfile_fresh` CI gate **is** the deferred-review mechanism L-21/#12 wanted (visible artifact, non-blocking) |
| **L-21** — frozen-path write-protection + old-bot corpus-drift legs | CI guard on frozen paths (allowlist reconciliation/Gate-0 PRs); old-bot change-policy | **ADVANCED, not claimed:** honestly owned elsewhere — the frozen-path CI guard is a Gate-0 item (FJ §3.5); the old-bot corpus policy is a Stage-3 consolidation line (FJ §3 "what can wait"). Same *class* of guard (a CI gate over a change-category agents can otherwise make freely), noted for the reviewer |
| **New owner-queue rows CL-1 / CL-2 / CL-3** | §4 gaps #10/#12 had **no** owner-queue row in FJ §6 (they were §4 completeness misses) | **GRADUATED** into owner-decidable rows with options+recommendation — the same §4-gap → owner-decision move concern ⑩ made for L-19→T-1 |
| **SF-d** (vocab §⑧ / 05 §9) | `SB_PROD_ATTEST` durable-custody, owner-gated | **CONSOLIDATED (CL-5):** folded into the credential registry as one lifecycle row rather than a standalone fork |

**Cross-reference (composition, not double-claim):** concern ⑩'s **class-13 probes N-1 (credential
lifecycle) / N-2 (supply chain)** are the **standing lens** that catches a *regression* forward (43× in
Stage-2, once in the Phase-B pass); **this dossier is the mechanic that lens asserts exists.** ⑩ explicitly
deferred the *fix* to a Gate-0 item — this is it.

---

## 6. DEFERRALS (labeled with reason)

| Deferral | Reason | Bound |
|---|---|---|
| The rotation **execution wiring** (concrete Railway/provider/Discord API calls + read-back) | The *grammar* + *cadence posture* + *runbook* are designed here; the concrete API integration is ops build, same tier as SF-d custody | **CUT-1** ops setup |
| The compromise **detection anomaly-model** beyond the existing signals (secret-scanning, usage alert, deploy webhook) | Those signals already exist and are wired; a richer anomaly model (e.g. per-key spend baselining) is ops observability, not a foundational rail | ops observability (bounded) |
| **FJ §4 #11** — prod-data copies in agent containers (restored snapshots, LLM-judge replays) retention/erasure | Distinct concern (data-subject erasure, not credential rotation); it is concern ⑩'s **class-12 R-2** probe + a Gate-0/CUT fix. *Note:* #10 and #11 share the same Q-0213 container, so the recovery arm's detection **helps**, but erasure is #11's home | Gate-0 / CUT-2 (concern ⑩ / a data-retention concern) |
| The **old-repo** `requirements.txt` `>=`-ceiling fix (CL-6) | This is a docs-only design pass; ceilings on the shipped file are a cheap fix-on-sight the owner/next session can take | fix-on-sight (noted) |

No open-ended speculation — every threat is grounded in a shipped credential, a frozen decision (Q-0213 /
Q-0105 / Q-0193), or a verified file (`requirements.txt`, `backup-db.yml`, `config.py:40`), and every
deferral names its owning phase within the corpus.

---

*Authored 2026-07-04 for the strand-3 cross-cutting concerns. Consumes `shared-vocabulary.md` (⑥ config/
secret grammar) + spec 05 (§3.1/§3.2/§3.5) + concern ⑩ (class-13 N-1/N-2). Spot-verified this session
against shipped source / frozen decisions: `requirements.txt` (12 deps, open `>=` ranges, no lockfile),
`.github/workflows/backup-db.yml:7,18` (`DATABASE_PUBLIC_URL` GitHub repo secret), `disbot/config.py:40`
(`BOT_OWNER_USER_ID` deploy config), router Q-0213 (concentration + `*Delete` brake), railway-setup-plan
§1 (`apiTokenDelete` in the destructive set, no-scope/no-expiry token). `sb/` re-confirmed design-only
(no files). **NOT SOURCE OF TRUTH for runtime** — a design contract; source wins (Q-0120).*
