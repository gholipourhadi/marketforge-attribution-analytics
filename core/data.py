from __future__ import annotations

import numpy as np
import pandas as pd

ASSETS = {
    "AAPL": (0.00055, 0.018), "MSFT": (0.00050, 0.016),
    "NVDA": (0.00085, 0.028), "AMZN": (0.00048, 0.020),
    "GOOGL": (0.00046, 0.017), "META": (0.00060, 0.022),
    "TSLA": (0.00045, 0.032), "JPM": (0.00032, 0.014),
}


def generate_market_data(days: int = 756, seed: int = 42) -> pd.DataFrame:
    """Create deterministic, correlated synthetic prices for offline demos."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    common = rng.normal(0, 0.009, days)
    prices: dict[str, np.ndarray] = {}
    for ticker, (drift, vol) in ASSETS.items():
        idiosyncratic = rng.normal(0, vol, days)
        returns = drift + 0.55 * common + 0.75 * idiosyncratic
        prices[ticker] = 100 * np.exp(np.cumsum(returns))
    frame = pd.DataFrame(prices, index=dates)
    frame.index.name = "date"
    return frame


def default_weights(columns: list[str]) -> pd.Series:
    raw = np.array([18, 17, 14, 13, 12, 10, 9, 7], dtype=float)[: len(columns)]
    return pd.Series(raw / raw.sum(), index=columns, name="weight")

