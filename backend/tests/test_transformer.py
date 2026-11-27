import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

from ingestion.transformer import transform_launch

LAUNCH = {
    "id": "aed29ce0-d4e3-4177-b286-d186c7b21354",
    "name": "Saturn V | Apollo 11",
    "net": "1969-07-16T13:32:00Z",
    "window_start": "1969-07-16T13:32:00Z",
    "window_end": "1969-07-16T13:32:00Z",
    "status": {"name": "Launch Successful"},
    "launch_service_provider": {"id": 44, "name": "National Aeronautics and Space Administration"},
    "image": None,
}


def test_launch_keeps_its_launch_service_provider_id() -> None:
    launch = transform_launch(LAUNCH)
    assert launch["launch_service_provider_source_id"] == "44"
    assert launch["source_provider"] == "ll2"


def test_launch_without_a_provider_stores_none() -> None:
    launch = transform_launch({**LAUNCH, "launch_service_provider": None})
    assert launch["launch_service_provider_source_id"] is None
