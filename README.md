# MarketForge Attribution Analytics

MarketForge is a privacy-aware marketing measurement platform for multi-touch customer journeys. It validates event-level telemetry, reconstructs point-in-time conversion paths, compares deterministic attribution models, estimates Markov removal effects, evaluates controlled experiments and simulates constrained channel-budget allocations.

## Implemented capabilities

- strict event contract, UTC normalization, consent filtering, event deduplication and revenue invariants
- journey reconstruction using the first conversion and configurable lookback windows to prevent post-conversion leakage
- first-touch, last-touch, linear, time-decay and position-based revenue attribution
- cross-model sensitivity analysis and exact revenue-conservation checks
- first-order Markov transition model with normalized channel removal effects
- channel KPIs including spend, CTR, CVR, CPA, attributed revenue and ROAS
- portfolio funnel and monthly acquisition-cohort reporting
- two-arm conversion experiment evaluation with lift, standard error, confidence interval and significance flag
- bounded budget allocation scenario using channel efficiency and diminishing-return response curves
- FastAPI endpoints and an interactive Streamlit command center
- deterministic synthetic sample data; no advertising-platform or customer data
- automated Ruff, Black and pytest gates for Python 3.11 and 3.12
- non-root Docker image and Compose services for API and dashboard

MarketForge is a portfolio/reference implementation. It does not claim causal attribution from observational paths, replace a production identity graph, or directly modify advertising accounts. Markov removal effects describe modeled journey dependence; incrementality requires randomized or defensible quasi-experimental evidence.

## Why this matters

Marketing budgets are often allocated using last-touch attribution or intuition. That can
systematically overvalue bottom-funnel channels such as branded search and retargeting while
undervaluing channels that create demand earlier in a journey. MarketForge makes that bias visible:

- `GET /api/v1/attribution/compare` shows how first-touch, last-touch, linear, time-decay, and
  position-based models distribute the same revenue across the same journeys.
- `GET /api/v1/markov` provides a model-independent comparison through channel-removal effects,
  exposing channels that observed journeys suggest are difficult to replace.
- `POST /api/v1/budget/scenario` converts attributed efficiency into bounded reallocations with
  diminishing-return response curves instead of assigning unlimited budget to the highest ROAS.
- `POST /api/v1/experiments/evaluate` reinforces the core guardrail: attribution and Markov outputs
  are associational, so consequential reallocations should be validated with randomized holdouts.

The platform therefore forces an important decision question before money moves between channels:
which attribution convention is being trusted, and how would the recommendation change under a
different defensible assumption?

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
make check
```

Run `make api` and open `/docs`, run `make dashboard`, or start both services with `docker compose up --build`.

## API surface

| Method | Route | Purpose |
|---|---|---|
| GET | `/health` | Liveness and sample-data readiness |
| GET | `/api/v1/quality` | Event and journey quality profile |
| GET | `/api/v1/funnel` | Impression, click and conversion funnel |
| POST | `/api/v1/attribution` | Channel revenue under a selected model |
| GET | `/api/v1/attribution/compare` | Attribution model sensitivity |
| GET | `/api/v1/channels` | Channel efficiency scorecard |
| GET | `/api/v1/markov` | Markov removal effects |
| GET | `/api/v1/cohorts` | Monthly conversion cohorts |
| POST | `/api/v1/experiments/evaluate` | Binary experiment evaluation |
| POST | `/api/v1/budget/scenario` | Constrained budget scenario |

## Architecture

```text
Event telemetry -> contract + consent -> point-in-time journeys
                                      -> attribution / Markov / funnel
                                      -> experiments / budget scenarios
                                      -> FastAPI + Streamlit
```

See [architecture](docs/ARCHITECTURE.md), [data contract](docs/DATA_CONTRACT.md), [attribution model card](docs/MODEL_CARD.md), and [privacy notes](docs/PRIVACY.md). Every implemented claim above maps to committed code and automated tests.
