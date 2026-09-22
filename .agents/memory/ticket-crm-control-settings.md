---
name: Ticket CRM control settings
description: Durable rules for the next-generation ticket dashboard's additive settings and permission persistence.
---

Ticket CRM control settings are additive to the legacy ticket configuration. Partial saves, especially permission-matrix saves, must preserve all unrelated close/archive, channel, panel-mode, and transcript settings.

**Why:** The dashboard has several independent modules that save from separate tabs. A partial request that writes defaults can silently undo live ticket behavior.

**How to apply:** Keep new settings in additive SQLite columns/JSON fields, normalize them on reads, and make update helpers merge omitted values with the current row before writing.