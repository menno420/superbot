# 2026-06-20 — AI self-introduction: advertise capabilities + available games

> **Status:** `in-progress`

## What I'm about to do
Owner asked (via Discord screenshot): when the bot is asked to *introduce itself*
(or similar), it should briefly explain its capabilities **and** the general things
the bot can do itself — e.g. which games are available. Today "@SuperBot introduce
yourself" produces a generic blurb (server management + BTD6) because the message
matches no command-catalog trigger, so only the static persona reaches the model and
games/economy/progression are never mentioned.

Plan: give the model a curated, always-present capability overview + intro guidance in
the AI instruction stack, and let intro-style phrasing inject the live command catalog.

(Born-red card per Q-0133 — flipped to `complete` as the final step.)
