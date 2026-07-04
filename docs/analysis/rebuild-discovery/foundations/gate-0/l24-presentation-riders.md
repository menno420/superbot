# Gate-0 · The L-24 presentation riders — pinned to buildable depth

> **Status:** `reference` — Gate-0 grammar-freeze artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a
> design/spec contract; shipped source + the owning specs win (Q-0120). This doc pins the **exact
> shapes** of the five L-24 presentation riders that README §6 names as Gate-0 *declared fields* but
> that the 14 foundational specs designed only to declared-field depth. It is Deliverable 5 of the
> Gate-0 consolidation. The uniform GROUP 18 fold slice that stitches into the fold set is the
> companion `_fold/18-l24-presentation-riders.md`.
>
> **Precedence for this doc:** the send-egress half of `allowed_mentions` is **already frozen** in
> spec 10 §8.1 (`TrustLevel`/`OutboundContent`/`ChannelEmitter`, folded at Group 16) — this doc
> **consumes** it, does not redesign it. The reply-egress `SurfaceResponder` default-deny is frozen in
> spec 02. The MODAL **surface + adapter** are frozen in spec 02 (§3.1/§3.7, line 461). `ModalSpec`
> flips amendment-registry **G-10 `ModalFormSpec`** to `in-spec`, pointing here. `alt_text`, the
> locale seam, and bundled fonts are **declared** here (FJ §3 carried them to Gate-0 as declared
> grammar); their enforcement/vendored-assets sequence with the render + media-subsystem build.

---

## 0. What L-24 is, and why these five are "declared-field" depth

**L-24** (final judgment §2) is the *presentation-substrate riders* row: alt-text, i18n/locale,
`allowed_mentions`, `ModalSpec`, bundled fonts (and autocomplete — carried, out of this slice's
five). FJ §3 dispositioned it: *"i18n / alt-text / a11y riders (L-24) — become declared Gate-0
grammar fields; no current-repo work"* (`final-judgment-fable5-2026-07-03.md:150`). The
retirement-coverage-map (line 73) records it **Covered (partial) + Carried**: spec 10 names the
send-egress `ChannelEmitter` (the `allowed_mentions` mass-ping vector) + alt-text as Gate-0 fields;
"the rest (i18n seam, ModalSpec-under-guarantees, bundled fonts, autocomplete) are carried to Gate-0
as declared grammar fields."

"Declared-field depth" means Gate-0 **ratifies the field/primitive exists with a pinned shape,
default, attach point, and semantics** — not that the enforcing compile fence, the vendored font
files, or the translation tables ship now. The build of each rider's *enforcement* sequences with the
subsystem that renders it (the render layer for alt-text/locale, the media subsystem for fonts). This
is the standard Gate-0 "freeze the grammar, sequence the enforcement" posture, identical to how
`cost_posture`'s Phase-2 live-binding check (spec 10 §2.A) sequences after the T2-15 spend counter.

All five **retire L-24**.

---

## 1. `alt_text` — accessibility alt-text on every image/attachment

**Shape (declared field):**

```python
# on EmbedFrameSpec (§2.3) and every discord.File / embed-image-emitting render spec
alt_text: str = ""        # [S] — the accessibility description the renderer sets on the
                          #        discord.File / embed image at construction time
```

- **Type · default · role:** `str` · `""` · **[S]** (hand-authored, sim-frozen — it is semantic copy,
  §2.0, so never sim-owned).
