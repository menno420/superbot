# Gate-0 · The amendment registry + its uniqueness checker

> **Status:** `reference` — Gate-0 grammar-freeze artifact (2026-07-04). **NOT SOURCE OF TRUTH** —
> a design/spec contract; shipped source + the owning specs win (Q-0120). The authoritative shape
> of the registry itself is the committed YAML (`docs/planning/rebuild-amendments.yml`) and its
> minting authority is spec 01 §3.7
> (`../design/strand-1-kernel-spine/01-compiler-snapshot-amendments.md`). This doc specifies the
> file's schema, the ~40-line checker, the minting protocol, and records which families **this**
> Gate-0 fold flips to `in-spec`.

---

## 1. What it is

`docs/planning/rebuild-amendments.yml` is the **sole collision-free minting authority** for every
rebuild grammar-amendment ID. It exists because the capability audit minted IDs *locally* in four
lanes and collided **three times** in one pass (Lane B/C/D all claimed "G-7…G-9"; the capstone
reconciled by hand — runtime-logic #92/#217; idea doc `rebuild-amendment-registry-2026-07-03.md`).
It is the same collision-kill pattern the runtime namespace registry (K1, spec 03) applies to
runtime string identities — here applied to **meta-artifacts** (the amendment numbering). The two
mechanisms are deliberately distinct and never overlap.

It is built **before** the Gate-0 fold so the fold that stamps `G-9…G-24` works off a
collision-free list (build-order step **S0**, worklist Part 3).

## 2. YAML schema

Top-level keys:

| Key | Type | Meaning |
|---|---|---|
| `version` | int | Schema version (currently `1`). |
| `spec_corpus` | list[path] | The files an `in-spec` `spec_ref` may resolve against. spec 01 §3.7 sketched a single-file `spec` arg; Gate-0 generalizes it to the corpus (merged spec + the 14 foundational specs + the Gate-0 freeze) because ratified grammar now lives across all three. |
| `amendments` | map `G-<n>` → row | The ratified grammar **families**. |
| `riders` | map `R-<n>` → row | Soft riders — field/vocab additions batched into the same fold PR. |
| `provisional` | map `P-<n>` → row | Held candidates with a recorded `ratify_when` condition. |
| `refuted` | map `<Name>` → row | Do-not-re-propose set; each carries a one-line `reason`. |

**Amendment row (`G-<n>`):**

| Field | Type | Rule |
|---|---|---|
| `name` | str | The family/spec name. Must not equal any `refuted` key. |
| `status` | enum | `in-spec` · `pending-gate-0` · (`spike` is a `source` tag, not a status). |
| `spec_ref` | str \| null | **REQUIRED non-null iff `status: in-spec`**; **MUST be null iff `pending-gate-0`**. A `§`/named reference resolvable in `spec_corpus`. |
| `consumers` | list[str] | Subsystems that need it (may be empty for a cross-cutting field). |
| `source` | str | Provenance lane(s)/tag: `spike`, `Lane D`, `"D+A"`, `"A+C+B"`, `B`, … |
| `note` | str (opt) | Free text — compose-first instructions, flip-candidate substrate, scope narrowing. |

**Rider / provisional / refuted rows** carry free-form descriptive fields (`desc`/`ratify_when`/
`reason` + `source`); the checker only enforces id-uniqueness and the refuted-name guard on them.

## 3. `tools/check_amendments.py` — the ~40-line checker (required check)

```python
# tools/check_amendments.py  — required check; returns [] when clean, else one string per violation.
import yaml, re, pathlib

def check_amendments(
    registry="docs/planning/rebuild-amendments.yml",
) -> list[str]:
    errs: list[str] = []
    d = yaml.safe_load(open(registry))
    amend, riders = d["amendments"], d.get("riders", {})
    prov, refuted = d.get("provisional", {}), d.get("refuted", {})
    corpus = [pathlib.Path(p) for p in d.get("spec_corpus", [])]

    def _num(k): return int(k.split("-")[1])

    # 1. G-/R-/P- ids unique and CONTIGUOUS (next-free-number; no gaps, no dups) per family.
    for prefix, block in (("G", amend), ("R", riders), ("P", prov)):
        nums = sorted(_num(k) for k in block)
        if len(nums) != len(set(nums)):
            errs.append(f"{prefix}: duplicate id(s) in {nums}")
        if nums and nums != list(range(1, nums[-1] + 1)):
            errs.append(f"{prefix}: non-contiguous ids {nums} (gaps at "
                        f"{[n for n in range(1, nums[-1]+1) if n not in nums]})")

    # 2. status/spec_ref consistency: in-spec REQUIRES a spec_ref that resolves in the corpus;
    #    pending-gate-0 REQUIRES spec_ref null.
    def _resolves(ref: str) -> bool:
        toks = re.findall(r"§[\w.\/]+|[A-Za-z0-9_\-]+\.md", ref)  # §-refs + named files
        text = "".join(p.read_text(errors="ignore")
                       for f in corpus for p in ([f] if f.is_file() else f.rglob("*.md")))
        return any(t.lstrip("§") in text for t in toks) if toks else False
    for k, v in amend.items():
        st, ref = v["status"], v.get("spec_ref")
        if st == "in-spec" and not ref:
            errs.append(f"{k}: in-spec but spec_ref is null")
        if st == "in-spec" and ref and not _resolves(ref):
            errs.append(f"{k}: in-spec spec_ref {ref!r} does not resolve in spec_corpus")
        if st == "pending-gate-0" and ref:
            errs.append(f"{k}: pending-gate-0 but spec_ref is set ({ref!r})")
        if st not in ("in-spec", "pending-gate-0"):
            errs.append(f"{k}: unknown status {st!r}")

    # 3. no refuted name is reused as an amendment/rider/provisional `name`.
    reused = {v.get("name") for v in {**amend, **prov}.values()} & set(refuted)
    errs += [f"refuted name reused as an amendment: {n}" for n in sorted(reused) if n]

    return errs

if __name__ == "__main__":
    import sys
    v = check_amendments()
    print("\n".join(v) if v else "amendments: OK")
    sys.exit(1 if v else 0)
```

**Semantics, pass by pass:**
1. **Uniqueness + contiguity** — per family (`G`/`R`/`P`), ids are unique and gap-free from `1`
   (the "next-free-number" invariant made mechanical — a lane cannot skip or collide a number).
2. **status ⇄ spec_ref** — an `in-spec` row must name a `spec_ref` that *resolves* in `spec_corpus`
   (the "every ratified family points at real frozen grammar" invariant; this is the multi-file
   generalization of spec 01 §3.7's single-file check-#2, needed because Gate-0 grammar homes span
   the corpus). A `pending-gate-0` row must have `spec_ref: null` (an unset ref is exactly what
   "not yet frozen" means; setting one without flipping status is the drift this catches).
3. **Refuted guard** — no `refuted` name may reappear as a live family/provisional `name`
   (keeps the adversarially-killed set enforceable — a future session re-proposing `LootTableSpec`
   greps one file instead of re-deriving three lanes' refute passes).

`check_amendments.py` provenance/reliability header (per Q-0105) — **specified here, not yet shipped**:
this Gate-0 session is docs/spec only, so the checker is *specified* above and **ships with the `sb/`
`tools/` build (S0, pre-Gate-0)**, carrying this header at build time: *added `<build-date>` to enforce
the spec 01 §3.7 minting rules; **unverified** — confirm its output against the YAML a few times across
sessions before trusting its green; **delete it if it proves unreliable over multiple sessions** (a
convenience guard, not load-bearing runtime code).* The YAML (`rebuild-amendments.yml`) IS shipped this
session; the checker is its build-time companion.

## 4. The minting protocol

- **Proposing a family (any lane/session):** pick the **next free** `G-`/`R-`/`P-` number, add the
  row **in the same PR** that introduces the proposal, cite the row from the proposing doc, and set
  `status: pending-gate-0` with `spec_ref: null` (or `provisional` with a `ratify_when`). Never mint
  a number locally in a lane doc — mint here.
- **Refuting a proposal:** move the name into `refuted` with a one-line `reason` + `source`. Do not
  delete the reasoning — the refuted set is append-only so it stays greppable.
- **Gate-0 consumes it:** the Gate-0 fold flips a ratified `pending-gate-0` family to `in-spec` and
  **sets `spec_ref`** to the section where its grammar is now frozen. Flipping status without setting
  a resolvable `spec_ref` is a checker failure (§3 pass 2) — the two always move together.
- **Append-only / next-free-number** are enforced by §3 pass 1; the checker is a required check so a
  colliding or gap-introducing mint reddens CI before merge.

## 5. What THIS Gate-0 fold flips vs leaves pending

The Gate-0 grammar freeze ratifies the L0 kernel-spine + cross-cutting grammar (the ~34 field
additions + ~53 primitives across the 14 foundational specs, worklist Part 1) **plus** the L-24
presentation riders as declared fields (worklist Group 18). Mapping that onto the `G-9…G-24`
family set:

- **FLIPPED to `in-spec` — G-10 `ModalFormSpec`.** The **L-24 presentation-riders design** ratifies
  `ModalSpec` to declared-field depth (worklist Group 18 #86: "ModalSpec … amendment G-10
  ModalFormSpec"; README §6). This is the one `G-9…G-24` family the L0 freeze itself designs, so it
  flips now; `spec_ref` points at the L-24 rider home.
- **G-1…G-8 remain `in-spec`** (already frozen — G-1…G-6 in the 2026-07-02 spike; G-7/G-8 as the
  Lane-D knowledge/AI facets, §2.8).
- **G-9, G-11…G-24 stay `pending-gate-0`.** These are **domain-grammar families** discovered in the
  capability audit whose owning K-step / Phase-4 port has not been built yet — the L0 kernel-spine
  freeze does not itself design them. Each mints its `spec_ref` when its fold ships. Two carry a
  **substrate note** flagging that a kernel spec already provides the underlying mechanism (a
  flip candidate the relevant fold should confirm rather than re-mint):
  - **G-9 `DeferredActionSpec`** — the one-shot-deferred-action gap it names is closed by spec 09's
    `TriggerKind.ONE_SHOT` + `DURABLE` due-queue + boot-reconcile. Left `pending` because spec 09
    delivers it as a `ManagedTaskSpec` trigger, not a named `DeferredActionSpec` family; the fold
    confirms absorb-vs-mint.
  - **G-12 `EconomyTransactionSpec`** — its atomic-money-move substrate is spec 07's `CompoundOpSpec`
    + `IdempotencyPosture`. Left `pending` because the *domain* family layering on `CompoundOpSpec`
    is a Phase-4 economy fold.
  - **G-24 `PreviewConfirmApplySpec`** carries spec 01 §3.7 / §8-fork-7's standing instruction:
    the fold **composes from §2.7 `MutationPreview` + `ConfirmationSpec` first and mints only if
    composition fails** — the minting authority records the instruction; the fold executes it.

Rationale for the conservative flip: this session **consolidates and ratifies, it does not redesign**
(Q-0120 — source wins; Q-0089 — no padding). Flipping a domain family before its grammar is actually
frozen would set a `spec_ref` that does not resolve (a §3 checker failure) and would mis-state the
build state to the fold agents. Only G-10 has real frozen grammar in the L0 corpus today.
