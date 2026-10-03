---
name: PRIME leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the PRIME leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phases 1–6 cover the SQLite foundation, text/voice/reaction XP, streaks, overtake events, the Phase 5 rank-card generator, and Discord `/rank`/`/top` commands. Phases 7, 8, and 9 were separately authorized and completed; Phase 8 connects the dashboard to authenticated SQLite-backed leveling APIs, while Phase 9 adds the public leaderboard. Do not start Phase 10 until explicitly authorized; wait for the exact instruction "START PHASE 10".

## Period leaderboard history

**Rule:** Daily, weekly, and monthly `/top` rankings use UTC award dates and are additive over lifetime XP. Do not reset lifetime XP or synthesize old period history.

**Why:** Legacy XP records have no award timestamps, so historical period totals cannot be recovered reliably. Fabricating a backfill would make the new rankings misleading.

**How to apply:** Record each new text, voice, reaction, and streak XP award in the same database transaction as its lifetime XP update. Period rankings begin when this ledger is introduced; all-time rankings continue using permanent totals.