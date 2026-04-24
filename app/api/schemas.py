from pydantic import BaseModel, Field


class AttributionRequest(BaseModel):
    model: str = "time_decay"
    lookback_days: int = Field(default=30, ge=1, le=180)
    half_life_days: float = Field(default=7.0, gt=0, le=90)


class ExperimentRequest(BaseModel):
    control_conversions: int = Field(ge=0)
    control_visitors: int = Field(gt=0)
    treatment_conversions: int = Field(ge=0)
    treatment_visitors: int = Field(gt=0)


class BudgetRequest(BaseModel):
    total_budget_eur: float = Field(gt=0)
    model: str = "time_decay"
    min_share: float = Field(default=0.05, ge=0, le=1)
    max_share: float = Field(default=0.5, ge=0, le=1)
