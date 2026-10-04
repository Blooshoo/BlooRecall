# Notes — January scrub findings

Written 2026-01-26, the morning after the monthly scrub. Filed under
notes because it started as "scrub found something" and turned into a
drive replacement.

## What the scrub found

The January scrub (ran 2026-01-25, 4 h 02 m) reported **12
checksum-corrected sectors on drive bay 3**, and nothing anywhere else.
Corrected, not uncorrectable — the pool healed itself from redundancy and
no data was touched. But twelve corrections on one drive in one pass,
after zero on that drive in December, is a drive writing its resignation
letter.

## What was done

1. Confirmed the corrections were confined to bay 3 (the scrub log lists
   them per-member; all twelve were).
2. Pulled the SMART data: reallocated sector count up 8 since December,
   pending sectors up 12. That plus the scrub result is the full pattern;
   a flaky cable produces correctable errors too, so the cable was
   reseated first and the drive re-scrubbed mid-week — corrections
   repeated on the same LBAs, which cleared the cable theory.
3. Ordered a replacement (same capacity, different manufacture batch on
   purpose — see the shopping list rule about pairs).
4. Swapped on 2026-02-01. The pool rebuilt in 9 h 20 m at the
   deliberately throttled rebuild rate, so evening sessions stayed
   smooth. The old drive is now the cold spare in the drawer, labeled
   "quarantine — retired 2026-02-01, do NOT trust" — it gets used for
   scratch imports only.

## What this validated

- The scrub-every-month cadence caught this with zero data loss. The
  scrub-before-firmware-upgrade rule in
  `runbooks/nas-firmware-upgrade.md` exists for exactly this reason.
- The "clean within 14 days" pre-check would have correctly refused a
  firmware upgrade during the window where bay 3 was misbehaving.
- Drive bay 3 runs 3–4 °C hotter than its neighbors per the board's
  thermal tile. The replacement went in with a fresh fan curve for that
  bay; worth watching, not worth worrying about yet.

## Standing rule going forward

Any scrub with more than zero corrections on one member gets a SMART
pull and a reseate-and-rescrub within the week. More than five
corrections on the rescrub, or any repeat on the same LBAs, is a
replacement order — no waiting for the annual review to argue about it.
