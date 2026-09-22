---
name: Overview telemetry boundaries
description: Rules for extending the Dashboard/Index overview without changing backend contracts.
---

The overview may derive presentation-only indicators from existing session, stats, actions, incidents, member, and channel payloads, but it must not invent unavailable business metrics or add a new backend route just for visual parity.

**Why:** The dashboard backend has stable API and authorization contracts; the visual overview needs to remain additive and safe when optional telemetry fields are absent.

**How to apply:** Treat fields such as messages, joins, leaves, and voice metrics as optional. Render empty/skeleton states when they are absent, keep all existing navigation and API URLs unchanged, and scope new styling to the overview view.