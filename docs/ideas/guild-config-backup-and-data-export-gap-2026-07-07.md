# Two adjacent gaps: self-service guild-config backup/restore, and GDPR "export my data"

> **Status:** `ideas` — capture only, not approved for implementation. Surfaced 2026-07-07 during a
> foundational-capability sweep requested by the owner, cross-checked against the rebuild's frozen
> taxonomy so nothing already-covered gets re-reported.
> **Subsystem:** none (cross-cutting; adjacent to K3/S14 backup-DR and the privacy/erasure rubric).

## 1. Self-service, per-guild config backup/restore — not covered anywhere

The rebuild has thorough **infrastructure-level** backup/DR: S14 covers whole-database `pg_dump` /
restore-verify / RPO targets, and CUT-3's N=7-day rollback window covers the migration cutover
itself (`rebuild-canonical-plan-2026-07-06.md` §2.1 B-4, §5 step 17). Neither of those is a
**self-service, single-guild** feature — there's no "export my server's SuperBot settings" or "roll
my server back to last week's configuration" independent of a full database disaster-recovery
event. The closest existing idea, a guild template/provisioning model
(`docs/ideas/future-product-direction-2026-06-07.md:152`), is framed as a template for *new* server
setups, not backup/restore of an *existing* server's live config. This capability doesn't appear
anywhere in the K0-K10 taxonomy or the B-1..B-4 rulings.

Worth having an explicit answer either way: build it (a per-guild settings snapshot/restore,
probably a thin read/write over the same settings-registry the settings engine already owns), or
rule that whole-DB backup + the owner's own manual intervention is sufficient and this is
deliberately out of scope. Either is fine — what's missing is that no one has looked at it yet.

## 2. GDPR-style "export my data" — half-built (erasure is solid, export isn't)

An earlier gap-analysis idea (`docs/ideas/gap-analysis-2026-06-11.md:21-26`) named this as a twinned
"export & erasure" concern, relevant since the project is EU-based. Since then, the **erasure**
half has been thoroughly mechanized in the rebuild: rubric class 12 (privacy/retention/erasure),
`StoreSpec.data_class`/`erasure_ref`/`cache_scope`, a `check_data_lifecycle` checker, and a dedicated
`sb/kernel/privacy/erasure.py` executor are all named and land at build step S11
(`rebuild-gate0-worklist-2026-07-04.md:171-178`, canonical plan §11 A-... adjacent to the backup/DR
row). But the **export** half — a user-facing "give me everything you have keyed to my user ID" —
does not reappear anywhere in the Gate-0 grammar or the S0-S15 build order. It looks like it quietly
dropped out between the original idea capture and the formalized privacy rubric.

This is worth re-raising specifically as "export," not "export & erasure" generically, since erasure
is done and only needs a mention that export is its still-open sibling. The practical build cost
should be small relative to what's already landing: the `StoreSpec` walk that erasure already needs
(enumerating every store that holds user-keyed data) is most of the plumbing an export command would
need too — it's a read instead of a delete over the same inventory.

## Recommended routing

Both are docs-only findings, not urgent the way the channel-role-authority gap is — neither blocks
K6/K7/K8 or any near-term build step. Reasonable next step: raise both at whatever session next
touches S11 (privacy/erasure lands there) or S14 (backup/DR), since both ride the same
`StoreSpec`/backup infrastructure already being built for other reasons — cheapest to add as a
sibling of work already in flight rather than as a separate initiative later.
