# Renderlet naming

Marco Deluca, 2025-09-24. Short note so nobody "improves" this later.

Farm nodes are `renderlet-01` through `renderlet-24`, assigned by row and
position: rows 1–5, six nodes per row, numbered left to right from the door.
The names are permanent. Hardware gets replaced, names do not — the history of
a node lives in the ledger under its name, and renaming a node orphans that
history.

Disks are `spool-a` and `spool-b` on every node, always. There is no spool-c
and there will not be.

Nicknames exist and are tolerated in speech only: row 5 is "the stragglers"
(older iron, kept for QC renders and the kindled pool experiments), renderlet-09
is "the stove" since the February stall investigation. Nicknames never appear
in configuration, dashboards, or ledger keys. If you write config against a
nickname, Marco will find you.

Why this matters: half of incident forensics is matching a log line to a
physical box under time pressure. Stable names, stable row arithmetic, no
creativity. The naming scheme is boring the way a fire exit is boring.
