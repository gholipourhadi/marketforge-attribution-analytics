import numpy as np

from core.data import default_weights, generate_market_data
from core.models import detect_anomalies, monte_carlo
from core.risk import portfolio_returns, returns_from_prices, risk_metrics


def setup_data():
    prices = generate_market_data(days=300)
    returns = returns_from_prices(prices)
    return returns, default_weights(list(returns.columns))


def test_market_data_is_reproducible():
    assert generate_market_data(days=20).equals(generate_market_data(days=20))


def test_weights_sum_to_one():
    returns, weights = setup_data()
    assert np.isclose(weights.sum(), 1)


def test_metrics_are_finite():
    returns, weights = setup_data()
    metrics = risk_metrics(portfolio_returns(returns, weights))
    assert all(np.isfinite(value) for value in metrics.values())
    assert metrics["max_drawdown"] <= 0


def test_monte_carlo_shape():
    returns, weights = setup_data()
    result = monte_carlo(returns, weights, simulations=50, horizon=20)
    assert result.shape == (21, 50)
    assert (result.iloc[0] == 100_000).all()


def test_anomaly_detector_flags_observations():
    returns, _ = setup_data()
    result = detect_anomalies(returns)
    assert result.anomaly.sum() > 0

