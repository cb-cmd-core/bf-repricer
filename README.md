
# bf-repricer

A modular, event-driven Betfair Horse Racing repricer.

This project is designed as a **long-running service**, not an interactive script.
It ingests live (or near-live) market data, maintains an internal market state,
computes fair prices under uncertainty, and optionally executes orders subject
to explicit risk controls.

The architecture prioritizes:
- separation of concerns
- reversibility of pricing logic
- robustness under partial data, disconnects, and market regime changes

---

## Design Principles

1. **Ingestion ≠ Pricing ≠ Execution**
   Each layer can be modified, replaced, or disabled independently.

2. **State is explicit**
   All pricing decisions are made against a reconstructed market state, not raw ticks.

3. **Fail closed**
   On stale data, inconsistent state, or unknown market status, execution halts.

4. **Paper-first**
   Live execution is an opt-in mode layered on top of identical pricing logic.

5. **Reproducibility**
   Market data can be replayed to debug decisions post hoc.

---

## High-Level Architecture
Market Data

│

▼

Ingest (stream / poll)

│

▼

Normalize → Domain Events

│

▼

MarketState (in-memory, idempotent)

│

▼

Pricing Model

│

▼

Guards & Risk Filters

│

├── Paper Execution (default)

└── Live Execution (explicit enable)

---

## Project Layout
src/bfrepricer/

config/         # environment + runtime configuration

domain/         # domain types and events

ingest/         # streaming and polling clients

state/          # market state + reconstruction logic

pricing/        # fair price models and sizing

execution/      # order placement and risk controls

app/            # runnable entrypoints

observability/  # logging and metrics

—-
---

## Execution Modes

- **Paper mode (default)**  
  Prices are computed and intended orders are logged, not sent.

- **Live mode**  
  Requires explicit configuration and passes through risk controls.

---

## Safety & Risk Controls

Execution is disabled automatically when:
- market data becomes stale
- market status is suspended or transitions unexpectedly
- price deltas exceed configured sanity bounds
- exposure or order rate limits are exceeded

---

## Setup (Local)

1. Create a virtual environment
2. Copy `.env.example` → `.env`
3. Populate Betfair credentials
4. Run one of the app entrypoints:

```bash
python -m bfrepricer.app.run_paper