from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BudgetScenario:
    current_budget_eur: float
    projected_revenue_eur: float
    projected_roas: float
    allocation: list[dict[str, float | str]]

    def to_dict(self) -> dict:
        return asdict(self)


def optimize_budget(
    performance: pd.DataFrame,
    total_budget_eur: float,
    min_share: float = 0.05,
    max_share: float = 0.5,
) -> BudgetScenario:
    """Allocate budget with bounded shares and diminishing-return response curves."""
    if total_budget_eur <= 0:
        raise ValueError("total_budget_eur must be positive")
    count = len(performance)
    if count == 0:
        raise ValueError("performance cannot be empty")
    if min_share * count > 1 or max_share * count < 1 or min_share < 0 or max_share > 1:
        raise ValueError("allocation constraints are infeasible")

    frame = performance.copy().reset_index(drop=True)
    efficiency = frame["roas"].replace([np.inf, -np.inf], np.nan).fillna(0).clip(lower=0).to_numpy()
    scores = np.sqrt(efficiency + 0.05)
    shares = scores / scores.sum()
    shares = np.clip(shares, min_share, max_share)
    for _ in range(100):
        difference = 1 - shares.sum()
        if abs(difference) < 1e-10:
            break
        eligible = shares < max_share - 1e-12 if difference > 0 else shares > min_share + 1e-12
        shares[eligible] += difference / eligible.sum()
        shares = np.clip(shares, min_share, max_share)

    allocations = total_budget_eur * shares
    current_spend = frame["spend_eur"].clip(lower=1).to_numpy()
    response = frame["attributed_revenue_eur"].to_numpy() * np.log1p(allocations / current_spend) / np.log(2)
    rows = [
        {
            "channel": str(frame.loc[index, "channel"]),
            "budget_eur": float(allocations[index]),
            "share": float(shares[index]),
            "projected_revenue_eur": float(response[index]),
        }
        for index in range(count)
    ]
    projected = float(response.sum())
    return BudgetScenario(total_budget_eur, projected, projected / total_budget_eur, rows)