- **Where it attaches (the ~50 sites):** the image/attachment-bearing render specs —
  **`EmbedFrameSpec`** (§2.3: `thumbnail_ref` and any embed image), **`ResultCardSpec`** (the
  `result_render=result_card` card, §2.6/§2.7), **`LeaderboardSpec.card_frame`** (§2.8 game facet),
  and every **media-generation output** that emits a `discord.File`. There is deliberately **no** new
  `FileSpec`/`AttachmentSpec` primitive: `alt_text` rides the spec that already declares the image ref,
  exactly where the renderer constructs the `discord.File`. spec 10 §1.C **X-5** grounds the gap ("An
  `discord.File` ships with no alt-text — all ~50 sites").
- **Semantics:** the string the concrete renderer passes as the attachment/description alt-text; empty
  ⇒ no alt-text emitted (the shipped behavior, made *declarable* rather than *impossible*).
- **Declared-field depth / sequenced enforcement:** Gate-0 ratifies the field. The intended compile
  fence — *an image-bearing render spec MUST carry a non-empty `alt_text`* (the class-13 non-functional
  leg, spec 10 §1.C X-5) — is declared but **sequenced with the render-layer build**, so v1 does not
  red every ported call site on day one. Default `""` keeps ported renders compiling.
- **Retires:** L-24 (alt-text leg).

---

## 2. The locale / i18n seam — the declared render/copy hook

**Shape (declared seam, not a field on an existing spec):**

```python
# sb/kernel/interaction/locale.py  (declared seam; identity resolver is the v1 default)
@dataclass(frozen=True)
class LocaleContext:
    locale: str = "en"                 # [S]/runtime — BCP-47-ish tag; "en" = the authored corpus
class CopyResolver(Protocol):          # the render/copy hook
    def resolve(self, copy: str, *, locale: LocaleContext) -> str: ...
IDENTITY_COPY_RESOLVER: CopyResolver   # returns copy verbatim — the v1 default
```

- **Type · default · role:** a declared **render-layer seam** (a `LocaleContext` threaded through
  `PanelContext` at render + a registered `CopyResolver` hook) · default = `IDENTITY_COPY_RESOLVER`
  (verbatim authored copy) · **[S]** (the seam is authored, not sim-owned).
- **Where it attaches:** the **render/copy layer** — `PanelContext` (§2.3, the engine's render
  argument) carries the `LocaleContext`; every place the renderer emits an **[S] copy string**
  (`title`, `label`, `EmbedFrameSpec` copy, `empty_state`, `user_message`) passes it through the
  resolver. Because copy is already **[S] and semantic** (design-spec §2.0), the seam is a *resolution
  hook over the existing copy strings*, not a new copy store.
- **Semantics:** at render time the engine resolves each authored copy string via the registered
  `CopyResolver`. v1 registers `IDENTITY_COPY_RESOLVER` ⇒ zero behavior change (authored copy renders
  verbatim). A future locale build registers a table-backed resolver **without touching any spec** —
  the seam is the entire point (it makes i18n a swap-in at one hook, not a grammar migration).
- **Declared-seam depth:** Gate-0 ratifies that the hook exists and defaults to identity. No
  translation tables, no per-locale corpus, no plural rules ship now (FJ §3 "no current-repo work").
- **Retires:** L-24 (i18n/locale leg).

---

## 3. `allowed_mentions` default policy — default-deny via `TrustLevel.UNTRUSTED` on **both** egress ports

**This rider is already frozen** — it is the cross-port materialization of spec 10 §8.1's
`TrustLevel`/`OutboundContent` (folded at Group 16 #79c). This doc pins the **policy** (the default),
not a new type.

**Shape (the frozen interlock):**

```python
class TrustLevel(StrEnum):            # spec 10 §8.1 — default-DENY (frozen; folded Group 16)
    UNTRUSTED = "untrusted"   # member-supplied text ⇒ mentions ALWAYS suppressed + markdown escaped (DEFAULT)
    TRUSTED   = "trusted"     # operator/owner-authored ⇒ mentions gated to an explicit allowlist
    SYSTEM    = "system"      # bot constant copy ⇒ mentions only if statically declared

@dataclass(frozen=True)
class OutboundContent:                # spec 10 §8.1 — the send-port payload
    body: str
    trust: TrustLevel = TrustLevel.UNTRUSTED   # [S] default-deny
    allow_mentions: tuple[str, ...] = ()        # honored ONLY for TRUSTED/SYSTEM
```

**The default policy (what Gate-0 ratifies as the L-24 field):** *the `allowed_mentions` a rendered
message carries is **computed from `TrustLevel`, never authored raw**, and the default `TrustLevel` is
`UNTRUSTED` ⇒ `discord.AllowedMentions.none()`* — on **both** egress ports:

| Egress port | Chokepoint (frozen) | Default | How the policy binds |
|---|---|---|---|
| **Reply** (interaction ack/reply) | `SurfaceResponder.render(Result)` / `deny(...)` (spec 02, `kernel/interaction`) | `UNTRUSTED` ⇒ `AllowedMentions.none()` + markdown-escape | A rendered field defaults `UNTRUSTED`; safety does **not** depend on tagging — it depends on the default. |
| **Send** (service-initiated `channel.send`) | `ChannelEmitter.send(cid, OutboundContent, guild_id=…)` (spec 10 §8.1, `kernel/interaction/egress.py`) | `OutboundContent.trust = UNTRUSTED` ⇒ `AllowedMentions.none()` | The `automation_executor.py:220` mass-ping (`await channel.send(template)`) becomes `emitter.send(cid, OutboundContent(body=template), guild_id=g)`; `@everyone` from user-authored template text is **structurally impossible**. |

The **concrete `DiscordChannelEmitter`** (`adapters/discord/responders.py`) is the **only** module that
constructs `discord.AllowedMentions`, from `(trust, allow_mentions)`: `UNTRUSTED ⇒
AllowedMentions.none()`; `TRUSTED`/`SYSTEM` ⇒ the allowlist only. A raw
`discord.abc.Messageable.send`/`channel.send`/`.reply` **outside** that adapter is a
`SEMANTIC_VIOLATION` (the egress AST fence, spec 10 §8.1 / Group 16 #79f).

- **Role:** **[S]** policy tag (the `trust` field) · default `UNTRUSTED`.
- **Semantics:** mention-suppression is a *default-deny property of the egress port*, not a per-callsite
  courtesy — the L-24 "allowed_mentions leg" is closed by construction, not by remembering to pass a
  flag.
- **Retires:** L-24 (allowed_mentions leg) / X-1 (the mass-ping vector).

---

## 4. `ModalSpec` — the declarative modal-form primitive (amendment G-10 `ModalFormSpec`, in-spec)

**The reconciliation to pin first (against spec 02, source-wins Q-0120):** spec 02 line 461 states a
modal *submit* "**is an ACK/entry mechanism of an existing action, not a separate primitive — so it
needs no new spec member**." That is about the **dispatch surface**: `Surface.MODAL` and the modal
**adapter** already exist (spec 02 §3.1 line 152; adapters §72). `ModalSpec` is **not** a new dispatch
surface and does **not** contradict that — it is the declarative **form body** (the input fields)
that replaces the escape-hatch `open_modal(modal_ref: HandlerRef)` handler (spec 02 §3.2 line 217)
with grammar. This is exactly amendment **G-10 `ModalFormSpec`**, which this Gate-0 fold flips to
`in-spec` (amendment-registry §5).

**Shape (minted in-spec against the manifest grammar):**

```python
class ModalFieldStyle(StrEnum):
    SHORT = "short"; PARAGRAPH = "paragraph"          # Discord TextStyle

@dataclass(frozen=True)
class ModalFieldSpec:                                  # one text input row
    field_id: str                                     # [S] namespaced; the submitted-args key on surface=MODAL
    label: str                                        # [S] semantic copy
    style: ModalFieldStyle = ModalFieldStyle.SHORT    # [S]
    required: bool = True                             # [S]
    min_length: int | None = None                     # [S]
    max_length: int | None = None                     # [S]
    placeholder: str = ""                             # [S] semantic copy
    default: str = ""                                 # [S] pre-filled value (e.g. the preset_kind="text" override, §2.5)

@dataclass(frozen=True)
class ModalSpec:                                       # G-10 ModalFormSpec — the declarative modal-form primitive
    modal_id: str                                     # [S] namespace kind `modal`; the custom-id root
    title: str                                        # [S] semantic copy
    fields: tuple[ModalFieldSpec, ...]                # [S] 1..5 (Discord cap; compile-checked ≤ 5)
    on_submit: "WorkflowRef | HandlerRef"             # [S] returns WorkflowResult (§2.7) — zero-code kernel workflow OR a domain handler
```

- **Type · default · role:** frozen dataclass · no default (it is a declared primitive, referenced by
  ref) · **[S]**.
- **Where it attaches:** referenced by the two existing modal-entry sites, replacing their
  `HandlerRef` escape hatch —
  - **`PanelActionSpec`** (§2.6): the frozen `defer_mode=modal` action gains `modal: ModalSpec | None`
    (compile rule: `defer_mode == modal ⇒ modal is not None`). The MODAL adapter, on submit, builds a
    `ResolveRequest` with `surface=MODAL`, `args = the submitted `ModalFieldSpec.field_id` values`,
    `target.spec = the declaring PanelActionSpec` (spec 02 line 461) — no new surface, the form is
    now data.
  - **`ConfirmationSpec`** (§2.7): `challenge ∈ {typed_phrase, typed_hash}` renders a `ModalSpec`
    (a one-field `typed_phrase`/`typed_hash` capture) instead of an ad-hoc modal (spec 02 §3.2 line
    245: "a modal for `typed_phrase`/`typed_hash`").
- **Semantics:** declares the modal's input fields + title + submit target as manifest data, so a
  form is expressible without a `RendererHandler` escape hatch. Dispatch is unchanged — submission
  re-enters through the frozen modal adapter → `resolve()`.
- **The `from_error` / `ErrorEnvelope` tie (why ModalSpec composes with C-1):** a `ModalSpec` carries
  **no** error handling of its own — it inherits the C-1 guarantee. On submit, `resolve()` runs
  `on_submit` at step 5 inside the single seam; any exception classifies through
  **`from_exception(exc, surface=Surface.MODAL, target=<the action's TargetRef>)` → `ErrorEnvelope`**
  (spec 02 §3.3), rendered by `SurfaceResponder` with the default-deny mention policy (§3 above). This
  is the retirement-coverage-map's "**ModalSpec-under-guarantees**" (line 73): the modal form is
  *under* the frozen envelope, visibility, and egress guarantees — a `ModalSpec` cannot dispatch,
  fail, or reply outside C-1. `on_submit` returns a `WorkflowResult` (§2.7) exactly like any action
  handler, so the confirm/audit/render pipeline is identical.
- **Amendment-registry action:** flips **G-10 `ModalFormSpec`** from `pending-gate-0` to `in-spec`,
  `spec_ref` → this section (amendment-registry §5, "FLIPPED to in-spec — G-10"). It is the **one**
  `G-9…G-24` family the L0 freeze itself designs; G-9/G-11…G-24 stay `pending-gate-0`.
- **Retires:** L-24 (modal leg); flips amendment G-10.

---

## 5. Bundled fonts — the declared asset set for deterministic media rendering

**Shape (declared asset set + a font ref):**

```python
# sb/assets/fonts/  — vendored, checked-in font files (NOT system fonts)
@dataclass(frozen=True)
class FontAsset:
    font_key: str          # [S] namespace kind `font`; the registry key
    path: str              # [S] repo-relative path under sb/assets/fonts/ (vendored, hash-stable)
    role: str = "body"     # [S] {body, heading, mono, emoji_fallback, ...}
FONT_REGISTRY: tuple[FontAsset, ...]   # [S] the declared bundled-font set the media renderer draws from
# media-render specs reference a font by key:
font_ref: str = ""         # [S] a FONT_REGISTRY.font_key; "" ⇒ the declared default body font
```

- **Type · default · role:** a declared **asset set** (`FONT_REGISTRY` of vendored `FontAsset`s) +
  a `font_ref` on media-render specs · default `""` ⇒ the declared default body font · **[S]**.
- **Where it attaches:** the **asset / media-render layer** — the media-generation output specs (image
  cards, generated media) and `EmbedFrameSpec` image renders reference `font_ref`; the media renderer
  loads **only** from `FONT_REGISTRY` (vendored files), never a system font path.
- **Semantics:** pins media rendering to a **repo-vendored, hash-stable** font set so image generation
  is **byte-deterministic across environments** (agent container, CI, prod) — the determinism the
  golden harness requires (design-spec §6 / §10.1 determinism-pinning: clock/RNG are injectable kernel
  services; fonts are the media-render analogue). A system-font dependency would make the same spec
  render differently per host and break golden replay.
- **Declared-asset depth:** Gate-0 ratifies the declared set + the `font_ref` grammar; the concrete
  vendored `.ttf`/`.otf` files + the populated `FONT_REGISTRY` ship with the **media subsystem build**
  (FJ §3 "no current-repo work").
- **Retires:** L-24 (bundled-fonts leg).

---

## 6. Summary table (the five, at a glance)

| Rider | Type · default · role | Attaches to | Retires |
|---|---|---|---|
| `alt_text` | `str` · `""` · [S] | `EmbedFrameSpec` + every `discord.File`/embed-image render spec (~50 sites) | L-24 |
| locale seam | `LocaleContext` + `CopyResolver` hook · `IDENTITY_COPY_RESOLVER` · [S] | render/copy layer (`PanelContext` + [S] copy strings) | L-24 |
| `allowed_mentions` policy | `TrustLevel` tag · `UNTRUSTED` ⇒ `AllowedMentions.none()` · [S] | **both** egress ports (`SurfaceResponder.render` + `ChannelEmitter.send`) | L-24 / X-1 |
| `ModalSpec` (G-10) | frozen dataclass · — · [S] | `PanelActionSpec`(defer_mode=modal) + `ConfirmationSpec`(typed_phrase/typed_hash) | L-24; flips G-10 |
| bundled fonts | `FONT_REGISTRY` asset set + `font_ref` · `""`=default body · [S] | asset / media-render layer | L-24 |

---

## 7. Source-wins reconciliations recorded (Q-0120)

1. **`ModalSpec` is a form-body primitive, NOT a dispatch surface.** Spec 02 line 461 ("a modal …
   needs no new spec member") is about the **surface/adapter**, which is frozen and reused. `ModalSpec`
   replaces the `open_modal(modal_ref: HandlerRef)` escape hatch (spec 02 line 217) with declarative
   fields; it attaches to `PanelActionSpec`/`ConfirmationSpec`, not the manifest root, and adds no new
   `Surface` member. The worklist Group 18 "attaches to: manifest grammar" is sharpened to these two
   referring specs. No contradiction with spec 02 — the dispatch surface and the form body are
   different layers.
2. **`allowed_mentions` is not a new type — it is the default policy over the frozen `TrustLevel`.**
   The send-egress half (`ChannelEmitter`/`OutboundContent`/`TrustLevel`) is frozen at spec 10 §8.1
   (folded Group 16 #79); this doc pins only the *cross-port default-deny policy*. Both egress ports
   (reply = spec 02 `SurfaceResponder`, send = spec 10 `ChannelEmitter`) default `UNTRUSTED`. No
   redesign.
3. **`alt_text` grounding is spec 10 §1.C X-5 + FJ L-24, declared at README §6.** The worklist cites
   README §6 (the Gate-0 declaration site); the threat-model grounding + the "becomes a Gate-0 field"
   ruling live in spec 10 §1.C X-5 and FJ §3 / retirement-map line 73. Citation enriched, no shape
   change.
4. **`ModalSpec-under-guarantees` = the from_error tie.** Retirement-coverage-map line 73's phrase is
   the requirement pinned in §4: a `ModalSpec` submit routes through `resolve()` and classifies via
   `from_exception(exc, surface=MODAL, target=…)` → `ErrorEnvelope`, under the frozen visibility +
   egress guarantees.
5. **Autocomplete is the sixth L-24 rider, out of this slice's five.** Retirement-map line 73 lists
   autocomplete alongside these five; the task scopes this deliverable to riders #83–#87. Autocomplete
   stays **carried to Gate-0 as a declared grammar field** (FJ §3), not pinned here — flagged so it is
   not silently dropped.

---

## Provenance

- **Authored by** Claude Opus 4.8 (ultracode), 2026-07-04 — a docs-only Gate-0 consolidation session
  (Deliverable 5 + the GROUP 18 fold slice). No `sb/`/`disbot/` code.
- **Verified against source (Q-0120):** `design/README.md` §6; `design/strand-3-cross-cutting-concerns/
  10-security-abuse-rubric.md` §1.C/§1.D/§8.1 (X-1/X-5, `TrustLevel`/`OutboundContent`/`ChannelEmitter`);
  `design/strand-1-kernel-spine/02-resolver-error-envelope.md` §3.1/§3.2/§3.3 (Surface.MODAL,
  `open_modal`, `from_exception`, line 461); `rebuild-design-spec-2026-07-02.md` §2.3 (`EmbedFrameSpec`/
  `PanelContext`), §2.6 (`PanelActionSpec.defer_mode`), §2.7 (`ConfirmationSpec`), §2.0 (copy is
  semantic), §6/§10.1 (determinism pins); `gate-0/amendment-registry.md` §5 (G-10 flip);
  `design/retirement-coverage-map.md` line 73 (L-24 disposition); `final-judgment-fable5-2026-07-03.md:150`
  (FJ §3 L-24 ruling).
- **NOT SOURCE OF TRUTH for runtime** — a design contract; source wins (Q-0120).
