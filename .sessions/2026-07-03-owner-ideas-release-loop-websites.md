# 2026-07-03 — Capture 2 owner ideas: release→test→verify loop + websites cutover-role

> **Status:** `complete`

**Run type:** owner idea-drop, mid-conversation after the Tier-1 sitting (Q-0237). Docs-only,
restarted fresh from `origin/main`. **PR TBD (opened this session).**

**Did:** captured and classified two owner-originated rebuild ideas, both of which independently
close gaps the Fable-5 judgment (§4) flagged as *missing*, so I cross-referenced each to its gap:

1. **`rebuild-release-testing-loop-2026-07-03.md`** — the in-server release → test → verify loop:
   (A) boot/release announcer of what changed so members know what to test; (B) per-command
   "tested-since-its-change" coverage from real usage; (C) dedicated test/debug mode (full traces to
   a channel, self-explaining actions); (D) explain-then-approve button = the `verified_live`
   sign-off. Closes judgment #5 (change-comms), #7 (field-signal), #8 (co-test throughput) and is
   the missing *mechanism* for the decided Q-0234 oracle + Q-0222 CUT-1 co-test + C-2 preview/confirm.
2. **`rebuild-websites-cutover-role-2026-07-03.md`** — give the botsite + dev dashboard a rebuild
   disposition (they die at cutover today — judgment #4), repoint the producer at the new repo's
   manifest, and use them during the switch as the public cutover-comms surface and a
   rebuild-progress/verified_live dashboard (the owner-consumable visual artifact judgment #16
   flagged). Pairs with idea 1.

Both routed as **new Stage-2 capability-corpus entries** (like D-2 media gen) + Gate-0 amendments to
the verification/cutover story; idea-1's A/C flagged as also current-bot-buildable now. Design forks
recorded in each doc (release-trigger vs every-boot; approve = gate vs sign-off, unified;
test-mode audience/PII; site interim producer).

**⚑ Self-initiated:** none — pure capture of owner-dropped ideas per the Q-0172 classify-then-route
discipline; no promotion to plan/implementation (the ideas note they're ready to promote when the
owner wants).

**💡 Session idea (Q-0089):** none new — this session's whole purpose was capturing the owner's two
ideas; forcing an additional one would be filler (Q-0089 bar). The captured ideas stand.

**⟲ Previous-session review (Q-0102):** the Tier-1 sitting (#1703) closed the decision loop in one
pass because the judgment pre-tiered the queue with recommendations — good. It could have gone one
step further and, at the end, *offered* to capture any follow-on ideas the decisions triggered;
instead this idea-drop came unprompted a turn later. **System note:** a decisions-recording session
could end by asking "did answering these surface anything to capture?" — cheap, and it keeps the
associative-idea flow (the owner's working style) from relying on him to re-raise it.

**Docs audit (Q-0104):** `check_docs --strict` + `check_plan_homing` green; both ideas indexed in
`docs/ideas/README.md` with gap cross-refs; nothing left in chat only.
