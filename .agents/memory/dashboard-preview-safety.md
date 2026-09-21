---
name: Dashboard preview safety
description: Safe way to review the dashboard visually without weakening production authentication or permissions
---

Dashboard design reviews should use the isolated mockup sandbox with realistic static data and local-only interactions. Do not add production routes, fixed passwords, session shortcuts, or permission bypasses just to capture a screenshot.

**Why:** The dashboard contains real Discord controls and server data; a visual preview must not become an accidental backdoor when the app is published.

**How to apply:** Put new visual dashboard previews under the mockup sandbox, keep their API/auth dependencies stubbed, and verify the production OAuth flow remains unchanged.