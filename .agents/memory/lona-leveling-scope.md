---
name: Lona leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the Lona leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phase 1 is the additive SQLite foundation; Phase 2 is text XP; Phase 3 is voice XP; Phase 4 is reactions, streaks, and internal overtake events only. Phase 4 does not authorize rank cards, commands, dashboard, REST API, public leaderboard, announcement UI, or a final overhaul. Wait for the user's explicit instruction "START PHASE 5" before beginning the next phase.