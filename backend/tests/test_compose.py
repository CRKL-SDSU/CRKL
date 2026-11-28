from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
COMPOSE = yaml.safe_load((ROOT / "docker-compose.yaml").read_text())
SERVICES = COMPOSE["services"]


def test_database_starts_empty() -> None:
    # the sample data is loaded only on request, with load-dummy-data
    init_files = " ".join(SERVICES["mysql"]["volumes"])
    assert "DDL.sql" in init_files
    assert "dummy_data.sql" not in init_files


def test_loaders_run_only_when_asked() -> None:
    for name in ("load-real-data", "load-dummy-data"):
        assert SERVICES[name]["profiles"] == ["tools"], name
        # each loader's script and data must exist in the repository
        for volume in SERVICES[name]["volumes"]:
            source = volume.split(":")[0]
            assert (ROOT / source).exists(), source


def test_real_data_loader_reads_the_snapshot() -> None:
    assert "./backend/data/snapshot:/app/data/snapshot:ro" in SERVICES["load-real-data"]["volumes"]
