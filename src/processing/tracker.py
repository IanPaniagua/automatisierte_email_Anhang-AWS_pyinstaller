import json
import os
from typing import Any, Dict
from utils.resource_path import resource_path
from config.loggin_config import logger

CONFIG_FILE = resource_path("config/config.json")

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dictionary."""
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save a dictionary to a JSON file."""
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")

def load_config() -> Dict[str, Any]:
    """Load the config.json file."""
    return load_json_file(CONFIG_FILE)

def save_config(config_data: Dict[str, Any]) -> None:
    """Save the config.json file."""
    save_json_file(CONFIG_FILE, config_data)

def get_last_saved_uid() -> int:
    """
    Retrieve the last saved UID from config.json.
    Returns 0 if the UID is not set or config file is missing.
    """
    config = load_config()
    saved_uid = int(config.get("max_uid", 0) or 0)

    if saved_uid < 0: 
        logger.warning(f"Invalid max_uid ({saved_uid}) found. Resetting to 0.")
        save_last_uid(0)
        return 0

    return saved_uid

def save_last_uid(uid: int) -> None:
    """
    Save the last UID to config.json.
    """
    config = load_config()
    config["max_uid"] = uid
    save_config(config)