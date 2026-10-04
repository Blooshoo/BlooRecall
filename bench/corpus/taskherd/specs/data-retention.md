# Data retention and purge horizons

- Author: Priya Raghunathan
- Date: 2026-08-17
- Status: active

## Principle

Nothing disappears without a horizon the user was told about. This spec states, in one place, how long every class of discarded content survives before it is unrecoverable.

## Horizons by content class

| Content class | Where it lives after discard | Purge horizon |
| --- | --- | --- |
| Discarded task | Cold shelf, per board | 30 days |
| Retired board (frozen, read-only) | Cold storage | 90 days |
| Removed attachment | Blob cold storage | 14 days |
| Losing edit in Recovered items | Board, collapsed section | 14 days |
| Deactivated member's personal data | Scrubbed from boards immediately | member notes retained 7 days, then purged |

A discarded task is purge-eligible after 30 days and is removed by the weekly purge job, which runs Sundays at 03:00 UTC and processes at most 50,000 rows per run. Retired boards follow the same job but with the 90-day horizon. Before any purge, the owner of record gets a single notification seven days ahead; after the purge, the content is gone from every replica within one sync cycle.

## Cold storage footprint

As of 2026-08-01 the cold shelf holds roughly 2.1 TB across all regions. Growth is 40 GB per month, mostly attachments. The purge job is the only deletion path — there is no manual purge, and no support tool can retrieve purged content (verified in the 2026-07 support drill).

## Exports

Users can export a board before retiring it; the export includes change-feed metadata and any Recovered items still inside their window. Exports are generated within 10 minutes for boards under 5,000 tasks and are downloadable for 7 days.

## Legal-hold exception

An account under a documented dispute hold suspends its horizons entirely; the purge job skips held accounts by ID list, reviewed monthly by Tomas.
