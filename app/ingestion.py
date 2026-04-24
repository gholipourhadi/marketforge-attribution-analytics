from pathlib import Path

import numpy as np
import pandas as pd

from app.domain import EVENT_TYPES, TOUCHPOINT_COLUMNS
from app.exceptions import DataContractError


def load_touchpoints(source: str | Path | pd.DataFrame) -> pd.DataFrame:
    """Load, validate and normalize consented marketing touchpoints."""
    frame = source.copy() if isinstance(source, pd.DataFrame) else pd.read_csv(source)
    missing = TOUCHPOINT_COLUMNS.difference(frame.columns)
    if missing:
        raise DataContractError(f"Missing required columns: {sorted(missing)}")

    frame = frame[list(sorted(TOUCHPOINT_COLUMNS))].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    if frame["timestamp"].isna().any():
        raise DataContractError("timestamp contains invalid values")

    for column in ("cost_eur", "revenue_eur"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any() or not np.isfinite(frame[column]).all():
            raise DataContractError(f"{column} must contain finite numbers")
        if (frame[column] < 0).any():
            raise DataContractError(f"{column} cannot be negative")

    text_columns = ["user_id", "journey_id", "event_id", "channel", "campaign", "event_type"]
    for column in text_columns:
        frame[column] = frame[column].astype(str).str.strip()
        if frame[column].eq("").any():
            raise DataContractError(f"{column} cannot be empty")

    if frame["event_id"].duplicated().any():
        raise DataContractError("event_id must be unique")
    invalid_types = set(frame["event_type"]).difference(EVENT_TYPES)
    if invalid_types:
        raise DataContractError(f"Unsupported event types: {sorted(invalid_types)}")
    if not frame["consent"].isin([True, False, 0, 1]).all():
        raise DataContractError("consent must be boolean")
    if (frame.loc[frame["event_type"] != "conversion", "revenue_eur"] > 0).any():
        raise DataContractError("Only conversion events may contain revenue")

    frame["consent"] = frame["consent"].astype(bool)
    frame = frame.loc[frame["consent"]].copy()
    if frame.empty:
        raise DataContractError("No consented events remain after filtering")
    return frame.sort_values(["journey_id", "timestamp", "event_id"]).reset_index(drop=True)


def journey_table(frame: pd.DataFrame, lookback_days: int = 30) -> pd.DataFrame:
    """Create point-in-time journeys ending at the first conversion."""
    if lookback_days < 1:
        raise ValueError("lookback_days must be positive")
    journeys: list[pd.DataFrame] = []
    for _, group in frame.groupby("journey_id", sort=False):
        ordered = group.sort_values(["timestamp", "event_id"])
        conversions = ordered.loc[ordered["event_type"] == "conversion"]
        if conversions.empty:
            continue
        conversion = conversions.iloc[0]
        cutoff = conversion["timestamp"] - pd.Timedelta(days=lookback_days)
        eligible = ordered.loc[
            (ordered["timestamp"] >= cutoff) & (ordered["timestamp"] <= conversion["timestamp"])
        ].copy()
        eligible["conversion_timestamp"] = conversion["timestamp"]
        eligible["conversion_revenue_eur"] = float(conversion["revenue_eur"])
        journeys.append(eligible)
    if not journeys:
        return frame.iloc[0:0].assign(
            conversion_timestamp=pd.Series(dtype="datetime64[ns, UTC]"),
            conversion_revenue_eur=pd.Series(dtype=float),
        )
    return pd.concat(journeys, ignore_index=True)
