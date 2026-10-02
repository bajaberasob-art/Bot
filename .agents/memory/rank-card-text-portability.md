---
name: Rank-card text portability
description: Why rank-card text must not depend on host fonts or optional Pillow shaping.
---

Keep rank-card Arabic rendering independent of system fonts and optional RAQM support.

**Why:** The installed Pillow wheel reported no RAQM support, and the project had no bundled fonts. Importing Pillow successfully is not proof that Arabic joins and reads correctly.

**How to apply:** Preserve explicit Arabic shaping and bidirectional ordering with the portable font set. When changing typography, visually inspect mixed Arabic/Latin names as well as emoji; a PNG-validity test alone cannot detect missing glyphs or disconnected Arabic letters.