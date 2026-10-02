from pathlib import Path
from typing import Any

import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "conf" / "local.yaml"
DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "name": "crkl_db",
    }
}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG

    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    if not isinstance(config, dict) or not isinstance(config.get("database"), dict):
        raise ValueError(f"Invalid database configuration in {CONFIG_PATH}")
    return config


CONFIG = load_config()
