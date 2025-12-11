from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import default_weights, generate_market_data
from core.models import detect_anomalies, efficient_frontier, monte_carlo
from core.risk import (drawdown_series, historical_stress, portfolio_returns,
                       returns_from_prices, risk_contribution, risk_metrics,
                       rolling_metrics)

st.set_page_config(page_title="MarketForge Attribution Analytics", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
  .stApp {background: #07111f; color: #e6edf7}
  [data-testid="stMetric"] {background:#101d30;border:1px solid #203653;padding:14px;border-radius:12px}
  h1,h2,h3 {letter-spacing:-.02em}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    prices = generate_market_data()
    returns = returns_from_prices(prices)
    return prices, returns

prices, returns = load_data()
st.sidebar.title("MarketForge Attribution Analytics")
st.sidebar.caption("Institutional portfolio intelligence")
selected = st.sidebar.multiselect("Assets", list(prices.columns), default=list(prices.columns))
selected = selected or list(prices.columns)
weights = default_weights(selected)
st.sidebar.markdown("#### Portfolio allocation")
custom = {asset: st.sidebar.slider(asset, 0, 40, int(weights[asset] * 100)) for asset in selected}
weights = pd.Series(custom, dtype=float)
weights = weights / weights.sum() if weights.sum() else default_weights(selected)

asset_returns = returns[selected]
port = portfolio_returns(asset_returns, weights)
metrics = risk_metrics(port)

st.title("MarketForge Attribution Analytics — Risk Intelligence Platform")
st.caption("Synthetic offline market data • Reproducible analytics • No API key required")

tabs = st.tabs(["Executive Overview", "Risk Lab", "Optimization", "Forecast", "Stress Tests", "AI Anomalies"])

with tabs[0]:
    cols = st.columns(6)
    values = [
        ("Annual return", metrics["annual_return"], "%"), ("Volatility", metrics["annual_volatility"], "%"),
        ("Sharpe", metrics["sharpe_ratio"], "x"), ("Sortino", metrics["sortino_ratio"], "x"),
        ("Max drawdown", metrics["max_drawdown"], "%"), ("95% daily VaR", metrics["value_at_risk"], "%"),
    ]
    for col, (label, value, suffix) in zip(cols, values):
        shown = f"{value:.2f}{suffix}" if suffix == "x" else f"{value:.1%}"
        col.metric(label, shown)
    wealth = (1 + port).cumprod() * 100_000
    c1, c2 = st.columns([2, 1])
    c1.plotly_chart(px.area(wealth, title="Portfolio value", labels={"value":"Value ($)","date":"Date"}), use_container_width=True)
    c2.plotly_chart(px.pie(values=weights.values, names=weights.index, hole=.58, title="Allocation"), use_container_width=True)
    normalized = prices[selected] / prices[selected].iloc[0] * 100
    st.plotly_chart(px.line(normalized, title="Normalized asset performance (base 100)"), use_container_width=True)

with tabs[1]:
    roll = rolling_metrics(port)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.line(roll, y="volatility", title="60-day rolling volatility"), use_container_width=True)
    c2.plotly_chart(px.line(drawdown_series(port), title="Underwater drawdown"), use_container_width=True)
    contrib = risk_contribution(asset_returns, weights).sort_values()
    c1.plotly_chart(px.bar(contrib, orientation="h", title="Component risk contribution"), use_container_width=True)
    corr = asset_returns.corr()
    c2.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="Return correlation"), use_container_width=True)
    st.plotly_chart(px.histogram(port, nbins=60, marginal="box", title="Daily return distribution and tail risk"), use_container_width=True)

with tabs[2]:
    frontier = efficient_frontier(asset_returns, portfolios=3500)
    best = frontier.loc[frontier.sharpe.idxmax()]
    fig = px.scatter(frontier, x="volatility", y="return", color="sharpe", color_continuous_scale="Viridis", title="Monte Carlo efficient frontier")
    fig.add_trace(go.Scatter(x=[best.volatility], y=[best["return"]], mode="markers", marker=dict(size=16, symbol="star", color="#ffcc00"), name="Max Sharpe"))
    st.plotly_chart(fig, use_container_width=True)
    best_weights = pd.Series(best.weights, index=selected).sort_values(ascending=False)
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(best_weights, title="Suggested max-Sharpe allocation"), use_container_width=True)
    comparison = pd.DataFrame({"Current": weights, "Optimized": best_weights}).fillna(0)
    c2.plotly_chart(px.bar(comparison, barmode="group", title="Current vs optimized"), use_container_width=True)

with tabs[3]:
    sims = monte_carlo(asset_returns, weights, simulations=2500)
    sample = sims.iloc[:, :100]
    fig = go.Figure([go.Scatter(y=sample[c], mode="lines", line=dict(width=.5, color="rgba(63,180,255,.12)"), showlegend=False) for c in sample])
    for q, color in [(0.05,"#ff5b6e"),(0.5,"#f5c451"),(0.95,"#45d6a1")]:
        fig.add_trace(go.Scatter(y=sims.quantile(q, axis=1), name=f"{int(q*100)}th percentile", line=dict(color=color, width=3)))
    fig.update_layout(title="One-year Monte Carlo value paths", xaxis_title="Trading day", yaxis_title="Portfolio value ($)")
    st.plotly_chart(fig, use_container_width=True)
    terminal = sims.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Median terminal value", f"${terminal.median():,.0f}")
    c2.metric("Probability of loss", f"{(terminal < 100000).mean():.1%}")
    c3.metric("5th percentile", f"${terminal.quantile(.05):,.0f}")
    st.plotly_chart(px.histogram(terminal, nbins=55, title="Terminal value distribution"), use_container_width=True)

with tabs[4]:
    stress = historical_stress(asset_returns, weights)
    stress["impact_pct"] = stress.portfolio_impact * 100
    st.plotly_chart(px.bar(stress, x="scenario", y="impact_pct", color="impact_pct", color_continuous_scale="RdYlGn", title="Scenario impact (%)"), use_container_width=True)
    st.dataframe(stress[["scenario", "portfolio_impact", "estimated_loss_100k"]].style.format({"portfolio_impact":"{:.2%}", "estimated_loss_100k":"${:,.0f}"}), use_container_width=True, hide_index=True)
    shock = st.slider("Custom market shock", -40, 10, -12) / 100
    beta = asset_returns.cov().mean() / asset_returns.mean(axis=1).var()
    impacts = weights * beta * shock
    st.plotly_chart(px.waterfall if False else px.bar(impacts.sort_values(), orientation="h", title="Custom shock attribution"), use_container_width=True)

with tabs[5]:
    anomalies = detect_anomalies(asset_returns)
    fig = px.scatter(anomalies, x=anomalies.index, y="portfolio_move", color="anomaly", size="market_volume_proxy", title="Isolation Forest anomaly detection")
    st.plotly_chart(fig, use_container_width=True)
    flagged = anomalies[anomalies.anomaly].sort_values("anomaly_score", ascending=False)
    c1, c2 = st.columns([1, 2])
    c1.metric("Flagged market days", len(flagged))
    c1.metric("Alert rate", f"{len(flagged)/len(anomalies):.1%}")
    c2.plotly_chart(px.bar(flagged.head(15), y="anomaly_score", title="Top anomaly scores"), use_container_width=True)
    st.dataframe(flagged.head(20).style.format("{:.4f}"), use_container_width=True)

