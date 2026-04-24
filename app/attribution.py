import math
from collections.abc import Callable

import pandas as pd

from app.domain import AttributionPolicy


def _eligible_touches(group: pd.DataFrame) -> pd.DataFrame:
    touches = group.loc[group["event_type"].isin(["impression", "click"])].copy()
    if touches.empty:
        touches = group.tail(1).copy()
    return touches


def _normalize(weights: pd.Series) -> pd.Series:
    total = float(weights.sum())
    return weights / total if total > 0 else pd.Series(1 / len(weights), index=weights.index)


def _first(touches: pd.DataFrame, _: AttributionPolicy) -> pd.Series:
    return pd.Series([1.0] + [0.0] * (len(touches) - 1), index=touches.index)


def _last(touches: pd.DataFrame, _: AttributionPolicy) -> pd.Series:
    return pd.Series([0.0] * (len(touches) - 1) + [1.0], index=touches.index)


def _linear(touches: pd.DataFrame, _: AttributionPolicy) -> pd.Series:
    return pd.Series(1 / len(touches), index=touches.index)


def _time_decay(touches: pd.DataFrame, policy: AttributionPolicy) -> pd.Series:
    age_days = (touches["conversion_timestamp"] - touches["timestamp"]).dt.total_seconds() / 86400
    return _normalize(age_days.map(lambda age: math.pow(0.5, age / policy.half_life_days)))


def _position(touches: pd.DataFrame, policy: AttributionPolicy) -> pd.Series:
    if len(touches) == 1:
        return pd.Series([1.0], index=touches.index)
    if len(touches) == 2:
        return pd.Series([0.5, 0.5], index=touches.index)
    middle = (1 - policy.position_first - policy.position_last) / (len(touches) - 2)
    return pd.Series(
        [policy.position_first] + [middle] * (len(touches) - 2) + [policy.position_last],
        index=touches.index,
    )


MODELS: dict[str, Callable[[pd.DataFrame, AttributionPolicy], pd.Series]] = {
    "first_touch": _first,
    "last_touch": _last,
    "linear": _linear,
    "time_decay": _time_decay,
    "position_based": _position,
}


def attribute_revenue(
    journeys: pd.DataFrame,
    model: str = "time_decay",
    policy: AttributionPolicy | None = None,
) -> pd.DataFrame:
    """Allocate each conversion's revenue across eligible pre-conversion touches."""
    if model not in MODELS:
        raise ValueError(f"Unknown attribution model: {model}")
    policy = policy or AttributionPolicy()
    rows: list[pd.DataFrame] = []
    for _, group in journeys.groupby("journey_id", sort=False):
        touches = _eligible_touches(group)
        weights = MODELS[model](touches, policy)
        output = touches[["journey_id", "event_id", "timestamp", "channel", "campaign"]].copy()
        output["model"] = model
        output["weight"] = weights.to_numpy()
        output["attributed_revenue_eur"] = weights.to_numpy() * float(group["conversion_revenue_eur"].iloc[0])
        rows.append(output)
    columns = [
        "journey_id",
        "event_id",
        "timestamp",
        "channel",
        "campaign",
        "model",
        "weight",
        "attributed_revenue_eur",
    ]
    return pd.concat(rows, ignore_index=True)[columns] if rows else pd.DataFrame(columns=columns)


def compare_models(journeys: pd.DataFrame, policy: AttributionPolicy | None = None) -> pd.DataFrame:
    reports = [attribute_revenue(journeys, model, policy) for model in MODELS]
    combined = pd.concat(reports, ignore_index=True)
    return (
        combined.groupby(["model", "channel"], as_index=False)["attributed_revenue_eur"]
        .sum()
        .sort_values(["model", "attributed_revenue_eur"], ascending=[True, False])
        .reset_index(drop=True)
    )
