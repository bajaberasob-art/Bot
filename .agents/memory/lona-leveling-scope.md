---
name: PRIME leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the PRIME leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phases 1–6 cover the SQLite foundation, text/voice/reaction XP, streaks, overtake events, the Phase 5 rank-card generator, and Discord `/rank`/`/top` commands. Phase 7 has been separately authorized and completed as a dashboard-only milestone. Do not start Phase 8 or later, add leveling REST endpoints, or change backend settings until explicitly authorized; wait for the exact instruction "START PHASE 8".