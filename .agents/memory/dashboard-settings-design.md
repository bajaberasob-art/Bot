---
name: Dashboard settings & DB conventions
description: Non-obvious decisions behind the guild-settings persistence, dashboard authorization and how to test the dashboard without Discord OAuth.
---

- Never drop/recreate `guild_settings`; extend it additively and keep legacy columns mirrored.
  **Why:** the live SQLite file already holds user balances/XP; the user ruled out recreating tables.
- Concurrency control is an integer revision, not timestamps. A nonzero expected revision must never create a row (that would let a stale client resurrect deleted settings).
  **Why:** second-resolution timestamps collide; the upsert insert arm silently bypassed the predicate once.
- The settings cache is process-local and published only after commit; any writer outside `database.py` must invalidate it or accept up to a minute of staleness.
- Dashboard authorization is per request AND per SSE tick: owner or Administrator bit, checked live through the bot, never trusted from the login-time guild list. Streams must drop as soon as a re-check fails.
- Frontend rule: rebase only the user's delta onto newer snapshots (SSE/409). Replacing the baseline while keeping a full old draft turns remote edits into "local changes" and overwrites them.
- Frontend URLs stay relative (no leading slash) because the dashboard may be mounted under a path prefix; snowflakes travel as strings.
- To test the dashboard in a browser without OAuth, use the harness under `tests/` that fakes the bot and seeds a session; the workspace bot is in zero guilds and OAuth env vars are not configured.
- After a command-policy save, update both the command row and the in-memory registry policy before rerendering the drawer.
  **Why:** rerendering from a stale registry snapshot makes a successful save appear to revert aliases and policy controls.
- Chip editors must include valid text still pending in the input when the save button is clicked, and successful saves should keep the detail drawer open.
  **Why:** mobile users commonly save without pressing Enter, and closing/reloading the drawer made a successful mutation look like a reset.
- The dashboard cookie uses a sliding expiry on authenticated `/api/me` requests, but the authoritative session store remains process-local.
  **Why:** refreshing the browser lifetime improves long-running dashboard use without pretending that an in-memory OAuth session survives a bot process restart.
  **How to apply:** preserve the server-side expiry check and do not describe cookie renewal as restart persistence; use the existing publishing/login follow-up for cross-restart auth.
- Optional ticket-control updates must resolve the `_UNSET` sentinel to the existing value before type coercion; an omitted nullable field must remain `None`, not be cast as an object.
  **Why:** permissions-only saves mirror into the legacy ticket config and can otherwise fail before the new permissions are committed.
  **How to apply:** normalize each omitted nullable field through one preserve-or-coerce helper before SQLite writes.
