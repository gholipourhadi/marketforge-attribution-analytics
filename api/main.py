from fastapi import FastAPI

from core.data import default_weights, generate_market_data
from core.risk import portfolio_returns, returns_from_prices, risk_metrics

app = FastAPI(title="MarketForge Attribution Analytics API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "quantguard-api"}


@app.get("/portfolio/metrics")
def metrics():
    prices = generate_market_data()
    returns = returns_from_prices(prices)
    weights = default_weights(list(returns.columns))
    return risk_metrics(portfolio_returns(returns, weights))

