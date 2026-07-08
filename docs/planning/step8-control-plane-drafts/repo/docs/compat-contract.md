# The backward-compat contract (frozen artifacts) — amendment ledger

> **Status:** `placeholder, armed` — this file is the CODEOWNERS-protected amendment ledger the
> `check_compat_frozen` gate reads (design-spec §6 gate 6 + §5.3). The frozen artifact *content*
> (the 43 subsystem keys, the static custom_id set, event literals, `AITask` names, audit payload
> field sets) lands at S4 in `sb/namespace/legacy_reservations.json`, extracted from
> `menno420/superbot` at the ref pinned in `parity/goldens-source.lock`
> (`4c25a1fabe63bb790f91e04f9925632913fcd249`). This doc exists from day 0 so the CODEOWNERS path
> and the gate's amendment mechanics are real before the content is.

## The rule (spec §6, verbatim contract)

`check_compat_frozen` diffs the pinned compat artifacts against the manifest export; **any drift
from the §5.3 contract is red until this doc is explicitly amended with owner sign-off.**
Ratification adds, never removes: the generated inventory from the frozen repo is authoritative
over any enumeration here.

## Amendment ledger

The gate parses this table mechanically. A drift PR goes green only when a row here names **every**
drifted identifier and carries the sign-off token.

**Identifier format (mechanical, matches the gate's matching exactly):** every drifted identifier
must be **kind-prefixed** as `<kind>:<name>`, where `<kind>` is one of the five artifact kinds —
`subsystem_key` | `custom_id` | `event` | `ai_task` | `audit_payload` — e.g. `custom_id:econ_home`,
`event:xp.level_up`, `audit_payload:warn_issued`. A bare name (`econ_home`) never matches: the gate
compares tokens against its `kind:name` drift tags verbatim, so an unprefixed entry pardons nothing.

| Date | PR | Drifted identifiers (exact `kind:name`, comma-separated) | Why | Sign-off |
|---|---|---|---|---|
| _(none yet)_ | | | | |

Sign-off convention: the cell must contain `Signed-off: menno420` plus the router Q-number that
recorded the ruling (e.g. `Signed-off: menno420 (Q-0NNN)`). Under Q-0241 the sign-off may be
recorded by an agent relaying an in-session owner directive — the Q-number is the provenance.
