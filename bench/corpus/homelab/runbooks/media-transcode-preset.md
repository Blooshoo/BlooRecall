# Runbook — the low-light transcode preset

Status: current. Created 2026-03-03. This documents `nq-720p-night`, the
transcode profile that exists purely because the main telly's dongle chokes
on anything heavier, and because nobody should re-litigate the settings at
22:30 on a school night.

## Where it lives

The profile is defined on `marquee` in `/etc/media/transcode/nq-720p-night.conf`.
It is referenced by name from the household guide app; do not rename the
file without also updating the guide app config, or sessions silently fall
back to the default profile, which is exactly the regression this profile
was built to prevent.

## What it sets, and why

- **Target resolution 720p.** The telly downscales anyway; the dongle's
  decoder is happier, and nobody has ever noticed at viewing distance.
- **Bitrate cap 4 Mbit.** This is the knob that matters. Below 3 Mbit the
  picture smears on panning shots; above 5 Mbit the dongle drops frames
  under load. 4 Mbit is the plateau.
- **Deinterlacing on, mode "blend".** The tuner recordings are still
  interlaced. The fancier modes eat CPU that the box does not have to spare
  while a session is active.
- **Audio passthrough for 5.1, stereo downmix otherwise.** The receiver
  handles 5.1 natively; the dongle does not, and its own downmix is awful.
- **Read-ahead 8 seconds.** This was tuned by experiment. Four seconds
  hitched on the weekly animated show (its file layout is fragmented); 16
  seconds made session starts feel broken. Eight is the compromise.

## When NOT to use it

Not for anything on the bedroom panel — that one decodes 1080p natively and
the preset just wastes quality. Not for the projector when it is plugged
straight into `marquee` over HDMI. The preset is for the dongle and only
the dongle.

## Changing it

1. Copy the file to `nq-720p-night.conf.staging` and edit that.
2. Test with the 21:00 slot show — it is the longest, most demanding thing
   the household regularly plays.
3. Swap the staging file over the live one and bounce the transcoder:
   `systemctl restart media-transcode`.
4. Verify in the guide app that the profile still resolves by name. If the
   app shows "default", stop and fix the name resolution before anyone
   notices the picture went soft.

## History

- 2026-03-03 — written down after the third "why does the picture look
  like soup" conversation. The answer, every time: it is the preset, the
  preset is intentional, here is the document.
