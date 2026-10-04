# Plan: localization pass (July 2026)

- Owner: Dmitri Vale
- Date: 2026-07-20
- Status: complete — shipped in 2.9.0 (2026-07-06) for app strings; store listings land with 3.0

## Scope

Twelve locales added to the five launch locales (English, German, Spanish, French, Japanese): Portuguese (Brazil), Italian, Dutch, Polish, Swedish, Finnish, Czech, Turkish, Korean, Chinese (simplified), Russian, and Arabic. The Arabic locale carries the first right-to-left layout support, which is why this pass took a full train instead of riding along.

## Numbers

- 1,840 strings in the base catalog; 1,812 translated in all 12 new locales at ship. The 28 stragglers are the notification-channel labels and two recovery-shelf errors, cleared by 2026-07-17.
- String freeze: 2026-06-15 to 2026-07-01. Two freeze exceptions granted, both bug-fix strings, both approved by Tomas within an hour.
- Translation partner turnaround: 9 days for the first full pass, 3 days for the review pass.

## Pseudo-localization gate

Before any real locale ships, the build runs the pseudo-loc harness: every string is inflated 40%, bracketed, and accented, and screenshots are taken on the four smallest supported viewports. The gate caught 31 layout breaks in June — 19 in the onboarding funnel v2 (long German and Finnish account-creation labels), 7 in the boards list, 5 in the composer. All fixed before freeze.

## RTL specifics

Arabic required mirroring the swipe affordances (Quick Capture's swipe-down is direction-neutral, but the board swipe actions are not), flipping the boards-list indentation, and one deliberate exception: task checkboxes stay on the left, because the 40-participant Arabic beta cohort unanimously kept them there when asked in the 2026-06-24 review session.

## Format handling

Dates, times, and numbers move to locale-aware formatters everywhere; the two hardcoded mm/dd call sites found by the harness were both in digest previews. Week-start day follows locale (Sunday/Saturday/Monday families). The reminders travel spec's daypart re-anchoring (`specs/reminders-travel.md`) already uses absolute offsets, so no scheduling code changed in this pass.

## Known gaps carried forward

- The 18-character channel-label truncation in Finnish and Czech (fix approved 2026-08-21, ships in 3.0).
- Store listings, screenshots, and the onboarding imagery are English-only until the 3.0 train.
- The pseudo-loc gate runs on demand but is not yet wired into the release checklist — committed in the midyear refresh for H2.
