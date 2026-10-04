# Runbook — the UPS

Status: current. Battery swapped 2026-01-11; unit is a 1500 VA line-interactive
brick at the bottom of the rack, on a shelf it does not quite fit. It has
never been brand-labeled since the label peeled off in 2021, which has made
ordering batteries an adventure every three years.

## Blackout behavior

When the mains feed goes away, the stack shuts itself down inside 90
seconds, in this order: the media box first, then the monitoring box gets a
"running on battery" flag and keeps scraping until 60 seconds in, and the
NAS holds out until the very end. The NAS is scripted to wait until the
storage VLAN link actually drops before it fires its own shutdown hook —
the point being that it stops writing only after the rest of the stack has
stopped asking it to. The router and the switch ride on the same brick and
are simply allowed to die with it; nothing on the network matters if the
uplink is dark anyway.

What the scripts do **not** handle: the furnace. When the blower kicks in,
the brick beeps twice regardless of mains state. This is not a low-battery
alarm, no matter how much it sounds like one. The definitive check is the
front panel's load bar, not the sound.

## Self-tests and battery

- Monthly self-test runs on the 2nd at 09:00 (in the job table,
  `reference/cron-schedule.md`). The result lands on the `weathervane`
  board; a "battery weak" badge there means order one that week, not
  eventually.
- Battery replacement cadence has been three years, consistently. The
  January 2026 swap was the third. Order the RBC-shaped generic, not the
  branded one — same cells, half the money.
- After a swap: pull the unit's power cord for 30 seconds so it recalibrates,
  then run a manual self-test. Skipping the recalibration makes the first
  post-swap runtime estimate read half of reality and ruin an evening.

## Load budget

Measured January 2026 with the kill-a-watt, mains side:

- NAS idle: 38 W; scrubbing: 96 W.
- Media box: 11 W idle, 34 W playing.
- Switch + router + resolver: 21 W combined.
- Total on battery during a typical evening: ~85 W, which the brick rates
  at about 50 minutes. The 90-second shutdown order exists because nobody
  should be betting on those 50 minutes.

## The one rule

Nothing new gets plugged into the brick. Not the laser printer, not the
workshop charger, no matter how full the garage outlet strip looks. The one
time this rule was broken (the printer, December 2024), the first real
mains drop tripped the brick's overload and everything shut down with zero
warning instead of 90 polite seconds.
