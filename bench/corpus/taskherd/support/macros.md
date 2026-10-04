# Support macros

- Maintainer: Tomas Lindgren
- Last reviewed: 2026-05-11
- Placeholders use curly braces: `{user_name}`, `{board_name}`, `{task_title}`, `{device_model}`. Never ship a macro reply with an unfilled placeholder — the 2026-03-13 incident where a user was addressed as "{user_name}" for the second time is why the checklist exists.

## How to use

Pick the macro, fill the placeholders, then add one personalized line. The personalized line is not optional: replies with one got a 41% satisfaction score in the 2026-04 sampling, replies without got 22%. Tone rules: plain sentences, no exclamation marks, never blame the user's device, never promise a date we do not control.

## The macros

### MACRO-11 — first response, greeting

Thanks for writing in, `{user_name}`. This is `{agent_name}` on the taskherd team, and I want to get this sorted for you. Could you confirm the app version from Settings > About and the device model so I am looking at the right build?

### MACRO-24 — sync backlog and queue drain

What you are seeing is the local queue draining. When taskherd cannot reach the internet, edits wait on the device and merge once the connection is back — oldest first, in batches. Large backlogs clear over a few minutes on a good connection, and nothing is lost while it waits. If `{board_name}` still looks wrong after ten minutes on a stable connection, reply and I will pull the sync trace for your account.

Follow-up procedure (also used to clear clock-glitch flags per the region-change spec): request a trace with the account ID, check the queue depth gauge on the sync dashboard, escalate to Priya if depth exceeds 500 after two clean passes.

### MACRO-31 — goodwill and refunds

I am sorry this one cost you time, `{user_name}`. I have applied a `{credit_length}`-month credit to the account; it appears on the next billing date and needs no action from you. If you would rather have the refund path instead, reply within 7 days and I will switch it.

### MACRO-41 — first launch slower after update

That slower first launch is expected exactly once: the update converts the on-device store to the new layout, and it happens on your device, not our servers. Typical time is a few seconds; `{device_model}` measured under 12 seconds even on large libraries. After that first launch, opening speed is back to normal — and measurably better than before, per the cold-start audit.

### MACRO-42 — badge showing the wrong count

The badge is computed on-device and can go stale after a restore or an account switch. Opening the app starts a backfill that corrects it from the server. If it is still wrong after two opens, we can trigger a forced repair from here — say the word and I will run it, which usually fixes it on your next open.

## Checklist before sending

1. Placeholders filled.
2. One personalized line present.
3. No promises with dates; "next update" is the strongest commitment allowed.
4. If the ticket mentions missing text or lost tasks, stop — data-loss tickets skip macros entirely (see `escalation-playbook.md`).
