---
name: Lona streak dates
description: Calendar policy for daily leveling rewards and future claim entry points.
---

Daily leveling claims use UTC calendar days for everyone, independent of display timezone.

**Why:** Phase 4 required reliable date-boundary and duplicate-claim protection but provided no guild-specific calendar policy. One canonical calendar prevents changing a host or display timezone from changing reward eligibility.

**How to apply:** Later commands and interfaces must use the existing server-side claim policy, not client-supplied dates or local-day calculations. Introducing guild-specific calendars requires an explicit transition policy so users cannot gain extra claims or lose streaks during the change.