---
name: Ticket system architecture
description: Durable design rules for persistent Discord tickets, transcript storage, and staff KPI calculations.
---

Ticket panels and ticket controls use persistent custom IDs, while ticket records, transcripts, and ratings live in SQLite.

**Why:** Discord reconnects discard in-memory View instances, but open ticket channels and rating outcomes must remain traceable across restarts.

**How to apply:** Register saved panel views during extension setup, keep channel ownership and support-role IDs on each ticket record, and scope every database mutation by guild and ticket ID.

Response time starts at ticket creation and ends at the first verified support-staff message; resolution time ends at the close action. Ratings attach to the closing staff member.

**Why:** These timestamps map directly to support KPIs and avoid counting the ticket owner's messages as staff response.

**How to apply:** Record the first staff message once, preserve null response times for unanswered tickets, and calculate averages with null-safe SQL.

The dashboard transcript viewer should remain an in-page, sandboxed iframe fed by the no-store HTML endpoint.

**Why:** Staff need to inspect archived conversations without losing dashboard context, while transcript HTML must not gain script privileges in the operator's page.

**How to apply:** Keep transcript responses inline and uncached, set an empty iframe sandbox for the viewer, and scope every transcript lookup to both guild ID and ticket ID.

Newly deployed panels use a guild-scoped persistent select view backed by `ticket_config` and `ticket_options`; legacy button panels remain restorable.

**Why:** A dropdown must rebuild its options after a gateway restart without trusting process memory, while existing servers must not lose their deployed controls during migration.

**How to apply:** Persist panel message/embed state and option metadata, restore the select view during cog setup, and enforce duplicate-open checks by `(guild, user, category)` rather than across all categories.

Dashboard panel publishing must call the existing community deployment path with the saved message and display mode, rather than creating a second ticket-panel implementation.

**Why:** Reusing the persistent Discord view registration keeps button/dropdown behavior, message replacement, and restart restoration consistent.

**How to apply:** Pass the panel's channel/message IDs and mode to the community cog, then retain the existing database record and API response shape for older dashboard clients.

Channel deletion must be preceded by transcript persistence, including for legacy closed records that do not yet have a transcript.

**Why:** A Discord channel can be deleted after an earlier partial close, and deleting it without backfilling the record permanently loses the conversation.

**How to apply:** Check for an existing transcript before any destructive delete; if absent, capture and save the channel history before removing the channel.