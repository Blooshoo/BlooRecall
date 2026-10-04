# taskherd changelog

Patch releases (third version component above zero) are not itemized here; see the release train notes in `plans/`.

## 3.0.0-beta — 2026-09-08 (staged rollout, 5% of accounts)

- Reminders rework: alarm shelf concept, delivery quotas, morning digest batching. See `specs/reminders-rework-spec.md`.
- Reminder delivery on idle devices moved from deferred windows to exact scheduling.
- New sync rate-limit model fully enforced server-side. See `specs/sync-rate-limits.md`.

## 2.9.0 — 2026-07-06

- Interim fix for late reminders on idle devices (exact window requests).
- Shared board member avatars refresh correctly after role changes.
- Localization pass: 12 new locales, RTL layout fixes. See `plans/localization-pass.md`.

## 2.8.0 — 2026-05-25

- Client support for the herd-store schema v2 migration flow.
- Cold-start work from the April audit: p95 cold start reduced by roughly a third. See `plans/cold-start-audit-final.md`.

## 2.7.0 — 2026-03-23

- Onboarding funnel v2. See `specs/onboarding-funnel-v2.md`.
- Conflict resolution v2: later-edit wins with a recovery shelf. See `specs/offline-conflicts-v2.md`.
- Sync rate limits replace the old per-device throttle.

## 2.6.0 — 2026-02-02

- Push pipeline hardening: coalescing window and undelivered-batch replay.
- Badge backfill controls for support-triggered repairs.

## 2.4.0 — 2025-11-24

- Quick Capture: swipe-down composer from any screen, Capture action on notifications, automatically quick-saved drafts. See `specs/quick-capture-gesture.md`.

## 2.0.0 — 2025-10-27

- Shared boards GA with roles and a change feed.
- Herd Sync v1 replication protocol.
- Per-device sync throttling (since replaced; see `specs/sync-rate-limits.md`).
