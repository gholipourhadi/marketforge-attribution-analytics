from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def returns_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna()


def portfolio_returns(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    w = weights.reindex(returns.columns).fillna(0)
    return returns.mul(w, axis=1).sum(axis=1).rename("portfolio")


def risk_metrics(series: pd.Series, confidence: float = 0.95) -> dict[str, float]:
    clean = series.dropna()
    annual_return = clean.mean() * TRADING_DAYS
    annual_vol = clean.std() * np.sqrt(TRADING_DAYS)
    cumulative = (1 + clean).cumprod()
    drawdown = cumulative / cumulative.cummax() - 1
    var = -float(clean.quantile(1 - confidence))
    tail = clean[clean <= clean.quantile(1 - confidence)]
    cvar = -float(tail.mean())
    downside = clean[clean < 0].std() * np.sqrt(TRADING_DAYS)
    return {
        "annual_return": float(annual_return),
        "annual_volatility": float(annual_vol),
        "sharpe_ratio": float(annual_return / annual_vol) if annual_vol else 0.0,
        "sortino_ratio": float(annual_return / downside) if downside else 0.0,
        "max_drawdown": float(drawdown.min()),
        "value_at_risk": var,
        "conditional_var": cvar,
    }


def rolling_metrics(series: pd.Series, window: int = 60) -> pd.DataFrame:
    return pd.DataFrame({
        "volatility": series.rolling(window).std() * np.sqrt(TRADING_DAYS),
        "return": series.rolling(window).mean() * TRADING_DAYS,
        "sharpe": (series.rolling(window).mean() / series.rolling(window).std()) * np.sqrt(TRADING_DAYS),
    }).dropna()


def drawdown_series(series: pd.Series) -> pd.Series:
    wealth = (1 + series).cumprod()
    return (wealth / wealth.cummax() - 1).rename("drawdown")


def risk_contribution(returns: pd.DataFrame, weights: pd.Series) -> pd.Series:
    cov = returns.cov() * TRADING_DAYS
    w = weights.reindex(returns.columns).fillna(0).to_numpy()
    portfolio_vol = np.sqrt(w @ cov.to_numpy() @ w)
    marginal = cov.to_numpy() @ w / portfolio_vol
    component = w * marginal
    return pd.Series(component / component.sum(), index=returns.columns, name="risk_contribution")


def historical_stress(returns: pd.DataFrame, weights: pd.Series) -> pd.DataFrame:
    shocks = {
        "Tech crash": {"NVDA": -0.24, "TSLA": -0.22, "META": -0.17, "AAPL": -0.12},
        "Rate shock": {"JPM": -0.08, "AMZN": -0.11, "GOOGL": -0.09},
        "Broad recession": {ticker: -0.14 for ticker in returns.columns},
        "AI correction": {"NVDA": -0.30, "MSFT": -0.10, "GOOGL": -0.12, "META": -0.14},
    }
    rows = []
    for scenario, mapping in shocks.items():
        loss = sum(weights.get(asset, 0) * shock for asset, shock in mapping.items())
        rows.append({"scenario": scenario, "portfolio_impact": loss, "estimated_loss_100k": loss * 100_000})
    return pd.DataFrame(rows)

