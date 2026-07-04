# No-transcript secret plumbing — moving secrets without ever printing them (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, owner-requested harvest). Not approved for
> implementation.

## The problem it solves

Q-0213's premise is that agents never need the owner "to enter certain values" — but several
standing tasks are secret *moves* between stores: Railway `DATABASE_PUBLIC_URL` → GitHub secret
(the backup workflow's rotation note says exactly this goes stale), future project tokens → GitHub
secrets (plan §6 R-3), new-project variable bootstrap (§4), test-guild webhook URLs. An agent doing
this naively `echo`s the value — landing it in a transcript, a session log, or a shell history.
Today's sessions held the line by hand (variable *names only*); a pattern held by discipline is one
tired session away from a leak.

## The idea

A small `scripts/secret_plumb.py` runbook tool where secrets flow **process-to-process, never
through text I/O**: read from source API (Railway GraphQL / env) → write to destination API
(GitHub Actions secret via libsodium-sealed PUT, Railway `variableUpsert`) inside one process;
stdout prints only `source → dest: <NAME> (sha256:<first8>) OK`. Supported routes to start:
railway-var → gh-secret, gh-secret rotation from railway, env → railway-var. The hash-prefix
receipt lets a later session verify "same value?" across stores without ever seeing it.

## Why it's worth having

It is the missing safety half of the full-automation grant: Q-0213 removed the owner from the
loop; this removes the *transcript* from the loop. Also directly needed twice in the near-term
roadmap (R-3 bootstrap; the DATABASE_PUBLIC_URL staleness class), and a natural portable
substrate-kit tool (every automated repo has this plumbing problem).

## Route

S5 (operations) / substrate-kit candidate · small tool + a journal Rule ("secrets move via
secret_plumb, never via echo/paste"). The GitHub half needs `secrets: write`-capable auth
(the fine-grained PAT/App the workflows already use — verify scope at build time).
