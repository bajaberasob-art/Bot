---
name: Lona leveling scope
description: Authorization boundaries for the new leveling system.
---

Implement the Lona leveling system in exactly ten separate phases. Stop after each phase and wait for a new instruction before proceeding.

**Why:** The user explicitly restricted the current authorization to Phase 1 and required unrelated bot systems and existing data to remain intact.

**How to apply:** Phase 1 covers additive SQLite foundations and reusable helpers only. Chat/voice XP engines, Discord commands, rank cards, dashboard, REST API, and public leaderboard require later-phase authorization.