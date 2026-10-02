---
name: Lona leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the Lona leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user requires separate authorization for each phase and preservation of unrelated bot systems and existing data.

**How to apply:** Phase 1 is the additive SQLite foundation; Phase 2 is the independent text XP engine. Phase 2 does not authorize voice XP, reaction XP, streaks, overtake alerts, rank cards, commands, dashboard, REST API, or public leaderboard. Wait for the user's instruction "START PHASE 3" before beginning voice XP.