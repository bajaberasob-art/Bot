---
name: PRIME leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the PRIME leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phase 1 is the additive SQLite foundation; Phase 2 is text XP; Phase 3 is voice XP; Phase 4 is reactions, streaks, and internal overtake events; Phase 5 is the rank-card generator; Phase 6 authorizes Discord /rank, shared rank aliases, and /top with TEXT/VOICE navigation only. It does not authorize dashboard changes, REST APIs, a public leaderboard, XP changes, or a final overhaul. Wait for the user's explicit instruction "START PHASE 7" before beginning the next phase.