# Scale review — May 2026

- Date: 2026-05-18, 60 minutes
- Attendees: Priya Raghunathan, Maya Okafor, Dmitri Vale, Tomas Lindgren
- Focus: fleet state after the April cutover and the May migration train

## Fleet snapshot (week of 2026-05-11)

- 2.1 million active devices, 1.8 million boards, 9.4 million edits per week.
- Reconciliation: 98.6% of passes within the 90-second budget (v1 baseline was 97%; the v2 slot allocator is doing its job). Deep-queue devices (2,000-entry campers) clear in a median of 3 drain passes, exactly as the cutover plan predicted.
- Storm machinery: one shed state the entire month (2026-04-28, 11 minutes, demand spike from a viral board import), shed worked, zero queue-overflow-class rejection storms since the cutover. Priya notes the old overflow guard code is now officially dead weight scheduled for removal with v1 retirement.

## Cutover retrospective (brief, the plan did its job)

- The staggered regional flip held; staging to primary in 20 minutes.
- Zero automatic rollback triggers fired; zero quarantined reconciliation entries remained at the 14-day mark.
- v1 retires 2026-04-20 as planned; the rollback window is closed, and everyone acknowledged it out loud, which was the point of writing the date into the plan.

## Migration train results

The herd-store schema v2 patch: p95 migration time in production 11.9 seconds versus 11 in the test fleet (within 8%, as the plan required). 31 tickets, 28 answered with the first-launch macro. 3 wipe-and-resyncs, all one bad-flash device. Dmitri: "the smallest-first ordering paid for itself in the first hour."

## Onboarding check-in

71% completion at three weeks (target 75), time to first task 2:05 (target 2:30, beaten), permission grant 81% (the contextual ask is a clear win), co-retention 77% against the 78% guardrail. Action: Dmitri takes the sample-board variant experiment; results to the July roadmap session.

## New pressures registered

- Reminder tickets keep climbing (the rework cannot come soon enough; beta staged September).
- Quarantine review tooling: manual inspection survived the soak, but Tomas wants the batch-inspect tool before 3.0 makes the shelf visible to everyone. Priya owns it, due 2026-09-30, slipping it is explicitly allowed; slipping the beta is not.
- Storage growth on the cold shelf is on the linear path the retention spec predicted (2.1 TB, 40 GB/month); no action, monitored quarterly.
