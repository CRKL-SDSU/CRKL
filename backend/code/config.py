# Purpose: config.py helps configure our database connection

import os
from pathlib import Path
from typing import Any

import yaml

# creating the variable for the path to our congfig file (local.yaml)
CONFIG_DIR = Path(__file__).resolve().parents[1] / "conf"
CONFIG_PATH = Path(os.environ.get("CRKL_CONFIG_PATH", CONFIG_DIR / "local.yaml"))

# the default dictionary for our database configuration, which includes the following login info:
# the host
# port
# user
# password
# name of the database
DEFAULT_CONFIG: dict[str, Any] = {
    "database": {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "",
        "name": "crkl_db",
    }
}

# function that will load our database using our config dictionary
def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return DEFAULT_CONFIG

    # "with the path to our config file, open it & load the YAML data into a dictionary"
    with CONFIG_PATH.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    # "if neither a valid dictionary was creted, nor was a database dictionary created at all, raise a ValueError"
    if not isinstance(config, dict) or not isinstance(config.get("database"), dict):
        raise ValueError(f"Invalid database configuration in {CONFIG_PATH}")
    return config


CONFIG = load_config()
