# Reminder delivery surfaces

- Author: Maya Okafor
- Date: 2026-08-31
- Status: active

## Surfaces, in priority order

A due reminder can land on four surfaces, tried in this order until one succeeds:

1. **Lock-screen banner** — full alert with sound and vibration, if the OS permits.
2. **Notification tray** — silent delivery, icon badge contribution.
3. **Morning digest** — folded into the next scheduled digest batch.
4. **In-app shelf marker** — a dot on the board tab, picked up at next open.

Each reminder records which surface it reached; that record drives the delivery report in Settings (added in 3.0).

## Suppressed-alert behavior

When the OS reports that an attention profile is active — the user has asked the device to suppress interruptions — the banner attempt is skipped entirely. The reminder goes straight to the tray without sound or vibration and is additionally folded into the next morning digest so it is not lost. Board owners on Herd Plus may mark a reminder as a priority ping, which requests an exception from the suppression; at most 2 such exceptions per device per night are honored, and the third is demoted to the tray. This cap exists because the 2026-06 support data showed three accounts abusing owner pings as a wake-up service, which generated 11 complaints from list members in one week.

## Wearable and desktop mirrors

A paired wearable shows the same tray-level (silent) content when suppression is active; it never escalates to a buzz. The desktop companion mirrors tray state only and adds nothing audible of its own.

## Fallback timer

If no surface confirms receipt within 10 minutes (device off, app uninstalled on a replacement phone), the reminder enters the shelf flow defined in `specs/reminders-rework-spec.md` and appears in the in-app shelf marker surface.

## Telemetry

Delivery success is measured per surface. Week of 2026-08-24: banner 71%, tray 22%, digest 5%, shelf marker 2%. Suppressed-alert nights shift roughly 18% of volume from banner to tray plus digest; that shift is expected and not counted as failure.
