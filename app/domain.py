from dataclasses import dataclass

TOUCHPOINT_COLUMNS = {
    "user_id",
    "journey_id",
    "event_id",
    "timestamp",
    "channel",
    "campaign",
    "event_type",
    "cost_eur",
    "revenue_eur",
    "consent",
}

EVENT_TYPES = {"impression", "click", "conversion"}


@dataclass(frozen=True)
class AttributionPolicy:
    lookback_days: int = 30
    half_life_days: float = 7.0
    position_first: float = 0.4
    position_last: float = 0.4

    def __post_init__(self) -> None:
        if self.lookback_days < 1:
            raise ValueError("lookback_days must be positive")
        if self.half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        if self.position_first < 0 or self.position_last < 0:
            raise ValueError("position weights cannot be negative")
        if self.position_first + self.position_last > 1:
            raise ValueError("position weights cannot exceed one")


@dataclass(frozen=True)
class ExperimentResult:
    control_rate: float
    treatment_rate: float
    absolute_lift: float
    relative_lift: float
    standard_error: float
    ci_low: float
    ci_high: float
    z_score: float
    statistically_significant: bool
