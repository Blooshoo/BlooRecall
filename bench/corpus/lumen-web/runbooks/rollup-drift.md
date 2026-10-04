# Runbook — ERR_ROLLUP_DRIFT_1180 (pre-aggregate divergence)

First seen: 2026-04-29. Owner: Rafa Lindqvist.

## What it means

A pre-aggregated value differs from the same range recomputed from raw samples beyond tolerance. Default tolerance is 500 ppm (`rollup.drift_tolerance_ppm`); the drift checker samples 1% of tiles hourly.

Typical log line:

`{"code":"ERR_ROLLUP_DRIFT_1180","series":"lat.p95@edge-3","ppm":1840,"range":"2026-04-28T22:00Z/23:00Z"}`

## Usual cause

Late-arriving samples landing after their chunk was sealed. The pre-aggregates were computed without them; the raw store has them.

## Repair

1. Confirm the range from the log line.
2. Run the repair job: `lumenctl rollup repair --series <id> --from <start> --to <end>`. It re-aggregates from raw and swaps the chunk atomically.
3. Re-run the checker for that range; drift must read 0 ppm afterwards.
4. If the same series drifts twice within a week, check its ingest lag — a slow upstream producer can keep outpacing sealing, and you will keep repairing forever.

## Do not

Do not delete chunks by hand. A repair that fails halfway is safe (the swap is atomic); a hand-deleted chunk is not recoverable without a full replay from raw.
