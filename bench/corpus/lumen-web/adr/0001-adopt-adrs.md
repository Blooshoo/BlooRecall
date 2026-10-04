# ADR 0001 — We record architecture decisions as numbered ADRs

Date: 2025-09-14. Decided by: everyone, kickoff week. Status: accepted.

We keep architecture decision records in `adr/`, numbered from 0001. Format: context, options, decision, consequences. Once merged, a record is never edited; a successor replaces it and cites the number it retires. The old file stays put for history.

## Consequences

- A teammate who joins in a year can reconstruct why the storage layer looks the way it does without archaeology in chat.
- Cost: writing discipline. Every ADR needs a named owner and a date or it does not merge.
- Dot owns the numbering; gaps in the sequence are records that were proposed and dropped, and that is fine.
