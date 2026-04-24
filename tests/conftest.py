import pandas as pd
import pytest

from app.generate_data import generate_touchpoints
from app.ingestion import load_touchpoints


@pytest.fixture
def raw_events() -> pd.DataFrame:
    return generate_touchpoints(journeys=400, seed=8)


@pytest.fixture
def events(raw_events: pd.DataFrame) -> pd.DataFrame:
    return load_touchpoints(raw_events)
