---
name: Scoped Discord command publication
description: Preserve remote command registrations when broad Slash sync is disabled.
---

Loading a Slash command locally is not the same as registering it with Discord. When a phase authorizes new commands while broad sync is disabled, register only that phase's commands and leave unrelated remote registrations untouched.

**Why:** The user requires every existing bot feature to remain working. A bulk replacement can remove remote commands that the current local tree does not represent; enabling broad sync is not implied by authorization of one feature.

**How to apply:** Register after all cogs load, honor the configured global/development-guild scope, and compare remote signatures before upserting to avoid rewriting unchanged registrations on each restart. Never bulk-sync from an individual cog while the tree is still being populated.