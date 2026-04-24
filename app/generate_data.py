from pathlib import Path

import numpy as np
import pandas as pd

CHANNELS = ["paid_search", "organic", "social", "email", "display", "affiliate"]
CAMPAIGNS = {
    "paid_search": "brand-search",
    "organic": "seo-content",
    "social": "social-prospecting",
    "email": "lifecycle-email",
    "display": "display-retargeting",
    "affiliate": "partner-network",
}
COST = {"paid_search": 1.2, "organic": 0.08, "social": 0.65, "email": 0.04, "display": 0.3, "affiliate": 0.9}
CONVERSION_EFFECT = {
    "paid_search": 0.08,
    "organic": 0.05,
    "social": 0.04,
    "email": 0.11,
    "display": 0.025,
    "affiliate": 0.065,
}


def generate_touchpoints(journeys: int = 1800, seed: int = 23) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp("2025-01-01", tz="UTC")
    rows: list[dict] = []
    event_number = 0
    for journey_number in range(journeys):
        user_id = f"usr-{journey_number // 2:05d}"
        journey_id = f"jrn-{journey_number:05d}"
        journey_start = start + pd.Timedelta(hours=int(rng.integers(0, 24 * 180)))
        touch_count = int(rng.integers(1, 7))
        selected = rng.choice(CHANNELS, size=touch_count, replace=True)
        score = -2.8
        for touch_index, channel in enumerate(selected):
            event_number += 1
            timestamp = journey_start + pd.Timedelta(hours=touch_index * int(rng.integers(2, 18)))
            event_type = "click" if rng.random() < 0.58 else "impression"
            score += CONVERSION_EFFECT[channel] * (1.8 if event_type == "click" else 1)
            rows.append(
                {
                    "user_id": user_id,
                    "journey_id": journey_id,
                    "event_id": f"evt-{event_number:07d}",
                    "timestamp": timestamp,
                    "channel": channel,
                    "campaign": CAMPAIGNS[channel],
                    "event_type": event_type,
                    "cost_eur": round(COST[channel] * (1 if event_type == "click" else 0.12), 4),
                    "revenue_eur": 0.0,
                    "consent": bool(rng.random() > 0.025),
                }
            )
        conversion_probability = 1 / (1 + np.exp(-score))
        if rng.random() < conversion_probability:
            event_number += 1
            conversion_time = journey_start + pd.Timedelta(hours=touch_count * 18 + int(rng.integers(1, 12)))
            revenue = float(np.clip(rng.lognormal(mean=4.25, sigma=0.55), 20, 450))
            rows.append(
                {
                    "user_id": user_id,
                    "journey_id": journey_id,
                    "event_id": f"evt-{event_number:07d}",
                    "timestamp": conversion_time,
                    "channel": selected[-1],
                    "campaign": CAMPAIGNS[selected[-1]],
                    "event_type": "conversion",
                    "cost_eur": 0.0,
                    "revenue_eur": round(revenue, 2),
                    "consent": True,
                }
            )
    return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "data" / "sample_touchpoints.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame = generate_touchpoints()
    frame.to_csv(output, index=False)
    print(f"Wrote {len(frame):,} events to {output}")
