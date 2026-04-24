from pathlib import Path

import plotly.express as px
import streamlit as st

from app.attribution import MODELS, attribute_revenue, compare_models
from app.budget import optimize_budget
from app.ingestion import journey_table, load_touchpoints
from app.markov import removal_effects
from app.metrics import channel_performance, funnel
from app.quality import quality_report

st.set_page_config(page_title="MarketForge", page_icon="📈", layout="wide")
st.title("MarketForge Attribution Command Center")
events = load_touchpoints(Path(__file__).resolve().parents[1] / "data" / "sample_touchpoints.csv")
model = st.sidebar.selectbox("Attribution model", list(MODELS), index=3)
journeys = journey_table(events)
attribution = attribute_revenue(journeys, model)
performance = channel_performance(events, attribution)
summary = quality_report(events)
funnel_metrics = funnel(events)

cards = st.columns(5)
cards[0].metric("Events", f"{summary['events']:,}")
cards[1].metric("Journeys", f"{summary['journeys']:,}")
cards[2].metric("Conversions", f"{summary['conversion_journeys']:,}")
cards[3].metric("Conversion rate", f"{summary['conversion_rate']:.1%}")
cards[4].metric("Revenue", f"€{attribution['attributed_revenue_eur'].sum():,.0f}")

left, right = st.columns(2)
left.plotly_chart(
    px.bar(performance, x="channel", y="attributed_revenue_eur", color="roas", title="Channel value"),
    use_container_width=True,
)
right.plotly_chart(
    px.bar(removal_effects(events), x="channel", y="attribution_share", title="Markov removal share"),
    use_container_width=True,
)

st.subheader("Model sensitivity")
st.plotly_chart(
    px.bar(compare_models(journeys), x="channel", y="attributed_revenue_eur", color="model", barmode="group"),
    use_container_width=True,
)

st.subheader("Budget scenario")
budget = st.slider("Budget (€)", 10_000, 200_000, 60_000, 5_000)
scenario = optimize_budget(performance, float(budget))
st.metric("Projected ROAS", f"{scenario.projected_roas:.2f}x")
st.dataframe(scenario.allocation, use_container_width=True)
funnel_text = (
    f"Funnel: {funnel_metrics['impressions']:,} impressions → "
    f"{funnel_metrics['clicks']:,} clicks → "
    f"{funnel_metrics['conversions']:,} conversions"
)
st.caption(funnel_text)
