from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from core.risk import TRADING_DAYS


def monte_carlo(returns: pd.DataFrame, weights: pd.Series, simulations: int = 4000,
                horizon: int = 252, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mean = returns.mean().to_numpy()
    cov = returns.cov().to_numpy()
    w = weights.reindex(returns.columns).fillna(0).to_numpy()
    paths = np.empty((horizon + 1, simulations))
    paths[0] = 100_000
    for day in range(1, horizon + 1):
        draws = rng.multivariate_normal(mean, cov, size=simulations)
        paths[day] = paths[day - 1] * (1 + draws @ w)
    return pd.DataFrame(paths)


def efficient_frontier(returns: pd.DataFrame, portfolios: int = 5000, seed: int = 12) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mean = returns.mean().to_numpy() * TRADING_DAYS
    cov = returns.cov().to_numpy() * TRADING_DAYS
    rows = []
    for _ in range(portfolios):
        w = rng.dirichlet(np.ones(len(mean)))
        ret = w @ mean
        vol = np.sqrt(w @ cov @ w)
        rows.append((ret, vol, ret / vol if vol else 0, w))
    result = pd.DataFrame(rows, columns=["return", "volatility", "sharpe", "weights"])
    return result


def detect_anomalies(returns: pd.DataFrame, contamination: float = 0.025) -> pd.DataFrame:
    features = pd.DataFrame({
        "portfolio_move": returns.mean(axis=1),
        "dispersion": returns.std(axis=1),
        "market_volume_proxy": returns.abs().sum(axis=1),
    })
    model = IsolationForest(contamination=contamination, random_state=42)
    features["anomaly"] = model.fit_predict(features) == -1
    features["anomaly_score"] = -model.decision_function(features.drop(columns="anomaly"))
    return features

