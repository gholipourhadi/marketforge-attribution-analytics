import pytest

from app.exceptions import DataContractError
from app.ingestion import journey_table, load_touchpoints


def test_load_touchpoints_normalizes_and_filters(raw_events):
    loaded = load_touchpoints(raw_events)
    assert loaded["consent"].all()
    assert str(loaded["timestamp"].dt.tz) == "UTC"
    assert loaded["event_id"].is_unique


@pytest.mark.parametrize("column", ["user_id", "event_id", "timestamp", "channel", "revenue_eur"])
def test_missing_required_columns_fail(raw_events, column):
    with pytest.raises(DataContractError, match="Missing required"):
        load_touchpoints(raw_events.drop(columns=column))


def test_duplicate_event_fails(raw_events):
    raw_events.loc[1, "event_id"] = raw_events.loc[0, "event_id"]
    with pytest.raises(DataContractError, match="unique"):
        load_touchpoints(raw_events)


def test_negative_spend_fails(raw_events):
    raw_events.loc[0, "cost_eur"] = -1
    with pytest.raises(DataContractError, match="negative"):
        load_touchpoints(raw_events)


def test_invalid_event_type_fails(raw_events):
    raw_events.loc[0, "event_type"] = "purchase-ish"
    with pytest.raises(DataContractError, match="Unsupported"):
        load_touchpoints(raw_events)


def test_revenue_on_click_fails(raw_events):
    index = raw_events.index[raw_events["event_type"] != "conversion"][0]
    raw_events.loc[index, "revenue_eur"] = 10
    with pytest.raises(DataContractError, match="Only conversion"):
        load_touchpoints(raw_events)


def test_journey_table_excludes_post_conversion(events):
    journeys = journey_table(events)
    assert (journeys["timestamp"] <= journeys["conversion_timestamp"]).all()
    assert journeys["journey_id"].nunique() > 0


def test_journey_table_without_conversion_is_empty(events):
    no_conversions = events.loc[events["event_type"] != "conversion"]
    assert journey_table(no_conversions).empty


def test_invalid_lookback_fails(events):
    with pytest.raises(ValueError):
        journey_table(events, 0)
