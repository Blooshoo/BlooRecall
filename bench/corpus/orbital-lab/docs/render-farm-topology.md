# Render farm topology

Marco Deluca, 2026-01-22, written in the cold aftermath of the heat week.
Structural reference; operational procedure lives in the operations handbook.

## Render farm

### Thermal envelope

Exhaust probes drive the fan curve, not die sensors: reacting to the die means
chasing it in circles, which the January saga demonstrated at length. At a die
reading of 83 °C the scheduler refuses new fragments and lets the pool drain
before accepting more — a soft ceiling, hit perhaps twice a quarter since fan
curve v3 shipped. Row 2's filters are on a quarterly rotation in Bram's
calendar; the January week is the reason that rotation exists, and the poster
that blocked renderlet-17 now hangs in the corridor as a monument.

### Node classes

Three kinds of iron. The big iron: rows 1–2, four encoder pipelines each,
does the nightly bulk. The workhorses: rows 3–4, two pipelines each, handles
the standard shift load with the big iron idle or failing. The stragglers:
row 5, single pipeline, retired from bulk work but kept for QC renders and the
kindled pool experiments — they are slow and trustworthy, which is its own
virtue. Scheduling prefers rows in order and drains in reverse.

### Spool layout

Each node owns two spool disks, spool-a and spool-b, striped so a reel's read
stream never competes with its own write stream. Compaction runs immediately
after the ledger roll, never inside a shift window — the February stall
census bought that rule with 17 stall events on one node. Watermark alarms at
0.90 and 0.95; the first means "plan", the second means "now".

## Cages and feeds

Cage A (12 rigs, 240 fps) and cage B (8 rigs, 120 fps) feed the same farm
through the hose. The farm is cage-agnostic; only the QC reference comparison
knows which cage a fragment came from. Cage C is on the autumn roadmap.
