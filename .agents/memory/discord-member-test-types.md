---
name: Discord member fixture types
description: Why member conversion tests need genuine Discord member objects.
---

Use genuine Discord member objects in tests that exercise Discord's member converter, not only duck-typed objects with matching IDs and names.

**Why:** The converter performs an actual Member type check. A cached duck-typed fixture can be rejected and cause a network lookup, incorrectly making a valid cached-member test fail as if the member were missing.

**How to apply:** Lightweight fixtures remain appropriate for isolated rendering and database tests. When testing native prefix member conversion, construct real members with complete required API fields and test invalid arguments explicitly rather than letting an optional converter silently select self.