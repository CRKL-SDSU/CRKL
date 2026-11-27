import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCHEMA_FILES = [ROOT / "specs/db/DDL.sql", ROOT / "backend/database/schema.sql"]
IMAGE_COLUMNS = {"image_url", "thumbnail_url", "image_credit", "image_license"}


def _tables(path: Path) -> dict[str, list[str]]:
    """Maps each CREATE TABLE in a schema file to its column names, in order"""
    tables = {}
    for name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\) ENGINE", path.read_text(), re.S):
        columns = []
        for line in body.splitlines():
            line = line.strip()
            match = re.match(r"(\w+) ", line)
            if match and match.group(1).upper() not in {"PRIMARY", "FOREIGN", "UNIQUE", "KEY", "INDEX", "CONSTRAINT"}:
                columns.append(match.group(1))
        tables[name] = columns
    return tables


def test_both_schema_files_define_the_same_tables_and_columns() -> None:
    ddl, schema = (_tables(path) for path in SCHEMA_FILES)
    assert ddl == schema


def test_every_resource_table_has_the_image_columns() -> None:
    tables = _tables(SCHEMA_FILES[0])
    for table in ("agencies", "spacecraft", "launches", "missions"):
        assert IMAGE_COLUMNS <= set(tables[table]), table


def test_launches_point_to_their_launch_service_provider() -> None:
    for path in SCHEMA_FILES:
        text = path.read_text()
        assert "launch_service_provider_id" in _tables(path)["launches"], path
        assert "FOREIGN KEY (launch_service_provider_id) REFERENCES agencies(agency_id) ON DELETE SET NULL" in text, path
