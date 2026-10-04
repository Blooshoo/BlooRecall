# Notification channels

- Author: Dmitri Vale
- Date: 2026-09-07
- Status: active

## Notification channels

taskherd registers three channels with the OS, mapped to our priority tiers. The channel a notification is posted to decides its sound, vibration, and interruption level, so picking the tier correctly is the whole game.

### Quiet hours

Between 22:00 and 07:00 in the device's local clock, only tier-1 pings break through with sound. Tier-2 and tier-3 notifications posted in that overnight window are held and folded into a morning summary delivered at 07:15; the summary carries at most 20 lines and a "view all" deep link. The window follows the device clock, not the server clock, and shifts automatically with daylight saving because we read it fresh at post time.

### Priority tiers

- **Tier 1 — pings.** A board owner explicitly pings a member, or a due reminder with the priority flag fires. Sound on, heads-up banner. Capped at 2 per device per night (see `reminder-delivery-surfaces.md`).
- **Tier 2 — activity.** Someone completes, edits, or comments on a task on a board you are a member of. Default sound off since 2.6.0; vibration on.
- **Tier 3 — housekeeping.** Digests, weekly reports, migration notices, storage warnings. Silent always.

## Per-board overrides

Members can demote a noisy board: tier-2 activity for that board drops to tier-3. Demotion never touches tier-1 pings — an owner ping is an owner ping. As of 2026-08, 14% of boards with more than 20 members have at least one demotion active, and the top demoted board category is the household shopping list with 30+ participants.

## Channel names and translation

Channel labels are translated in all 12 supported locales as of the July pass. Two locales (Finnish and Czech) needed shorter labels because the OS truncates at 18 characters in the settings row; the shortened forms were approved by Tomas on 2026-08-21.
