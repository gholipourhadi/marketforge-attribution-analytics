import pytest

from app.attribution import MODELS, attribute_revenue, compare_models
from app.ingestion import journey_table


@pytest.mark.parametrize("model", list(MODELS))
def test_models_conserve_conversion_revenue(events, model):
    journeys = journey_table(events)
    result = attribute_revenue(journeys, model)
    expected = journeys.groupby("journey_id")["conversion_revenue_eur"].first().sum()
    assert result["attributed_revenue_eur"].sum() == pytest.approx(expected)
    totals = result.groupby("journey_id")["weight"].sum()
    assert all(total == pytest.approx(1.0) for total in totals)


def test_first_and_last_touch_assign_single_credit(events):
    journeys = journey_table(events)
    first = attribute_revenue(journeys, "first_touch")
    last = attribute_revenue(journeys, "last_touch")
    assert first.groupby("journey_id")["weight"].max().eq(1).all()
    assert last.groupby("journey_id")["weight"].max().eq(1).all()


def test_unknown_model_fails(events):
    with pytest.raises(ValueError, match="Unknown"):
        attribute_revenue(journey_table(events), "magic")


def test_compare_models_contains_every_model(events):
    result = compare_models(journey_table(events))
    assert set(result["model"]) == set(MODELS)
