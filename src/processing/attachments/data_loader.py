import json
from config.loggin_config import logger

def load_parameters_from_db(json_file):
    """
    Loads parameters from the JSON file and organizes them by 'verw_nr'.

    Args:
        json_file (str): Path to the JSON file.

    Returns:
        list: A list of dictionaries containing 'verw_nr', 'objekt', and 'eigentümer'.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [
                {"verw_nr": entry["verw_nr"], "objekt": entry["objekt"], "eigentümer": entry["eigentümer"]}
                for entry in data if "verw_nr" in entry and "objekt" in entry and "eigentümer" in entry
            ]
    except Exception as e:
        logger.error(f"An error occurred while loading parameters from DB: {e}")
        return []