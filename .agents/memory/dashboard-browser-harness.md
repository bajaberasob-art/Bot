---
name: Dashboard browser harness
description: The reliable way to serve an authenticated dashboard preview without Discord OAuth.
---

Run the manual dashboard harness with the workspace root on `PYTHONPATH`, then use its test login route to seed the administrator cookie before inspecting authenticated dashboard responses.

**Why:** launching the script directly makes Python resolve imports relative to `tests/`, so the project modules are not found.

**How to apply:** use `PYTHONPATH=. python tests/dashboard_harness.py` and keep the harness temporary; do not add it as a permanent workflow. Capture the cookie from the test-login 302 without repeatedly following the redirect, then call authenticated API routes once to avoid harness rate limits.