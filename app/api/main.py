from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.api.schemas import AttributionRequest, BudgetRequest, ExperimentRequest
from app.attribution import MODELS, attribute_revenue, compare_models
from app.budget import optimize_budget
from app.domain import AttributionPolicy
from app.exceptions import InsufficientDataError
from app.experiments import evaluate_binary_experiment
from app.ingestion import journey_table, load_touchpoints
from app.markov import removal_effects
from app.metrics import channel_performance, funnel, monthly_cohorts
from app.quality import quality_report

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "sample_touchpoints.csv"
app = FastAPI(title="MarketForge Attribution Analytics", version="2.0.0")


def _events():
    return load_touchpoints(DATA_PATH)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "sample_data": DATA_PATH.exists()}


@app.get("/api/v1/quality")
def quality() -> dict:
    return quality_report(_events())


@app.get("/api/v1/funnel")
def funnel_endpoint() -> dict:
    return funnel(_events())


@app.post("/api/v1/attribution")
def attribution(request: AttributionRequest) -> list[dict]:
    if request.model not in MODELS:
        raise HTTPException(status_code=422, detail=f"model must be one of {sorted(MODELS)}")
    events = _events()
    policy = AttributionPolicy(request.lookback_days, request.half_life_days)
    journeys = journey_table(events, request.lookback_days)
    result = attribute_revenue(journeys, request.model, policy)
    return result.groupby("channel", as_index=False)["attributed_revenue_eur"].sum().to_dict("records")


@app.get("/api/v1/attribution/compare")
def attribution_compare() -> list[dict]:
    events = _events()
    return compare_models(journey_table(events)).to_dict("records")


@app.get("/api/v1/channels")
def channels(model: str = "time_decay") -> list[dict]:
    if model not in MODELS:
        raise HTTPException(status_code=422, detail="Unknown attribution model")
    events = _events()
    attribution = attribute_revenue(journey_table(events), model)
    return channel_performance(events, attribution).to_dict("records")


@app.get("/api/v1/markov")
def markov() -> list[dict]:
    return removal_effects(_events()).to_dict("records")


@app.get("/api/v1/cohorts")
def cohorts() -> list[dict]:
    return monthly_cohorts(_events()).to_dict("records")


@app.post("/api/v1/experiments/evaluate")
def experiment(request: ExperimentRequest) -> dict:
    try:
        return asdict(evaluate_binary_experiment(**request.model_dump()))
    except (ValueError, InsufficientDataError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/v1/budget/scenario")
def budget(request: BudgetRequest) -> dict:
    if request.model not in MODELS:
        raise HTTPException(status_code=422, detail="Unknown attribution model")
    events = _events()
    attribution = attribute_revenue(journey_table(events), request.model)
    performance = channel_performance(events, attribution)
    try:
        return optimize_budget(performance, request.total_budget_eur, request.min_share, request.max_share).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
