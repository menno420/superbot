# 2026-06-23 — BTD6 cash model: empirical validation (capture)

> **Status:** `complete` — owner-driven investigation, docs-only capture.

Long owner-driven Q&A debugging the BTD6 late-game cash numbers against a real in-game
measurement. Outcome: **our cash model is validated** (within ~3% on pop cash, once the
double-cash modifier, the absent-in-sandbox round bonus, and the CHIMPS≠sandbox mode
difference are accounted for), and **CyberQuincy over-counts fortified bloons** (the game
gives fortified-independent cash, exactly as our model assumes). Captured the full finding
+ the owner's planned per-round verification in the runtime-extraction idea doc so the
next session starts from it.

## 💡 Session idea (Q-0089)
Already filed this arc's idea (runtime-extraction, PR #1391). Sub-idea logged in the doc:
the owner's per-round in-game capture becomes the **oracle** a drift test pins to — turning
a manual verification into a standing regression guard.

## ⟲ Previous-session review (Q-0102)
Reviewed the #1391 idea capture. It did well to frame the *runtime layer* as the gap; what
today added is the **empirical proof** that the gap is real and that secondary calculators
(CQ over-counts fortified, topper stale decay) genuinely disagree with the game — the
strongest possible motivation for the idea, now recorded in its validation log.

## Doc audit (Q-0104)
Docs-only. Finding lives in its durable home (the idea doc's Empirical validation log).
`check_docs --strict` before push. No ledger/owner-decision change.
