# Onboarding — development setup

Written 2025-10-15 by Juno Park. Last touched 2026-02-20 (flag list refresh).

## Prerequisites

- Node 20.x, Go 1.23, postgres 16 with the columnar extension, redis 7 for the local bus.
- The repo boots a complete local estate from fixtures. No production access is needed, ever.

## First boot

1. `./scripts/dev.sh bootstrap` — builds the service tier, starts postgres and redis in containers, loads the demo estate (12 boards, roughly 180 series).
2. `./scripts/dev.sh seed` — 90 days of synthetic samples so every chart has something to draw.
3. `./scripts/dev.sh up` — web on :8310, service tier on :4310.

## Environment

Copy `env.example` to `.env`. The two values you usually touch: `LUMEN_INGEST_ENDPOINT` (default `http://localhost:4310`) and `LUMEN_DEV_PORT`. The local estate is open by design; nothing here is locked down.

## First-week tasks

- Ship a one-tile board end to end. This exercises the query cache and grain selection for real.
- Follow the on-call runbook for a fake page: break the local bus and watch the retry hop to the fixed fallback.
- Read ADR 0002 and ADR 0009 rev 2, then write a one-paragraph objection to each. Juno reviews these seriously; "it seems fine" fails.

## Who to ask

Rendering and interactions: Juno. Ingest, storage, query: Rafa. Palette and motion: Cece. Scope, audits, pager schedule: Dot.
