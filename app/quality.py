import pandas as pd


def quality_report(events: pd.DataFrame) -> dict[str, float | int]:
    """Summarize volume, duplication, missingness, and conversion coverage."""
    journey_counts = events.groupby("journey_id").size()
    converted = events.groupby("journey_id")["event_type"].apply(lambda values: (values == "conversion").any())
    return {
        "events": len(events),
        "users": int(events["user_id"].nunique()),
        "journeys": int(events["journey_id"].nunique()),
        "channels": int(events["channel"].nunique()),
        "conversion_journeys": int(converted.sum()),
        "conversion_rate": float(converted.mean()),
        "median_touches": float(journey_counts.median()),
        "duplicate_events": int(events["event_id"].duplicated().sum()),
        "missing_values": int(events.isna().sum().sum()),
    }
