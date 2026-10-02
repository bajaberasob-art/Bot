---
name: PRIME leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the PRIME leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phases 1–6 cover the SQLite foundation, text/voice/reaction XP, streaks, overtake events, the Phase 5 rank-card generator, and Discord `/rank`/`/top` commands. Phase 7 and Phase 8 were separately authorized and completed; Phase 8 connects the dashboard to authenticated SQLite-backed leveling APIs and the existing rank-card generator. Do not start Phases 9 or 10 until explicitly authorized; wait for the exact instruction "START PHASE 9".