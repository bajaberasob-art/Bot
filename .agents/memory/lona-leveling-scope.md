---
name: Lona leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the Lona leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phase 1 is the additive SQLite foundation; Phase 2 is text XP; Phase 3 is voice XP; Phase 4 is reactions, streaks, and internal overtake events; Phase 5 is the rank-card generator only. Phase 5 does not authorize /rank, /top, aliases, dashboard, REST API, public leaderboard, or a final overhaul. Wait for the user's explicit instruction "START PHASE 6" before beginning the next phase.