import numpy as np
import pandas as pd


def channel_performance(events: pd.DataFrame, attribution: pd.DataFrame) -> pd.DataFrame:
    """Combine spend, engagement and attributed revenue into channel KPIs."""
    base = events.groupby("channel", as_index=False).agg(
        spend_eur=("cost_eur", "sum"),
        impressions=("event_type", lambda values: int((values == "impression").sum())),
        clicks=("event_type", lambda values: int((values == "click").sum())),
        conversions=("event_type", lambda values: int((values == "conversion").sum())),
    )
    revenue = attribution.groupby("channel", as_index=False)["attributed_revenue_eur"].sum()
    report = base.merge(revenue, on="channel", how="left").fillna({"attributed_revenue_eur": 0.0})
    report["ctr"] = np.where(report["impressions"] > 0, report["clicks"] / report["impressions"], 0.0)
    report["cvr"] = np.where(report["clicks"] > 0, report["conversions"] / report["clicks"], 0.0)
    report["cpa_eur"] = np.where(report["conversions"] > 0, report["spend_eur"] / report["conversions"], np.nan)
    report["roas"] = np.where(report["spend_eur"] > 0, report["attributed_revenue_eur"] / report["spend_eur"], np.nan)
    return report.sort_values("attributed_revenue_eur", ascending=False).reset_index(drop=True)


def funnel(events: pd.DataFrame) -> dict[str, float | int]:
    """Return portfolio-wide funnel counts and stage conversion rates."""
    impressions = int((events["event_type"] == "impression").sum())
    clicks = int((events["event_type"] == "click").sum())
    conversions = int((events["event_type"] == "conversion").sum())
    return {
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "impression_to_click": clicks / impressions if impressions else 0.0,
        "click_to_conversion": conversions / clicks if clicks else 0.0,
    }


def monthly_cohorts(events: pd.DataFrame) -> pd.DataFrame:
    """Report converting customers and revenue by acquisition and conversion month."""
    first_seen = events.groupby("user_id")["timestamp"].min().dt.tz_localize(None).dt.to_period("M").astype(str)
    conversions = events.loc[events["event_type"] == "conversion"].copy()
    conversions["cohort"] = conversions["user_id"].map(first_seen)
    conversions["conversion_month"] = conversions["timestamp"].dt.tz_localize(None).dt.to_period("M").astype(str)
    return conversions.groupby(["cohort", "conversion_month"], as_index=False).agg(
        customers=("user_id", "nunique"), revenue_eur=("revenue_eur", "sum")
    )
