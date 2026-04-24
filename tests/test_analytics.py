import math

import pandas as pd
import pytest

from app.attribution import attribute_revenue
from app.budget import optimize_budget
from app.exceptions import InsufficientDataError
from app.experiments import evaluate_binary_experiment
from app.ingestion import journey_table
from app.markov import removal_effects
from app.metrics import channel_performance, funnel, monthly_cohorts
from app.quality import quality_report


def test_channel_performance_has_business_metrics(events):
    report = channel_performance(events, attribute_revenue(journey_table(events)))
    assert {"roas", "cpa_eur", "ctr", "cvr"}.issubset(report.columns)
    assert report["spend_eur"].sum() == pytest.approx(events["cost_eur"].sum())


def test_funnel_and_quality(events):
    stages = funnel(events)
    quality = quality_report(events)
    assert stages["impressions"] + stages["clicks"] + stages["conversions"] == len(events)
    assert quality["duplicate_events"] == 0
    assert 0 <= quality["conversion_rate"] <= 1


def test_funnel_handles_zero_impressions():
    events = pd.DataFrame({"event_type": ["click", "conversion"]})
    stages = funnel(events)
    assert stages["impression_to_click"] == 0.0
    assert stages["click_to_conversion"] == pytest.approx(1.0)


def test_cohorts_only_include_conversions(events):
    cohorts = monthly_cohorts(events)
    assert cohorts["customers"].sum() > 0
    assert cohorts["revenue_eur"].sum() == pytest.approx(events["revenue_eur"].sum())


def test_markov_shares_sum_to_one(events):
    result = removal_effects(events)
    assert result["attribution_share"].sum() == pytest.approx(1.0)
    assert (result["removal_effect"] >= 0).all()


def test_experiment_detects_lift():
    result = evaluate_binary_experiment(100, 2000, 160, 2000)
    assert result.absolute_lift > 0
    assert result.statistically_significant
    assert result.ci_low > 0


def test_experiment_handles_zero_control():
    result = evaluate_binary_experiment(0, 100, 3, 100)
    assert math.isinf(result.relative_lift)


def test_experiment_rejects_small_sample():
    with pytest.raises(InsufficientDataError):
        evaluate_binary_experiment(1, 20, 2, 20)


def test_experiment_rejects_impossible_counts():
    with pytest.raises(ValueError):
        evaluate_binary_experiment(101, 100, 5, 100)


def test_budget_constraints_and_conservation(events):
    report = channel_performance(events, attribute_revenue(journey_table(events)))
    scenario = optimize_budget(report, 50_000, 0.05, 0.4)
    allocations = scenario.allocation
    assert sum(row["budget_eur"] for row in allocations) == pytest.approx(50_000)
    assert all(0.05 <= row["share"] <= 0.4 for row in allocations)
    assert scenario.projected_roas >= 0


@pytest.mark.parametrize("budget", [0, -1])
def test_budget_must_be_positive(events, budget):
    report = channel_performance(events, attribute_revenue(journey_table(events)))
    with pytest.raises(ValueError):
        optimize_budget(report, budget)


def test_infeasible_budget_constraints_fail(events):
    report = channel_performance(events, attribute_revenue(journey_table(events)))
    with pytest.raises(ValueError, match="infeasible"):
        optimize_budget(report, 1000, min_share=0.3)
