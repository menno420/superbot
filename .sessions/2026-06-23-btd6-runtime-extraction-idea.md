# 2026-06-23 — Capture: BTD6 runtime mechanics straight from the game

> **Status:** `complete` — owner-raised idea capture (docs-only), no runtime code.

Follow-on to the freeplay-curve/RBE + cash investigation (PRs #1384/#1387). The owner
reflected that the **original plan to pull data straight from the game** is still worth
doing "eventually," *because we see so many different stats and numbers everywhere.*

Captured it as `docs/ideas/btd6-runtime-mechanics-from-game-2026-06-23.md` + README index
entry. The sharpened framing: Phase 1 (consume the Mod Helper **model** dump) is done; the
recurring number disputes all live in the **runtime/simulation layer** the model export
omits (freeplay health ramp, superceramic swap, per-round RBE & cash). Proposes a BTD Mod
Helper **runtime-extraction mod** as the game-sourced oracle, pairing with the drift-check
idea so our curated sidecars become game-verified rather than community-derived.

## 💡 Session idea (Q-0089)
The capture itself is the idea (owner-raised + agent-sharpened). Distinct sub-idea worth
flagging: a **first slice** scoped to just the freeplay health curve + per-round RBE/cash
(the exact things contested this session) would de-risk the larger extraction effort and
immediately replace the topper64 cross-checks with a game oracle.

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-23-btd6-freeplay-curve-and-rbe** (#1387). Did well: caught + fixed its
own predecessor's (#1384) wrong brackets, validated against two anchors, and flagged the
fortified-RBE 0.1% gap honestly. What this capture adds: #1387's residual uncertainty (one
anchor for superceramic RBE, fortified ~0.1% off, topper-as-source) is *exactly* the
"secondary sources disagree" pain this idea targets — the session-chain surfaced the root
cause, and this routes it instead of letting it recur.

## Doc audit (Q-0104)
Docs-only; idea filed in its durable home (`docs/ideas/` + README index). No ledger/owner
decision to record. `check_docs --strict` run before push.
